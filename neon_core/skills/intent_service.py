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
from threading import Event
from typing import List

from ovos_bus_client.util import get_message_lang
from ovos_utils import flatten_list

from neon_transformers.text_transformers import UtteranceTransformersService
from ovos_bus_client import Message, MessageBusClient, SessionManager, UtteranceState
from neon_utils.message_utils import get_message_user, dig_for_message
from neon_utils.metrics_utils import Stopwatch
from neon_utils.user_utils import apply_local_user_profile_updates
from neon_utils.configuration_utils import get_neon_user_config
from lingua_franca.parse import get_full_lang_code
from ovos_config.locale import set_default_lang, setup_locale
from ovos_utils.log import LOG
from neon_core.configuration import Configuration
from neon_core.language import get_lang_config

from ovos_core.intent_services import IntentService, ConverseService

try:
    from neon_utterance_translator_plugin import UtteranceTranslator
except ImportError:
    UtteranceTranslator = None
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
    def __init__(self, bus: MessageBusClient):
        super().__init__(bus)
        self.converse = NeonConverseService(bus)
        self.config = Configuration()
        self.language_config = get_lang_config()
        LOG.debug(f"Languages Adapt={self.adapt_service.engines.keys()}|"
                  f"Padatious={self.padatious_service.containers.keys()}")

        # Initialize default user to inject into incoming messages
        try:
            self._default_user = get_neon_user_config()
        except PermissionError:
            LOG.warning("Unable to get writable config path; fallback to /tmp")
            self._default_user = get_neon_user_config("/tmp")

        self._default_user['user']['username'] = "local"
        set_default_lang(self.language_config["internal"])

        # self._setup_converse_handlers()

        self.transformers = UtteranceTransformersService(self.bus, self.config)

        self.transcript_service = None
        if callable(Transcribe):
            try:
                self.transcript_service = Transcribe()
            except Exception as e:
                LOG.exception(e)

        self.bus.on("neon.profile_update", self.handle_profile_update)
        self.bus.on("neon.languages.skills", self.handle_supported_languages)

    @property
    def supported_languages(self) -> List[str]:
        """
        Get a list of supported ISO 639-1 language codes
        """
        return [lang.split('-')[0] for lang in
                self.language_config.get("supported_langs") or []]

    def handle_supported_languages(self, message):
        """
        Handle a request for supported skills languages
        :param message: neon.get_languages_skills request
        """
        translator = self.transformers.loaded_modules.get(
            'neon_utterance_translator_plugin')
        translate_langs = list(translator.translator.available_languages) if \
            translator and translator.translator else list()

        native_langs = list(self.supported_languages or ['en'])
        skill_langs = list(set(native_langs + translate_langs))
        self.bus.emit(message.response({"skill_langs": skill_langs,
                                        "native_langs": native_langs,
                                        "translate_langs": translate_langs}))

    def handle_profile_update(self, message):
        updated_profile = message.data.get("profile")
        if updated_profile["user"]["username"] == \
                self._default_user["user"]["username"]:
            apply_local_user_profile_updates(updated_profile,
                                             self._default_user)

    def shutdown(self):
        self.transformers.shutdown()

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

    def _get_parsers_service_context(self, message: Message, lang: str):
        """
        Pipe utterance thorough text parsers to get more metadata.
        Utterances may be modified by any parser and context overwritten
        :param message: Message to parse
        """
        utterances = message.data.get('utterances', [])
        message.context["lang"] = lang
        LOG.debug(f"lang={lang}|utterances={utterances}")
        utterances, message.context = \
            self.transformers.transform(utterances, message.context)
        message.data["utterances"] = utterances
        return message

    def handle_utterance(self, message):
        """
        Handler for 'recognizer_loop:utterance'
        Main entrypoint for handling user utterances with skills module

        Arguments:
            message (Message): message associated with user request
        """
        utt_received = time.time()

        # Notify emitting module that skills is handling this utterance
        self.bus.emit(message.response())

        # Add or init timing data
        message.context.setdefault("timing", dict())
        message.context["timing"]["handle_utterance"] = utt_received
        if message.context["timing"].get("client_sent") and \
                not message.context["timing"].get("client_to_core"):
            message.context["timing"]["client_to_core"] = \
                utt_received - message.context["timing"]["client_sent"]

        try:
            # Get language of the utterance
            requested_lang = message.data.get('lang')
            lang = get_full_lang_code(
                message.data.get('lang') or self.language_config["user"])
            if requested_lang and \
                    requested_lang.split('-')[0] != lang.split('-')[0]:
                lang = get_full_lang_code(requested_lang.split('-')[0])
                LOG.warning(f"requested={requested_lang}|resolved={lang}")
            message.data["lang"] = lang
            LOG.debug(f"message_lang={lang}")
        except Exception as e:
            LOG.exception(e)
            if '-' not in message.data.get("lang", ""):
                raise RuntimeError(f"Full `lang` code not in message.data: "
                                   f"{message.data}")
            lang = message.data["lang"]

        try:
            # Ensure user profile data is present
            if "user_profiles" not in message.context:
                message.context["user_profiles"] = [self._default_user.content]
                message.context["username"] = \
                    self._default_user.content["user"]["username"]

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
                message = self._get_parsers_service_context(message, lang)
            # TODO: `text_parsers` timing context left for backwards-compat.
            message.context["timing"]["text_parsers"] = stopwatch.time
            message.context["timing"]["transform_utterance"] = stopwatch.time

            # Normalize all utterances for intent engines
            message.data['utterances'] = [u.lower().strip() for u in
                                          message.data.get('utterances', [])
                                          if u.strip()]

            # Catch empty utterances after parser service
            if len(message.data['utterances']) == 0:
                LOG.info("Received empty utterance!")
                reply = message.reply('intent_aborted',
                                      {'utterances': message.data['utterances'],
                                       'lang': lang})
                self.bus.emit(reply)
                return

            if message.data["lang"].split('-')[0] in self.supported_languages:
                LOG.debug(f'Native language support ({message.data["lang"]})')
                if message.context.get("translation_data") and \
                    message.context.get("translation_data")[0].get(
                        "was_translated"):
                    # TODO: Patching translation plugin supported language check
                    LOG.warning(f"Translated supported input!")
                    real_utterances = [message.context.get(
                        "translation_data")[0].get("raw_utterance")]
                    message.data["utterances"] = real_utterances
            # If translated, make sure message.data['lang'] is updated
            elif message.context.get("translation_data") and \
                    message.context.get("translation_data")[0].get(
                        "was_translated"):
                LOG.info(f"Using utterance translated to: "
                         f"{self.language_config['internal']}")
                message.data["lang"] = self.language_config["internal"]
            # now pass our modified message to Mycroft
            # TODO: Consider how to implement 'and' parsing and converse DM
            LOG.info(f"lang={message.data['lang']} "
                     f"{message.data.get('utterances')}")
            super().handle_utterance(message)
        except Exception as err:
            LOG.exception(err)

    def handle_get_padatious(self, message):
        # TODO: Override to explicitly handle language
        utterance = message.data["utterance"]
        language = message.data.get("lang")
        norm = message.data.get('norm_utt', utterance)
        if language not in self.padatious_service.containers:
            LOG.warning(f"{language} not found in padatious containers "
                        f"{self.padatious_service.containers}")
        intent = self.padatious_service.calc_intent(utterance, language)
        if not intent and norm != utterance:
            intent = self.padatious_service.calc_intent(norm, language)
        if intent:
            intent = intent.__dict__
        self.bus.emit(message.reply("intent.service.padatious.reply",
                                    {"intent": intent}))


