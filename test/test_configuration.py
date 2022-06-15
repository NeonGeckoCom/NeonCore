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
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config")

    @classmethod
    def setUpClass(cls) -> None:
        os.environ["XDG_CONFIG_HOME"] = cls.CONFIG_PATH

        import neon_core
        assert isinstance(neon_core.CORE_VERSION_STR, str)
        assert os.path.isfile(os.path.join(cls.CONFIG_PATH,
                                           "OpenVoiceOS", "ovos.conf"))

        from neon_core.util.runtime_utils import use_neon_core
        from ovos_utils.configuration import get_ovos_config
        ovos_config = use_neon_core(get_ovos_config)()
        LOG.info(pformat(ovos_config))
        assert ovos_config['config_filename'] == 'neon.conf'
        assert os.path.basename(ovos_config['default_config_path']) == "neon.conf"

    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.exists(cls.CONFIG_PATH):
            shutil.rmtree(cls.CONFIG_PATH)
        os.environ.pop("XDG_CONFIG_HOME")

    def test_neon_core_config_init(self):
        from neon_utils.configuration_utils import \
            get_mycroft_compatible_config
        from neon_core.configuration import Configuration
        from neon_core.util.runtime_utils import use_neon_core

        configuration = Configuration()
        deprecated_neon_config = use_neon_core(get_mycroft_compatible_config)()
        for key, val in deprecated_neon_config.items():
            if isinstance(val, dict):
                for k, v in val.items():
                    if not isinstance(v, dict):
                        self.assertEqual(configuration[key][k],
                                         v, configuration[key])
            else:
                self.assertEqual(configuration[key], val)

    def test_ovos_core_config_init(self):
        from neon_utils.configuration_utils import \
            get_mycroft_compatible_config
        from mycroft.configuration import Configuration as MycroftConfig
        from neon_core.util.runtime_utils import use_neon_core

        mycroft_config = MycroftConfig()
        neon_config = use_neon_core(get_mycroft_compatible_config)()
        for key, val in neon_config.items():
            if isinstance(val, dict):
                for k, v in val.items():
                    if not isinstance(v, dict):
                        self.assertEqual(mycroft_config[key][k],
                                         v, mycroft_config[key])
            else:
                self.assertEqual(mycroft_config[key], val)

    def test_patch_config(self):
        from os.path import join
        import json

        test_config_dir = os.path.join(os.path.dirname(__file__), "config")
        os.makedirs(test_config_dir, exist_ok=True)
        os.environ["XDG_CONFIG_HOME"] = test_config_dir

        from neon_core.util.runtime_utils import use_neon_core
        from neon_utils.configuration_utils import init_config_dir

        use_neon_core(init_config_dir)()

        with open(join(test_config_dir, "OpenVoiceOS", 'ovos.conf')) as f:
            ovos_conf = json.load(f)
        self.assertEqual(ovos_conf['submodule_mappings']['neon_core'],
                         "neon_core")
        self.assertIsInstance(ovos_conf['module_overrides']['neon_core'], dict)

        from neon_core.configuration import patch_config
        test_config = {"new_key": {'val': True}}
        patch_config(test_config)
        conf_file = os.path.join(test_config_dir, 'neon',
                                 'neon.conf')
        self.assertTrue(os.path.isfile(conf_file))
        with open(conf_file) as f:
            config = json.load(f)

        self.assertTrue(config['new_key']['val'])
        shutil.rmtree(test_config_dir)
        # os.environ.pop("XDG_CONFIG_HOME")


if __name__ == '__main__':
    unittest.main()
