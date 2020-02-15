from os.path import join, dirname
from mycroft.processing_modules import ModuleLoaderService


class AudioParsersService(ModuleLoaderService):

    def __init__(self, bus):
        parsers_dir = join(dirname(__file__), "modules").rstrip("/")
        super(AudioParsersService, self).__init__(bus, parsers_dir)

    def feed_audio(self, chunk):
        for parser in self.loaded_modules:
            instance = self.loaded_modules[parser].get("instance")
            if instance:
                instance.on_audio(chunk)

    def feed_hotword(self, chunk):
        for parser in self.loaded_modules:
            instance = self.loaded_modules[parser].get("instance")
            if instance:
                instance.on_hotword(chunk)

    def feed_speech(self, chunk):
        for parser in self.loaded_modules:
            instance = self.loaded_modules[parser].get("instance")
            if instance:
                instance.on_speech(chunk)


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
        pass

    def on_hotword(self, audio_data):
        """ Take any action you want, audio_data is a full wake/hotword """
        pass

    def on_speech(self, audio_data):
        """ Take any action you want, audio_data is a speech chunk (NOT a
        full utterance) this is during recording """
        pass

    def default_shutdown(self):
        """ perform any shutdown actions """
        pass

