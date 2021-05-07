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
__active_lang = "en-us"  # English is the default active language
# TODO: Should this really be stored in the user config file?


def get_active_lang():
    """ Get the active full language code (BCP-47)

    Returns:
        str: A BCP-47 language code, e.g. ("en-us", or "pt-pt")
    """
    return __active_lang


def set_active_lang(lang_code):
    """ Set the active BCP-47 language code to be used in formatting/parsing

    Args:
        lang (str): BCP-47 language code, e.g. "en-us" or "es-mx"
    """
    global __active_lang
    if __active_lang != lang_code:
        # TODO: Validate lang codes?
        __active_lang = lang_code


def get_primary_lang_code(lang=None):
    """ Get the primary language code

    Args:
        lang (str, optional): A BCP-47 language code, or None for default

    Returns:
        str: A primary language family, such as "en", "de" or "pt"
    """
    # split on the hyphen and only return the primary-language code
    # NOTE: This is typically a two character code.  The standard allows
    #       1, 2, 3 and 4 character codes.  In the future we can consider
    #       mapping from the 3 to 2 character codes, for example.  But for
    #       now we can just be careful in use.
    return get_full_lang_code(lang).split("-")[0]


def get_full_lang_code(lang=None):
    """ Get the full language code

    Args:
        lang (str, optional): A BCP-47 language code, or None for default

    Returns:
        str: A full language code, such as "en-us" or "de-de"
    """
    if not lang:
        lang = __active_lang

    return lang or "en-us"
