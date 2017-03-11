"""
.. module:: errors
   :platform: Unix
   :synopsis: A module containing errors.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

class FileNotSupported(Exception):
    """
    This exception is raised when a test file is not supported.
    """
    pass

class FileParseError(Exception):
    """
    This exception is raised when a test file can't be parsed.
    """
    pass

class RemotePathNotExistError(Exception):
    """
    This exception is raised when a target remote path doesn't exist.
    """
    pass

class LocalPathNotExistError(Exception):
    """
    This exception is raised when a local path to transfer doesn't exist.
    """
    pass

class SSHConnectionError(Exception):
    """
    This exception is raised when there's an error connecting to the target
    using the openssh protocol.
    """
    pass

class SerialConnectionError(Exception):
    """
    This exception is raised when there's an error connecting to a serial port.
    """
    pass

class ExecCommandError(Exception):
    """
    This exception is raised when there's an error when executing commands.
    """
    pass
