from mycroft.util.log import LOG
from mycroft.processing_modules.audio import AudioParser
import tempfile
from os.path import join
import time
try:
    from voice_gender import GenderClassifier
except ImportError:
    # NOTE this is just for testing, accuracy for this SUCKS
    LOG.error("Run pip install voice_gender")
    raise


class Gender(AudioParser):
    def __init__(self):
        super().__init__("gender", 10)
        self._audio = None

    def on_hotword(self, audio_data):
        self._audio = audio_data

    def on_speech(self, audio_data):
        self._audio.frame_data += audio_data.frame_data

    def on_speech_end(self):
        wav_data = self._audio.get_wav_data()
        temp = join(tempfile.gettempdir(), str(time.time()) + ".wav")
        with open(temp, "wb") as f:
            f.write(wav_data)
        gender = GenderClassifier.predict(temp)
        self._audio = None
        return {"user": {"gender": gender}}


def create_module():
    return Gender()
