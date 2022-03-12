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
import wave
from copy import deepcopy
from time import time

from mock import Mock
from mycroft_bus_client import Message
from ovos_utils.messagebus import FakeBus

from neon_core import NeonIntentService

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class TestIntentService(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bus = FakeBus()
        cls.intent_service = NeonIntentService(cls.bus)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.intent_service.shutdown()

    def test_save_utterance_transcription(self):
        self.intent_service.transcript_service = Mock()
        transcribe_time = time()
        test_message = Message("recognizer_loop:utterance",
                               {"utterances": ["test 1", "test one"],
                                "lang": "en-us"},
                               {"timing": {"transcribed": transcribe_time}})
        self.intent_service._save_utterance_transcription(test_message)
        self.intent_service.transcript_service.write_transcript.\
            assert_called_once_with(None, test_message.data["utterances"][0],
                                    transcribe_time, None)

        test_audio = os.path.join(os.path.dirname(__file__),
                                  "audio_files", "stop.wav")
        test_message.context["raw_audio"] = test_audio
        audio = wave.open(test_audio, 'r')
        audio = audio.readframes(audio.getnframes())
        self.intent_service._save_utterance_transcription(test_message)
        self.intent_service.transcript_service.write_transcript. \
            assert_called_with(None, test_message.data["utterances"][0],
                               transcribe_time, audio)

    def test_get_parsers_service_context(self):
        utterances = ["test 1", "test one"]
        lang = "en-us"
        test_message = Message("recognizer_loop:utterance",
                               {"utterances": deepcopy(utterances),
                                "lang": lang}, {})

        def mod_1_parse(utterances, lang):
            utterances.append("mod 1 parsed")
            return utterances, {"parser_context": "mod_1"}

        def mod_2_parse(utterances, lang):
            utterances.append("mod 2 parsed")
            return utterances, {"parser_context": "mod_2"}

        real_modules = self.intent_service.parser_service.loaded_modules
        mod_1 = Mock()
        mod_1.priority = 2
        mod_1.parse = mod_1_parse
        mod_2 = Mock()
        mod_2.priority = 100
        mod_2.parse = mod_2_parse
        self.intent_service.parser_service.loaded_modules = \
            {"test_mod_1": {"instance": mod_1},
             "test_mod_2": {"instance": mod_2}}
        self.intent_service._get_parsers_service_context(test_message)
        self.assertEqual(test_message.context["parser_context"], "mod_2")
        self.assertNotEqual(utterances, test_message.data['utterances'])
        self.assertEqual(len(test_message.data['utterances']),
                         len(utterances) + 2)

        mod_2.priority = 1
        self.intent_service._get_parsers_service_context(test_message)
        self.assertEqual(test_message.context["parser_context"], "mod_1")
        self.intent_service.parser_service.loaded_modules = real_modules

        valid_parsers = {"cancel", "entity_parser", "translator"}
        self.assertTrue(all([p for p in valid_parsers if p in
                        self.intent_service.parser_service.loaded_modules]))

    def test_handle_utterance(self):
        pass

    def test_converse(self):
        pass

if __name__ == "__main__":
    unittest.main()
