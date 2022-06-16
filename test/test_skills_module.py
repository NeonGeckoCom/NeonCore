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

import importlib
import os
import shutil
import sys
import unittest
import wave

from copy import deepcopy
from os.path import join, dirname
from threading import Event
from time import time, sleep

from mock import Mock
from mock.mock import patch
from mycroft_bus_client import Message
from ovos_utils.messagebus import FakeBus


sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class MockEventSchedulerInterface(Mock):
    def __init__(self, *_, **__):
        super().__init__()


class TestIntentService(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from neon_core import NeonIntentService

        cls.bus = FakeBus()
        cls.intent_service = NeonIntentService(cls.bus)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.intent_service.shutdown()

    def test_save_utterance_transcription(self):
        self.intent_service.transcript_service = Mock()
        transcribe_time = time()
        test_message = Message("recognizer_loop:utterance",
                               {"utterances": ["test 1", "test one"],
                                "lang": "en-us"},
                               {"timing": {"transcribed": transcribe_time}})
        self.intent_service._save_utterance_transcription(test_message)
        self.intent_service.transcript_service.write_transcript.\
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

    def test_get_parsers_service_context(self):
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

        real_modules = self.intent_service.parser_service.loaded_modules
        mod_1 = Mock()
        mod_1.priority = 2
        mod_1.parse = mod_1_parse
        mod_2 = Mock()
        mod_2.priority = 100
        mod_2.parse = mod_2_parse
        self.intent_service.parser_service.loaded_modules = \
            {"test_mod_1": {"instance": mod_1},
             "test_mod_2": {"instance": mod_2}}
        self.intent_service._get_parsers_service_context(test_message)
        self.assertEqual(test_message.context["parser_context"], "mod_2")
        self.assertNotEqual(utterances, test_message.data['utterances'])
        self.assertEqual(len(test_message.data['utterances']),
                         len(utterances) + 2)

        mod_2.priority = 1
        self.intent_service._get_parsers_service_context(test_message)
        self.assertEqual(test_message.context["parser_context"], "mod_1")
        self.intent_service.parser_service.loaded_modules = real_modules

        valid_parsers = {"cancel", "entity_parser", "translator"}
        self.assertTrue(all([p for p in valid_parsers if p in
                        self.intent_service.parser_service.loaded_modules]))

    @patch("mycroft.skills.intent_service.IntentService.handle_utterance")
    def test_handle_utterance(self, patched):
        from neon_core import NeonIntentService

        intent_service = NeonIntentService(self.bus)

        test_message_invalid = Message("test", {"utterances": [' ', '  ']})
        intent_service.handle_utterance(test_message_invalid)
        patched.assert_not_called()

        test_message_valid = Message("test", {"utterances": ["test", "tests"]})
        intent_service.handle_utterance(test_message_valid)

        patched.assert_called_once_with(test_message_valid)
        self.assertIn("lang", test_message_valid.data)
        self.assertIn('-', test_message_valid.data['lang'])  # full code
        self.assertIsInstance(test_message_valid.context["timing"], dict)
        self.assertIsInstance(test_message_valid.context["user_profiles"],
                              list)
        self.assertIsInstance(test_message_valid.context["username"], str)

        intent_service.shutdown()


class TestSkillManager(unittest.TestCase):
    config_dir = join(dirname(__file__), "test_config")

    @classmethod
    def setUpClass(cls) -> None:
        os.environ["XDG_CONFIG_HOME"] = cls.config_dir
        from neon_core.configuration import patch_config
        patch_config({"skills": {"auto_update": True}})

    @classmethod
    def tearDownClass(cls) -> None:
        os.environ.pop("XDG_CONFIG_HOME")
        if os.path.isdir(cls.config_dir):
            shutil.rmtree(cls.config_dir)

    @patch("neon_core.skills.skill_store.SkillsStore.install_default_skills")
    @patch("mycroft.skills.skill_manager.SkillManager.run")
    def test_download_or_update_defaults(self, patched_run, patched_installer):
        from neon_core.skills.skill_manager import NeonSkillManager
        manager = NeonSkillManager(FakeBus())
        manager.run()
        patched_run.assert_called_once()
        patched_installer.assert_called_once()

        patched_installer.reset_mock()
        manager.config.update({"skills": {"auto_update": False}})
        manager.download_or_update_defaults()
        patched_installer.assert_not_called()
        manager.stop()


class TestSkillStore(unittest.TestCase):
    essential = ["https://github.com/OpenVoiceOS/skill-ovos-homescreen/tree/main"]
    config = {
        "disable_osm": False,
        "auto_update": True,
        "auto_update_interval": 1,
        "appstore_sync_interval": 1,
        "neon_token": None,
        "essential_skills": essential,
        "default_skills": "https://raw.githubusercontent.com/NeonGeckoCom/"
                          "neon_skills/TEST_ShortSkillsList/skill_lists/"
                          "TEST-SHORTLIST"
    }
    skill_dir = join(dirname(__file__), "skill_module_skills")
    bus = FakeBus()

    @classmethod
    def setUpClass(cls) -> None:
        import mycroft.skills.event_scheduler
        mocked_scheduler = MockEventSchedulerInterface
        mycroft.skills.event_scheduler.EventSchedulerInterface = \
            mocked_scheduler
        import neon_core.skills.skill_store
        importlib.reload(neon_core.skills.skill_store)

        from neon_core.skills.skill_store import SkillsStore
        cls.skill_store = SkillsStore(cls.skill_dir, cls.config, cls.bus)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.skill_store.shutdown()

    def test_00_store_init(self):
        self.assertEqual(self.skill_store.config, self.config)
        self.assertFalse(self.skill_store.disabled)
        self.assertEqual(self.skill_store.skills_dir, self.skill_dir)
        self.assertEqual(self.skill_store.bus, self.bus)
        self.assertIsNotNone(self.skill_store.osm)
        self.assertIsInstance(self.skill_store.scheduler,
                              MockEventSchedulerInterface)
        self.assertEqual(
            self.skill_store.scheduler.schedule_repeating_event.call_count, 2)

    def test_schedule_sync(self):
        pass

    def test_schedule_update(self):
        pass

    def test_handle_update(self):
        pass

    def test_handle_sync_appstores(self):
        pass

    def test_handle_load_osm(self):
        from ovos_skills_manager import OVOSSkillsManager
        self.skill_store.disabled = True
        self.assertIsNone(self.skill_store.load_osm())

        self.skill_store.disabled = False
        self.assertIsInstance(self.skill_store.load_osm(), OVOSSkillsManager)

    def test_essential_skills(self):
        self.assertFalse(self.skill_store.disabled)
        self.assertEqual(len(self.skill_store.essential_skills),
                         len(self.essential))

    def test_default_skills(self):
        self.assertFalse(self.skill_store.disabled)
        self.assertIsInstance(self.skill_store.default_skills, list)
        self.assertGreater(len(self.skill_store.default_skills), 0)

    def test_authenticate_neon(self):
        pass

    def test_deauthenticate_neon(self):
        pass

    def test_get_skill_entry(self):
        # TODO: Implement skills by ID after fixing in OSM
        # TODO: Support missing branch specs
        from ovos_skills_manager import SkillEntry
        url = "https://github.com/OpenVoiceOS/skill-ovos-homescreen/tree/main"
        # skill_id = "skill-ovos-homescreen.openvoiceos"
        url_entry = self.skill_store.get_skill_entry(url)
        self.assertIsInstance(url_entry, SkillEntry)
        # id_entry = self.skill_store.get_skill_entry(skill_id)
        # self.assertIsInstance(id_entry, SkillEntry)
        # self.assertEqual(url_entry.skill_name, id_entry.skill_name)

    def test_get_remote_entries(self):
        from neon_core.util.skill_utils import get_remote_entries
        test_urls = {
            "https://raw.githubusercontent.com/NeonGeckoCom/neon_skills/master/skill_lists/DEFAULT-SKILLS",
            "https://raw.githubusercontent.com/NeonGeckoCom/neon_skills/master/skill_lists/DEFAULT-PREMIUM-SKILLS"
        }
        for url in test_urls:
            self.assertEqual(self.skill_store.get_remote_entries(url),
                             get_remote_entries(url))

    def test_parse_config_entry(self):
        # TODO: Implement skills by ID after fixing in OSM
        from ovos_skills_manager import SkillEntry
        self.skill_store.osm.disable_appstore("local")

        valid_entry_url = self.config["default_skills"]
        valid_entry_list_url = self.config["essential_skills"]
        # valid_entry_list_id = ["skill-ovos-homescreen.openvoiceos",
        #                        "caffeinewiz.neon.neongeckocom"]

        self.skill_store.disabled = True
        self.assertEqual(self.skill_store._parse_config_entry(valid_entry_url),
                         list())
        self.skill_store.disabled = False

        # with self.assertRaises(ValueError):
        #     self.skill_store._parse_config_entry(valid_entry_list_id[0])

        with self.assertRaises(ValueError):
            self.skill_store._parse_config_entry(None)

        default_entries = self.skill_store._parse_config_entry(valid_entry_url)
        self.assertIsInstance(default_entries, list)
        self.assertTrue(all([isinstance(x, SkillEntry)
                             for x in default_entries]), default_entries)

        essential_entries = \
            self.skill_store._parse_config_entry(valid_entry_list_url)
        self.assertIsInstance(essential_entries, list)
        self.assertEqual(len(essential_entries), 1, essential_entries)
        self.assertIsInstance(essential_entries[0], SkillEntry)

        # list_entries = \
        #     self.skill_store._parse_config_entry(valid_entry_list_id)
        # self.assertIsInstance(list_entries, list)
        # self.assertEqual(len(list_entries), 2, list_entries)
        # self.assertTrue(all([isinstance(x, SkillEntry)
        #                      for x in list_entries]), list_entries)

    def test_install_skill(self):
        skill_entry = Mock()
        install_dir = self.skill_dir

        def skill_entry_installer(*_, **kwargs):
            self.assertEqual(kwargs["folder"], install_dir)
            if kwargs.get("update"):
                return True
            return False

        self.skill_store.disabled = True
        self.assertFalse(self.skill_store.install_skill(skill_entry))
        self.skill_store.disabled = False

        skill_entry.install = skill_entry_installer
        self.assertFalse(self.skill_store.install_skill(skill_entry))

        install_dir = "/tmp"
        self.assertTrue(self.skill_store.install_skill(skill_entry, "/tmp",
                                                       update=True))

    def test_install_default_skills(self):
        install_skill = Mock()
        real_install_skill = self.skill_store.install_skill
        self.skill_store.install_skill = install_skill

        self.skill_store.disabled = True
        self.assertEqual(self.skill_store.install_default_skills(), list())
        self.assertEqual(self.skill_store.install_default_skills(True), list())
        self.skill_store.disabled = False

        install_skill.reset_mock()
        skills = self.skill_store.install_default_skills(False)
        self.assertEqual(install_skill.call_count, len(skills))

        install_skill.reset_mock()
        skills = self.skill_store.install_default_skills(True)
        self.assertEqual(install_skill.call_count, len(skills))

        self.skill_store.install_skill = real_install_skill


class TestSkillService(unittest.TestCase):
    config_dir = join(dirname(__file__), "test_config")

    @classmethod
    def setUpClass(cls) -> None:
        os.environ["XDG_CONFIG_HOME"] = cls.config_dir
        if os.path.exists(cls.config_dir):
            shutil.rmtree(cls.config_dir)
        import neon_core

    @classmethod
    def tearDownClass(cls) -> None:
        os.environ.pop("XDG_CONFIG_HOME")
        if os.path.exists(cls.config_dir):
            shutil.rmtree(cls.config_dir)

    @patch("neon_core.skills.skill_store.SkillsStore.install_default_skills")
    @patch("mycroft.skills.skill_manager.SkillManager.run")
    def test_neon_skills_service(self, run, install_default):
        from neon_core.skills.service import NeonSkillService
        from neon_core.skills.skill_manager import NeonSkillManager
        from mycroft.util.process_utils import ProcessState

        config = {"skills": {
                "disable_osm": False,
                "auto_update": True,
                "directory": join(dirname(__file__), "skill_module_skills"),
                "run_gui_file_server": True
            }
        }

        started = Event()

        def started_hook():
            started.set()

        alive_hook = Mock()
        ready_hook = Mock()
        error_hook = Mock()
        stopping_hook = Mock()
        service = NeonSkillService(alive_hook, started_hook, ready_hook,
                                   error_hook, stopping_hook, config=config,
                                   daemonic=True)
        print(config["skills"])
        print(service.config['skills'])
        self.assertTrue(all(config['skills'][x] == service.config['skills'][x]
                            for x in config['skills']))
        service.bus = FakeBus()
        service.bus.connected_event = Event()
        service.start()
        started.wait(30)
        self.assertIsNotNone(service.http_server)
        self.assertTrue(service.config['skills']['auto_update'])
        install_default.assert_called_once()
        run.assert_called_once()

        self.assertIsInstance(service.skill_manager, NeonSkillManager)
        service.skill_manager.status.state = ProcessState.ALIVE
        sleep(1)
        alive_hook.assert_called_once()
        service.skill_manager.status.state = ProcessState.READY
        sleep(1)
        ready_hook.assert_called_once()

        service.shutdown()
        stopping_hook.assert_called_once()
        service.join(10)


if __name__ == "__main__":
    unittest.main()
