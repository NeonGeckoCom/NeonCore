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
from os.path import dirname, join, exists, isdir
from unittest.mock import patch
from unittest import skip

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

    def test_get_skills_from_remote_list(self):
        from neon_core.util.skill_utils import _get_skills_from_remote_list

        skills_list = _get_skills_from_remote_list(SKILL_CONFIG["default_skills"])

        self.assertIsInstance(skills_list, list)
        self.assertTrue(len(skills_list) > 0)
        self.assertTrue(all(skill.startswith("https://github.com")
                            for skill in skills_list))

    @skip("Installation from Git is deprecated")
    def test_install_skills_from_list_no_auth(self):
        from neon_core.util.skill_utils import install_skills_from_list
        install_skills_from_list(TEST_SKILLS_NO_AUTH, SKILL_CONFIG)
        skill_dirs = [d for d in os.listdir(SKILL_DIR)
                      if os.path.isdir(os.path.join(SKILL_DIR, d))]
        self.assertEqual(len(skill_dirs), len(TEST_SKILLS_NO_AUTH))
        self.assertIn("alerts.neon.neongeckocom", skill_dirs)

    @skip("Installation from Git is deprecated")
    def test_install_skills_from_list_with_auth(self):
        from neon_core.util.skill_utils import install_skills_from_list
        install_skills_from_list(TEST_SKILLS_WITH_AUTH, SKILL_CONFIG)
        skill_dirs = [d for d in os.listdir(SKILL_DIR)
                      if os.path.isdir(os.path.join(SKILL_DIR, d))]
        self.assertEqual(len(skill_dirs), len(TEST_SKILLS_WITH_AUTH))
        self.assertIn("i-like-brands.neon.neongeckocom", skill_dirs)

    @patch("neon_core.util.skill_utils.install_skills_from_list")
    def test_install_skills_default(self, install_skills):
        from neon_core.util.skill_utils import install_skills_default,\
            _get_skills_from_remote_list
        install_skills_default(SKILL_CONFIG)
        expected = _get_skills_from_remote_list(SKILL_CONFIG["default_skills"])
        install_skills.assert_called_once_with(expected,
                                               install_skills.call_args[0][1])

    def test_install_skills_with_pip(self):
        from neon_core.util.skill_utils import install_skills_from_list
        install_skills_from_list(TEST_SKILLS_WITH_PIP, SKILL_CONFIG)
        skill_dirs = [d for d in os.listdir(SKILL_DIR)
                      if os.path.isdir(os.path.join(SKILL_DIR, d))]
        self.assertEqual(len(skill_dirs), 1)
        self.assertIn("skill-date_time.neongeckocom", skill_dirs)

        returned = os.system("pip show neon-skill-support-helper")
        self.assertEqual(returned, 0)

    @skip("OSM skill installation deprecated")
    def test_get_neon_skills_data(self):
        from neon_core.util.skill_utils import get_neon_skills_data
        from ovos_skills_manager.github.utils import normalize_github_url
        neon_skills = get_neon_skills_data()
        self.assertIsInstance(neon_skills, dict)
        for skill in neon_skills:
            self.assertIsInstance(neon_skills[skill], dict)
            self.assertEqual(skill,
                             normalize_github_url(neon_skills[skill]["url"]))

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

        os.remove(test_outfile)

    # def test_set_osm_constraints_file(self):
    #     import ovos_skills_manager.requirements
    #     from neon_core.util.skill_utils import set_osm_constraints_file
    #     set_osm_constraints_file(__file__)
    #     self.assertEqual(ovos_skills_manager.requirements.DEFAULT_CONSTRAINTS,
    #                      __file__)

    @skip("Skill class patching is deprecated")
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

        from neon_utils.skills.neon_skill import NeonSkill
        # self.assertTrue(issubclass(FallbackSkill, NeonSkill))
        self.assertTrue(issubclass(CommonPlaySkill, PatchedMycroftSkill))
        self.assertTrue(issubclass(CommonQuerySkill, PatchedMycroftSkill))
        self.assertTrue(issubclass(CommonIoTSkill, PatchedMycroftSkill))

        from ovos_workshop.skills.mycroft_skill import MycroftSkill as Patched
        from ovos_workshop.skills import MycroftSkill as Patched2
        # from ovos_workshop.skills.ovos import MycroftSkill as Patched3
        self.assertEqual(Patched, PatchedMycroftSkill)
        self.assertEqual(Patched2, PatchedMycroftSkill)
        # self.assertEqual(Patched3, PatchedMycroftSkill)

        from ovos_workshop.skills.ovos import OVOSSkill
        from ovos_workshop.skills import OVOSSkill as OVOSSkill2
        # self.assertTrue(issubclass(OVOSSkill, PatchedMycroftSkill))
        self.assertEqual(OVOSSkill, OVOSSkill2)

        from neon_utils.skills import NeonFallbackSkill, NeonSkill
        # self.assertTrue(issubclass(NeonFallbackSkill, PatchedMycroftSkill))
        # self.assertTrue(issubclass(NeonSkill, PatchedMycroftSkill))
        self.assertTrue(issubclass(NeonFallbackSkill, OVOSSkill))
        # self.assertTrue(issubclass(NeonFallbackSkill, NeonSkill))

        from neon_utils.skills.neon_fallback_skill import NeonFallbackSkill as \
            NeonFallbackSkill2
        from neon_utils.skills.neon_skill import NeonSkill as NeonSkill2
        self.assertEqual(NeonFallbackSkill, NeonFallbackSkill2)
        self.assertEqual(NeonSkill, NeonSkill2)

        # from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill
        # self.assertTrue(issubclass(OVOSCommonPlaybackSkill,
        #                            PatchedMycroftSkill))
        #
        # try:
        #     from ovos_workshop.skills.common_query_skill import CommonQuerySkill
        #     self.assertTrue(issubclass(CommonQuerySkill, PatchedMycroftSkill))
        # except ModuleNotFoundError:
        #     # Class added in ovos-workwhop 0.0.12
        #     pass

    @patch("neon_core.util.skill_utils.Configuration")
    def test_update_default_resources(self, config):
        from neon_core.util.skill_utils import update_default_resources
        mock_config = {"data_dir": join(dirname(__file__), "test_resources",
                                        "res")}
        config.return_value = mock_config

        # Valid create resource path
        update_default_resources()
        self.assertTrue(exists(mock_config['data_dir']))
        self.assertTrue(isdir(join(mock_config['data_dir'], "text", "uk-ua")))

        # Valid path already exists
        update_default_resources()
        self.assertTrue(exists(mock_config['data_dir']))
        self.assertTrue(isdir(join(mock_config['data_dir'], "text", "uk-ua")))

        os.remove(mock_config['data_dir'])

        # Invalid path already exists
        mock_config['data_dir'] = dirname(__file__)
        update_default_resources()
        self.assertFalse(isdir(join(mock_config['data_dir'], "text", "uk-ua")))


if __name__ == '__main__':
    unittest.main()
