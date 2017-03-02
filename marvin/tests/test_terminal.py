"""
.. module:: test_terminal
   :platform: Unix
   :synopsis: terminal module unittest.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

from marvin.terminal import TerminalWriter
from marvin.tests.test_events import TestCoreEvents

class TestTerminalWriter(TestCoreEvents):
    """ test TestWriter class """
    def test_listen(self):
        """ test the listen method """
        terminal = TerminalWriter()
        self.assertFalse(terminal.listen(self.events))
        self.test_events()
