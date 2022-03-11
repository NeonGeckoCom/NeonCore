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

from neon_utils.configuration_utils import get_neon_skills_config
from neon_utils.log_utils import LOG

from neon_core.skills.skill_store import SkillsStore

from mycroft.util import connected
from mycroft.skills.skill_manager import SkillManager

SKILL_MAIN_MODULE = '__init__.py'


class NeonSkillManager(SkillManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skill_config = kwargs.get("config") or get_neon_skills_config()
        self.skill_downloader = SkillsStore(skills_dir=self.skill_config["directory"], config=self.skill_config,
                                            bus=self.bus)
        self.skill_downloader.skills_dir = self.skill_config["directory"]

    def download_or_update_defaults(self):
        # on launch only install if missing, updates handled separately
        # if osm is disabled in .conf this does nothing
        if self.skill_config["auto_update"]:
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

    def run(self):
        """Load skills and update periodically from disk and internet."""
        self.download_or_update_defaults()
        super().run()

    def _emit_converse_error(self, message, skill_id, error_msg):
        if hasattr(super(), "_emit_converse_error"):
            super()._emit_converse_error(message, skill_id, error_msg)
        # Also emit the old error message to keep compatibility and for any
        # listener on the bus
        reply = message.reply('skill.converse.error',
                              data=dict(skill_id=skill_id, error=error_msg))
        self.bus.emit(reply)
