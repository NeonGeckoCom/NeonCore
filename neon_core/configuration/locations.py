import os
from os.path import join, dirname, expanduser, exists

DEFAULT_NEON_CONFIG = join(dirname(__file__), 'neon.conf')
SYSTEM_NEON_CONFIG = os.environ.get('NEON_SYSTEM_CONFIG',
                               '/etc/neon/neon.conf')
USER_NEON_CONFIG = join(expanduser('~'), '.neon/neon.conf')


# some monkey patching...
# this ensures regular MycroftSkills import the neon config instead of the
# mycroft.conf
import mycroft.configuration
mycroft.configuration.locations.DEFAULT_CONFIG = DEFAULT_NEON_CONFIG
mycroft.configuration.locations.SYSTEM_CONFIG = SYSTEM_NEON_CONFIG
mycroft.configuration.locations.USER_CONFIG = USER_NEON_CONFIG
