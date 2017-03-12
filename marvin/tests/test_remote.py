"""
.. module:: test_remote
   :platform: Unix
   :synopsis: Unittests for the remote module.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

import os
import sys
import shutil
import unittest
from marvin.remote import OpenSSH
from marvin.remote import OpenSSHProtocol
from marvin.remote import Serial
from marvin.remote import SerialProtocol
from marvin.remote import SFTPProtocol
from marvin.remote import DataItem
from marvin.remote import CommandStream
from marvin.errors import SSHConnectionError
from marvin.errors import RemotePathNotExistError
from marvin.errors import LocalPathNotExistError
from marvin.errors import SerialConnectionError

class TestRemote(unittest.TestCase):
    """ Test the remote module """

    @classmethod
    def setUpClass(cls):
        # local data
        cls.currdir = os.path.dirname(os.path.abspath(__file__))
        cls.localdir = os.path.join(cls.currdir, "testdir")
        cls.nesteddir = os.path.join(cls.localdir, "nesteddir")
        cls.localfiles = [
            os.path.join(cls.localdir, "toremove0.txt"),
            os.path.join(cls.localdir, "toremove1.txt"),
            os.path.join(cls.localdir, "toremove2.txt"),
            os.path.join(cls.localdir, "toremove3.txt")
        ]

        if not os.path.isdir(cls.localdir):
            os.mkdir(cls.localdir)

        if not os.path.isdir(cls.nesteddir):
            os.mkdir(cls.nesteddir)

        for item in cls.localfiles:
            with open(item, 'a') as fhandler:
                fhandler.write("created by remote unittest")

        # remote data
        cls.home = os.environ['HOME']
        cls.remotedir = os.path.join(cls.home, "testdir")
        cls.commands = ["test -d /", "test -d /dsajkdlsad"]

    @classmethod
    def tearDownClass(cls):
        if os.path.isdir(cls.remotedir):
            shutil.rmtree(cls.remotedir)

        if os.path.isdir(cls.localdir):
            shutil.rmtree(cls.localdir)

    def _from_host_to_target(self, src, dst):
        srcdir = os.path.dirname(src)
        self.assertEqual(self.localdir, srcdir)

        dstdir = os.path.dirname(dst)
        self.assertEqual(self.remotedir, dstdir)

    def _from_target_to_host(self, src, dst):
        srcdir = os.path.dirname(src)
        self.assertEqual(self.remotedir, srcdir)

        dstdir = os.path.dirname(dst)
        self.assertEqual(self.localdir, dstdir)

    def _test_removing_dir(self, path):
        self.assertEqual(self.remotedir, path)

    @staticmethod
    def _print_status(curr_bytes, tot_bytes):
        sys.stdout.write("%s/%s Bytes"%(curr_bytes, tot_bytes))

    def test_sftp_transfer(self):
        """ test sftp_transfer function """
        protocol = SFTPProtocol(
            "localhost", 22,
            "", "",
            2.0
        )

        ssh = OpenSSH(protocol)

        # from host to target
        data_remote = [DataItem(self.localdir, self.remotedir, "remote")]
        self.assertFalse(ssh.sftp_transfer(data_remote, \
            self._from_host_to_target))

        # remove local data
        self.assertTrue(os.path.isdir(self.localdir))
        shutil.rmtree(self.localdir)

        # from target to host
        data_local = [DataItem(self.remotedir, self.localdir, "local")]
        self.assertFalse(ssh.sftp_transfer(data_local, \
            self._from_target_to_host))

        # remove remote data
        self.assertFalse(ssh.sftp_remove([self.remotedir], \
            self._test_removing_dir))

        self.assertFalse(os.path.exists(self.remotedir))

    def test_sftp_path_not_exist_error(self):
        """ test transferring a path that does not exist """
        protocol = SFTPProtocol(
            "localhost", 22,
            "", "",
            2.0
        )

        ssh = OpenSSH(protocol)

        with self.assertRaises(LocalPathNotExistError):
            item = DataItem("this_src_does_not_exist", "", "remote")
            ssh.sftp_transfer([item])

        with self.assertRaises(RemotePathNotExistError):
            item = DataItem("this_src_does_not_exist", "", "local")
            ssh.sftp_transfer([item])

    def _test_execute_callback(self, command, stdout, stderr):
        self.assertIn(command, self.commands)
        self.assertIsNotNone(stdout)
        self.assertIsNotNone(stderr)

    def _create_stream(self, commands, results):
        class StreamTester(CommandStream):
            """ CommandStream tester """
            def __init__(self, tester, commands, results):
                self._tester = tester
                self._commands = commands
                self._results = results

            def cmd_executing(self, command):
                self._tester.assertIn(command, self._commands)

            def handle_stdout_line(self, line):
                self._tester.assertIsNotNone(line)

            def cmd_completed(self, result):
                self._tester.assertIn(result, self._results)

        stream = StreamTester(self, commands, results)
        return stream

    def test_ssh_execute(self):
        """ test ssh_execute function """
        protocol = OpenSSHProtocol(
            "localhost", 22,
            "", "",
            2.0
        )

        ssh = OpenSSH(protocol)

        results = ["0", "1"]
        stream = self._create_stream(self.commands, results)
        self.assertEqual(ssh.ssh_execute(self.commands, stream), results)

    def test_ssh_address_error(self):
        """ test a SSH address wrong assignment """
        protocol = OpenSSHProtocol(
            "this_host_does_not_exist", 22,
            "", "",
            2.0
        )

        ssh = OpenSSH(protocol)
        with self.assertRaises(SSHConnectionError):
            ssh.ssh_execute("ls")

    def test_ssh_port_error(self):
        """ test a SSH port wrong assignment """
        protocol = OpenSSHProtocol(
            "localhost", 2200,
            "", "",
            2.0
        )

        ssh = OpenSSH(protocol)
        with self.assertRaises(SSHConnectionError):
            ssh.ssh_execute("ls")

    def test_ssh_user_error(self):
        """ test a SSH user wrong assignment """
        protocol = OpenSSHProtocol(
            "localhost", 22,
            "this_user_does_not_exist", "",
            2.0
        )

        ssh = OpenSSH(protocol)
        with self.assertRaises(SSHConnectionError):
            ssh.ssh_execute("ls")

    def test_serial_execute(self):
        """ test serial command execution """
        protocol = SerialProtocol(
            "loop",
            91200,
            'odd',
            1,
            5,
            1
        )

        serial = Serial(protocol)

        # we are using "loop" port, so commands == results
        commands = ["ciao_0", "ciao_1"]
        stream = self._create_stream(commands, commands)
        self.assertEqual(serial.send_command(commands, stream), commands)

    def test_serial_port_error(self):
        """ test a wrong serial port """
        protocol = SerialProtocol(
            "/dev/this_port_does_not_exist",
            91200,
            'odd',
            1,
            5,
            1
        )

        serial = Serial(protocol)
        with self.assertRaises(SerialConnectionError):
            serial.send_command("something")
