# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
#
# Notice of License - Duplicating this Notice of License near the start of any file containing
# a derivative of this software is a condition of license for this software.
# Friendly Licensing:
# No charge, open source royalty free use of the Neon AI software source and object is offered for
# educational users, noncommercial enthusiasts, Public Benefit Corporations (and LLCs) and
# Social Purpose Corporations (and LLCs). Developers can contact developers@neon.ai
# For commercial licensing, distribution of derivative works or redistribution please contact licenses@neon.ai
# Distributed on an "AS IS” basis without warranties or conditions of any kind, either express or implied.
# Trademarks of Neongecko: Neon AI(TM), Neon Assist (TM), Neon Communicator(TM), Klat(TM)
# Authors: Guy Daniels, Daniel McKnight, Regina Bloomstine, Elon Gasper, Richard Leeds
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2021: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

import os

from time import time, sleep

import psutil
from signal import SIGTERM
from threading import Event
from subprocess import Popen, STDOUT

import sys
from mycroft_bus_client import MessageBusClient, Message
from neon_utils.configuration_utils import get_neon_device_type
from neon_utils.log_utils import remove_old_logs, archive_logs, LOG_DIR, LOG, get_log_file_for_module
from typing.io import IO

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

run_log = open(os.path.join(LOG_DIR, "start.log"), "a+")
sys.stdout = run_log

LOG_FILES = {}
PROCESSES = {}
STOP_MODULES = Event()
STOP_MODULES.clear()
instance = time()
bus = MessageBusClient()


# TODO: Use core hash or something to validate these messages to restart/kill modules DM
def handle_shutdown(_):
    global STOP_MODULES
    STOP_MODULES.set()


def handle_load_modules(message):
    modules_to_load = message.data.get("modules", [])
    for module in modules_to_load:
        if module in PROCESSES:
            _stop_process(PROCESSES.pop(module))
        _start_process(module)


def _cycle_logs():
    archive_logs()
    remove_old_logs()


def _get_log_file(process_name):
    """
    Get a writable object to use
    :param process_name: Name of module for which to get a log
    :return: io object for log file
    """
    log_name = get_log_file_for_module(process_name)
    if log_name in LOG_FILES:
        logfile = LOG_FILES[log_name]
        if not logfile.closed:
            return logfile
    logfile = open(log_name, 'a+')
    LOG_FILES[log_name] = logfile
    return logfile


def _start_process(name, logfile: IO = None):
    # TODO: As discussed in https://github.com/NeonJarbas/NeonCore/pull/76 this should be handled differently DM
    logfile = logfile or _get_log_file(name)
    proc = Popen(name, stdout=logfile, stderr=STDOUT)
    PROCESSES[repr(name)] = proc


def _stop_process(process):
    process.send_signal(SIGTERM)
    try:
        process.wait(5)
    except Exception as e:
        LOG.error(e)
        try:
            pid = process.pid
            psutil.Process(pid).kill()
        except Exception as e:
            LOG.error(e)
            LOG.error(f"{process} not terminated!")
            raise e


def _stop_all_core_processes(include_runner=False):
    procs = {p.pid: p.cmdline() for p in psutil.process_iter()}
    for pid, cmdline in procs.items():
        if cmdline and (any(pname in cmdline[-1] for pname in ("mycroft.messagebus.service", "neon_speech_client",
                                                               "neon_audio_client", "mycroft.skills",
                                                               "neon_core_server", "neon_enclosure_client",
                                                               "neon_core_client", "mycroft-gui-app",
                                                               "NGI.utilities.gui"))
                        or include_runner and cmdline[-1] == "run_neon.py"):
            LOG.info(f"Terminating {cmdline} {pid}")
            try:
                psutil.Process(pid).terminate()
                sleep(1)
                if psutil.pid_exists(pid) and psutil.Process(pid).is_running():
                    LOG.error(f"Process {pid} not terminated!!")
                    psutil.Process(pid).kill()
            except Exception as e:
                LOG.error(e)


def start_neon():
    """
    Sets listeners and starts up neon processes
    """
    bus.on("neon.shutdown", handle_shutdown)
    bus.on("neon.load_modules", handle_load_modules)
    bus.run_in_thread()

    try:
        _stop_all_core_processes()
        _cycle_logs()
        _start_process(["python3", "-m", "mycroft.messagebus.service"])
        _start_process("neon_speech_client")
        _start_process("neon_audio_client")
        _start_process(["python3", "-m", "mycroft.skills"])
        if get_neon_device_type() == "server":
            _start_process("neon_core_server")
        else:
            _start_process("neon_enclosure_client")
            _start_process("neon_core_client")
            _start_process("mycroft-gui-app")
    except Exception as e:
        LOG.error(e)
        STOP_MODULES.set()
    try:
        STOP_MODULES.wait()
    except KeyboardInterrupt:
        pass

    LOG.info("Stopping all modules")

    for p in PROCESSES.values():
        _stop_process(p)

    for log in LOG_FILES.values():
        log.close()

    sys.stdout = sys.__stdout__
    run_log.close()

    _stop_all_core_processes(True)


def stop_neon():
    """
    Notifies any running instances to shutdown and then cleans up any leftover processes
    """
    try:
        bus.run_in_thread()
        if bus.connected_event.is_set():
            LOG.info("Messagebus running, emit shutdown")
            bus.emit(Message("neon.shutdown"))
            sleep(10)  # Give modules a chance to nicely shutdown
    except Exception as x:
        LOG.error(x)
    LOG.info("stopping")
    _stop_all_core_processes(True)

    LOG.info("stopped")
    exit(0)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        stop_neon()
    else:
        start_neon()


if __name__ == "__main__":
    main()
