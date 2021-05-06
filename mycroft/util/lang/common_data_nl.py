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
from collections import OrderedDict


_ARTICLES = {'de', 'het'}


_NUM_STRING_NL = {
    0: 'nul',
    1: 'een',
    2: 'twee',
    3: 'drie',
    4: 'vier',
    5: 'vijf',
    6: 'zes',
    7: 'zeven',
    8: 'acht',
    9: 'negen',
    10: 'tien',
    11: 'elf',
    12: 'twaalf',
    13: 'dertien',
    14: 'veertien',
    15: 'vijftien',
    16: 'zestien',
    17: 'zeventien',
    18: 'achttien',
    19: 'negentien',
    20: 'twintig',
    30: 'dertig',
    40: 'veertig',
    50: 'vijftig',
    60: 'zestig',
    70: 'zeventig',
    80: 'tachtig',
    90: 'negentig'
}


_FRACTION_STRING_NL = {
    2: 'half',
    3: 'derde',
    4: 'vierde',
    5: 'vijfde',
    6: 'zesde',
    7: 'zevende',
    8: 'achtste',
    9: 'negende',
    10: 'tiende',
    11: 'elfde',
    12: 'twaalfde',
    13: 'dertiende',
    14: 'veertiende',
    15: 'vijftiende',
    16: 'zestiende',
    17: 'zeventiende',
    18: 'achttiende',
    19: 'negentiende',
    20: 'twintigste'
}


_LONG_SCALE_NL = OrderedDict([
    (100, 'honderd'),
    (1000, 'duizend'),
    (1000000, 'miljoen'),
    (1e12, "biljoen"),
    (1e18, 'triljoen'),
    (1e24, "quadriljoen"),
    (1e30, "quintillion"),
    (1e36, "sextillion"),
    (1e42, "septillion"),
    (1e48, "octillion"),
    (1e54, "nonillion"),
    (1e60, "decillion"),
    (1e66, "undecillion"),
    (1e72, "duodecillion"),
    (1e78, "tredecillion"),
    (1e84, "quattuordecillion"),
    (1e90, "quinquadecillion"),
    (1e96, "sedecillion"),
    (1e102, "septendecillion"),
    (1e108, "octodecillion"),
    (1e114, "novendecillion"),
    (1e120, "vigintillion"),
    (1e306, "unquinquagintillion"),
    (1e312, "duoquinquagintillion"),
    (1e336, "sesquinquagintillion"),
    (1e366, "unsexagintillion")
])


_SHORT_SCALE_NL = OrderedDict([
    (100, 'honderd'),
    (1000, 'duizend'),
    (1000000, 'miljoen'),
    (1e9, "miljard"),
    (1e12, 'biljoen'),
    (1e15, "quadrillion"),
    (1e18, "quintiljoen"),
    (1e21, "sextiljoen"),
    (1e24, "septiljoen"),
    (1e27, "octiljoen"),
    (1e30, "noniljoen"),
    (1e33, "deciljoen"),
    (1e36, "undeciljoen"),
    (1e39, "duodeciljoen"),
    (1e42, "tredeciljoen"),
    (1e45, "quattuordeciljoen"),
    (1e48, "quinquadeciljoen"),
    (1e51, "sedeciljoen"),
    (1e54, "septendeciljoen"),
    (1e57, "octodeciljoen"),
    (1e60, "novendeciljoen"),
    (1e63, "vigintiljoen"),
    (1e66, "unvigintiljoen"),
    (1e69, "uuovigintiljoen"),
    (1e72, "tresvigintiljoen"),
    (1e75, "quattuorvigintiljoen"),
    (1e78, "quinquavigintiljoen"),
    (1e81, "qesvigintiljoen"),
    (1e84, "septemvigintiljoen"),
    (1e87, "octovigintiljoen"),
    (1e90, "novemvigintiljoen"),
    (1e93, "trigintiljoen"),
    (1e96, "untrigintiljoen"),
    (1e99, "duotrigintiljoen"),
    (1e102, "trestrigintiljoen"),
    (1e105, "quattuortrigintiljoen"),
    (1e108, "quinquatrigintiljoen"),
    (1e111, "sestrigintiljoen"),
    (1e114, "septentrigintiljoen"),
    (1e117, "octotrigintiljoen"),
    (1e120, "noventrigintiljoen"),
    (1e123, "quadragintiljoen"),
    (1e153, "quinquagintiljoen"),
    (1e183, "sexagintiljoen"),
    (1e213, "septuagintiljoen"),
    (1e243, "octogintiljoen"),
    (1e273, "nonagintiljoen"),
    (1e303, "centiljoen"),
    (1e306, "uncentiljoen"),
    (1e309, "duocentiljoen"),
    (1e312, "trescentiljoen"),
    (1e333, "decicentiljoen"),
    (1e336, "undecicentiljoen"),
    (1e363, "viginticentiljoen"),
    (1e366, "unviginticentiljoen"),
    (1e393, "trigintacentiljoen"),
    (1e423, "quadragintacentiljoen"),
    (1e453, "quinquagintacentiljoen"),
    (1e483, "sexagintacentiljoen"),
    (1e513, "septuagintacentiljoen"),
    (1e543, "ctogintacentiljoen"),
    (1e573, "nonagintacentiljoen"),
    (1e603, "ducentiljoen"),
    (1e903, "trecentiljoen"),
    (1e1203, "quadringentiljoen"),
    (1e1503, "quingentiljoen"),
    (1e1803, "sescentiljoen"),
    (1e2103, "septingentiljoen"),
    (1e2403, "octingentiljoen"),
    (1e2703, "nongentiljoen"),
    (1e3003, "milliniljoen")
])


_ORDINAL_STRING_BASE_NL = {
    1: 'eerste',
    2: 'tweede',
    3: 'derde',
    4: 'vierde',
    5: 'vijfde',
    6: 'zesde',
    7: 'zevende',
    8: 'achtste',
    9: 'negende',
    10: 'tiende',
    11: 'elfde',
    12: 'twaalfde',
    13: 'dertiende',
    14: 'veertiende',
    15: 'vijftiende',
    16: 'zestiende',
    17: 'zeventiende',
    18: 'achttiende',
    19: 'negentiende',
    20: 'twintigste',
    30: 'dertigste',
    40: "veertigste",
    50: "vijftigste",
    60: "zestigste",
    70: "zeventigste",
    80: "tachtigste",
    90: "negentigste",
    10e3: "honderdste",
    1e3: "duizendste"
}


_SHORT_ORDINAL_STRING_NL = {
    1e6: "miloenste",
    1e9: "miljardste",
    1e12: "biljoenste",
    1e15: "biljardste",
    1e18: "triljoenste",
    1e21: "trijardste",
    1e24: "quadriljoenste",
    1e27: "quadriljardste",
    1e30: "quintiljoenste",
    1e33: "quintiljardste"
    # TODO > 1e-33
}
_SHORT_ORDINAL_STRING_NL.update(_ORDINAL_STRING_BASE_NL)


_LONG_ORDINAL_STRING_NL = {
    1e6: "miloenste",
    1e9: "miljardste",
    1e12: "biljoenste",
    1e15: "biljardste",
    1e18: "triljoenste",
    1e21: "trijardste",
    1e24: "quadriljoenste",
    1e27: "quadriljardste",
    1e30: "quintiljoenste",
    1e33: "quintiljardste"
    # TODO > 1e60
}
_LONG_ORDINAL_STRING_NL.update(_ORDINAL_STRING_BASE_NL)
