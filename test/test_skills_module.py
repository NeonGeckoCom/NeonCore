# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2025 Neongecko.com Inc.
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
import wave

from pytest import mark
from mock import Mock, patch
from copy import deepcopy
from os.path import join, dirname, expanduser, isdir
from threading import Event
from time import time
from ovos_bus_client import Message
from ovos_utils.messagebus import FakeBus
from ovos_utils.xdg_utils import xdg_data_home
from ovos_plugin_manager.templates.language import LanguageTranslator

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class MockEventSchedulerInterface(Mock):
    def __init__(self, *_, **__):
        super().__init__()


class MockTranslator(LanguageTranslator):
    def __init__(self):
        super(MockTranslator, self).__init__()
        self.supported_langs = []

    @property
    def available_languages(self) -> set:
        return set(self.supported_langs)


class TestSkillService(unittest.TestCase):
    config_dir = join(dirname(__file__), "test_config")

    @classmethod
    def setUpClass(cls) -> None:
        os.environ["XDG_CONFIG_HOME"] = cls.config_dir

    @classmethod
    def tearDownClass(cls) -> None:
        os.environ.pop("XDG_CONFIG_HOME")
        if os.path.exists(cls.config_dir):
            shutil.rmtree(cls.config_dir)

    @patch("ovos_core.skill_manager.SkillManager.run")
    def test_neon_skills_service(self, run):
        from neon_core.skills.service import NeonSkillService
        from neon_core.skills.skill_manager import NeonSkillManager

        config = {"skills": {
            "disable_osm": False,
            "auto_update": True,
            "directory": join(dirname(__file__), "skill_module_skills"),
            "run_gui_file_server": True
        },
            "location": {"timezone": {"code": "America/Los_Angeles",
                                      "name": "Pacific Standard Time",
                                      "dstOffset": 3600000,
                                      "offset": -28800000},
                         "coordinate": {"latitude": 47.482880,
                                        "longitude": -122.217064},
                         "city": {"code": "Renton",
                                  "name": "Renton",
                                  "state": {"code": "WA", "name": "Washington",
                                            "country": {"code": "US",
                                                        "name": "United States"}
                                            }
                                  }
                         },
        }

        started = Event()

        def ready_hook(*_, **__):
            started.set()

        alive_hook = Mock()
        started_hook = Mock()
        error_hook = Mock()
        stopping_hook = Mock()
        run.side_effect = ready_hook
        service = NeonSkillService(alive_hook, started_hook, ready_hook,
                                   error_hook, stopping_hook, config=config,
                                   daemonic=True, bus=FakeBus())
        from neon_core.configuration import Configuration
        self.assertEqual(service.config, Configuration())
        self.assertIsInstance(Configuration()["location"]["timezone"], dict)
        self.assertTrue(all(config['skills'][x] == service.config['skills'][x]
                            for x in config['skills']))
        self.assertIsInstance(service.config['location'], dict, service.config)
        service.bus = FakeBus()
        service.bus.connected_event = Event()
        service.start()
        self.assertTrue(started.wait(30))
        self.assertTrue(service.config['skills']['auto_update'])
        # install_default.assert_called_once()

        # Check mock method called
        run.assert_called_once()
        # Mock status change calls from mocked `run`
        self.assertIsInstance(service.skill_manager, NeonSkillManager)
        service.skill_manager.status.set_alive()
        alive_hook.assert_called_once()
        service.skill_manager.status.set_ready()
        started_hook.assert_called_once()

        service.shutdown()
        stopping_hook.assert_called_once()
        service.join(10)

    @patch("ovos_plugin_manager.skills.get_plugin_skills")
    @patch("ovos_plugin_manager.skills.get_skill_directories")
    def test_get_skill_dirs(self, skill_dirs, plugin_skills):
        from neon_core.skills.service import NeonSkillService

        test_dir = join(dirname(__file__), "get_skill_dirs_skills")
        skill_dirs.return_value = [join(test_dir, "extra_dir_1"),
                                   join(test_dir, "extra_dir_2")]
        plugin_skills.return_value = ([join(test_dir, "plugins",
                                            "skill-plugin")],
                                      ["skill-plugin.neongeckocom"])

        skill_dirs = NeonSkillService(bus=FakeBus())._get_skill_dirs()
        # listdir doesn't guarantee order, base skill directory order matters
        self.assertEqual(set(skill_dirs),
                         {join(test_dir, "plugins", "skill-plugin"),
                          join(test_dir, "extra_dir_1",
                               "skill-test-1.neongeckocom"),
                          join(test_dir, "extra_dir_1",
                               "skill-test-2.neongeckocom"),
                          join(test_dir, "extra_dir_1",
                               "skill-test-3.neongeckocom"),
                          join(test_dir, "extra_dir_2",
                               "skill-test-1.neongeckocom")
                          })
        self.assertEqual(skill_dirs[0],
                         join(test_dir, "plugins", "skill-plugin"))
        self.assertEqual(skill_dirs[-1],
                         join(test_dir, "extra_dir_2",
                              "skill-test-1.neongeckocom"))


