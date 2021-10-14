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
from os.path import join, dirname, exists
import xdg.BaseDirectory
import json
from ovos_utils.json_helper import merge_dict
from ovos_utils.system import set_root_path
from ovos_utils.configuration import set_config_name

NEON_ROOT_PATH = dirname(dirname(__file__))

# first thing to do is ensure user holmes.conf exists
# NOTE: must be done before any mycroft (neon) import
def setup_holmes_config():
    HOLMES_CONFIG = join(xdg.BaseDirectory.save_config_path("HolmesV"),
                         "holmes.conf")

    _NEON_HOLMES_CONFIG = {
        "module_overrides": {
            "neon_core": {
                "xdg": True,
                "base_folder": "neon",
                "config_filename": "neon.conf",
                "default_config_path": join(dirname(__file__),
                                            'configuration', 'neon.conf')
            }
        },
        # if these services are running standalone (neon_core not in venv)
        # config them to use neon_core config from above
        "submodule_mappings": {
            "neon_speech": "neon_core",
            "neon_audio": "neon_core",
            "neon_enclosure": "neon_core"
        }
    }
    cfg = {}
    if exists(HOLMES_CONFIG):
        try:
            with open(HOLMES_CONFIG) as f:
                cfg = json.load(f)
        except:
            pass
    cfg = merge_dict(cfg, _NEON_HOLMES_CONFIG)
    with open(HOLMES_CONFIG, "w") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=True)

# make holmesV Configuration.get() load neon.conf
# TODO HolmesV does not yet support yaml configs, once it does
#  Configuration.get() will be made to load the existing neon config files,
#  for now it simply provides correct default values
setup_holmes_config()


def setup_ovos_config():
    # ensure ovos_utils can find neon_core
    set_root_path(NEON_ROOT_PATH)
    # make ovos_utils load the proper .conf files
    set_config_name("neon", "neon_core")


setup_ovos_config()

# patch version string to allow downstream to know where it is running
import mycroft.version
CORE_VERSION_STR = '.'.join(map(str, mycroft.version.CORE_VERSION_TUPLE)) + \
                   "(NeonGecko)"
mycroft.version.CORE_VERSION_STR = CORE_VERSION_STR


from neon_core.skills import NeonSkill, NeonFallbackSkill
from neon_core.skills.intent_service import NeonIntentService


__all__ = ['NEON_ROOT_PATH',
           'NeonIntentService',
           'NeonSkill',
           'NeonFallbackSkill',
           'CORE_VERSION_STR']
