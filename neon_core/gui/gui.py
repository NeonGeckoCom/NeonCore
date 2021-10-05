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
import tornado.web as web

from os.path import join
from collections import namedtuple
from threading import Lock
from typing import Optional, Awaitable
from tornado import ioloop
from tornado.websocket import WebSocketHandler
from neon_core.configuration import Configuration
from neon_core.messagebus import get_messagebus
from ovos_utils import wait_for_exit_signal

from mycroft.util import create_daemon
from mycroft.util.log import LOG
from mycroft.messagebus.message import Message
from mycroft.util import resolve_resource_file


class SkillGUI:
    """SkillGUI - Interface to the Graphical User Interface

    Values set in this class are synced to the GUI, accessible within QML
    via the built-in sessionData mechanism.  For example, in Python you can
    write in a skill:
        self.gui['temp'] = 33
        self.gui.show_page('Weather.qml')
    Then in the Weather.qml you'd access the temp via code such as:
        text: sessionData.time
    """

    def __init__(self, skill):
        self.__session_data = {}  # synced to GUI for use by this skill's pages
        self.page = None    # the active GUI page (e.g. QML template) to show
        self.skill = skill
        self.on_gui_changed_callback = None
        self.config = Configuration.get()

    @property
    def remote_url(self):
        """Returns configuration value for url of remote-server."""
        return self.config.get('remote-server')

    def build_message_type(self, event):
        """Builds a message matching the output from the enclosure."""
        return '{}.{}'.format(self.skill.skill_id, event)

    def setup_default_handlers(self):
        """Sets the handlers for the default messages."""
        msg_type = self.build_message_type('set')
        self.skill.add_event(msg_type, self.gui_set)

    def register_handler(self, event, handler):
        """Register a handler for GUI events.

        When using the triggerEvent method from Qt
        triggerEvent("event", {"data": "cool"})

        Arguments:
            event (str):    event to catch
            handler:        function to handle the event
        """
        msg_type = self.build_message_type(event)
        self.skill.add_event(msg_type, handler)

    def set_on_gui_changed(self, callback):
        """Registers a callback function to run when a value is
        changed from the GUI.

        Arguments:
            callback:   Function to call when a value is changed
        """
        self.on_gui_changed_callback = callback

    def gui_set(self, message):
        """Handler catching variable changes from the GUI.

        Arguments:
            message: Messagebus message
        """
        for key in message.data:
            self[key] = message.data[key]
        if self.on_gui_changed_callback:
            self.on_gui_changed_callback()

    def __setitem__(self, key, value):
        """Implements set part of dict-like behaviour with named keys."""
        self.__session_data[key] = value

        if self.page:
            # emit notification (but not needed if page has not been shown yet)
            data = self.__session_data.copy()
            data.update({'__from': self.skill.skill_id})
            self.skill.bus.emit(Message("gui.value.set", data))

    def __getitem__(self, key):
        """Implements get part of dict-like behaviour with named keys."""
        return self.__session_data[key]

    def __contains__(self, key):
        """Implements the "in" operation."""
        return self.__session_data.__contains__(key)

    def clear(self):
        """Reset the value dictionary, and remove namespace from GUI."""
        self.__session_data = {}
        self.page = None
        self.skill.bus.emit(Message("gui.clear.namespace",
                                    {"__from": self.skill.skill_id}))

    def send_event(self, event_name, params=None):
        """Trigger a gui event.

        Arguments:
            event_name (str): name of event to be triggered
            params: json serializable object containing any parameters that
                    should be sent along with the request.
        """
        params = params or {}
        self.skill.bus.emit(Message("gui.event.send",
                                    {"__from": self.skill.skill_id,
                                     "event_name": event_name,
                                     "params": params}))

    def show_page(self, name, override_idle=None):
        """Begin showing the page in the GUI

        Arguments:
            name (str): Name of page (e.g "mypage.qml") to display
            override_idle (boolean, int):
                True: Takes over the resting page indefinitely
                (int): Delays resting page for the specified number of
                       seconds.
        """
        self.show_pages([name], 0, override_idle)

    def show_pages(self, page_names, index=0, override_idle=None):
        """Begin showing the list of pages in the GUI.

        Arguments:
            page_names (list): List of page names (str) to display, such as
                               ["Weather.qml", "Forecast.qml", "Details.qml"]
            index (int): Page number (0-based) to show initially.  For the
                         above list a value of 1 would start on "Forecast.qml"
            override_idle (boolean, int):
                True: Takes over the resting page indefinitely
                (int): Delays resting page for the specified number of
                       seconds.
        """
        if not isinstance(page_names, list):
            raise ValueError('page_names must be a list')

        if index > len(page_names):
            raise ValueError('Default index is larger than page list length')

        self.page = page_names[index]

        # First sync any data...
        data = self.__session_data.copy()
        data.update({'__from': self.skill.skill_id})
        self.skill.bus.emit(Message("gui.value.set", data))

        # Convert pages to full reference
        page_urls = []
        for name in page_names:
            if name.startswith("SYSTEM"):
                page = resolve_resource_file(join('ui', name))
            else:
                page = self.skill.find_resource(name, 'ui')
            if page:
                if self.config.get('remote'):
                    page_urls.append(self.remote_url + "/" + page)
                else:
                    page_urls.append("file://" + page)
            else:
                raise FileNotFoundError("Unable to find page: {}".format(name))

        self.skill.bus.emit(Message("gui.page.show",
                                    {"page": page_urls,
                                     "index": index,
                                     "__from": self.skill.skill_id,
                                     "__idle": override_idle}))

    def remove_page(self, page):
        """Remove a single page from the GUI.

        Arguments:
            page (str): Page to remove from the GUI
        """
        return self.remove_pages([page])

    def remove_pages(self, page_names):
        """Remove a list of pages in the GUI.

        Arguments:
            page_names (list): List of page names (str) to display, such as
                               ["Weather.qml", "Forecast.qml", "Other.qml"]
        """
        if not isinstance(page_names, list):
            raise ValueError('page_names must be a list')

        # Convert pages to full reference
        page_urls = []
        for name in page_names:
            page = self.skill.find_resource(name, 'ui')
            if page:
                page_urls.append("file://" + page)
            else:
                raise FileNotFoundError("Unable to find page: {}".format(name))

        self.skill.bus.emit(Message("gui.page.delete",
                                    {"page": page_urls,
                                     "__from": self.skill.skill_id}))

    def show_text(self, text, title=None, override_idle=None):
        """Display a GUI page for viewing simple text.

        Arguments:
            text (str): Main text content.  It will auto-paginate
            title (str): A title to display above the text content.
            override_idle (boolean, int):
                True: Takes over the resting page indefinitely
                (int): Delays resting page for the specified number of
                       seconds.
        """
        self.clear()
        self["text"] = text
        self["title"] = title
        self.show_page("SYSTEM_TextFrame.qml", override_idle)

    def show_image(self, url, caption=None,
                   title=None, fill=None,
                   override_idle=None):
        """Display a GUI page for viewing an image.

        Arguments:
            url (str): Pointer to the image
            caption (str): A caption to show under the image
            title (str): A title to display above the image content
            fill (str): Fill type supports 'PreserveAspectFit',
            'PreserveAspectCrop', 'Stretch'
            override_idle (boolean, int):
                True: Takes over the resting page indefinitely
                (int): Delays resting page for the specified number of
                       seconds.
        """
        self.clear()
        self["image"] = url
        self["title"] = title
        self["caption"] = caption
        self["fill"] = fill
        self.show_page("SYSTEM_ImageFrame.qml", override_idle)

    def show_html(self, html, resource_url=None, override_idle=None):
        """Display an HTML page in the GUI.

        Arguments:
            html (str): HTML text to display
            resource_url (str): Pointer to HTML resources
            override_idle (boolean, int):
                True: Takes over the resting page indefinitely
                (int): Delays resting page for the specified number of
                       seconds.
        """
        self.clear()
        self["html"] = html
        self["resourceLocation"] = resource_url
        self.show_page("SYSTEM_HtmlFrame.qml", override_idle)

    def show_url(self, url, override_idle=None):
        """Display an HTML page in the GUI.

        Arguments:
            url (str): URL to render
            override_idle (boolean, int):
                True: Takes over the resting page indefinitely
                (int): Delays resting page for the specified number of
                       seconds.
        """
        self.clear()
        self["url"] = url
        self.show_page("SYSTEM_UrlFrame.qml", override_idle)

    def shutdown(self):
        """Shutdown gui interface.

        Clear pages loaded through this interface and remove the skill
        reference to make ref counting warning more precise.
        """
        self.clear()
        self.skill = None


