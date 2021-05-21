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
import boto3
from neon_core.tts import TTS, TTSValidator
from neon_core.configuration import Configuration


class PollyTTS(TTS):

    def __init__(self, lang="en-us", config=None):
        config = config or Configuration.get().get("tts", {}).get("polly", {})
        super(PollyTTS, self).__init__(lang, config, PollyTTSValidator(self),
                                       audio_ext="mp3",
                                       ssml_tags=["speak", "say-as", "voice",
                                                  "prosody", "break",
                                                  "emphasis", "sub", "lang",
                                                  "phoneme", "w", "whisper",
                                                  "amazon:auto-breaths",
                                                  "p", "s", "amazon:effect",
                                                  "mark"])

        self.voice = self.config.get("voice", "Matthew")
        self.key_id = self.config.get("key_id", '')
        self.key = self.config.get("secret_key", '')
        self.region = self.config.get("region", 'us-east-1')

        if self.keys.get("polly"):
            self.key_id = self.keys["polly"].get("key_id") or self.key_id
            self.key = self.keys["polly"].get("secret_key") or self.key
            self.region = self.keys["polly"].get("region") or self.region
            self.voice = self.keys["polly"].get("voice") or self.voice
        # these checks are separate in case we want to use different keys for the translate api for example
        elif self.keys.get("amazon"):
            self.key_id = self.keys["amazon"].get("key_id") or self.key_id
            self.key = self.keys["amazon"].get("secret_key") or self.key
            self.region = self.keys["amazon"].get("region") or self.region
            self.voice = self.keys["amazon"].get("voice") or self.voice

        self.polly = boto3.Session(aws_access_key_id=self.key_id,
                                   aws_secret_access_key=self.key,
                                   region_name=self.region).client('polly')

    def get_tts(self, sentence, wav_file):
        text_type = "text"
        if self.remove_ssml(sentence) != sentence:
            text_type = "ssml"
            sentence = sentence.replace("\whispered", "/amazon:effect") \
                .replace("\\whispered", "/amazon:effect") \
                .replace("whispered", "amazon:effect name=\"whispered\"")
        response = self.polly.synthesize_speech(
            OutputFormat=self.audio_ext,
            Text=sentence,
            TextType=text_type,
            VoiceId=self.voice)

        with open(wav_file, 'wb') as f:
            f.write(response['AudioStream'].read())
        return (wav_file, None)  # No phonemes

    def describe_voices(self, language_code="en-US"):
        if language_code.islower():
            a, b = language_code.split("-")
            b = b.upper()
            language_code = "-".join([a, b])
        # example 'it-IT' useful to retrieve voices
        voices = self.polly.describe_voices(LanguageCode=language_code)

        return voices


class PollyTTSValidator(TTSValidator):
    def __init__(self, tts):
        super(PollyTTSValidator, self).__init__(tts)

    def validate_lang(self):
        # TODO
        pass

    def validate_dependencies(self):
        try:
            from boto3 import Session
        except ImportError:
            raise Exception(
                'PollyTTS dependencies not installed, please run pip install '
                'boto3 ')

    def validate_connection(self):
        try:
            if not self.tts.voice:
                raise Exception("Polly TTS Voice not configured")
            output = self.tts.describe_voices()
        except TypeError:
            raise Exception(
                'PollyTTS server could not be verified. Please check your '
                'internet connection and credentials.')

    def get_tts_class(self):
        return PollyTTS


if __name__ == "__main__":
    e = PollyTTS()
    ssml = """<speak>
     This is my original voice, without any modifications. <amazon:effect vocal-tract-length="+15%"> 
     Now, imagine that I am much bigger. </amazon:effect> <amazon:effect vocal-tract-length="-15%"> 
     Or, perhaps you prefer my voice when I'm very small. </amazon:effect> You can also control the 
     timbre of my voice by making minor adjustments. <amazon:effect vocal-tract-length="+10%"> 
     For example, by making me sound just a little bigger. </amazon:effect><amazon:effect 
     vocal-tract-length="-10%"> Or, making me sound only somewhat smaller. </amazon:effect> 
</speak>"""
    e.get_tts(ssml, "polly.mp3")
