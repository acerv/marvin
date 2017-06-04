"""
.. module:: events
   :platform: Unix
   :synopsis: The module defining events.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes

import logging

_logger = logging.getLogger(__name__)

class Event:
    """
    Generic event. A simple usage is the following:

        # create it
        event = Event()
        # hook it
        def handle_event(mydata):
            print(mydata)
        event += handle_event
        # fire it
        event(mydata)

    """
    def __init__(self):
        self._handlers = set()

    def __iadd__(self, handler):
        self._handlers.add(handler)
        return self

    def __isub__(self, handler):
        try:
            self._handlers.remove(handler)
        except:
            raise ValueError("'%s' is not currently handled", handler.__name__)
        return self

    def __call__(self, *args, **kargs):
        for handler in self._handlers:
            handler(*args, **kargs)

    def __len__(self):
        return len(self._handlers)

class CoreEvents:
    """ The set of Core events """

    def __init__(self):
        _logger.debug("creating core events")

        # opening/closing test events
        self.testStarted = Event()
        self.testCompleted = Event()

        # loading events
        self.readFileStarted = Event()
        self.readFileCompleted = Event()
        self.createReportDirStarted = Event()
        self.createReportDirCompleted = Event()
        self.readProtocolStarted = Event()
        self.readProtocolCompleted = Event()
        self.readDeployStarted = Event()
        self.readDeployCompleted = Event()
        self.readExecuteStarted = Event()
        self.readExecuteCompleted = Event()
        self.readCollectStarted = Event()
        self.readCollectCompleted = Event()

        # operation events
        self.deployStarted = Event()
        self.deployCompleted = Event()
        self.dataTransfer = Event()
        self.dataTransferProgress = Event()
        self.cleanupTargetStarted = Event()
        self.cleanupTargetPath = Event()
        self.cleanupTargetCompleted = Event()
        self.executeStarted = Event()
        self.executeStreamLine = Event()
        self.executeCompleted = Event()
        self.executeCommandStarted = Event()
        self.executeCommandCompleted = Event()
        self.collectStarted = Event()
        self.collectCompleted = Event()

        # exceptions events
        self.exceptionCatched = Event()