class TestIntentService(unittest.TestCase):
    bus = FakeBus()
    test_config_dir = join(dirname(__file__), "test_config")

    @classmethod
    def setUpClass(cls) -> None:
        # Import to set default config path
        import neon_core

        os.environ["XDG_CONFIG_HOME"] = cls.test_config_dir
        import ovos_config
        import importlib
        importlib.reload(ovos_config.meta)
        meta = ovos_config.meta.get_ovos_config()
        assert meta['default_config_path'].endswith('neon.yaml')
        importlib.reload(ovos_config.locations)
        assert ovos_config.locations.DEFAULT_CONFIG == meta['default_config_path']
        import ovos_config.models
        importlib.reload(ovos_config.models)
        importlib.reload(ovos_config.config)
        importlib.reload(ovos_config)
        assert ovos_config.config.Configuration.default.path == meta['default_config_path']

        from neon_core.skills.intent_service import NeonIntentService
        cls.intent_service = NeonIntentService(cls.bus)
        assert set(cls.intent_service.config['utterance_transformers'].keys()) \
               == {"neon_utterance_translator_plugin",
                   "neon_utterance_normalizer_plugin"}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.intent_service.shutdown()
        os.environ.pop("XDG_CONFIG_HOME")
        shutil.rmtree(cls.test_config_dir)

    def test_save_utterance_transcription(self):
        self.intent_service.transcript_service = Mock()
        transcribe_time = time()
        test_message = Message("recognizer_loop:utterance",
                               {"utterances": ["test 1", "test one"],
                                "lang": "en-us"},
                               {"timing": {"transcribed": transcribe_time}})
        self.intent_service._save_utterance_transcription(test_message)
        self.intent_service.transcript_service.write_transcript. \
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

    def test_get_transformers_service_context(self):
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

        real_modules = self.intent_service.transformers.loaded_modules
        mod_1 = Mock()
        mod_1.priority = 2
        mod_1.transform = mod_1_parse
        mod_2 = Mock()
        mod_2.priority = 1
        mod_2.transform = mod_2_parse
        self.intent_service.transformers.loaded_modules = \
            {"test_mod_1": mod_1,
             "test_mod_2": mod_2}
        self.intent_service._get_parsers_service_context(test_message, lang)
        self.assertEqual(test_message.context["parser_context"], "mod_2")
        self.assertNotEqual(utterances, test_message.data['utterances'])
        self.assertEqual(len(test_message.data['utterances']),
                         len(utterances) + 2)

        mod_2.priority = 100
        self.intent_service._get_parsers_service_context(test_message, lang)
        self.assertEqual(test_message.context["parser_context"], "mod_1")
        self.intent_service.transformers.loaded_modules = real_modules

        valid_parsers = {"cancel", "entity_parser", "translator"}
        self.assertTrue(all([p for p in valid_parsers if p in
                             self.intent_service.transformers.loaded_modules]))

    @patch("ovos_core.intent_services.IntentService.handle_utterance")
    def test_handle_utterance(self, patched):
        test_message_invalid = Message("test", {"utterances": [' ', '  ']})
        self.intent_service.handle_utterance(test_message_invalid)
        patched.assert_not_called()

        test_message_valid = Message("test", {"utterances": ["test", "tests"]})
        self.intent_service.handle_utterance(test_message_valid)

        patched.assert_called_once_with(test_message_valid)
        self.assertIn("lang", test_message_valid.data)
        self.assertIn('-', test_message_valid.data['lang'])  # full code
        self.assertIsInstance(test_message_valid.context["timing"], dict)
        self.assertIsInstance(test_message_valid.context["user_profiles"],
                              list)
        self.assertIsInstance(test_message_valid.context["username"], str)

        message = Message('recognizer_loop:utterance',
                          {'utterances': ['test']}, {})
        patched.reset_mock()
        self.bus.emit(message)
        patched.assert_called_once_with(message)

    def test_handle_supported_languages(self):
        handled = Event()
        response: Message = None

        def _handle_languages_response(msg):
            nonlocal response
            response = msg
            handled.set()

        self.bus.on('neon.languages.skills.response',
                    _handle_languages_response)

        # Patch things
        real_config = self.intent_service.language_config
        self.assertIn("neon_utterance_translator_plugin",
                      self.intent_service.transformers.loaded_modules,
                      self.intent_service.transformers.loaded_modules)
        translator = self.intent_service.transformers.loaded_modules.get(
            'neon_utterance_translator_plugin')
        real_plug = translator.translator
        translator.translator = MockTranslator()

        # Test default intent languages no translation
        self.intent_service.language_config = {
            'supported_langs': None
        }
        translator.translator.supported_langs = []
        handled.clear()
        self.bus.emit(Message('neon.languages.skills'))
        handled.wait(3)
        self.assertEqual(response.data['native_langs'], ['en'])
        self.assertEqual(response.data['translate_langs'], [])
        self.assertEqual(response.data['skill_langs'], ['en'])

        # Test supported languages and translation
        translator.translator.supported_langs = ['en', 'pt', 'es']
        self.intent_service.language_config = {
            'supported_langs': ['en', 'uk', 'pt']
        }
        handled.clear()
        self.bus.emit(Message('neon.languages.skills'))
        handled.wait(3)
        self.assertEqual(response.data['native_langs'], ['en', 'uk', 'pt'])
        self.assertEqual(set(response.data['translate_langs']),
                         {'en', 'pt', 'es'})
        self.assertEqual(set(response.data['skill_langs']),
                         {'en', 'pt', 'es', 'uk'})
        self.assertEqual(len(response.data['skill_langs']),
                         len(set(response.data['skill_langs'])))

        self.intent_service.language_config = real_config
        translator.translator = real_plug


