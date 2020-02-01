from mycroft.hivemind import add_client
import sys


def main():
    """
    Main function, will run if executed from command line.

    Sends parameters from commandline.

    Param 1:    client name  - default"
    Param 2:    client key   - default == "HiveMind"
    Param 3:    client email - default == "dummy@fakemail.mail"
    """

    mail = "dummy@fakemail.mail"
    key = "HiveMind"
    admin = False

    # Parse the command line
    if len(sys.argv) == 2:
        name = sys.argv[1]
    elif len(sys.argv) == 3:
        name = sys.argv[1]
        key = sys.argv[2]
    elif len(sys.argv) == 4:
        name = sys.argv[1]
        key = sys.argv[2]
        mail = sys.argv[3]
    else:
        print("Command line interface to the mycroft hivemind")
        print("Usage: python -m mycroft.hivemind.add_client <name>")
        print("       python -m mycroft.hivemind.add_client <name> <key>")
        print("       python -m mycroft.hivemind.add_client <name> <key> <mail>\n")
        print("Examples: python -m mycroft.hivemind.add_client MyClientID MySecretKey")
        exit()

    add_client(name, mail, key, admin)


if __name__ == '__main__':
    main()

