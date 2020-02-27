import sys
from mycroft.configuration import Configuration
from mycroft.util.log import LOG
from mycroft.util import create_daemon
from mycroft.messagebus import MessageBusClient
import time
from mycroft.client.file_reader import FileConsumer
from mycroft.processing_modules.audio import AudioParsersService


if __name__ == "__main__":
    ws = MessageBusClient()
    config = Configuration.get()
    create_daemon(ws.run_forever)

    service = AudioParsersService(ws)
    service.start()

    config = config.get("wav_client",
                        {"path": "/tmp/mycroft_in.wav"})

    file_consumer = FileConsumer(file_location=config["path"], bus=ws)
    file_consumer.bind(service)
    file_consumer.start()
    try:

        while True:
            time.sleep(100)
    except KeyboardInterrupt as e:
        LOG.exception(e)
        file_consumer.stop()
        file_consumer.join()
        sys.exit()
