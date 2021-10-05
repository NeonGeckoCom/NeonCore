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

import asyncio
import json
from threading import Thread
from typing import Optional, Awaitable
import sys
import tornado.options
import tornado.web as web
from mycroft.messagebus.message import Message
from mycroft.util.log import LOG
from neon_core.configuration import Configuration
from neon_core.gui.gui import GUIManager
from neon_core.gui.resting_screen import RestingScreen
from tornado import ioloop
from tornado.websocket import WebSocketHandler

##########################################################################
# GUIConnection
##########################################################################

gui_app_settings = {
    'debug': True
}


class GUIWebsocketHandler(WebSocketHandler):
    """The socket pipeline between the GUI and Mycroft."""
    clients = []

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def open(self):
        GUIWebsocketHandler.clients.append(self)
        LOG.info('New Connection opened!')
        self.synchronize()

    def on_close(self):
        LOG.info('Closing {}'.format(id(self)))
        GUIWebsocketHandler.clients.remove(self)

    def synchronize(self):
        """ Upload namespaces, pages and data to the last connected. """
        namespace_pos = 0
        gui_service = self.application.gui_service

        for namespace, pages in gui_service.loaded:
            LOG.info('Sync {}'.format(namespace))
            # Insert namespace
            self.send({"type": "mycroft.session.list.insert",
                       "namespace": "mycroft.system.active_skills",
                       "position": namespace_pos,
                       "data": [{"skill_id": namespace}]
                       })
            # Insert pages
            self.send({"type": "mycroft.gui.list.insert",
                       "namespace": namespace,
                       "position": 0,
                       "data": [{"url": p} for p in pages]
                       })
            # Insert data
            data = gui_service.datastore.get(namespace, {})
            for key in data:
                self.send({"type": "mycroft.session.set",
                           "namespace": namespace,
                           "data": {key: data[key]}
                           })
            namespace_pos += 1

    def on_message(self, message):
        LOG.info("Received: {}".format(message))
        msg = json.loads(message)
        if (msg.get('type') == "mycroft.events.triggered" and
                (msg.get('event_name') == 'page_gained_focus' or
                 msg.get('event_name') == 'system.gui.user.interaction')):
            # System event, a page was changed
            msg_type = 'gui.page_interaction'
            msg_data = {'namespace': msg['namespace'],
                        'page_number': msg['parameters'].get('number'),
                        'skill_id': msg['parameters'].get('skillId')}
        elif msg.get('type') == "mycroft.events.triggered":
            # A normal event was triggered
            msg_type = '{}.{}'.format(msg['namespace'], msg['event_name'])
            msg_data = msg['parameters']

        elif msg.get('type') == 'mycroft.session.set':
            # A value was changed send it back to the skill
            msg_type = '{}.{}'.format(msg['namespace'], 'set')
            msg_data = msg['data']
        else:
            LOG.error(f"Unhandled message type: {msg.get('type')}")
            return
        message = Message(msg_type, msg_data)
        LOG.info('Forwarding to bus...')
        self.application.gui_service.bus.emit(message)
        LOG.info('Done!')

    def write_message(self, *arg, **kwarg):
        """Wraps WebSocketHandler.write_message() with a lock. """
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        with write_lock:
            super().write_message(*arg, **kwarg)

    def send(self, data):
        """Send the given data across the socket as JSON

        Args:
            data (dict): Data to transmit
        """
        s = json.dumps(data)
        LOG.info('Sending {}'.format(s))
        self.write_message(s)

    def check_origin(self, origin):
        """Disable origin check to make js connections work."""
        return True


class NeonGUIService(Thread):
    def __init__(self, config=None, debug=False, daemonic=False):
        super().__init__()
        config_core = Configuration.get()
        self.config = config or config_core['gui_websocket']
        self.debug = debug
        self.setDaemon(daemonic)

    def run(self):
        LOG.info('Starting GUI service...')
        self._init_gui()
        self._init_tornado()
        self._listen()
        LOG.info('GUI service started!')
        ioloop.IOLoop.instance().start()

    def _init_tornado(self):
        # Disable all tornado logging so mycroft loglevel isn't overridden
        tornado.options.parse_command_line(sys.argv + ['--logging=None'])
        # get event loop for this thread
        asyncio.set_event_loop(asyncio.new_event_loop())

    def _init_gui(self):
        self.gui_manager = GUIManager()
        RestingScreen()

    def _listen(self):
        routes = [(self.config['route'], GUIWebsocketHandler)]
        application = web.Application(routes, debug=True)
        application.gui_service = self.gui_manager
        application.listen(self.config['base_port'], self.config['host'])

    def shutdown(self):
        pass  # TODO
