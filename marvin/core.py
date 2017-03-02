"""
.. module:: core
   :platform: Unix
   :synopsis: The module defining the main tester.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

import os
import logging
import marvin.file
import marvin.report
from marvin.events import CoreEvents
from marvin.remote import OpenSSHProtocol
from marvin.remote import SFTPProtocol
from marvin.stages import DeployStage
from marvin.stages import ExecuteStage
from marvin.stages import CollectStage
from marvin.errors import FileParseError
from marvin.errors import LocalPathNotExistError
from marvin.errors import RemotePathNotExistError
from marvin.errors import SSHConnectionError

class Core:
    """ Execute a test from a test file definition """

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._events = CoreEvents()
        self._testdef = None
        self._testdir = ""
        self._deploy = None
        self._protocols = []
        self._reportdir = None
        self._execute = None
        self._collect = None
        self._loaded = False

    def __read_test_definition(self, testfile):
        self.events.readFileStarted(testfile)
        self._testdef = marvin.file.load(testfile)
        self.events.readFileCompleted(self._testdef)

    def __create_report_dir(self, reportsdir):
        self.events.createReportDirStarted(reportsdir)
        self._reportdir = marvin.report.create_test_report_dir(\
            reportsdir, \
            self._testdef['name'], \
            self._testdef['version'])
        self.events.createReportDirCompleted(self._reportdir)

    def __read_protocols_definition(self):
        protocolsdef = self._testdef['protocols']

        self._protocols.clear()

        # read sftp protocol definition
        if 'sftp' in protocolsdef:
            self.events.readProtocolStarted("sftp")
            sftp = protocolsdef['sftp']
            sftp_protocol = SFTPProtocol(
                sftp['address'],
                sftp['port'],
                sftp['user'],
                sftp['password'],
                sftp['timeout']
            )
            self._protocols.append(sftp_protocol)
            self.events.readProtocolCompleted(sftp)

        # read ssh protocol definition
        if 'ssh' in protocolsdef:
            self.events.readProtocolStarted("ssh")
            ssh = protocolsdef['ssh']
            ssh_protocol = OpenSSHProtocol(
                ssh['address'],
                ssh['port'],
                ssh['user'],
                ssh['password'],
                ssh['timeout']
            )
            self._protocols.append(ssh_protocol)
            self.events.readProtocolCompleted(ssh)

    def __read_deploy_definition(self):
        self._deploy = DeployStage(
            self._testdef,
            self._testdir,
            self._reportdir,
            self._events,
            self._protocols
        )

    def __read_execute_definition(self):
        self._execute = ExecuteStage(
            self._testdef,
            self._testdir,
            self._reportdir,
            self._events,
            self._protocols
        )

    def __read_collect_definition(self):
        self._collect = CollectStage(
            self._testdef,
            self._testdir,
            self._reportdir,
            self._events,
            self._protocols
        )

    @property
    def events(self):
        """ The event handler """
        return self._events

    @property
    def deploy(self):
        """ The deploy stage handler """
        return self._deploy

    @property
    def execute(self):
        """ The execute stage handler """
        return self._execute

    @property
    def collect(self):
        """ The collect stage handler """
        return self._collect

    def load(self, testfile, reportsdir):
        """
        Load the test definition. If you need to hook the loading events,
        use the `events` property **before** calling this method.

        :param testfile: the test definition file
        :type testfile: str
        :param reportsdir: directory where reports will be saved
        :type reportsdir: str
        :param iohandler: the standard I/O handler
        :type iohandler: IOHandler
        :raises: ValueError, FileParseError
        :returns: Core object
        """
        try:
            if not testfile or not os.path.isfile(testfile):
                raise ValueError("test file does not exist")

            if not reportsdir or not os.path.isdir(reportsdir):
                raise ValueError("reports directory does not exist")

            self._testdir = os.path.abspath(os.path.dirname(testfile))
            self.__read_test_definition(testfile)
            self.__create_report_dir(reportsdir)
            self.__read_protocols_definition()
            self.__read_deploy_definition()
            self.__read_execute_definition()
            self.__read_collect_definition()

            self._loaded = True
        except (ValueError, FileParseError) as ex:
            self._logger.exception(ex)

            if len(self._events.exceptionCatched) != 0:
                self._events.exceptionCatched(ex)
            else: # let it flow
                raise ex

    def runall(self):
        """ Run all the stages """
        if not self._loaded:
            self._logger.debug("core is not loaded. Skipping runall")
            return

        self._logger.debug("running stages")

        deploy_done = False

        try:
            self.deploy.run()

            deploy_done = True

            self.execute.run()
            self.collect.run()
        except (SSHConnectionError, \
                LocalPathNotExistError, \
                RemotePathNotExistError) as ex:
            self._logger.exception(ex)

            if len(self._events.exceptionCatched) != 0:
                self._events.exceptionCatched(ex)
            else: # let it flow
                raise ex
        finally:
            if deploy_done:
                try:
                    self.deploy.cleanup()
                except RemotePathNotExistError as ex:
                    self._logger.exception(ex)

                    if len(self._events.exceptionCatched) != 0:
                        self._events.exceptionCatched(ex)
                    else: # let it flow
                        raise ex
