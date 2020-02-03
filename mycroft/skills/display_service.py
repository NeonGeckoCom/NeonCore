import time
from mycroft.messagebus.message import Message
from mycroft.messagebus.client import MessageBusClient
from os.path import abspath


def ensure_uri(s):
    """
        Interprete paths as file:// uri's

        Args:
            s: string to be checked

        Returns:
            if s is uri, s is returned otherwise file:// is prepended
    """
    if isinstance(s, str):
        if '://' not in s:
            return 'file://' + abspath(s)
        else:
            return s
    elif isinstance(s, (tuple, list)):
        if '://' not in s[0]:
            return 'file://' + abspath(s[0]), s[1]
        else:
            return s
    else:
        raise ValueError('Invalid picture')


class DisplayService:
    """
        DisplayService object for interacting with the display subsystem
        Args:
            emitter: eventemitter or websocket object
    """

    def __init__(self, bus, name="skills"):
        self.name = name
        self.bus = bus
        self.bus.on('mycroft.display.service.picture_info_reply',
                    self._pic_info)
        self.info = None

    def _pic_info(self, message=None):
        """
            Handler for catching returning pic info
        """
        self.info = message.data

    def display(self, pictures=None, utterance=''):
        """ Start display.
            Args:
                pictures: list of paths
                utterance: forward utterance for further processing by the
                           audio service.
        """
        if pictures is None:
            pictures = []
        if isinstance(pictures, str):
            pictures = [pictures]
        if not isinstance(pictures, list):
            raise ValueError
        pictures = [ensure_uri(t) for t in pictures]
        self.bus.emit(Message('mycroft.display.service.display',
                              data={'pictures': pictures,
                                    'utterance': utterance},
                              context={"source": self.name,
                                       "destination": "Display Service"}))

    def add_pictures(self, pictures):
        """ Start display.
            Args:
                file_path: track or list of paths
                utterance: forward utterance for further processing by the
                           audio service.
        """
        if isinstance(pictures, str):
            pictures = [pictures]
        if not isinstance(pictures, list):
            raise ValueError

        self.bus.emit(Message('mycroft.display.service.queue',
                              data={'pictures': pictures}))

    def next_picture(self):
        """ Change to next pic. """
        self.bus.emit(Message('mycroft.display.service.next'))

    def close(self):
        """ Change to next pic. """
        self.bus.emit(Message('mycroft.display.service.close'))

    def previous_picture(self):
        """ Change to previous pic. """
        self.bus.emit(Message('mycroft.display.service.prev'))

    def clear(self):
        """ Clear Display """
        self.bus.emit(Message('mycroft.display.service.clear'))

    def set_fullscreen(self, value):
        self.bus.emit(Message('mycroft.display.service.fullscreen',
                              data={"value": value}))

    def set_height(self, height=1600,):
        """ Reset Display. """
        self.bus.emit(Message('mycroft.display.service.height',
                              data={"value": height}))

    def set_width(self, width=900):
        """ Reset Display. """
        self.bus.emit(Message('mycroft.display.service.width',
                              data={"value": width}))

    def reset(self):
        """ Reset Display. """
        self.bus.emit(Message('mycroft.display.service.reset'))

    def pic_info(self):
        """ Request information of current displaying pic.
            Returns:
                Dict with pic info.
        """
        self.info = None
        self.bus.emit(Message('mycroft.display.service.picture_info'))
        wait = 5.0
        while self.info is None and wait >= 0:
            time.sleep(0.1)
            wait -= 0.1
        return self.info or {"is_displaying": False}

    @property
    def is_displaying(self):
        return self.pic_info()["is_displaying"]


if __name__ == "__main__":
    from time import sleep
    from mycroft.util import create_daemon
    bus = MessageBusClient()
    create_daemon(bus.run_forever)

    display = DisplayService(bus)
    display.set_fullscreen(False)
    print(display.is_displaying)
    display.display([
        "/home/user/Pictures/78281963_2870836686294904_3010935635440566272_n.jpg",
        "/home/user/Pictures/78261461_2870836602961579_9198065999352430592_n.jpg"
    ])
    sleep(1)
    display.next_picture()
    print(display.pic_info())
    print(display.is_displaying)
    sleep(1)
    display.clear()
    sleep(2)
    display.previous_picture()
    sleep(1)
    display.next_picture()
    sleep(1)
    display.next_picture()
    sleep(5)
    display.reset()
    display.set_fullscreen(True)
    sleep(5)
    display.close()
    print(display.is_displaying)
