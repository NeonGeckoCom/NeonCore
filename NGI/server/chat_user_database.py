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

import json
import mysql.connector
from mysql.connector import Error
from time import time
from neon_utils.location_utils import *

from NGI.utilities.configHelper import NGIConfig as ngiConf
from mycroft.messagebus import MessageBusClient
from mycroft.util import LOG, create_daemon


class ChatUser:
    def __init__(self, nickname, dicts_requested=('user', 'brands', 'speech', 'units', 'location'),
                 cache_locations=None):
        if cache_locations is None:
            cache_locations = dict()
        start_time = time()
        LOG.debug("init ChatUser")
        self.updated_profile = False
        self.nick = nickname
        self.email = ''
        self.stt_language = 'en'
        self.stt_region = 'US'
        self.tts_language = 'en-us'
        self.tts_secondary_language = 'en-us'
        self.tts_gender = 'female'
        self.tts_secondary_gender = 'female'
        self.ai_speech_voice = 'Joanna'
        self.location_lat = 47.4799078
        self.location_long = -122.2034496
        self.time_format = 12
        self.unit_measure = 'imperial'
        self.date_format = 'MDY'
        self.location_tz = None
        self.location_utc = None
        self.location_city = 'Renton'
        self.location_state = 'Washington'
        self.location_country = 'USA'
        self.cache_locations = cache_locations
        self.config = ngiConf("ngi_auth_vars").content
        LOG.debug("config init time: " + str(time() - start_time))
        self.host = self.config['chatUserDbConnection']['host']
        self.database = self.config['chatUserDbConnection']['database']
        self.user = self.config['chatUserDbConnection']['user']
        self.password = self.config['chatUserDbConnection']['password']
        self.charset = self.config['chatUserDbConnection']['charset']
        self.first_name = ''
        self.middle_name = ''
        self.last_name = ''
        self.preferred_name = ''
        self.birthday = 'YYYY/MM/DD'
        self.age = ''
        self.avatar = ''
        self.about = ''
        self.phone = ''
        self.email_verified = False
        self.phone_verified = False
        self.speech_rate = 1.0
        # self.synonyms = {}
        self.brands_requested = {}
        self.brands_favorite = {}
        self.brands_ignored = {}

        self.utc = -8
        self.alt_languages = ['en']
        self.secondary_neon_voice = ''
        self.username = ''

        self.skill_settings = []

        LOG.debug("time to get to connection: " + str(time() - start_time))
        LOG.debug("About to print connection details")
        LOG.info(f"host: {self.host}  database: {self.database}  user: {self.user}  pass: {self.password}  "
                 f"charset: {self.charset}")
        self.connection = mysql.connector.connect(host=self.host, database=self.database, user=self.user,
                                                  password=self.password, charset=self.charset)
        db_info = self.connection.get_server_info()
        LOG.debug("Connected to MySQL database... MySQL Server version on " + db_info)
        self.get_chat_user_info(self.nick)
        LOG.debug("SQL read time: " + str(time() - start_time))
        LOG.info(f"DM: skill_settings={self.skill_settings}")

        if 'location' in dicts_requested:
            try:
                # Lat/Lng diff than City
                if (self.location_lat == 47.4799078 and self.location_city and
                    self.location_city not in ['Renton', 'undefined']) or \
                        (not self.location_lat and self.location_city):
                    LOG.debug("GBD: >>>Updating default lat/lng!")
                    # TODO: Reverse dict lookup cache
                    self.location_lat, self.location_long = get_coordinates(
                        {'city': self.location_city,
                         'state': self.location_state,
                         'country': self.location_country})
                    self.updated_profile = True

                elif self.location_lat != 47.4799078 and self.location_long != -122.2034496 and \
                        self.location_city in ['Renton', 'undefined', None]:
                    LOG.debug(">>>Updating city/state/country from lat/lng")
                    if self.cache_locations and f"{self.location_lat}, {self.location_long}" in self.cache_locations:
                        loc_data = cache_locations[f"{self.location_lat}, {self.location_long}"]
                        self.location_city = loc_data["city"]
                        self.location_state = loc_data["state"]
                        self.location_country = loc_data["country"]
                    else:
                        self.location_city, _, self.location_state, self.location_country = \
                            get_location(self.location_lat, self.location_long)
                        self.cache_locations[f"{self.location_lat}, {self.location_long}"] = {
                            "city": self.location_city, "state": self.location_state, "country": self.location_country}
                    self.updated_profile = True

                # City undefined, use defaults
                if not self.location_city or self.location_city == "undefined" or self.location_city == "null":
                    LOG.warning(f"{nickname} has invalid city (location_city={self.location_city})! using default")
                    self.location_lat = 47.4799078
                    self.location_long = -122.2034496
                    self.location_city = 'Renton'
                    self.location_state = 'Washington'
                    self.location_country = 'USA'

                if not self.location_tz or not self.location_utc:
                    self.location_tz, self.location_utc = get_timezone(self.location_lat, self.location_long)
                    self.updated_profile = True
                # elif not self.location_utc and self.location_tz:
                #     self.location_utc = get_offset(self.location_tz)
                #     self.updated_profile = True
                LOG.debug(">>>Profile tz, utc: " + str(self.location_tz) + ' ' + str(self.location_utc))
            except Exception as e:
                LOG.error(e)
        if 'units' in dicts_requested:
            if self.unit_measure not in ["imperial", "metric"]:
                LOG.warning(f"unit_measure value invalid! ({self.unit_measure}")
                self.unit_measure = "imperial"
            if self.date_format not in ["MDY", "YMD"]:
                LOG.warning(f"date_format value invalid! ({self.date_format}")
                self.date_format = "MDY"
            if self.time_format not in [12, 24]:
                LOG.warning(f"time_format value invalid! ({self.time_format}")
                self.date_format = 12
        if 'user' in dicts_requested:
            if self.email == "bogus@makeitup.com":
                self.email = ""
            if not self.first_name:
                self.first_name = ""
            if not self.middle_name:
                self.middle_name = ""
            if not self.last_name:
                self.last_name = ""
            if self.first_name:
                self.preferred_name = self.first_name
            else:
                self.preferred_name = self.nick
        LOG.debug("Profile init time: " + str(time() - start_time))

    def get_chat_user_info(self, nickname):
        LOG.debug(nickname)
        start_time = time()
        cursor = None
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()
                cursor.execute("select mail, stt_language, tts_language, tts_secondary_language, tts_voice_gender, \
                                ai_speech_voice, location_lat, location_long, time_format, unit_measure, \
                                date_format, location_city, location_state, location_country, timezone, first_name, \
                                middle_name, last_name, preferred_name, birthday, age, \
                                utc, birthday, email_verified, phone_verified, ignored_brands, favorite_brands, \
                                specially_requested, stt_region, alt_languages, secondary_tts_gender, \
                                secondary_neon_voice, username, phone, synonyms, skill_settings \
                                from shoutbox_users \
                                where nick = '" + nickname + "'")
                # record = cursor.fetchone()
                # LOG.debug ("Your connected to - " + record)
                rows = cursor.fetchall()
                LOG.debug("cursor time: " + str(time() - start_time))
                LOG.debug(rows)
                if len(rows) > 0:
                    for row in rows:
                        # return row[0]
                        self.email = row[0]
                        self.stt_language = row[1]
                        self.tts_language = row[2]
                        self.tts_secondary_language = row[3]
                        self.tts_gender = row[4]
                        self.ai_speech_voice = row[5]

                        if row[6]:
                            self.location_lat = float(row[6])
                            self.location_long = float(row[7])

                        self.time_format = int(row[8])
                        self.unit_measure = row[9]
                        self.date_format = row[10]
                        self.location_city = row[11]
                        self.location_state = row[12]
                        self.location_country = row[13]
                        self.location_tz = row[14]
                        self.first_name = row[15]
                        self.middle_name = row[16]
                        self.last_name = row[17]
                        self.preferred_name = row[18]
                        self.birthday = row[19]
                        self.age = row[20]

                        self.utc = row[21]
                        # self.birthday = row[22] DUPLICATE
                        self.email_verified = row[23]
                        self.phone_verified = row[24]
                        self.brands_ignored = json.loads(row[25]) if row[25] else {}
                        self.brands_favorite = json.loads(row[26]) if row[26] else {}
                        self.brands_requested = json.loads(row[27]) if row[27] else {}
                        self.stt_region = row[28]
                        self.alt_languages = row[29]
                        self.tts_secondary_gender = row[30]
                        self.secondary_neon_voice = row[31]
                        self.username = row[32]
                        self.phone = row[33]
                        # self.synonyms = json.loads(row[34])
                        LOG.info(row[35])
                        self.skill_settings = json.loads(row[35].strip('"')) if row[35] else {}
                        LOG.info(self.skill_settings)

        except Error as e:
            LOG.debug(f"Error while connecting to MySQL {e}")
        except Exception as e:
            LOG.debug("Mysql Error = " + str(e))
        finally:
            # closing database connection.
            if cursor and self.connection.is_connected():
                cursor.close()
                self.connection.close()
                LOG.debug("get_chat_user_info time: " + str(time() - start_time))
                LOG.debug("MySQL connection is closed")


