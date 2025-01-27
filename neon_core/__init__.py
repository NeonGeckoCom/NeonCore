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

from os import environ
from os.path import join, dirname

environ["OVOS_DEFAULT_CONFIG"] = join(dirname(__file__),
                                      "configuration", "neon.yaml")

# Patching deprecation warnings
# TODO: Deprecate after migration to ovos-workshop 1.0+ and ovos-core 0.1+
import ovos_workshop.resource_files
import ovos_core.intent_services.stop_service
from ovos_utils.bracket_expansion import expand_template
ovos_workshop.resource_files.expand_options = expand_template
ovos_core.intent_services.stop_service.expand_options = expand_template


# Patching backwards-compat. intent language codes
import ovos_core.intent_services
from ovos_bus_client.util import get_message_lang


def _patched_get_message_lang(*args, **kwargs):
    # https://github.com/OpenVoiceOS/ovos-utils/pull/267 started normalizing
    # lang codes to `en-US`, where previously this would be `en-us`. This
    # patches the intent_service to use the lowercase tags for improved
    # backwards-compatibility
    return get_message_lang(*args, **kwargs).lower()


ovos_core.intent_services.get_message_lang = _patched_get_message_lang
