import sys

from threading import Thread, Lock, Event

from os.path import exists
from mycroft.stt import STTFactory
from mycroft.configuration import Configuration
from mycroft.util.log import LOG
from mycroft.messagebus import MessageBusClient
from mycroft.messagebus.message import Message
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

    def run(self):
        """
        Monitors for a specific file, if it exists it is transcribed and
        processed, file is deleted afterwards """
        while not self.stop_event.is_set():
            if exists(self.path):
                audio = read_wave_file(self.path)
                text = self.stt.execute(audio).lower().strip()
                self.bus.emit(
                    Message("recognizer_loop:utterance",
                            {"utterances": [text]},
                            {"source": "wav_client",
                             "destination": "skills"}))
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
            transcript = self.stt.execute(audio).lower().strip()
            self.bus.emit(message.reply("recognizer_loop:utterance",
                                        {"utterances": [transcript]}))

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
            transcript = self.stt.execute(audio).lower().strip()
            self.bus.emit(message.reply("stt.reply",
                                        {"transcription": transcript}))

    def stop(self):
        self.stop_event.set()


def main():
    ws = MessageBusClient()
    config = Configuration.get()

    def connect():
        ws.run_forever()

    event_thread = Thread(target=connect)
    event_thread.setDaemon(True)
    event_thread.start()
    config = config.get("wav_client",
                        {"path": "/tmp/mycroft_in.wav"})
    try:
        file_consumer = FileConsumer(file_location=config["path"], bus=ws)
        file_consumer.start()
        while True:
            time.sleep(100)
    except KeyboardInterrupt as e:
        LOG.exception(e)
        file_consumer.stop()
        file_consumer.join()
        sys.exit()


if __name__ == "__main__":
    main()
