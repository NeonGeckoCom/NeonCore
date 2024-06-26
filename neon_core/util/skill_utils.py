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

import re

from copy import copy
from os import makedirs, symlink
from os.path import expanduser, join, isdir, dirname, islink
from typing import List

from ovos_utils.xdg_utils import xdg_data_home
from ovos_utils.log import LOG

from ovos_config.config import Configuration


def _write_pip_constraints_to_file(output_file: str):
    """
    Writes out a constraints file for OSM to use to prevent broken dependencies
    :param output_file: path to constraints file to write
    """
    if not output_file:
        raise ValueError(f"Expected string path but got: {output_file}")

    from neon_utils.packaging_utils import get_package_dependencies
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
    Installs the passed list of skills (valid pip arguments).
    :param skills_to_install: list of skills to install
    :param config: optional dict configuration
    """
    constraints_file = join(xdg_data_home(), "neon", "constraints.txt")
    _write_pip_constraints_to_file(constraints_file)

    for spec in skills_to_install:
        if "://" in spec and "git+" not in spec:
            LOG.error(f"Got an invalid package spec to install: {spec}")
        elif not _install_skill_pip(spec, constraints_file):
            LOG.error(f"Pip installation failed for: {spec}")

    LOG.info(f"Installed {len(skills_to_install)} skills")


def install_skills_default(config: dict = None):
    """
    Installs default skills from passed or default configuration
    """
    config = config or Configuration()["skills"]
    skills_list = config.get("default_skills")
    if isinstance(skills_list, str):
        skills_list = _get_skills_from_remote_list(skills_list)
    assert isinstance(skills_list, list)
    if skills_list:
        LOG.info(f"Installing configured skills: {skills_list}")
        install_skills_from_list(skills_list, config)


def _get_skills_from_remote_list(url: str) -> List[str]:
    import requests
    resp = requests.get(url)
    if not resp.ok:
        LOG.error(f"Unable to fetch skills list from: {url} ({resp.status_code})")
        return []
    return [s for s in resp.text.split("\n") if s.strip() and not s.startswith('#')]


def update_default_resources():
    """
    Ensure the `res` directory contents are available at the configured data_dir
    """
    res_dir = Configuration().get('data_dir')
    if not res_dir:
        LOG.info("`data_dir` is None; not linking default resources.")
        return
    res_dir = expanduser(res_dir)
    if isdir(res_dir):
        LOG.info(f"Directory exists; not linking default resources. {res_dir}")
        return
    if islink(res_dir):
        LOG.debug(f"Link exists; not doing anything.")
        return
    if not isdir(dirname(res_dir)):
        # Ensure directory exists to link default resources in
        makedirs(dirname(res_dir))

    symlink(join(dirname(dirname(__file__)), "res"), res_dir)
    LOG.debug("Updated Neon default resources")
