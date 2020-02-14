"""
All database implementations should return and accept these as input
These classes will be used all over the mycroft code base
"""
import json


class User:
    def __init__(self, user_id=-1, name=None):
        # internal
        self.user_id = user_id  # -1 is a unknown user
        self.is_admin = False
        #
        self.name = name or "user:" + str(user_id)
        self.mail = None
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
