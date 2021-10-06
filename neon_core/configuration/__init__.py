from mycroft.configuration.config import Configuration, LocalConf

def get_private_keys():
    return Configuration.get(remote=False).get("keys", {})



