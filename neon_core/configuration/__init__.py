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

from ovos_config.config import Configuration
from os.path import exists, isdir, dirname
from os import makedirs
from neon_utils.logger import LOG

"""
Neon modules should import config from this module since module_overrides will
result in different configurations depending on originating module.
"""


def get_private_keys():
    return Configuration().get("keys", {})


def patch_config(config: dict = None):
    """
    Write the specified speech configuration to the global config file
    :param config: Mycroft-compatible configuration override
    """
    from ovos_config.config import LocalConf
    from ovos_config.locations import USER_CONFIG
    if not exists(USER_CONFIG):
        if not isdir(dirname(USER_CONFIG)):
            LOG.warning(f"Creating config dir: {dirname(USER_CONFIG)}")
            makedirs(dirname(USER_CONFIG), exist_ok=True)
        with open(USER_CONFIG, 'w+'):
            pass

    config = config or dict()
    local_config = LocalConf(USER_CONFIG)
    local_config.update(config)
    local_config.store()
    Configuration().reload()
    import mycroft.configuration
    mycroft.configuration.Configuration().reload()