class KlatUserDatabase:
    """
    Class to hold profile data for Klat users
    """
    def __init__(self):
        self.active_chat_users = {}

        bus = MessageBusClient()
        bus.on('neon.remove_cache_entry', self.remove_cached_profile)
        create_daemon(bus.run_forever)

    def get_profile(self, nick: str) -> dict:
        return self.active_chat_users.get(nick)

    @staticmethod
    def _build_entry_for_nick(nick: str) -> dict:
        """
        Builds a ChatUser object for the passed nick and loads those preferences into a user dict for use in Neon Core.
        :param nick: Klat nick to lookup
        :return: Dict of user preferences
        """
        chat_user = ChatUser(nick)
        try:
            LOG.debug(chat_user)
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
        """
        Called to get a user from the remote database and save their profile locally in active_chat_users
        :param nick: Klat nick to load
        """
        if nick not in self.active_chat_users:
            self.active_chat_users[nick] = self._build_entry_for_nick(nick)

    def get_nick_profiles(self, nicks: list) -> dict:
        """
        Ensures the passed list of user nicks are in active_chat_users and returns a dict of preferences for each nick
        :param nicks: list of nicks in conversation
        :return: dict of nicks: preferences
        """
        # nicks = self._get_nicks_for_shout_conversation(filename)
        # LOG.info('shout_id = '+str(shout_id))
        if not isinstance(nicks, list):
            raise TypeError("Expected list of nicks")
        nicks_in_conversation = dict()
        for nickname in nicks:
            if nickname == "neon":
                LOG.debug("Ignoring neon")
            elif nickname not in self.active_chat_users:
                self.update_profile_for_nick(nickname)
            nicks_in_conversation[nickname] = self.active_chat_users[nickname]
            LOG.info(nicks_in_conversation[nickname])
        return nicks_in_conversation

    def remove_cached_profile(self, message):
        """
        Handler to remove a cached nick profile when a profile is updated.
        This may be called when a skill or external source changes a user profile
        :param message: Message associated with request
        """
        # LOG.debug(f"DM: remove_cache_entry called message={message.data}")
        # LOG.debug(message.data)
        nick = message.data.get("nick", "")  # This IS data, not context
        if not nick:
            LOG.error("Invalid remove cache entry request")
            return
        LOG.debug(f"Removing cached nick: {nick}")
        self.active_chat_users.pop(nick)
