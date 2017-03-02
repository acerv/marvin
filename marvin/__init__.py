"""
.. module:: __init__
   :platform: Unix
   :synopsis: The marvin library.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

__all__ = ["core", "errors", "terminal"]

import os
import logging
import yaml

def init_logging(debug):
    """
    Initialize the logging module.
    :param debug: if True, the package will be configured to generate a debug
        logging file
    :type debug: bool
    """
    # get the logging configuration file
    current_dir = os.path.dirname(os.path.realpath(__file__))
    logging_conf_file = os.path.join("files", "normal.yml")
    if debug:
        logging_conf_file = os.path.join("files", "debug.yml")

    # load logging configuration file
    logging_conf = os.path.join(current_dir, logging_conf_file)
    with open(logging_conf) as fconfig:
        logging_dict = yaml.load(fconfig)
        logging.config.dictConfig(logging_dict)
