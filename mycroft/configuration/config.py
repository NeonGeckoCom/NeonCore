
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

import re
import json
import inflection
from os.path import exists, isfile
from requests import RequestException

from mycroft.util.json_helper import load_commented_json, merge_dict
from mycroft.util.log import LOG
from neon_utils.configuration_utils import NGIConfig
from mycroft.configuration.locations import (DEFAULT_CONFIG, SYSTEM_CONFIG, USER_CONFIG, WEB_CONFIG_CACHE)


def is_remote_list(values):
    ''' check if this list corresponds to a backend formatted collection of
    dictionaries '''
    for v in values:
        if not isinstance(v, dict):
            return False
        if "@type" not in v.keys():
            return False
    return True


def translate_remote(config, setting):
    """
        Translate config names from server to equivalents usable
        in mycroft-core.

        Args:
                config:     base config to populate
                settings:   remote settings to be translated
    """
    IGNORED_SETTINGS = ["uuid", "@type", "active", "user", "device"]

    for k, v in setting.items():
        if k not in IGNORED_SETTINGS:
            # Translate the CamelCase values stored remotely into the
            # Python-style names used within mycroft-core.
            key = inflection.underscore(re.sub(r"Setting(s)?", "", k))
            if isinstance(v, dict):
                config[key] = config.get(key, {})
                translate_remote(config[key], v)
            elif isinstance(v, list):
                if is_remote_list(v):
                    if key not in config:
                        config[key] = {}
                    translate_list(config[key], v)
                else:
                    config[key] = v
            else:
                config[key] = v


def translate_list(config, values):
    """
        Translate list formated by mycroft server.

        Args:
            config (dict): target config
            values (list): list from mycroft server config
    """
    for v in values:
        module = v["@type"]
        if v.get("active"):
            config["module"] = module
        config[module] = config.get(module, {})
        translate_remote(config[module], v)


class LocalConf(dict):
    """
        Config dict from file.
    """
    def __init__(self, path):
        super(LocalConf, self).__init__()
        if path:
            self.path = path
            self.load_local(path)

    def load_local(self, path):
        """
            Load local json file into self.

            Args:
                path (str): file to load
        """
        if exists(path) and isfile(path):
            try:
                config = load_commented_json(path)
                for key in config:
                    self.__setitem__(key, config[key])

                LOG.debug("Configuration {} loaded".format(path))
            except Exception as e:
                LOG.error("Error loading configuration '{}'".format(path))
                LOG.error(repr(e))
        else:
            LOG.debug("Configuration '{}' not defined, skipping".format(path))

    def store(self, path=None):
        """
            Cache the received settings locally. The cache will be used if
            the remote is unreachable to load settings that are as close
            to the user's as possible
        """
        path = path or self.path
        with open(path, 'w') as f:
            json.dump(self, f, indent=2)

    def merge(self, conf):
        merge_dict(self, conf)


class RemoteConf(LocalConf):
    """
        Config dict fetched from mycroft.ai
    """
    def __init__(self, cache=None):
        super(RemoteConf, self).__init__(None)

        cache = cache or WEB_CONFIG_CACHE
        from mycroft.api import is_paired, is_disabled
        if not is_paired() or is_disabled():
            self.load_local(cache)
            return

        try:
            # Here to avoid cyclic import
            from mycroft.api import DeviceApi
            api = DeviceApi()
            setting = api.get_settings() or {}

            try:
                location = api.get_location()
            except RequestException as e:
                LOG.error("RequestException fetching remote location: {}"
                          .format(str(e)))
                if exists(cache) and isfile(cache):
                    location = load_commented_json(cache).get('location')

            if location:
                setting["location"] = location
            # Remove server specific entries
            config = {}
            translate_remote(config, setting)
            for key in config:
                self.__setitem__(key, config[key])
            self.store(cache)

        except RequestException as e:
            LOG.error("RequestException fetching remote configuration: {}"
                      .format(str(e)))
            self.load_local(cache)

        except Exception as e:
            LOG.error("Failed to fetch remote configuration: %s" % repr(e),
                      exc_info=True)
            self.load_local(cache)


