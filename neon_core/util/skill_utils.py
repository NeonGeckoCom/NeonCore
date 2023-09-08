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
import re

from copy import copy
from os import listdir, makedirs
from tempfile import mkdtemp
from shutil import rmtree
from os.path import expanduser, join, isdir, dirname
from ovos_utils.xdg_utils import xdg_data_home
from ovos_skills_manager.skill_entry import SkillEntry
from ovos_skills_manager.osm import OVOSSkillsManager
from ovos_skills_manager.session import set_github_token, clear_github_token
from ovos_skills_manager.github import normalize_github_url, get_branch_from_github_url, download_url_from_github_url
from ovos_skills_manager.utils import get_skills_from_url as get_remote_entries
from ovos_skills_manager.utils import install_local_skill_dependencies as install_local_skills
from ovos_skills_manager.utils import set_osm_constraints_file
from ovos_skill_installer import download_extract_zip
from ovos_utils.log import LOG

from ovos_config.config import Configuration


def get_neon_skills_data(skill_meta_repository: str =
                         "https://github.com/neongeckocom/neon_skills",
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
    try:
        download_extract_zip(zip_url, temp_download_dir,
                             "neon_skill_meta.zip", base_dir)
    except PermissionError:
        LOG.exception(f"Failed to download {zip_url} to {base_dir}")
        return dict()
    meta_dir = join(base_dir, repo_metadata_path)
    for entry in listdir(meta_dir):
        with open(join(meta_dir, entry)) as f:
            skill_entry = json.load(f)
        skills_data[normalize_github_url(skill_entry["url"])] = skill_entry
    rmtree(temp_download_dir)
    return skills_data


def _write_pip_constraints_to_file(output_file: str = None):
    """
    Writes out a constraints file for OSM to use to prevent broken dependencies
    :param output_file: path to constraints file to write
    """
    from neon_utils.packaging_utils import get_package_dependencies

    output_file = output_file or '/etc/mycroft/constraints.txt'
    if not isdir(dirname(output_file)):
        makedirs(dirname(output_file))

    with open(output_file, 'w+') as f:
        constraints = get_package_dependencies("neon-core")
        for c in copy(constraints):
            try:
                constraint = re.split('[^a-zA-Z0-9_-]', c, 1)[0] or c
                constraints.extend(get_package_dependencies(constraint))
            except ModuleNotFoundError:
                LOG.warning(f"Ignoring uninstalled dependency: {constraint}")
        constraints = [f'{c.split("[")[0]}{c.split("]")[1]}' if '[' in c
                       else c for c in constraints if '@' not in c]
        constraints.append('neon-utils>=1.0.0a1')  # TODO: Patching dep. bug
        LOG.debug(f"Got package constraints: {constraints}")
        f.write('\n'.join(constraints))
    LOG.info(f"Wrote core constraints to file: {output_file}")


def _install_skill_osm(skill_url: str, skill_dir: str, skills_catalog: dict):
    """
    Install a skill from source using OVOS Skills Manager
    :param skill_url: URL of skill to install
    :param skill_dir: Directory to install skill to
    :param skills_catalog: dict Neon skill information (url to dict data)
    """
    osm = OVOSSkillsManager()
    try:
        normalized_url = normalize_github_url(skill_url)
        # Check if this skill is in the Neon list
        if normalized_url in skills_catalog:
            branch = get_branch_from_github_url(skill_url)
            # Set URL and branch to requested spec
            skills_catalog[normalized_url]["url"] = normalized_url
            skills_catalog[normalized_url]["branch"] = branch
            entry = SkillEntry.from_json(skills_catalog.get(normalized_url), False)
        else:
            LOG.warning(f"Requested Skill not in Neon skill store ({skill_url})")
            entry = osm.skill_entry_from_url(skill_url)
            LOG.debug(entry.json)

        osm.install_skill(entry, skill_dir)
        if not os.path.isdir(os.path.join(skill_dir, entry.uuid)):
            LOG.error(f"Failed to install: "
                      f"{os.path.join(skill_dir, entry.uuid)}")
            if entry.download(skill_dir):
                LOG.info(f"Downloaded failed skill: {entry.uuid}")
            else:
                LOG.error(f"Failed to download: {entry.uuid}")
        else:
            LOG.info(f"Installed {skill_url} to {skill_dir}")
    except Exception as e:
        LOG.exception(e)


def _install_skill_pip(skill_package: str, constraints_file: str) -> bool:
    """
    Pip install the specified package
    :param skill_package: package to install (git url or pypi name)
    :param constraints_file: system Python package constraints
    :returns: True if installation was successful, else False
    """
    import pip
    LOG.info(f"Requested installation of plugin skill: {skill_package}")
    returned = pip.main(['install', skill_package, "-c",
                         constraints_file])
    LOG.info(f"pip status: {returned}")
    return returned == 0


def install_skills_from_list(skills_to_install: list, config: dict = None):
    """
    Installs the passed list of skill URLs and/or PyPI package names
    :param skills_to_install: list of skills to install
    :param config: optional dict configuration
    """
    config = config or Configuration()["skills"]
    LOG.info(f"extra_directories={config.get('extra_directories')}")
    LOG.info(f"directory={config.get('directory')}")
    skill_dir = expanduser(config.get("extra_directories")[0] if
                           config.get("extra_directories") else
                           config.get("directory") if config.get("directory")
                           and config["directory"] != "skills" else
                           join(xdg_data_home(), "neon", "skills"))
    LOG.info(f"skill_dir={skill_dir}")
    skills_catalog = get_neon_skills_data()
    token_set = False
    if config.get("neon_token"):
        token_set = True
        set_github_token(config["neon_token"])
        LOG.info(f"Added token to request headers: {config.get('neon_token')}")
    try:
        _write_pip_constraints_to_file()
        constraints_file = '/etc/mycroft/constraints.txt'
    except PermissionError:
        constraints_file = join(xdg_data_home(), "neon", "constraints.txt")
        _write_pip_constraints_to_file(constraints_file)
        set_osm_constraints_file(constraints_file)
    for url in skills_to_install:
        if "://" in url and "git+" not in url:
            _install_skill_osm(url, skill_dir, skills_catalog)
        else:
            if not _install_skill_pip(url, constraints_file):
                LOG.warning(f"Pip installation failed for: {url}")
                _install_skill_osm(url, skill_dir, skills_catalog)

    if token_set:
        clear_github_token()
    LOG.info(f"Installed skills to: {skill_dir}")


def install_skills_default(config: dict = None):
    """
    Installs default skills from passed or default configuration
    """
    config = config or Configuration()["skills"]
    skills_list = config.get("default_skills")
    if isinstance(skills_list, str):
        skills_list = get_remote_entries(skills_list)
    assert isinstance(skills_list, list)
    install_skills_from_list(skills_list, config)
    clear_github_token()
