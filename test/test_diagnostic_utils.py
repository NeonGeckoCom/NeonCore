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
import shutil
import sys
import unittest
import neon_utils.metrics_utils

from mock import Mock

from neon_utils import get_neon_local_config

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class DiagnosticUtilsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report_metric = Mock()
        cls.config_dir = os.path.join(os.path.dirname(__file__), "test_config")
        os.makedirs(cls.config_dir)

        os.environ["NEON_CONFIG_PATH"] = cls.config_dir
        test_dir = os.path.join(os.path.dirname(__file__), "diagnostic_files")
        local_config = get_neon_local_config()
        local_config["dirVars"]["diagsDir"] = test_dir
        local_config["dirVars"]["docsDir"] = test_dir
        local_config["dirVars"]["logsDir"] = test_dir
        local_config["dirVars"]["diagsDir"] = test_dir
        local_config.write_changes()

    @classmethod
    def tearDownClass(cls) -> None:
        if os.getenv("NEON_CONFIG_PATH"):
            os.environ.pop("NEON_CONFIG_PATH")
        shutil.rmtree(cls.config_dir)

    def setUp(self) -> None:
        self.report_metric.reset_mock()
        neon_utils.metrics_utils.report_metric = self.report_metric

    def test_send_diagnostics_default(self):
        from neon_core.util.diagnostic_utils import send_diagnostics
        send_diagnostics()
        self.report_metric.assert_called_once()
        args = self.report_metric.call_args
        self.assertEqual(args.args, ("diagnostics",))
        data = args.kwargs
        self.assertIsInstance(data, dict)
        self.assertIsInstance(data["host"], str)
        self.assertIsInstance(data["configurations"], str)
        # self.assertIsInstance(data["logs"], str)
        # self.assertIsInstance(data["transcripts"], str)

    def test_send_diagnostics_no_extras(self):
        from neon_core.util.diagnostic_utils import send_diagnostics
        send_diagnostics(False, False, False)
        self.report_metric.assert_called_once()
        args = self.report_metric.call_args
        self.assertEqual(args.args, ("diagnostics",))
        data = args.kwargs
        self.assertIsInstance(data, dict)
        self.assertIsInstance(data["host"], str)
        self.assertIsNone(data["configurations"])
        self.assertIsNone(data["logs"])
        self.assertIsNone(data["transcripts"])

    def test_send_diagnostics_allow_logs(self):
        from neon_core.util.diagnostic_utils import send_diagnostics
        send_diagnostics(True, False, False)
        self.report_metric.assert_called_once()
        args = self.report_metric.call_args
        self.assertEqual(args.args, ("diagnostics",))
        data = args.kwargs
        self.assertIsInstance(data, dict)
        self.assertIsInstance(data["host"], str)
        self.assertIsNone(data["configurations"])
        # self.assertIsInstance(data["logs"], str)
        self.assertIsNone(data["transcripts"])

    def test_send_diagnostics_allow_transcripts(self):
        from neon_core.util.diagnostic_utils import send_diagnostics
        send_diagnostics(False, True, False)
        self.report_metric.assert_called_once()
        args = self.report_metric.call_args
        self.assertEqual(args.args, ("diagnostics",))
        data = args.kwargs
        self.assertIsInstance(data, dict)
        self.assertIsInstance(data["host"], str)
        self.assertIsNone(data["configurations"])
        self.assertIsNone(data["logs"])
        # self.assertIsInstance(data["transcripts"], str)

    def test_send_diagnostics_allow_config(self):
        from neon_core.util.diagnostic_utils import send_diagnostics
        send_diagnostics(False, False, True)
        self.report_metric.assert_called_once()
        args = self.report_metric.call_args
        self.assertEqual(args.args, ("diagnostics",))
        data = args.kwargs
        self.assertIsInstance(data, dict)
        self.assertIsInstance(data["host"], str)
        self.assertIsInstance(data["configurations"], str)
        self.assertIsNone(data["logs"])
        self.assertIsNone(data["transcripts"])


if __name__ == '__main__':
    unittest.main()
