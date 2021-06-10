import unittest
from neon_utils.configuration_utils import get_neon_local_config


class TestSetupLocalMimic(unittest.TestCase):
    def test_config_from_setup(self):
        local_config = get_neon_local_config()
        self.assertFalse(local_config["prefFlags"]["devMode"])
        self.assertEqual(local_config["tts"]["module"], "mimic")
        self.assertIsInstance(local_config["skills"]["neon_token"], str)

    def test_installed_packages(self):
        import mycroft
        import neon_core_client
        # TODO: Check for mimic package DM
        with self.assertRaises(ImportError):
            import neon_core_server


if __name__ == '__main__':
    unittest.main()
