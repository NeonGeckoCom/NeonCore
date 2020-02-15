
class TextParser:
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

    def parse(self, utterances, user, lang="en-us"):
        """ parse utterances ,
        return modified utterances + dict to be merged into message context
         """
        return utterances, {}

    def default_shutdown(self):
        """ perform any shutdown actions """
        pass

