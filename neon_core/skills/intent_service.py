# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
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

from mycroft.skills.intent_services import ConverseService

from neon_core.configuration import Configuration
from neon_core.language import get_lang_config
from neon_core.processing_modules.text import TextParsersService

from mycroft_bus_client import Message
from neon_utils.message_utils import get_message_user
from neon_utils.metrics_utils import Stopwatch
from neon_utils.log_utils import LOG
from neon_utils.user_utils import apply_local_user_profile_updates
from neon_utils.configuration_utils import get_neon_user_config
from ovos_utils.json_helper import merge_dict
from lingua_franca.parse import get_full_lang_code

from mycroft.configuration.locale import set_default_lang
from mycroft.skills.intent_service import IntentService


# try:
#     if get_neon_device_type() == "server":
#         from neon_transcripts_controller.transcript_db_manager import\
#             TranscriptDBManager as Transcribe
#     else:
#         from neon_transcripts_controller.transcript_file_manager import\
#             TranscriptFileManager as Transcribe
# except ImportError:
Transcribe = None


class NeonIntentService(IntentService):
    def __init__(self, bus):
        super().__init__(bus)
        self.converse = NeonConverseService(bus)
        self.config = Configuration.get().get('context', {})
        self.language_config = get_lang_config()

        # Initialize default user to inject into incoming messages
        self._default_user = get_neon_user_config()
        self._default_user['user']['username'] = "local"

        set_default_lang(self.language_config["internal"])

        # self._setup_converse_handlers()

        self.parser_service = TextParsersService(self.bus)
        self.parser_service.start()

        self.transcript_service = None
        if Transcribe:
            try:
                self.transcript_service = Transcribe()
            except Exception as e:
                LOG.exception(e)

        self.bus.on("neon.profile_update", self.handle_profile_update)

    def handle_profile_update(self, message):
        updated_profile = message.data.get("profile")
        if updated_profile["user"]["username"] == \
                self._default_user["user"]["username"]:
            apply_local_user_profile_updates(updated_profile,
                                             self._default_user)

    def shutdown(self):
        self.parser_service.shutdown()

    def _save_utterance_transcription(self, message):
        """
        Record a user utterance with the transcript_service.
        Adds the `audio_file` context to message context.

        Args:
            message (Message): message associated with user input
        """
        if self.transcript_service:
            # TODO: Read transcription preferences here DM
            audio = message.context.get("raw_audio")  # This is a tempfile
            if audio:
                audio = wave.open(audio, 'r')
                audio = audio.readframes(audio.getnframes())
            timestamp = message.context["timing"].get("transcribed",
                                                      time.time())
            audio_file = self.transcript_service.write_transcript(
                get_message_user(message),
                message.data.get('utterances', [''])[0], timestamp, audio)
            message.context["audio_file"] = audio_file

    def _get_parsers_service_context(self, message: Message):
        """
        Pipe utterance thorough text parsers to get more metadata.
        Utterances may be modified by any parser and context overwritten
        :param message: Message to parse
        """
        utterances = message.data.get('utterances', [])
        lang = message.data.get('lang')
        for parser in self.parser_service.modules:
            # mutate utterances and retrieve extra data
            utterances, data = self.parser_service.parse(parser, utterances,
                                                         lang)
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
            lang = get_full_lang_code(
                message.data.get('lang') or self.language_config["user"])
            message.data["lang"] = lang

            # Add or init timing data
            message.context = message.context or {}
            if not message.context.get("timing"):
                LOG.debug("No timing data available at intent service")
                message.context["timing"] = {}
            message.context["timing"]["handle_utterance"] = time.time()

            # Ensure user profile data is present
            if "user_profiles" not in message.context:
                message.context["user_profiles"] = [self._default_user.content]
                message.context["username"] = \
                    self._default_user.content["user"]["username"]

            # Make sure there is a `transcribed` timestamp
            if not message.context["timing"].get("transcribed"):
                message.context["timing"]["transcribed"] = \
                    message.context["timing"]["handle_utterance"]

            stopwatch = Stopwatch()

            # TODO: Consider saving transcriptions after text parsers cleanup
            #  utterance. This should retain the raw transcription, in addition
            #  to the one modified by the parsers DM
            # Write out text and audio transcripts if service is available
            with stopwatch:
                self._save_utterance_transcription(message)
            message.context["timing"]["save_transcript"] = stopwatch.time

            # Get text parser context
            with stopwatch:
                self._get_parsers_service_context(message)
            message.context["timing"]["text_parsers"] = stopwatch.time

            # Catch empty utterances after parser service
            if len([u for u in message.data.get("utterances", [])
                    if u.strip()]) == 0:
                LOG.debug("Received empty utterance!!")
                reply = \
                    message.reply('intent_aborted',
                                  {'utterances': message.data.get('utterances',
                                                                  []),
                                   'lang': lang})
                self.bus.emit(reply)
                return

            # TODO: Try the original lang and fallback to translation
            # If translated, make sure message.data['lang'] is updated
            if message.context.get("translation_data") and \
                    message.context.get("translation_data")[0].get(
                        "was_translated"):
                message.data["lang"] = self.language_config["internal"]
            # now pass our modified message to Mycroft
            # TODO: Consider how to implement 'and' parsing and converse DM
            super().handle_utterance(message)
        except Exception as err:
            LOG.exception(err)


class NeonConverseService(ConverseService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _collect_converse_skills(self):
        # TODO: Patching bug in ovos-core 0.0.3
        return self.get_active_skills()
