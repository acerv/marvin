"""
.. module:: test_report
   :platform: Unix
   :synopsis: Unittests for the report module.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

import os
import shutil
import unittest
import marvin.report
from marvin.report import ReportWriter
from marvin.tests.test_events import TestCoreEvents

class TestReport(unittest.TestCase):
    """ Test the report module """
    @classmethod
    def setUpClass(cls):
        currdir = os.path.abspath(os.path.dirname(__file__))
        cls.reportsdir = os.path.join(currdir, "reports")
        os.mkdir(cls.reportsdir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.reportsdir)

    def test_create_report_dir(self):
        """ Test create_report_dir method """
        self.assertIsNotNone(marvin.report.create_test_report_dir( \
                self.reportsdir, \
                "test01", \
                "1.0"))

        reportdir = marvin.report.create_test_report_dir( \
            self.reportsdir, \
            "test01", \
            "1.0")

        self.assertTrue(os.path.isdir(reportdir.root))
        self.assertTrue(os.path.isdir(reportdir.localdata))
        self.assertTrue(os.path.isdir(reportdir.remotedata))

class TestReportWriter(TestCoreEvents):
    """ test ReportWriter class """
    def test_listen(self):
        """ test the listen method """
        report = ReportWriter()
        self.assertFalse(report.listen(self.events))
        self.test_events()
