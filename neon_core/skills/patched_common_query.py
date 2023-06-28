# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re
import time
from dataclasses import dataclass
from itertools import chain
from threading import Event
from typing import Dict

from ovos_bus_client.message import Message, dig_for_message
from ovos_utils.enclosure.api import EnclosureAPI
from ovos_utils.log import LOG
from ovos_utils.messagebus import get_message_lang

from mycroft.skills.intent_services.base import IntentMatch
from mycroft.skills.skill_data import CoreResources
# TODO: Port to ovos-core
EXTENSION_TIME = 10


@dataclass
class Query:
    session_id: str
    query: str
    replies: list = None
    extensions: list = None
    timeout_time: float = time.time() + 1
    responses_gathered: Event = Event()
    completed: Event = Event()
    answered: bool = False


class CommonQuery:
    def __init__(self, bus):
        self.bus = bus
        self.skill_id = "common_query.neongeckocom"  # fake skill
        self.active_queries: Dict[str, Query] = dict()  # dict of session ID to query
        # self.lock = Lock()
        self.enclosure = EnclosureAPI(self.bus, self.skill_id)
        self._vocabs = {}
        self.bus.on('question:query.response', self.handle_query_response)
        self.bus.on('common_query.question', self.handle_question)
        # TODO: Register available CommonQuery skills

    def get_sid(self, message: Message):
        sid = message.context.get('session', {}).get('session_id')
        if not sid:
            LOG.warning(f"Session ID not found! falling back to utterance")
            sid = message.data.get('utterance')
        return sid

    def voc_match(self, utterance, voc_filename, lang, exact=False):
        """Determine if the given utterance contains the vocabulary provided.

        By default the method checks if the utterance contains the given vocab
        thereby allowing the user to say things like "yes, please" and still
        match against "Yes.voc" containing only "yes". An exact match can be
        requested.

        The method checks the "res/text/{lang}" folder of mycroft-core.
        The result is cached to avoid hitting the disk each time the method is called.

        Args:
            utterance (str): Utterance to be tested
            voc_filename (str): Name of vocabulary file (e.g. 'yes' for
                                'res/text/en-us/yes.voc')
            lang (str): Language code, defaults to self.lang
            exact (bool): Whether the vocab must exactly match the utterance

        Returns:
            bool: True if the utterance has the given vocabulary it
        """
        match = False

        if lang not in self._vocabs:
            resources = CoreResources(language=lang)
            vocab = resources.load_vocabulary_file(voc_filename)
            self._vocabs[lang] = list(chain(*vocab))

        if utterance:
            if exact:
                # Check for exact match
                match = any(i.strip() == utterance
                            for i in self._vocabs[lang])
            else:
                # Check for matches against complete words
                match = any([re.match(r'.*\b' + i + r'\b.*', utterance)
                             for i in self._vocabs[lang]])

        return match

    def is_question_like(self, utterance, lang):
        # skip utterances with less than 3 words
        if len(utterance.split(" ")) < 3:
            return False
        # skip utterances meant for common play
        if self.voc_match(utterance, "common_play", lang):
            return False
        return True

    def match(self, utterances, lang, message):
        """Send common query request and select best response

        Args:
            utterances (list): List of tuples,
                               utterances and normalized version
            lang (str): Language code
            message: Message for session context
        Returns:
            IntentMatch or None
        """
        match = None
        utterance = utterances[0][0]
        if self.is_question_like(utterance, lang):
            message.data["lang"] = lang  # only used for speak
            message.data["utterance"] = utterance
            answered = self.handle_question(message)
            if answered:
                match = IntentMatch('CommonQuery', None, {}, None)
        return match

    def handle_question(self, message):
        """ Send the phrase to the CommonQuerySkills and prepare for handling
            the replies.
        """
        utt = message.data.get('utterance')
        sid = self.get_sid(message)
        query = Query(session_id=sid, query=utt, replies=[], extensions=[])
        self.active_queries[sid] = query
        self.enclosure.mouth_think()

        LOG.info(f'Searching for {utt}')
        # Send the query to anyone listening for them
        msg = message.reply('question:query', data={'phrase': utt})
        if "skill_id" not in msg.context:
            msg.context["skill_id"] = self.skill_id
        self.bus.emit(msg)

        query.timeout_time = time.time() + 1
        timeout = False
        while not query.responses_gathered.wait(EXTENSION_TIME):
            if time.time() > query.timeout_time + 1:
                LOG.debug(f"Timeout gathering responses ({query.session_id})")
                timeout = True
                break

        # forcefully timeout if search is still going
        if timeout:
            LOG.warning(f"Timed out getting responses for: {query.query}")
        self._query_timeout(message)
        if not query.completed.wait(10):
            raise TimeoutError("Timed out processing responses")
        answered = bool(query.answered)
        self.active_queries.pop(sid)
        LOG.debug(f"answered={answered}")
        return answered

    def handle_query_response(self, message):
        search_phrase = message.data['phrase']
        skill_id = message.data['skill_id']
        searching = message.data.get('searching')
        answer = message.data.get('answer')

        query = self.active_queries.get(self.get_sid(message))
        if not query:
            LOG.warning(f"No active query for: {search_phrase}")
        # Manage requests for time to complete searches
        if searching:
            LOG.debug(f"{skill_id} is searching")
            # request extending the timeout by EXTENSION_TIME
            query.timeout_time = time.time() + EXTENSION_TIME
            # TODO: Perhaps block multiple extensions?
            if skill_id not in query.extensions:
                query.extensions.append(skill_id)
        else:
            # Search complete, don't wait on this skill any longer
            if answer:
                LOG.info(f'Answer from {skill_id}')
                query.replies.append(message.data)

            # Remove the skill from list of timeout extensions
            if skill_id in query.extensions:
                LOG.debug(f"Done waiting for {skill_id}")
                query.extensions.remove(skill_id)

            # not waiting for any more skills
            if not query.extensions:
                time.sleep(1)  # TODO: Patching quick replies
                if query.extensions:
                    LOG.debug(f"Another skill started handling "
                              f"{query.session_id}")
                    return
                LOG.debug(f"No more skills to wait for ({query.session_id})")
                query.responses_gathered.set()

    def _query_timeout(self, message):
        query: Query = self.active_queries.get(self.get_sid(message))
        LOG.info(f'Check responses with {len(query.replies)} replies')
        search_phrase = message.data.get('phrase', "")
        if query.extensions:
            query.extensions = []
        self.enclosure.mouth_reset()

        # Look at any replies that arrived before the timeout
        # Find response(s) with the highest confidence
        best = None
        ties = []
        for response in query.replies:
            if not best or response['conf'] > best['conf']:
                best = response
                ties = []
            elif response['conf'] == best['conf']:
                ties.append(response)

        if best:
            if ties:
                # TODO: Ask user to pick between ties or do it automagically
                pass

            # invoke best match
            self.speak(best['answer'], message)
            LOG.info('Handling with: ' + str(best['skill_id']))
            cb = best.get('callback_data') or {}
            self.bus.emit(message.forward('question:action',
                                          data={'skill_id': best['skill_id'],
                                                'phrase': search_phrase,
                                                'callback_data': cb}))
            query.answered = True
        else:
            query.answered = False
        query.completed.set()

    def speak(self, utterance, message=None):
        """Speak a sentence.

        Args:
            utterance (str):        sentence mycroft should speak
        """
        # registers the skill as being active
        self.enclosure.register(self.skill_id)

        message = message or dig_for_message()
        lang = get_message_lang(message)
        data = {'utterance': utterance,
                'expect_response': False,
                'meta': {"skill": self.skill_id},
                'lang': lang}

        m = message.forward("speak", data) if message \
            else Message("speak", data)
        m.context["skill_id"] = self.skill_id
        self.bus.emit(m)


import mycroft.skills.intent_services.commonqa_service
mycroft.skills.intent_services.commonqa_service.CommonQAService = CommonQuery
mycroft.skills.intent_service.CommonQAService = CommonQuery
