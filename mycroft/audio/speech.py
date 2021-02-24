# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import re
import time
from threading import Lock

from mycroft.configuration import Configuration
from mycroft.metrics import report_timing, Stopwatch
from mycroft.tts import TTSFactory
from mycroft.util import check_for_signal
from mycroft.util.log import LOG
from mycroft.messagebus.message import Message
from mycroft.tts.remote_tts import RemoteTTSTimeoutException
from mycroft.tts.mimic_tts import Mimic

bus = None  # Mycroft messagebus connection
config = None
tts = None
tts_hash = None
lock = Lock()
mimic_fallback_obj = None
speak_muted = False

_last_stop_signal = 0


def handle_unmute_tts(event):
    """ enable tts execution """
    global speak_muted
    speak_muted = False
    bus.emit(Message("mycroft.tts.mute_status", {"muted": speak_muted}))


def handle_mute_tts(event):
    """ disable tts execution """
    global speak_muted
    speak_muted = True
    bus.emit(Message("mycroft.tts.mute_status", {"muted": speak_muted}))


def handle_mute_status(event):
    """ emit tts mute status to bus """
    bus.emit(Message("mycroft.tts.mute_status", {"muted": speak_muted}))


def handle_speak(event):
    """Handle "speak" message

    Parse sentences and invoke text to speech service.
    """
    Configuration.set_config_update_handlers(bus)
    global _last_stop_signal

    event.context = event.context or {}

    # if the message is targeted and audio is not the target don't
    # don't synthezise speech
    if 'audio' not in event.context.get('destination', []):
        return

    # Get conversation ID
    event.context['ident'] = event.context.get("ident", "unknown")

    with lock:
        stopwatch = Stopwatch()
        stopwatch.start()
        utterance = event.data['utterance']
        mute_and_speak(utterance, event)
        stopwatch.stop()
    report_timing(event.context['ident'], 'speech', stopwatch,
                  {'utterance': utterance, 'tts': tts.__class__.__name__})


def mute_and_speak(utterance, event):
    """Mute mic and start speaking the utterance using selected tts backend.

    Arguments:
        utterance:  The sentence to be spoken
        ident:      Ident tying the utterance to the source query
    """
    global tts_hash, speak_muted
    LOG.info("Speak: " + utterance)
    if speak_muted:
        LOG.warning("Tried to speak, but TTS is muted!")
        return

    listen = event.data.get('expect_response', False)

    # update TTS object if configuration has changed
    if tts_hash != hash(str(config.get('tts', ''))):
        global tts
        # Stop tts playback thread
        tts.playback.stop()
        tts.playback.join()
        # Create new tts instance
        tts = TTSFactory.create()
        tts.init(bus)
        tts_hash = hash(str(config.get('tts', '')))


    try:
        tts.execute(utterance, event.context['ident'], listen, event)
    except RemoteTTSTimeoutException as e:
        LOG.error(e)
        mimic_fallback_tts(utterance, event.context['ident'], event)
    except Exception as e:
        LOG.error('TTS execution failed ({})'.format(repr(e)))


def mimic_fallback_tts(utterance, ident, event=None):
    global mimic_fallback_obj
    # fallback if connection is lost
    config = Configuration.get()
    tts_config = config.get('tts', {}).get("mimic", {})
    lang = config.get("lang", "en-us")
    if not mimic_fallback_obj:
        mimic_fallback_obj = Mimic(lang, tts_config)
    tts = mimic_fallback_obj
    LOG.debug("Mimic fallback, utterance : " + str(utterance))
    tts.init(bus)
    tts.execute(utterance, ident, message=event)


def handle_stop(event):
    """Handle stop message.

    Shutdown any speech.
    """
    global _last_stop_signal
    if check_for_signal("isSpeaking", -1):
        _last_stop_signal = time.time()
        tts.playback.clear()  # Clear here to get instant stop
        bus.emit(Message("mycroft.stop.handled", {"by": "TTS"}))


def init(messagebus):
    """Start speech related handlers.

    Arguments:
        messagebus: Connection to the Mycroft messagebus
    """

    global bus
    global tts
    global tts_hash
    global config

    bus = messagebus
    Configuration.set_config_update_handlers(bus)
    config = Configuration.get()
    bus.on('mycroft.stop', handle_stop)
    bus.on('mycroft.audio.speech.stop', handle_stop)
    bus.on('speak', handle_speak)
    bus.on('mycroft.tts.mute', handle_mute_tts)
    bus.on('mycroft.tts.unmute', handle_unmute_tts)
    bus.on('mycroft.tts.mute_status.request', handle_mute_status)

    tts = TTSFactory.create()
    tts.init(bus)
    tts_hash = hash(str(config.get('tts', '')))


def shutdown():
    """Shutdown the audio service cleanly.

    Stop any playing audio and make sure threads are joined correctly.
    """
    if tts:
        tts.playback.stop()
        tts.playback.join()
    if mimic_fallback_obj:
        mimic_fallback_obj.playback.stop()
        mimic_fallback_obj.playback.join()
