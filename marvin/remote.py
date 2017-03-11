"""
.. module:: remote
   :platform: Unix
   :synopsis: A module defining remote functionalities.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

import os
import io
import stat
import logging
import socket
import paramiko
import serial
from marvin.errors import LocalPathNotExistError
from marvin.errors import RemotePathNotExistError
from marvin.errors import SSHConnectionError
from marvin.errors import ExecCommandError
from marvin.errors import SerialConnectionError

# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments

class _Protocol(object):
    """
    The protocol definition
    """
    def __init__(self, name):
        self.name = name

class OpenSSHProtocol(_Protocol):
    """
    The openssh protocol definition
    """
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
    """
    The sftp protocol definition
    """
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
    """
    The data item to transfer
    """
    def __init__(self, source, destination, target):
        self.source = source
        self.destination = destination
        self.target = target

class CommandStream(object):
    """
    The command stream is used to handle a command execution.
    """
    def cmd_executing(self, command):
        """
        Raised when the command is going to be executed.
        :param command: the command executing
        :type command: str
        """
        raise NotImplementedError("please implement this method")

    def handle_stdout_line(self, line):
        """
        Raised when a command stdout line has been acquired.
        :param line: stdout read line
        :type line: str
        """
        raise NotImplementedError("please implement this method")

    def cmd_completed(self, result):
        """
        Raised when a command has been completed.
        :param result: the command result when it's completed
        :type result: str
        """
        raise NotImplementedError("please implement this method")

class OpenSSH:
    """
    The openssh protocol handler
    """
    def __init__(self, protocol):
        """
        :param protocol: the protocol definition
        :type protocol: OpenSSHProtocol or SFTPProtocol
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

            # paramiko doesn't accept empty string for user/password but None
            inner_user = None
            if protocol.user:
                inner_user = protocol.user

            inner_pwd = None
            if protocol.password:
                inner_pwd = protocol.password

            ssh.connect(protocol.address, \
                port=protocol.port, \
                username=inner_user, \
                password=inner_pwd, \
                timeout=protocol.timeout)
        except (paramiko.SSHException, \
                paramiko.AuthenticationException, \
                paramiko.BadHostKeyException,
                socket.error) as ex:
            raise SSHConnectionError("%s"%ex) from ex

        return ssh

    @staticmethod
    def _sftp_full_permissions(sftp, path):
        sftp.chmod(path, \
            stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | \
            stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | \
            stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH)

    def _sftp_put_path(self, sftp, src, dst, icallback, tcallback):
        if os.path.isdir(src): # transfer directory
            sftp.mkdir(dst)
            self._sftp_full_permissions(sftp, dst)

            for src_root, dirs, files in os.walk(src, topdown=True):
                # skip this stage if directory is empty
                if not dirs and not files:
                    break

                dst_root = src_root.replace(src, dst)
                dst_file = ""

                self._logger.debug("dirs=%s, files=%s", dirs, files)

                for name in dirs:
                    dst_file = "%s/%s" % (dst_root, name)

                    self._logger.debug("creating %s", dst_file)

                    sftp.mkdir(dst_file)

                for name in files:
                    src_file = "%s/%s" % (src_root, name)
                    dst_file = "%s/%s" % (dst_root, name)

                    self._logger.debug("sending %s -> %s", src_file, dst_file)

                    # notify when sending item
                    if icallback:
                        icallback(src_file, dst_file)

                    sftp.put(src_file, dst_file, tcallback)

                self._sftp_full_permissions(sftp, dst_file)
        else: # transfer single file
            if icallback:
                icallback(src, dst)

            sftp.put(src, dst, tcallback)

            self._sftp_full_permissions(sftp, dst)

    @staticmethod
    def _sftp_remote_path_isdir(sftp, path):
        if not path:
            raise ValueError("path is empty")

        if stat.S_ISDIR(sftp.stat(path).st_mode):
            return True

        return False

    def _sftp_get_path(self, sftp, src, dst, icallback, tcallback):
        if self._sftp_remote_path_isdir(sftp, src):
            os.mkdir(dst)

            files = sftp.listdir(path=src)

            for file in files:
                filepath = "%s/%s"%(src, file)
                destpath = "%s/%s"%(dst, file)

                self._logger.debug("fetching %s -> %s", filepath, destpath)

                self._sftp_get_path(sftp, \
                    filepath, destpath, \
                    icallback, tcallback)
        else:
            if icallback:
                icallback(src, dst)

            sftp.get(src, dst, tcallback)

    def _sftp_rm_path(self, sftp, pathtoremove, icallback):
        if self._sftp_remote_path_isdir(sftp, pathtoremove):
            files = sftp.listdir(path=pathtoremove)

            for file in files:
                filepath = "%s/%s"%(pathtoremove, file)

                self._logger.debug("removing %s", filepath)

                self._sftp_rm_path(sftp, filepath, icallback)

            # remove the directory once it's emty
            sftp.rmdir(pathtoremove)
        else:
            sftp.remove(pathtoremove)

    def sftp_transfer(self, data, icallback=None, tcallback=None):
        """
        Transfer data from/to target using a the *sftp* protocol.

        :param data: the list of data items to transfer
        :type data: list(DataItem)
        :param icallback:
            optional callback defined as ``funct(str, str)``, where arguments
            are source and destination paths.
        :type icallback: callable
        :param tcallback:
            optional callback defined as ``funct(int, int)``, where arguments
            are bytes transferred so far and the total bytes.
        :type tcallback: callable
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
                if item.target == "remote":
                    self._sftp_put_path(sftp, \
                        item.source, item.destination, \
                        icallback, tcallback)
                else: # local
                    try:
                        self._sftp_get_path(sftp, \
                            item.source, item.destination, \
                            icallback, tcallback)
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
                    self._sftp_rm_path(sftp, item, callback)
                except IOError as ex:
                    raise RemotePathNotExistError(\
                        "'%s' doesn't exist"%item) from ex

    def ssh_execute(self, commands, stream=None):
        """
        Execute a command on target using the *ssh* protocol.

        :param commands: the list of commands to execute
        :type commands: list(str)
        :param stream: the optional command stream
        :type stream: CommandStream
        :raises ConnectionError: if there's a connection problem
        :returns: a list of commands return codes
        """
        self._logger.debug("execute commands using 'ssh' protocol")
        self._logger.debug("commands=%s", commands)

        timeout = self._protocol.timeout
        results = []

        with self._ssh_connect_to_target(self._protocol) as ssh:
            # run commands
            for command in commands:
                # create the stream channel
                tran = ssh.get_transport()
                chan = tran.open_session(timeout=timeout)
                chan.settimeout(timeout)

                # request error stream to be merged with the remote pty terminal
                chan.set_combine_stderr(True)
                chan.get_pty()

                if stream:
                    # send command executing event
                    stream.cmd_executing(command)

                try:
                    chan.exec_command(command)
                except paramiko.SSHException as ex:
                    raise ExecCommandError("%s"%ex) from ex

                result = None

                with chan.makefile('r', -1) as stdout:
                    if stream:
                        # send stdout line
                        for line in iter(stdout.readline, ""):
                            stream.handle_stdout_line(line)

                    result = stdout.channel.recv_exit_status()

                    if stream:
                        # send command result
                        stream.cmd_completed(str(result))

                results.append(result)

        self._logger.debug("results=%s", results)

        return results

class SerialProtocol(_Protocol):
    """
    The serial protocol definition.
    """
    def __init__(self, port, baudrate, parity, stop_bits, data_bits, timeout):
        """
        :param port: the serial port
        :type port: str
        :param baudrate: the serial baudrate
        :type baudrate: int
        :param parity: the number of parity bits
        :type parity: int
        :param stop_bits: the number of stop bits
        :type stop_bits: int
        :param data_bits: the number of data bits
        :type data_bits: int
        :param timeout: the command timeout
        :type timeout: float
        """
        super().__init__("serial")
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.stop_bits = stop_bits
        self.data_bits = data_bits
        self.timeout = timeout

class Serial:
    """
    The serial protocol handler
    """
    def __init__(self, protocol):
        """
        :param protocol: the protocol definition
        :type protocol: SerialProtocol
        """
        self._protocol = protocol

        self._logger = logging.getLogger(__name__)
        self._logger.debug("protocol=%s", protocol)

        self._port = self._protocol.port
        if self._protocol.port == "loop":
            self._port = "loop://" # special pySerial port

        self._parity = serial.PARITY_NONE
        if self._protocol.parity == 'odd':
            self._parity = serial.PARITY_ODD
        elif self._protocol.parity == 'even':
            self._parity = serial.PARITY_EVEN
        elif self._protocol.parity == 'none':
            self._parity = serial.PARITY_NONE
        else:
            raise NotImplementedError("parity version not suppoted")

        self._data_bits = serial.FIVEBITS
        if self._protocol.data_bits == 5:
            self._data_bits = serial.FIVEBITS
        elif self._protocol.data_bits == 6:
            self._data_bits = serial.SIXBITS
        elif self._protocol.data_bits == 7:
            self._data_bits = serial.SEVENBITS
        elif self._protocol.data_bits == 8:
            self._data_bits = serial.EIGHTBITS
        else:
            raise ValueError("data bits value not suppoted")

        self._stop_bits = serial.STOPBITS_ONE
        if self._protocol.stop_bits == 1.0:
            self._stop_bits = serial.STOPBITS_ONE
        elif self._protocol.stop_bits == 1.5:
            self._stop_bits = serial.STOPBITS_ONE_POINT_FIVE
        elif self._protocol.stop_bits == 2.0:
            self._stop_bits = serial.STOPBITS_TWO
        else:
            raise ValueError("stop bits value not suppoted")

    def send_command(self, commands, stream=None):
        """
        Send commands through the serial port.
        :param commands: the commands to send
        :type commands: list(str)
        :param stream: the command stream handler
        :type stream: CommandStream
        :raises: ExecCommandError
        """
        self._logger.debug("execute commands using 'serial' protocol")
        self._logger.debug("commands=%s", commands)

        retvalues = []

        sio = None
        ser = None
        try:
            ser = serial.serial_for_url(self._port, \
                        self._protocol.baudrate, \
                        self._data_bits, \
                        self._parity, \
                        self._stop_bits, \
                        timeout=self._protocol.timeout)

            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
        except serial.SerialException as ex:
            raise SerialConnectionError("%s"%ex)

        for command in commands:
            self._logger.debug("executing command '%s'", command)

            # notify command execution
            if stream:
                stream.cmd_executing(command)

            # return value is the last line of the serial command output
            retvalue = ""

            try:
                sio.write(command)

                while True:
                    sio.flush()
                    line = sio.readline()

                    # notify line has been acquired
                    if stream:
                        stream.handle_stdout_line(line)

                    if line:
                        retvalue = line
                        break

                # notify command completion
                if stream:
                    stream.cmd_completed(retvalue)
            except IOError as ex:
                raise ExecCommandError("%s"%ex) from ex
            finally:
                sio.close()
                ser.close()

            retvalues.append(retvalue)

        return retvalues
