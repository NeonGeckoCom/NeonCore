# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
#
# Notice of License - Duplicating this Notice of License near the start of any file containing
# a derivative of this software is a condition of license for this software.
# Friendly Licensing:
# No charge, open source royalty free use of the Neon AI software source and object is offered for
# educational users, noncommercial enthusiasts, Public Benefit Corporations (and LLCs) and
# Social Purpose Corporations (and LLCs). Developers can contact developers@neon.ai
# For commercial licensing, distribution of derivative works or redistribution please contact licenses@neon.ai
# Distributed on an "AS IS” basis without warranties or conditions of any kind, either express or implied.
# Trademarks of Neongecko: Neon AI(TM), Neon Assist (TM), Neon Communicator(TM), Klat(TM)
# Authors: Guy Daniels, Daniel McKnight, Regina Bloomstine, Elon Gasper, Richard Leeds
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2021: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending
#
# This software is an enhanced derivation of the Mycroft Project which is licensed under the
# Apache software Foundation software license 2.0 https://www.apache.org/licenses/LICENSE-2.0
# Changes Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
#
# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import json

from abc import ABCMeta, abstractmethod
from speech_recognition import Recognizer
from queue import Queue
from threading import Thread

from mycroft.configuration import Configuration, get_private_keys
from mycroft.util import check_for_signal
from mycroft.util.log import LOG
from mycroft.util.plugins import load_plugin


class STT(metaclass=ABCMeta):
    """ STT Base class, all  STT backends derives from this one. """

    def __init__(self):
        config_core = Configuration.get()
        self.lang = str(self.init_language(config_core))
        config_stt = config_core.get("stt", {})
        self.config = config_stt.get(config_stt.get("module"), {})
        self.credential = self.config.get("credential", {})
        self.recognizer = Recognizer()
        self.can_stream = False
        self.keys = get_private_keys()

    @staticmethod
    def init_language(config_core):
        lang = config_core.get("lang", "en-US")
        langs = lang.split("-")
        if len(langs) == 2:
            return langs[0].lower() + "-" + langs[1].upper()
        return lang

    @abstractmethod
    def execute(self, audio, language=None, alt_langs=None):
        pass


class TokenSTT(STT, metaclass=ABCMeta):
    def __init__(self):
        super(TokenSTT, self).__init__()
        self.token = self.credential.get("token")


class GoogleJsonSTT(STT, metaclass=ABCMeta):
    def __init__(self):
        super(GoogleJsonSTT, self).__init__()
        if not self.credential.get("json") or self.keys.get("google_cloud"):
            self.credential["json"] = self.keys["google_cloud"]
        self.json_credentials = json.dumps(self.credential.get("json"))


class BasicSTT(STT, metaclass=ABCMeta):

    def __init__(self):
        super(BasicSTT, self).__init__()
        self.username = str(self.credential.get("username"))
        self.password = str(self.credential.get("password"))


class KeySTT(STT, metaclass=ABCMeta):

    def __init__(self):
        super(KeySTT, self).__init__()
        self.id = str(self.credential.get("client_id"))
        self.key = str(self.credential.get("client_key"))


class GoogleCloudSTT(GoogleJsonSTT):
    def __init__(self):
        super(GoogleCloudSTT, self).__init__()
        # override language with module specific language selection
        self.lang = self.config.get('lang') or self.lang

    def execute(self, audio, language=None, alt_langs=None):
        self.lang = language or self.lang
        return self.recognizer.recognize_google_cloud(audio,
                                                      self.json_credentials,
                                                      self.lang)


class StreamThread(Thread, metaclass=ABCMeta):
    """
        ABC class to be used with StreamingSTT class implementations.
    """

    def __init__(self, queue, language):
        super().__init__()
        self.language = language
        self.queue = queue
        self.transcriptions = None

    def _get_data(self):
        while True:
            d = self.queue.get()
            if d is None:
                break
            yield d
            self.queue.task_done()

    def run(self):
        return self.handle_audio_stream(self._get_data(), self.language)

    @abstractmethod
    def handle_audio_stream(self, audio, language):
        pass


