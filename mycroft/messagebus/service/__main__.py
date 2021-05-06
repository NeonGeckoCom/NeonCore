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
