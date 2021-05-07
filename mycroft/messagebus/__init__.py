# # NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
# # All trademark and other rights reserved by their respective owners
# # Copyright 2008-2021 Neongecko.com Inc.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
from mycroft_bus_client import MessageBusClient, Message
from mycroft.messagebus.service.event_handler import MessageBusEventHandler
from mycroft.util import create_daemon
from mycroft.messagebus.load_config import load_message_bus_config
from mycroft.util.json_helper import merge_dict
import json
from threading import Event


def get_messagebus(running=True):
    config = load_message_bus_config()
    bus = MessageBusClient(host=config.host, port=config.port,
                           route=config.route, ssl=config.ssl)
    if running:
        bus_connected = Event()
        # Set the bus connected event when connection is established
        bus.once('open', bus_connected.set)
        create_daemon(bus.run_forever)
        # Wait for connection
        bus_connected.wait()
    return bus


def send_message(message, data=None, context=None, bus=None):
    auto_close = bus is None
    bus = bus or get_messagebus()
    if isinstance(message, str):
        if isinstance(data, dict) or isinstance(context, dict):
            message = Message(message, data, context)
        else:
            try:
                message = json.loads(message)
            except:
                message = Message(message)
    if isinstance(message, dict):
        message = Message(message["type"],
                          message.get("data"),
                          message.get("context"))
    if not isinstance(message, Message):
        raise ValueError
    bus.emit(message)
    if auto_close:
        bus.close()


def send_binary_data_message(binary_data, msg_type="mycroft.binary.data",
                             msg_data=None, msg_context=None, bus=None):
    msg_data = msg_data or {}
    msg = {
        "type": msg_type,
        "data": merge_dict(msg_data, {"binary": binary_data.hex()}),
        "context": msg_context or None
    }
    send_message(msg, bus=bus)


def send_binary_file_message(filepath, msg_type="mycroft.binary.file",
                             msg_context=None, bus=None):
    with open(filepath, 'rb') as f:
        binary_data = f.read()
    msg_data = {"path": filepath}
    send_binary_data_message(binary_data, msg_type=msg_type, msg_data=msg_data,
                             msg_context=msg_context, bus=bus)


def decode_binary_message(message):
    if isinstance(message, str):
        try:  # json string
            message = json.loads(message)
            binary_data = message.get("binary") or message["data"]["binary"]
        except:  # hex string
            binary_data = message
    elif isinstance(message, dict):
        # data field or serialized message
        binary_data = message.get("binary") or message["data"]["binary"]
    else:
        # message object
        binary_data = message.data["binary"]
    # decode hex string
    return bytearray.fromhex(binary_data)

