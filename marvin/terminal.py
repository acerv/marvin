"""
.. module:: terminal
   :platform: Unix
   :synopsis: The module defining how to print out events coming from Core
              on terminal.
   :license: GPL3

.. moduleauthor:: Andrea Cervesato <andrea.cervesato@mailbox.org>
"""

import os
import sys
import colorama
from colorama import Fore, Style

class TerminalWriter:
    """ Write on terminal the Core events """
    def __init__(self, stdout=sys.stdout):
        self._stdout = stdout
        self._last_progress = None

    def listen(self, events):
        """
        :param core: the core instance
        :type core: Core
        """
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
        self._stdout.write(Fore.GREEN+"OK\n"+Fore.RESET)

    def _print_fail(self):
        self._stdout.write(Fore.RED+"FAIL\n"+Fore.RESET)

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

    def _print_exec_command(self, command, stdout, stdint):
        self._stdout.write("executing '%s'..."%command)

    def _print_exec_result(self, command, passing, failing, result):
        if result == passing:
            self._stdout.write("%sPASSED (%s)%s\n"%\
                (Fore.GREEN, result, Fore.RESET))
        elif result == failing:
            self._stdout.write("%sFAILED (%s)%s\n"%\
                (Fore.RED, result, Fore.RESET))
        else:
            self._stdout.write("%sUNKNOWN (%s)%s\n"%\
                (Fore.BLUE, result, Fore.RESET))

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