Namespace = namedtuple('Namespace', ['name', 'pages'])
write_lock = Lock()
namespace_lock = Lock()

RESERVED_KEYS = ['__from', '__idle']


def _get_page_data(message):
    """ Extract page related data from a message.

    Args:
        message: messagebus message object
    Returns:
        tuple (page, namespace, index)
    Raises:
        ValueError if value is missing.
    """
    data = message.data
    # Note:  'page' can be either a string or a list of strings
    if 'page' not in data:
        raise ValueError("Page missing in data")
    if 'index' in data:
        index = data['index']
    else:
        index = 0
    page = data.get("page", "")
    namespace = data.get("__from", "")
    return page, namespace, index


class GUIManager:
    def __init__(self, bus=None):
        config = Configuration.get()
        self.lang = config['lang']
        self.config = config

        # Establish Enclosure's websocket connection to the messagebus
        self.bus = bus or get_messagebus()

        # This datastore holds the data associated with the GUI provider. Data
        # is stored in Namespaces, so you can have:
        # self.datastore["namespace"]["name"] = value
        # Typically the namespace is a meaningless identifier, but there is a
        # special "SYSTEM" namespace.
        self.datastore = {}

        # self.loaded is a list, each element consists of a namespace named
        # tuple.
        # The namespace namedtuple has the properties "name" and "pages"
        # The name contains the namespace name as a string and pages is a
        # mutable list of loaded pages.
        #
        # [Namespace name, [List of loaded qml pages]]
        # [
        # ["SKILL_NAME", ["page1.qml, "page2.qml", ... , "pageN.qml"]
        # [...]
        # ]
        self.loaded = []  # list of lists in order.
        self.explicit_move = True  # Set to true to send reorder commands

        # Listen for new GUI clients to announce themselves on the main bus
        self.active_namespaces = []
        self.bus.on("mycroft.gui.connected", self.on_gui_client_connected)
        self.register_gui_handlers()

        # First send any data:
        self.bus.on("gui.value.set", self.on_gui_set_value)
        self.bus.on("gui.page.show", self.on_gui_show_page)
        self.bus.on("gui.page.delete", self.on_gui_delete_page)
        self.bus.on("gui.clear.namespace", self.on_gui_delete_namespace)
        self.bus.on("gui.event.send", self.on_gui_send_event)
        self.bus.on("gui.status.request", self.handle_gui_status_request)

    def run(self):
        try:
            if not self.bus.started_running:
                self.bus.run_forever()
            else:
                wait_for_exit_signal()
        except Exception as e:
            LOG.error("Error: {0}".format(e))
            self.stop()

    def stop(self):
        pass

    ######################################################################
    # GUI client API
    @property
    def gui_connected(self):
        """Returns True if at least 1 gui is connected, else False"""
        return len(GUIWebsocketHandler.clients) > 0

    def handle_gui_status_request(self, message):
        """Reply to gui status request, allows querying if a gui is
        connected using the message bus"""
        self.bus.emit(message.reply("gui.status.request.response",
                                    {"connected": self.gui_connected}))

    @staticmethod
    def send(msg_dict):
        """ Send to all registered GUIs. """
        for connection in GUIWebsocketHandler.clients:
            try:
                connection.send(msg_dict)
            except Exception as e:
                LOG.exception(repr(e))

    def on_gui_send_event(self, message):
        """ Send an event to the GUIs. """
        try:
            data = {'type': 'mycroft.events.triggered',
                    'namespace': message.data.get('__from'),
                    'event_name': message.data.get('event_name'),
                    'params': message.data.get('params')}
            self.send(data)
        except Exception as e:
            LOG.error('Could not send event ({})'.format(repr(e)))

    def on_gui_set_value(self, message):
        data = message.data
        namespace = data.get("__from", "")

        # Pass these values on to the GUI renderers
        for key in data:
            if key not in RESERVED_KEYS:
                try:
                    self.set(namespace, key, data[key])
                except Exception as e:
                    LOG.exception(repr(e))

    def set(self, namespace, name, value):
        """ Perform the send of the values to the connected GUIs. """
        if namespace not in self.datastore:
            self.datastore[namespace] = {}
        if self.datastore[namespace].get(name) != value:
            self.datastore[namespace][name] = value

            # If the namespace is loaded send data to GUI
            if namespace in [ns.name for ns in self.loaded]:
                msg = {"type": "mycroft.session.set",
                       "namespace": namespace,
                       "data": {name: value}}
                self.send(msg)

    def on_gui_delete_page(self, message):
        """ Bus handler for removing pages. """
        page, namespace, _ = _get_page_data(message)
        try:
            with namespace_lock:
                self.remove_pages(namespace, page)
        except Exception as e:
            LOG.exception(repr(e))

    def on_gui_delete_namespace(self, message):
        """ Bus handler for removing namespace. """
        try:
            namespace = message.data['__from']
            with namespace_lock:
                self.remove_namespace(namespace)
        except Exception as e:
            LOG.exception(repr(e))

    def on_gui_show_page(self, message):
        try:
            page, namespace, index = _get_page_data(message)
            # Pass the request to the GUI(s) to pull up a page template
            with namespace_lock:
                self.show(namespace, page, index)
        except Exception as e:
            LOG.exception(repr(e))

    def __find_namespace(self, namespace):
        for i, skill in enumerate(self.loaded):
            if skill[0] == namespace:
                return i
        return None

    def __insert_pages(self, namespace, pages):
        """ Insert pages into the namespace

        Args:
            namespace (str): Namespace to add to
            pages (list):    Pages (str) to insert
        """
        LOG.debug("Inserting new pages")
        if not isinstance(pages, list):
            raise ValueError('Argument must be list of pages')

        self.send({"type": "mycroft.gui.list.insert",
                   "namespace": namespace,
                   "position": len(self.loaded[0].pages),
                   "data": [{"url": p} for p in pages]
                   })
        # Insert the pages into local reprensentation as well.
        updated = Namespace(self.loaded[0].name, self.loaded[0].pages + pages)
        self.loaded[0] = updated

    def __remove_page(self, namespace, pos):
        """ Delete page.

        Args:
            namespace (str): Namespace to remove from
            pos (int):      Page position to remove
        """
        LOG.debug("Deleting {} from {}".format(pos, namespace))
        self.send({"type": "mycroft.gui.list.remove",
                   "namespace": namespace,
                   "position": pos,
                   "items_number": 1
                   })
        # Remove the page from the local reprensentation as well.
        self.loaded[0].pages.pop(pos)
        # Add a check to return any display to idle from position 0
        if pos == 0 and len(self.loaded[0].pages) == 0:
            self.bus.emit(Message("mycroft.device.show.idle"))

    def __insert_new_namespace(self, namespace, pages):
        """ Insert new namespace and pages.

        This first sends a message adding a new namespace at the
        highest priority (position 0 in the namespace stack)

        Args:
            namespace (str):  The skill namespace to create
            pages (list):     Pages to insert (name matches QML)
        """
        LOG.debug("Inserting new namespace")
        self.send({"type": "mycroft.session.list.insert",
                   "namespace": "mycroft.system.active_skills",
                   "position": 0,
                   "data": [{"skill_id": namespace}]
                   })

        # Load any already stored Data
        data = self.datastore.get(namespace, {})
        for key in data:
            msg = {"type": "mycroft.session.set",
                   "namespace": namespace,
                   "data": {key: data[key]}}
            self.send(msg)

        LOG.debug("Inserting new page")
        self.send({"type": "mycroft.gui.list.insert",
                   "namespace": namespace,
                   "position": 0,
                   "data": [{"url": p} for p in pages]
                   })
        # Make sure the local copy is updated
        self.loaded.insert(0, Namespace(namespace, pages))

    def __move_namespace(self, from_pos, to_pos):
        """ Move an existing namespace to a new position in the stack.

        Args:
            from_pos (int): Position in the stack to move from
            to_pos (int): Position to move to
        """
        LOG.debug("Activating existing namespace")
        # Seems like the namespace is moved to the top automatically when
        # a page change is done. Deactivating this for now.
        if self.explicit_move:
            LOG.debug("move {} to {}".format(from_pos, to_pos))
            self.send({"type": "mycroft.session.list.move",
                       "namespace": "mycroft.system.active_skills",
                       "from": from_pos, "to": to_pos,
                       "items_number": 1})
        # Move the local representation of the skill from current
        # position to position 0.
        self.loaded.insert(to_pos, self.loaded.pop(from_pos))

    def __switch_page(self, namespace, pages):
        """ Switch page to an already loaded page.

        Args:
            pages (list): pages (str) to switch to
            namespace (str):  skill namespace
        """
        try:
            num = self.loaded[0].pages.index(pages[0])
        except Exception as e:
            LOG.exception(repr(e))
            num = 0

        LOG.debug('Switching to already loaded page at '
                  'index {} in namespace {}'.format(num, namespace))
        self.send({"type": "mycroft.events.triggered",
                   "namespace": namespace,
                   "event_name": "page_gained_focus",
                   "data": {"number": num}})

    def show(self, namespace, page, index):
        """ Show a page and load it as needed.

        Args:
            page (str or list): page(s) to show
            namespace (str):  skill namespace
            index (int): ??? TODO: Unused in code ???

        TODO: - Update sync to match.
              - Separate into multiple functions/methods
        """

        LOG.debug("GUIConnection activating: " + namespace)
        pages = page if isinstance(page, list) else [page]

        # find namespace among loaded namespaces
        try:
            index = self.__find_namespace(namespace)
            if index is None:
                # This namespace doesn't exist, insert them first so they're
                # shown.
                self.__insert_new_namespace(namespace, pages)
                return
            else:  # Namespace exists
                if index > 0:
                    # Namespace is inactive, activate it by moving it to
                    # position 0
                    self.__move_namespace(index, 0)

                # Find if any new pages needs to be inserted
                new_pages = [p for p in pages if p not in self.loaded[0].pages]
                if new_pages:
                    self.__insert_pages(namespace, new_pages)
                else:
                    # No new pages, just switch
                    self.__switch_page(namespace, pages)
        except Exception as e:
            LOG.exception(repr(e))

    def remove_namespace(self, namespace):
        """ Remove namespace.

        Args:
            namespace (str): namespace to remove
        """
        index = self.__find_namespace(namespace)
        if index is None:
            return
        else:
            LOG.debug("Removing namespace {} at {}".format(namespace, index))
            self.send({"type": "mycroft.session.list.remove",
                       "namespace": "mycroft.system.active_skills",
                       "position": index,
                       "items_number": 1
                       })
            # Remove namespace from loaded namespaces
            self.loaded.pop(index)

    def remove_pages(self, namespace, pages):
        """ Remove the listed pages from the provided namespace.

        Args:
            namespace (str):    The namespace to modify
            pages (list):       List of page names (str) to delete
        """
        try:
            index = self.__find_namespace(namespace)
            if index is None:
                return
            else:
                # Remove any pages that doesn't exist in the namespace
                pages = [p for p in pages if p in self.loaded[index].pages]
                # Make sure to remove pages from the back
                indexes = [self.loaded[index].pages.index(p) for p in pages]
                indexes = sorted(indexes)
                indexes.reverse()
                for page_index in indexes:
                    self.__remove_page(namespace, page_index)
        except Exception as e:
            LOG.exception(repr(e))

    ######################################################################
    # GUI client socket
    #
    # The basic mechanism is:
    # 1) GUI client announces itself on the main messagebus
    # 2) Mycroft prepares a port for a socket connection to this GUI
    # 3) The port is announced over the messagebus
    # 4) The GUI connects on the socket
    # 5) Connection persists for graphical interaction indefinitely
    #
    # If the connection is lost, it must be renegotiated and restarted.
    def on_gui_client_connected(self, message):
        # GUI has announced presence
        LOG.info('GUI HAS ANNOUNCED!')
        port = self.config["gui_websocket"]["base_port"]
        LOG.debug("on_gui_client_connected")
        gui_id = message.data.get("gui_id")

        LOG.debug("Heard announcement from gui_id: {}".format(gui_id))

        # Announce connection, the GUI should connect on it soon
        self.bus.emit(Message("mycroft.gui.port",
                              {"port": port,
                               "gui_id": gui_id}))

    def register_gui_handlers(self):
        # TODO: Register handlers for standard (Mark 1) events
        # self.bus.on('enclosure.eyes.on', self.on)
        # self.bus.on('enclosure.eyes.off', self.off)
        # self.bus.on('enclosure.eyes.blink', self.blink)
        # self.bus.on('enclosure.eyes.narrow', self.narrow)
        # self.bus.on('enclosure.eyes.look', self.look)
        # self.bus.on('enclosure.eyes.color', self.color)
        # self.bus.on('enclosure.eyes.level', self.brightness)
        # self.bus.on('enclosure.eyes.volume', self.volume)
        # self.bus.on('enclosure.eyes.spin', self.spin)
        # self.bus.on('enclosure.eyes.timedspin', self.timed_spin)
        # self.bus.on('enclosure.eyes.reset', self.reset)
        # self.bus.on('enclosure.eyes.setpixel', self.set_pixel)
        # self.bus.on('enclosure.eyes.fill', self.fill)

        # self.bus.on('enclosure.mouth.reset', self.reset)
        # self.bus.on('enclosure.mouth.talk', self.talk)
        # self.bus.on('enclosure.mouth.think', self.think)
        # self.bus.on('enclosure.mouth.listen', self.listen)
        # self.bus.on('enclosure.mouth.smile', self.smile)
        # self.bus.on('enclosure.mouth.viseme', self.viseme)
        # self.bus.on('enclosure.mouth.text', self.text)
        # self.bus.on('enclosure.mouth.display', self.display)
        # self.bus.on('enclosure.mouth.display_image', self.display_image)
        # self.bus.on('enclosure.weather.display', self.display_weather)

        # self.bus.on('recognizer_loop:record_begin', self.mouth.listen)
        # self.bus.on('recognizer_loop:record_end', self.mouth.reset)
        # self.bus.on('recognizer_loop:audio_output_start', self.mouth.talk)
        # self.bus.on('recognizer_loop:audio_output_end', self.mouth.reset)
        pass

