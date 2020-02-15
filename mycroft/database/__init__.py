from mycroft.configuration import Configuration
from mycroft.util.log import LOG
from mycroft.database.models import User


DATABASE_PATH = Configuration.get()["database"]["path"]

if "sql" not in DATABASE_PATH.split(":/")[0]:
    from mycroft.database.json_db import JsonUserDatabase
    _clazz = JsonUserDatabase
else:
    # this is here mostly to support remote databases
    try:
        from mycroft.database.sql import SQLUserDatabase
        _clazz = SQLUserDatabase
    except ImportError:
        LOG.error("Run pip install sqlalchemy")
        raise


class UserDatabase(_clazz):
    # backend agnostic database with caching
    _user_cache = {}

    def get_user_by_id(self, user_id):
        # caching to save database queries
        if user_id in self._user_cache:
            return self._user_cache[user_id]
        user = super().get_user_by_id(user_id)
        if user:
            UserDatabase._user_cache[user_id] = user
        return user

    def update_user(self, user):
        updated = super().update_user(user)
        # save updated value in cache
        if updated:
            UserDatabase._user_cache[user.user_id] = user
        return updated

    def delete_user(self, user_id):
        deleted = super().delete_user(user_id)
        # update cache
        if deleted:
            UserDatabase._user_cache[user_id] = User(user_id, "Deleted_user")
        return deleted


def match_user(query_data, min_conf=0.85):
    # query_data is a dict, usually a message.context

    # TODO use all information to search the database
    # Criteria (WIP) this is a mock up
    score = 0
    # - user_id present
    score += 10
    # - face match (encodings)
    score += 50 * 0.8  # 0.8 is face_id match confidence
    # - voice match (encodings)
    score += 50 * 0.8  # 0.8 is voice_id match confidence
    # - face match (sample)
    score += 30 * 0.8  # 0.8 is face_id match confidence
    # - voice match (sample)
    score += 25 * 0.8  # 0.8 is voice_id match confidence
    # - name
    score += 25
    # - name (fuzzy_match)
    score += 15 * 0.65  # 0.65 is fuzzy_match confidence
    # - email
    score += 25
    # - nickname
    nicknames = ["username", "nicknames"]  # stuff extracted from query_data
    score += 10 * len(nicknames)
    # - other data
    for match in query_data.get("some_other_check", []):
        score += 5

    # TODO convert score into a 0 - 100 confidence
    conf = 0
    # TODO get User object
    user = None
    if conf >= min_conf:
        return user
    return None
