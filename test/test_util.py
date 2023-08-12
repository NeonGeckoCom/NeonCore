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
from os.path import join, dirname, isfile, isdir

import neon_utils.metrics_utils

from mock import Mock


sys.path.append(os.path.dirname(os.path.dirname(__file__)))


TEST_SKILLS_NO_AUTH = [
    "https://github.com/NeonGeckoCom/alerts.neon/tree/dev",
    "https://github.com/NeonGeckoCom/caffeinewiz.neon/tree/dev",
    "https://github.com/NeonGeckoCom/launcher.neon/tree/dev"
]

TEST_SKILLS_WITH_PIP = [
    "https://github.com/NeonGeckoCom/skill-date_time/tree/dev",
    "git+https://github.com/NeonGeckoCom/malls-parser-skill",
    "neon-skill-support_helper"
]

TEST_SKILLS_WITH_AUTH = [
    "https://github.com/NeonGeckoCom/i-like-brands.neon/tree/dev",
    "https://github.com/NeonGeckoCom/i-like-coupons.neon/tree/dev"
]
SKILL_DIR = os.path.join(os.path.dirname(__file__), "test_skills")
SKILL_CONFIG = {
    "default_skills": "https://raw.githubusercontent.com/NeonGeckoCom/neon_skills/master/skill_lists/"
                      "DEFAULT-SKILLS-DEV",
    "neon_token": os.environ.get("GITHUB_TOKEN"),
    "directory": SKILL_DIR
}


class SkillUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        if os.path.exists(SKILL_DIR):
            shutil.rmtree(SKILL_DIR)
        os.makedirs(SKILL_DIR)

    def tearDown(self) -> None:
        if os.path.exists(SKILL_DIR):
            shutil.rmtree(SKILL_DIR)

    def test_get_remote_entries(self):
        from neon_core.util.skill_utils import get_remote_entries
        from ovos_skills_manager.session import set_github_token,\
            clear_github_token
        set_github_token(SKILL_CONFIG["neon_token"])
        skills_list = get_remote_entries(SKILL_CONFIG["default_skills"])
        clear_github_token()
        self.assertIsInstance(skills_list, list)
        self.assertTrue(len(skills_list) > 0)
        self.assertTrue(all(skill.startswith("https://github.com")
                            for skill in skills_list))

    def test_install_skills_from_list_no_auth(self):
        from neon_core.util.skill_utils import install_skills_from_list
        install_skills_from_list(TEST_SKILLS_NO_AUTH, SKILL_CONFIG)
        skill_dirs = [d for d in os.listdir(SKILL_DIR)
                      if os.path.isdir(os.path.join(SKILL_DIR, d))]
        self.assertEqual(len(skill_dirs), len(TEST_SKILLS_NO_AUTH))
        self.assertIn("alerts.neon.neongeckocom", skill_dirs)

    def test_install_skills_from_list_with_auth(self):
        from neon_core.util.skill_utils import install_skills_from_list
        install_skills_from_list(TEST_SKILLS_WITH_AUTH, SKILL_CONFIG)
        skill_dirs = [d for d in os.listdir(SKILL_DIR)
                      if os.path.isdir(os.path.join(SKILL_DIR, d))]
        self.assertEqual(len(skill_dirs), len(TEST_SKILLS_WITH_AUTH))
        self.assertIn("i-like-brands.neon.neongeckocom", skill_dirs)

    def test_install_skills_default(self):
        from neon_core.util.skill_utils import install_skills_default,\
            get_remote_entries
        install_skills_default(SKILL_CONFIG)
        skill_dirs = [d for d in os.listdir(SKILL_DIR) if
                      os.path.isdir(os.path.join(SKILL_DIR, d))]
        self.assertEqual(
            len(skill_dirs),
            len(get_remote_entries(SKILL_CONFIG["default_skills"])),
            f"{skill_dirs}\n\n"
            f"{get_remote_entries(SKILL_CONFIG['default_skills'])}")

    def test_install_skills_with_pip(self):
        from neon_core.util.skill_utils import install_skills_from_list
        install_skills_from_list(TEST_SKILLS_WITH_PIP, SKILL_CONFIG)
        skill_dirs = [d for d in os.listdir(SKILL_DIR)
                      if os.path.isdir(os.path.join(SKILL_DIR, d))]
        self.assertEqual(len(skill_dirs), 1)
        self.assertIn("skill-date_time.neongeckocom", skill_dirs)

        returned = os.system("pip show neon-skill-support-helper")
        self.assertEqual(returned, 0)

    def test_get_neon_skills_data(self):
        from neon_core.util.skill_utils import get_neon_skills_data
        from ovos_skills_manager.github.utils import normalize_github_url
        neon_skills = get_neon_skills_data()
        self.assertIsInstance(neon_skills, dict)
        for skill in neon_skills:
            self.assertIsInstance(neon_skills[skill], dict)
            self.assertEqual(skill,
                             normalize_github_url(neon_skills[skill]["url"]))

    def test_install_local_skills(self):
        import importlib
        import ovos_skills_manager.requirements
        import neon_core.util.skill_utils
        importlib.reload(neon_core.util.skill_utils)
        install_pip_deps = Mock()
        install_sys_deps = Mock()
        ovos_skills_manager.requirements.pip_install = install_pip_deps
        ovos_skills_manager.requirements.install_system_deps = install_sys_deps

        install_local_skills = neon_core.util.skill_utils.install_local_skills

        local_skills_dir = os.path.join(os.path.dirname(__file__),
                                        "local_skills")

        installed = install_local_skills(local_skills_dir)
        num_installed = len(installed)
        self.assertEqual(installed, os.listdir(local_skills_dir))
        self.assertEqual(num_installed, install_pip_deps.call_count)
        self.assertEqual(num_installed, install_sys_deps.call_count)

    def test_write_pip_constraints_to_file(self):
        from neon_core.util.skill_utils import _write_pip_constraints_to_file
        from neon_utils.packaging_utils import get_package_dependencies
        real_deps = get_package_dependencies("neon-core")
        real_deps = [f'{c.split("[")[0]}{c.split("]")[1]}' if '[' in c
                     else c for c in real_deps if '@' not in c]
        test_outfile = os.path.join(os.path.dirname(__file__),
                                    "constraints.txt")
        _write_pip_constraints_to_file(test_outfile)
        with open(test_outfile) as f:
            read_deps = f.read().split('\n')
        self.assertTrue(all((d in read_deps for d in real_deps)))

        try:
            _write_pip_constraints_to_file()
            self.assertTrue(os.path.isfile("/etc/mycroft/constraints.txt"))
            with open("/etc/mycroft/constraints.txt") as f:
                deps = f.read().split('\n')
            self.assertTrue(all((d in deps for d in real_deps)))
        except Exception as e:
            self.assertIsInstance(e, PermissionError)
        os.remove(test_outfile)

    def test_set_osm_constraints_file(self):
        import ovos_skills_manager.requirements
        from neon_core.util.skill_utils import set_osm_constraints_file
        set_osm_constraints_file(__file__)
        self.assertEqual(ovos_skills_manager.requirements.DEFAULT_CONSTRAINTS,
                         __file__)

    def test_skill_class_patches(self):
        import neon_core.skills  # Import to do all the patching
        from neon_utils.skills.mycroft_skill import PatchedMycroftSkill
        from mycroft.skills import MycroftSkill
        from mycroft import MycroftSkill as MycroftSkill1
        from mycroft.skills.mycroft_skill import MycroftSkill as MycroftSkill2
        from mycroft.skills.core import MycroftSkill as MycroftSkill3
        from mycroft.skills.fallback_skill import FallbackSkill
        from mycroft import FallbackSkill as FallbackSkill1
        from mycroft.skills.core import FallbackSkill as FallbackSkill2
        from mycroft.skills.common_play_skill import CommonPlaySkill
        from mycroft.skills.common_query_skill import CommonQuerySkill
        from mycroft.skills.common_iot_skill import CommonIoTSkill

        self.assertEqual(MycroftSkill, PatchedMycroftSkill)
        self.assertEqual(MycroftSkill1, PatchedMycroftSkill)
        self.assertEqual(MycroftSkill2, PatchedMycroftSkill)
        self.assertEqual(MycroftSkill3, PatchedMycroftSkill)

        self.assertEqual(FallbackSkill1, FallbackSkill)
        self.assertEqual(FallbackSkill2, FallbackSkill)

        self.assertTrue(issubclass(FallbackSkill, PatchedMycroftSkill))
        self.assertTrue(issubclass(CommonPlaySkill, PatchedMycroftSkill))
        self.assertTrue(issubclass(CommonQuerySkill, PatchedMycroftSkill))
        self.assertTrue(issubclass(CommonIoTSkill, PatchedMycroftSkill))

        from ovos_workshop.skills.mycroft_skill import MycroftSkill as Patched
        from ovos_workshop.skills import MycroftSkill as Patched2
        from ovos_workshop.skills.ovos import MycroftSkill as Patched3
        self.assertEqual(Patched, PatchedMycroftSkill)
        self.assertEqual(Patched2, PatchedMycroftSkill)
        self.assertEqual(Patched3, PatchedMycroftSkill)

        from ovos_workshop.skills.ovos import OVOSSkill
        from ovos_workshop.skills import OVOSSkill as OVOSSkill2
        self.assertTrue(issubclass(OVOSSkill, PatchedMycroftSkill))
        self.assertEqual(OVOSSkill, OVOSSkill2)

        from neon_utils.skills import NeonFallbackSkill, NeonSkill
        self.assertTrue(issubclass(NeonFallbackSkill, PatchedMycroftSkill))
        self.assertTrue(issubclass(NeonSkill, PatchedMycroftSkill))
        self.assertTrue(issubclass(NeonFallbackSkill, OVOSSkill))
        self.assertTrue(issubclass(NeonFallbackSkill, NeonSkill))

        from neon_utils.skills.neon_fallback_skill import NeonFallbackSkill as \
            NeonFallbackSkill2
        from neon_utils.skills.neon_skill import NeonSkill as NeonSkill2
        self.assertEqual(NeonFallbackSkill, NeonFallbackSkill2)
        self.assertEqual(NeonSkill, NeonSkill2)

        from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill
        self.assertTrue(issubclass(OVOSCommonPlaybackSkill,
                                   PatchedMycroftSkill))

        try:
            from ovos_workshop.skills.common_query_skill import CommonQuerySkill
            self.assertTrue(issubclass(CommonQuerySkill, PatchedMycroftSkill))
        except ModuleNotFoundError:
            # Class added in ovos-workwhop 0.0.12
            pass


