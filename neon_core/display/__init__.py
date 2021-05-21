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
import imp
import sys
from os import listdir
from os.path import abspath, dirname, basename, isdir, join
from threading import Lock

from neon_core.configuration import Configuration
from mycroft.messagebus.message import Message
from mycroft.util.log import LOG


MAINMODULE = '__init__'
sys.path.append(abspath(dirname(__file__)))


def create_service_descriptor(service_folder):
    """Prepares a descriptor that can be used together with imp.

        Args:
            service_folder: folder that shall be imported.

        Returns:
            Dict with import information
    """
    info = imp.find_module(MAINMODULE, [service_folder])
    return {"name": basename(service_folder), "info": info}


def get_services(services_folder):
    """
        Load and initialize services from all subfolders.

        Args:
            services_folder: base folder to look for services in.

        Returns:
            Sorted list of display services.
    """
    LOG.info("Loading services from " + services_folder)
    services = []
    possible_services = listdir(services_folder)
    for i in possible_services:
        location = join(services_folder, i)
        if (isdir(location) and
                not MAINMODULE + ".py" in listdir(location)):
            for j in listdir(location):
                name = join(location, j)
                if (not isdir(name) or
                        not MAINMODULE + ".py" in listdir(name)):
                    continue
                try:
                    services.append(create_service_descriptor(name))
                except Exception:
                    LOG.error('Failed to create service from ' + name,
                              exc_info=True)
        if (not isdir(location) or
                not MAINMODULE + ".py" in listdir(location)):
            continue
        try:
            services.append(create_service_descriptor(location))
        except Exception:
            LOG.error('Failed to create service from ' + location,
                      exc_info=True)
    return sorted(services, key=lambda p: p.get('name'))


def load_services(config, bus, path=None):
    """
        Search though the service directory and load any services.

        Args:
            config: configuration dict for the display backends.
            bus: Mycroft messagebus

        Returns:
            List of started services.
    """
    if path is None:
        path = dirname(abspath(__file__)) + '/services/'
    service_directories = get_services(path)
    services = []
    for descriptor in service_directories:
        LOG.info('Loading ' + descriptor['name'])
        try:
            service_module = imp.load_module(descriptor["name"] + MAINMODULE,
                                             *descriptor["info"])
        except Exception as e:
            LOG.error('Failed to import module ' + descriptor['name'] + '\n' +
                      repr(e))
            continue

        if hasattr(service_module, 'load_service'):
            try:
                s = service_module.load_service(config, bus)
                services += s
            except Exception as e:
                LOG.error('Failed to load service. ' + repr(e))
    return services


