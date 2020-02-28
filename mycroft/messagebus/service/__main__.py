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
""" Message bus service for mycroft-core

The message bus facilitates inter-process communication between mycroft-core
processes. It implements a websocket server so can also be used by external
systems to integrate with the Mycroft system.
"""
import sys
from os.path import expanduser, isfile
from tornado import autoreload, web, ioloop

from mycroft.lock import Lock  # creates/supports PID locking file
from mycroft.messagebus.load_config import load_message_bus_config
from mycroft.messagebus.service.event_handler import MessageBusEventHandler
from mycroft.util import (
    reset_sigint_handler,
    create_daemon,
    wait_for_exit_signal
)
from mycroft.util.log import LOG


def main():
    import tornado.options
    LOG.info('Starting message bus service...')
    reset_sigint_handler()
    lock = Lock("service")
    # Disable all tornado logging so mycroft loglevel isn't overridden
    tornado.options.parse_command_line(sys.argv + ['--logging=None'])

    def reload_hook():
        """ Hook to release lock when auto reload is triggered. """
        lock.delete()

    autoreload.add_reload_hook(reload_hook)
    config = load_message_bus_config()
    routes = [(config.route, MessageBusEventHandler)]
    application = web.Application(routes, debug=True)

    ssl_options = None
    if config.ssl:
        cert = expanduser(config.ssl_cert)
        key = expanduser(config.ssl_key)
        if not isfile(key) or not isfile(cert):
            LOG.error("ssl keys dont exist, falling back to unsecured socket")
        else:
            LOG.info("using ssl key at " + key)
            LOG.info("using ssl certificate at " + cert)
            ssl_options = {"certfile": cert, "keyfile": key}
    if ssl_options:
        LOG.info("wss connection started")
        application.listen(config.port, config.host, ssl_options=ssl_options)
    else:
        LOG.info("ws connection started")
        application.listen(config.port, config.host)

    create_daemon(ioloop.IOLoop.instance().start)
    LOG.info('Message bus service started!')
    wait_for_exit_signal()


if __name__ == "__main__":
    main()
