"""
All database implementations should return and accept these as input
These classes will be used all over the mycroft code base
"""
import json
import datetime
from jarbas_utils.location import geolocate, reverse_geolocate, get_timezone
from dateutil.tz import gettz, tzlocal


class Location:
    def __init__(self, lat=38.971669, lon=-95.23525):
        self.latitude = lat
        self.longitude = lon
        # everything is automatically derived from lat/lon
        # this ensures location is not ambiguous
        self._address = None
        self._timezone_code = None
        self._city = None
        self._state = None
        self._country = None
        self._country_code = None

    @property
    def timezone_code(self):
        if self._timezone_code is None:
            self._timezone_code = get_timezone(self.latitude, self.longitude)
        return self._timezone_code

    @property
    def timezone(self):
        if self.timezone_code:
            return gettz(self.timezone_code)
        return tzlocal()

    @property
    def current_time(self):
        return datetime.datetime.now(self.timezone)

    @property
    def address(self):
        if not self._address:
            if not self._city or not self._country:
                self._reverse_geolocate()
            self._address = self._city
            if self._state:
                self._address += ", " + self._state
            if self._country:
                self._address += ", " + self._country
        return self._address

    @property
    def city(self):
        if not self._city:
            self._reverse_geolocate()
        return self._city

    @property
    def state(self):
        if not self._state:
            self._reverse_geolocate()
        return self._state

    @property
    def country(self):
        if not self._country:
            self._reverse_geolocate()
        return self._country

    @property
    def country_code(self):
        if not self._country_code:
            self._reverse_geolocate()
        return self._country_code

    def _reverse_geolocate(self):
        data = reverse_geolocate(self.latitude, self.longitude)
        self.from_dict(data)
        return self

    def from_address(self, address):
        data = geolocate(address)
        self.from_dict(data)
        self._address = address
        return self

    def from_dict(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        self.latitude = data["coordinate"]["latitude"]
        self.longitude = data["coordinate"]["longitude"]
        self._city = data["city"]["name"]
        self._state = data["city"]["state"].get("name")
        self._country = data["city"]["state"]["country"]["name"]
        self._timezone_code = data.get("timezone", {}).get("name")
        self._address = data.get("address")
        return self

    def as_dict(self):
        return {
            "city": {
                "name": self.city,
                "state": {
                    "name": self.state,
                    "country": {
                        "code": self.country_code,
                        "name": self.country
                    }
                }
            },
            "coordinate": {
                "latitude": self.latitude,
                "longitude": self.longitude
            },
            "timezone": {
                "name": self.timezone_code
            },
            "address": self.address
        }


class User:
    def __init__(self, user_id=-1, name=None):
        # internal
        self.user_id = user_id  # -1 is a unknown user
        self.is_admin = False
        self.name = name or "user:" + str(user_id)
        self.mail = None
        self.languages = ["en"]  # by order of preference
        self.location = None
        # metrics
        self.last_seen = - 1  # unix timestamp, -1 means never
        # biometrics data
        # NOTE: most of this is expected to be implemented in the future and
        # currently useless
        self.voice_encoding = None  # path to saved voice print
        self.voice_sample = None  # path to a .wav file
        self.face_encoding = None  # path to a saved face encoding
        self.face_sample = None  # path to a reference picture

        # arbitrary user data, you can store anything here
        # things like nicknames, TTS/STT preferences and so on
        self.data = {}

        # user.data = {
        #     "first_name": "Jon",
        #     "middle_name": "Something",
        #     "last_name": "Doe",
        #     "nicknames": ["Dude", "FuriousBadger"],
        #     "birthday": "YYYY/MM/DD",
        #     "about": "very nice user, likes cookies",
        #     "phone": "666",
        #     "avatar": "human.jpg"
        # }

        self.preferences = {}

        # user.preferences = {
        #     "name": "Master",
        #     "units": "metric",
        #     "date_format": "DD/MM/YYYY",
        #     "time_format": 24,
        #     "tts": {"gender": "female", "voice": "Joanna"},
        #     "stt": {"lang": "en", "region": "US"},
        #     "brands": {"favorite": [], "ignored": []},
        #     "synonyms": {"a": "means b"}
        # }

        self.auth = {}

        # user.auth = {
        #     "phone_verified": False,
        #     "email_verified": True,
        #     "key": "SecretUsedForAuthentication",
        #     "secret_phrase": "Tell me your secret phrase vocal interaction / password recovery",
        #     "HiveMind": "api_key",
        #     "blacklisted_skills": []
        # }

    @property
    def blacklisted_skills(self):
        return self.auth.get("blacklisted_skills", [])

    @property
    def blacklisted_skills(self):
        return self.auth.get("blacklisted_skills", [])

    @property
    def age(self):
        # returns a datetime.timedelta object
        bday = self.data.get("birthday") or \
               self.data.get("dob") or \
               self.data.get("bday")
        if not bday:
            age = self.data.get("age")
            if age:
                return datetime.timedelta(days=365 * age)
            return None  # None means unknown
        y, m, d = bday.splt("/")
        now = datetime.datetime.now()
        bday = datetime.datetime(year=y, month=m, day=d)
        delta = now - bday
        return delta

    def from_dict(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        if data.get("location") is not None:
            self.location = Location().from_dict(data["location"])
        for key in data:
            self.__setattr__(key, data[key])
        return self

    def as_dict(self):
        data = self.__dict__
        if self.location:
            data["location"] = self.location.as_dict()
        return data

    def update_from_dict(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        for key in data:
            if data.get(key) is not None:
                self.__setattr__(key, data[key])


if __name__ == "__main__":
    from pprint import pprint
    loc = Location()
    pprint(loc.as_dict())

    # useful properties
    print(loc.timezone)  # timezone object
    print(loc.current_time)  # timezone aware datetime object

