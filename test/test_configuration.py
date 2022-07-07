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
import yaml

from copy import deepcopy
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
        assert ovos_config['config_filename'] == 'neon.yaml'
        assert os.path.basename(ovos_config['default_config_path']) == "neon.yaml"

    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.exists(cls.CONFIG_PATH):
            shutil.rmtree(cls.CONFIG_PATH)
        os.environ.pop("XDG_CONFIG_HOME")

    def test_neon_core_config_init(self):
        from neon_core.configuration import Configuration
        from mycroft.configuration import Configuration as MycroftConfig
        # TODO: Replace test after ovos_utils YML config compat.
        from ovos_utils.configuration import read_mycroft_config
        from neon_core.util.runtime_utils import use_neon_core

        configuration = Configuration()
        self.assertIsInstance(configuration, dict)
        self.assertEqual(configuration, use_neon_core(MycroftConfig)())
        # self.assertEqual(configuration, use_neon_core(read_mycroft_config)())

    def test_patch_config(self):
        from os.path import join
        import json

        test_config_dir = os.path.join(os.path.dirname(__file__), "config")
        os.makedirs(test_config_dir, exist_ok=True)
        os.environ["XDG_CONFIG_HOME"] = test_config_dir

        from neon_core.util.runtime_utils import use_neon_core
        from neon_utils.configuration_utils import init_config_dir
        use_neon_core(init_config_dir)()
        from mycroft.configuration import Configuration
        from mycroft.configuration.locations import DEFAULT_CONFIG
        self.assertTrue(DEFAULT_CONFIG.endswith("neon.yaml"))
        self.assertTrue(Configuration.default.path == DEFAULT_CONFIG,
                        Configuration.default.path)
        with open(join(test_config_dir, "OpenVoiceOS", 'ovos.conf')) as f:
            ovos_conf = json.load(f)
        self.assertEqual(ovos_conf['submodule_mappings']['neon_core'],
                         "neon_core")
        self.assertIsInstance(ovos_conf['module_overrides']['neon_core'], dict)

        from neon_core.configuration import patch_config
        test_config = {"new_key": {'val': True}}
        patch_config(test_config)
        self.assertEqual(Configuration(), use_neon_core(Configuration)())
        conf_file = os.path.join(test_config_dir, 'neon',
                                 'neon.yaml')
        self.assertTrue(os.path.isfile(conf_file))
        with open(conf_file) as f:
            config = yaml.safe_load(f)
        for k in config:
            if isinstance(k, dict):
                for s in k:
                    self.assertEqual(config[k][s], Configuration()[k][s],
                                     Configuration()[k][s])
            else:
                self.assertEqual(config[k], Configuration()[k],
                                 Configuration()[k])

        self.assertTrue(config['new_key']['val'])

        test_config = deepcopy(config)
        test_config["new_key"]["val"] = False
        test_config['skills'] = \
            {'auto_update': not Configuration()['skills']['auto_update']}
        valid_val = test_config['skills']['auto_update']
        self.assertNotEqual(config, test_config)
        patch_config(test_config)
        conf_file = os.path.join(test_config_dir, 'neon',
                                 'neon.yaml')
        with open(conf_file) as f:
            config = yaml.safe_load(f)
        self.assertEqual(config, test_config)
        self.assertEqual(config['skills']['auto_update'], valid_val)
        self.assertFalse(config['new_key']['val'])
        self.assertEqual(config['skills']['auto_update'],
                         Configuration()['skills']['auto_update'])

        shutil.rmtree(test_config_dir)
        # os.environ.pop("XDG_CONFIG_HOME")


if __name__ == '__main__':
    unittest.main()
