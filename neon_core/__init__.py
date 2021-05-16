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

# this import will monkey patch mycroft.conf to ovos.conf
from neon_core.configuration import *
from neon_core.skills import NeonSkill, NeonFallbackSkill
from neon_core.skills.intent_service import NeonIntentService
from ovos_utils.system import set_root_path
from ovos_utils.fingerprinting import get_fingerprint
from os.path import dirname


NEON_ROOT_PATH = dirname(dirname(__file__))
# ensure ovos_utils can find neon_core
set_root_path(NEON_ROOT_PATH)


# patch version string to allow downstream to know where it is running
import mycroft.version
CORE_VERSION_STR = '.'.join(map(str, mycroft.version.CORE_VERSION_TUPLE)) + \
                   "(NeonGecko)"
mycroft.version.CORE_VERSION_STR = CORE_VERSION_STR


FINGERPRINT = get_fingerprint()


__all__ = ['NEON_ROOT_PATH',
           'NeonIntentService',
           'NeonSkill',
           'NeonFallbackSkill',
           'FINGERPRINT',
           'CORE_VERSION_STR']
