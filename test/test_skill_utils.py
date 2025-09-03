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
from os.path import dirname, join, exists, isdir
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

TEST_SKILLS_NO_AUTH = [
    "https://github.com/NeonGeckoCom/alerts.neon/tree/dev",
    "https://github.com/NeonGeckoCom/caffeinewiz.neon/tree/dev",
    "https://github.com/NeonGeckoCom/launcher.neon/tree/dev"
]

TEST_SKILLS_WITH_PIP = [
#    "https://github.com/NeonGeckoCom/skill-date_time/tree/dev",
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
        self.assertEqual(len(skill_dirs), 0)
        # self.assertIn("skill-date_time.neongeckocom", skill_dirs)

        returned = os.system("pip show neon-skill-support-helper")
        self.assertEqual(returned, 0)

    def test_write_pip_constraints_to_file(self):
        from neon_core.util.skill_utils import _write_pip_constraints_to_file
        from neon_utils.packaging_utils import get_package_dependencies

        with self.assertRaises(ValueError):
            _write_pip_constraints_to_file("")

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
