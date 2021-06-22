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
import mock
import unittest

from multiprocessing import Process
from time import time, sleep
from mycroft_bus_client import MessageBusClient, Message
from neon_speech.__main__ import main as neon_speech_main
from neon_audio.__main__ import main as neon_audio_main
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from neon_core.messagebus.service.__main__ import main as messagebus_service


AUDIO_FILE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "audio_files")


class TestModules(unittest.TestCase):
    bus_thread = None
    speech_thread = None
    audio_thread = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.bus_thread = Process(target=messagebus_service, daemon=False)
        cls.speech_thread = Process(target=neon_speech_main, daemon=False)
        cls.audio_thread = Process(target=neon_audio_main, daemon=False)
        cls.bus_thread.start()
        cls.speech_thread.start()
        cls.audio_thread.start()
        cls.bus = MessageBusClient()
        cls.bus.run_in_thread()
        while not cls.bus.started_running:
            sleep(1)
        sleep(45)  # TODO: Actually do something to check for modules started? DM

    @classmethod
    def tearDownClass(cls) -> None:
        cls.bus_thread.terminate()
        cls.speech_thread.terminate()
        cls.audio_thread.terminate()

    def test_get_stt_valid_file(self):
        context = {"client": "tester",
                   "ident": "12345",
                   "user": "TestRunner"}
        stt_resp = self.bus.wait_for_response(Message("neon.get_stt", {"audio_file": os.path.join(AUDIO_FILE_PATH,
                                                                                                  "stop.wav")},
                                                      context), context["ident"])
        self.assertEqual(stt_resp.context, context)
        self.assertIsInstance(stt_resp.data.get("parser_data"), dict)
        self.assertIsInstance(stt_resp.data.get("transcripts"), list)
        self.assertIn("stop", stt_resp.data.get("transcripts"))

    def test_audio_input_valid(self):
        handle_utterance = mock.Mock()
        self.bus.once("recognizer_loop:utterance", handle_utterance)
        context = {"client": "tester",
                   "ident": "11111",
                   "user": "TestRunner"}
        stt_resp = self.bus.wait_for_response(Message("neon.audio_input", {"audio_file": os.path.join(AUDIO_FILE_PATH,
                                                                                                      "stop.wav")},
                                                      context), context["ident"], 30.0)
        self.assertIsInstance(stt_resp, Message)
        for key in context:
            self.assertIn(key, stt_resp.context)
            self.assertEqual(context[key], stt_resp.context[key])
        self.assertIsInstance(stt_resp.data.get("skills_recv"), bool)
        handle_utterance.assert_called_once()

    def test_get_tts_valid_default(self):
        text = "This is a test"
        context = {"client": "tester",
                   "ident": str(time()),
                   "user": "TestRunner"}
        stt_resp = self.bus.wait_for_response(Message("neon.get_tts", {"text": text}, context),
                                              context["ident"], timeout=60)
        self.assertEqual(stt_resp.context, context)
        responses = stt_resp.data
        self.assertIsInstance(responses, dict)
        print(responses)
        self.assertEqual(len(responses), 1)
        resp = list(responses.values())[0]
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp.get("sentence"), text)


if __name__ == '__main__':
    unittest.main()
