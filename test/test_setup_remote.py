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
import unittest

from neon_core.util.runtime_utils import use_neon_core
from ovos_utils.xdg_utils import xdg_data_home


class TestSetupRemote(unittest.TestCase):
    @use_neon_core
    def test_config_from_setup(self):
        from mycroft.configuration import Configuration
        config = Configuration()

        self.assertFalse(config.get("debug"))
        self.assertEqual(config["stt"]["module"], "google_cloud_streaming")
        self.assertEqual(config["tts"]["module"], "amazon")
        self.assertIsInstance(config["skills"]["neon_token"], str)

    def test_installed_packages(self):
        import neon_tts_plugin_polly
        import neon_stt_plugin_google_cloud_streaming
        import mycroft
        with self.assertRaises(ImportError):
            import neon_test_utils

    def test_installed_skills(self):
        self.assertEqual(xdg_data_home(), os.path.expanduser("~/.local/share"))
        skill_dir = os.path.join(xdg_data_home(), "neon", "skills")
        self.assertTrue(os.path.isdir(skill_dir))
        self.assertGreater(len(os.listdir(skill_dir)), 0)


if __name__ == '__main__':
    unittest.main()
