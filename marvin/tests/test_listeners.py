"""
.. module:: test_listeners
   :platform: Unix
   :synopsis: Unittests for the listeners module.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

from marvin.listeners import EventsListener
from marvin.tests.test_events import TestCoreEvents

class TestListeners(TestCoreEvents):
    """ test EventsListener class """
    def test_logs_listen(self):
        """ test the listen method """
        report = EventsListener("logs")
        self.assertFalse(report.listen(self.events))
        self.test_events()

    def test_terminal_listen(self):
        """ test the listen method """
        report = EventsListener("terminal")
        self.assertFalse(report.listen(self.events))
        self.test_events()

    def test_junit_listen(self):
        """ test the listen method """
        report = EventsListener("junit")
        self.assertFalse(report.listen(self.events))
        self.test_events()
