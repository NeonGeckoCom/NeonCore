#!/usr/bin/env python3
import traceback
from time import sleep
from mycroft.util.log import LOG
from mycroft.messagebus import get_messagebus
from mycroft.util import wait_for_exit_signal


def on_message(message):
    LOG.info(str(message))


def main():
    sleep(0.5)
    client = get_messagebus()
    client.on("message", on_message)
    wait_for_exit_signal()


if __name__ == '__main__':
    # Run loop trying to reconnect if there are any issues starting
    # the websocket
    while True:
        try:
            main()
        except KeyboardInterrupt:
            raise
        except:
            traceback.print_exc()
