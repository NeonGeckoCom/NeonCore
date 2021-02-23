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
from mycroft.language import Pycld2Detector, Pycld3Detector, \
    FastLangDetector, LangDetectDetector, GoogleDetector, \
    LibreTranslateDetector


class TestLibreTranslate(unittest.TestCase):
    def test_detect(self):
        d = LibreTranslateDetector()
        self.assertEqual(d.detect("My name is Neon"), "en")
        self.assertEqual(d.detect("O meu nome é Jarbas"), "pt")
        self.assertEqual(d.detect("O meu nome é neon"), "pt")
        self.assertNotEqual(d.detect("My name is jarbas"), "en")


class TestGoogle(unittest.TestCase):
    def test_detect(self):
        d = GoogleDetector()
        self.assertEqual(d.detect("My name is Neon"), "en")
        self.assertEqual(d.detect("O meu nome é Jarbas"), "pt")
        self.assertEqual(d.detect("My name is jarbas"), "en")
        self.assertEqual(d.detect("O meu nome é neon"), "pt")


class TestCld2(unittest.TestCase):
    def test_detect(self):
        d = Pycld2Detector()
        self.assertEqual(d.detect("My name is Neon"), "en")
        self.assertEqual(d.detect("O meu nome é Jarbas"), "pt")
        self.assertEqual(d.detect("My name is jarbas"), "en")

    def test_known_failures(self):
        d = Pycld2Detector()
        self.assertNotEqual(d.detect("O meu nome é neon"), "pt")


class TestCld3(unittest.TestCase):
    def test_detect(self):
        d = Pycld3Detector()
        self.assertEqual(d.detect("My name is Neon"), "en")
        self.assertEqual(d.detect("O meu nome é Jarbas"), "pt")

    def test_known_failures(self):
        d = Pycld3Detector()
        self.assertNotEqual(d.detect("My name is jarbas"), "en")
        self.assertNotEqual(d.detect("O meu nome é neon"), "pt")


class TestFastLang(unittest.TestCase):
    def test_detect(self):
        d = FastLangDetector()
        self.assertEqual(d.detect("My name is Neon"), "en")
        self.assertEqual(d.detect("O meu nome é Jarbas"), "pt")
        self.assertEqual(d.detect("My name is jarbas"), "en")
        self.assertEqual(d.detect("O meu nome é neon"), "pt")


class TestLangDetect(unittest.TestCase):
    def test_detect(self):
        d = LangDetectDetector()
        self.assertEqual(d.detect("My name is Neon"), "en")
        self.assertEqual(d.detect("O meu nome é Jarbas"), "pt")
        self.assertEqual(d.detect("O meu nome é neon"), "pt")

    def test_known_failures(self):
        d = LangDetectDetector()
        self.assertNotEqual(d.detect("My name is jarbas"), "en")


if __name__ == "__main__":
    unittest.main()
