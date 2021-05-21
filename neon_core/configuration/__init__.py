from neon_core.configuration.config import Configuration, LocalConf
from neon_core.configuration.locations import *
from ovos_utils.configuration import set_config_name


def get_private_keys():
    return Configuration.get(remote=False).get("keys", {})

# make ovos_utils load the proper .conf files
set_config_name("neon", "neon_core")
