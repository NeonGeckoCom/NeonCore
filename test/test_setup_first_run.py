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

from multiprocessing import Process
from time import sleep

from neon_utils.logger import LOG

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from neon_core.run_neon import start_neon, stop_neon


class TestSetupFirstRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.process = Process(target=start_neon, daemon=False)
        cls.process.start()

    @classmethod
    @pytest.mark.timeout(30)
    def tearDownClass(cls) -> None:
        try:
            stop = Process(target=stop_neon, daemon=False)
            stop.start()
            stop.join(10)
            cls.process.join(5)
            stop.kill()
            cls.process.kill()
        except Exception as e:
            LOG.error(e)

    @pytest.mark.timeout(60)
    def test_messagebus_connection(self):
        from mycroft_bus_client import MessageBusClient
        bus = MessageBusClient()
        bus.run_in_thread()
        self.assertTrue(bus.started_running)
        bus.connected_event.wait(30)
        self.assertTrue(bus.connected_event.is_set())

    @pytest.mark.timeout(60)
    def test_skills_list(self):
        from mycroft_bus_client import MessageBusClient, Message
        bus = MessageBusClient()
        bus.run_in_thread()
        response = bus.wait_for_response(Message("skillmanager.list"), "mycroft.skills.list")
        self.assertIsInstance(response, Message)
        loaded_skills = response.data
        self.assertIsInstance(loaded_skills, dict)

    # TODO: Trivial test of speech, audio, enclosure modules
    # TODO: Test default skills installation
    # TODO: Test user utterance -> response


if __name__ == '__main__':
    unittest.main()
