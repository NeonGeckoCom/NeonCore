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

import os
import shutil
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from neon_core.util.skill_utils import *

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
    "default_skills": "https://raw.githubusercontent.com/NeonGeckoCom/neon-skills-submodules/dev/.utilities/"
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
        from ovos_skills_manager.session import set_github_token, clear_github_token
        set_github_token(SKILL_CONFIG["neon_token"])
        skills_list = get_remote_entries(SKILL_CONFIG["default_skills"])
        clear_github_token()
        self.assertIsInstance(skills_list, list)
        self.assertTrue(len(skills_list) > 0)
        self.assertTrue(all(skill.startswith("https://github.com") for skill in skills_list))

    def test_install_skills_from_list_no_auth(self):
        install_skills_from_list(TEST_SKILLS_NO_AUTH, SKILL_CONFIG)
        skill_dirs = [d for d in os.listdir(SKILL_DIR) if os.path.isdir(os.path.join(SKILL_DIR, d))]
        self.assertEqual(len(skill_dirs), len(TEST_SKILLS_NO_AUTH))
        self.assertIn("alerts.neon.neon", skill_dirs)

    def test_install_skills_from_list_with_auth(self):
        install_skills_from_list(TEST_SKILLS_WITH_AUTH, SKILL_CONFIG)
        skill_dirs = [d for d in os.listdir(SKILL_DIR) if os.path.isdir(os.path.join(SKILL_DIR, d))]
        self.assertEqual(len(skill_dirs), len(TEST_SKILLS_WITH_AUTH))
        self.assertIn("i-like-brands.neon.neon", skill_dirs)

    def test_install_skills_default(self):
        install_skills_default(SKILL_CONFIG)
        skill_dirs = [d for d in os.listdir(SKILL_DIR) if os.path.isdir(os.path.join(SKILL_DIR, d))]
        self.assertEqual(len(skill_dirs), len(get_remote_entries(SKILL_CONFIG["default_skills"])))


if __name__ == '__main__':
    unittest.main()
