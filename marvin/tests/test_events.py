"""
.. module:: test_events
   :platform: Unix
   :synopsis: events module unittest.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

import os
import time
import shutil
import unittest
import marvin.file
import marvin.report
from marvin.events import CoreEvents

class DummyStream:
    """ a dummy stream to test events case """
    def write(self, msg):
        """ write on buffer """
        pass
    def read(self):
        """ read a byte from buffer """
        pass
    def readline(self):
        """ read a line from buffer """
        pass

class TestCoreEvents(unittest.TestCase):
    """ Test CoreEvents class """
    @classmethod
    def setUpClass(cls):
        cls._currpath = os.path.abspath(os.path.dirname(__file__))
        cls._reportsdir = os.path.join(cls._currpath, "reports")

        if not os.path.exists(cls._reportsdir):
            os.mkdir(cls._reportsdir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._reportsdir)

    def setUp(self):
        self.testfile = os.path.join(self._currpath, "files", "events.yml")
        self.testdef = marvin.file.load(self.testfile)
        self.events = CoreEvents()

    def test_events(self):
        """ simulate Core events """
        # loading test file
        self.assertFalse(self.events.readFileStarted(self.testfile))
        self.assertFalse(self.events.readFileCompleted(self.testdef))

        # create reports directory
        self.assertFalse(self.events.createReportDirStarted(self._reportsdir))
        reportdir = marvin.report.create_test_report_dir(\
            self._reportsdir,\
            self.testdef['name'],\
            self.testdef['version'])
        self.assertFalse(self.events.createReportDirCompleted(reportdir))

        # loading stages informations
        self.assertFalse(self.events.readProtocolStarted("sftp"))
        self.assertFalse(self.events.readProtocolCompleted(
            self.testdef["protocols"]["sftp"]))
        self.assertFalse(self.events.readDeployStarted())
        self.assertFalse(self.events.readDeployCompleted(\
            self.testdef["deploy"]))
        self.assertFalse(self.events.readExecuteStarted())
        self.assertFalse(self.events.readExecuteCompleted(\
            self.testdef["execute"]))
        self.assertFalse(self.events.readCollectStarted())
        self.assertFalse(self.events.readCollectCompleted(\
            self.testdef["collect"]))

        # start deploy
        self.assertFalse(self.events.deployStarted())
        for data in self.testdef["deploy"]["transfer"]:
            self.assertFalse(self.events.dataTransfer(\
                data["source"],
                data["dest"]))
            for i in range(0, 10):
                time.sleep(0.05)
                self.assertFalse(self.events.dataTransferProgress(i, 10))
        self.assertFalse(self.events.deployCompleted())

        #start execute
        self.assertFalse(self.events.executeStarted())
        for command in self.testdef["execute"]["commands"]:
            # simulate output stream
            stdout = DummyStream()
            stderr = DummyStream()
            self.assertFalse(self.events.executeCommandStarted(\
                command["script"], stdout, stderr))
            self.assertFalse(self.events.executeCommandCompleted(\
                command["script"], \
                command["passing"], \
                command["failing"], \
                "0"))
        self.assertFalse(self.events.executeCompleted())

        # collect deploy
        self.assertFalse(self.events.collectStarted())
        for data in self.testdef["collect"]["transfer"]:
            self.assertFalse(self.events.dataTransfer(\
                data["source"],
                data["dest"]))
            for i in range(0, 10):
                time.sleep(0.2)
                self.assertFalse(self.events.dataTransferProgress(i, 10))
        self.assertFalse(self.events.collectCompleted())
