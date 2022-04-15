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

import json
import os.path

import requests

from os import listdir
from tempfile import mkdtemp
from shutil import rmtree
from os.path import expanduser, join, isdir

from ovos_skills_manager.requirements import install_system_deps, pip_install
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
        LOG.info(f"Added token to request headers: {config.get('neon_token')}")
    LOG.info(f"Neon Core headers={SESSION.headers}")
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
                LOG.info(entry.json)

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
    if isinstance(skills_list, str):
        skills_list = get_remote_entries(skills_list)
    assert isinstance(skills_list, list)
    install_skills_from_list(skills_list, config)
    clear_github_token()


def get_remote_entries(url: str):
    """
    Parse a skill list at a given URL
    :param url: URL of skill list to parse (one skill per line)
    :returns: list of skills by name, url, and/or ID
    """
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


def _install_skill_dependencies(skill: SkillEntry):
    """
    Install any system and Python dependencies for the specified skill
    :param skill: Skill to install dependencies for
    """
    sys_deps = skill.requirements.get("system")
    requirements = skill.requirements.get("python")
    if sys_deps:
        install_system_deps(sys_deps)
    if requirements:
        pip_install(requirements)
    LOG.info(f"Installed dependencies for {skill.skill_folder}")


def install_local_skills(local_skills_dir: str = "/skills") -> list:
    """
    Install skill dependencies for skills in the specified directory and ensure
    the directory is loaded.
    NOTE: dependence on other skills is not handled here.
          Only Python and System dependencies are handled
    :param local_skills_dir: Directory to install skills from
    :returns: list of installed skill directories
    """
    github_token = get_neon_skills_config()["neon_token"]
    local_skills_dir = expanduser(local_skills_dir)
    if not isdir(local_skills_dir):
        raise ValueError(f"{local_skills_dir} is not a valid directory")
    installed_skills = list()
    for skill in listdir(local_skills_dir):
        if not isdir(skill):
            pass
        LOG.debug(f"Attempting installation of {skill}")
        try:
            entry = SkillEntry.from_directory(join(local_skills_dir, skill),
                                              github_token)
            _install_skill_dependencies(entry)
            installed_skills.append(skill)
        except Exception as e:
            LOG.error(f"Exception while installing {skill}")
            LOG.error(e)
    if local_skills_dir not in \
            get_neon_skills_config().get("extra_directories", []):
        LOG.error(f"{local_skills_dir} not found in configuration")
    return installed_skills
