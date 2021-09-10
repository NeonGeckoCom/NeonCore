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

import os
import sys
import unittest

from ovos_plugin_manager.templates.language import LanguageDetector, LanguageTranslator

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from neon_core.language import *


class LanguageTests(unittest.TestCase):
    def test_get_lang_config(self):
        config = get_lang_config()
        self.assertIsInstance(config, dict)
        self.assertIsInstance(config['internal'], str)
        self.assertIsInstance(config['user'], str)

    def test_get_language_dir(self):
        # TODO: Write some tests for this method DM
        pass

    def test_translator(self):
        translator = TranslatorFactory.create("libretranslate_plug")
        self.assertIsInstance(translator, LanguageTranslator)
        output = translator.translate("hello", "es-es", "en-us")
        self.assertEqual(output, "hola")

    def test_detector(self):
        detector = DetectorFactory.create("libretranslate_detection_plug")
        self.assertIsInstance(detector, LanguageDetector)
        lang = detector.detect("hello")
        self.assertEqual(lang, "en")


if __name__ == '__main__':
    unittest.main()
