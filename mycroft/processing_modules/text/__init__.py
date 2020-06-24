from os.path import join, dirname
from mycroft.processing_modules import ModuleLoaderService
from mycroft.configuration import Configuration


class TextParsersService(ModuleLoaderService):

    def __init__(self, bus):
        parsers_dir = join(dirname(__file__), "modules").rstrip("/")
        super(TextParsersService, self).__init__(bus, parsers_dir)
        self.config = Configuration.get().get("text_parsers", {})
        self.blacklist = self.config.get("blacklist", [])

    def parse(self, parser, utterances=None, lang="en-us"):
        utterances = utterances or []
        if parser in self.loaded_modules:
            instance = self.loaded_modules[parser].get("instance")
            if instance:
                return instance.parse(utterances, lang)
        return utterances, {}


class TextParser:
    def __init__(self, name="test_parser", priority=50):
        self.name = name
        self.bus = None
        self.priority = priority
        self.config = Configuration.get().get("text_parsers", {}).\
            get(self.name, {})

    def bind(self, bus):
        """ attach messagebus """
        self.bus = bus

    def initialize(self):
        """ perform any initialization actions """
        pass

    def parse(self, utterances, lang="en-us"):
        """ parse utterances , return modified utterances + dict to be merged into message context """
        return utterances, {}

    def default_shutdown(self):
        """ perform any shutdown actions """
        pass

