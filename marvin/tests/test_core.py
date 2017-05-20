"""
.. module:: test_core
   :platform: Unix
   :synopsis: The unittest for the core module.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

import os
import shutil
import unittest
from marvin.core import Core
from marvin.errors import FileParseError
from marvin.errors import LocalPathNotExistError
from marvin.errors import RemotePathNotExistError

class TestTester(unittest.TestCase):
    """ The tester unittest definition """

    @classmethod
    def setUpClass(cls):
        cls.currdir = os.path.abspath(os.path.dirname(__file__))
        cls.reportsdir = os.path.join(cls.currdir, "reports")
        cls.homedir = os.environ['HOME']
        cls.remotefile = os.path.join(cls.homedir, "testfile.txt")

        if not os.path.exists(cls.reportsdir):
            os.mkdir(cls.reportsdir)

        with open(cls.remotefile, 'a') as file:
            file.write("")

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.reportsdir):
            shutil.rmtree(cls.reportsdir)

        if os.path.exists(cls.remotefile):
            os.remove(cls.remotefile)

    def test_core_deploy_failure(self):
        """ Test if FileParseError is raised when core is bad formatted """
        testfile = os.path.join(self.currdir, "files", "failure", "deploy.yml")
        with self.assertRaises(FileParseError):
            core = Core()
            core.load(testfile, self.reportsdir)

    def test_deploy_localpath_failure(self):
        """ Test if LocalPathNotExistError is raised when localpath doesn't exist """
        testfile = os.path.join(self.currdir, "files", "failure", "local_path.yml")
        with self.assertRaises(LocalPathNotExistError):
            core = Core()
            core.load(testfile, self.reportsdir)
            core.deploy.run()

    def test_core_deploy_success(self):
        """ Test deploy stage when it success """
        testfile = os.path.join(self.currdir, "files", "success", "deploy.yml")
        core = Core()
        core.load(testfile, self.reportsdir)

        self.assertIsNotNone(core.deploy)
        self.assertFalse(core.deploy.run())
        self.assertFalse(core.deploy.cleanup())

    def test_core_execute_failure(self):
        """ Test if FileParseError is raised when execute is wrong """
        testfile = os.path.join(self.currdir, "files", "failure", "execute.yml")
        with self.assertRaises(FileParseError):
            core = Core()
            core.load(testfile, self.reportsdir)

    def test_core_execute_success(self):
        """ Test execute stage when it success """
        testfile = os.path.join(self.currdir, "files", "success", "execute.yml")
        core = Core()
        core.load(testfile, self.reportsdir)

        self.assertIsNotNone(core.execute)
        self.assertFalse(core.execute.run())

    def test_core_collect_failure(self):
        """ Test if FileParseError is raised when collect is bad formatted """
        testfile = os.path.join(self.currdir, "files", "failure", "collect.yml")
        with self.assertRaises(FileParseError):
            core = Core()
            core.load(testfile, self.reportsdir)

    def test_collect_remotepath_failure(self):
        """ Test if RemotePathNotExistError is raised when remote path doesn't exist """
        testfile1 = os.path.join(self.currdir, "files", "failure", "remote_path.yml")
        with self.assertRaises(RemotePathNotExistError):
            core = Core()
            core.load(testfile1, self.reportsdir)
            core.collect.run()

    def test_core_collect_success(self):
        """ Test collect stage when it success """
        testfile = os.path.join(self.currdir, "files", "success", "collect.yml")
        core = Core()
        core.load(testfile, self.reportsdir)

        self.assertIsNotNone(core.collect)
        self.assertFalse(core.collect.run())
