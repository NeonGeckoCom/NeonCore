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
from ovos_utils.xdg_utils import xdg_data_home
from ovos_utils.log import LOG
from ovos_bus_client.message import Message
from ovos_core.skill_manager import SkillManager


class NeonSkillManager(SkillManager):

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

    def _load_new_skills(self, *args, **kwargs):
        # Override load method for config module checks
        SkillManager._load_new_skills(self, *args, **kwargs)

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
            if not self._internet_loaded.wait(self._internet_skill_timeout):
                LOG.error("Timeout waiting for internet skills to load")
                return False
        LOG.info(f"Configured  ready settings met: {ready_settings}")
        return True

    def _check_device_ready(self):
        while not self._wait_until_skills_ready():
            LOG.warning("Skills not ready, still waiting...")
        ready_settings = self.config.get("ready_settings", ["skills"])
        valid_services = ("skills", "voice", "audio", "gui_service", "internet")
        ready_services = {s: False for s in ready_settings if s in valid_services}
        while not all(ready_services.values()):
            for service in ready_services:
                if not ready_services[service]:
                    resp = self.bus.wait_for_response(Message(f"mycroft.{service}.is_ready", context={"source": ["skills"], "destination": [service]}))
                    service_ready = resp and resp.data.get("status") == "ready"
                    if service_ready:
                        LOG.info(f"{service} reports ready")
                        ready_services[service] = service_ready
        LOG.info(f"All configured ready settings met: {ready_services}")
        self.bus.emit(Message("mycroft.ready", context={"source": ["skills"], "destination": valid_services}))

    # Override to maintain skill load support
    def handle_initial_training(self, message):
        """
        This method blocks `run` until network and internet skills are loaded
        (if configured). After `self.initial_load_complete` is set to True,
        the skills service will be marked as ready
        """
        # Wait for network and internet skills to load as configured
        if not self._wait_until_skills_ready():
            LOG.error("Skills did not report ready. Continuing anyway.")
        self.initial_load_complete = True
            
