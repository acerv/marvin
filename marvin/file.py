"""
.. module:: file
   :platform: Unix
   :synopsis: A module handling test files.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

import os
import logging
import yaml
from marvin.errors import FileNotSupported
from marvin.errors import FileParseError
from pykwalify.core import Core
from pykwalify.errors import PyKwalifyException

def load(testfile):
    """
    It loads a test file.

    :param testfile: the file path of the test
    :type testfile: str
    :returns: dict representing the test file
    """
    if not testfile:
        raise ValueError("'testfile' is empty")

    logger = logging.getLogger(__name__)
    logger.debug("loading file '%s'", testfile)

    file_def = {}
    file_name, file_ext = os.path.splitext(testfile)

    logger.debug("filename=%s, extension=%s", file_name, file_ext)

    if file_ext == '.yml' or file_ext == '.yaml':
        try:
            currdir = os.path.abspath(os.path.dirname(__file__))
            schemafile = os.path.join(currdir, "files", "schema.yml")
            validator = Core(source_file=testfile, schema_files=[schemafile])
            validator.validate(raise_exception=True)
        except PyKwalifyException as ex:
            raise FileParseError(ex.msg)

        with open(testfile, 'r') as stream:
            file_def = yaml.load(stream)
    else:
        raise FileNotSupported("'%s' file type is not supported"%file_ext)

    return file_def
