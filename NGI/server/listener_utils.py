# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
#
# Notice of License - Duplicating this Notice of License near the start of any file containing
# a derivative of this software is a condition of license for this software.
# Friendly Licensing:
# No charge, open source royalty free use of the Neon AI software source and object is offered for
# educational users, noncommercial enthusiasts, Public Benefit Corporations (and LLCs) and
# Social Purpose Corporations (and LLCs). Developers can contact developers@neon.ai
# For commercial licensing, distribution of derivative works or redistribution please contact licenses@neon.ai
# Distributed on an "AS IS” basis without warranties or conditions of any kind, either express or implied.
# Trademarks of Neongecko: Neon AI(TM), Neon Assist (TM), Neon Communicator(TM), Klat(TM)
# Authors: Guy Daniels, Daniel McKnight, Regina Bloomstine, Elon Gasper, Richard Leeds
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2021: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

from NGI.utilities.chat_user_util import ChatUser
from mycroft.messagebus import MessageBusClient
from mycroft.util import LOG, create_daemon


class ServerListener:
    def __init__(self):
        self.chat_user_dict = {}
        bus = MessageBusClient()
        bus.on('neon.remove_cache_entry', self.remove_cached_profile)
        create_daemon(bus.run_forever)

    @staticmethod
    def _build_entry_for_nick(nick: str) -> dict:
        chat_user = ChatUser(nick)
        try:
            LOG.info(chat_user)
            user_profile_settings = {
                "brands": {
                    'ignored_brands': chat_user.brands_ignored,
                    'favorite_brands': chat_user.brands_favorite,
                    'specially_requested': chat_user.brands_requested,
                },
                "user": {
                    'first_name': chat_user.first_name,
                    'middle_name': chat_user.middle_name,
                    'last_name': chat_user.last_name,
                    'preferred_name': chat_user.nick,
                    'full_name': " ".join([name for name in (chat_user.first_name,
                                                             chat_user.middle_name,
                                                             chat_user.last_name) if name]),
                    'dob': chat_user.birthday,
                    'age': chat_user.age,
                    'email': chat_user.email,
                    'username': nick,
                    'password': chat_user.password,
                    'picture': chat_user.avatar,
                    'about': chat_user.about,
                    'phone': chat_user.phone,
                    'email_verified': chat_user.email_verified,
                    'phone_verified': chat_user.phone_verified
                },
                "location": {
                    'lat': chat_user.location_lat,
                    'lng': chat_user.location_long,
                    'city': chat_user.location_city,
                    'state': chat_user.location_state,
                    'country': chat_user.location_country,
                    'tz': chat_user.location_tz,
                    'utc': chat_user.location_utc
                },
                "units": {
                    'time': chat_user.time_format,
                    'date': chat_user.date_format,
                    'measure': chat_user.unit_measure
                },
                "speech": {
                 'stt_language': chat_user.stt_language,
                 'stt_region': chat_user.stt_region,
                 'alt_languages': ['en'],
                 'tts_language': chat_user.tts_language,
                 'tts_gender': chat_user.tts_gender,
                 'neon_voice': chat_user.ai_speech_voice,
                 'secondary_tts_language': chat_user.tts_secondary_language,
                 'secondary_tts_gender': chat_user.tts_secondary_gender,
                 'secondary_neon_voice': '',
                 'speed_multiplier': chat_user.speech_rate
                 # 'synonyms': chat_user.synonyms
                },
                "skills": {i.get("skill_id"): i for i in chat_user.skill_settings}
            }
        except Exception as e:
            LOG.error(e)
            user_profile_settings = None
        return user_profile_settings

    def update_profile_for_nick(self, nick: str):
        if nick not in self.chat_user_dict:
            self.chat_user_dict[nick] = self._build_entry_for_nick(nick)

    def get_nick_profiles(self, nicks: list):
        """
        Updates self.chatUserDict with all users in the conversation associated with the passed filename
        :param nicks: list of nicks in conversation
        """
        # nicks = self._get_nicks_for_shout_conversation(filename)
        # LOG.info('shout_id = '+str(shout_id))
        if not isinstance(nicks, list):
            raise TypeError("Expected list of nicks")
        nicks_in_conversation = dict()
        for nickname in nicks:
            if nickname == "neon":
                LOG.debug("Ignoring neon")
            elif nickname in self.chat_user_dict:
                nicks_in_conversation[nickname] = self.chat_user_dict.get(nickname, None)
                LOG.debug('profile in cache: ' + nickname + ', cache length = ' + str(len(self.chat_user_dict)))
            else:
                # chat_user = ChatUser(nickname)
                try:
                    # LOG.info(chat_user)
                    self.chat_user_dict[nickname] = self._build_entry_for_nick(nickname)
                    LOG.info(self.chat_user_dict[nickname])
                    nicks_in_conversation[nickname] = self.chat_user_dict[nickname]
                    LOG.info(nicks_in_conversation[nickname])
                except Exception as x:
                    LOG.error(x)
                finally:
                    LOG.debug(f'profile added to cache: {nickname} cache length = {len(self.chat_user_dict)}')

        return nicks_in_conversation

    def remove_cached_profile(self, message):
        """
        Handler to remove a cached nick profile when a profile is updated.
        This may be called when a skill or external source changes a user profile
        :param message: Message associated with request
        """
        LOG.debug(f"DM: remove_cache_entry called message={message.data}")
        # LOG.debug(message.data)
        nick = message.data.get("nick", "")  # This IS data, not context
        if not nick:
            LOG.error("Invalid remove cache entry request")
            nick = message.data
        self.chat_user_dict.pop(nick)
