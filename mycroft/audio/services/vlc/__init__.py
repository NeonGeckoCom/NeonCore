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
import vlc

from mycroft.audio.services import AudioBackend
from mycroft.util.log import LOG


class VlcService(AudioBackend):
    def __init__(self, config, bus=None, name='vlc'):
        super(VlcService, self).__init__(config, bus)
        self.instance = vlc.Instance("--no-video")
        self.list_player = self.instance.media_list_player_new()
        self.player = self.instance.media_player_new()
        self.list_player.set_media_player(self.player)
        self.track_list = self.instance.media_list_new()
        self.list_player.set_media_list(self.track_list)
        self.vlc_events = self.player.event_manager()
        self.vlc_events.event_attach(vlc.EventType.MediaPlayerPlaying,
                                     self.track_start, 1)
        self.config = config
        self.bus = bus
        self.name = name
        self.normal_volume = None
        self.low_volume = self.config.get('low_volume', 30)

    def track_start(self, data, other):
        if self._track_start_callback:
            self._track_start_callback(self.track_info()['name'])

    def supported_uris(self):
        return ['file', 'http', 'https']

    def clear_list(self):
        # Create a new media list
        self.track_list = self.instance.media_list_new()
        # Set list as current track list
        self.list_player.set_media_list(self.track_list)

    def add_list(self, tracks):
        LOG.debug("Track list is " + str(tracks))
        for t in tracks:
            self.track_list.add_media(self.instance.media_new(t))

    def play(self, repeat=False):
        """ Play playlist using vlc. """
        LOG.debug('VLCService Play')
        if repeat:
            self.list_player.set_playback_mode(vlc.PlaybackMode.loop)
        else:
            self.list_player.set_playback_mode(vlc.PlaybackMode.default)

        self.list_player.play()

    def stop(self):
        """ Stop vlc playback. """
        LOG.info('VLCService Stop')
        if self.player.is_playing():
            # Restore volume if lowered
            self.restore_volume()
            self.clear_list()
            self.list_player.stop()
            return True
        else:
            return False

    def pause(self):
        """ Pause vlc playback. """
        self.player.set_pause(1)

    def resume(self):
        """ Resume paused playback. """
        self.player.set_pause(0)

    def next(self):
        """ Skip to next track in playlist. """
        self.list_player.next()

    def previous(self):
        """ Skip to previous track in playlist. """
        self.list_player.previous()

    def lower_volume(self):
        """ Lower volume (will be called when mycroft is listening
        or speaking.
        """
        # Lower volume if playing, volume isn't already lowered
        # and ducking is enabled
        if (self.normal_volume is None and self.player.is_playing() and
                self.config.get('duck', False)):
            self.normal_volume = self.player.audio_get_volume()
            self.player.audio_set_volume(self.low_volume)

    def restore_volume(self):
        """ Restore volume to previous level. """
        # if vlc has been lowered restore the volume
        if self.normal_volume:
            self.player.audio_set_volume(self.normal_volume)
            self.normal_volume = None

    def track_info(self):
        """ Extract info of current track. """
        ret = {}
        meta = vlc.Meta
        t = self.player.get_media()
        ret['album'] = t.get_meta(meta.Album)
        ret['artists'] = [t.get_meta(meta.Artist)]
        ret['name'] = t.get_meta(meta.Title)
        return ret

    def seek_forward(self, seconds=1):
        """
        skip X seconds

          Args:
                seconds (int): number of seconds to seek, if negative rewind
        """
        seconds = seconds * 1000
        new_time = self.player.get_time() + seconds
        duration = self.player.get_length()
        if new_time > duration:
            new_time = duration
        self.player.set_time(new_time)

    def seek_backward(self, seconds=1):
        """
        rewind X seconds

          Args:
                seconds (int): number of seconds to seek, if negative rewind
        """
        seconds = seconds * 1000
        new_time = self.player.get_time() - seconds
        if new_time < 0:
            new_time = 0
        self.player.set_time(new_time)


def load_service(base_config, bus):
    backends = base_config.get('backends', [])
    services = [(b, backends[b]) for b in backends
                if backends[b]['type'] == 'vlc' and
                backends[b].get('active', True)]
    instances = [VlcService(s[1], bus, s[0]) for s in services]
    return instances