# TODO: Overrides below backporting 0.0.8 compat
class NeonConverseService(ConverseService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bus.on('mycroft.speech.recognition.unknown', self.reset_converse)
        self.bus.on('intent.service.skills.deactivate', self.handle_deactivate_skill_request)
        self.bus.on('intent.service.skills.activate', self.handle_activate_skill_request)
        self.bus.on('active_skill_request', self.handle_activate_skill_request)  # TODO backwards compat, deprecate
        self.bus.on('intent.service.active_skills.get', self.handle_get_active_skills)
        self.bus.on("skill.converse.get_response.enable", self.handle_get_response_enable)
        self.bus.on("skill.converse.get_response.disable", self.handle_get_response_disable)

    @property
    def active_skills(self):
        session = SessionManager.get()
        return session.active_skills

    @active_skills.setter
    def active_skills(self, val):
        session = SessionManager.get()
        session.active_skills = []
        for skill_id, ts in val:
            session.activate_skill(skill_id)

    def get_active_skills(self, message=None):
        """Active skill ids ordered by converse priority
        this represents the order in which converse will be called

        Returns:
            active_skills (list): ordered list of skill_ids
        """
        session = SessionManager.get(message)
        return [skill[0] for skill in session.active_skills]

    def deactivate_skill(self, skill_id, source_skill=None, message=None):
        """Remove a skill from being targetable by converse.

        Args:
            skill_id (str): skill to remove
            source_skill (str): skill requesting the removal
        """
        source_skill = source_skill or skill_id
        if self._deactivate_allowed(skill_id, source_skill):
            session = SessionManager.get(message)
            if session.is_active(skill_id):
                # update converse session
                session.deactivate_skill(skill_id)

                # keep message.context
                message = message or Message("")
                message.context["session"] = session.serialize()  # update session active skills
                # send bus event
                self.bus.emit(
                    message.forward("intent.service.skills.deactivated",
                                    data={"skill_id": skill_id}))
                if skill_id in self._consecutive_activations:
                    self._consecutive_activations[skill_id] = 0

    def activate_skill(self, skill_id, source_skill=None, message=None):
        """Add a skill or update the position of an active skill.

        The skill is added to the front of the list, if it's already in the
        list it's removed so there is only a single entry of it.

        Args:
            skill_id (str): identifier of skill to be added.
            source_skill (str): skill requesting the removal
        """
        source_skill = source_skill or skill_id
        if self._activate_allowed(skill_id, source_skill):
            # update converse session
            session = SessionManager.get(message)
            session.activate_skill(skill_id)

            # keep message.context
            message = message or Message("")
            message.context["session"] = session.serialize()  # update session active skills
            message = message.forward("intent.service.skills.activated",
                                      {"skill_id": skill_id})
            # send bus event
            self.bus.emit(message)
            # update activation counter
            self._consecutive_activations[skill_id] += 1

    def _collect_converse_skills(self, message=None):
        """use the messagebus api to determine which skills want to converse
        This includes all skills and external applications"""
        message = message or dig_for_message()
        session = SessionManager.get(message)

        skill_ids = []
        # include all skills in get_response state
        want_converse = [skill_id for skill_id, state in session.utterance_states.items()
                         if state == UtteranceState.RESPONSE]
        skill_ids += want_converse  # dont wait for these pong answers (optimization)

        active_skills = self.get_active_skills()

        if not active_skills:
            return want_converse

        event = Event()

        def handle_ack(msg):
            nonlocal event
            skill_id = msg.data["skill_id"]

            # validate the converse pong
            if all((skill_id not in want_converse,
                   msg.data.get("can_handle", True),
                   skill_id in active_skills)):
                want_converse.append(skill_id)

            if skill_id not in skill_ids: # track which answer we got
                skill_ids.append(skill_id)

            if all(s in skill_ids for s in active_skills):
                # all skills answered the ping!
                event.set()

        self.bus.on("skill.converse.pong", handle_ack)

        # ask skills if they want to converse
        for skill_id in active_skills:
            self.bus.emit(message.forward(f"{skill_id}.converse.ping",
                                          {"skill_id": skill_id}))

        # wait for all skills to acknowledge they want to converse
        event.wait(timeout=0.5)

        self.bus.remove("skill.converse.pong", handle_ack)
        return want_converse

    def _check_converse_timeout(self, message=None):
        """ filter active skill list based on timestamps """
        message = message or dig_for_message()
        timeouts = self.config.get("skill_timeouts") or {}
        def_timeout = self.config.get("timeout", 300)
        session = SessionManager.get(message)
        session.active_skills = [
            skill for skill in session.active_skills
            if time.time() - skill[1] <= timeouts.get(skill[0], def_timeout)]

    def converse(self, utterances, skill_id, lang, message):
        """Call skill and ask if they want to process the utterance.

        Args:
            utterances (list of tuples): utterances paired with normalized
                                         versions.
            skill_id: skill to query.
            lang (str): current language
            message (Message): message containing interaction info.

        Returns:
            handled (bool): True if handled otherwise False.
        """
        session = SessionManager.get(message)
        session.lang = lang

        state = session.utterance_states.get(skill_id, UtteranceState.INTENT)
        if state == UtteranceState.RESPONSE:
            converse_msg = message.reply(f"{skill_id}.converse.get_response",
                                         {"utterances": utterances,
                                          "lang": lang})
            self.bus.emit(converse_msg)
            return True

        if self._converse_allowed(skill_id):
            converse_msg = message.reply(f"{skill_id}.converse.request",
                                         {"utterances": utterances,
                                          "lang": lang})
            result = self.bus.wait_for_response(converse_msg,
                                                'skill.converse.response')
            if result and 'error' in result.data:
                error_msg = result.data['error']
                LOG.error(f"{skill_id}: {error_msg}")
                return False
            elif result is not None:
                return result.data.get('result', False)
        return False

    def converse_with_skills(self, utterances, lang, message):
        """Give active skills a chance at the utterance

        Args:
            utterances (list):  list of utterances
            lang (string):      4 letter ISO language code
            message (Message):  message to use to generate reply

        Returns:
            IntentMatch if handled otherwise None.
        """
        # we call flatten in case someone is sending the old style list of tuples
        utterances = flatten_list(utterances)
        # filter allowed skills
        self._check_converse_timeout(message)
        # check if any skill wants to handle utterance
        for skill_id in self._collect_converse_skills(message):
            if self.converse(utterances, skill_id, lang, message):
                return IntentMatch('Converse', None, None, skill_id)
        return None

    def handle_get_response_enable(self, message):
        skill_id = message.data["skill_id"]
        session = SessionManager.get(message)
        session.enable_response_mode(skill_id)
        if session.session_id == "default":
            SessionManager.sync(message)

    def handle_get_response_disable(self, message):
        skill_id = message.data["skill_id"]
        session = SessionManager.get(message)
        session.disable_response_mode(skill_id)
        if session.session_id == "default":
            SessionManager.sync(message)

    def handle_activate_skill_request(self, message):
        # TODO imperfect solution - only a skill can activate itself
        # someone can forge this message and emit it raw, but in OpenVoiceOS all
        # skill messages should have skill_id in context, so let's make sure
        # this doesnt happen accidentally at very least
        skill_id = message.data['skill_id']
        source_skill = message.context.get("skill_id")
        self.activate_skill(skill_id, source_skill, message)
        sess = SessionManager.get(message)
        if sess.session_id == "default":
            SessionManager.sync(message)

    def handle_deactivate_skill_request(self, message):
        # TODO imperfect solution - only a skill can deactivate itself
        # someone can forge this message and emit it raw, but in ovos-core all
        # skill message should have skill_id in context, so let's make sure
        # this doesnt happen accidentally
        skill_id = message.data['skill_id']
        source_skill = message.context.get("skill_id") or skill_id
        self.deactivate_skill(skill_id, source_skill, message)
        sess = SessionManager.get(message)
        if sess.session_id == "default":
            SessionManager.sync(message)

    def reset_converse(self, message):
        """Let skills know there was a problem with speech recognition"""
        lang = get_message_lang(message)
        try:
            setup_locale(lang)  # restore default lang
        except Exception as e:
            LOG.exception(f"Failed to set lingua_franca default lang to {lang}")

        self.converse_with_skills([], lang, message)

    def handle_get_active_skills(self, message):
        """Send active skills to caller.

        Argument:
            message: query message to reply to.
        """
        self.bus.emit(message.reply("intent.service.active_skills.reply",
                                    {"skills": self.get_active_skills(message)}))
