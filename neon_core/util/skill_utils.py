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
from os.path import expanduser
from ovos_skills_manager.osm import OVOSSkillsManager
from ovos_skills_manager.session import SESSION as requests, set_github_token, clear_github_token
from neon_utils.configuration_utils import get_neon_skills_config
from neon_utils.log_utils import LOG


def install_skills_from_list(skills_to_install: list, config: dict = None):
    """
    Installs the passed list of skill URLs
    :param skills_to_install: list or skill URLs to install
    :param config: optional dict configuration
    """
    config = config or get_neon_skills_config()
    skill_dir = expanduser(config["directory"])
    osm = OVOSSkillsManager()
    token_set = False
    if config.get("neon_token"):
        token_set = True
        set_github_token(config["neon_token"])
    for url in skills_to_install:
        try:
            osm.install_skill_from_url(url, skill_dir)
            LOG.info(f"Installed {url} to {skill_dir}")
        except Exception as e:
            LOG.error(e)
    if token_set:
        clear_github_token()


def install_skills_default(config: dict = None):
    """
    Installs default skills from passed or default configuration
    """
    config = config or get_neon_skills_config()
    skills_list = config["default_skills"]
    set_github_token(config.get("neon_token"))
    if isinstance(skills_list, str):
        skills_list = get_remote_entries(skills_list)
    assert isinstance(skills_list, list)
    install_skills_from_list(skills_list, config)
    clear_github_token()


def get_remote_entries(url):
    """ parse url and return a list of SkillEntry,
     expects 1 skill per line, can be a skill_id or url"""
    r = requests.get(url)
    if r.status_code == 200:
        return [s for s in r.text.split("\n") if s.strip()]
    else:
        LOG.error(f"{url} request failed with code: {r.status_code}")
    return []
