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
"""Keep the settingsmeta.json and settings.json files in sync with the backend.

The SkillSettingsMeta and SkillSettings classes run a synchronization every
minute to ensure the device and the server have the same values.

The settingsmeta.json file (or settingsmeta.yaml, if you prefer working with
yaml) in the skill's root directory contains instructions for the Selene UI on
how to display and update a skill's settings, if there are any.

For example, you might have a setting named "username".  In the settingsmeta
you can describe the interface to edit that value with:
    ...
    "fields": [
        {
            "name": "username",
            "type": "email",
            "label": "Email address to associate",
            "placeholder": "example@mail.com",
            "value": ""
        }
    ]
    ...

When the user changes the setting via the web UI, it will be sent down to all
the devices related to an account and automatically placed into
settings['username'].  Any local changes made to the value (e.g. via a verbal
interaction) will also be synchronized to the server to show on the web
interface.

The settings.json file contains name/value pairs for each setting.  There can
be entries in settings.json that are not related to those the user can
manipulate on the web.  There is logic in the SkillSettings class to ensure
these "hidden" settings are not affected when the synchronization occurs.  A
skill can define a function that will be called when any settings change.

SkillSettings Usage Example:
    from mycroft.skill.settings import SkillSettings

        s = SkillSettings('./settings.json', 'ImportantSettings')
        s.skill_settings['meaning of life'] = 42
        s.skill_settings['flower pot sayings'] = 'Not again...'
        s.save_settings()  # This happens automagically in a MycroftSkill
"""
import json
import re
from pathlib import Path
from mycroft.util import camel_case_split
from mycroft.util.log import LOG


def get_local_settings(skill_dir, skill_name) -> dict:
    """Build a dictionary using the JSON string stored in settings.json."""
    skill_settings = {}
    settings_path = Path(skill_dir).joinpath('settings.json')
    LOG.info(settings_path)
    if settings_path.exists():
        with open(str(settings_path)) as settings_file:
            settings_file_content = settings_file.read()
        if settings_file_content:
            try:
                skill_settings = json.loads(settings_file_content)
            # TODO change to check for JSONDecodeError in 19.08
            except Exception:
                log_msg = 'Failed to load {} settings from settings.json'
                LOG.exception(log_msg.format(skill_name))

    return skill_settings


def save_settings(skill_dir, skill_settings):
    """Save skill settings to file."""
    if isinstance(skill_settings, Settings):
        settings_to_save = skill_settings.as_dict()
    else:
        settings_to_save = skill_settings
    settings_path = Path(skill_dir).joinpath('settings.json')
    if Path(skill_dir).exists():
        with open(str(settings_path), 'w') as settings_file:
            try:
                json.dump(settings_to_save, settings_file)
            except Exception:
                LOG.exception('error saving skill settings to '
                              '{}'.format(settings_path))
            else:
                LOG.info('Skill settings successfully saved to '
                         '{}' .format(settings_path))
    else:
        LOG.info('Skill folder no longer exists, can\'t save settings.')


def get_display_name(skill_name: str):
    """Splits camelcase and removes leading/trailing "skill"."""
    skill_name = re.sub(r'(^[Ss]kill|[Ss]kill$)', '', skill_name)
    return camel_case_split(skill_name)


def _extract_settings_from_meta(settings_meta: dict) -> dict:
    """Extract the skill setting name/value pairs from settingsmeta.json

    Args:
        settings_meta: contents of the settingsmeta.json

    Returns:
        Dictionary of settings keyed by name
    """
    fields = {}
    try:
        sections = settings_meta['skillMetadata']['sections']
    except KeyError:
        pass
    else:
        for section in sections:
            for field in section.get('fields', []):
                fields[field['name']] = field['value']

    return fields


# TODO: remove in 20.02
class Settings:
    def __init__(self, skill):
        self._skill = skill
        self._settings = get_local_settings(skill.root_dir, skill.name)

    def __getattr__(self, attr):
        if attr not in ['store', 'set_changed_callback', 'as_dict']:
            return getattr(self._settings, attr)
        else:
            return getattr(self, attr)

    def __setitem__(self, key, val):
        self._settings[key] = val

    def __getitem__(self, key):
        return self._settings[key]

    def __iter__(self):
        return iter(self._settings)

    def __contains__(self, key):
        return key in self._settings

    def __delitem__(self, item):
        del self._settings[item]

    def store(self, force=False):
        LOG.warning('DEPRECATED - use mycroft.skills.settings.save_settings()')
        save_settings(self._skill.root_dir, self._settings)

    def set_changed_callback(self, callback):
        LOG.warning('DEPRECATED - set the settings_change_callback attribute')
        self._skill.settings_change_callback = callback

    def as_dict(self):
        return self._settings

    def shutdown(self):
        """Shutdown the Settings object removing any references."""
        self._skill = None
