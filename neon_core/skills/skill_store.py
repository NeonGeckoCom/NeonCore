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
from ovos_skills_manager.session import SESSION as requests
from ovos_skills_manager.osm import OVOSSkillsManager
from ovos_skills_manager.skill_entry import SkillEntry
from neon_core.configuration import Configuration
from neon_core.messagebus import get_messagebus
from mycroft.skills.event_scheduler import EventSchedulerInterface
from mycroft.util import connected
from mycroft.util.log import LOG
from os.path import expanduser
from datetime import datetime, timedelta


class SkillsStore:
    def __init__(self, skills_dir, config=None, bus=None):
        self.config = config or Configuration.get()["skills"]
        self.disabled = self.config.get("disable_osm", False)
        self.skills_dir = skills_dir
        self.osm = self.load_osm()
        self._default_skills = []
        self._alternative_skills = []
        self._essential_skills = []
        self.bus = bus or get_messagebus()
        self.scheduler = EventSchedulerInterface("OSM", sched_id="osm",
                                                 bus=self.bus)
        if not self.disabled or not self.config["auto_update"]:
            if self.config.get("auto_update_interval"):
                self.schedule_update()
            if self.config.get("appstore_sync_interval"):
                self.schedule_sync()

    def schedule_sync(self):
        # every X hours
        interval = 60 * 60 * self.config["appstore_sync_interval"]
        when = datetime.now() + timedelta(seconds=interval)
        self.scheduler.schedule_repeating_event(self.handle_sync_appstores,
                                                when, interval=interval,
                                                name="appstores.sync")

    def schedule_update(self):
        # every X hours
        interval = 60 * 60 * self.config["auto_update_interval"]
        when = datetime.now() + timedelta(seconds=interval)
        self.scheduler.schedule_repeating_event(self.handle_update,
                                                when, interval=interval,
                                                name="default_skills.update")

    def handle_update(self, message):
        try:
            self.install_default_skills(update=True)
        except Exception as e:
            if connected():
                # if there is internet log the error
                LOG.exception(e)
                LOG.error("skills update failed")
            else:
                # if no internet just skip this update
                LOG.error("no internet, skipped skills update")

    def handle_sync_appstores(self, message):
        try:
            self.osm.sync_appstores()
        except Exception as e:
            if connected():
                # if there is internet log the error
                LOG.exception(e)
                LOG.error("appstore sync failed")
            else:
                # if no internet just skip this update
                LOG.error("no internet, skipped appstore sync")

    def shutdown(self):
        self.scheduler.shutdown()

    def load_osm(self):
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
        self.osm.enable_appstore("neon")
        neon = self.osm.get_appstore("neon")
        neon_token = self.config.get("neon_token")
        if neon_token:
            neon.authenticate(neon_token, False)
        else:
            neon.authenticate(bootstrap=False)

    def deauthenticate_neon(self):
        neon = self.osm.get_appstore("neon")
        neon.clear_authentication()

    def get_skill_entry(self, skill):
        if "http" in skill:
            store_skill = self.osm.search_skills_by_url(skill)
            if not store_skill:
                # skill is not in any appstore
                if "/neon" in skill.lower() and "github" in skill:
                    self.authenticate_neon()
                    entry = SkillEntry.from_github_url(skill)
                    self.deauthenticate_neon()
                else:
                    entry = SkillEntry.from_github_url(skill)
                return entry
            else:
                return store_skill
        elif "." in skill:
            return self.osm.search_skills_by_id(skill)
        return None

    def get_remote_entries(self, url):
        """ parse url and return a list of SkillEntry,
         expects 1 skill per line, can be a skill_id or url"""
        # TODO improve detection of neon github repos
        if "/neon" in url.lower() and "github" in url:
            self.authenticate_neon()
            r = requests.get(url)
            self.deauthenticate_neon()
        else:
            r = requests.get(url)
        if r.status_code == 200:
            return [s for s in r.text.split("\n") if s.strip()]
        return []

    def _parse_config_entry(self, entry):
        """
        entry can be
         - an url (str) to download essential skill list
             - can be a list of skill repo urls, or skill_ids
         - list (list) of names (str)
         - list (list) of skill_urls (str)
        """
        if self.disabled:
            return []
        if isinstance(entry, str):
            if not entry.startswith("http"):
                raise ValueError  # TODO new exception
            skills = self.get_remote_entries(entry)
        elif isinstance(entry, list):
            skills = entry
        else:
            raise ValueError("invalid configuration entry")
        for idx, skill in enumerate(skills):
            skills[idx] = self.get_skill_entry(skill)
        skills = [s for s in skills if s]
        return skills

    def install_skill(self, skill_entry, folder=None, *args, **kwargs):
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
            updated = self.install_skill(skill, update=update)
            skills.append((skill, updated))
        return skills