class TestSkillManager(unittest.TestCase):
    config_dir = join(dirname(__file__), "test_config")

    @classmethod
    def setUpClass(cls) -> None:
        os.environ["XDG_CONFIG_HOME"] = cls.config_dir

    @classmethod
    def tearDownClass(cls) -> None:
        os.environ.pop("XDG_CONFIG_HOME")
        if os.path.isdir(cls.config_dir):
            shutil.rmtree(cls.config_dir)

    @mark.skip("Skill directory handling is deprecated")
    @patch("ovos_core.skill_manager.SkillManager.run")
    def test_get_default_skills_dir(self, _):
        from neon_core.skills.skill_manager import NeonSkillManager
        manager = NeonSkillManager(FakeBus())
        manager.config = dict(manager.config)  # Override Configuration to test

        # Default, no config
        manager.config['skills'] = {}
        default_dir = manager.get_default_skills_dir()
        self.assertEqual(default_dir, join(xdg_data_home(), "neon", "skills"))

        # Default, empty extra_directories
        manager.config['skills']['extra_directories'] = []
        default_dir = manager.get_default_skills_dir()
        self.assertEqual(default_dir, join(xdg_data_home(), "neon", "skills"))

        # Default, invalid extra_directories
        manager.config['skills']['extra_directories'] = "/skills"
        default_dir = manager.get_default_skills_dir()
        self.assertEqual(default_dir, join(xdg_data_home(), "neon", "skills"))

        # extra_directories valid spec
        manager.config['skills']['extra_directories'] = '~/skills'
        default_dir = manager.get_default_skills_dir()
        self.assertEqual(default_dir, expanduser('~/skills'))
        self.assertTrue(isdir(expanduser("~/skills")))

        # directory invalid spec
        manager.config['skills']['directory'] = "/skills"
        default_dir = manager.get_default_skills_dir()
        self.assertEqual(default_dir, join(xdg_data_home(), "neon", "skills"))

        # directory valid spec
        manager.config['skills']['directory'] = "~/neon-skills"
        default_dir = manager.get_default_skills_dir()
        self.assertEqual(default_dir, expanduser('~/neon-skills'))
        self.assertTrue(isdir(expanduser("~/neon-skills")))

    def test_wait_until_skills_ready(self):
        from neon_core.skills.skill_manager import NeonSkillManager
        manager = NeonSkillManager(FakeBus())
        manager._network_skill_timeout = 1

        # No ready settings is ready
        manager.config['ready_settings'] = []
        self.assertTrue(manager._wait_until_skills_ready())

        # Check network skills not ready
        manager.config['ready_settings'] = ['network_skills']
        self.assertFalse(manager._wait_until_skills_ready())

        # Check internet skills not ready
        manager.config['ready_settings'].append('internet_skills')
        self.assertFalse(manager._wait_until_skills_ready())

        # Check skills are loaded
        manager._network_loaded.set()
        manager._internet_loaded.set()
        self.assertTrue(manager._wait_until_skills_ready())

    def test_check_device_ready(self):
        from neon_core.skills.skill_manager import NeonSkillManager
        manager = NeonSkillManager(FakeBus())

        on_ready = Mock()
        manager.bus.on("mycroft.ready", on_ready)

        # No services to wait for
        manager.config['ready_settings'] = []
        manager._check_device_ready()
        on_ready.assert_called_once()


if __name__ == "__main__":
    unittest.main()
