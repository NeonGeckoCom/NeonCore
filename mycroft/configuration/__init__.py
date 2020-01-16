# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from mycroft.configuration.config import Configuration, LocalConf, RemoteConf
from mycroft.configuration.locations import SYSTEM_CONFIG, USER_CONFIG
import platform
import socket


# Compatibility
class ConfigurationManager(Configuration):
    @staticmethod
    def instance():
        return Configuration.get()


def get_device_type():
    device = "desktop"
    if"arm" in platform.machine():
        device = "pi"
    else:
        server_hosts = Configuration.get()["device"].get("server_hosts",
                                                         [".187.223", ".186.92", ".186.120"])
        host = socket.gethostbyname(socket.gethostname())
        for h in server_hosts:
            if h in host:
                # TODO need clarification, a better check could be
                # host.endswith(h)
                device = "server"
    return device


def is_server():
    return get_device_type() == "server"