class StreamingSTT(STT, metaclass=ABCMeta):
    """
        ABC class for threaded streaming STT implemenations.
    """

    def __init__(self):
        super().__init__()
        self.queue = None
        self.stream = None
        self.has_result = False
        self.can_stream = True

    def stream_start(self, language=None):
        """
        Starts a stream for audio processing
        """
        self.stream_stop()
        language = language or self.lang
        self.queue = Queue()
        self.stream = self.create_streaming_thread()
        self.stream.start()

    def stream_data(self, data):
        """
        Adds audio chunks to the active STT stream
        :param data: audio chunk
        :return:
        """
        self.queue.put(data)

    def stream_stop(self):
        """
        Ends the stream thread and returns the list of transcript candidates (called by StreamingSTT.execute)
        :return: list of possible transcriptions
        """
        if self.stream is not None:
            self.queue.put(None)
            self.stream.join()

            transcriptions = self.stream.transcriptions

            self.stream = None
            self.queue = None
            return transcriptions
        return None

    def execute(self, audio, language=None, alt_langs=None):
        """
        Overrides STT class execute and ends and returns the result of the current stream
        :param audio: (AudioData) equivalent to chunks processed by the stream
        :param language: (str) expected language of audio input
        :param alt_langs: (str) alternative languages of audio input
        :return: (list[str]) transcriptions
        """
        return self.stream_stop()

    @abstractmethod
    def create_streaming_thread(self):
        pass


class GoogleStreamThread(StreamThread):
    def __init__(self, queue, lang, client, streaming_config):
        super().__init__(queue, lang)
        self.client = client
        self.streaming_config = streaming_config

    def handle_audio_stream(self, audio, language):
        req = (types.StreamingRecognizeRequest(audio_content=x) for x in audio)
        responses = self.client.streaming_recognize(self.streaming_config, req)
        for res in responses:
            if res.results and res.results[0].is_final:
                self.transcriptions = [res.results[0].alternatives[0].transcript]
                check_for_signal("CORE_streamToSTT")
        return self.transcriptions


class GoogleCloudStreamingSTT(StreamingSTT):
    """
        Streaming STT interface for Google Cloud Speech-To-Text
        To use pip install google-cloud-speech and add the
        Google API key to local mycroft.conf file. The STT config
        will look like this:

        "stt": {
            "module": "google_cloud_streaming",
            "google_cloud_streaming": {
                "credential": {
                    "json": {
                        # Paste Google API JSON here
        ...

    """

    def __init__(self):
        global SpeechClient, types, enums, Credentials
        from google.cloud.speech import SpeechClient
        from google.oauth2.service_account import Credentials

        super(GoogleCloudStreamingSTT, self).__init__()
        # override language with module specific language selection
        self.language = self.config.get('lang') or self.lang

        if not self.credential.get("json") or self.keys.get("google_cloud"):
            self.credential["json"] = self.keys["google_cloud"]

        credentials = Credentials.from_service_account_info(
            self.credential.get('json')
        )

        self.client = SpeechClient(credentials=credentials)
        recognition_config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=self.language,
            model='command_and_search',
            max_alternatives=1,
        )
        self.streaming_config = types.StreamingRecognitionConfig(
            config=recognition_config,
            interim_results=True,
            single_utterance=True,
        )

    def create_streaming_thread(self):
        self.queue = Queue()
        return GoogleStreamThread(
            self.queue,
            self.language,
            self.client,
            self.streaming_config
        )


