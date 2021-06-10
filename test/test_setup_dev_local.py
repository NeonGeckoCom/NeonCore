import unittest
from neon_utils.configuration_utils import get_neon_local_config


class TestSetupDevLocal(unittest.TestCase):
    def test_config_from_setup(self):
        local_config = get_neon_local_config()
        self.assertTrue(local_config["prefFlags"]["devMode"])
        self.assertEqual(local_config["stt"]["module"], "deepspeech_stream_local")
        self.assertEqual(local_config["tts"]["module"], "mozilla_remote")

    def test_installed_packages(self):
        import neon_tts_plugin_mozilla_remote
        import neon_stt_plugin_deepspeech_stream_local
        import neon_test_utils


if __name__ == '__main__':
    unittest.main()
