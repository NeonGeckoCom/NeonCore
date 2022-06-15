# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
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

from os.path import join
from neon_utils import LOG

from mycroft.dialog import MustacheDialogRenderer, load_dialogs, get
from mycroft.util import resolve_resource_file


def get_all(phrase, lang=None, context=None):
    """
    Looks up a resource file for the given phrase.  If no file
    is found, the requested phrase is returned as the string.
    This will use the default language for translations.
    Args:
        phrase (str): resource phrase to retrieve/translate
        lang (str): the language to use
        context (dict): values to be inserted into the string
    Returns:
        [str]: Array of all the versions of the phrase
    """
    if not lang:
        from neon_core.configuration import Configuration
        conf = Configuration.get()
        lang = conf.get("internal_lang") or conf.get("lang")

    filename = "text/" + lang.lower() + "/" + phrase + ".dialog"
    template = resolve_resource_file(filename)
    if template:
        stache = MustacheDialogRenderer()
        stache.load_template_file(phrase, template)
        if phrase in stache.templates:
            if not context:
                context = {}

            # Render all templates...
            result = []
            for i in range(0, len(stache.templates[phrase])):
                result.append(stache.render("template", context, i))
            return result

    # Use the given phrase as the template content.  Useful for
    # short phrase or single-words that can be enhanced and
    # translated later.  No rendering happens, though.
    return [phrase.replace('.', ' ')]
