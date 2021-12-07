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
from multiprocessing import Process
from threading import Thread
from time import sleep

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from neon_core.util.signal_utils import *
from neon_core.messagebus.service.__main__ import main as messagebus_service


class TestSignalUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bus_thread = Process(target=messagebus_service, daemon=False)
        cls.bus_thread.start()
        cls.signal_manager = SignalManager()
        # sleep(15)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.bus_thread.terminate()

    def test_create_signal(self):
        self.assertTrue(create_signal("test_signal"))
        self.assertTrue(create_signal("test_signal"))
        self.assertIsInstance(self.signal_manager._signals["test_signal"], Signal)
        self.assertTrue(self.signal_manager._signals["test_signal"].is_set)

    def test_check_for_signal(self):
        self.assertFalse(check_for_signal("test_signal"))
        create_signal("test_signal")
        self.assertTrue(check_for_signal("test_signal", -1))
        self.assertTrue(check_for_signal("test_signal", 60))
        self.assertTrue(check_for_signal("test_signal"))
        self.assertFalse(check_for_signal("test_signal"))
        create_signal("test_signal")
        self.assertTrue(check_for_signal("test_signal", 15))
        sleep(2)
        self.assertTrue(check_for_signal("test_signal", 15))
        self.assertFalse(check_for_signal("test_signal", 2))
        self.assertFalse(check_for_signal("test_signal"))

    def test_wait_for_signal_create(self):
        def create_testing_signal():
            sleep(3)
            create_signal("test_signal")
        check_for_signal("test_signal")
        self.assertFalse(wait_for_signal_create("test_signal", 1))
        Thread(target=create_testing_signal).start()
        self.assertTrue(wait_for_signal_create("test_signal", 5))
        self.assertTrue(check_for_signal("test_signal"))

    def test_wait_for_signal_clear(self):
        def _clear_signal():
            sleep(3)
            self.assertTrue(check_for_signal("test_signal"))
        check_for_signal("test_signal")
        self.assertFalse(wait_for_signal_clear("test_signal", 1))
        self.assertTrue(create_signal("test_signal"))
        self.assertTrue(wait_for_signal_clear("test_signal", 1))
        Thread(target=_clear_signal).start()
        self.assertFalse(wait_for_signal_clear("test_signal", 10))
        self.assertFalse(check_for_signal("test_signal"))

    def test_threaded_signal_handling(self):
        create_results = []
        check_results = []

        def _create_signal(n):
            stat = create_signal(f"test_signal{n}")
            create_results.append(stat)

        def _check_signal(n):
            sleep(1)
            stat = check_for_signal(f"test_signal{n}", -1)
            check_results.append(stat)

        threads = []
        for i in range(8):
            t = Thread(target=_create_signal, args=(i,))
            threads.append(t)
            t.start()
            t = Thread(target=_check_signal, args=(i,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        self.assertTrue(all(create_results))
        self.assertTrue(all(check_results))
        self.assertEqual(8, len(create_results), len(check_results))


if __name__ == '__main__':
    unittest.main()
