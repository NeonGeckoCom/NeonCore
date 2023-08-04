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

from os import listdir
from os.path import join
from typing import Optional
from threading import Thread

from ovos_bus_client import Message, MessageBusClient
from ovos_config.locale import set_default_lang, set_default_tz
from ovos_config.config import Configuration
from ovos_utils.log import LOG
from ovos_utils.skills.locations import get_plugin_skills, get_skill_directories
from ovos_utils.process_utils import StatusCallbackMap
from neon_utils.metrics_utils import announce_connection
from neon_utils.signal_utils import init_signal_handlers, init_signal_bus
from neon_utils.messagebus_utils import get_messagebus
from ovos_bus_client.util.scheduler import EventScheduler
from ovos_utils.skills.api import SkillApi
from ovos_workshop.skills.fallback import FallbackSkill

from neon_core.skills.intent_service import NeonIntentService
from neon_core.skills.skill_manager import NeonSkillManager
from neon_core.util.diagnostic_utils import report_metric


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
        LOG.debug("Starting Skills Service")
        self.daemon = daemonic
        self.bus: Optional[MessageBusClient] = None
        self.skill_manager = None
        self.http_server = None
        self.event_scheduler = None
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

    @property
    def status(self):
        LOG.warning("This reference is deprecated. "
                    "Use `NeonSkillService.skill_manager.status` directly.")
        return self.skill_manager.status

    def _get_skill_dirs(self) -> list:
        """
        Get a list of paths to every loaded skill in load order (priority last)
        """
        plugin_dirs, _ = get_plugin_skills()
        skill_base_dirs = get_skill_directories(self.config)
        # TODO: Get ovos_plugin_common_play too
        skill_dirs = [join(base_dir, d) for base_dir in skill_base_dirs
                      for d in listdir(base_dir)]
        return plugin_dirs + skill_dirs

    def run(self):
        LOG.debug("Starting Skills Service Thread")
        # Set the active lang to match the configured one
        set_default_lang(self.config.get("language", {}).get('internal') or
                         self.config.get("lang") or "en-us")
        # Set the default timezone to match the configured one
        set_default_tz()

        # Setup signal manager
        try:
            self.bus = self.bus or get_messagebus(timeout=300)
        except TimeoutError as e:
            LOG.exception(e)
            self.callbacks.on_error(repr(e))
            raise e

        init_signal_bus(self.bus)
        init_signal_handlers()

        # Setup Intents and Skill Manager
        self._register_intent_services()
        self.event_scheduler = EventScheduler(self.bus, autostart=False)
        self.event_scheduler.daemon = True
        self.event_scheduler.start()
        SkillApi.connect_bus(self.bus)
        LOG.info("Starting Skill Manager")
        self.skill_manager = NeonSkillManager(
            bus=self.bus, watchdog=self.watchdog,
            alive_hook=self.callbacks.on_alive,
            started_hook=self.callbacks.on_started,
            ready_hook=self.callbacks.on_ready,
            error_hook=self.callbacks.on_error,
            stopping_hook=self.callbacks.on_stopping)
        self.skill_manager.name = "skill_manager"
        self.skill_manager.start()
        LOG.info("Skill Manager started")

        self.register_wifi_setup_events()
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

    def handle_wifi_setup_completed(self, _):
        self.bus.emit(Message('ovos.shell.status.ok'))
        # # Skills have been loaded, allow some time for time sync service
        # time.sleep(10)
        # self.bus.emit(Message("system.display.homescreen"))

    def register_wifi_setup_events(self):
        self.bus.once("ovos.wifi.setup.completed",
                      self.handle_wifi_setup_completed)
        self.bus.once("ovos.phal.wifi.plugin.skip.setup",
                      self.handle_wifi_setup_completed)

    def shutdown(self):
        LOG.info('Shutting down Skills service')
        # self.status.set_stopping()
        if self.event_scheduler is not None:
            self.event_scheduler.shutdown()

        if self.http_server is not None:
            self.http_server.shutdown()

        # Terminate all running threads that update skills
        if self.skill_manager is not None:
            self.skill_manager.stop()
            self.skill_manager.join()

        self.bus.close()
        LOG.info('Skills service shutdown complete!')