class DiagnosticUtilsTests(unittest.TestCase):
    config_dir = os.path.join(os.path.dirname(__file__), "test_config")
    report_metric = Mock()

    @classmethod
    def setUpClass(cls) -> None:
        os.makedirs(cls.config_dir, exist_ok=True)

        os.environ["NEON_CONFIG_PATH"] = cls.config_dir
        os.environ["XDG_CONFIG_HOME"] = cls.config_dir
        test_dir = os.path.join(os.path.dirname(__file__), "diagnostic_files")
        from neon_core.configuration import patch_config
        patch_config({"log_dir": test_dir})

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
        self.assertIsInstance(data["logs"], str)
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
        self.assertIsInstance(data["logs"], str)
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


class DeviceUtilsTests(unittest.TestCase):
    def test_export_user_config(self):
        from neon_core.util.device_utils import export_user_config
        output_path = join(dirname(__file__), "test_config_export")
        config_path = join(output_path, "config")
        output_file = export_user_config(output_path, config_path)
        self.assertTrue(isfile(output_file))
        self.assertEqual(dirname(output_file), output_path)

        # Validate exported contents
        extract_path = join(output_path, "exported")
        shutil.unpack_archive(output_file, extract_path)
        self.assertTrue(isdir(extract_path))
        self.assertTrue(isfile(join(extract_path, "skills",
                                    "skill-test.neon", "skill.json")),
                        repr(os.listdir(extract_path)))
        self.assertTrue(isfile(join(extract_path, "neon.yaml")))

        # Validate export file exists
        with self.assertRaises(FileExistsError):
            export_user_config(output_path, config_path)

        # Cleanup test files
        shutil.rmtree(extract_path)
        os.remove(output_file)

    def test_import_user_config(self):
        from neon_core.util.device_utils import import_user_config
        valid_import_directory = join(dirname(__file__), "test_config_import",
                                      "config")
        valid_import_file = join(dirname(__file__), "test_config_import",
                                 "neon_export.zip")
        # Write test config to be overwritten
        with open(join(valid_import_directory, "neon.yaml"), "w+") as f:
            f.write("success: False\n")

        # Validate imported contents
        imported = import_user_config(valid_import_file, valid_import_directory)
        self.assertEqual(imported, valid_import_directory)
        self.assertTrue(isfile(join(valid_import_directory, "neon.yaml")))
        self.assertTrue(isfile(join(valid_import_directory, "skills",
                                    "skill-test.neon", "test.file")))
        self.assertTrue(isfile(join(valid_import_directory, "skills",
                                    "skill-test.neon", "skill.json")))
        self.assertTrue(isfile(join(valid_import_directory, "neon.yaml")))
        with open(join(valid_import_directory, "neon.yaml")) as f:
            contents = f.read()
        self.assertEqual(contents, "test: true\n")

        # Validate import file exists
        with self.assertRaises(FileNotFoundError):
            import_user_config(valid_import_directory)

        # Cleanup
        os.remove(join(valid_import_directory, "neon.yaml"))
        os.remove(join(valid_import_directory, "skills", "skill-test.neon",
                       "skill.json"))


if __name__ == '__main__':
    unittest.main()
