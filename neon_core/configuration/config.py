import json
from neon_core.configuration.locations import DEFAULT_NEON_CONFIG, \
    SYSTEM_NEON_CONFIG, USER_NEON_CONFIG
from mycroft.configuration.config import LocalConf as _LocalConf, \
    Configuration as _Configuration
from ovos_utils.json_helper import merge_dict


class LocalConf(_LocalConf):
    def __init__(self, path):
        dict.__init__(self)
        if path:
            self.path = path
            self.load_local(path)

    def store(self, path=None):
        """
            Cache the received settings locally. The cache will be used if
            the remote is unreachable to load settings that are as close
            to the user's as possible
        """
        path = path or self.path
        with open(path, 'w', encoding="utf-8") as f:
            json.dump(self, f, indent=4, ensure_ascii=False)


class Configuration(_Configuration):

    @staticmethod
    def init(bus):
        # backward compatibility # TODO deprecate
        Configuration.set_config_update_handlers(bus)

    @staticmethod
    def load_config_stack(configs=None, cache=True, remote=False):
        """
            load a stack of config dicts into a single dict

            Args:
                configs (list): list of dicts to load
                cache (boolean): True if result should be cached

            Returns: merged dict of all configuration files
        """
        if not configs:
            configs = [LocalConf(DEFAULT_NEON_CONFIG),
                       LocalConf(SYSTEM_NEON_CONFIG),
                       LocalConf(USER_NEON_CONFIG),
                       Configuration.__patch]
        else:
            # Handle strings in stack
            for index, item in enumerate(configs):
                if isinstance(item, str):
                    configs[index] = LocalConf(item)

        # Merge all configs into one
        base = {}
        for c in configs:
            base = merge_dict(base, c, skip_empty=True, merge_lists=True)

        # copy into cache
        if cache:
            Configuration.__config.clear()
            for key in base:
                Configuration.__config[key] = base[key]
            return Configuration.__config
        else:
            return base


# some monkey patching...
# this ensures regular MycroftSkills import the neon config instead of the
# mycroft.conf
import mycroft.configuration
mycroft.configuration.LocalConf = LocalConf
mycroft.configuration.Configuration = Configuration
mycroft.configuration.config.LocalConf = LocalConf
mycroft.configuration.config.Configuration = Configuration
