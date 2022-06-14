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

import os
import shutil
import sys
import unittest
from pprint import pformat

from neon_utils.logger import LOG
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class ConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config_path = os.path.join(os.path.dirname(__file__), "config")
        os.environ["XDG_CONFIG_HOME"] = cls.config_path

        import neon_core
        assert isinstance(neon_core.CORE_VERSION_STR, str)

        # from mycroft.configuration.config import USER_CONFIG
        # assert USER_CONFIG == cls.config_path

        from neon_core.util.runtime_utils import use_neon_core
        from ovos_utils.configuration import get_ovos_config
        ovos_config = use_neon_core(get_ovos_config)()
        LOG.info(pformat(ovos_config))
        assert ovos_config['config_filename'] == 'neon.conf'

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.config_path)
        os.environ.pop("XDG_CONFIG_HOME")

    def test_neon_core_config_init(self):
        from neon_utils.configuration_utils import \
            get_mycroft_compatible_config
        from neon_core.configuration import Configuration
        from neon_core.util.runtime_utils import use_neon_core

        neon_compat_config = Configuration.get()
        neon_config = use_neon_core(get_mycroft_compatible_config)()
        for key, val in neon_config.items():
            if isinstance(val, dict):
                for k, v in val.items():
                    if not isinstance(v, dict):
                        self.assertEqual(neon_compat_config[key][k],
                                         v, neon_compat_config[key])
            else:
                self.assertEqual(neon_compat_config[key], val)

    def test_ovos_core_config_init(self):
        from neon_utils.configuration_utils import \
            get_mycroft_compatible_config
        from mycroft.configuration import Configuration as MycroftConfig
        from neon_core.util.runtime_utils import use_neon_core

        mycroft_config = MycroftConfig.get()
        neon_config = use_neon_core(get_mycroft_compatible_config)()
        for key, val in neon_config.items():
            if isinstance(val, dict):
                for k, v in val.items():
                    if not isinstance(v, dict):
                        self.assertEqual(mycroft_config[key][k],
                                         v, mycroft_config[key])
            else:
                self.assertEqual(mycroft_config[key], val)

    def test_signal_dir(self):
        from neon_utils.skill_override_functions import IPC_DIR as neon_ipc_dir
        from ovos_utils.signal import get_ipc_directory as ovos_ipc_dir
        from mycroft.util.signal import get_ipc_directory as mycroft_ipc_dir

        from neon_core.util.runtime_utils import use_neon_core

        self.assertEqual(neon_ipc_dir, use_neon_core(ovos_ipc_dir)())
        self.assertEqual(neon_ipc_dir,
                         use_neon_core(mycroft_ipc_dir)())


if __name__ == '__main__':
    unittest.main()
