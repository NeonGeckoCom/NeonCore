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
from time import sleep
from os.path import dirname, join, abspath
from threading import Event, Thread

from mycroft.configuration import Configuration
from mycroft.util.log import LOG
from mycroft.util.plugins import load_plugin


INIT_TIMEOUT = 120  # In seconds


class TriggerReload(Exception):
    pass


class NoModelAvailable(Exception):
    pass


class HotWordEngine:
    def __init__(self, key_phrase="hey mycroft", config=None, lang="en-us"):
        self.key_phrase = str(key_phrase).lower()
        # rough estimate 1 phoneme per 2 chars
        self.num_phonemes = len(key_phrase) / 2 + 1
        if config is None:
            config = Configuration.get().get("hotwords", {})
            config = config.get(self.key_phrase, {})
        self.config = config
        self.listener_config = Configuration.get().get("listener", {})
        self.module = self.config.get("module")
        self.lang = str(self.config.get("lang", lang)).lower()

    def found_wake_word(self, frame_data):
        return False

    def update(self, chunk):
        pass

    def stop(self):
        """ Perform any actions needed to shut down the hot word engine.

            This may include things such as unload loaded data or shutdown
            external processess.
        """
        pass


def load_wake_word_plugin(module_name):
    """Wrapper function for loading wake word plugin.

    Arguments:
        (str) Mycroft wake word module name from config
    """
    return load_plugin('mycroft.plugin.wake_word', module_name)


class HotWordFactory:
    CLASSES = {
        # engines without plugins can be added here
    }

    @staticmethod
    def load_module(module, hotword, config, lang, loop):
        LOG.info('Loading "{}" wake word via {}'.format(hotword, module))
        instance = None
        complete = Event()

        def initialize():
            nonlocal instance, complete
            try:
                if module in HotWordFactory.CLASSES:
                    clazz = HotWordFactory.CLASSES[module]
                else:
                    clazz = load_wake_word_plugin(module)
                    LOG.info('Loaded the Wake Word plugin {}'.format(module))

                instance = clazz(hotword, config, lang=lang)
            except TriggerReload:
                complete.set()
                sleep(0.5)
                loop.reload()
            except NoModelAvailable:
                LOG.warning('Could not found find model for {} on {}.'.format(
                    hotword, module
                ))
                instance = None
            except Exception:
                LOG.exception(
                    'Could not create hotword. Falling back to default.')
                instance = None
            complete.set()

        Thread(target=initialize, daemon=True).start()
        if not complete.wait(INIT_TIMEOUT):
            LOG.info('{} is taking too long to load'.format(module))
            complete.set()
        return instance

    @classmethod
    def create_hotword(cls, hotword="dummy", config=None,
                       lang="en-us", loop=None):
        if not config:
            config = Configuration.get()['hotwords']
        config = config[hotword]

        module = config.get("module", "dummy_ww_plug")
        return cls.load_module(module, hotword, config, lang, loop) or \
            cls.load_module('dummy_ww_plug', "dummy", config, lang, loop)
