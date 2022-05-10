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
from neon_utils.configuration_utils import get_neon_local_config


class TestSetupDevLocal(unittest.TestCase):
    def test_config_from_setup(self):
        local_config = get_neon_local_config()
        self.assertEqual(local_config["devVars"]["devType"], "server")
        self.assertTrue(local_config["prefFlags"]["devMode"])
        self.assertEqual(local_config["stt"]["module"], "deepspeech_stream_local")
        self.assertEqual(local_config["tts"]["module"], "neon_tts_mimic")
        self.assertIsInstance(local_config["skills"]["neon_token"], str)

    def test_installed_packages(self):
        import neon_tts_plugin_mimic
        import neon_stt_plugin_deepspeech_stream_local
        import mycroft
        import neon_cli

    def test_installed_skills(self):
        local_config = get_neon_local_config()
        skill_dir = os.path.expanduser(local_config["dirVars"]["skillsDir"])
        self.assertTrue(os.path.isdir(skill_dir))
        self.assertGreater(len(os.listdir(skill_dir)), 0)


if __name__ == '__main__':
    unittest.main()
