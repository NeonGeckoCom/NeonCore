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

from mycroft.tts import TTS, TTSValidator
from mycroft.tts.remote_tts import RemoteTTSTimeoutException
from mycroft.util.log import LOG
from mycroft.util.format import pronounce_number
from mycroft.tts import cache_handler
from mycroft.util import play_wav, get_cache_directory
from requests_futures.sessions import FuturesSession
from requests.exceptions import (
    ReadTimeout, ConnectionError, ConnectTimeout, HTTPError
)
from urllib import parse
from .mimic_tts import VISIMES
import math
import base64
import os
import re
import json


# Heuristic value, caps character length of a chunk of text to be spoken as a
# work around for current Mimic2 implementation limits.
_max_sentence_size = 170


def _break_chunks(l, n):
    """ Yield successive n-sized chunks

    Args:
        l (list): text (str) to split
        chunk_size (int): chunk size
    """
    for i in range(0, len(l), n):
        yield " ".join(l[i:i + n])


def _split_by_chunk_size(text, chunk_size):
    """ Split text into word chunks by chunk_size size

    Args:
        text (str): text to split
        chunk_size (int): chunk size

    Returns:
        list: list of text chunks
    """
    text_list = text.split()

    if len(text_list) <= chunk_size:
        return [text]

    if chunk_size < len(text_list) < (chunk_size * 2):
        return list(_break_chunks(
            text_list,
            int(math.ceil(len(text_list) / 2))
        ))
    elif (chunk_size * 2) < len(text_list) < (chunk_size * 3):
        return list(_break_chunks(
            text_list,
            int(math.ceil(len(text_list) / 3))
        ))
    elif (chunk_size * 3) < len(text_list) < (chunk_size * 4):
        return list(_break_chunks(
            text_list,
            int(math.ceil(len(text_list) / 4))
        ))
    else:
        return list(_break_chunks(
            text_list,
            int(math.ceil(len(text_list) / 5))
        ))


def _split_by_punctuation(chunks, puncs):
    """splits text by various punctionations
    e.g. hello, world => [hello, world]

    Args:
        chunks (list or str): text (str) to split
        puncs (list): list of punctuations used to split text

    Returns:
        list: list with split text
    """
    if isinstance(chunks, str):
        out = [chunks]
    else:
        out = chunks

    for punc in puncs:
        splits = []
        for t in out:
            # Split text by punctuation, but not embedded punctuation.  E.g.
            # Split:  "Short sentence.  Longer sentence."
            # But not at: "I.B.M." or "3.424", "3,424" or "what's-his-name."
            splits += re.split(r'(?<!\.\S)' + punc + r'\s', t)
        out = splits
    return [t.strip() for t in out]


def _add_punctuation(text):
    """ Add punctuation at the end of each chunk.

    Mimic2 expects some form of punctuation at the end of a sentence.
    """
    punctuation = ['.', '?', '!', ';']
    if len(text) >= 1 and text[-1] not in punctuation:
        return text + '.'
    else:
        return text


def _sentence_chunker(text):
    """ Split text into smaller chunks for TTS generation.

    NOTE: The smaller chunks are needed due to current Mimic2 TTS limitations.
    This stage can be removed once Mimic2 can generate longer sentences.

    Args:
        text (str): text to split
        chunk_size (int): size of each chunk
        split_by_punc (bool, optional): Defaults to True.

    Returns:
        list: list of text chunks
    """
    if len(text) <= _max_sentence_size:
        return [_add_punctuation(text)]

    # first split by punctuations that are major pauses
    first_splits = _split_by_punctuation(
        text,
        puncs=[r'\.', r'\!', r'\?', r'\:', r'\;']
    )

    # if chunks are too big, split by minor pauses (comma, hyphen)
    second_splits = []
    for chunk in first_splits:
        if len(chunk) > _max_sentence_size:
            second_splits += _split_by_punctuation(chunk,
                                                   puncs=[r'\,', '--', '-'])
        else:
            second_splits.append(chunk)

    # if chunks are still too big, chop into pieces of at most 20 words
    third_splits = []
    for chunk in second_splits:
        if len(chunk) > _max_sentence_size:
            third_splits += _split_by_chunk_size(chunk, 20)
        else:
            third_splits.append(chunk)

    return [_add_punctuation(chunk) for chunk in third_splits]


