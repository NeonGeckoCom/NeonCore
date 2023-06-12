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

import importlib

from ovos_utils.log import LOG
from neon_utils.skills.mycroft_skill import PatchedMycroftSkill
from neon_core.skills.decorators import intent_handler, intent_file_handler, \
    resting_screen_handler, conversational_intent

# Patch the base skill
import ovos_workshop.skills
ovos_workshop.skills.mycroft_skill.MycroftSkill = PatchedMycroftSkill

workshop_modules = ("ovos_workshop.skills.ovos",
                    "ovos_workshop.skills.fallback",
                    "ovos_workshop.skills.common_query_skill",
                    "ovos_workshop.skills.common_play",
                    "ovos_workshop.skills")
neon_utils_modules = ("neon_utils.skills.neon_fallback_skill",
                      "neon_utils.skills")
mycroft_skills_modules = ("mycroft.skills.mycroft_skill.mycroft_skill",
                          "mycroft.skills.mycroft_skill",
                          "mycroft.skills.fallback_skill",
                          "mycroft.skills.common_play_skill",
                          "mycroft.skills.common_query_skill",
                          "mycroft.skills.common_iot_skill",
                          "mycroft.skills")

# Reload ovos_workshop modules with Patched class
for module in workshop_modules:
    try:
        importlib.reload(importlib.import_module(module))
    except Exception as e:
        LOG.exception(e)

# Reload neon_utils modules with Patched class
for module in neon_utils_modules:
    try:
        importlib.reload(importlib.import_module(module))
    except Exception as e:
        LOG.exception(e)

# Reload mycroft modules with Patched class
for module in mycroft_skills_modules:
    try:
        importlib.reload(importlib.import_module(module))
    except Exception as e:
        LOG.exception(e)

# Manually patch top-level `mycroft` references
import mycroft
mycroft.MycroftSkill = PatchedMycroftSkill
mycroft.FallbackSkill = mycroft.skills.fallback_skill.FallbackSkill

# Manually patch re-defined classes in `mycroft.skills.core`
import mycroft.skills.core
mycroft.skills.core.MycroftSkill = PatchedMycroftSkill
mycroft.skills.core.FallbackSkill = mycroft.skills.fallback_skill.FallbackSkill

# TODO: Remove below patches with ovos-core 0.0.8 refactor
import neon_core.skills.patched_plugin_loader

from mycroft.skills import api
from mycroft.skills import skill_manager
from mycroft.skills.intent_services import padatious_service
from ovos_bus_client.message import Message
mycroft.skills.api.Message = Message
mycroft.skills.skill_manager.Message = Message
mycroft.skills.intent_services.padatious_service.Message = Message

__all__ = ['intent_handler',
           'intent_file_handler',
           'resting_screen_handler',
           'conversational_intent']
