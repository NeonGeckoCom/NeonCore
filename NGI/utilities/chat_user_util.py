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
from typing import Optional

from mycroft.util.log import LOG
import os
import json
from NGI.utilities.configHelper import NGIConfig as ngiConf
# from NGI.utilities.utilHelper import LookupHelpers
from neon_utils.location_utils import *
from time import time

import mysql.connector
from mysql.connector import Error


def neon_should_respond(message):
    """
    Determines if Neon should respond to an utterance passed from the chat server
    :param message: Message object associated with utterance
    :return boolean to respond or not
    """
    if not message.context.get("klat_data"):
        LOG.warning("Server function called on non-server")
        return True
    # filename = message.context.get("flac_filename", message.data.get("flac_filename"))
    # if filename:
    #     title = str(get_chat_conversation_title(filename))
    # else:
    #     title = None
    title = message.context.get("klat_data", {}).get("title")
    # LOG.debug(f"title={title}")
    # LOG.debug(f">>>data={message.data}")
    utterance = message.data.get("utterances", [""])[0].lower()
    if utterance.startswith("@") and not utterance.startswith("@neon"):
        # @user that isn't Neon
        return False
    elif message.data.get("Neon") or message.data.get("neon"):
        # User Said "Neon"
        return True
    elif "neon" in utterance:
        # String "neon" in the utterance
        return True
    elif "neon" in str(message.data.get("utterance")).lower():
        # String "neon" in the utterance
        LOG.warning("utterance passed instead of utterances")
        return True
    elif message.context.get("neon_should_respond", False):
        # Explicit execute line
        return True
    elif not title:
        LOG.error("null conversation title!")
        return True
    elif not title.startswith("!PRIVATE:"):
        # Public Conversation
        LOG.debug("DM: Public Conversation")
        return False
    elif title.startswith("!PRIVATE:"):
        # Private Conversation
        if ',' in title:
            users = title.split(':')[1].split(',')
            for idx, val in enumerate(users):
                users[idx] = val.strip()
            if len(users) == 2 and "Neon" in users:
                # Private with Neon
                # LOG.debug("DM: Private Conversation with Neon")
                return True
            else:
                # Private with Other Users
                LOG.debug("DM: Private Conversation with Others")
                return False
        else:
            # Solo Private
            # LOG.debug("DM: Private Conversation")
            return True


def get_chat_nickname_from_filename(filename):
    LOG.warning(f"This method is depreciated. Please get nick from message.context['klat_data']")
    filename = os.path.basename(filename)
    LOG.info(filename)
    file_parts = filename.split('-')
    LOG.info(f"nick =  {str(file_parts[3])}")
    return file_parts[3]


def get_response_filename(path: str) -> Optional[str]:
    """
    Gets the appropriate destination path for a server response.
    :param path: Desired output path
    :return: Validated output path to use
    """
    x = 1
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new_path = path
    while os.path.exists(new_path):
        parts = str(os.path.basename(new_path)).split('-')
        parts[0] = 'sid' + str(x)
        new_file_name = '-'.join(parts)
        new_path = os.path.join(os.path.dirname(new_path), new_file_name)
        x = x + 1
    return new_path


class ChatUser:
    def __init__(self, nickname, dicts_requested=('user', 'brands', 'speech', 'units', 'location'),
                 cache_locations=None):
        # TODO: This should probably use one self param per dict (user, brands, speech, units, location, skills DM

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
