from os.path import join, dirname
from mycroft.processing_modules import ModuleLoaderService
from mycroft.util.json_helper import merge_dict
from speech_recognition import AudioData


class AudioParsersService(ModuleLoaderService):

    def __init__(self, bus):
        parsers_dir = join(dirname(__file__), "modules").rstrip("/")
        super(AudioParsersService, self).__init__(bus, parsers_dir)

    def feed_audio(self, chunk):
        for instance in self.modules:
            instance.on_audio(chunk)

    def feed_hotword(self, chunk):
        for instance in self.modules:
            instance.on_hotword(chunk)

    def feed_speech(self, chunk):
        for instance in self.modules:
            instance.on_speech(chunk)

    def get_context(self):
        context = {}
        for instance in self.modules:
            data = instance.on_speech_end()
            context = merge_dict(context, data)
        return context


class AudioParser:
    def __init__(self, name="test_parser", priority=50):
        self.name = name
        self.bus = None
        self.priority = priority

    def bind(self, bus):
        """ attach messagebus """
        self.bus = bus

    def initialize(self):
        """ perform any initialization actions """
        pass

    def on_audio(self, audio_data):
        """ Take any action you want, audio_data is a non-speech chunk """
        assert isinstance(audio_data, AudioData)

    def on_hotword(self, audio_data):
        """ Take any action you want, audio_data is a full wake/hotword
        Common action would be to prepare to received speech chunks
        NOTE: this might be a hotword or a wakeword, listening is not assured
        """
        assert isinstance(audio_data, AudioData)

    def on_speech(self, audio_data):
        """ Take any action you want, audio_data is a speech chunk (NOT a
        full utterance) this is during recording

         You can do streaming predictions or save the audio_data"""
        assert isinstance(audio_data, AudioData)

    def on_speech_end(self):
        """ return any additional message context to be passed in
        recognize_loop:utterance message, usually a streaming prediction

         Optionally make the prediction here with saved chunks (extra latency
         """
        return {}

    def default_shutdown(self):
        """ perform any shutdown actions """
        pass

