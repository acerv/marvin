"""
.. module:: listeners
   :platform: Unix
   :synopsis: The module defines the events listeners
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

import os
import sys
import shutil
import time
import datetime
import colorama
from colorama import Fore, Style
from junit_xml import TestCase, TestSuite

class GenericEventsListener:
    """
    A generic report writer.
    """

    def listen(self, events):
        """
        Listen to the core events and attach to its event handlers.

        :param events: The events to listen to
        :type events: CoreEvents
        """
        raise NotImplementedError("Inherit the class and implement this method")

class EventsListener:
    """
    Listen to the core events and do something, depending on initialization
    """

    def __new__(cls, name):
        """
        Create a listener instance.

        :param name: the listener name. Supported writers are the following:
            * logs: listen to the core events and write a log file in the reports
                directory
            * terminal: listen to the core events and print them in the stdout
            * junit: listen to the core events and write a junit file in the reports
                directory
        :type name: str
        :returns: GenericEventsListener object
        """
        writer = None

        if name is "logs":
            writer = LogsWriter()
        elif name is "terminal":
            writer = TerminalWriter()
        elif name is "junit":
            writer = JUnitWriter()

        return writer

    def listen(self, events):
        """
        Forward declaration for GenericEventsListener
        """
        raise NotImplementedError()

class LogsWriter(GenericEventsListener):
    """
    Write core events inside a plain-text file in the report directory
    """
    def __init__(self):
        self._reportdir = None
        self._freport = None
        self._testfile = None

    def listen(self, events):
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
        events.executeStreamLine += self._print_exec_line
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

    def _print_exec_command(self, command):
        self._write_file("executing '%s'...\n"%command)

    def _print_exec_line(self, line):
        self._write_file(line)

    def _print_exec_result(self, passing, failing, result):
        if result == passing:
            self._write_file("PASSED (%s)\n"%(result))
        elif result == failing:
            self._write_file("FAILED (%s)\n"%(result))
        else:
            self._write_file("UNKNOWN (%s)\n"%(result))

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

class TerminalWriter(GenericEventsListener):
    """
    Write on terminal the events
    """
    def __init__(self):
        self._stdout = sys.stdout
        self._last_progress = None

    def listen(self, events):
        # initialize colorama for multiplatform support
        colorama.init()

        # register loading callbacks
        events.readFileStarted += self._print_read_file_started
        events.readFileCompleted += self._print_read_file_completed
        events.createReportDirStarted += self._print_reportsdir
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
        events.deployCompleted += self._print_deploy_completed
        events.dataTransfer += self._print_data_transfer
        events.dataTransferProgress += self._print_data_transfer_progress
        events.cleanupTargetStarted += self._print_cleanup_started
        events.cleanupTargetPath += self._print_cleanup_target_path
        events.cleanupTargetCompleted += self._print_cleanup_completed
        events.executeStarted += self._print_execute_started
        events.executeCompleted += self._print_execute_completed
        events.executeCommandStarted += self._print_exec_command
        #events.executeStreamLine += self._print_stream_line
        events.executeCommandCompleted += self._print_exec_result
        events.collectStarted += self._print_collect_started
        events.collectCompleted += self._print_collect_completed

        # register exception callback
        events.exceptionCatched += self._print_exception

    def _print_exception(self, ex):
        self._stdout.write(Fore.LIGHTRED_EX)
        self._stdout.write("\n\n%s"%ex)
        self._stdout.write(Fore.RESET)
        self._stdout.write("\n\n")

    def _print_ok(self):
        self._stdout.write(Fore.LIGHTGREEN_EX+"OK\n"+Fore.RESET)

    def _print_fail(self):
        self._stdout.write(Fore.LIGHTRED_EX+"FAIL\n"+Fore.RESET)

    def _print_read_file_started(self, testfile):
        self._stdout.write("\n")
        self._stdout.write(Style.BRIGHT+"Reading...\n"+Style.RESET_ALL)
        self._stdout.write("loading '%s'..."%testfile)

    def _print_read_file_completed(self, testdef):
        if testdef:
            self._print_ok()
        else:
            self._print_fail()

    def _print_reportsdir(self, reportsdir):
        self._stdout.write("reports: %s\n"%os.path.abspath(reportsdir))

    def _print_reportdir(self, reportdir):
        self._stdout.write("report: %s\n"%reportdir.root)

    def _print_protocol_name(self, name):
        self._stdout.write("protocol '%s':\n"%name)

    def _print_protocol_definition(self, protocol):
        for key, value in protocol.items():
            self._stdout.write("    %s: %s\n"%(key, value))

    ############# EXECUTE STAGE ##############
    def _print_execute_started(self):
        self._stdout.write("\n")
        self._stdout.write(Style.BRIGHT+"Execute started\n"+Style.RESET_ALL)

    def _print_execute_completed(self):
        pass

    def _print_read_execute_started(self):
        self._stdout.write("reading 'execute' stage...")

    def _print_read_execute_completed(self, executedef):
        if executedef:
            self._print_ok()
        else:
            self._print_fail()

    def _print_exec_command(self, command):
        self._stdout.write("executing '%s'..."%command)

    def _print_exec_result(self, passing, failing, result):
        if result == passing:
            self._stdout.write("%sPASSED (%s)%s\n"%\
                (Fore.LIGHTGREEN_EX, result, Fore.RESET))
        elif result == failing:
            self._stdout.write("%sFAILED (%s)%s\n"%\
                (Fore.LIGHTRED_EX, result, Fore.RESET))
        else:
            self._stdout.write("%sUNKNOWN (%s)%s\n"%\
                (Fore.LIGHTBLUE_EX, result, Fore.RESET))

    ############# DEPLOY/COLLECT STAGE ##############
    def _print_deploy_started(self):
        self._stdout.write("\n")
        self._stdout.write(Style.BRIGHT+"Deploy started"+Style.RESET_ALL)
        self._last_progress = ""

    def _print_deploy_completed(self):
        self._stdout.write("\n")
        self._last_progress = ""

    def _print_collect_started(self):
        self._stdout.write("\n")
        self._stdout.write(Style.BRIGHT+"Collect started"+Style.RESET_ALL)
        self._last_progress = ""

    def _print_collect_completed(self):
        self._stdout.write("\n")
        self._last_progress = ""

    def _print_read_deploy_started(self):
        self._stdout.write("reading 'deploy' stage...")

    def _print_read_deploy_completed(self, deploydef):
        if deploydef:
            self._print_ok()
        else:
            self._print_fail()

    def _print_read_collect_started(self):
        self._stdout.write("reading 'collect' stage...")

    def _print_read_collect_completed(self, collectdef):
        if collectdef:
            self._print_ok()
        else:
            self._print_fail()

    def _print_data_transfer(self, source, destination):
        self._last_progress = ""
        self._stdout.write("\n%s -> %s..."%\
            (os.path.basename(source), destination))
        self._stdout.flush()

    def _print_data_transfer_progress(self, current, total):
        if self._last_progress:
            self._stdout.write("\b"*len(self._last_progress))
            self._stdout.flush()

        self._last_progress = "%s/%s Bytes"%(current, total)
        self._stdout.write(self._last_progress)
        self._stdout.flush()

    def _print_cleanup_target_path(self, path):
        self._stdout.write("removing %s...\n"%path)

    def _print_cleanup_started(self):
        self._stdout.write("\n")
        self._stdout.write(Style.BRIGHT+"Cleaning up\n"+Style.RESET_ALL)

    def _print_cleanup_completed(self):
        self._stdout.write("\n")

class JUnitWriter(GenericEventsListener):
    """
    Listen to the core events and write a JUnit report
    """
    def __init__(self):
        self._test_cases = []
        self._current_command = None
        self._test_suite = None
        self._reportdir = None
        self._junitfile = None
        self._cmd_stdout = ""
        self._filename = None
        self._start_time = None

    def listen(self, events):
        events.readFileStarted += self._save_filename
        events.createReportDirCompleted += self._save_reportdir
        events.executeCommandStarted += self._save_command_name
        events.executeStreamLine += self._save_command_streamline
        events.executeCommandCompleted += self._create_test_case
        events.testCompleted += self._write_junit_file

    ###########################################
    # SAVE INFORMATIONS
    ###########################################
    def _save_filename(self, name):
        self._filename = name

    def _save_reportdir(self, reportdir):
        self._junitfile = os.path.join(reportdir.root, "report.xml")
        self._reportdir = reportdir

    def _save_command_name(self, command):
        self._start_time = time.time()
        self._current_command = command

        # reset command stdout
        self._cmd_stdout = ""

    def _save_command_streamline(self, line):
        self._cmd_stdout += line

    ###########################################
    # CREATE JUnit FILE
    ###########################################
    def _create_test_case(self, passing, failing, result):
        test_case = None

        elapsed_time = time.time() - self._start_time

        if result == failing:
            test_case = TestCase(self._current_command, \
                stderr=self._cmd_stdout, elapsed_sec=elapsed_time)
            test_case.add_failure_info("result=%s"%result)
        else:
            test_case = TestCase(self._current_command, \
                stdout=self._cmd_stdout, elapsed_sec=elapsed_time)

        self._test_cases.append(test_case)

    def _write_junit_file(self):
        test_suite = TestSuite(self._filename, self._test_cases, \
            timestamp=datetime.datetime.now())

        with open(self._junitfile, 'w') as junitfile:
            TestSuite.to_file(junitfile, [test_suite])