class DisplayService:
    """ Display Service class.
        Handles display of images and selecting proper backend for
        the image to be displayed.
    """

    def __init__(self, bus):
        """
            Args:
                bus: Mycroft messagebus
        """
        self.bus = bus
        self.config = Configuration.get().get("Display")
        self.service_lock = Lock()

        self.default = None
        self.services = []
        self.current = None

        bus.once('open', self.load_services_callback)

    def load_services_callback(self):
        """
            Main callback function for loading services. Sets up the globals
            service and default and registers the event handlers for the
            subsystem.
        """

        self.services = load_services(self.config, self.bus)

        # Register end of picture callback
        for s in self.services:
            s.set_display_start_callback(self.display_start)

        # Find default backend
        default_name = self.config.get('default-backend', '')
        LOG.info('Finding default backend...')
        for s in self.services:
            if s.name == default_name:
                self.default = s
                LOG.info('Found ' + self.default.name)
                break
        else:
            self.default = None
            LOG.info('no default found')

        # Setup event handlers
        self.bus.on('mycroft.display.service.display', self._display)
        self.bus.on('mycroft.display.service.queue', self._queue)
        self.bus.on('mycroft.display.service.stop', self._stop)
        self.bus.on('mycroft.display.service.clear', self._clear)
        self.bus.on('mycroft.display.service.close', self._close)
        self.bus.on('mycroft.display.service.reset', self._reset)
        self.bus.on('mycroft.display.service.next', self._next)
        self.bus.on('mycroft.display.service.prev', self._prev)
        self.bus.on('mycroft.display.service.height', self._set_height)
        self.bus.on('mycroft.display.service.width', self._set_width)
        self.bus.on('mycroft.display.service.fullscreen', self._set_fullscreen)
        self.bus.on('mycroft.display.service.picture_info', self._picture_info)
        self.bus.on('mycroft.display.service.list_backends', self._list_backends)

    def get_prefered(self, utterance=""):
        # Find if the user wants to use a specific backend
        for s in self.services:
            if s.name in utterance:
                prefered_service = s
                LOG.debug(s.name + ' would be prefered')
                break
        else:
            prefered_service = None
        return prefered_service

    def display_start(self, picture):
        """
            Callback method called from the services to indicate start of
            playback of a picture.
        """
        self.bus.emit(Message('mycroft.display.displaying_picture',
                              data={'picture': picture}))

    def _set_fullscreen(self, message=None):
        value = message.data["value"]
        if self.current:
            self.current.change_fullscreen(value)

    def _set_height(self, message=None):
        value = message.data["value"]
        if self.current:
            self.current.set_height(value)

    def _set_width(self, message=None):
        value = message.data["value"]
        if self.current:
            self.current.set_width(value)

    def _close(self, message=None):
        if self.current:
            self.current.close()

    def _clear(self, message=None):
        if self.current:
            self.current.clear()

    def _reset(self, message=None):
        if self.current:
            self.current.reset()
        else:
            LOG.error("No active display to reset")

    def _next(self, message=None):
        if self.current:
            self.current.next()

    def _prev(self, message=None):
        if self.current:
            self.current.previous()

    def _stop(self, message=None):
        LOG.debug('stopping display services')
        with self.service_lock:
            if self.current:
                name = self.current.name
                if self.current.stop():
                    self.bus.emit(Message("mycroft.stop.handled",
                                          {"by": "display:" + name}))

                self.current = None

    def _queue(self, message):
        if self.current:
            pictures = message.data['pictures']
            self.current.add_pictures(pictures)
        else:
            self._display(message)

    def _display(self, message):
        """
            Handler for mycroft.display.service.play. Starts display of a
            picturelist. Also  determines if the user requested a special
            service.

            Args:
                message: message bus message, not used but required
        """
        try:
            pictures = message.data['pictures']
            prefered_service = self.get_prefered(message.data.get("utterance", ""))

            if isinstance(pictures[0], str):
                uri_type = pictures[0].split(':')[0]
            else:
                uri_type = pictures[0][0].split(':')[0]

            # check if user requested a particular service
            if prefered_service and uri_type in prefered_service.supported_uris():
                selected_service = prefered_service
            # check if default supports the uri
            elif self.default and uri_type in self.default.supported_uris():
                LOG.debug("Using default backend ({})".format(self.default.name))
                selected_service = self.default
            else:  # Check if any other service can play the media
                LOG.debug("Searching the services")
                for s in self.services:
                    if uri_type in s.supported_uris():
                        LOG.debug("Service {} supports URI {}".format(s, uri_type))
                        selected_service = s
                        break
                else:
                    LOG.info('No service found for uri_type: ' + uri_type)
                    return
            selected_service.clear_pictures()
            selected_service.add_pictures(pictures)
            selected_service.display()
            self.current = selected_service
        except Exception as e:
            LOG.exception(e)

    def _picture_info(self, message):
        """
            Returns picture info on the message bus.

            Args:
                message: message bus message, not used but required
        """
        if self.current:
            picture_info = self.current.picture_info()
        else:
            picture_info = {}
        self.bus.emit(Message('mycroft.display.service.picture_info_reply',
                              data=picture_info))

    def _list_backends(self, message):
        """ Return a dict of available backends. """
        data = {}
        for s in self.services:
            info = {
                'supported_uris': s.supported_uris(),
                'default': s == self.default
            }
            data[s.name] = info
        self.bus.emit(message.response(data))

    def shutdown(self):
        for s in self.services:
            try:
                LOG.info('shutting down ' + s.name)
                s.shutdown()
            except Exception as e:
                LOG.error('shutdown of ' + s.name + ' failed: ' + repr(e))

        # remove listeners
        self.bus.remove('mycroft.display.service.display', self._display)
        self.bus.remove('mycroft.display.service.queue', self._queue)
        self.bus.remove('mycroft.display.service.stop', self._stop)
        self.bus.remove('mycroft.display.service.clear', self._clear)
        self.bus.remove('mycroft.display.service.close', self._close)
        self.bus.remove('mycroft.display.service.reset', self._reset)
        self.bus.remove('mycroft.display.service.next', self._next)
        self.bus.remove('mycroft.display.service.prev', self._prev)
        self.bus.remove('mycroft.display.service.height', self._set_height)
        self.bus.remove('mycroft.display.service.width', self._set_width)
        self.bus.remove('mycroft.display.service.fullscreen', self._set_fullscreen)
        self.bus.remove('mycroft.display.service.picture_info', self._picture_info)
        self.bus.remove('mycroft.display.service.list_backends', self._list_backends)
