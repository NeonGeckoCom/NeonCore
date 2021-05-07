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
"""Message bus configuration loader.

The message bus event handler and client use basically the same configuration.
This code is re-used in both to load config values.
"""
from collections import namedtuple

from mycroft.configuration import Configuration
from mycroft.util.log import LOG

MessageBusConfig = namedtuple(
    'MessageBusConfig',
    ['host', 'port', 'route', 'ssl', 'allow_self_signed', 'ssl_cert',
     'ssl_key']
)


def load_message_bus_config(**overrides):
    """Load the bits of device configuration needed to run the message bus."""
    LOG.info('Loading message bus configs')
    config = Configuration.get()
    try:
        websocket_configs = config['websocket']
    except KeyError as ke:
        LOG.error('No websocket configs found ({})'.format(repr(ke)))
        raise
    else:
        mb_config = MessageBusConfig(
            host=overrides.get('host') or websocket_configs.get('host'),
            port=overrides.get('port') or websocket_configs.get('port'),
            route=overrides.get('route') or websocket_configs.get('route'),
            ssl=overrides.get('ssl') or websocket_configs.get('ssl'),
            allow_self_signed=overrides.get("allow_self_signed") or
                              websocket_configs.get("allow_self_signed", False),
            ssl_cert=overrides.get("ssl_cert") or websocket_configs.get("ssl_cert"),
            ssl_key=overrides.get("ssl_key") or websocket_configs.get("ssl_key")
        )
        if not all([mb_config.host, mb_config.port, mb_config.route]):
            error_msg = 'Missing one or more websocket configs'
            LOG.error(error_msg)
            raise ValueError(error_msg)

    return mb_config
