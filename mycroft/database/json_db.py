from mycroft.configuration import Configuration
from json_database import JsonDatabase
from mycroft.util.log import LOG
from mycroft.database.models import User


class JsonUserDatabase(JsonDatabase):
    def __init__(self):
        path = Configuration.get()["database"]["path"]
        super().__init__("users", path)

    def _get_user(self, user_id):
        search = self.search_by_value("user_id", user_id)
        user = None
        if len(search):
            user = search[0]
        return user

    def delete_user(self, user_id):
        user = self._get_user(user_id)
        if user:
            # item_id != user_id
            item_id = self.get_item_id(user)
            user = User(user_id, "Deleted_user")
            self.update_item(item_id, user)
            return True
        return False

    def get_user_by_id(self, user_id):
        user = self._get_user(user_id)
        if user:
            return User().from_dict(user)
        return None

    def get_users_by_name(self, name):
        users = self.search_by_value("name", name)
        return [User().from_dict(user) for user in users]

    def add_user(self, name, mail=None):
        user_id = self.total_users() + 1
        user = User(user_id, name)
        user.mail = mail
        self.add_item(user)
        return user

    def update_user(self, user):
        user_data = self._get_user(user.user_id)
        if user_data:
            # item_id != user_id
            item_id = self.get_item_id(user_data)
            self.update_item(item_id, user)
            return True
        return False

    def total_users(self):
        return len(self)

    def __enter__(self):
        """ Context handler """
        return self

    def __exit__(self, _type, value, traceback):
        """ Commits changes and Closes the session """
        try:
            self.commit()
        except Exception as e:
            LOG.error(e)

