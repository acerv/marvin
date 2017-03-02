"""
.. module:: remote
   :platform: Unix
   :synopsis: A module defining remote functionalities.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

import os
import logging
import socket
import paramiko
from marvin.errors import LocalPathNotExistError
from marvin.errors import RemotePathNotExistError
from marvin.errors import SSHConnectionError

# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments

class _Protocol(object):
    """ The protocol definition """
    def __init__(self, name):
        self.name = name

class OpenSSHProtocol(_Protocol):
    """ The openssh protocol definition """
    def __init__(self, address, port, user, password, timeout):
        """
        :param address: the target address
        :type address: str
        :param port: the target port
        :type port: int
        :param user: the login user
        :type user: str
        :param password: the login password
        :type password: str
        :param timeout: the connection timeout
        :type timeout: float
        """
        super().__init__("ssh")
        self.address = address
        self.port = port
        self.user = user
        self.password = password
        self.timeout = timeout

class SFTPProtocol(_Protocol):
    """ The sftp protocol definition """
    def __init__(self, address, port, user, password, timeout):
        """
        :param address: the target address
        :type address: str
        :param port: the target port
        :type port: int
        :param user: the login user
        :type user: str
        :param password: the login password
        :type password: str
        :param timeout: the connection timeout
        :type timeout: float
        """
        super().__init__("sftp")
        self.address = address
        self.port = port
        self.user = user
        self.password = password
        self.timeout = timeout

class DataItem(object):
    """ The data item to transfer """
    def __init__(self, source, destination, target):
        self.source = source
        self.destination = destination
        self.target = target

class OpenSSH:
    """ The openssh protocol handler """

    def __init__(self, protocol):
        """
        :param protocol: the protocol definition
        :type protocol: OpenSSHProtocol
        :raises: NotImplementedError
        """
        if not isinstance(protocol, OpenSSHProtocol) and \
           not isinstance(protocol, SFTPProtocol):
            raise NotImplementedError(\
                "'protocol' definition is of type '%s'"%type(protocol))

        self._logger = logging.getLogger(__name__)
        self._logger.debug("protocol=%s", protocol)

        self._protocol = protocol

    @staticmethod
    def _ssh_connect_to_target(protocol):
        try:
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(protocol.address, \
                port=protocol.port, \
                username=protocol.user, \
                password=protocol.password, \
                timeout=protocol.timeout)
        except (paramiko.SSHException, \
                paramiko.AuthenticationException, \
                paramiko.BadHostKeyException,
                socket.error) as ex:
            raise SSHConnectionError("%s"%ex) from ex

        return ssh

    def sftp_transfer(self, data, item_callback=None, transfer_callback=None):
        """
        Transfer data from/to target using a the *sftp* protocol.

        :param data: the list of data items to transfer
        :type data: list(DataItem)
        :param item_callback:
            optional callback defined as ``funct(str, str)``, where arguments
            are source and destination paths.
        :type item_callback: callable
        :param transfer_callback:
            optional callback defined as ``funct(int, int)``, where arguments
            are bytes transferred so far and the total bytes.
        :type transfer_callback: callable
        :raises ConnectionError: if there's a connection problem
        :raises LocalPathNotExistError: if local path doesn't exist
        :raises RemotePathNotExistError: if remote path doesn't exist
        """
        self._logger.debug("transfer data using 'sftp' protocol")
        self._logger.debug("data=%s", data)

        # check if the local file to transfer exists
        # there's no need to do the same with the remote files, since they are
        # overwritten by the paramiko library
        for item in data:
            if item.target == "remote" and not os.path.exists(item.source):
                raise LocalPathNotExistError(\
                    "'%s' doesn't exist"%item.source)

        with self._ssh_connect_to_target(self._protocol) as ssh:
            sftp = ssh.open_sftp()

            # transfer data
            for item in data:
                if item_callback:
                    item_callback(item.source, item.destination)

                if item.target == "remote":
                    sftp.put(item.source, item.destination, transfer_callback)
                else: # local
                    try:
                        sftp.get(item.source, item.destination, \
                            transfer_callback)
                    except IOError as ex:
                        raise RemotePathNotExistError(\
                            "'%s' doesn't exist"%item.source) from ex

    def sftp_remove(self, paths, callback=None):
        """
        Remove a remote path using SFTP protocol.

        :param paths: the paths to remove
        :type paths: list(str)
        :param callback: an optional callback that is called when a path is
            going to be removed. The function is defined as
            ``callback(str)``, where the argument is the path of the file to
            remove.
        :raises ConnectionError: if there's a connection problem
        :raises RemotePathNotExistError: if remote path doesn't exist
        """
        self._logger.debug("remove paths using 'sftp' protocol")
        self._logger.debug("paths=%s", paths)

        with self._ssh_connect_to_target(self._protocol) as ssh:
            sftp = ssh.open_sftp()

            # remove data
            for item in paths:
                if callback:
                    callback(item)

                try:
                    sftp.remove(item)
                except IOError as ex:
                    raise RemotePathNotExistError(\
                        "'%s' doesn't exist"%item) from ex

    def ssh_execute(self, commands, item_callback=None, exec_callback=None):
        """
        Execute a command on target using the *ssh* protocol.

        :param commands: the list of commands to execute
        :type commands: list(str)
        :param item_callback: optional callback used to trace the command
            stdout. The function is defined as ``funct(str, io, io)`` where
            arguments are command, stdout and stderr.
        :type item_callback: callable
        :param exec_callback: optional callback raised when a command has been
            executed. The function is defined as
            ``funct(str, str, str, str)`` where arguments are command,
            passing, failing defined by the user and the command's return value.
        :type exec_callback: callable
        :raises ConnectionError: if there's a connection problem
        :returns: a list of commands return codes
        """
        self._logger.debug("execute commands using 'ssh' protocol")
        self._logger.debug("commands=%s", commands)

        timeout = self._protocol.timeout
        results = []

        with self._ssh_connect_to_target(self._protocol) as ssh:
            for command in commands:
                stdin, stdout, stderr = ssh.exec_command(\
                    command, \
                    timeout=timeout, \
                    get_pty=True)

                if item_callback:
                    item_callback(command, stdout, stderr)

                result = stdout.channel.recv_exit_status()

                if exec_callback:
                    exec_callback(command, str(result))

                results.append(result)

                stdin.close()
                stdout.close()
                stderr.close()

        self._logger.debug("results=%s", results)

        return results