class Configuration:
    __config = {}  # Cached config
    __patch = {}  # Patch config that skills can update to override config
    __neon = {}

    @staticmethod
    def get(configs=None, cache=True):
        """
            Get configuration, returns cached instance if available otherwise
            builds a new configuration dict.

            Args:
                configs (list): List of configuration dicts
                cache (boolean): True if the result should be cached
        """
        ngi_local = NGIConfig("ngi_local_conf").make_equal_by_keys(NGIConfig("default_local_conf").content)
        Configuration.__neon["local"] = ngi_local
        ngi_user = NGIConfig("ngi_user_info").make_equal_by_keys(NGIConfig("default_user_info").content)
        Configuration.__neon["user"] = ngi_user
        ngi_auth = NGIConfig("ngi_auth_vars")
        Configuration.__neon["auth"] = ngi_auth

        # TODO: Only do this once? this could get computationally expensive to always rebuild config DM
        if Configuration.__config:
            mycroft_config = Configuration.__config
        else:
            mycroft_config = Configuration.load_config_stack(configs, cache)

        mycroft_keys = mycroft_config.pop("keys")

        date_format = mycroft_config.pop("date_format")
        mycroft_location = mycroft_config.pop("location")
        unit = mycroft_config.pop("system_unit")
        time_format = mycroft_config.pop("time_format")  # half'?
        mycroft_user = {"units": {"time": 12 if time_format == 'half' else 24,
                                  "date": date_format,
                                  "measure": unit},
                        "location": {"lat": mycroft_location["coordinate"].get("latitude"),
                                     "lng": mycroft_location["coordinate"].get("longitude"),
                                     "city": mycroft_location["city"].get("name"),
                                     "state": mycroft_location["city"].get("state", {}).get("name"),
                                     "country": mycroft_location["city"].get("state", {}).get("country",
                                                                                              {}).get("name"),
                                     "tz": mycroft_location["timezone"].get("code")}}
        user_config = ngi_user.update_keys(mycroft_user)
        auth_config = ngi_auth.update_keys(mycroft_keys)
        local_config = ngi_local.update_keys(mycroft_config)
        local_config["keys"] = auth_config
        local_config["user"] = user_config  # TODO: This should probably be depreciated? DM
        return local_config

    @staticmethod
    def load_config_stack(configs=None, cache=False):
        """
            load a stack of config dicts into a single dict

            Args:
                configs (list): list of dicts to load
                cache (boolean): True if result should be cached

            Returns: merged dict of all configuration files
        """
        if not configs:
            configs = [LocalConf(DEFAULT_CONFIG), RemoteConf(),
                       LocalConf(SYSTEM_CONFIG), LocalConf(USER_CONFIG),
                       Configuration.__patch]
        else:
            # Handle strings in stack
            for index, item in enumerate(configs):
                if isinstance(item, str):
                    configs[index] = LocalConf(item)

        # Merge all configs into one
        base = {}
        for c in configs:
            merge_dict(base, c)

        for config_name, config_obj in Configuration.__neon:
            base[config_name] = config_obj.content
        # copy into cache
        if cache:
            Configuration.__config.clear()
            for key in base:
                Configuration.__config[key] = base[key]
            return Configuration.__config
        else:
            return base

    @staticmethod
    def set_config_update_handlers(bus):
        """Setup websocket handlers to update config.

        Args:
            bus: Message bus client instance
        """
        bus.on("configuration.updated", Configuration.updated)
        bus.on("configuration.patch", Configuration.patch)

    @staticmethod
    def updated(message):
        """
            handler for configuration.updated, triggers an update
            of cached config.
        """
        if message.data.get("modified"):
            LOG.info(f"Updated: {message.data['modified']}")
            LOG.info(message.context.get("origin"))
        Configuration.load_config_stack(cache=True)

    @staticmethod
    def patch(message):
        """
            patch the volatile dict usable by skills

            Args:
                message: Messagebus message should contain a config
                         in the data payload.
        """
        config = message.data.get("config", {})
        merge_dict(Configuration.__patch, config)
        Configuration.load_config_stack(cache=True)
