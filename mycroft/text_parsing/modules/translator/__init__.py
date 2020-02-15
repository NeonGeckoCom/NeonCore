from mycroft.text_parsing.modules import TextParser
from mycroft.util.log import LOG
from mycroft.language import DetectorFactory, TranslatorFactory, get_lang_config


class UtteranceTranslator(TextParser):
    def __init__(self, name="utterance_translator", priority=5):
        super().__init__(name, priority)
        self.language_config = get_lang_config()
        self.lang_detector = DetectorFactory.create()
        self.translator = TranslatorFactory.create()

    def parse(self, utterances, user, lang="en-us"):
        metadata = []
        for idx, ut in enumerate(utterances):
            original = ut
            detected_lang = self.lang_detector.detect(original)
            LOG.debug("Detected language: {lang}".format(lang=detected_lang))
            if detected_lang != self.language_config["internal"].split("-")[0]:
                utterances[idx] = self.translator.translate(original,
                                                            self.language_config["internal"])
            # add language metadata to context
            metadata += [{
                "source_lang": lang,
                "detected_lang": detected_lang,
                "internal": self.language_config["internal"],
                "was_translated": detected_lang != self.language_config["internal"].split("-")[0],
                "raw_utterance": original
            }]

        # return translated utterances + data
        return utterances, {"translation_data": metadata}


def create_parser():
    return UtteranceTranslator()



