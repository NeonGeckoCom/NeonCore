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

# TODO: Remove below patches with ovos-core 0.0.8
import mycroft.skills.skill_loader

from ovos_bus_client.message import Message
from ovos_utils.log import LOG

try:
    from ovos_workshop.skill_launcher import SkillLoader
    from ovos_workshop.skill_launcher import PluginSkillLoader as _Plugin
    from ovos_workshop.skill_launcher import get_skill_class, \
        get_create_skill_function

    class PluginSkillLoader(_Plugin):
        def _create_skill_instance(self, skill_module=None):
            skill_module = skill_module or self.skill_module

            try:
                # in skill classes __new__ should fully create the skill object
                skill_class = self._skill_class or get_skill_class(skill_module)
                LOG.debug(f"loading skill: {skill_class}")
                self.instance = skill_class(bus=self.bus, skill_id=self.skill_id)
                return self.instance is not None
            except Exception as e:
                LOG.warning(f"Skill load raised exception: {e}")

            try:
                # attempt to use old style create_skill function entrypoint
                skill_creator = get_create_skill_function(skill_module) or \
                                self.skill_class
            except Exception as e:
                LOG.exception(f"Failed to load skill creator: {e}")
                self.instance = None
                return False

            # if the signature supports skill_id and bus pass them
            # to fully initialize the skill in 1 go
            try:
                # skills that do will have bus and skill_id available
                # as soon as they call super()
                self.instance = skill_creator(bus=self.bus,
                                              skill_id=self.skill_id)
            except Exception as e:
                # most old skills do not expose bus/skill_id kwargs
                LOG.warning(f"Legacy skill: {e}")
                self.instance = skill_creator()

            try:
                # finish initialization of skill if we didn't manage to inject
                # skill_id and bus kwargs.
                # these skills only have skill_id and bus available in initialize,
                # not in __init__
                try:
                    if not self.instance.is_fully_initialized:
                        self.instance._startup(self.bus, self.skill_id)
                except AttributeError:
                    if not self.instance._is_fully_initialized:
                        self.instance._startup(self.bus, self.skill_id)
            except Exception as e:
                LOG.exception(f'Skill __init__ failed with {e}')
                self.instance = None

            return self.instance is not None

except ImportError:
    LOG.warning(f"Patching PluginSkillLoader")
    from mycroft.skills.skill_loader import PluginSkillLoader as _Plugin
    from mycroft.skills.skill_loader import SkillLoader
    get_skill_class, get_create_skill_function = None, None


    class PluginSkillLoader(_Plugin):
        def load(self, skill_class=None):
            skill_class = skill_class or self._skill_class
            _Plugin.load(self, skill_class)


mycroft.skills.skill_loader.SkillLoader = SkillLoader
mycroft.skills.skill_loader.PluginSkillLoader = PluginSkillLoader
mycroft.skills.skill_loader.Message = Message
