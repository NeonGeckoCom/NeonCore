import re
from os import walk
from os.path import join, exists
from threading import Timer
import time
from enum import Enum

from mycroft import dialog
from mycroft.audio import wait_while_speaking
from mycroft.messagebus.message import Message, dig_for_message
from mycroft.util import camel_case_split
from mycroft.util.log import LOG
from mycroft.skills.mycroft_skill.event_container import create_wrapper, \
    get_handler_name
from mycroft.skills.settings import save_settings
from mycroft.skills.skill_data import load_vocabulary, load_regex
from padatious import IntentContainer

from neon_core.language import DetectorFactory, TranslatorFactory, \
    get_lang_config, get_language_dir
from neon_core.configuration import get_private_keys
from neon_core.dialog import load_dialogs
from neon_core.skills.decorators import AbortEvent, \
    AbortQuestion, killable_event
from mycroft.skills import MycroftSkill


class UserReply(str, Enum):
    YES = "yes"
    NO = "no"


def get_non_properties(obj):
    """Get attibutes that are not properties from object.

    Will return members of object class along with bases down to MycroftSkill.

    Arguments:
        obj:    object to scan

    Returns:
        Set of attributes that are not a property.
    """

    def check_class(cls):
        """Find all non-properties in a class."""
        # Current class
        d = cls.__dict__
        np = [k for k in d if not isinstance(d[k], property)]
        # Recurse through base classes excluding MycroftSkill and object
        for b in [b for b in cls.__bases__ if b not in (object, NeonSkill)]:
            np += check_class(b)
        return np

    return set(check_class(obj.__class__))


