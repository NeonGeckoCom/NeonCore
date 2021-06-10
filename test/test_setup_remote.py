import unittest
from neon_utils.configuration_utils import get_neon_local_config


class TestSetupRemote(unittest.TestCase):
    def test_config_from_setup(self):
        local_config = get_neon_local_config()
        self.assertFalse(local_config["prefFlags"]["devMode"])
        self.assertEqual(local_config["stt"]["module"], "google_cloud_streaming")
        self.assertEqual(local_config["tts"]["module"], "polly")
        self.assertIsInstance(local_config["skills"]["neon_token"], str)

    def test_installed_packages(self):
        import neon_tts_plugin_polly
        import neon_stt_plugin_google_cloud_streaming
        import mycroft
        import neon_core_client
        with self.assertRaises(ImportError):
            import neon_test_utils
            import neon_core_server


if __name__ == '__main__':
    unittest.main()
