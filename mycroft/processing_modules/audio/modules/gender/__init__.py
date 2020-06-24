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

    def on_speech_end(self, audio_data):
        wav_data = audio_data.get_wav_data()
        temp = join(tempfile.gettempdir(), str(time.time()) + ".wav")
        with open(temp, "wb") as f:
            f.write(wav_data)
        gender = GenderClassifier.predict(temp)
        return audio_data, {"user": {"gender": gender}}


def create_module():
    return Gender()
