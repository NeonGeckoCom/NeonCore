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
from abc import ABCMeta, abstractmethod


class AudioBackend(metaclass=ABCMeta):
    """
        Base class for all audio backend implementations.

        Args:
            config: configuration dict for the instance
            bus:    Mycroft messagebus emitter
    """

    def __init__(self, config, bus):
        self._track_start_callback = None
        self.supports_mime_hints = False

    @abstractmethod
    def supported_uris(self):
        """
            Returns: list of supported uri types.
        """
        pass

    @abstractmethod
    def clear_list(self):
        """
            Clear playlist
        """
        pass

    @abstractmethod
    def add_list(self, tracks):
        """
            Add tracks to backend's playlist.

            Args:
                tracks: list of tracks.
        """
        pass

    @abstractmethod
    def play(self, repeat=False):
        """
            Start playback.

            Args:
                repeat: Repeat playlist, defaults to False
        """
        pass

    @abstractmethod
    def stop(self):
        """
            Stop playback.

            Returns: (bool) True if playback was stopped, otherwise False
        """
        pass

    def set_track_start_callback(self, callback_func):
        """
            Register callback on track start, should be called as each track
            in a playlist is started.
        """
        self._track_start_callback = callback_func

    def pause(self):
        """
            Pause playback.
        """
        pass

    def resume(self):
        """
            Resume paused playback.
        """
        pass

    def next(self):
        """
            Skip to next track in playlist.
        """
        pass

    def previous(self):
        """
            Skip to previous track in playlist.
        """
        pass

    def lower_volume(self):
        """
            Lower volume.
        """
        pass

    def restore_volume(self):
        """
            Restore normal volume.
        """
        pass

    def seek_forward(self, seconds=1):
        """
            Skip X seconds

            Args:
                seconds (int): number of seconds to seek, if negative rewind
        """
        pass

    def seek_backward(self, seconds=1):
        """
            Rewind X seconds

            Args:
                seconds (int): number of seconds to seek, if negative rewind
        """
        pass

    def track_info(self):
        """
            Fetch info about current playing track.

            Returns:
                Dict with track info.
        """
        ret = {}
        ret['artist'] = ''
        ret['album'] = ''
        return ret

    def shutdown(self):
        """ Perform clean shutdown """
        self.stop()


class RemoteAudioBackend(AudioBackend):
    """ Base class for remote audio backends.

        These may be things like Chromecasts, mopidy servers, etc.
    """
    pass
