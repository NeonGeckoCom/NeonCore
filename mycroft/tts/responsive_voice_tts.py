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
import requests
from mycroft.tts import TTS, TTSValidator
from mycroft.util.log import LOG


class ResponsiveVoiceTTS(TTS):
    def __init__(self, lang, config):
        super().__init__(
            lang, config, ResponsiveVoiceValidator(self), 'mp3',
            ssml_tags=[]
        )
        from responsive_voice import get_voice, ResponsiveVoice

        self.pitch = config.get("pitch", 0.5)
        self.rate = config.get("rate", 0.5)
        self.vol = config.get("vol", 1)
        if "f" in config.get("gender", ""):
            self.gender = ResponsiveVoice.FEMALE
        if "m" in config.get("gender", ""):
            self.gender = ResponsiveVoice.MALE
        else:
            self.gender = ResponsiveVoice.UNKNOWN_GENDER
        self.voice = config.get("voice")
        if not self.voice:
            self.engine = ResponsiveVoice(lang=self.lang,
                                          pitch=self.pitch,
                                          rate=self.rate,
                                          vol=self.vol,
                                          gender=self.gender)
        else:
            Voice = get_voice(self.voice, self.lang)
            if not Voice:
                # dont filter by language
                Voice = get_voice(self.voice)
            if not Voice:
                raise
            self.engine = Voice(pitch=self.pitch,
                                rate=self.rate,
                                vol=self.vol)

    def get_tts(self, sentence, wav_file):
        self.engine.get_mp3(sentence, wav_file)
        return wav_file, None


class ResponsiveVoiceValidator(TTSValidator):
    def __init__(self, tts):
        super(ResponsiveVoiceValidator, self).__init__(tts)

    def validate_dependencies(self):
        try:
            import responsive_voice
        except:
            LOG.error("Run pip install ResponsiveVoice")
            raise

    def validate_lang(self):
        # TODO: Verify responsive voice can handle the requested language
        pass

    def validate_connection(self):
        r = requests.get("http://responsivevoice.org")
        if r.status_code == 200:
            return True
        raise AssertionError("Could not reach http://responsivevoice.org")

    def get_tts_class(self):
        return ResponsiveVoiceTTS