class Mimic2(TTS):

    def __init__(self, lang, config):
        super(Mimic2, self).__init__(
            lang, config, Mimic2Validator(self)
        )
        try:
            LOG.info("Getting Pre-loaded cache")
            cache_handler.main(config['preloaded_cache'])
            LOG.info("Successfully downloaded Pre-loaded cache")
        except Exception as e:
            LOG.error("Could not get the pre-loaded cache ({})"
                      .format(repr(e)))
        self.url = config['url']
        self.session = FuturesSession()

    def _save(self, data):
        """ Save WAV files in tmp

        Args:
            data (byes): WAV data
        """
        with open(self.filename, 'wb') as f:
            f.write(data)

    def _play(self, req):
        """ Play WAV file after saving to tmp

        Args:
            req (object): requests object
        """
        if req.status_code == 200:
            self._save(req.content)
            play_wav(self.filename).communicate()
        else:
            LOG.error(
                '%s Http Error: %s for url: %s' %
                (req.status_code, req.reason, req.url))

    def _requests(self, sentence):
        """create asynchronous request list

        Args:
            chunks (list): list of text to synthesize

        Returns:
            list: list of FutureSession objects
        """
        url = self.url + parse.quote(sentence)
        req_route = url + "&visimes=True"
        return self.session.get(req_route, timeout=5)

    def viseme(self, phonemes):
        """ Maps phonemes to appropriate viseme encoding

        Args:
            phonemes (list): list of tuples (phoneme, time_start)

        Returns:
            list: list of tuples (viseme_encoding, time_start)
        """
        visemes = []
        for pair in phonemes:
            if pair[0]:
                phone = pair[0].lower()
            else:
                # if phoneme doesn't exist use
                # this as placeholder since it
                # is the most common one "3"
                phone = 'z'
            vis = VISIMES.get(phone)
            vis_dur = float(pair[1])
            visemes.append((vis, vis_dur))
        return visemes

    def _prepocess_sentence(sentence):
        """ Split sentence in chunks better suited for mimic2. """
        return _sentence_chunker(sentence)

    def get_tts(self, sentence, wav_file):
        """ Generate (remotely) and play mimic2 WAV audio

        Args:
            sentence (str): Phrase to synthesize to audio with mimic2
            wav_file (str): Location to write audio output
        """
        LOG.debug("Generating Mimic2 TSS for: " + str(sentence))
        try:
            req = self._requests(sentence)
            results = req.result().json()
            audio = base64.b64decode(results['audio_base64'])
            vis = results['visimes']
            with open(wav_file, 'wb') as f:
                f.write(audio)
        except (ReadTimeout, ConnectionError, ConnectTimeout, HTTPError):
            raise RemoteTTSTimeoutException(
                "Mimic 2 server request timed out. Falling back to mimic")
        return (wav_file, vis)

    def save_phonemes(self, key, phonemes):
        """
            Cache phonemes

            Args:
                key:        Hash key for the sentence
                phonemes:   phoneme string to save
        """
        cache_dir = get_cache_directory("tts/" + self.tts_name)
        pho_file = os.path.join(cache_dir, key + ".pho")
        try:
            with open(pho_file, "w") as cachefile:
                cachefile.write(json.dumps(phonemes))
        except Exception:
            LOG.exception("Failed to write {} to cache".format(pho_file))

    def load_phonemes(self, key):
        """
            Load phonemes from cache file.

            Args:
                Key:    Key identifying phoneme cache
        """
        pho_file = os.path.join(get_cache_directory("tts/" + self.tts_name),
                                key + ".pho")
        if os.path.exists(pho_file):
            try:
                with open(pho_file, "r") as cachefile:
                    phonemes = json.load(cachefile)
                return phonemes
            except Exception as e:
                LOG.error("Failed to read .PHO from cache ({})".format(e))
        return None


class Mimic2Validator(TTSValidator):

    def __init__(self, tts):
        super(Mimic2Validator, self).__init__(tts)

    def validate_lang(self):
        # TODO
        pass

    def validate_connection(self):
        # TODO
        pass

    def get_tts_class(self):
        return Mimic2
