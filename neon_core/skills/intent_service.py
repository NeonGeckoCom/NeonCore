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
import wave

from neon_core.configuration import Configuration
from neon_core.language import get_lang_config
from neon_core.processing_modules.text import TextParsersService

from copy import copy
from mycroft_bus_client import Message
from neon_utils.message_utils import get_message_user
from neon_utils.metrics_utils import Stopwatch
from neon_utils.log_utils import LOG
from neon_utils.configuration_utils import get_neon_device_type
from ovos_utils.json_helper import merge_dict

from mycroft.configuration.locale import set_default_lang
from mycroft.skills.intent_service import IntentService


try:
    if get_neon_device_type() == "server":
        from neon_transcripts_controller.transcript_db_manager import TranscriptDBManager as Transcribe
    else:
        from neon_transcripts_controller.transcript_file_manager import TranscriptFileManager as Transcribe
except ImportError:
    Transcribe = None


class NeonIntentService(IntentService):
    def __init__(self, bus):
        super().__init__(bus)
        self.config = Configuration.get().get('context', {})
        self.language_config = get_lang_config()

        set_default_lang(self.language_config["internal"])

        self._setup_converse_handlers()

        self.parser_service = TextParsersService(self.bus)
        self.parser_service.start()

        if Transcribe:
            self.transcript_service = Transcribe()
        else:
            self.transcript_service = None

    def _setup_converse_handlers(self):
        self.bus.on('skill.converse.error', self.handle_converse_error)
        self.bus.on('skill.converse.activate_skill',
                    self.handle_activate_skill)
        self.bus.on('skill.converse.deactivate_skill',
                    self.handle_deactivate_skill)
        # backwards compat
        self.bus.on('active_skill_request',
                    self.handle_activate_skill)

    def handle_activate_skill(self, message):
        self.add_active_skill(message.data['skill_id'])

    def handle_deactivate_skill(self, message):
        self.remove_active_skill(message.data['skill_id'])

    def reset_converse(self, message):
        """Let skills know there was a problem with speech recognition"""
        lang = message.data.get('lang', "en-us")
        set_default_lang(lang)
        for skill in copy(self.active_skills):
            self.do_converse([], skill[0], lang, message)

    def _save_utterance_transcription(self, message):
        """
        Record a user utterance with the transcript_service. Adds the `audio_file` context to message context.

        Args:
            message (Message): message associated with user input
        """
        if self.transcript_service:
            # TODO: Read transcription preferences here DM
            audio = message.context.get("raw_audio")  # This is a tempfile
            if audio:
                audio = wave.open(audio, 'r')
                audio = audio.readframes(audio.getnframes())
            timestamp = message.context["timing"].get("transcribed", time.time())
            audio_file = self.transcript_service.write_transcript(get_message_user(message),
                                                                  message.data.get('utterances', [''])[0],
                                                                  timestamp, audio)
            message.context["audio_file"] = audio_file

    def _get_parsers_service_context(self, message, lang):
        """
        Pipe utterance thorough text parsers to get more metadata.
        Utterances may be modified by any parser and context overwritten
        """
        utterances = message.data.get('utterances', [])
        for parser in self.parser_service.modules:
            # mutate utterances and retrieve extra data
            utterances, data = self.parser_service.parse(parser, utterances, lang)
            # update message context with extra data
            message.context = merge_dict(message.context, data)
        message.data["utterances"] = utterances

    def handle_utterance(self, message):
        """
        Handler for 'recognizer_loop:utterance'
        Main entrypoint for handling user utterances with skills module

        Arguments:
            message (Message): message associated with user request
        """

        # Notify emitting module that skills is handling this utterance
        self.bus.emit(message.response())

        try:
            # Get language of the utterance
            lang = message.data.get('lang', self.language_config["user"])

            # Add or init timing data
            message.context = message.context or {}
            if not message.context.get("timing"):
                LOG.debug("No timing data available at intent service")
                message.context["timing"] = {}
            message.context["timing"]["handle_utterance"] = time.time()

            # Make sure there is a `transcribed` timestamp (should have been added in speech module)
            if not message.context["timing"]["transcribed"]:
                message.context["timing"]["transcribed"] = message.context["timing"]["handle_utterance"]

            stopwatch = Stopwatch()

            # TODO: Consider saving transcriptions after text parsers cleanup utterance. This should retain the raw
            #       transcription, in addition to the one modified by the parsers DM
            # Write out text and audio transcripts if service is available
            with stopwatch:
                self._save_utterance_transcription(message)
            message.context["timing"]["save_transcript"] = stopwatch.time

            # Get text parser context
            with stopwatch:
                self._get_parsers_service_context(message, lang)
            message.context["timing"]["text_parsers"] = stopwatch.time

            # Catch empty utterances after parser service
            if len([u for u in message.data["utterances"] if u.strip()]) == 0:
                LOG.debug("Received empty utterance!!")
                reply = message.reply('intent_aborted',
                                      {'utterances': message.data.get('utterances', []),
                                       'lang': lang})
                self.bus.emit(reply)
                return

            # now pass our modified message to mycroft-lib
            message.data["lang"] = lang
            # TODO: Consider how to implement 'and' parsing and converse here DM
            super().handle_utterance(message)
        except Exception as err:
            LOG.exception(err)

    def _converse(self, utterances, lang, message):
        """
        Wraps the actual converse method to add timing data

        Args:
            utterances (list):  list of utterances
            lang (string):      4 letter ISO language code
            message (Message):  message to use to generate reply

        Returns:
            IntentMatch if handled otherwise None.
        """
        stopwatch = Stopwatch()
        with stopwatch:
            match = super()._converse(utterances, lang, message)
        message.context["timing"]["check_converse"] = stopwatch.time
        if match:
            LOG.info(f"converse handling response: {match.skill_id}")
        return match

