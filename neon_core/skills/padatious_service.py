import mycroft.skills.intent_services.padatious_service
from mycroft.skills.intent_services.padatious_service import PadatiousService as _svc, PadatiousIntent
from mycroft.skills.intent_services.padatious_service import PadatiousMatcher as _match

from multiprocessing.pool import Pool
from ovos_utils import flatten_list
from ovos_utils.log import LOG
from mycroft.skills.intent_services.base import IntentMatch


class PadatiousMatcher(_match):
    def _match_level(self, utterances, limit, lang=None):
        """Match intent and make sure a certain level of confidence is reached.

        Args:
            utterances (list of tuples): Utterances to parse, originals paired
                                         with optional normalized version.
            limit (float): required confidence level.
        """
        # we call flatten in case someone is sending the old style list of tuples
        utterances = flatten_list(utterances)
        if not self.has_result:
            lang = lang or self.service.lang
            LOG.debug(f'Padatious Matching confidence > {limit}')
            padatious_intent = self.service.threaded_calc_intent(utterances,
                                                                 lang)

            if padatious_intent:
                LOG.info(f"matched intent: {padatious_intent}")
                skill_id = padatious_intent.name.split(':')[0]
                self.ret = IntentMatch(
                    'Padatious', padatious_intent.name,
                    padatious_intent.matches, skill_id)
                self.conf = padatious_intent.conf
            self.has_result = True
        if self.conf and self.conf > limit:
            return self.ret


class PadatiousService(_svc):
    def threaded_calc_intent(self, utterances, lang):
        lang = lang or self.lang
        lang = lang.lower()
        if lang in self.containers:
            intent_container = self.containers.get(lang)
            with Pool(16) as pool:
                idx = 0
                padatious_intent = None
                for intent in pool.imap(calc_intent,
                                        ((utt, intent_container)
                                         for utt in utterances)):
                    if intent:
                        best = \
                            padatious_intent.conf if padatious_intent else 0.0
                        if best < intent.conf:
                            padatious_intent = intent
                            padatious_intent.matches['utterance'] = \
                                utterances[idx]
                            if intent.conf == 1.0:
                                LOG.debug(f"Returning perfect match")
                                return intent
                    idx += 1
            return padatious_intent


def calc_intent(*args):
    utt = args[0]
    intent_container = args[1]
    intent = intent_container.calc_intent(utt)
    if isinstance(intent, dict):
        if "entities" in intent:
            intent["matches"] = intent.pop("entities")
        intent["sent"] = utt
        intent = PadatiousIntent(**intent)
    return intent


mycroft.skills.intent_service.PadatiousMatcher = PadatiousMatcher
mycroft.skills.intent_service.PadatiousService = PadatiousService
