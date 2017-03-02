"""
.. module:: test_remote
   :platform: Unix
   :synopsis: Unittests for the file module.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

import os
import unittest
import marvin.file
from marvin.errors import FileParseError
from marvin.errors import FileNotSupported

class TestYaml(unittest.TestCase):
    """
    Test the Yaml configuration.
    """

    def test_configuration_format(self):
        """
        This test check if the configuration module raises any error when the
        test file is bad formatted or not supported.
        """
        with self.assertRaises(FileNotSupported):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            marvin.file.load(os.path.join(\
                current_dir, 'files', 'not_supported.ini'))

        with self.assertRaises(FileParseError):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            marvin.file.load(os.path.join(\
                current_dir, 'files', 'bad_formatted.yml'))

    def test_configuration_content(self):
        """
        This test if the configuration module loads a test file without errors.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_def = marvin.file.load(os.path.join(\
            current_dir, 'files', 'simple.yml'))

        # header
        self.assertEqual(file_def['description'], 'A simple test Yaml configuration file.')
        self.assertEqual(file_def['name'], 'simple_test')
        self.assertEqual(file_def['version'], '1.0')
        self.assertEqual(file_def['author'], 'Andrea Cervesato')

        # protocols
        self.assertEqual(file_def['protocols']['sftp']['address'], 'localhost')
        self.assertEqual(file_def['protocols']['sftp']['port'], 22)
        self.assertEqual(file_def['protocols']['sftp']['user'], 'sshtest')
        self.assertEqual(file_def['protocols']['sftp']['password'], 'test')
        self.assertEqual(file_def['protocols']['sftp']['timeout'], 5.0)

        self.assertEqual(file_def['protocols']['ssh']['address'], 'localhost')
        self.assertEqual(file_def['protocols']['ssh']['port'], 22)
        self.assertEqual(file_def['protocols']['ssh']['user'], 'sshtest')
        self.assertEqual(file_def['protocols']['ssh']['password'], 'test')
        self.assertEqual(file_def['protocols']['ssh']['timeout'], 5.0)

        # deploy
        self.assertEqual(file_def['deploy']['protocol'], 'sftp')
        self.assertEqual(file_def['deploy']['delete'], True)
        self.assertEqual(file_def['deploy']['transfer'][0]['source'], 'setup.sh')
        self.assertEqual(file_def['deploy']['transfer'][0]['dest'], '/home/sshtest/setup.sh')
        self.assertEqual(file_def['deploy']['transfer'][0]['type'], 'file')

        # execute
        self.assertEqual(file_def['execute']['protocol'], 'ssh')
        self.assertEqual(file_def['execute']['commands'][0]['script'], \
            'chmod +x /home/sshtest/setup.sh')
        self.assertEqual(file_def['execute']['commands'][1]['script'], \
            '/home/sshtest/setup.sh')

        # collect
        self.assertEqual(file_def['collect']['protocol'], 'sftp')
        self.assertEqual(file_def['collect']['transfer'][0]['source'], \
            '/home/sshtest/marvin_testing/results.log')
        self.assertEqual(file_def['collect']['transfer'][0]['dest'], 'results.log')
