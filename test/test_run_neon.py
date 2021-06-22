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

import os.path
import sys
import unittest
import pytest

from time import time, sleep
from multiprocessing import Process
from neon_utils.log_utils import LOG, LOG_DIR
from mycroft_bus_client import MessageBusClient, Message

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from neon_core.run_neon import start_neon, stop_neon

AUDIO_FILE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "audio_files")
# LOG_FILES = ("bus.log", "speech.log", "skills.log", "audio.log", "gui.log")


class TestRunNeon(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.process = Process(target=start_neon, daemon=False)
        cls.process.start()
        cls.bus = MessageBusClient()
        cls.bus.run_in_thread()
        sleep(30)  # TODO: This shouldn't be necessary? DM
        # for log in LOG_FILES:
        #     with open(os.path.join(LOG_DIR, log)) as f:
        #         LOG.info(log)
        #         LOG.info(f.read())

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.bus.emit(Message("neon.shutdown"))
            cls.bus.close()
            cls.process.join(30)
            if cls.process.is_alive():
                stop = Process(target=stop_neon, daemon=False)
                stop.start()
                stop.join(60)
                cls.process.join(15)
            if cls.process.is_alive:
                raise ChildProcessError("Process Not Killed!")
        except Exception as e:
            LOG.error(e)

    def setUp(self) -> None:
        self.bus.connected_event.wait(30)
        while not self.bus.started_running:
            sleep(1)

    @pytest.mark.timeout(60)
    def test_messagebus_connection(self):
        from mycroft_bus_client import MessageBusClient
        bus = MessageBusClient()
        bus.run_in_thread()
        self.assertTrue(bus.started_running)
        bus.connected_event.wait(10)
        self.assertTrue(bus.connected_event.is_set())
        bus.close()

    @pytest.mark.timeout(60)
    def test_speech_module(self):
        context = {"client": "tester",
                   "ident": str(round(time())),
                   "user": "TestRunner"}
        stt_resp = self.bus.wait_for_response(Message("neon.get_stt",
                                                 {"audio_file": os.path.join(AUDIO_FILE_PATH, "stop.wav")},
                                                 context), context["ident"])
        self.assertEqual(stt_resp.context, context)
        self.assertIsInstance(stt_resp.data.get("parser_data"), dict)
        self.assertIsInstance(stt_resp.data.get("transcripts"), list)
        self.assertIn("stop", stt_resp.data.get("transcripts"))

    def test_audio_module(self):
        text = "This is a test"
        context = {"client": "tester",
                   "ident": str(time()),
                   "user": "TestRunner"}
        stt_resp = self.bus.wait_for_response(Message("neon.get_tts", {"text": text}, context),
                                         context["ident"], timeout=60)
        self.assertEqual(stt_resp.context, context)
        responses = stt_resp.data
        self.assertIsInstance(responses, dict)
        self.assertEqual(len(responses), 1)
        resp = list(responses.values())[0]
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp.get("sentence"), text)

    @pytest.mark.timeout(60)
    def test_skills_list(self):
        response = self.bus.wait_for_response(Message("skillmanager.list"), "mycroft.skills.list")
        self.assertIsInstance(response, Message)
        loaded_skills = response.data
        self.assertIsInstance(loaded_skills, dict)

    # def test_skills_module(self):
    #     bus = MessageBusClient()
    #     bus.run_in_thread()
    #     bus.connected_event.wait(10)
    # TODO: Trivial test of enclosure module
    # TODO: Test default skills installation
    # TODO: Test user utterance -> response


if __name__ == '__main__':
    unittest.main()
