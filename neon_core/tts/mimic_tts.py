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
import os
import stat
import subprocess
from threading import Thread
from time import time, sleep

import os.path
from os.path import exists, join, expanduser

from mycroft import MYCROFT_ROOT_PATH
from mycroft.api import DeviceApi
from mycroft.configuration import Configuration
from mycroft.tts import TTS, TTSValidator
from mycroft.util.download import download
from mycroft.util.log import LOG

config = Configuration.get().get("tts").get("mimic")
data_dir = expanduser(Configuration.get()['data_dir'])

BIN = config.get("path",
                 os.path.join(MYCROFT_ROOT_PATH, 'mimic', 'bin', 'mimic'))

if not os.path.isfile(BIN):
    # Search for mimic on the path
    import distutils.spawn

    BIN = distutils.spawn.find_executable("mimic")

SUBSCRIBER_VOICES = {'trinity': join(data_dir, 'voices/mimic_tn')}


def download_subscriber_voices(selected_voice):
    """
        Function to download all premium voices, starting with
        the currently selected if applicable
    """

    def make_executable(dest):
        """ Call back function to make the downloaded file executable. """
        LOG.info('Make executable')
        # make executable
        st = os.stat(dest)
        os.chmod(dest, st.st_mode | stat.S_IEXEC)

    # First download the selected voice if needed
    voice_file = SUBSCRIBER_VOICES.get(selected_voice)
    if voice_file is not None and not exists(voice_file):
        LOG.info('voice doesn\'t exist, downloading')
        url = DeviceApi().get_subscriber_voice_url(selected_voice)
        # Check we got an url
        if url:
            dl = download(url, voice_file, make_executable)
            # Wait for completion
            while not dl.done:
                sleep(1)
        else:
            LOG.debug('{} is not available for this architecture'
                      .format(selected_voice))

    # Download the rest of the subsciber voices as needed
    for voice in SUBSCRIBER_VOICES:
        voice_file = SUBSCRIBER_VOICES[voice]
        if not exists(voice_file):
            url = DeviceApi().get_subscriber_voice_url(voice)
            # Check we got an url
            if url:
                dl = download(url, voice_file, make_executable)
                # Wait for completion
                while not dl.done:
                    sleep(1)
            else:
                LOG.debug('{} is not available for this architecture'
                          .format(voice))


class Mimic(TTS):
    def __init__(self, lang, config):
        super(Mimic, self).__init__(
            lang, config, MimicValidator(self), 'wav',
            ssml_tags=["speak", "ssml", "phoneme", "voice", "audio", "prosody"]
        )
        self.dl = None
        self.clear_cache()

        # Download subscriber voices if needed
        self.is_subscriber = DeviceApi().is_subscriber
        if self.is_subscriber:
            t = Thread(target=download_subscriber_voices, args=[self.voice])
            t.daemon = True
            t.start()

    def modify_tag(self, tag):
        for key, value in [
            ('x-slow', '0.4'),
            ('slow', '0.7'),
            ('medium', '1.0'),
            ('high', '1.3'),
            ('x-high', '1.6'),
            ('speed', 'rate')
        ]:
            tag = tag.replace(key, value)
        return tag

    @property
    def args(self):
        """ Build mimic arguments. """
        if (self.voice in SUBSCRIBER_VOICES and
                exists(SUBSCRIBER_VOICES[self.voice]) and self.is_subscriber):
            # Use subscriber voice
            mimic_bin = SUBSCRIBER_VOICES[self.voice]
            voice = self.voice
        elif self.voice in SUBSCRIBER_VOICES:
            # Premium voice but bin doesn't exist, use ap while downloading
            mimic_bin = BIN
            voice = 'ap'
        else:
            # Normal case use normal binary and selected voice
            mimic_bin = BIN
            voice = self.voice

        args = [mimic_bin, '-voice', voice, '-psdur', '-ssml']

        stretch = config.get('duration_stretch', None)
        if stretch:
            args += ['--setf', 'duration_stretch=' + stretch]
        return args

    def get_tts(self, sentence, wav_file):
        #  Generate WAV and phonemes
        phonemes = subprocess.check_output(self.args + ['-o', wav_file,
                                                        '-t', sentence])
        return wav_file, phonemes.decode()

    def viseme(self, output):
        visemes = []
        start = time()
        pairs = str(output).split(" ")
        for pair in pairs:
            pho_dur = pair.split(":")  # phoneme:duration
            if len(pho_dur) == 2:
                visemes.append((VISIMES.get(pho_dur[0], '4'),
                                float(pho_dur[1])))
        return visemes


class MimicValidator(TTSValidator):
    def __init__(self, tts):
        super(MimicValidator, self).__init__(tts)

    def validate_lang(self):
        # TODO: Verify version of mimic can handle the requested language
        pass

    def validate_connection(self):
        try:
            subprocess.call([BIN, '--version'])
        except Exception:
            LOG.info("Failed to find mimic at: " + BIN)
            raise Exception(
                'Mimic was not found. Run install-mimic.sh to install it.')

    def get_tts_class(self):
        return Mimic


# Mapping based on Jeffers phoneme to viseme map, seen in table 1 from:
# http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.221.6377&rep=rep1&type=pdf
#
# Mycroft unit visemes based on images found at:
# http://www.web3.lu/wp-content/uploads/2014/09/visemes.jpg
#
# Mapping was created partially based on the "12 mouth shapes visuals seen at:
# https://wolfpaulus.com/journal/software/lipsynchronization/

VISIMES = {
    # /A group
    'v': '5',
    'f': '5',
    # /B group
    'uh': '2',
    'w': '2',
    'uw': '2',
    'er': '2',
    'r': '2',
    'ow': '2',
    # /C group
    'b': '4',
    'p': '4',
    'm': '4',
    # /D group
    'aw': '1',
    # /E group
    'th': '3',
    'dh': '3',
    # /F group
    'zh': '3',
    'ch': '3',
    'sh': '3',
    'jh': '3',
    # /G group
    'oy': '6',
    'ao': '6',
    # /Hgroup
    'z': '3',
    's': '3',
    # /I group
    'ae': '0',
    'eh': '0',
    'ey': '0',
    'ah': '0',
    'ih': '0',
    'y': '0',
    'iy': '0',
    'aa': '0',
    'ay': '0',
    'ax': '0',
    'hh': '0',
    # /J group
    'n': '3',
    't': '3',
    'd': '3',
    'l': '3',
    # /K group
    'g': '3',
    'ng': '3',
    'k': '3',
    # blank mouth
    'pau': '4',
}
