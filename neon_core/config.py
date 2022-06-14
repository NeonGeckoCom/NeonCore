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

from os.path import join
from ovos_utils.xdg_utils import xdg_config_home


def init_config():
    """
    Initialize all configuration methods to read from the same config
    """
    from neon_utils.configuration_utils import \
        write_mycroft_compatible_config, init_config_dir

    # First validate envvars, initialize `ovos.conf`, and set default config to
    # bundled neon.conf
    init_config_dir()

    # Write Mycroft-compat conf file with yml config values
    neon_config_path = join(xdg_config_home(), "neon", "neon.conf")
    write_mycroft_compatible_config(neon_config_path)

    # Tell config module to get changes we just wrote
    from mycroft.configuration.config import Configuration
    for config in Configuration.xdg_configs:
        config.reload()
    # TODO: Move old config file so this only happens 1x


def get_core_version() -> str:
    """
    Get the core version string.
    NOTE: `init_config` should be called before this method
    """
    from neon_core.configuration import Configuration
    Configuration.load_config_stack(cache=True, remote=False)

    # patch version string to allow downstream to know where it is running
    import mycroft.version
    core_version_str = '.'.join(map(str,
                                    mycroft.version.CORE_VERSION_TUPLE)) + \
                       "(NeonGecko)"
    mycroft.version.CORE_VERSION_STR = core_version_str
    return core_version_str


def setup_resolve_resource_file():
    """
    Override default resolve_resource_file to include resources in neon-core.
    Priority: neon-utils, neon-core, ~/.local/share/neon, ~/.neon, mycroft-core
    """
    from neon_utils.file_utils import resolve_neon_resource_file
    from mycroft.util.file_utils import resolve_resource_file

    def patched_resolve_resource_file(res_name):
        resource = resolve_neon_resource_file(res_name) or \
                   resolve_resource_file(res_name)
        return resource

    import mycroft.util
    mycroft.util.file_utils.resolve_resource_file = \
        patched_resolve_resource_file
