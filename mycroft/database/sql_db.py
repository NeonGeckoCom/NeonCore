from sqlalchemy import Column, Text, String, Integer, create_engine, Boolean
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import json
from mycroft.util.log import LOG
from mycroft.configuration import Configuration
from mycroft.database.models import User

Base = declarative_base()


def _model_to_dict(obj):
    serialized_data = {c.key: getattr(obj, c.key) for c in obj.__table__.columns}
    return serialized_data


def _props(cls):
    return [i for i in cls.__dict__.keys() if i[:1] != '_']


class _User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    is_admin = Column(Boolean, default=False)
    name = Column(String)
    mail = Column(String)
    last_seen = Column(Integer, default=-1)
    voice_encoding = Column(String)
    voice_sample = Column(String)
    face_encoding = Column(String)
    face_sample = Column(String)
    data = Column(Text)  # saved as json string


class SQLUserDatabase:
    def __init__(self, debug=False, session=None):
        path = Configuration.get()["database"]["path"]
        self.db = create_engine(path)
        self.db.echo = debug
        if session:
            self.session = session
        else:
            Session = sessionmaker(bind=self.db)
            self.session = Session()
        Base.metadata.create_all(self.db)

    def delete_user(self, user_id):
        user = self.session.query(_User).filter_by(user_id=user_id).first()
        if user:
            self.session.delete(user)
            return True
        return False

    def get_user_by_id(self, user_id):
        user = self.session.query(_User).filter_by(user_id=user_id).first()
        if not user:
            return None
        data = _model_to_dict(user)
        return User().from_dict(data)

    def get_users_by_name(self, name):
        users = self.session.query(_User).filter_by(name=name).all()
        user_data = [_model_to_dict(u) for u in users]
        return [User().from_dict(u) for u in user_data]

    def add_user(self, name=None):
        user = _User(name=name,
                     user_id=self.total_users() + 1)
        self.session.add(user)
        user_data = _model_to_dict(user)
        return User().from_dict(user_data)

    def update_user(self, user):
        _user = self.session.query(_User).filter_by(
            user_id=user.user_id).first()
        if not _user:
            return False
        _user.is_admin = user.is_admin
        _user.name = user.name
        _user.mail = user.mail
        _user.last_seen = user.last_seen
        _user.voice_sample = user.voice_sample
        _user.voice_encoding = user.voice_encoding
        _user.face_sample = user.face_sample
        _user.face_encoding = user.face_encoding
        _user.data = json.dumps(user.data)

    def total_users(self):
        return self.session.query(_User).count()

    def commit(self):
        try:
            self.session.commit()
            return True
        except IntegrityError:
            self.session.rollback()
        return False

    def close(self):
        self.session.close()

    def __enter__(self):
        """ Context handler """
        return self

    def __exit__(self, _type, value, traceback):
        """ Commits changes and Closes the session """
        try:
            self.commit()
        except Exception as e:
            LOG.error(e)
        finally:
            self.close()

