import unittest
from neon_utils.configuration_utils import get_neon_local_config


class TestSetupLocalMimic(unittest.TestCase):
    def test_config_from_setup(self):
        local_config = get_neon_local_config()
        self.assertFalse(local_config["prefFlags"]["devMode"])
        self.assertEqual(local_config["stt"]["module"], "deepspeech_stream_local")
        self.assertEqual(local_config["tts"]["module"], "mimic")
        self.assertIsInstance(local_config["skills"]["neon_token"], str)

    def test_installed_packages(self):
        import neon_tts_plugin_mozilla_remote
        import neon_stt_plugin_deepspeech_stream_local
        import mycroft
        import neon_core_client
        with self.assertRaises(ImportError):
            import neon_core_server


if __name__ == '__main__':
    unittest.main()
