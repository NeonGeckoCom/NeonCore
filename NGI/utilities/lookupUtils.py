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

import os
from datetime import date


from mycroft.util import LOG


def get_coordinates(gps_loc):
    from geopy.geocoders import Nominatim
    coordinates = Nominatim(user_agent="neon-ai")
    try:
        location = coordinates.geocode(gps_loc)
        LOG.debug(f"{location}")
        return location.latitude, location.longitude
    except Exception as x:
        LOG.error(x)
        return -1, -1


# Accepts lat, lng string or float and returns str city, state, country
def get_location(lat, lng):
    from geopy.geocoders import Nominatim
    address = Nominatim(user_agent="neon-ai")
    location = address.reverse([lat, lng], language="en-US")
    LOG.debug(f"{location}")
    LOG.debug(f"{location.raw}")
    LOG.debug(f"{location.raw.get('address')}")
    city = location.raw.get('address').get('city')
    county = location.raw.get('address').get('county')
    state = location.raw.get('address').get('state')
    country = location.raw.get('address').get('country')
    return city, county, state, country


# Accepts str or float lat, lng and returns str timezone name, hours offset
def get_timezone(lat, lng):
    from timezonefinder import TimezoneFinder as Tf
    import pendulum
    timezone = Tf().timezone_at(lng=float(lng), lat=float(lat))
    offset = pendulum.from_timestamp(0, timezone).offset_hours
    return timezone, offset


# Accepts a timezone name and returns the hours offset
def get_offset(timezone):
    from pendulum import from_timestamp
    return from_timestamp(0, timezone).offset_hours


# Accepts str year, month, day and returns int age
def get_age(year, month='1', day='1'):
    # TODO: Update this to use the same method as personal skill DM
    age = date.today().year - int(year) - ((date.today().month, date.today().day) < (int(month), int(day)))
    return age


# Accepts str phrase and returns str phonemes
def get_phonemes(phrase):
    import nltk
    import re

    try:
        nltk.download('cmudict')
        output = ''
        for word in phrase.split():
            phoenemes = nltk.corpus.cmudict.dict()[word.lower()][0]

            for phoeneme in phoenemes:
                output += str(re.sub('[0-9]', '', phoeneme) + ' ')
            output += '. '
        return output.rstrip()
    except Exception as x:
        LOG.debug(x)
        nltk.download('cmudict')


# Returns Device MAC Address
def get_net_info():
    import netifaces
    default_dev = netifaces.gateways()['default'][netifaces.AF_INET][1]
    mac = netifaces.ifaddresses(default_dev)[netifaces.AF_LINK][0]['addr']
    ip4 = netifaces.ifaddresses(default_dev)[netifaces.AF_INET][0]['addr']
    ip6 = netifaces.ifaddresses(default_dev)[netifaces.AF_INET6][0]['addr']
    return ip4, ip6, mac


# Returns list of available script files
def get_scripts_list():
    from NGI.utilities.configHelper import NGIConfig

    cc_skill_dir = NGIConfig("ngi_local_conf").content["dirVars"]["skillsDir"] + "/custom-conversation.neon"
    available = [os.path.splitext(x)[0].replace("_", " ") for x in os.listdir(f'{cc_skill_dir}/script_txt/')
                 if os.path.isfile(os.path.join(f'{cc_skill_dir}/script_txt', x))]
    LOG.info(available)
    return available


# Encrypts Data
def encrypt(plaintext):
    from Crypto.Cipher import AES
    from NGI.utilities.configHelper import NGIConfig

    key = NGIConfig("ngi_local_conf").content['dirVars']['coreDir'].encode('utf-16')[0:32]
    cipher = AES.new(key, AES.MODE_EAX, key)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-16'))
    return ciphertext
    # print(key)
    # key = hashlib.sha256(key.encode('utf-8')).digest()
    # print(key)
    # pad = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16)
    # raw = pad(raw)
    # iv = Random.new().read(AES.block_size)
    # cipher = AES.new(key, AES.MODE_CBC, iv)
    # return base64.b64encode(iv + cipher.encrypt(raw.encode('utf-8')))


# Decrypts Data
def decrypt(encrypted_text):
    from Crypto.Cipher import AES
    from NGI.utilities.configHelper import NGIConfig

    key = NGIConfig("ngi_local_conf").content['dirVars']['coreDir'].encode('utf-16')[0:32]
    cipher = AES.new(key, AES.MODE_EAX, key)
    output = cipher.decrypt(encrypted_text)
    return output.decode('utf-16')