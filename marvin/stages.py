"""
.. module:: stages
   :platform: Unix
   :synopsis: The module containing test stages definitions.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

import os
import logging
from marvin.remote import OpenSSH
from marvin.remote import DataItem
from marvin.remote import OpenSSHProtocol
from marvin.remote import SFTPProtocol
from marvin.errors import FileParseError

# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments

# i tried to use namedtuple here, but the code was to complex
class TransferDataItem(object):
    """ It contains transfer data item informations """

    def __init__(self, src, dst, src_type):
        self.src = src
        self.dst = dst
        self.src_type = src_type

    def get_data(self, callback=None):
        """
        If needed, it gets data from a remote source, then it returns a
        DataItem object with the local path that must be transferred.
        :param callback:
            ``funct(curr_bytes, tot_bytes)`` where `curr_bytes` are the current
            downloaded bytes and `tot_bytes` are the amount of bytes to
            download. Not always is needed. If it does, it will be used.
        :type callback: callable
        :returns: DataItem object
        """
        raise NotImplementedError("Please Implement this method")

class DeployDataItem(TransferDataItem):
    """ It contains deploy data informations """

    def __init__(self, src, dst, src_type, reportdir):
        super().__init__(src, dst, src_type)
        self._reportdir = reportdir

    def get_data(self, callback=None):
        src = ""
        dst = ""
        target = "remote"

        if self.src_type == "file":
            src = self.src
            dst = self.dst
        else:
            raise NotImplementedError("'%s' is not implemented" % self.src_type)

        data = DataItem(src, dst, target)
        return data

class CollectDataItem(TransferDataItem):
    """ It contains collect data informations """

    def get_data(self, callback=None):
        src = ""
        dst = ""
        target = "local"

        if self.src_type == "file":
            src = self.src
            dst = self.dst
        else:
            raise NotImplementedError("'%s' is not implemented" % self.src_type)

        data = DataItem(src, dst, target)
        return data

class ExecuteDataItem(object):
    """ It contains execute stage commands informations """

    def __init__(self, command, passing, failing):
        self.command = command
        self.passing = passing
        self.failing = failing

class Stage(object):
    """ A generic test stage """

    def __init__(self, testdef, testdir, reportdir, events):
        self.testdef = testdef
        self.testdir = testdir
        self.reportdir = reportdir
        self.events = events

class DeployStage(Stage):
    """ deploy stage handler """

    def __init__(self, testdef, testdir, reportdir, events, protocols):
        super().__init__(testdef, testdir, reportdir, events)
        self._logger = logging.getLogger(__name__)
        self._protocols = protocols
        self._deploy_exists = False
        self._deploy_del_remote = True
        self._deploy_data = []
        self._deploy_protocol = None
        self._read_definition()

    def _read_definition(self):
        """
        Read the deploy configuration.
        """
        if 'deploy' not in self.testdef:
            self._logger.debug("'deploy' stage is not defined")
            return

        # notify deploy is going to be read
        self.events.readDeployStarted()

        self._deploy_exists = True

        deploydef = self.testdef['deploy']

        # read the default protocol
        protoname = deploydef['protocol']

        self._logger.debug("default deploy protocol=%s", protoname)

        self._deploy_protocol = None
        for protocol in self._protocols:
            if protocol.name == protoname:
                self._deploy_protocol = protocol
                break

        if not self._deploy_protocol:
            raise FileParseError(\
               "'%s' protocol is not defined anywhere. Path: /deploy/protocol"%\
               protoname)

        # create the deploy data list
        transferdef = deploydef['transfer']

        self._logger.debug("transferdef=%s", transferdef)

        self._deploy_data.clear()
        for item in transferdef:
            src = item['source']
            dst = item['dest']
            src_type = ""

            # if type is not defined, suppose it's a local file
            if 'type' in item:
                src_type = item['type']
            else:
                src_type = "file"

            # get the absolute path of the source
            if not os.path.isabs(src):
                src = os.path.join(self.testdir, src)

            data = DeployDataItem(src, dst, src_type, self.reportdir)

            self._deploy_data.append(data)

        # notify deploy has been read
        self.events.readDeployCompleted(deploydef)

    def run(self):
        """
        Run the deploy stage if defined.
        """
        if not self._deploy_exists:
            self._logger.debug("deploy is not defined. Skipping run")
            return

        self.events.deployStarted()

        dataitems = []
        for item in self._deploy_data:
            data = item.get_data()
            dataitems.append(data)

        # sftp is defined
        if isinstance(self._deploy_protocol, SFTPProtocol):
            self._logger.debug("transfer data using sftp protocol")

            openssh = OpenSSH(self._deploy_protocol)
            openssh.sftp_transfer(dataitems, \
                self.events.dataTransfer, \
                self.events.dataTransferProgress)
        else:
            raise NotImplementedError(\
               "'%s' protocol is not implemented"%self._deploy_protocol.name())

        self.events.deployCompleted()

    def cleanup(self):
        """ Remove the transferred files from target """
        if not self._deploy_exists:
            self._logger.debug("deploy is not defined. Skipping cleanup")
            return

        self.events.cleanupTargetStarted()

        paths = []
        for item in self._deploy_data:
            paths.append(item.dst)

        if isinstance(self._deploy_protocol, SFTPProtocol):
            openssh = OpenSSH(self._deploy_protocol)
            openssh.sftp_remove(paths, \
                self.events.cleanupTargetPath)
        else:
            raise NotImplementedError(\
                "'%s' protocol is not implemented"%self._deploy_protocol.name())

        self.events.cleanupTargetCompleted()

class ExecuteStage(Stage):
    """ execute stage handler """

    def __init__(self, testdef, testdir, reportdir, events, protocols):
        super().__init__(testdef, testdir, reportdir, events)

        self._logger = logging.getLogger(__name__)
        self._protocols = protocols
        self._execute_exists = False
        self._execute_cmds = []
        self._execute_protocol = None
        self._read_definition()

    def _read_definition(self):
        """
        Read the execute configuration.
        """
        if 'execute' not in self.testdef:
            self._logger.debug("'execute' stage is not defined")
            return

        # notify execute reading has started
        self.events.readExecuteStarted()

        self._execute_exists = True

        executedef = self.testdef['execute']

        # read the default protocol
        protoname = executedef['protocol']

        self._logger.debug("default execute protocol=%s", protoname)

        self._execute_protocol = None
        for protocol in self._protocols:
            if protoname == protocol.name:
                self._execute_protocol = protocol
                break

        if not self._execute_protocol:
            raise FileParseError(\
                "'%s' is not defined anywhere. Path: /execute/protocol"%\
                protoname)

        # create the list of commands
        commands = executedef['commands']

        self._logger.debug("commands=%s", commands)

        self._execute_cmds.clear()
        for command in commands:
            script = command['script']
            failing = ""
            passing = ""

            # failing and passing strings are optional
            if 'failing' in command:
                failing = command['failing']
            if 'passing' in command:
                passing = command['passing']

            item = ExecuteDataItem(script, passing, failing)

            self._execute_cmds.append(item)

        # notify execute has been read
        self.events.readExecuteCompleted(executedef)

    def _hook_exec_callback(self, command, retvalue):
        for item in self._execute_cmds:
            if item.command == command:
                self.events.executeCommandCompleted(\
                    item.command, \
                    item.passing, \
                    item.failing, \
                    retvalue)

    def run(self):
        """
        Run the execute stage if defined.
        """
        if not self._execute_exists:
            self._logger.debug("execute is not defined. Skipping run")
            return

        self.events.executeStarted()

        commands = []
        for item in self._execute_cmds:
            commands.append(item.command)

        # ssh is defined
        if isinstance(self._execute_protocol, OpenSSHProtocol):
            self._logger.debug("execute commands using ssh protocol")

            openssh = OpenSSH(self._execute_protocol)
            openssh.ssh_execute(commands, \
                self.events.executeCommandStarted, \
                    exec_callback=self._hook_exec_callback)
        else:
            raise NotImplementedError(\
              "'%s' protocol is not implemented"%self._execute_protocol.name())

        self.events.executeCompleted()

class CollectStage(Stage):
    """ collect stage handler """

    def __init__(self, testdef, testdir, reportdir, events, protocols):
        super().__init__(testdef, testdir, reportdir, events)

        self._logger = logging.getLogger(__name__)
        self._protocols = protocols
        self._collect_exists = False
        self._collect_data = []
        self._collect_protocol = None
        self._read_definition()

    def _read_definition(self):
        if 'collect' not in self.testdef:
            self._logger.debug("collect is not defined")
            return

        # notify collect reading has started
        self.events.readCollectStarted()

        self._collect_exists = True

        collectdef = self.testdef['collect']

        # read the default protocol
        protoname = collectdef['protocol']

        self._logger.debug("default collect protocol=%s", protoname)

        self._collect_protocol = None
        for protocol in self._protocols:
            if protocol.name == protoname:
                self._collect_protocol = protocol
                break

        if not self._collect_protocol:
            raise FileParseError(\
              "'%s' protocol is not defined anywhere. Path: /collect/protocol"%\
              protoname)

        # create the collect data list
        transferdef = collectdef['transfer']

        self._logger.debug("transferdef=%s", transferdef)

        self._collect_data.clear()
        for item in transferdef:
            src = item['source']
            dst = item['dest']
            src_type = ""

            # if type is not defined, suppose it's a local file
            if 'type' in item:
                src_type = item['type']
            else:
                src_type = "file"

            # get the absolute path of the source
            if not os.path.isabs(dst):
                dst = os.path.join(self.reportdir.remotedata, dst)

            data = CollectDataItem(src, dst, src_type)

            self._collect_data.append(data)

        # notify that collect has been read
        self.events.readCollectCompleted(collectdef)

    def run(self):
        """
        Run the collect stage if defined.
        """
        if not self._collect_exists:
            self._logger.debug("collect is not defined. Skipping run")
            return

        self.events.collectStarted()

        dataitems = []
        for item in self._collect_data:
            data = item.get_data()
            dataitems.append(data)

        # sftp is defined
        if isinstance(self._collect_protocol, SFTPProtocol):
            self._logger.debug("transfer data using sftp protocol")

            openssh = OpenSSH(self._collect_protocol)
            openssh.sftp_transfer(dataitems, \
                self.events.dataTransfer, \
                self.events.dataTransferProgress)
        else:
            raise NotImplementedError(\
               "'%s' protocol is not implemented"%\
               self._collect_protocol.name())

        self.events.collectCompleted()
