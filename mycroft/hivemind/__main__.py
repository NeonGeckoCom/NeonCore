from mycroft.hivemind import start_mind
from mycroft.configuration import Configuration
from mycroft.messagebus.client import MessageBusClient
from mycroft.util import create_daemon

config = Configuration.get().get("hivemind")

bus = MessageBusClient()
create_daemon(bus.run_forever)

start_mind(config, bus)
