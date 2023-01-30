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

from os import makedirs
from os.path import isdir, join, expanduser

from mycroft_bus_client import Message
from ovos_utils.xdg_utils import xdg_data_home
from ovos_utils.log import LOG

from neon_core.skills.skill_store import SkillsStore

from mycroft.util import connected
from mycroft.skills.skill_manager import SkillManager

SKILL_MAIN_MODULE = '__init__.py'
# TODO: deprecate `SKILL_MAIN_MODULE`?


class NeonSkillManager(SkillManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        skill_dir = self.get_default_skills_dir()
        self.skill_downloader = SkillsStore(
            skills_dir=skill_dir,
            config=self.config["skills"], bus=self.bus)
        self.skill_downloader.skills_dir = skill_dir

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

    def download_or_update_defaults(self):
        # on launch only install if missing, updates handled separately
        # if osm is disabled in .conf this does nothing
        if self.config["skills"].get("auto_update"):
            try:
                self.skill_downloader.install_default_skills()
            except Exception as e:
                if connected():
                    # if there is internet log the error
                    LOG.exception(e)
                    LOG.error("default skills installation failed")
                else:
                    # if no internet just skip this update
                    LOG.error("no internet, skipped default skills installation")

    def _load_new_skills(self, *args, **kwargs):
        super()._load_new_skills(*args, **kwargs)

    def run(self):
        """Load skills and update periodically from disk and internet."""
        self.download_or_update_defaults()
        from neon_utils.net_utils import check_online
        if check_online():
            LOG.debug("Already online, allow skills to load")
            self.bus.emit(Message("mycroft.network.connected"))
            self.bus.emit(Message("mycroft.internet.connected"))
        super().run()
