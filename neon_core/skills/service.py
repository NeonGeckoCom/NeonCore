# # NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
# # All trademark and other rights reserved by their respective owners
# # Copyright 2008-2021 Neongecko.com Inc.
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

from neon_utils.configuration_utils import get_neon_skills_config, \
    get_neon_lang_config, get_neon_local_config
from neon_utils.net_utils import check_online
from neon_utils import LOG
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
from mycroft.configuration.locale import set_default_lang, set_default_tz
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


class NeonSkillService:
    def __init__(self, alive_hook=on_alive, started_hook=on_started,
                 ready_hook=on_ready, error_hook=on_error,
                 stopping_hook=on_stopping, watchdog=None):
        self.bus = None
        self.skill_manager = None
        self.event_scheduler = None
        self.status = None
        self.watchdog = watchdog
        self.callbacks = StatusCallbackMap(on_started=started_hook,
                                           on_alive=alive_hook,
                                           on_ready=ready_hook,
                                           on_error=error_hook,
                                           on_stopping=stopping_hook)
        skill_config = get_neon_skills_config()
        if skill_config.get("run_gui_file_server"):
            self.http_server = start_qml_http_server(
                skill_config["directory"])
        else:
            self.http_server = None

    def start(self):
        # config = Configuration.get()
        # Set the active lang to match the configured one
        set_default_lang(get_neon_lang_config().get('internal', 'en-us'))
        # Set the default timezone to match the configured one
        set_default_tz()

        self.bus = self.bus or get_messagebus()
        init_signal_bus(self.bus)
        init_signal_handlers()
        self._register_intent_services()
        self.event_scheduler = EventScheduler(self.bus)
        self.status = ProcessStatus('skills', self.bus, self.callbacks)
        SkillApi.connect_bus(self.bus)
        self.skill_manager = NeonSkillManager(self.bus, self.watchdog)
        self.status.set_started()
        # self._wait_for_internet_connection()
        # # TODO can this be removed? its a hack around msm requiring internet...
        # if self.skill_manager is None:
        #     self._initialize_skill_manager()
        self.skill_manager.start()
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

        if get_neon_local_config()['prefFlags']['metrics']:
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

    # def _initialize_skill_manager(self):
    #     """Create a thread that monitors the loaded skills, looking for updates
    #
    #     Returns:
    #         SkillManager instance or None if it couldn't be initialized
    #     """
    #     self.skill_manager = NeonSkillManager(self.bus, self.watchdog)
    #
    #     # # TODO: This config patching should be handled in neon_utils
    #     # self.skill_manager.config["skills"]["priority_skills"] = \
    #     #     self.skill_manager.config["skills"].get("priority") or \
    #     #     self.skill_manager.config["skills"]["priority_skills"]
    #     LOG.info(f"Priority={self.skill_manager.config['skills']['priority_skills']}")
    #     LOG.info(f"Blacklisted={self.skill_manager.config['skills']['blacklisted_skills']}")
    #     # self.skill_manager.load_priority()

    def _wait_for_internet_connection(self):
        if get_neon_skills_config().get("wait_for_internet", True):
            while not check_online():
                time.sleep(1)
        else:
            LOG.info("Online check disabled, device may be offline")

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
