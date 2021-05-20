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
from neon_core.configuration import Configuration, get_private_keys
from ovos_plugin_manager.language import load_lang_detect_plugin, \
    load_tx_plugin
import os


def get_lang_config():
    config = Configuration.get()
    lang_config = config.get("language", {})
    lang_config["internal"] = lang_config.get("internal") or config.get("lang",
                                                                        "en-us")
    lang_config["user"] = lang_config.get("user") or config.get("lang",
                                                                "en-us")
    return lang_config


def get_language_dir(base_path, lang="en-us"):
    """ checks for all language variations and returns best path """
    lang_path = os.path.join(base_path, lang)
    # base_path/en-us
    if os.path.isdir(lang_path):
        return lang_path
    if "-" in lang:
        main = lang.split("-")[0]
        # base_path/en
        general_lang_path = os.path.join(base_path, main)
        if os.path.isdir(general_lang_path):
            return general_lang_path
    else:
        main = lang
    # base_path/en-uk, base_path/en-au...
    if os.path.isdir(base_path):
        candidates = [os.path.join(base_path, f)
                      for f in os.listdir(base_path) if f.startswith(main)]
        paths = [p for p in candidates if os.path.isdir(p)]
        # TODO how to choose best local dialect?
        if len(paths):
            return paths[0]
    return os.path.join(base_path, lang)


class TranslatorFactory:
    CLASSES = {}

    @staticmethod
    def create(module=None):
        config = Configuration.get().get("language", {})
        module = module or config.get("translation_module", "google")
        if module not in DetectorFactory.CLASSES:
            # plugin!
            clazz = load_tx_plugin(module)
        else:
            clazz = TranslatorFactory.CLASSES.get(module)

        config["keys"] = get_private_keys()
        return clazz(config)


class DetectorFactory:
    CLASSES = {}

    @staticmethod
    def create(module=None):
        config = Configuration.get().get("language", {})
        module = module or config.get("detection_module", "fastlang")

        if module not in DetectorFactory.CLASSES:
            # plugin!
            clazz = load_lang_detect_plugin(module)
        else:
            clazz = DetectorFactory.CLASSES.get(module)

        config["keys"] = get_private_keys()
        return clazz(config)
