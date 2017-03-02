#!/usr/bin/env python

"""
.. module:: setup
   :platform: Unix
   :synopsis: The Marvin installer module.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

from distutils.core import setup

setup(name='marvin',
      version='1.0',
      description='Remote test framework',
      author='Andrea Cervesato',
      author_email='andrea.cervesato@mailbox.org',
      packages=['marvin'],
      scripts=['bin/marvin']
     )
