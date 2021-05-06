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
import argparse
import os
import pyaudio
from contextlib import contextmanager

from speech_recognition import Recognizer
# TODO this import is failing, out of scope for this PP
from mycroft.client.speech.mic import MutableMicrophone
from mycroft.configuration import Configuration
from mycroft.util import play_wav
from mycroft.util.log import LOG
import logging

"""
Audio Test
A tool for recording X seconds of audio, and then playing them back. Useful
for testing hardware, and ensures
compatibility with mycroft recognizer loop code.
"""

# Reduce loglevel
LOG.level = 'ERROR'
logging.getLogger('urllib3').setLevel(logging.WARNING)


@contextmanager
def mute_output():
    """ Context manager blocking stdout and stderr completely.

    Redirects stdout and stderr to dev-null and restores them on exit.
    """
    # Open a pair of null files
    null_fds = [os.open(os.devnull, os.O_RDWR) for i in range(2)]
    # Save the actual stdout (1) and stderr (2) file  descriptors.
    orig_fds = [os.dup(1), os.dup(2)]
    # Assign the null pointers to stdout and stderr.
    os.dup2(null_fds[0], 1)
    os.dup2(null_fds[1], 2)
    try:
        yield
    finally:
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(orig_fds[0], 1)
        os.dup2(orig_fds[1], 2)
        for fd in null_fds + orig_fds:
            os.close(fd)


def record(filename, duration):
    mic = MutableMicrophone()
    recognizer = Recognizer()
    with mic as source:
        audio = recognizer.record(source, duration=duration)
        with open(filename, 'wb') as f:
            f.write(audio.get_wav_data())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f', '--filename', dest='filename', default="/tmp/test.wav",
        help="Filename for saved audio (Default: /tmp/test.wav)")
    parser.add_argument(
        '-d', '--duration', dest='duration', type=int, default=10,
        help="Duration of recording in seconds (Default: 10)")
    parser.add_argument(
        '-v', '--verbose', dest='verbose', action='store_true', default=False,
        help="Add extra output regarding the recording")
    parser.add_argument(
        '-l', '--list', dest='show_devices', action='store_true',
        default=False, help="List all availabile input devices")
    args = parser.parse_args()

    if args.show_devices:
        print(" Initializing... ")
        pa = pyaudio.PyAudio()

        print(" ====================== Audio Devices ======================")
        print("  Index    Device Name")
        for device_index in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(device_index)
            if dev['maxInputChannels'] > 0:
                print('   {}:       {}'.format(device_index, dev['name']))
        print()

    config = Configuration.get()
    if "device_name" in config["listener"]:
        dev = config["listener"]["device_name"]
    elif "device_index" in config["listener"]:
        dev = "Device at index {}".format(config["listener"]["device_index"])
    else:
        dev = "Default device"
    samplerate = config["listener"]["sample_rate"]
    play_cmd = config["play_wav_cmdline"].replace("%1", "WAV_FILE")
    print(" ========================== Info ===========================")
    print(" Input device: {} @ Sample rate: {} Hz".format(dev, samplerate))
    print(" Playback commandline: {}".format(play_cmd))
    print()
    print(" ===========================================================")
    print(" ==         STARTING TO RECORD, MAKE SOME NOISE!          ==")
    print(" ===========================================================")

    if not args.verbose:
        with mute_output():
            record(args.filename, args.duration)
    else:
        record(args.filename, args.duration)

    print(" ===========================================================")
    print(" ==           DONE RECORDING, PLAYING BACK...             ==")
    print(" ===========================================================")
    status = play_wav(args.filename).wait()
    if status:
        print('An error occured while playing back audio ({})'.format(status))


if __name__ == "__main__":
    main()
