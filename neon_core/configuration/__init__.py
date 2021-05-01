from neon_core.configuration.config import Configuration, LocalConf
from neon_core.configuration.locations import *


def get_private_keys():
    return Configuration.get().get("keys", {})
