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
import sys
import unittest
import shutil

from ovos_plugin_manager.templates.language import LanguageDetector, LanguageTranslator

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


resolved_languages = {
    "en": "en",
    "en-uk": "en-uk",
    "en-au": "en",
    "es-mx": "es-es",
    "es-es": "es-es"
}


class LanguageTests(unittest.TestCase):
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config")

    @classmethod
    def setUpClass(cls) -> None:
        os.environ["XDG_CONFIG_HOME"] = cls.CONFIG_PATH
        from neon_utils.configuration_utils import init_config_dir
        init_config_dir()

    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.exists(cls.CONFIG_PATH):
            shutil.rmtree(cls.CONFIG_PATH)
        os.environ.pop("XDG_CONFIG_HOME")

    def test_get_lang_config(self):
        from neon_core.language import get_lang_config
        config = get_lang_config()
        self.assertIsInstance(config, dict)
        self.assertIsInstance(config['internal'], str)
        self.assertIsInstance(config['user'], str)

    def test_get_language_dir_valid(self):
        from neon_core.language import get_language_dir
        base_dir = os.path.join(os.path.dirname(__file__), "lang_res")
        self.assertEqual(get_language_dir(base_dir),
                         os.path.join(base_dir, "en-us"))
        for search, result in resolved_languages.items():
            self.assertEqual(get_language_dir(base_dir, search),
                             os.path.join(base_dir, result))

    def test_get_language_dir_invalid(self):
        from neon_core.language import get_language_dir
        base_dir = os.path.join(os.path.dirname(__file__), "lang_res")
        self.assertEqual(get_language_dir(base_dir, "ru"),
                         os.path.join(base_dir, "ru"))
        self.assertEqual(get_language_dir(base_dir, "ru-ru"),
                         os.path.join(base_dir, "ru-ru"))

    def test_translator(self):
        from neon_core.language import TranslatorFactory
        translator = TranslatorFactory.create(
            {"module": "libretranslate_plug"})
        self.assertIsInstance(translator, LanguageTranslator)
        output = translator.translate("hello", "es-es", "en-us")
        self.assertEqual(output.lower(), "hola")

    def test_detector(self):
        from neon_core.language import DetectorFactory
        detector = DetectorFactory.create(
            {"module": "libretranslate_detection_plug"})
        self.assertIsInstance(detector, LanguageDetector)
        lang = detector.detect("hello")
        self.assertEqual(lang, "en")


if __name__ == '__main__':
    unittest.main()
