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
import re
from enum import Enum
from abc import ABC, abstractmethod
from mycroft.messagebus.message import Message
from .mycroft_skill import MycroftSkill
from .audioservice import AudioService


class CPSMatchLevel(Enum):
    EXACT = 1
    MULTI_KEY = 2
    TITLE = 3
    ARTIST = 4
    CATEGORY = 5
    GENERIC = 6


class CommonPlaySkill(MycroftSkill, ABC):
    """ To integrate with the common play infrastructure of Mycroft
    skills should use this base class and override the two methods
    `CPS_match_query_phrase` (for checking if the skill can play the
    utterance) and `CPS_start` for launching the media.

    The class makes the skill available to queries from the
    mycroft-playback-control skill and no special vocab for starting playback
    is needed.
    """
    def __init__(self, name=None, bus=None):
        super().__init__(name, bus)
        self.audioservice = None
        self.play_service_string = None

        # "MusicServiceSkill" -> "Music Service"
        spoken = name or self.__class__.__name__
        self.spoken_name = re.sub(r"([a-z])([A-Z])", r"\g<1> \g<2>",
                                  spoken.replace("Skill", ""))
        # NOTE: Derived skills will likely want to override self.spoken_name
        # with a translatable name in their initialize() method.

    def bind(self, bus):
        """ Overrides the normal bind method.
        Adds handlers for play:query and play:start messages allowing
        interaction with the playback control skill.

        This is called automatically during setup, and
        need not otherwise be used.
        """
        if bus:
            super().bind(bus)
            self.audioservice = AudioService(self.bus)
            self.add_event('play:query', self.__handle_play_query)
            self.add_event('play:start', self.__handle_play_start)

    def __handle_play_query(self, message):
        search_phrase = message.data["phrase"]

        # First, notify the requestor that we are attempting to handle
        # (this extends a timeout while this skill looks for a match)
        self.bus.emit(message.response({"phrase": search_phrase,
                                        "skill_id": self.skill_id,
                                        "searching": True}))

        # Now invoke the CPS handler to let the skill perform its search
        result = self.CPS_match_query_phrase(search_phrase)

        if result:
            match = result[0]
            level = result[1]
            callback = result[2] if len(result) > 2 else None
            confidence = self.__calc_confidence(match, search_phrase, level)
            self.bus.emit(message.response({"phrase": search_phrase,
                                            "skill_id": self.skill_id,
                                            "callback_data": callback,
                                            "service_name": self.spoken_name,
                                            "conf": confidence}))
        else:
            # Signal we are done (can't handle it)
            self.bus.emit(message.response({"phrase": search_phrase,
                                            "skill_id": self.skill_id,
                                            "searching": False}))

    def __calc_confidence(self, match, phrase, level):
        # "play pandora"
        # "play pandora is my girlfriend"
        # "play tom waits on pandora"

        # Assume the more of the words that get consumed, the better the match
        consumed_pct = len(match.split()) / len(phrase.split())
        if consumed_pct > 1.0:
            consumed_pct = 1.0 / consumed_pct  # deal with over/under-matching

        # We'll use this to modify the level, but don't want it to allow a
        # match to jump to the next match level.  So bonus is 0 - 0.05 (1/20)
        bonus = consumed_pct / 20.0

        if level == CPSMatchLevel.EXACT:
            return 1.0
        elif level == CPSMatchLevel.MULTI_KEY:
            return 0.9 + bonus
        elif level == CPSMatchLevel.TITLE:
            return 0.8 + bonus
        elif level == CPSMatchLevel.ARTIST:
            return 0.7 + bonus
        elif level == CPSMatchLevel.CATEGORY:
            return 0.6 + bonus
        elif level == CPSMatchLevel.GENERIC:
            return 0.5 + bonus
        else:
            return 0.0  # should never happen

    def __handle_play_start(self, message):
        if message.data["skill_id"] != self.skill_id:
            # Not for this skill!
            return
        phrase = message.data["phrase"]
        data = message.data.get("callback_data")

        # Stop any currently playing audio
        if self.audioservice.is_playing:
            self.audioservice.stop()
        self.bus.emit(Message("mycroft.stop"))

        # Save for CPS_play() later, e.g. if phrase includes modifiers like
        # "... on the chromecast"
        self.play_service_string = phrase

        # Invoke derived class to provide playback data
        self.CPS_start(phrase, data)

    def CPS_play(self, *args, **kwargs):
        """
        Begin playback of a media file or stream

        Normally this method will be invoked with somthing like:
           self.CPS_play(url)
        Advanced use can also include keyword arguments, such as:
           self.CPS_play(url, repeat=True)

        Args:
            same as the Audioservice.play method
        """
        # Inject the user's utterance in case the audio backend wants to
        # interpret it.  E.g. "play some rock at full volume on the stereo"
        if 'utterance' not in kwargs:
            kwargs['utterance'] = self.play_service_string
        self.audioservice.play(*args, **kwargs)

    def stop(self):
        if self.audioservice.is_playing:
            self.audioservice.stop()
            return True
        else:
            return False

    ######################################################################
    # Abstract methods
    # All of the following must be implemented by a skill that wants to
    # act as a CommonPlay Skill
    @abstractmethod
    def CPS_match_query_phrase(self, phrase):
        """
        Analyze phrase to see if it is a play-able phrase with this
        skill.

        Args:
            phrase (str): User phrase uttered after "Play", e.g. "some music"

        Returns:
            (match, CPSMatchLevel[, callback_data]) or None: Tuple containing
                 a string with the appropriate matching phrase, the PlayMatch
                 type, and optionally data to return in the callback if the
                 match is selected.
        """
        # Derived classes must implement this, e.g.
        #
        # if phrase in ["Zoosh"]:
        #     return ("Zoosh", CPSMatchLevel.Generic, {"hint": "music"})
        # or:
        # zoosh_song = find_zoosh(phrase)
        # if zoosh_song and "Zoosh" in phrase:
        #     # "play Happy Birthday in Zoosh"
        #     return ("Zoosh", CPSMatchLevel.MULTI_KEY, {"song": zoosh_song})
        # elif zoosh_song:
        #     # "play Happy Birthday"
        #     return ("Zoosh", CPSMatchLevel.TITLE, {"song": zoosh_song})
        # elif "Zoosh" in phrase
        #     # "play Zoosh"
        #     return ("Zoosh", CPSMatchLevel.GENERIC, {"cmd": "random"})
        return None

    @abstractmethod
    def CPS_start(self, phrase, data):
        """
        Begin playing whatever is specified in 'phrase'

        Args:
            phrase (str): User phrase uttered after "Play", e.g. "some music"
            data (dict): Callback data specified in match_query_phrase()
        """
        # Derived classes must implement this, e.g.
        # self.CPS_play("http://zoosh.com/stream_music")
        pass
