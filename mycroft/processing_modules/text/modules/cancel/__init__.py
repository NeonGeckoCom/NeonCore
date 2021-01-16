from mycroft.processing_modules.text import TextParser
from mycroft import dialog


class Nevermind(TextParser):
    def __init__(self, name="utterance_cancel", priority=15):
        super().__init__(name, priority)

    def parse(self, utterances, lang="en-us"):
        cancel_words = dialog.get("cancel", lang)
        for nevermind in cancel_words:
            for utterance in utterances:
                if utterance.endswith(nevermind):
                    return [], {"canceled": True, "cancel_word": nevermind}

        return utterances, {}


def create_module():
    return Nevermind()



