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
from mycroft.util.log import LOG
from mycroft.util import resolve_resource_file
from time import sleep


class DisplayBackend:
    """
        Base class for all display backend implementations.
        Args:
            config: configuration dict for the instance
            bus: websocket object
    """

    def __init__(self, bus, config=None, name="dummy display"):
        self.name = name
        self.bus = bus
        self.config = config
        self.index = 0
        self._is_displaying = False
        self.pictures = []
        self.width = 1600
        self.height = 900
        self.fullscreen = False
        self._display_start_callback = None
        self.default_picture = resolve_resource_file("ui/neon_logo.png")

    @staticmethod
    def supported_uris():
        """
            Returns: list of supported uri types.
        """
        return ['file']  #, 'http', 'https']

    def handle_fullscreen(self, new_value, old_value):
        # display was told to change fullscreen status
        pass

    def handle_reset(self):
        # display was told to reset to default state
        # usually a logo
        if self.default_picture is not None:
            self.handle_display(self.default_picture)

    def handle_stop(self):
        # display was told to stop displaying
        self.handle_reset()

    def handle_close(self):
        # display was told to close window
        pass

    def handle_display(self, picture):
        # display was told to display picture
        pass

    def handle_clear(self):
        # display was told to clear
        # usually a black image
        pass

    def handle_height_change(self, new_value, old_value):
        # change display height in pixels
        pass

    def handle_width_change(self, new_value, old_value):
        # change display width in pixels
        pass

    def display(self):
        """
           Display self.index in Pictures List of paths
        """
        if len(self.pictures):
            pic = self.pictures[self.index]
            self.handle_display(pic)
        else:
            LOG.error("Nothing to display")

    def clear_pictures(self):
        self.pictures = []
        self.index = 0

    def add_pictures(self, picture_list):
        """
          add pics
        """
        self.pictures.extend(picture_list)

    def reset(self):
        """
            Reset Display.
        """
        self.index = 0
        self.pictures = []
        self.handle_reset()

    def clear(self):
        """
            Clear Display.
        """
        self.handle_clear()

    def next(self):
        """
            Skip to next pic in playlist.
        """
        self.index += 1
        if self.index > len(self.pictures):
            self.index = 0
        self.display()

    def previous(self):
        """
            Skip to previous pic in playlist.
        """
        self.index -= 1
        if self.index > 0:
            self.index = len(self.pictures)
        self.display()

    def lock(self):
        """
           Set Lock Flag so nothing else can display
        """
        pass

    def unlock(self):
        """
           Unset Lock Flag so nothing else can display
        """
        pass

    def change_index(self, index):
        """
           Change picture index
        """
        self.index = index
        self.display()

    def change_fullscreen(self, value=True):
        """
           toogle fullscreen
        """
        old = self.fullscreen
        self.fullscreen = value
        self.handle_fullscreen(value, old)

    def change_height(self, value=900):
        """
           change display height
        """
        old = self.height
        self.height = int(value)
        self.handle_height_change(int(value), old)

    def change_width(self, value=1600):
        """
           change display width
        """
        old = self.width
        self.width = int(value)
        self.handle_width_change(int(value), old)

    def stop(self):
        """
            Stop display.
        """
        self._is_displaying = False
        self.handle_stop()

    def close(self):
        self.stop()
        sleep(0.5)
        self.handle_close()

    def shutdown(self):
        """ Perform clean shutdown """
        self.stop()
        self.close()

    def set_display_start_callback(self, callback_func):
        """
            Register callback on display start, should be called as each
            picture in picture list is displayed
        """
        self._display_start_callback = callback_func

    def picture_info(self):
        ret = {}
        ret['artist'] = 'unknown'
        ret['path'] = None
        if len(self.pictures):
            ret['path'] = self.pictures[self.index]
        else:
            ret['path'] = self.default_picture
        ret["is_displaying"] = self._is_displaying
        return ret

