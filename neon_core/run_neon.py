# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import sys
import psutil

from time import time, sleep
from signal import SIGTERM
from threading import Event
from subprocess import Popen, STDOUT
from mycroft_bus_client import MessageBusClient, Message
from ovos_utils.gui import is_gui_running
from neon_utils.log_utils import remove_old_logs, archive_logs, LOG, \
    get_log_file_for_module, init_log
from typing.io import IO

LOG_FILES = {}
PROCESSES = {}
STOP_MODULES = Event()
STOP_MODULES.clear()
instance = time()
bus = MessageBusClient()
run_log = None


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
    try:
        remove_old_logs()
    except Exception as e:
        LOG.error(e)


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
    try:
        logfile = logfile or _get_log_file(name)
        proc = Popen(name, stdout=logfile, stderr=STDOUT)
        PROCESSES[repr(name)] = proc
        return True
    except Exception as e:
        LOG.error(f"Failed to start: {name}")
        LOG.error(e)
        return False


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


def _stop_all_core_processes():
    my_pid = os.getpid()
    procs = {p.pid: p.cmdline() for p in psutil.process_iter()}
    for pid, cmdline in procs.items():
        if cmdline and (any(pname in cmdline[-1] for pname in ("mycroft.messagebus.service", "neon_speech_client",
                                                               "neon_audio_client", "neon_messagebus_service",
                                                               "neon_core.skills", "neon_core.gui", "neon_gui_service",
                                                               "neon_core_server", "neon_enclosure_client",
                                                               "neon_core_client", "mycroft-gui-app",
                                                               "NGI.utilities.gui", "run_neon.py")
                            if "test" not in cmdline[-1])
                        or cmdline[-1].endswith("bin/neon-start")):
            LOG.info(f"Terminating {cmdline} {pid}")
            try:
                if pid == my_pid:
                    LOG.debug(f"Skipping Termination of self ({pid})")
                    continue
                psutil.Process(pid).terminate()
                sleep(1)
                if psutil.pid_exists(pid) and psutil.Process(pid).is_running():
                    LOG.info(f"Process {pid} not terminated!!")
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
    _stop_all_core_processes()
    _cycle_logs()

    # init_config_dir()  Already Done

    from neon_messagebus.service import NeonBusService
    from neon_messagebus.util.signal_utils import SignalManager
    from neon_messagebus.util.mq_connector import start_mq_connector
    from neon_messagebus.util.config import load_message_bus_config
    from neon_speech.service import NeonSpeechClient
    from neon_audio.service import NeonPlaybackService
    from neon_core.skills.service import NeonSkillService


    init_log(log_name="bus")
    bus_service = NeonBusService(debug=True, daemonic=True)
    bus_service.start()
    bus.connected_event.wait()
    signal_manager = SignalManager(bus)
    mq_connector = start_mq_connector(load_message_bus_config()._asdict())

    init_log(log_name="voice")
    speech_service = NeonSpeechClient()
    speech_service.start()

    init_log(log_name="audio")
    audio_service = NeonPlaybackService()
    audio_service.start()

    init_log(log_name="skills")
    skill_service = NeonSkillService()
    skill_service.start()

    # _start_process(["neon_messagebus_service"]) or STOP_MODULES.set()
    # bus.connected_event.wait()
    # _start_process("neon_speech_client") or STOP_MODULES.set()
    # _start_process("neon_audio_client") or STOP_MODULES.set()
    # _start_process(["python3", "-m", "neon_core.skills"]) or STOP_MODULES.set()
    # _start_process("neon_transcripts_controller")
    # if get_neon_device_type() == "server":
    #     _start_process("neon_core_server")
    # else:
    if not is_gui_running():
        _start_process("mycroft-gui-app")
    _start_process("neon_enclosure_client")
    # _start_process("neon_core_client")
    _start_process(["neon_gui_service"])

    try:
        STOP_MODULES.wait()
    except KeyboardInterrupt:
        pass

    LOG.info("Stopping all modules")
    mq_connector.stop()
    skill_service.shutdown()
    audio_service.shutdown()
    speech_service.shutdown()
    bus_service.shutdown()

    for p in PROCESSES.values():
        _stop_process(p)

    for log in LOG_FILES.values():
        log.close()

    sys.stdout = sys.__stdout__
    if run_log:
        run_log.close()

    _stop_all_core_processes()


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
    _stop_all_core_processes()

    LOG.info("stopped")
    exit(0)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        stop_neon()
    else:
        start_neon()


if __name__ == "__main__":
    from neon_utils.log_utils import get_log_dir
    LOG_DIR = get_log_dir()
    if not os.path.isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    run_log = open(os.path.join(LOG_DIR, "start.log"), "a+")
    sys.stdout = run_log
    sys.stderr = run_log
    main()
