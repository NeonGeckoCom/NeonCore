# # NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
# # All trademark and other rights reserved by their respective owners
# # Copyright 2008-2021 Neongecko.com Inc.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import time
from threading import Lock
from uuid import uuid4

from mycroft.configuration import Configuration
from mycroft.util.log import LOG


class Session:
    """
    An class representing a Mycroft Session Identifier
    """

    def __init__(self, session_id, expiration_seconds=180):
        self.session_id = session_id
        self.touch_time = int(time.time())
        self.expiration_seconds = expiration_seconds

    def touch(self):
        """
        update the touch_time on the session

        :return:
        """
        self.touch_time = int(time.time())

    def expired(self):
        """
        determine if the session has expired

        :return:
        """
        return int(time.time()) - self.touch_time > self.expiration_seconds

    def __str__(self):
        return "{%s,%d}" % (str(self.session_id), self.touch_time)


class SessionManager:
    """ Keeps track of the current active session. """
    __current_session = None
    __lock = Lock()

    @staticmethod
    def get():
        """
        get the active session.

        :return: An active session
        """
        config = Configuration.get().get('session')

        with SessionManager.__lock:
            if (not SessionManager.__current_session or
                    SessionManager.__current_session.expired()):
                SessionManager.__current_session = Session(
                    str(uuid4()), expiration_seconds=config.get('ttl', 180))
                LOG.info(
                    "New Session Start: " +
                    SessionManager.__current_session.session_id)
            return SessionManager.__current_session

    @staticmethod
    def touch():
        """
        Update the last_touch timestamp on the current session

        :return: None
        """
        SessionManager.get().touch()
