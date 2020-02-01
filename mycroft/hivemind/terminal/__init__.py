import json
from threading import Thread
from jarbas_hive_mind.slave.terminal import HiveMindTerminalProtocol, HiveMindTerminal
from jarbas_utils.log import LOG

platform = "JarbasCliTerminalv0.1"


class JarbasCliTerminalProtocol(HiveMindTerminalProtocol):
    def onOpen(self):
        LOG.info("WebSocket connection open. ")
        self.input_loop = Thread(target=self.get_cli_input)
        self.input_loop.setDaemon(True)
        self.input_loop.start()

    def onMessage(self, payload, isBinary):
        if not isBinary:
            payload = payload.decode("utf-8")
            msg = json.loads(payload)
            if msg.get("type", "") == "speak":
                utterance = msg["data"]["utterance"]
                LOG.info("[OUTPUT] " + utterance)
            elif msg.get("type", "") == "hive.complete_intent_failure":
                LOG.error("complete intent failure")
        else:
            pass

    # cli input thread
    def get_cli_input(self):
        LOG.info("waiting for input")
        while True:
            line = input("")
            msg = {"data": {"utterances": [line], "lang": "en-us"},
                   "type": "recognizer_loop:utterance",
                   "context": {"source": self.peer,
                               "destination": "hive_mind",
                               "platform": platform}}
            msg = json.dumps(msg)
            msg = bytes(msg, encoding="utf-8")
            self.sendMessage(msg, False)


class JarbasCliTerminal(HiveMindTerminal):
    protocol = JarbasCliTerminalProtocol
