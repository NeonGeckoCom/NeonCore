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
import time
from os.path import abspath

from mycroft.messagebus.message import Message


def ensure_uri(s):
    """
        Interprete paths as file:// uri's

        Args:
            s: string to be checked

        Returns:
            if s is uri, s is returned otherwise file:// is prepended
    """
    if isinstance(s, str):
        if '://' not in s:
            return 'file://' + abspath(s)
        else:
            return s
    elif isinstance(s, (tuple, list)):
        if '://' not in s[0]:
            return 'file://' + abspath(s[0]), s[1]
        else:
            return s
    else:
        raise ValueError('Invalid track')


class AudioService:
    """
        AudioService class for interacting with the audio subsystem

        Arguments:
            bus: Mycroft messagebus connection
    """

    def __init__(self, bus):
        self.bus = bus
        self.bus.on('mycroft.audio.service.track_info_reply',
                    self._track_info)
        self.info = None

    def _track_info(self, message=None):
        """
            Handler for catching returning track info
        """
        self.info = message.data

    def queue(self, tracks=None):
        """ Queue up a track to playing playlist.

            Args:
                tracks: track uri or list of track uri's
        """
        tracks = tracks or []
        if isinstance(tracks, str):
            tracks = [tracks]
        elif not isinstance(tracks, list):
            raise ValueError
        tracks = [ensure_uri(t) for t in tracks]
        self.bus.emit(Message('mycroft.audio.service.queue',
                              data={'tracks': tracks}))

    def play(self, tracks=None, utterance=None, repeat=None):
        """ Start playback.

            Args:
                tracks: track uri or list of track uri's
                        Each track can be added as a tuple with (uri, mime)
                        to give a hint of the mime type to the system
                utterance: forward utterance for further processing by the
                           audio service.
                repeat: if the playback should be looped
        """
        repeat = repeat or False
        tracks = tracks or []
        utterance = utterance or ''
        if isinstance(tracks, (str, tuple)):
            tracks = [tracks]
        elif not isinstance(tracks, list):
            raise ValueError
        tracks = [ensure_uri(t) for t in tracks]
        self.bus.emit(Message('mycroft.audio.service.play',
                              data={'tracks': tracks,
                                    'utterance': utterance,
                                    'repeat': repeat}))

    def stop(self):
        """ Stop the track. """
        self.bus.emit(Message('mycroft.audio.service.stop'))

    def next(self):
        """ Change to next track. """
        self.bus.emit(Message('mycroft.audio.service.next'))

    def prev(self):
        """ Change to previous track. """
        self.bus.emit(Message('mycroft.audio.service.prev'))

    def pause(self):
        """ Pause playback. """
        self.bus.emit(Message('mycroft.audio.service.pause'))

    def resume(self):
        """ Resume paused playback. """
        self.bus.emit(Message('mycroft.audio.service.resume'))

    def seek(self, seconds=1):
        """
        seek X seconds

         Args:
                seconds (int): number of seconds to seek, if negative rewind
        """
        if seconds < 0:
            self.seek_backward(abs(seconds))
        else:
            self.seek_forward(seconds)

    def seek_forward(self, seconds=1):
        """
        skip ahead X seconds

         Args:
                seconds (int): number of seconds to skip
        """
        self.bus.emit(Message('mycroft.audio.service.seek_forward',
                              {"seconds": seconds}))

    def seek_backward(self, seconds=1):
        """
        rewind X seconds

         Args:
                seconds (int): number of seconds to rewind
        """
        self.bus.emit(Message('mycroft.audio.service.seek_backward',
                              {"seconds": seconds}))

    def track_info(self):
        """ Request information of current playing track.

            Returns:
                Dict with track info.
        """
        self.info = None
        self.bus.emit(Message('mycroft.audio.service.track_info'))
        wait = 5.0
        while self.info is None and wait >= 0:
            time.sleep(0.1)
            wait -= 0.1

        return self.info or {}

    def available_backends(self):
        """ Return available audio backends.

        Returns:
            dict with backend names as keys
        """
        msg = Message('mycroft.audio.service.list_backends')
        response = self.bus.wait_for_response(msg)
        return response.data if response else {}

    @property
    def is_playing(self):
        return self.track_info() != {}
