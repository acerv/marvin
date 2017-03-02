"""
.. module:: report
   :platform: Unix
   :synopsis: A module handling test report.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

import os
import re

# pylint: disable=too-few-public-methods
# pylint: disable=anomalous-backslash-in-string

class ReportDirectory(object):
    """
    The report directory
    """
    def __init__(self, root, localdata, remotedata):
        """
        :param root: the report directory
        :type root: str
        :param localdata: where local data are stored before sending them
            to the target
        :type localdata: str
        :param remotedata: where remote data is stored after fetching it from
            the target
        :type remotedata: str
        """
        self.root = root
        self.localdata = localdata
        self.remotedata = remotedata

def create_test_report_dir(reportsdir, testname, testver):
    """
    Create the directory where report is saved.

    :param reportsdir: the directory where creating test report directory
    :type reportsdir: str
    :param testname: the test name
    :type testname: str
    :param testver: the test version
    :type testver: str
    :raises: ValueError
    :returns: ReportDirectory object
    """
    if not reportsdir or not os.path.exists(reportsdir):
        raise ValueError("'%s' directory does not exist"%reportsdir)

    if not testname:
        raise ValueError("'testname' is empty")

    if not testver:
        raise ValueError("'testver' is empty")

    # get the report prefix
    import uuid
    prefix_str = uuid.uuid4()

    # remove wrong path characters and replace tham with '_'
    test_name = re.sub('[^\w\-_\. ]', '_', testname)
    test_ver = re.sub('[^\w\-_\. ]', '_', testver)
    test_report_dir_name = "%s-%s-%s" % (test_name, test_ver, prefix_str)

    # create the report directory
    reportsdir_abs = os.path.abspath(reportsdir)
    test_report_dir = os.path.join(reportsdir_abs, test_report_dir_name)

    os.mkdir(test_report_dir)

    # create local and remote data directories
    data_path = os.path.join(test_report_dir, 'data')
    local_data_path = os.path.join(data_path, 'local')
    remote_data_path = os.path.join(data_path, 'remote')

    os.mkdir(data_path)
    os.mkdir(local_data_path)
    os.mkdir(remote_data_path)

    # create the report directory object
    reportdir = ReportDirectory(\
        test_report_dir,
        local_data_path,
        remote_data_path)

    return reportdir
