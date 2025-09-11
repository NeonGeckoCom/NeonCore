# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2025 Neongecko.com Inc.
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

from os import makedirs
from os.path import isdir, join, expanduser
from threading import Thread
from ovos_utils.xdg_utils import xdg_data_home
from ovos_utils.log import LOG
from ovos_bus_client.message import Message
from ovos_core.skill_manager import SkillManager


class NeonSkillManager(SkillManager):
    def _sync_skill_loading_state(self):
        """
        Override to wait for configured ready settings before announcing the
        service is ready
        """
        SkillManager._sync_skill_loading_state(self)
        LOG.info("Waiting for skill ready settings")  # TODO Log is only for debugging
        self._wait_until_skills_ready()

        # Start a background thread to check for configured ready settings
        # while allowing the skills service to continue initialization
        ready_event_thread = Thread(target=self._check_device_ready)
        ready_event_thread.daemon = True
        ready_event_thread.start()

    def get_default_skills_dir(self):
        """
        Go through legacy config params to locate the default skill directory
        """
        skill_config = self.config["skills"]
        skill_dir = skill_config.get("directory") or \
            skill_config.get("extra_directories")
        skill_dir = skill_dir[0] if isinstance(skill_dir, list) and \
            len(skill_dir) > 0 else skill_dir or \
            join(xdg_data_home(), "neon", "skills")

        skill_dir = expanduser(skill_dir)
        if not isdir(skill_dir):
            LOG.warning("Creating requested skill directory")
            try:
                makedirs(skill_dir)
            except Exception as e:
                LOG.error(e)
                if skill_dir != join(xdg_data_home(), "neon", "skills"):
                    skill_dir = join(xdg_data_home(), "neon", "skills")
                    LOG.warning("Using XDG skills directory")
                    makedirs(skill_dir, exist_ok=True)

        return skill_dir

    def _get_plugin_skill_loader(self, skill_id, init_bus=True):
        assert self.bus is not None
        if not init_bus:
            LOG.debug("Ignoring request not to bind bus")
        return SkillManager._get_plugin_skill_loader(self, skill_id, True)

    # Re-implement support for internet and network skill load
    def _wait_until_skills_ready(self):
        """
        Block until configured network and internet skills are loaded to
        delay skills service reporting ready.
        """
        ready_settings = self.config.get("ready_settings", ["skills"])
        if "network_skills" in ready_settings:
            if not self._network_loaded.wait(self._network_skill_timeout):
                LOG.error("Timeout waiting for network skills to load")
                return False
        if "internet_skills" in ready_settings:
            if not self._internet_loaded.wait(self._network_skill_timeout):
                LOG.error("Timeout waiting for internet skills to load")
                return False
        LOG.debug("Configured skill load conditions met")
        return True

    def _check_device_ready(self):
        while not self._wait_until_skills_ready():
            LOG.warning("Skills not ready, still waiting...")
        ready_settings = self.config.get("ready_settings", ["skills"])
        valid_services = ("skills", "voice", "audio", "gui_service", "internet")
        ready_services = {s: False for s in ready_settings if s in valid_services}
        LOG.info(f"Waiting for services: {ready_services}")
        while not all(ready_services.values()):
            for service in ready_services:
                if not ready_services[service]:
                    resp = self.bus.wait_for_response(Message(f"mycroft.{service}.is_ready", context={"source": ["skills"], "destination": [service]}))
                    LOG.debug(resp.data if resp else f"No response for service={service}")  # TODO: Log to be downgraded to debug
                    service_ready = resp and resp.data.get("status")
                    if service_ready:
                        LOG.info(f"{service} reports ready")
                        ready_services[service] = service_ready
        LOG.info(f"All configured ready settings met: {ready_services}")
        self.bus.emit(Message("mycroft.ready", context={"source": ["skills"], "destination": valid_services}))

