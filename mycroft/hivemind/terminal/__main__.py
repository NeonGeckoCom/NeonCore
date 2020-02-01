from mycroft.hivemind.terminal import JarbasCliTerminal, platform
from jarbas_hive_mind import HiveMindConnection


def connect_to_hivemind(host="127.0.0.1",
                        port=5678, name="JarbasCliTerminal",
                        key="cli_key", useragent=platform):
    con = HiveMindConnection(host, port)

    terminal = JarbasCliTerminal(con.address,
                                 headers=con.get_headers(name, key),
                                 useragent=useragent)

    con.secure_connect(terminal)


if __name__ == '__main__':
    # TODO argparse
    connect_to_hivemind()
