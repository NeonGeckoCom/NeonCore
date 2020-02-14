"""
All database implementations should return and accept these as input
These classes will be used all over the mycroft code base
"""
import json
import datetime
from dateutil.tz import gettz, tzlocal


class Location:
    def __init__(self, name, lat, lon):
        self.name = name  # a human name, can be a city or something like "home"
        self.latitude = lat
        self.longitude = lon
        self._address = None
        self._timezone_code = None #
        # everything else is derived from lat/lon

    @property
    def timezone(self):
        if self._timezone_code:
            return gettz(self._timezone_code)
        # TODO geolocation
        from_lat_lon = tzlocal()
        return from_lat_lon or tzlocal()

    @property
    def current_time(self):
        return datetime.datetime.now(self.timezone)

    @property
    def address(self):
        return self._address or self.reverse_geolocate()

    def reverse_geolocate(self):
        # TODO geolocation
        return "address from lat/lon"

    def from_dict(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        self.name = data["name"]
        self.latitude = data["latitude"]
        self.longitude = data["longitude"]
        self._address = data.get("address") or self._address
        self._timezone_code = data.get("timezone_code") or self._timezone_code
        return self

    def as_dict(self):
        return self.__dict__


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
        self.preferences = {}
        self.auth = {}

    @property
    def age(self):
        # returns a datetime.timedelta object
        bday = self.data.get("birthday") or self.data.get("bday")
        if not bday:
            age = self.data.get("age")
            if age:
                return datetime.timedelta(days=365*age)
            return None  # None means unknown
        y, m, d = bday.splt("/")
        now = datetime.datetime.now()
        bday = datetime.datetime(year=y, month=m, day=d)
        delta = now - bday
        return delta

    def from_dict(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        for key in data:
            self.__setattr__(key, data[key])
        return self

    def as_dict(self):
        return self.__dict__

    def update_from_dict(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        for key in data:
            if data.get(key) is not None:
                self.__setattr__(key, data[key])
