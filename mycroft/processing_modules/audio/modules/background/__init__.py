from mycroft.processing_modules.audio import AudioParser
import audioop
from math import log10


class BackgroundNoise(AudioParser):
    def __init__(self):
        super().__init__("background_noise", 10)
        self._audio = None
        self._prediction = None
        self._buffer_size = 5  # seconds

    @staticmethod
    def seconds_to_size(seconds):
        # 1 seconds of audio.frame_data = 44032
        return int(seconds * 44032)

    def on_audio(self, audio_data):
        max_size = self.seconds_to_size(self._buffer_size)
        if self._audio:
            self._audio.frame_data += audio_data.frame_data
        else:
            self._audio = audio_data
        if len(self._audio.frame_data) > max_size:
            self._audio.frame_data = self._audio.frame_data[-max_size:]

    def noise_level(self):
        # NOTE: on_audio will usually include a partial wake word at the end,
        # discard the last ~0.7 seconds of audio
        audio = self._audio.frame_data[:-self.seconds_to_size(0.7)]
        rms = audioop.rms(audio, 2)
        decibel = 20 * log10(rms)
        return decibel

    def on_hotword(self, audio_data):
        # In here we can run predictions, for example classify the
        # background noise, or save the audio and if STT fails we can
        # then perform STT to enable things like "tell me a joke, Neon"
        self._prediction = self.noise_level()

        self._audio = None

    def on_speech_end(self, audio_data):
        return audio_data, {"noise_level": self._prediction}


def create_module():
    return BackgroundNoise()

