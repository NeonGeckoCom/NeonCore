# -*- coding: iso-8859-15 -*-
#
# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import unittest
from mycroft.language import GoogleTranslator


class TestGoogle(unittest.TestCase):
    def test_tx(self):
        t = GoogleTranslator()
        # auto detect language + to default language
        self.assertEqual(
            t.translate("O meu nome é jarbas"), "My name is jarbas")

        # auto detect language + to target language
        self.assertEqual(
            t.translate("My name is neon", target="pt"), "Meu nome é neon")


if __name__ == "__main__":
    unittest.main()
