"""
.. module:: report
   :platform: Unix
   :synopsis: A module handling test report.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

import os
import re
import shutil

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
    local_data_path = os.path.join(test_report_dir, 'local')
    remote_data_path = os.path.join(test_report_dir, 'remote')

    os.mkdir(local_data_path)
    os.mkdir(remote_data_path)

    # create the report directory object
    reportdir = ReportDirectory(\
        test_report_dir,
        local_data_path,
        remote_data_path)

    return reportdir

class ReportWriter:
    """
    Write the reports in the report directory
    """
    def __init__(self):
        self._reportdir = None
        self._freport = None
        self._testfile = None

    def listen(self, events):
        """
        Listen to the Core events, to log them in the report file.
        """
         # register loading callbacks
        events.readFileStarted += self._print_read_file_started
        events.createReportDirCompleted += self._print_reportdir
        events.readProtocolStarted += self._print_protocol_name
        events.readProtocolCompleted += self._print_protocol_definition
        events.readDeployStarted += self._print_read_deploy_started
        events.readDeployCompleted += self._print_read_deploy_completed
        events.readExecuteStarted += self._print_read_execute_started
        events.readExecuteCompleted += self._print_read_execute_completed
        events.readCollectStarted += self._print_read_collect_started
        events.readCollectCompleted += self._print_read_collect_completed

        # register operations callbacks
        events.deployStarted += self._print_deploy_started
        events.dataTransfer += self._print_data_transfer
        events.dataTransferProgress += self._print_data_transfer_progress
        events.cleanupTargetStarted += self._print_cleanup_started
        events.cleanupTargetPath += self._print_cleanup_target_path
        events.executeStarted += self._print_execute_started
        events.executeCommandStarted += self._print_exec_command
        events.executeCommandCompleted += self._print_exec_result
        events.collectStarted += self._print_collect_started

        # register exception callback
        events.exceptionCatched += self._print_exception

    def __del__(self):
        if self._freport:
            self._freport.close()

    def _write_file(self, text):
        if self._freport:
            self._freport.write(text)

    def _write_stream(self, stream):
        for line in iter(stream.readline, ""):
            self._write_file(line)

    def _print_exception(self, ex):
        self._write_file("\n\n%s"%ex)
        self._write_file("\n\n")

    def _print_ok(self):
        self._write_file("OK\n")

    def _print_fail(self):
        self._write_file("FAIL\n")

    def _print_read_file_started(self, testfile):
        self._testfile = testfile

    def _print_read_file_completed(self, testdef):
        if testdef:
            self._print_ok()
        else:
            self._print_fail()

    def _print_reportdir(self, reportdir):
        self._reportdir = reportdir

        self._freport = open(os.path.join(reportdir.root, "report.log"), "a")
        self._write_file("report: %s\n"%reportdir.root)

        test_copy = os.path.join(self._reportdir.root, \
            os.path.basename(self._testfile))
        shutil.copyfile(self._testfile, test_copy)

    def _print_protocol_name(self, name):
        self._write_file("protocol '%s':\n"%name)

    def _print_protocol_definition(self, protocol):
        for key, value in protocol.items():
            self._write_file("    %s: %s\n"%(key, value))

    def _print_execute_started(self):
        self._write_file("execute started...\n")

    def _print_read_execute_started(self):
        self._write_file("reading 'execute' stage...")

    def _print_read_execute_completed(self, executedef):
        if executedef:
            self._print_ok()
        else:
            self._print_fail()

    def _print_exec_command(self, command, stdout, stderr):
        self._write_file("executing '%s'...\n"%command)

        self._write_file("STDOUT:\n")
        self._write_stream(stdout)

        self._write_file("STDERR:\n")
        self._write_stream(stderr)

    def _print_exec_result(self, command, passing, failing, result):
        if result == passing:
            self._write_file("'%s' PASSED (%s)\n"%(command, result))
        elif result == failing:
            self._write_file("'%s' FAILED (%s)\n"%(command, result))
        else:
            self._write_file("'%s' UNKNOWN (%s)\n"%(command, result))

    def _print_deploy_started(self):
        self._write_file("deploy started...\n")

    def _print_collect_started(self):
        self._write_file("collect started...\n")

    def _print_cleanup_started(self):
        self._write_file("cleaning up...")

    def _print_read_deploy_started(self):
        self._write_file("reading 'deploy' stage...")

    def _print_read_deploy_completed(self, deploydef):
        if deploydef:
            self._print_ok()
        else:
            self._print_fail()

    def _print_read_collect_started(self):
        self._write_file("reading 'collect' stage...")

    def _print_read_collect_completed(self, collectdef):
        if collectdef:
            self._print_ok()
        else:
            self._print_fail()

    def _print_data_transfer(self, source, destination):
        self._write_file("transfer '%s' to '%s'..."%\
            (os.path.basename(source), destination))

    def _print_data_transfer_progress(self, current, total):
        pass

    def _print_cleanup_target_path(self, path):
        self._write_file("removing '%s'...\n"%path)
