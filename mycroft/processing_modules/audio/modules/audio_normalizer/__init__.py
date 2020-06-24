from mycroft.processing_modules.audio import AudioParser
from pydub import AudioSegment
import tempfile
from os.path import join
import time
from speech_recognition import AudioData


class AudioNormalizer(AudioParser):
    def __init__(self):
        super().__init__("audio_normalizer", 1)
        # silence_threshold in dB
        self.thresh = self.config.get("threshold", 10)
        # final volume  in dB
        self.final_db = self.config.get("final_volume", -18.0)

    def trim_silence(self, audio_data):
        if isinstance(audio_data, AudioData):
            audio_data = AudioSegment(
                data=audio_data.frame_data,
                sample_width=audio_data.sample_width,
                frame_rate=audio_data.sample_rate,
                channels=1

            )
        assert isinstance(audio_data, AudioSegment)
        start_trim = self.detect_leading_silence(audio_data,
                                                 audio_data.dBFS + self.thresh)
        end_trim = self.detect_leading_silence(audio_data.reverse(),
                                               audio_data.dBFS + self.thresh
                                               // 3)
        trimmed = audio_data[start_trim:-end_trim]
        if len(trimmed) >= 0.15 * len(audio_data):
            audio_data = trimmed
        if audio_data.dBFS != self.final_db:
            change_needed = self.final_db - audio_data.dBFS
            audio_data = audio_data.apply_gain(change_needed)

        filename = join(tempfile.gettempdir(), str(time.time()) + ".wav")
        audio_data.export(filename, format="wav")
        with open(filename, "rb") as byte_data:
            return AudioData(byte_data.read(),
                             audio_data.frame_rate,
                             audio_data.sample_width)

    @staticmethod
    def detect_leading_silence(sound, silence_threshold=-36.0, chunk_size=10):
        """
        sound is a pydub.AudioSegment
        silence_threshold in dB
        chunk_size in ms
        iterate over chunks until you find the first one with sound
        """
        trim_ms = 0  # ms
        assert chunk_size > 0  # to avoid infinite loop
        while sound[trim_ms:trim_ms + chunk_size].dBFS < silence_threshold \
                and trim_ms < len(sound):
            trim_ms += chunk_size
        return trim_ms

    def on_speech_end(self, audio_data):
        audio_data = self.trim_silence(audio_data)
        return audio_data, {}


def create_module():
    return AudioNormalizer()
