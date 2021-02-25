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
from mycroft.language import GoogleTranslator, ApertiumTranslator, LibreTranslateTranslator


class TestGoogle(unittest.TestCase):
    def test_autodetect(self):
        t = GoogleTranslator()
        # auto detect language + to default language
        self.assertEqual(
            t.translate("O meu nome é jarbas"), "My name is jarbas")

        # auto detect language + to target language
        self.assertEqual(
            t.translate("My name is neon", target="pt"), "Meu nome é neon")

    def test_langpair(self):
        t = GoogleTranslator()
        self.assertEqual(
            t.translate("O meu nome é jarbas", source="pt", target="en"),
            "My name is jarbas")
        self.assertEqual(
            t.translate("My name is neon", source="en", target="pt"),
            "Meu nome é neon")


class TestApertium(unittest.TestCase):
    def test_autodetect(self):
        t = ApertiumTranslator()
        # TODO add auto-detect functionality using LanguageDetector modules

    def test_langpair(self):
        t = ApertiumTranslator()
        self.assertEqual(
            t.translate("My name is Jarbas", source="en", target="es"),
            "Mi nombre es Jarbas")
        self.assertEqual(
            t.translate("O meu nome é Jarbas", source="pt", target="es"),
            "Mi nombre es Jarbas")

    def test_missing_langpair(self):
        t = ApertiumTranslator()
        self.assertEqual(
            t.translate("O meu nome é jarbas", source="pt", target="en"),
            None)
        self.assertEqual(
            t.translate("My name is neon", source="en", target="pt"),
            None)


class TestLibreTranslate(unittest.TestCase):
    def test_autodetect(self):
        t = LibreTranslateTranslator()
        # TODO add auto-detect functionality using LanguageDetector modules

    def test_langpair(self):
        t = LibreTranslateTranslator()
        self.assertEqual(
            t.translate("O meu nome é jarbas", source="pt", target="en"),
            "My name is jarbas")
        self.assertEqual(
            t.translate("My name is neon", source="en", target="pt"),
            "Meu nome é neon")
        self.assertEqual(
            t.translate("My name is jarbas", source="en", target="es"),
            "Mi nombre es Jarbas")
        self.assertEqual(
            t.translate("O meu nome é Jarbas", source="pt", target="es"),
            "Mi nombre es Jarbas")

    def test_missing_langpair(self):
        t = LibreTranslateTranslator()
        # TODO check which pairs are available
        # new validate method for all modules?


if __name__ == "__main__":
    unittest.main()
