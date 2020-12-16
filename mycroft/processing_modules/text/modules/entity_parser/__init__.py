# pip install simple_NER
# it's here mainly to test that a bad module does not cause failure
# might be useful to tag entities in the future
# check https://github.com/OpenJarbas/simple_NER

from RAKEkeywords import Rake
from mycroft.processing_modules.text import TextParser


class EntityTagger(TextParser):
    def __init__(self, name="keyword_tagger", priority=99):
        super().__init__(name, priority)

    def parse(self, utterances, lang="en-us"):
        keywords = []
        for utterance in utterances:
            # extract keywords
            rake = Rake(lang)
            keywords += rake.extract_keywords(utterance)

        # return unchanged utterances + data
        return utterances, {"keywords": keywords}


def create_module():
    return EntityTagger()



