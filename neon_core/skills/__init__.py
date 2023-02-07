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
import neon_utils.skills
import mycroft.skills.core

from neon_utils.skills.mycroft_skill import PatchedMycroftSkill
from neon_core.skills.decorators import intent_handler, intent_file_handler, \
    resting_screen_handler, conversational_intent

# Patch the base skill
import ovos_workshop.skills
ovos_workshop.skills.mycroft_skill.MycroftSkill = PatchedMycroftSkill

# Reload ovos_workshop modules with Patched class
importlib.reload(ovos_workshop.skills.ovos)
importlib.reload(ovos_workshop.skills.fallback)
importlib.reload(ovos_workshop.skills)

# Reload neon_utils modules with Patched class
importlib.reload(neon_utils.skills.neon_fallback_skill)
importlib.reload(neon_utils.skills)

# Reload mycroft modules with Patched class
importlib.reload(mycroft.skills.mycroft_skill.mycroft_skill)
importlib.reload(mycroft.skills.mycroft_skill)
importlib.reload(mycroft.skills.fallback_skill)
importlib.reload(mycroft.skills.common_play_skill)
importlib.reload(mycroft.skills.common_query_skill)
importlib.reload(mycroft.skills.common_iot_skill)
importlib.reload(mycroft.skills)

# Manually patch re-defined classes in `mycroft.skills.core`
mycroft.skills.core.MycroftSkill = PatchedMycroftSkill
mycroft.skills.core.FallbackSkill = mycroft.skills.fallback_skill.FallbackSkill


__all__ = ['intent_handler',
           'intent_file_handler',
           'resting_screen_handler',
           'conversational_intent']
