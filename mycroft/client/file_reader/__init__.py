from threading import Thread, Event

from os.path import exists
from mycroft.stt import STTFactory
from mycroft.util.log import LOG
from mycroft.messagebus.message import Message
from mycroft.util.json_helper import merge_dict
import speech_recognition as sr
import time
from os import remove


def read_wave_file(wave_file_path):
    '''
    reads the wave file at provided path and return the expected
    Audio format
    '''
    # use the audio file as the audio source
    r = sr.Recognizer()
    with sr.AudioFile(wave_file_path) as source:
        audio = r.record(source)
    return audio


class FileConsumer(Thread):
    def __init__(self, file_location='/tmp/mycroft_in.wav', bus=None):
        super(FileConsumer, self).__init__()
        self.path = file_location
        self.stop_event = Event()
        LOG.info("Creating SST interface")
        self.stt = STTFactory.create()
        self.bus = bus
        self.bus.on("stt.request", self.handle_external_request)
        self.bus.on("recognizer_loop:server_utterance",
                    self.handle_server_request)
        self.parsers_service = None

    def bind(self, audio_parsers):
        self.parsers_service = audio_parsers

    def run(self):
        """
        Monitors for a specific file, if it exists it is transcribed and
        processed, file is deleted afterwards """
        while not self.stop_event.is_set():
            if exists(self.path):
                audio = read_wave_file(self.path)

                self.parsers_service.feed_speech(audio)
                audio, context = self.parsers_service.get_context(audio)
                context = merge_dict(context,
                                     {"source": "audio",
                                      "destination": "skills"})
                text = self.stt.execute(audio).lower().strip()
                self.bus.emit(
                    Message("recognizer_loop:utterance",
                            {"utterances": [text]},
                            context))
                remove(self.path)
            time.sleep(0.5)

    def handle_server_request(self, message):
        """ utterance from server is processed here """
        file = message.data.get("File")
        if not file:
            error = "No file provided for transcription"
            self.bus.emit(
                message.reply("recognizer_loop:server_error",
                              {"error": error}))
        elif not exists(file):
            error = "Invalid file path provided for transcription"
            self.bus.emit(
                message.reply("recognizer_loop:server_error",
                              {"error": error}))
        else:
            audio = read_wave_file(file)
            self.parsers_service.feed_speech(audio)
            audio, context = self.parsers_service.get_context(audio)
            context = merge_dict(context, message.context)
            transcript = self.stt.execute(audio).lower().strip()
            message = message.reply("recognizer_loop:utterance",
                                    {"utterances": [transcript]})
            message.context = context
            self.bus.emit(message)

    def handle_external_request(self, message):
        """ Standalone request, transcription is returned but NOT processed """
        file = message.data.get("File")
        if not file:
            error = "No file provided for transcription"
            self.bus.emit(
                message.reply("stt.error", {"error": error}))
        elif not exists(file):
            error = "Invalid file path provided for transcription"
            self.bus.emit(
                message.reply("stt.error", {"error": error}))
        else:
            audio = read_wave_file(file)
            self.parsers_service.feed_speech(audio)
            audio, context = self.parsers_service.get_context(audio)
            context = merge_dict(context, message.context)
            transcript = self.stt.execute(audio).lower().strip()
            message = message.reply("stt.reply",
                                    {"transcription": transcript})
            message.context = context
            self.bus.emit(message)

    def stop(self):
        self.stop_event.set()

