# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
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
"""Decorators for use with MycroftSkill methods"""
import time
import threading

from functools import wraps
from inspect import signature
from ovos_bus_client import Message
from ovos_utils import create_killable_daemon

from mycroft.skills.mycroft_skill.decorators import intent_handler, \
    intent_file_handler, resting_screen_handler, skill_api_method


class AbortEvent(StopIteration):
    """ abort bus event handler """


class AbortIntent(AbortEvent):
    """ abort intent parsing """


class AbortQuestion(AbortEvent):
    """ gracefully abort get_response queries """


def killable_intent(msg="mycroft.skills.abort_execution",
                    callback=None, react_to_stop=True, call_stop=True,
                    stop_tts=True):
    return killable_event(msg, AbortIntent, callback, react_to_stop,
                          call_stop, stop_tts)


def killable_event(msg="mycroft.skills.abort_execution", exc=AbortEvent,
                   callback=None, react_to_stop=False, call_stop=False,
                   stop_tts=False):
    # Begin wrapper
    def create_killable(func):

        @wraps(func)
        def call_function(*args, **kwargs):
            skill = args[0]
            t = create_killable_daemon(func, args, kwargs, autostart=False)

            def abort(_):
                if not t.is_alive():
                    return
                if stop_tts:
                    skill.bus.emit(Message("mycroft.audio.speech.stop"))
                if call_stop:
                    # call stop on parent skill
                    skill.stop()

                # ensure no orphan get_response daemons
                # this is the only killable daemon that core itself will
                # create, users should also account for this condition with
                # callbacks if using the decorator for other purposes
                skill._handle_killed_wait_response()
                try:
                    while t.is_alive():
                        t.raise_exc(exc)
                        time.sleep(0.1)
                except threading.ThreadError:
                    pass  # already killed
                except AssertionError:
                    pass  # could not determine thread id ?
                if callback is not None:
                    if len(signature(callback).parameters) == 1:
                        # class method, needs self
                        callback(args[0])
                    else:
                        callback()

            # save reference to threads so they can be killed later
            skill._threads.append(t)
            skill.bus.once(msg, abort)
            if react_to_stop:
                skill.bus.once(args[0].skill_id + ".stop", abort)
            t.start()
            return t

        return call_function

    return create_killable


def conversational_intent(intent_file):
    """Decorator for adding a method as an converse intent handler.
    NOTE: only padatious supported, not adapt
    """

    def real_decorator(func):
        # Store the intent_file inside the function
        # This will be used later to train intents
        if not hasattr(func, 'converse_intents'):
            func.converse_intents = []
        func.converse_intents.append(intent_file)
        return func

    return real_decorator
