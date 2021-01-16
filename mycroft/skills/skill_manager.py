# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Load, update and manage skills on this device."""
import os
from glob import glob
from threading import Thread, Event
from time import sleep
from os.path import expanduser, join, isdir

from mycroft.enclosure.api import EnclosureAPI
from mycroft.configuration import Configuration
from mycroft.messagebus.message import Message
from mycroft.util.log import LOG
from mycroft.skills.skill_loader import SkillLoader

import git

SKILL_MAIN_MODULE = '__init__.py'


class SkillManager(Thread):

    def __init__(self, bus):
        """Constructor

        Arguments:
            bus (event emitter): Mycroft messagebus connection
        """
        super(SkillManager, self).__init__()
        self.bus = bus
        self._stop_event = Event()
        self._connected_event = Event()
        self.config = Configuration.get()
        self.skills_dir = expanduser(self.config["skills"]["directory"])

        self.skill_loaders = {}
        self.enclosure = EnclosureAPI(bus)
        self.initial_load_complete = False
        self._define_message_bus_events()
        self.daemon = True

        # Statuses
        self._alive_status = False  # True after priority skills has loaded
        self._loaded_status = False  # True after all skills has loaded

    def _define_message_bus_events(self):
        """Define message bus events with handlers defined in this class."""
        # Conversation management
        self.bus.on('skill.converse.request', self.handle_converse_request)

        # Update on initial connection
        self.bus.on(
            'mycroft.internet.connected',
            lambda x: self._connected_event.set()
        )

        # Update upon request
        self.bus.on('skillmanager.list', self.send_skill_list)
        self.bus.on('skillmanager.deactivate', self.deactivate_skill)
        self.bus.on('skillmanager.keep', self.deactivate_except)
        self.bus.on('skillmanager.activate', self.activate_skill)
        self.bus.on('mycroft.skills.is_alive', self.is_alive)
        self.bus.on('mycroft.skills.all_loaded', self.is_all_loaded)

    @property
    def skills_config(self):
        return self.config['skills']

    def load_priority(self):
        priority_skills = self.skills_config.get("priority_skills", [])
        for skill_name in priority_skills:
            path = join(self.skills_dir, skill_name)
            if path is not None:
                self._load_skill(path)
            else:
                LOG.error(
                    'Priority skill {} can\'t be found'.format(skill_name)
                )

        self._alive_status = True

    def download_or_update_defaults(self):
        # if skills dir does not exist (first run) download default skills
        if self.skills_config.get("repo"):
            if not isdir(self.skills_dir):
                LOG.info("Downloading default skills")
                try:
                    git.Repo.clone_from(self.skills_config.get("repo"), self.skills_dir)
                except Exception as e:
                    LOG.exception(e)
                    LOG.error("Could not download default skills!")
            else:
                LOG.info("Attempting skills update")
                try:
                    # git pull
                    g = git.cmd.Git(self.skills_dir)
                    g.pull()
                except Exception as e:
                    LOG.exception(e)
                    LOG.error("Could not update default skills, did you change any default skill?")
                    LOG.info("If you edit a single default skill, update will fail, blacklist skill instead")

    def run(self):
        """Load skills and update periodically from disk and internet."""
        self._connected_event.wait()
        self.download_or_update_defaults()
        self._load_on_startup()

        # Scan the file folder that contains Skills.  If a Skill is updated,
        # unload the existing version from memory and reload from the disk.
        while not self._stop_event.is_set():
            try:
                self._reload_modified_skills()
                self._load_new_skills()
                self._unload_removed_skills()
                sleep(2)  # Pause briefly before beginning next scan
            except Exception:
                LOG.exception('Something really unexpected has occured '
                              'and the skill manager loop safety harness was '
                              'hit.')
                sleep(30)

    def _load_on_startup(self):
        """Handle initial skill load."""
        LOG.info('Loading installed skills...')
        self._load_new_skills()
        LOG.info("Skills all loaded!")
        self.bus.emit(Message('mycroft.skills.initialized'))
        self._loaded_status = True

    def _reload_modified_skills(self):
        """Handle reload of recently changed skill(s)"""
        reload_occured = False
        for skill_dir in self._get_skill_directories():
            try:
                skill_loader = self.skill_loaders.get(skill_dir)
                if skill_loader is not None and skill_loader.reload_needed():
                    skill_loader.reload()
                    reload_occured = True
            except Exception:
                LOG.exception('Unhandled exception occured while '
                              'reloading {}'.format(skill_dir))

    def _load_new_skills(self):
        """Handle load of skills installed since startup."""
        for skill_dir in self._get_skill_directories():
            if skill_dir not in self.skill_loaders:
                self._load_skill(skill_dir)

    def _load_skill(self, skill_directory):
        skill_loader = SkillLoader(self.bus, skill_directory)
        try:
            skill_loader.load()
        except Exception:
            LOG.exception('Load of skill {} failed!'.format(skill_directory))
        finally:
            self.skill_loaders[skill_directory] = skill_loader

    def _get_skill_directories(self):
        skill_glob = glob(os.path.join(self.skills_dir, '*/'))

        skill_directories = []
        for skill_dir in skill_glob:
            # TODO: all python packages must have __init__.py!  Better way?
            # check if folder is a skill (must have __init__.py)
            if SKILL_MAIN_MODULE in os.listdir(skill_dir):
                skill_directories.append(skill_dir.rstrip('/'))
            else:
                LOG.debug('Found skills directory with no skill: ' + skill_dir)

        return skill_directories

    def _unload_removed_skills(self):
        """Shutdown removed skills."""
        skill_dirs = self._get_skill_directories()
        # Find loaded skills that don't exist on disk
        removed_skills = [
            s for s in self.skill_loaders.keys() if s not in skill_dirs
        ]
        for skill_dir in removed_skills:
            skill = self.skill_loaders[skill_dir]
            LOG.info('removing {}'.format(skill.skill_id))
            try:
                skill.unload()
            except Exception:
                LOG.exception('Failed to shutdown skill ' + skill.id)
            del self.skill_loaders[skill_dir]

    def is_alive(self, message=None):
        """Respond to is_alive status request."""
        if message:
            status = {'status': self._alive_status}
            self.bus.emit(message.response(data=status))
        return self._alive_status

    def is_all_loaded(self, message=None):
        """ Respond to all_loaded status request."""
        if message:
            status = {'status': self._loaded_status}
            self.bus.emit(message.response(data=status))

        return self._loaded_status

    def send_skill_list(self, _):
        """Send list of loaded skills."""
        try:
            message_data = {}
            for skill_dir, skill_loader in self.skill_loaders.items():
                message_data[skill_loader.skill_id] = dict(
                    active=skill_loader.active and skill_loader.loaded,
                    id=skill_loader.skill_id
                )
            self.bus.emit(Message('mycroft.skills.list', data=message_data))
        except Exception:
            LOG.exception('Failed to send skill list')

    def deactivate_skill(self, message):
        """Deactivate a skill."""
        try:
            for skill_loader in self.skill_loaders.values():
                if message.data['skill'] == skill_loader.skill_id:
                    skill_loader.deactivate()
        except Exception:
            LOG.exception('Failed to deactivate ' + message.data['skill'])

    def deactivate_except(self, message):
        """Deactivate all skills except the provided."""
        try:
            skill_to_keep = message.data['skill']
            LOG.info('Deactivating all skills except {}'.format(skill_to_keep))
            loaded_skill_file_names = [
                os.path.basename(skill_dir) for skill_dir in self.skill_loaders
            ]
            if skill_to_keep in loaded_skill_file_names:
                for skill in self.skill_loaders.values():
                    if skill.skill_id != skill_to_keep:
                        skill.deactivate()
            else:
                LOG.info('Couldn\'t find skill ' + message.data['skill'])
        except Exception:
            LOG.exception('An error occurred during skill deactivation!')

    def activate_skill(self, message):
        """Activate a deactivated skill."""
        try:
            for skill_loader in self.skill_loaders.values():
                if (message.data['skill'] in ('all', skill_loader.skill_id) and
                        not skill_loader.active):
                    skill_loader.activate()
        except Exception:
            LOG.exception('Couldn\'t activate skill')

    def stop(self):
        """Tell the manager to shutdown."""
        self._stop_event.set()
        # Do a clean shutdown of all skills
        for skill_loader in self.skill_loaders.values():
            if skill_loader.instance is not None:
                try:
                    skill_loader.instance.default_shutdown()
                except Exception:
                    LOG.exception(
                        'Failed to shut down skill: ' + skill_loader.skill_id
                    )

    def handle_converse_request(self, message):
        """Check if the targeted skill id can handle conversation

        If supported, the conversation is invoked.
        """
        skill_id = message.data['skill_id']

        # loop trough skills list and call converse for skill with skill_id
        skill_found = False
        for skill_loader in self.skill_loaders.values():
            if skill_loader.skill_id == skill_id:
                skill_found = True
                if not skill_loader.loaded:
                    error_message = 'converse requested but skill not loaded'
                    self._emit_converse_error(message, skill_id, error_message)
                    break
                try:
                    utterances = message.data['utterances']
                    lang = message.data['lang']
                    intents = skill_loader.instance.handle_internal_intents
                    handled = intents(message)
                    if not handled:
                        handled = skill_loader.instance.converse(utterances,
                                                                 lang)
                    self._emit_converse_response(handled, message, skill_loader)
                except Exception:
                    error_message = 'exception in converse method'
                    LOG.exception(error_message)
                    self._emit_converse_error(message, skill_id, error_message)
                finally:
                    break

        if not skill_found:
            error_message = 'skill id does not exist'
            self._emit_converse_error(message, skill_id, error_message)

    def _emit_converse_error(self, message, skill_id, error_msg):
        """Emit a message reporting the error back to the intent service."""
        reply = message.reply('skill.converse.response',
                              data=dict(skill_id=skill_id, error=error_msg))
        self.bus.emit(reply)
        # Also emit the old error message to keep compatibility and for any
        # listener on the bus
        reply = message.reply('skill.converse.error',
                              data=dict(skill_id=skill_id, error=error_msg))
        self.bus.emit(reply)

    def _emit_converse_response(self, result, message, skill_loader):
        reply = message.reply(
            'skill.converse.response',
            data=dict(skill_id=skill_loader.skill_id, result=result)
        )
        self.bus.emit(reply)
