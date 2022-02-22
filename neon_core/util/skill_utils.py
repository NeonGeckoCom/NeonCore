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

import json
import os.path

import requests

from os import listdir
from tempfile import mkdtemp
from shutil import rmtree
from os.path import expanduser, join
from ovos_skills_manager.skill_entry import SkillEntry
from ovos_skills_manager.osm import OVOSSkillsManager
from ovos_skills_manager.session import SESSION, set_github_token, clear_github_token
from ovos_skills_manager.github import normalize_github_url, get_branch_from_github_url, download_url_from_github_url
from ovos_skill_installer import download_extract_zip
from neon_utils.configuration_utils import get_neon_skills_config
from neon_utils import LOG


def get_neon_skills_data(skill_meta_repository: str = "https://github.com/neongeckocom/neon_skills",
                         branch: str = "master",
                         repo_metadata_path: str = "skill_metadata") -> dict:
    """
    Get skill data from configured neon_skills repository.
    :param skill_meta_repository: URL of skills repository containing metadata
    :param branch: branch of repository to checkout
    :param repo_metadata_path: Path to repo directory containing json metadata files
    """
    skills_data = dict()
    temp_download_dir = mkdtemp()
    zip_url = download_url_from_github_url(skill_meta_repository, branch)
    base_dir = join(temp_download_dir, "neon_skill_meta")
    download_extract_zip(zip_url, temp_download_dir, "neon_skill_meta.zip", base_dir)

    meta_dir = join(base_dir, repo_metadata_path)
    for entry in listdir(meta_dir):
        with open(join(meta_dir, entry)) as f:
            skill_entry = json.load(f)
        skills_data[normalize_github_url(skill_entry["url"])] = skill_entry
    rmtree(temp_download_dir)
    return skills_data


def install_skills_from_list(skills_to_install: list, config: dict = None):
    """
    Installs the passed list of skill URLs
    :param skills_to_install: list of skill URLs to install
    :param config: optional dict configuration
    """
    config = config or get_neon_skills_config()
    skill_dir = expanduser(config["directory"])
    osm = OVOSSkillsManager()
    skills_catalog = get_neon_skills_data()
    token_set = False
    if config.get("neon_token"):
        token_set = True
        set_github_token(config["neon_token"])
    for url in skills_to_install:
        try:
            normalized_url = normalize_github_url(url)
            # Check if this skill is in the Neon list
            if normalized_url in skills_catalog:
                branch = get_branch_from_github_url(url)
                # Set URL and branch to requested spec
                skills_catalog[normalized_url]["url"] = normalized_url
                skills_catalog[normalized_url]["branch"] = branch
                entry = SkillEntry.from_json(skills_catalog.get(normalized_url), False)
            else:
                LOG.warning(f"Requested Skill not in Neon skill store ({url})")
                entry = osm.skill_entry_from_url(url)

            osm.install_skill(entry, skill_dir)
            if not os.path.isdir(os.path.join(skill_dir, entry.uuid)):
                LOG.error(f"Failed to install: "
                          f"{os.path.join(skill_dir, entry.uuid)}")
            else:
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
    r = SESSION.get(url)
    if not r.ok:
        LOG.warning(f"Cached response returned: {r.status_code}")
        SESSION.cache.delete_url(r.url)
        r = requests.get(url)
    if r.ok:
        return [s for s in r.text.split("\n") if s.strip()]
    else:
        LOG.error(f"{url} request failed with code: {r.status_code}")
    return []
