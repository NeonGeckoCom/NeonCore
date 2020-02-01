from jarbas_hive_mind import HiveMindListener
from jarbas_hive_mind.configuration import CONFIGURATION
from jarbas_hive_mind.database import ClientDatabase
from jarbas_utils.log import LOG
from os.path import exists, join


def start_mind(config=None, bus=None):

    config = config or CONFIGURATION

    # read configuration
    port = config["port"]
    max_connections = config.get("max_connections", -1)
    certificate_path = config["ssl"]["certificates"]
    key = join(certificate_path,
               config["ssl"]["ssl_keyfile"])
    cert = join(certificate_path,
                config["ssl"]["ssl_certfile"])

    # generate self signed keys
    if not exists(key):
        LOG.warning("ssl keys dont exist")
        HiveMindListener.generate_keys(certificate_path)

    # listen
    listener = HiveMindListener(port, max_connections, bus)
    listener.secure_listen(key, cert)


def add_client(name, mail, key, admin=False):
    db = ClientDatabase(debug=True)
    db.add_client(name, mail, key, admin=admin)
