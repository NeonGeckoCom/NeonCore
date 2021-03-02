import datetime
import os
from pprint import pformat
from time import time
from mycroft_bus_client import MessageBusClient, Message

from mycroft.audio import is_speaking
from mycroft.util import create_daemon, LOG
from threading import Event
from time import sleep


IDENT = None
HANDLED = Event()
SESSION = "test"
LAST_REQUEST = ""
results = []


def handle_speech_end(_):
    if not results:
        return
    if HANDLED.set() or not results[-1].get("speech_start"):
        LOG.info(f"Extra response!")
        return
    speak_time = time() - results[-1].pop("speech_start")
    results[-1]["speech_time"] = speak_time
    HANDLED.set()


def handle_neon_metric(message):
    if message.data.get("name") == "failed-intent" and \
            message.data.get("utterance").replace(" ", "") == LAST_REQUEST.replace(" ", ""):
        LOG.error(f"ERROR! ({LAST_REQUEST})")
        results.append({"ident": IDENT,
                        "error": True,
                        "response": None,
                        "request": LAST_REQUEST,
                        "failure_type": "Failed Intent"
                        })
        HANDLED.set()
    elif message.data.get("name") == "audio-response":
        times = message.context.get("timing")
        times["speech_start"] = time()
        transcribe_time = times['transcribed'] - times['emit']
        intent_time = times.get('processed', 0) - times['transcribed']
        synthesis_time = times['speech_start'] - times.get('processed', 0)
        total_time = times['speech_start'] - times['emit']

        results.append({"ident": message.context.get("ident"),
                        "error": False,
                        "response": "PLAYBACK",
                        "request": LAST_REQUEST,
                        "transcribe_time": transcribe_time,
                        "intent_time": intent_time,
                        "synthesis_time": synthesis_time,
                        "total_time": total_time,
                        "speech_start": times["speech_start"]})
        LOG.debug(f"Response! (Audio)")
        HANDLED.set()
    # type": "neon.metric", "data": {"utterance": "neon cancel all alarms", "device": "generic", "name": "failed-intent"


def handle_response(message):
    if message.context.get("ident") == IDENT:
        times = message.context.get("timing")
        transcribe_time = times['transcribed'] - times['emit']
        intent_time = times.get('processed', 0) - times['transcribed']
        synthesis_time = times['speech_start'] - times.get('processed', 0)
        total_time = times['speech_start'] - times['emit']
        if "error" in message.data["utterance"].lower():
            error = True
        else:
            error = False
        results.append({"ident": message.context.get("ident"),
                        "error": error,
                        "response": message.data["utterance"],
                        "request": LAST_REQUEST,
                        "transcribe_time": transcribe_time,
                        "intent_time": intent_time,
                        "synthesis_time": synthesis_time,
                        "total_time": total_time,
                        "speech_start": times["speech_start"]})
        LOG.debug(f"Response! ({LAST_REQUEST}) (error={error})")


def emit_utterance(utterance, ident):
    data = {
        'utterances': [utterance],
        'lang': 'en-US',
        'session': SESSION
    }
    context = {'client_name': 'neon_gui',
               "ident": ident,
               'source': 'testrunner',
               'destination': ["skills"],
               "audio_parser_data": {},
               "mobile": False,
               "client": "tester",
               "neon_should_respond": True,
               "nick_profiles": {},
               "timing": {"emit": time()}
               }

    bus.emit(Message("recognizer_loop:utterance", data, context))


def run_text_tests(test_sets: list):
    global IDENT, LAST_REQUEST
    tests_dir = os.path.dirname(__file__)
    tests = []
    for test_set in test_sets:
        subset_tests = os.listdir(os.path.join(tests_dir, test_set))
        subset_tests.sort()
        subset_tests = [test[2:-4].strip() for test in subset_tests]
        tests.extend(subset_tests)
    LOG.debug(tests)
    # TODO: Audio tests (play into listener?)
    for test_utterance in tests:
        IDENT = time()
        HANDLED.clear()
        LAST_REQUEST = test_utterance
        emit_utterance(test_utterance, IDENT)
        HANDLED.wait(30)  # TODO: Handle audio playback (no speech)
        if not HANDLED.is_set():
            if results[-1].get("ident") == IDENT:
                LOG.warning(f"No audio with previous request ({LAST_REQUEST})")
            else:
                LOG.warning(f"No response! ({LAST_REQUEST})")
                results.append({"ident": IDENT,
                                "error": True,
                                "response": "ERROR",
                                "request": LAST_REQUEST,
                                "failure_type": "Timeout"})
        else:
            sleep(2)
        while is_speaking():
            sleep(0.5)


def run_audio_tests(test_sets: list):
    global IDENT, LAST_REQUEST
    tests_dir = os.path.dirname(__file__)
    tests = []
    for test_set in test_sets:
        subset_tests = os.listdir(os.path.join(tests_dir, test_set))
        subset_tests = [os.path.join(tests_dir, test_set, filename) for filename in subset_tests]
        subset_tests.sort()
        tests.extend(subset_tests)
    LOG.debug(tests)
    for test_utterance in tests:
        IDENT = time()
        HANDLED.clear()
        LAST_REQUEST = test_utterance
        # TODO: Handle audio playback (no speech)
        HANDLED.wait(30)
        if not HANDLED.is_set():
            if results[-1].get("ident") == IDENT:
                LOG.warning(f"No audio with previous request ({LAST_REQUEST})")
            else:
                LOG.warning(f"No response! ({LAST_REQUEST})")
                results.append({"ident": IDENT,
                                "error": True,
                                "response": "ERROR",
                                "request": LAST_REQUEST,
                                "failure_type": "Timeout"})
        else:
            sleep(2)
        while is_speaking():
            sleep(0.5)


if __name__ == "__main__":
    bus = MessageBusClient()
    bus.on("speak", handle_response)
    bus.on("recognizer_loop:audio_output_end", handle_speech_end)
    bus.on("neon.metric", handle_neon_metric)

    create_daemon(bus.run_forever)
    start_time = time()
    run_text_tests(["brandsTests", "userTests", "systemTests"])
    run_time = str(datetime.timedelta(seconds=(time() - start_time)))
    LOG.info(run_time)
    LOG.info(pformat(results))
    for result in results:
        if result["error"]:
            LOG.error(pformat(result))