class DeepSpeechLocalStreamThread(StreamThread):
    def __init__(self, queue, lang, client):
        super().__init__(queue, lang)
        self.client = client

    def handle_audio_stream(self, audio, language):
        import numpy as np
        import time
        import math

        short_normalize = (1.0 / 32768.0)
        swidth = 2
        threshold = 10
        timeout_length = 5

        def rms(frame):
            count = len(frame) / swidth
            sum_squares = 0.0
            for sample in frame:
                n = sample * short_normalize
                sum_squares += n * n
            rms_value = math.pow(sum_squares / count, 0.5)
            return rms_value * 1000

        stream = self.client.createStream()
        current_time = time.time()
        end_time = current_time + timeout_length
        previous_intermediate_result, current_intermediate_result = '', ''
        has_data = False
        for data in audio:
            data16 = np.frombuffer(data, dtype=np.int16)
            if data16.max() != data16.min():
                has_data = True
            current_time = time.time()
            stream.feedAudioContent(data16)
            current_intermediate_result = stream.intermediateDecode()
            if rms(data16) > threshold and current_intermediate_result != previous_intermediate_result:
                end_time = current_time + timeout_length
            previous_intermediate_result = current_intermediate_result
            if current_time > end_time:
                break
        responses = stream.finishStream()
        self.transcriptions = responses

        if not has_data:  # Model sometimes transcribes words from silence, simple check for any audio data
            LOG.warning(f"Audio was empty!")
            self.transcriptions = None
        check_for_signal("CORE_streamToSTT")
        return self.transcriptions


class DeepSpeechLocalStreamingSTT(StreamingSTT):
    """
        Streaming STT interface for DeepSpeech
    """

    def __init__(self):
        import deepspeech
        import os

        super(DeepSpeechLocalStreamingSTT, self).__init__()
        # override language with module specific language selection
        self.language = self.config.get('lang') or self.lang
        if not self.language.startswith("en"):
            raise ValueError("DeepSpeech is currently english only")

        model_path = self.config.get("model_path")
        scorer_path = self.config.get("scorer_path")
        if not model_path or not os.path.isfile(model_path):
            LOG.error("You need to provide a valid model file")
            LOG.info("download a model from https://github.com/mozilla/DeepSpeech")
            raise FileNotFoundError
        if not scorer_path or not os.path.isfile(scorer_path):
            LOG.warning("You should provide a valid scorer")
            LOG.info("download scorer from https://github.com/mozilla/DeepSpeech")

        self.client = deepspeech.Model(model_path)

        if scorer_path:
            self.client.enableExternalScorer(scorer_path)

    def create_streaming_thread(self):
        self.queue = Queue()
        return DeepSpeechLocalStreamThread(
            self.queue,
            self.language,
            self.client
        )


def load_stt_plugin(module_name):
    """Wrapper function for loading stt plugin.

    Arguments:
        (str) Mycroft stt module name from config
    """
    return load_plugin('mycroft.plugin.stt', module_name)


class STTFactory:
    CLASSES = {
        "deepspeech_stream_local": DeepSpeechLocalStreamingSTT,
        "google_cloud": GoogleCloudSTT,
        "google_cloud_streaming": GoogleCloudStreamingSTT
    }

    @staticmethod
    def create():
        # TODO: If SWW and module doesn't stream, log warning and clear signal? DM
        module = None
        try:
            config = Configuration.get().get("stt", {})
            module = config.get("module", "mycroft")  # TODO: Default to something defined in CLASSES? DM
            if module in STTFactory.CLASSES:
                clazz = STTFactory.CLASSES[module]
            else:
                clazz = load_stt_plugin(module)
                LOG.info('Loaded the STT plugin {}'.format(module))
            return clazz()
        except Exception as e:
            # The STT backend failed to start. Report it and fall back to
            # default.
            LOG.exception('The selected STT backend could not be loaded, '
                          'falling back to default...')
            LOG.error(e)
            if module != 'chromium_stt_plug':
                clazz = load_stt_plugin("chromium_stt_plug")
                LOG.info('Loaded fallback STT plugin {}'.format(module))
                return clazz()
            else:
                raise
