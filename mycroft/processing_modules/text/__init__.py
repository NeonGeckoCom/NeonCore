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

from os.path import join, dirname
from mycroft.processing_modules import ModuleLoaderService
from mycroft.configuration import Configuration


class TextParsersService(ModuleLoaderService):

    def __init__(self, bus):
        parsers_dir = join(dirname(__file__), "modules").rstrip("/")
        super(TextParsersService, self).__init__(bus, parsers_dir)
        self.config = Configuration.get().get("text_parsers", {})
        self.blacklist = self.config.get("blacklist", [])

    def parse(self, parser, utterances=None, lang="en-us"):
        utterances = utterances or []
        if parser in self.loaded_modules:
            instance = self.loaded_modules[parser].get("instance")
            if instance:
                return instance.parse(utterances, lang)
        return utterances, {}


class TextParser:
    def __init__(self, name="test_parser", priority=50):
        self.name = name
        self.bus = None
        self.priority = priority
        self.config = Configuration.get().get("text_parsers", {}).\
            get(self.name, {})

    def bind(self, bus):
        """ attach messagebus """
        self.bus = bus

    def initialize(self):
        """ perform any initialization actions """
        pass

    def parse(self, utterances, lang="en-us"):
        """ parse utterances , return modified utterances + dict to be merged into message context """
        return utterances, {}

    def default_shutdown(self):
        """ perform any shutdown actions """
        pass

