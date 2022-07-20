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

import time

from tempfile import gettempdir
from os import listdir
from os.path import isdir, dirname, join
from typing import Optional
from threading import Thread

from ovos_config.locale import set_default_lang, set_default_tz
from ovos_config.config import Configuration
from ovos_utils.log import LOG
from ovos_utils.skills.locations import get_plugin_skills, get_skill_directories
from neon_utils.metrics_utils import announce_connection
from neon_utils.signal_utils import init_signal_handlers, init_signal_bus
from neon_utils.messagebus_utils import get_messagebus

from neon_core.skills.fallback_skill import FallbackSkill
from neon_core.skills.intent_service import NeonIntentService
from neon_core.skills.skill_manager import NeonSkillManager
from neon_core.util.diagnostic_utils import report_metric
from neon_core.util.qml_file_server import start_qml_http_server

from mycroft.skills.api import SkillApi
from mycroft.skills.event_scheduler import EventScheduler
from mycroft.util.process_utils import ProcessStatus, StatusCallbackMap


def on_started():
    LOG.info('Skills service is starting up.')


def on_alive():
    LOG.info('Skills service is alive.')


def on_ready():
    LOG.info('Skills service is ready.')


def on_error(e='Unknown'):
    LOG.info('Skills service failed to launch ({})'.format(repr(e)))


def on_stopping():
    LOG.info('Skills service is shutting down...')


class NeonSkillService(Thread):
    def __init__(self,
                 alive_hook: callable = on_alive,
                 started_hook: callable = on_started,
                 ready_hook: callable = on_ready,
                 error_hook: callable = on_error,
                 stopping_hook: callable = on_stopping,
                 watchdog: Optional[callable] = None,
                 config: Optional[dict] = None, daemonic: bool = False):
        Thread.__init__(self)
        self.setDaemon(daemonic)
        self.bus = None
        self.skill_manager = None
        self.http_server = None
        self.event_scheduler = None
        self.status = None
        self.watchdog = watchdog
        self.callbacks = StatusCallbackMap(on_started=started_hook,
                                           on_alive=alive_hook,
                                           on_ready=ready_hook,
                                           on_error=error_hook,
                                           on_stopping=stopping_hook)
        # Apply any passed config values and load Configuration
        if config:
            LOG.info("Updating global config with passed config")
            from neon_core.configuration import patch_config
            patch_config(config)
        self.config = Configuration()

    def _init_gui_server(self):
        """
        If configured, start the local file server to serve QML resources
        """
        from os.path import basename, isdir, join
        from os import symlink, makedirs
        # from shutil import copytree
        if not self.config["skills"].get("run_gui_file_server"):
            return
        directory = join(gettempdir(), "neon", "qml", "skills")
        if not isdir(directory):
            makedirs(directory, exist_ok=True)
        for d in reversed(self._get_skill_dirs()):
            if not isdir(join(d, "ui")):
                continue
            skill_dir = basename(d)
            if not isdir(join(directory, skill_dir)):
                makedirs(join(directory, skill_dir))
                symlink(join(d, "ui"), join(directory, skill_dir, "ui"))
                LOG.info(f"linked {d}/ui to {directory}/{skill_dir}/ui")
        self.http_server = start_qml_http_server(directory)

    def _get_skill_dirs(self) -> list:
        """
        Get a list of paths to every loaded skill in load order (priority last)
        """
        plugin_dirs, _ = get_plugin_skills()
        skill_base_dirs = get_skill_directories(self.config)

        skill_dirs = [join(base_dir, d) for base_dir in skill_base_dirs
                      for d in listdir(base_dir)]
        return plugin_dirs + skill_dirs

    def run(self):
        # Set the active lang to match the configured one
        set_default_lang(self.config.get("language", {}).get('internal') or
                         self.config.get("lang") or "en-us")
        # Set the default timezone to match the configured one
        set_default_tz()

        # Setup signal manager
        self.bus = self.bus or get_messagebus()
        init_signal_bus(self.bus)
        init_signal_handlers()

        # Setup Intents and Skill Manager
        self._register_intent_services()
        self.event_scheduler = EventScheduler(self.bus)
        self.status = ProcessStatus('skills', self.bus, self.callbacks,
                                    namespace="neon")
        SkillApi.connect_bus(self.bus)
        LOG.info("Starting Skill Manager")
        self.skill_manager = NeonSkillManager(self.bus, self.watchdog)
        self.skill_manager.setName("skill_manager")
        self.skill_manager.start()
        LOG.info("Skill Manager started")

        # Setup GUI File Server
        try:
            self._init_gui_server()
        except Exception as e:
            # Allow service to start if GUI file server fails
            LOG.exception(e)

        # Update status
        self.status.set_started()

        # TODO: These should be event-based in Mycroft/OVOS
        # Wait for skill manager to start up
        while not self.skill_manager.is_alive():
            time.sleep(0.1)
        self.status.set_alive()
        while not self.skill_manager.is_all_loaded():
            time.sleep(0.1)
        self.status.set_ready()
        announce_connection()

    def _initialize_metrics_handler(self):
        """
        Start bus listener for metrics
        """
        def handle_metric(message):
            report_metric(message.data.pop("name"), **message.data)

        if self.config.get("server", {}).get('metrics'):
            LOG.info("Metrics reporting enabled")
            self.bus.on("neon.metric", handle_metric)
        else:
            LOG.info("Metrics reporting disabled")

    def _register_intent_services(self):
        """
        Start up the all intent services and connect them as needed.
        """
        service = NeonIntentService(self.bus)
        # Register handler to trigger fallback system
        self.bus.on(
            'mycroft.skills.fallback',
            FallbackSkill.make_intent_failure_handler(self.bus)
        )
        return service

    def shutdown(self):
        LOG.info('Shutting down Skills service')
        if self.status:
            self.status.set_stopping()
        if self.event_scheduler is not None:
            self.event_scheduler.shutdown()

        if self.http_server is not None:
            self.http_server.shutdown()

        # Terminate all running threads that update skills
        if self.skill_manager is not None:
            self.skill_manager.stop()
            self.skill_manager.join()
        LOG.info('Skills service shutdown complete!')
