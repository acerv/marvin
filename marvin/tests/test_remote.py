"""
.. module:: test_remote
   :platform: Unix
   :synopsis: Unittests for the remote module.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

import os
import sys
import unittest
from marvin.remote import OpenSSH
from marvin.remote import OpenSSHProtocol
from marvin.remote import SFTPProtocol
from marvin.remote import DataItem

class TestRemote(unittest.TestCase):
    """ Test the remote module """

    @classmethod
    def setUpClass(cls):
        cls.currdir = os.path.dirname(os.path.abspath(__file__))
        cls.localfile = os.path.join(cls.currdir, 'testfile.txt')
        cls.home = os.environ['HOME']
        cls.remotefile = os.path.join(cls.home, "testfile.txt")
        cls.commands = ["test -d /", "test -d /dsajkdlsad"]

        with open(cls.localfile, 'a') as fhandler:
            fhandler.write('created by remote unittest')

        cls.remotestoremove = [
            os.path.join(cls.home, "toremove0.txt"),
            os.path.join(cls.home, "toremove1.txt"),
            os.path.join(cls.home, "toremove2.txt"),
            os.path.join(cls.home, "toremove3.txt")
        ]

        for item in cls.remotestoremove:
            with open(item, 'a') as fhandler:
                fhandler.write("created by remote unittest")

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.localfile)
        os.remove(cls.remotefile)

        for item in cls.remotestoremove:
            if os.path.exists(item):
                os.remove(item)

    def _from_local_to_target(self, src, dst):
        self.assertEqual(src, self.localfile)
        self.assertEqual(dst, self.remotefile)

    def _from_target_to_local(self, src, dst):
        self.assertEqual(src, self.remotefile)
        self.assertEqual(dst, self.localfile)

    @staticmethod
    def _print_status(curr_bytes, tot_bytes):
        sys.stdout.write("%s/%s Bytes"%(curr_bytes, tot_bytes))

    def _test_removing_item(self, item):
        self.assertIn(item, self.remotestoremove)
        self.assertTrue(os.path.exists(item))

    def test_sftp_remove(self):
        """ test sftp_remove function """
        protocol = SFTPProtocol(
            "localhost", 22,
            "", "",
            2.0
        )

        ssh = OpenSSH(protocol)

        self.assertFalse(ssh.sftp_remove(self.remotestoremove, \
            self._test_removing_item))

    def test_sftp_transfer(self):
        """ test sftp_transfer function """
        protocol = SFTPProtocol(
            "localhost", 22,
            "", "",
            2.0
        )

        ssh = OpenSSH(protocol)

        # from host to target
        data_remote = [DataItem(self.localfile, self.remotefile, "remote")]
        self.assertFalse(ssh.sftp_transfer(data_remote, \
            self._from_local_to_target))

        # from target to host
        data_local = [DataItem(self.remotefile, self.localfile, "local")]
        self.assertFalse(ssh.sftp_transfer(data_local, \
            self._from_target_to_local))

    def _test_execute_callback(self, command, stdout, stderr):
        self.assertIn(command, self.commands)
        self.assertIsNotNone(stdout)
        self.assertIsNotNone(stderr)

    def test_ssh_execute(self):
        """ test ssh_execute function """
        protocol = OpenSSHProtocol(
            "localhost", 22,
            "", "",
            2.0
        )

        ssh = OpenSSH(protocol)

        self.assertEqual(ssh.ssh_execute(self.commands, \
            self._test_execute_callback), [0, 1])
