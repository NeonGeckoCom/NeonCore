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

import json
import os

from os.path import join, dirname
from ovos_utils.json_helper import merge_dict
from ovos_utils.system import set_root_path
from ovos_utils.xdg_utils import xdg_config_home

from neon_utils.logger import LOG


def setup_ovos_core_config():
    """
    Runs at module init to ensure base ovos.conf exists to patch ovos-core.
    Note that this must run before any import of Configuration class.
    """
    ovos_config_path = join(xdg_config_home(), "OpenVoiceOS", "ovos.conf")

    neon_default_config = {
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
    try:
        with open(ovos_config_path) as f:
            cfg = json.load(f)
    except FileNotFoundError:
        pass
    except Exception as e:
        LOG.error(e)

    if cfg == neon_default_config:
        # Skip merge/write config if it's already equivalent
        return
    disk_cfg = dict(cfg)
    cfg = merge_dict(cfg, neon_default_config)
    if disk_cfg == cfg:
        # Skip write config if it's already equivalent
        return
    if not os.path.isdir(dirname(ovos_config_path)):
        os.makedirs(dirname(ovos_config_path))
    LOG.info(f"Writing config file: {ovos_config_path}")
    with open(ovos_config_path, "w+") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=True)


def setup_ovos_config(neon_root_path: str):
    """
    Configure ovos_utils to read from neon.conf files and set the root path
    """
    # TODO: This method will be handled in ovos-core directly in the future
    # ensure ovos_utils can find neon_core
    set_root_path(neon_root_path)


def setup_neon_system_config():
    """
    Ensure default neon config file is specified in envvars
    """
    config_home = join(xdg_config_home(), "neon")
    config_file = join(config_home, "neon.conf")
    if not os.path.isdir(config_home):
        os.makedirs(config_home)
    os.environ["MYCROFT_SYSTEM_CONFIG"] = config_file


def overwrite_neon_conf():
    """
    Write over neon.conf file with Neon configuration
    """

    from neon_utils.configuration_utils import \
        write_mycroft_compatible_config, init_config_dir
    init_config_dir()

    # Write and reload Mycroft-compat conf file
    neon_config_path = join(xdg_config_home(), "neon", "neon.conf")
    # TODO: This log should be in the called method
    LOG.info(f"{neon_config_path} will be overwritten with Neon YAML config")
    write_mycroft_compatible_config(neon_config_path)


def init_config(neon_root_path: str):
    """
    Initialize all configuration methods to read from the same config
    """
    setup_ovos_config(neon_root_path)
    setup_neon_system_config()
    # make ovos-core Configuration.get() load neon.conf
    # TODO ovos-core does not yet support yaml configs, once it does
    #  Configuration.get() will be made to load the existing neon config files,
    #  for now it simply provides correct default values
    setup_ovos_core_config()
    overwrite_neon_conf()

    from neon_core.configuration import Configuration
    Configuration.load_config_stack(cache=True, remote=False)

    # patch version string to allow downstream to know where it is running
    import mycroft.version
    core_version_str = '.'.join(map(str,
                                    mycroft.version.CORE_VERSION_TUPLE)) + \
                       "(NeonGecko)"
    mycroft.version.CORE_VERSION_STR = core_version_str
    return core_version_str
