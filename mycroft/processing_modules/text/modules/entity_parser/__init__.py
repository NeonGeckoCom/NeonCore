# pip install simple_NER
# it's here mainly to test that a bad module does not cause failure
# might be useful to tag entities in the future
# check https://github.com/OpenJarbas/simple_NER

from simple_NER.annotators.keyword_ner import KeywordNER
from mycroft.processing_modules.text import TextParser


class EntityTagger(TextParser):
    def __init__(self, name="keyword_tagger", priority=99):
        super().__init__(name, priority)
        self.rake = KeywordNER()

    def parse(self, utterances, lang="en-us"):
        keywords = []
        for utterance in utterances:
            # extract keywords
            ents = list(self.rake.extract_entities(utterance))  # generator, needs list()
            # group into tuples of (keyword, score)
            keywords += [(ent.value, ent.score) for ent in ents]
        # sort by score
        keywords = sorted(keywords, key=lambda kw: kw[1], reverse=True)

        # return unchanged utterances + data
        return utterances, {"keywords": keywords}


def create_parser():
    return EntityTagger()



