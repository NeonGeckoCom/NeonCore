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

from os import makedirs
from os.path import isdir
from typing import List, Optional, Generator, Union
from ovos_skills_manager.osm import OVOSSkillsManager
from ovos_skills_manager.skill_entry import SkillEntry
from ovos_utils.log import LOG
from neon_utils.net_utils import check_online
from neon_utils.authentication_utils import repo_is_neon
from datetime import datetime, timedelta
from neon_utils.messagebus_utils import get_messagebus

from neon_core.util.skill_utils import get_remote_entries
from mycroft.skills.event_scheduler import EventSchedulerInterface
from ovos_config.config import Configuration


class SkillsStore:
    def __init__(self, skills_dir, config=None, bus=None):
        self.config = config or Configuration()["skills"]
        self.disabled = self.config.get("disable_osm", False)
        self.skills_dir = skills_dir
        self.osm = self.load_osm()
        self._default_skills = []
        self._alternative_skills = []
        self._essential_skills = []
        self.bus = bus or get_messagebus()
        self.scheduler = EventSchedulerInterface(skill_id="osm",
                                                 bus=self.bus)
        if not self.disabled or not self.config["auto_update"]:
            if self.config.get("auto_update_interval"):
                self.schedule_update()
            if self.config.get("appstore_sync_interval"):
                self.schedule_sync()

    def schedule_sync(self):
        """
        Use the EventScheduler to update osm with updated appstore data
        """
        # every X hours
        interval = 60 * 60 * self.config["appstore_sync_interval"]
        when = datetime.now() + timedelta(seconds=interval)
        self.scheduler.schedule_repeating_event(self.handle_sync_appstores,
                                                when, interval=interval,
                                                name="appstores.sync")

    def schedule_update(self):
        """
        Use the EventScheduler to update default skills
        """
        # every X hours
        interval = 60 * 60 * self.config["auto_update_interval"]
        when = datetime.now() + timedelta(seconds=interval)
        self.scheduler.schedule_repeating_event(self.handle_update,
                                                when, interval=interval,
                                                name="default_skills.update")

    def handle_update(self, _):
        """
        Scheduled action to update installed skills
        """
        try:
            # TODO: Include non-default installed skills?
            self.install_default_skills(update=True)
        except Exception as e:
            if check_online():
                # if there is internet log the error
                LOG.exception(e)
                LOG.error("skills update failed")
            else:
                # if no internet just skip this update
                LOG.error("no internet, skipped skills update")

    def handle_sync_appstores(self, _):
        """
        Scheduled action to update OSM appstore listings
        """
        try:
            self.osm.sync_appstores()
        except Exception as e:
            # TODO: OSM should raise more specific exceptions
            if check_online():
                # if there is internet log the error
                LOG.exception(e)
                LOG.error("appstore sync failed")
            else:
                # if no internet just skip this update
                LOG.error("no internet, skipped appstore sync")

    def shutdown(self):
        self.scheduler.shutdown()

    def load_osm(self):
        """
        Get an authenticated instance of OSM if not disabled
        """
        from ovos_utils.skills import get_skills_folder
        osm_skill_dir = get_skills_folder()
        if osm_skill_dir and osm_skill_dir != self.skills_dir:
            LOG.warning(f"OSM configured local skills: {osm_skill_dir}")
            if not isdir(osm_skill_dir):
                makedirs(osm_skill_dir)
        if self.disabled:
            return None
        osm = OVOSSkillsManager()
        neon_token = self.config.get("neon_token")
        if neon_token:
            osm.set_appstore_auth_token("neon", neon_token)
        return osm

    @property
    def essential_skills(self):
        """
        List of absolute minimum skills needed for mycroft to work properly
        .conf accepts:
          - an url (str) to download essential skill list
          - list (list) of names (str)
          - list (list) of skill_urls (str)

        NOTES:
            - depending on enabled appstores / authentication this might fail
            - Neon Skills need authentication
            - see alternative_essential_skills
            - Installing essential skills can be disabled in .conf
            - these should be hardcoded in mycroft.conf and version pinned
        """
        if not self._essential_skills and \
                self.config.get("install_essential", True):
            self._essential_skills = self._parse_config_entry(
                self.config.get("essential_skills", []))
        return self._essential_skills

    @property
    def default_skills(self):
        """
        Default skills for every install
         .conf accepts:
          - an url (str) to download essential skill list
          - list (list) of names (str)
          - list (list) of skill_urls (str)

        NOTES:
            - depending on enabled appstores / authentication this might fail
            - Neon Skills need authentication
            - Installing defaults can be disabled in .conf
        """

        if not self._default_skills and \
                self.config.get("install_default", True):
            self._default_skills = self._parse_config_entry(
                self.config.get("default_skills", []))
        return self._default_skills

    def authenticate_neon(self):
        """
        Enable and authenticate the Neon skills store
        """
        self.osm.enable_appstore("neon")
        neon = self.osm.get_appstore("neon")
        neon_token = self.config.get("neon_token")
        if neon_token:
            neon.authenticate(neon_token, False)
        else:
            neon.authenticate(bootstrap=False)

    def deauthenticate_neon(self):
        """
        Clear authentication for the Neon skills store
        """
        neon = self.osm.get_appstore("neon")
        neon.clear_authentication()

    def get_skill_entry(self, skill: str) -> Optional[SkillEntry]:
        """
        Build a SkillEntry object from the passed skill URL or ID
        :param skill: str skill to search
        :returns best match of input skill or None
        """
        if "http" in skill:
            if "/neongeckocom/" in skill.lower():
                # TODO: This is just patching OSM updates DM
                store_skill = None
            else:
                try:
                    store_skill = self.osm.search_skills_by_url(skill)
                    if isinstance(store_skill, SkillEntry):
                        return store_skill
                    elif isinstance(store_skill, list):
                        return store_skill[0]
                    elif isinstance(store_skill, Generator):
                        # Return the first item
                        for s in store_skill:
                            return s
                except Exception as e:
                    LOG.error(f"OSM Error: {e}")
            # skill is not in any appstore
            if "/neon" in skill.lower() and "github" in skill:
                self.authenticate_neon()
                entry = SkillEntry.from_github_url(skill)
                self.deauthenticate_neon()
            else:
                entry = SkillEntry.from_github_url(skill)
            return entry
        elif "." in skill:
            # Return the first item
            for skill in self.osm.search_skills_by_id(skill):
                return skill
        return None

    def get_remote_entries(self, url: str) -> List[str]:
        """
        Wraps a call to `neon_core.util.skill_utils.get_remote_entries` to
        include authentication.
        :param url: URL of skill list to parse (one skill per line)
        :returns: list of skills by name, url, and/or ID
        """
        authenticated = False
        if repo_is_neon(url):
            self.authenticate_neon()
            authenticated = True
        skills_list = get_remote_entries(url)
        if authenticated:
            self.deauthenticate_neon()
        return skills_list

    def _parse_config_entry(self, entry: Union[list, str]) -> List[SkillEntry]:
        """
        Parse a config value into a list of SkillEntry objects
        :param entry: Configuration value, one of:
             - str url of a skill list of skill repo urls, or skill_ids
             - list of skill IDs (str)
             - list of skill_urls (str)
        :returns: list of parsed SkillEntry objects
        """
        if self.disabled:
            LOG.warning("Ignoring parse request as SkillStore is disabled")
            return []
        if isinstance(entry, str):
            if not entry.startswith("http"):
                raise ValueError(f"passed entry not a valid URL or list: "
                                 f"{entry}")
            skills = self.get_remote_entries(entry)
        elif isinstance(entry, list):
            skills = entry
        else:
            raise ValueError(f"invalid configuration entry: {entry}")

        skill_entries = list()
        for skill in skills:
            entry = self.get_skill_entry(skill)
            if entry:
                skill_entries.append(entry)

        return skill_entries

    def install_skill(self, skill_entry: SkillEntry,
                      folder: Optional[str] = None, *args, **kwargs) -> bool:
        """
        Install a SkillEntry to a local directory.
        args/kwargs are passed to `skill_entry.install`
        :param skill_entry: SkillEntry to install
        :param folder: Skill installation directory (default self.skills_dir)
        :returns: True if skill is installed or updated
        """
        if self.disabled:
            return False
        self.authenticate_neon()
        kwargs["folder"] = folder or self.skills_dir
        updated = skill_entry.install(*args, **kwargs)
        self.deauthenticate_neon()
        return updated

    def install_default_skills(self, update=False):
        skills = []
        if self.disabled:
            return skills
        for skill in self.essential_skills:
            updated = self.install_skill(skill, update=update)
            skills.append((skill, updated))
        for skill in self.default_skills:
            try:
                updated = self.install_skill(skill, update=update)
            except Exception as e:
                LOG.error(e)
                continue  # Assume install has failed and skill is not installed
            skills.append((skill, updated))
        return skills
