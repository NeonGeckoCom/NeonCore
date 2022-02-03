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
import importlib
import json
import os
import shutil
import sys
import unittest
from copy import deepcopy

from importlib import reload
from mock.mock import Mock

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

TEST_SKILLS_NO_AUTH = [
    "https://github.com/NeonGeckoCom/alerts.neon/tree/dev",
    "https://github.com/NeonGeckoCom/caffeinewiz.neon/tree/dev",
    "https://github.com/NeonGeckoCom/launcher.neon/tree/dev"
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
        from ovos_skills_manager.session import set_github_token, clear_github_token
        set_github_token(SKILL_CONFIG["neon_token"])
        skills_list = get_remote_entries(SKILL_CONFIG["default_skills"])
        clear_github_token()
        self.assertIsInstance(skills_list, list)
        self.assertTrue(len(skills_list) > 0)
        self.assertTrue(all(skill.startswith("https://github.com") for skill in skills_list))

    def test_install_skills_from_list_no_auth(self):
        from neon_core.util.skill_utils import install_skills_from_list
        install_skills_from_list(TEST_SKILLS_NO_AUTH, SKILL_CONFIG)
        skill_dirs = [d for d in os.listdir(SKILL_DIR) if os.path.isdir(os.path.join(SKILL_DIR, d))]
        self.assertEqual(len(skill_dirs), len(TEST_SKILLS_NO_AUTH))
        self.assertIn("alerts.neon.neongeckocom", skill_dirs)

    def test_install_skills_from_list_with_auth(self):
        from neon_core.util.skill_utils import install_skills_from_list
        install_skills_from_list(TEST_SKILLS_WITH_AUTH, SKILL_CONFIG)
        skill_dirs = [d for d in os.listdir(SKILL_DIR) if os.path.isdir(os.path.join(SKILL_DIR, d))]
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
        import neon_core.util.skill_utils
        importlib.reload(neon_core.util.skill_utils)
        install_deps = Mock()
        neon_core.util.skill_utils._install_skill_dependencies = install_deps
        install_local_skills = neon_core.util.skill_utils.install_local_skills

        local_skills_dir = os.path.join(os.path.dirname(__file__),
                                        "local_skills")

        installed = install_local_skills(local_skills_dir)
        num_installed = len(installed)
        self.assertEqual(installed, os.listdir(local_skills_dir))
        self.assertEqual(num_installed, install_deps.call_count)


    def test_install_skill_dependencies(self):
        # Patch dependency installation
        import ovos_skills_manager.requirements
        importlib.reload(ovos_skills_manager.requirements)
        pip_install = Mock()
        install_system_deps = Mock()
        ovos_skills_manager.requirements.install_system_deps = \
            install_system_deps
        ovos_skills_manager.requirements.pip_install = pip_install
        from ovos_skills_manager.skill_entry import SkillEntry
        import neon_core.util.skill_utils
        importlib.reload(neon_core.util.skill_utils)
        from neon_core.util.skill_utils import _install_skill_dependencies
        local_skills_dir = os.path.join(os.path.dirname(__file__),
                                        "local_skills")
        with open(os.path.join(local_skills_dir,
                               "skill-osm_parsing", "skill.json")) as f:
            skill_json = json.load(f)
        entry = SkillEntry.from_json(skill_json, False)
        self.assertEqual(entry.json["requirements"],
                         skill_json["requirements"])

        _install_skill_dependencies(entry)
        pip_install.assert_called_once()
        pip_install.assert_called_with(entry.json["requirements"]["python"])
        install_system_deps.assert_called_once()
        install_system_deps.assert_called_with(
            entry.json["requirements"]["system"])


if __name__ == '__main__':
    unittest.main()
