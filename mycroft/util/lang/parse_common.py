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


def is_numeric(input_str):
    """
    Takes in a string and tests to see if it is a number.
    Args:
        text (str): string to test if a number
    Returns:
        (bool): True if a number, else False

    """

    try:
        float(input_str)
        return True
    except ValueError:
        return False


def look_for_fractions(split_list):
    """"
    This function takes a list made by fraction & determines if a fraction.

    Args:
        split_list (list): list created by splitting on '/'
    Returns:
        (bool): False if not a fraction, otherwise True

    """

    if len(split_list) == 2:
        if is_numeric(split_list[0]) and is_numeric(split_list[1]):
            return True

    return False


def extract_numbers_generic(text, pronounce_handler, extract_handler,
                            short_scale=True, ordinals=False):
    """
        Takes in a string and extracts a list of numbers.
        Language agnostic, per language parsers need to be provided

    Args:
        text (str): the string to extract a number from
        pronounce_handler (function): function that pronounces a number
        extract_handler (function): function that extracts the last number
        present in a string
        short_scale (bool): Use "short scale" or "long scale" for large
            numbers -- over a million.  The default is short scale, which
            is now common in most English speaking countries.
            See https://en.wikipedia.org/wiki/Names_of_large_numbers
        ordinals (bool): consider ordinal numbers, e.g. third=3 instead of 1/3
    Returns:
        list: list of extracted numbers as floats
    """
    numbers = []
    normalized = text
    extract = extract_handler(normalized, short_scale, ordinals)
    to_parse = normalized
    while extract:
        numbers.append(extract)
        prev = to_parse
        num_txt = pronounce_handler(extract)
        extract = str(extract)
        if extract.endswith(".0"):
            extract = extract[:-2]

        # handle duplicate occurences, replace last one only
        def replace_right(source, target, replacement, replacements=None):
            return replacement.join(source.rsplit(target, replacements))

        normalized = replace_right(normalized, num_txt, extract, 1)
        # last biggest number was replaced, recurse to handle cases like
        # test one two 3
        to_parse = replace_right(to_parse, num_txt, extract, 1)
        to_parse = replace_right(to_parse, extract, " ", 1)
        if to_parse == prev:
            # avoid infinite loops, occasionally pronounced number may be
            # different from extracted text,
            # ie pronounce(0.5) != half and extract(half) == 0.5
            extract = False
            # TODO fix this
        else:
            extract = extract_handler(to_parse, short_scale, ordinals)
    numbers.reverse()
    return numbers