class NeonSkill(MycroftSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keys = get_private_keys()

        # Lang support
        self.language_config = get_lang_config()
        self.lang_detector = DetectorFactory.create()
        self.translator = TranslatorFactory.create()

        # conversational intents
        intent_cache = join(self.file_system.path, "intent_cache")
        self.intent_parser = IntentContainer(intent_cache)
        if "min_intent_conf" not in self.settings:
            self.settings["min_intent_conf"] = 0.6
        self.converse_intents = {}

        self._threads = []
        self._original_converse = self.converse

    @property
    def lang(self):
        """Get the configured language."""
        return self.language_config.get("internal") or \
               self.config_core.get('lang')

    def bind(self, bus):
        """Register messagebus emitter with skill.

        Arguments:
            bus: Mycroft messagebus connection
        """
        if bus:
            super().bind(bus)
            self.train_internal_intents()

    def _register_system_event_handlers(self):
        super()._register_system_event_handlers()
        self.add_event("converse.deactivated", self._deactivate_skill)
        self.add_event("converse.activated", self._activate_skill)

    def register_converse_intent(self, intent_file, handler):
        """ converse padatious intents """
        name = '{}.converse:{}'.format(self.skill_id, intent_file)
        filename = self.find_resource(intent_file, 'vocab')
        if not filename:
            raise FileNotFoundError('Unable to find "{}"'.format(intent_file))
        self.intent_parser.load_intent(name, filename)
        self.converse_intents[name] = self.create_event_wrapper(handler)

    def train_internal_intents(self):
        """ train internal padatious parser """
        self.intent_parser.train(single_thread=True)

    def handle_internal_intents(self, message):
        """ called before converse method
        this gives active skills a chance to parse their own intents and
        consume the utterance, see conversational_intent decorator for usage
        """
        best_match = None
        best_score = 0
        for utt in message.data['utterances']:
            match = self.intent_parser.calc_intent(utt)
            if match and match.conf > best_score:
                best_match = match
                best_score = match.conf

        if best_score < self.settings["min_intent_conf"]:
            return False
        # call handler for intent
        message = message.forward(best_match.name, best_match.matches)
        self.converse_intents[best_match.name](message)
        return True

    def _deactivate_skill(self, message):
        skill_id = message.data.get("skill_id")
        if skill_id == self.skill_id:
            self.handle_skill_deactivated()

    def _activate_skill(self, message):
        skill_id = message.data.get("skill_id")
        if skill_id == self.skill_id:
            self.handle_skill_activated()

    def handle_skill_deactivated(self):
        """
        Invoked when the skill is removed from active skill list

        This means Converse method won't be called anymore
        """
        pass

    def handle_skill_activated(self):
        """
        Invoked when the skill is added to active skill list

        This means Converse method will be called from now on
        """
        pass

    def __get_response(self):
        """Helper to get a reponse from the user

        Returns:
            str: user's response or None on a timeout
        """

        def converse(message):
            utterances = message.data["utterances"]
            converse.response = utterances[0] if utterances else None
            converse.finished = True
            return True

        # install a temporary conversation handler
        self.make_active()
        converse.finished = False
        converse.response = None
        self.converse = converse

        # 10 for listener, 5 for SST, then timeout
        # NOTE a threading event is not used otherwise we can't raise the
        # AbortEvent exception to kill the thread
        start = time.time()
        while time.time() - start <= 15 and not converse.finished:
            time.sleep(0.1)
            if self._response is not False:
                converse.response = self._response
                converse.finished = True  # was overrided externally
        self.converse = self._original_converse
        return converse.response

    def _handle_killed_wait_response(self):
        self._response = None
        self.converse = self._original_converse

    def _wait_response(self, is_cancel, validator, on_fail, num_retries):
        """Loop until a valid response is received from the user or the retry
        limit is reached.

        Arguments:
            is_cancel (callable): function checking cancel criteria
            validator (callbale): function checking for a valid response
            on_fail (callable): function handling retries

        """
        self._response = False
        self._real_wait_response(is_cancel, validator, on_fail, num_retries)
        while self._response is False:
            time.sleep(0.1)
        return self._response

    @killable_event("mycroft.skills.abort_question", exc=AbortQuestion,
                    callback=_handle_killed_wait_response)
    def _real_wait_response(self, is_cancel, validator, on_fail, num_retries):
        """Loop until a valid response is received from the user or the retry
        limit is reached.

        Arguments:
            is_cancel (callable): function checking cancel criteria
            validator (callbale): function checking for a valid response
            on_fail (callable): function handling retries

        """
        num_fails = 0
        while True:
            if self._response is not False:
                # usually None when aborted externally (is None)
                # also allows overriding returned result from other events
                return self._response
            response = self.__get_response()

            if response is None:
                # if nothing said, prompt one more time
                num_none_fails = 1 if num_retries < 0 else num_retries
                if num_fails >= num_none_fails:
                    self._response = None
                    return
            else:
                if validator(response):
                    self._response = response
                    return

                # catch user saying 'cancel'
                if is_cancel(response):
                    self._response = None
                    return

            num_fails += 1
            if 0 < num_retries < num_fails or self._response is not False:
                self._response = None
                return

            line = on_fail(response)
            if line:
                self.speak(line, expect_response=True)
            else:
                self.bus.emit(Message('mycroft.mic.listen'))

    def ask_yesno(self, prompt, data=None):
        """Read prompt and wait for a yes/no answer

        This automatically deals with translation and common variants,
        such as 'yeah', 'sure', etc.

        Args:
              prompt (str): a dialog id or string to read
              data (dict): response data
        Returns:
              string:  'yes', 'no' or whatever the user response if not
                       one of those, including None
        """
        resp = self.get_response(dialog=prompt, data=data)

        if self.voc_match(resp, 'yes'):
            return UserReply.YES
        elif self.voc_match(resp, 'no'):
            return UserReply.NO
        else:
            return resp

    def ask_confirm(self, dialog, data=None):
        """Read prompt and wait for a yes/no answer
        This automatically deals with translation and common variants,
        such as 'yeah', 'sure', etc.
        Args:
              dialog (str): a dialog id or string to read
              data (dict): response data
        Returns:
              bool: True if 'yes', False if 'no', None for all other
                    responses or no response
        """
        resp = self.ask_yesno(dialog, data=data)
        if resp == UserReply.YES:
            return True
        elif resp == UserReply.NO:
            return False
        return None

    def remove_voc(self, utt, voc_filename, lang=None):
        """ removes any entry in .voc file from the utterance """
        lang = lang or self.lang
        cache_key = lang + voc_filename

        if cache_key not in self.voc_match_cache:
            # this will load .voc file to cache
            self.voc_match(utt, voc_filename, lang)

        if utt:
            # Check for matches against complete words
            for i in self.voc_match_cache[cache_key]:
                # Substitute only whole words matching the token
                utt = re.sub(r'\b' + i + r"\b", "", utt)

        return utt

    def activate_skill(self):
        """Bump skill to active_skill list in intent_service.

        This enables converse method to be called even without skill being
        used in last 5 minutes.
        """
        self.bus.emit(Message('skill.converse.activate_skill',
                              {'skill_id': self.skill_id}))

    def deactivate_skill(self):
        """Remove skill from active_skill list in intent_service.

        This disables converse method from being called
        """
        self.bus.emit(Message('skill.converse.deactivate_skill',
                              {'skill_id': self.skill_id}))

    def make_active(self):
        # backwards compat
        self.log.warning("make_active() has been deprecated, please use "
                         "activate_skill()")
        self.activate_skill()

    def _register_decorated(self):
        """Register all intent handlers that are decorated with an intent.

        Looks for all functions that have been marked by a decorator
        and read the intent data from them.  The intent handlers aren't the
        only decorators used.  Skip properties as calling getattr on them
        executes the code which may have unintended side-effects
        """
        super()._register_decorated()
        for attr_name in get_non_properties(self):
            method = getattr(self, attr_name)
            if hasattr(method, 'converse_intents'):
                for intent_file in getattr(method, 'converse_intents'):
                    self.register_converse_intent(intent_file, method)

    def _find_resource(self, res_name, lang, res_dirname=None):
        """Finds a resource by name, lang and dir
        """
        if res_dirname:
            # Try the old translated directory (dialog/vocab/regex)
            root_path = get_language_dir(join(self.root_dir, res_dirname),
                                         self.lang)
            path = join(root_path, res_name)
            if exists(path):
                return path

            # Try old-style non-translated resource
            path = join(self.root_dir, res_dirname, res_name)
            if exists(path):
                return path

        # New scheme:  search for res_name under the 'locale' folder
        root_path = get_language_dir(join(self.root_dir, 'locale'), self.lang)
        for path, _, files in walk(root_path):
            if res_name in files:
                return join(path, res_name)

        # Not found
        return None

    def create_event_wrapper(self, handler, handler_info=None):
        skill_data = {'name': get_handler_name(handler)}

        def on_error(e):
            """Speak and log the error."""
            if not isinstance(e, AbortEvent):
                # Convert "MyFancySkill" to "My Fancy Skill" for speaking
                handler_name = camel_case_split(self.name)
                msg_data = {'skill': handler_name}
                msg = dialog.get('skill.error', self.lang, msg_data)
                self.speak(msg)
                LOG.exception(msg)
            else:
                LOG.info("Skill execution aborted")
            # append exception information in message
            skill_data['exception'] = repr(e)

        def on_start(message):
            """Indicate that the skill handler is starting."""
            if handler_info:
                # Indicate that the skill handler is starting if requested
                msg_type = handler_info + '.start'
                self.bus.emit(message.forward(msg_type, skill_data))

        def on_end(message):
            """Store settings and indicate that the skill handler has completed
            """
            if self.settings != self._initial_settings:
                save_settings(self.root_dir, self.settings)
                self._initial_settings = self.settings
            if handler_info:
                msg_type = handler_info + '.complete'
                self.bus.emit(message.forward(msg_type, skill_data))

        return create_wrapper(handler, self.skill_id, on_start, on_end,
                              on_error)

    def add_event(self, name, handler, handler_info=None, once=False):
        """Create event handler for executing intent or other event.

        Arguments:
            name (string): IntentParser name
            handler (func): Method to call
            handler_info (string): Base message when reporting skill event
                                   handler status on messagebus.
            once (bool, optional): Event handler will be removed after it has
                                   been run once.
        """
        wrapper = self.create_event_wrapper(handler, handler_info)
        return self.events.add(name, wrapper, once)

    def speak(self, utterance, expect_response=False, wait=False, meta=None):
        """Speak a sentence.

        Arguments:
            utterance (str):        sentence mycroft should speak
            expect_response (bool): set to True if Mycroft should listen
                                    for a response immediately after
                                    speaking the utterance.
            wait (bool):            set to True to block while the text
                                    is being spoken.
            meta:                   Information of what built the sentence.
        """
        # registers the skill as being active
        meta = meta or {}
        meta['skill'] = self.name
        self.enclosure.register(self.name)

        message = dig_for_message()

        # check for user specified language
        # NOTE this will likely change in future
        user_lang = message.user_data.get("lang") or self.language_config[
            "user"]

        original = utterance
        detected_lang = self.lang_detector.detect(utterance)
        LOG.debug("Detected language: {lang}".format(lang=detected_lang))
        if detected_lang != user_lang.split("-")[0]:
            utterance = self.translator.translate(utterance, user_lang)

        data = {'utterance': utterance,
                'expect_response': expect_response,
                'meta': meta}

        # add language metadata to context
        message.context["utterance_data"] = {
            "detected_lang": detected_lang,
            "user_lang": self.language_config["user"],
            "was_translated": detected_lang ==
                              self.language_config["user"].split("-")[0],
            "raw_utterance": original
        }

        m = message.forward("speak", data) if message \
            else Message("speak", data)
        self.bus.emit(m)

        if wait:
            wait_while_speaking()

    def init_dialog(self, root_directory):
        # If "<skill>/dialog/<lang>" exists, load from there.  Otherwise
        # load dialog from "<skill>/locale/<lang>"
        dialog_dir = get_language_dir(join(root_directory, 'dialog'),
                                      self.lang)
        locale_dir = get_language_dir(join(root_directory, 'locale'),
                                      self.lang)
        # TODO support both? currently assumes only one of the schemes is used
        if exists(dialog_dir):
            self.dialog_renderer = load_dialogs(dialog_dir)
        elif exists(locale_dir):
            self.dialog_renderer = load_dialogs(locale_dir)
        else:
            LOG.debug('No dialog loaded')

    def load_vocab_files(self, root_directory):
        """ Load vocab files found under root_directory.

        Arguments:
            root_directory (str): root folder to use when loading files
        """
        keywords = []
        vocab_dir = get_language_dir(join(root_directory, 'vocab'),
                                     self.lang)
        locale_dir = get_language_dir(join(root_directory, 'locale'),
                                      self.lang)
        if exists(vocab_dir):
            keywords = load_vocabulary(vocab_dir, self.skill_id)
        elif exists(locale_dir):
            keywords = load_vocabulary(locale_dir, self.skill_id)
        else:
            LOG.debug('No vocab loaded')

        # For each found intent register the default along with any aliases
        for vocab_type in keywords:
            for line in keywords[vocab_type]:
                entity = line[0]
                aliases = line[1:]
                self.intent_service.register_adapt_keyword(vocab_type,
                                                           entity,
                                                           aliases)

    def load_regex_files(self, root_directory):
        """ Load regex files found under the skill directory.

        Arguments:
            root_directory (str): root folder to use when loading files
        """
        regexes = []
        regex_dir = get_language_dir(join(root_directory, 'regex'),
                                     self.lang)
        locale_dir = get_language_dir(join(root_directory, 'locale'),
                                      self.lang)
        if exists(regex_dir):
            regexes = load_regex(regex_dir, self.skill_id)
        elif exists(locale_dir):
            regexes = load_regex(locale_dir, self.skill_id)

        for regex in regexes:
            self.intent_service.register_adapt_regex(regex)

    def __handle_stop(self, _):
        """Handler for the "mycroft.stop" signal. Runs the user defined
        `stop()` method.
        """
        # abort any running killable intent
        self.bus.emit(Message(self.skill_id + ".stop"))

        def __stop_timeout():
            # The self.stop() call took more than 100ms, assume it handled Stop
            self.bus.emit(Message('mycroft.stop.handled',
                                  {'skill_id': str(self.skill_id) + ':'}))

        timer = Timer(0.1, __stop_timeout)  # set timer for 100ms
        try:
            if self.stop():
                self.bus.emit(Message("mycroft.stop.handled",
                                      {"by": "skill:" + self.skill_id}))
            timer.cancel()
        except Exception:
            timer.cancel()
            LOG.error('Failed to stop skill: {}'.format(self.name),
                      exc_info=True)

    def default_shutdown(self):
        super().default_shutdown()
        # kill any running kthreads from decorators
        for t in self._threads:
            try:
                t.kill()
            except:
                pass
