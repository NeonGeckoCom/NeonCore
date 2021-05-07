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
from mycroft.configuration import Configuration, get_private_keys
from mycroft.util.log import LOG
import os
import requests
import boto3


def langcode2name(lang_code):
    LANGUAGES = (('ABKHAZIAN', 'ab'),
                 ('AFAR', 'aa'),
                 ('AFRIKAANS', 'af'),
                 ('AKAN', 'ak'),
                 ('ALBANIAN', 'sq'),
                 ('AMHARIC', 'am'),
                 ('ARABIC', 'ar'),
                 ('ARMENIAN', 'hy'),
                 ('ASSAMESE', 'as'),
                 ('AYMARA', 'ay'),
                 ('AZERBAIJANI', 'az'),
                 ('BASHKIR', 'ba'),
                 ('BASQUE', 'eu'),
                 ('BELARUSIAN', 'be'),
                 ('BENGALI', 'bn'),
                 ('BIHARI', 'bh'),
                 ('BISLAMA', 'bi'),
                 ('BOSNIAN', 'bs'),
                 ('BRETON', 'br'),
                 ('BULGARIAN', 'bg'),
                 ('BURMESE', 'my'),
                 ('CATALAN', 'ca'),
                 ('CEBUANO', 'ceb'),
                 ('CHEROKEE', 'chr'),
                 ('NYANJA', 'ny'),
                 ('CORSICAN', 'co'),
                 ('CROATIAN', 'hr'),
                 ('CROATIAN', 'hr'),
                 ('CZECH', 'cs'),
                 ('Chinese', 'zh'),
                 ('Chinese', 'zh'),
                 ('Chinese', 'zh'),
                 ('Chinese', 'zh'),
                 ('ChineseT', 'zh-Hant'),
                 ('ChineseT', 'zh-Hant'),
                 ('ChineseT', 'zh-Hant'),
                 ('ChineseT', 'zh-Hant'),
                 ('ChineseT', 'zh-Hant'),
                 ('ChineseT', 'zh-Hant'),
                 ('DANISH', 'da'),
                 ('DHIVEHI', 'dv'),
                 ('DUTCH', 'nl'),
                 ('DZONGKHA', 'dz'),
                 ('ENGLISH', 'en'),
                 ('ESPERANTO', 'eo'),
                 ('ESTONIAN', 'et'),
                 ('EWE', 'ee'),
                 ('FAROESE', 'fo'),
                 ('FIJIAN', 'fj'),
                 ('FINNISH', 'fi'),
                 ('FRENCH', 'fr'),
                 ('FRISIAN', 'fy'),
                 ('GA', 'gaa'),
                 ('GALICIAN', 'gl'),
                 ('GANDA', 'lg'),
                 ('GEORGIAN', 'ka'),
                 ('GERMAN', 'de'),
                 ('GREEK', 'el'),
                 ('GREENLANDIC', 'kl'),
                 ('GUARANI', 'gn'),
                 ('GUJARATI', 'gu'),
                 ('HAITIAN_CREOLE', 'ht'),
                 ('HAUSA', 'ha'),
                 ('HAWAIIAN', 'haw'),
                 ('HEBREW', 'iw'),
                 ('HEBREW', 'iw'),
                 ('HINDI', 'hi'),
                 ('HMONG', 'hmn'),
                 ('HUNGARIAN', 'hu'),
                 ('ICELANDIC', 'is'),
                 ('IGBO', 'ig'),
                 ('INDONESIAN', 'id'),
                 ('INTERLINGUA', 'ia'),
                 ('INTERLINGUE', 'ie'),
                 ('INUKTITUT', 'iu'),
                 ('INUPIAK', 'ik'),
                 ('IRISH', 'ga'),
                 ('ITALIAN', 'it'),
                 ('Ignore', 'xxx'),
                 ('JAVANESE', 'jw'),
                 ('JAVANESE', 'jw'),
                 ('Japanese', 'ja'),
                 ('KANNADA', 'kn'),
                 ('KASHMIRI', 'ks'),
                 ('KAZAKH', 'kk'),
                 ('KHASI', 'kha'),
                 ('KHMER', 'km'),
                 ('KINYARWANDA', 'rw'),
                 ('KRIO', 'kri'),
                 ('KURDISH', 'ku'),
                 ('KYRGYZ', 'ky'),
                 ('Korean', 'ko'),
                 ('LAOTHIAN', 'lo'),
                 ('LATIN', 'la'),
                 ('LATVIAN', 'lv'),
                 ('LIMBU', 'lif'),
                 ('LIMBU', 'lif'),
                 ('LIMBU', 'lif'),
                 ('LINGALA', 'ln'),
                 ('LITHUANIAN', 'lt'),
                 ('LOZI', 'loz'),
                 ('LUBA_LULUA', 'lua'),
                 ('LUO_KENYA_AND_TANZANIA', 'luo'),
                 ('LUXEMBOURGISH', 'lb'),
                 ('MACEDONIAN', 'mk'),
                 ('MALAGASY', 'mg'),
                 ('MALAY', 'ms'),
                 ('MALAYALAM', 'ml'),
                 ('MALTESE', 'mt'),
                 ('MANX', 'gv'),
                 ('MAORI', 'mi'),
                 ('MARATHI', 'mr'),
                 ('MAURITIAN_CREOLE', 'mfe'),
                 ('ROMANIAN', 'ro'),
                 ('MONGOLIAN', 'mn'),
                 ('MONTENEGRIN', 'sr-ME'),
                 ('MONTENEGRIN', 'sr-ME'),
                 ('MONTENEGRIN', 'sr-ME'),
                 ('MONTENEGRIN', 'sr-ME'),
                 ('NAURU', 'na'),
                 ('NDEBELE', 'nr'),
                 ('NEPALI', 'ne'),
                 ('NEWARI', 'new'),
                 ('NORWEGIAN', 'no'),
                 ('NORWEGIAN', 'no'),
                 ('NORWEGIAN_N', 'nn'),
                 ('NYANJA', 'ny'),
                 ('OCCITAN', 'oc'),
                 ('ORIYA', 'or'),
                 ('OROMO', 'om'),
                 ('OSSETIAN', 'os'),
                 ('PAMPANGA', 'pam'),
                 ('PASHTO', 'ps'),
                 ('PEDI', 'nso'),
                 ('PERSIAN', 'fa'),
                 ('POLISH', 'pl'),
                 ('PORTUGUESE', 'pt'),
                 ('PUNJABI', 'pa'),
                 ('QUECHUA', 'qu'),
                 ('RAJASTHANI', 'raj'),
                 ('RHAETO_ROMANCE', 'rm'),
                 ('ROMANIAN', 'ro'),
                 ('RUNDI', 'rn'),
                 ('RUSSIAN', 'ru'),
                 ('SAMOAN', 'sm'),
                 ('SANGO', 'sg'),
                 ('SANSKRIT', 'sa'),
                 ('SCOTS', 'sco'),
                 ('SCOTS_GAELIC', 'gd'),
                 ('SERBIAN', 'sr'),
                 ('SERBIAN', 'sr'),
                 ('SESELWA', 'crs'),
                 ('SESELWA', 'crs'),
                 ('SESOTHO', 'st'),
                 ('SHONA', 'sn'),
                 ('SINDHI', 'sd'),
                 ('SINHALESE', 'si'),
                 ('SISWANT', 'ss'),
                 ('SLOVAK', 'sk'),
                 ('SLOVENIAN', 'sl'),
                 ('SOMALI', 'so'),
                 ('SPANISH', 'es'),
                 ('SUNDANESE', 'su'),
                 ('SWAHILI', 'sw'),
                 ('SWEDISH', 'sv'),
                 ('SYRIAC', 'syr'),
                 ('TAGALOG', 'tl'),
                 ('TAJIK', 'tg'),
                 ('TAMIL', 'ta'),
                 ('TATAR', 'tt'),
                 ('TELUGU', 'te'),
                 ('THAI', 'th'),
                 ('TIBETAN', 'bo'),
                 ('TIGRINYA', 'ti'),
                 ('TONGA', 'to'),
                 ('TSONGA', 'ts'),
                 ('TSWANA', 'tn'),
                 ('TUMBUKA', 'tum'),
                 ('TURKISH', 'tr'),
                 ('TURKMEN', 'tk'),
                 ('TWI', 'tw'),
                 ('UIGHUR', 'ug'),
                 ('UKRAINIAN', 'uk'),
                 ('URDU', 'ur'),
                 ('UZBEK', 'uz'),
                 ('VENDA', 've'),
                 ('VIETNAMESE', 'vi'),
                 ('VOLAPUK', 'vo'),
                 ('WARAY_PHILIPPINES', 'war'),
                 ('WELSH', 'cy'),
                 ('WOLOF', 'wo'),
                 ('XHOSA', 'xh'),
                 ('X_Arabic', 'xx-Arab'),
                 ('X_Armenian', 'xx-Armn'),
                 ('X_Avestan', 'xx-Avst'),
                 ('X_BORK_BORK_BORK', 'zzb'),
                 ('X_Balinese', 'xx-Bali'),
                 ('X_Bamum', 'xx-Bamu'),
                 ('X_Batak', 'xx-Batk'),
                 ('X_Bengali', 'xx-Beng'),
                 ('X_Bopomofo', 'xx-Bopo'),
                 ('X_Brahmi', 'xx-Brah'),
                 ('X_Braille', 'xx-Brai'),
                 ('X_Buginese', 'xx-Bugi'),
                 ('X_Buhid', 'xx-Buhd'),
                 ('X_Canadian_Aboriginal', 'xx-Cans'),
                 ('X_Carian', 'xx-Cari'),
                 ('X_Chakma', 'xx-Cakm'),
                 ('X_Cham', 'xx-Cham'),
                 ('X_Cherokee', 'xx-Cher'),
                 ('X_Common', 'xx-Zyyy'),
                 ('X_Coptic', 'xx-Copt'),
                 ('X_Cuneiform', 'xx-Xsux'),
                 ('X_Cypriot', 'xx-Cprt'),
                 ('X_Cyrillic', 'xx-Cyrl'),
                 ('X_Deseret', 'xx-Dsrt'),
                 ('X_Devanagari', 'xx-Deva'),
                 ('X_ELMER_FUDD', 'zze'),
                 ('X_Egyptian_Hieroglyphs', 'xx-Egyp'),
                 ('X_Ethiopic', 'xx-Ethi'),
                 ('X_Georgian', 'xx-Geor'),
                 ('X_Glagolitic', 'xx-Glag'),
                 ('X_Gothic', 'xx-Goth'),
                 ('X_Greek', 'xx-Grek'),
                 ('X_Gujarati', 'xx-Gujr'),
                 ('X_Gurmukhi', 'xx-Guru'),
                 ('X_HACKER', 'zzh'),
                 ('X_Han', 'xx-Hani'),
                 ('X_Hangul', 'xx-Hang'),
                 ('X_Hanunoo', 'xx-Hano'),
                 ('X_Hebrew', 'xx-Hebr'),
                 ('X_Hiragana', 'xx-Hira'),
                 ('X_Imperial_Aramaic', 'xx-Armi'),
                 ('X_Inherited', 'xx-Qaai'),
                 ('X_Inscriptional_Pahlavi', 'xx-Phli'),
                 ('X_Inscriptional_Parthian', 'xx-Prti'),
                 ('X_Javanese', 'xx-Java'),
                 ('X_KLINGON', 'tlh'),
                 ('X_Kaithi', 'xx-Kthi'),
                 ('X_Kannada', 'xx-Knda'),
                 ('X_Katakana', 'xx-Kana'),
                 ('X_Kayah_Li', 'xx-Kali'),
                 ('X_Kharoshthi', 'xx-Khar'),
                 ('X_Khmer', 'xx-Khmr'),
                 ('X_Lao', 'xx-Laoo'),
                 ('X_Latin', 'xx-Latn'),
                 ('X_Lepcha', 'xx-Lepc'),
                 ('X_Limbu', 'xx-Limb'),
                 ('X_Linear_B', 'xx-Linb'),
                 ('X_Lisu', 'xx-Lisu'),
                 ('X_Lycian', 'xx-Lyci'),
                 ('X_Lydian', 'xx-Lydi'),
                 ('X_Malayalam', 'xx-Mlym'),
                 ('X_Mandaic', 'xx-Mand'),
                 ('X_Meetei_Mayek', 'xx-Mtei'),
                 ('X_Meroitic_Cursive', 'xx-Merc'),
                 ('X_Meroitic_Hieroglyphs', 'xx-Mero'),
                 ('X_Miao', 'xx-Plrd'),
                 ('X_Mongolian', 'xx-Mong'),
                 ('X_Myanmar', 'xx-Mymr'),
                 ('X_New_Tai_Lue', 'xx-Talu'),
                 ('X_Nko', 'xx-Nkoo'),
                 ('X_Ogham', 'xx-Ogam'),
                 ('X_Ol_Chiki', 'xx-Olck'),
                 ('X_Old_Italic', 'xx-Ital'),
                 ('X_Old_Persian', 'xx-Xpeo'),
                 ('X_Old_South_Arabian', 'xx-Sarb'),
                 ('X_Old_Turkic', 'xx-Orkh'),
                 ('X_Oriya', 'xx-Orya'),
                 ('X_Osmanya', 'xx-Osma'),
                 ('X_PIG_LATIN', 'zzp'),
                 ('X_Phags_Pa', 'xx-Phag'),
                 ('X_Phoenician', 'xx-Phnx'),
                 ('X_Rejang', 'xx-Rjng'),
                 ('X_Runic', 'xx-Runr'),
                 ('X_Samaritan', 'xx-Samr'),
                 ('X_Saurashtra', 'xx-Saur'),
                 ('X_Sharada', 'xx-Shrd'),
                 ('X_Shavian', 'xx-Shaw'),
                 ('X_Sinhala', 'xx-Sinh'),
                 ('X_Sora_Sompeng', 'xx-Sora'),
                 ('X_Sundanese', 'xx-Sund'),
                 ('X_Syloti_Nagri', 'xx-Sylo'),
                 ('X_Syriac', 'xx-Syrc'),
                 ('X_Tagalog', 'xx-Tglg'),
                 ('X_Tagbanwa', 'xx-Tagb'),
                 ('X_Tai_Le', 'xx-Tale'),
                 ('X_Tai_Tham', 'xx-Lana'),
                 ('X_Tai_Viet', 'xx-Tavt'),
                 ('X_Takri', 'xx-Takr'),
                 ('X_Tamil', 'xx-Taml'),
                 ('X_Telugu', 'xx-Telu'),
                 ('X_Thaana', 'xx-Thaa'),
                 ('X_Thai', 'xx-Thai'),
                 ('X_Tibetan', 'xx-Tibt'),
                 ('X_Tifinagh', 'xx-Tfng'),
                 ('X_Ugaritic', 'xx-Ugar'),
                 ('X_Vai', 'xx-Vaii'),
                 ('X_Yi', 'xx-Yiii'),
                 ('YIDDISH', 'yi'),
                 ('YORUBA', 'yo'),
                 ('ZHUANG', 'za'),
                 ('ZULU', 'zu'))
    lang_code = lang_code.lower()
    for name, code in LANGUAGES:
        if code == lang_code:
            return name.lower().capitalize()
    lang_code = lang_code.split("-")[0]
    for name, code in LANGUAGES:
        if code == lang_code:
            return name.lower().capitalize()
    return "Unknown"


def get_lang_config():
    config = Configuration.get()
    lang_config = config.get("language", {})
    lang_config["internal"] = lang_config.get("internal") or config.get("lang", "en-us")
    lang_config["user"] = lang_config.get("user") or config.get("lang", "en-us")
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


class LanguageDetector:
    def __init__(self):
        self.config = get_lang_config()
        self.default_language = self.config["user"].split("-")[0]
        # hint_language: str  E.g., 'ITALIAN' or 'it' boosts Italian
        self.hint_language = self.config["user"].split("-")[0]
        self.boost = self.config["boost"]

    def detect(self, text):
        # assume default language
        return self.default_language

    def detect_probs(self, text):
        return {self.detect(text): 1}


class LanguageTranslator:
    def __init__(self):
        self.config = get_lang_config()
        self.boost = self.config["boost"]
        self.default_language = self.config["user"].split("-")[0]
        self.internal_language = self.config["internal"]

    def translate(self, text, target=None, source=None):
        return text


class Pycld2Detector(LanguageDetector):
    def __init__(self):
        super().__init__()
        import pycld2
        self.cld2 = pycld2

    def cl2_detect(self, text, return_multiple=False, return_dict=False,
                   hint_language=None, filter_unreliable=False):
        """
        :param text:
        :param return_multiple bool if True return a list of all languages detected, else the top language
        :param return_dict: bool  if True returns all data, E.g.,  pt -> {'lang': 'Portuguese', 'lang_code': 'pt', 'conf': 0.96}
        :param hint_language: str  E.g., 'ITALIAN' or 'it' boosts Italian
        :return:
        """
        isReliable, textBytesFound, details = self.cld2.detect(
            text, hintLanguage=hint_language)
        languages = []

        # filter unreliable predictions
        if not isReliable and filter_unreliable:
            return None

        # select first language only
        if not return_multiple:
            details = [details[0]]

        for name, code, score, _ in details:
            if code == "un":
                continue
            if return_dict:
                languages.append({"lang": name.lower().capitalize(),
                                  "lang_code": code, "conf": score / 100})
            else:
                languages.append(code)

        # return top language only
        if not return_multiple:
            if not len(languages):
                return None
            return languages[0]
        return languages

    def detect(self, text):
        if self.boost:
            return self.cl2_detect(text, hint_language=self.hint_language) or \
                   self.default_language
        else:
            return self.cl2_detect(text) or self.default_language

    def detect_probs(self, text):
        if self.boost:
            data = self.cl2_detect(text, return_multiple=True,
                                   return_dict=True,
                                   hint_language=self.hint_language)
        else:
            data = self.cl2_detect(text, return_multiple=True,
                                   return_dict=True)
        langs = {}
        for lang in data:
            langs[lang["lang_code"]] = lang["conf"]
        return langs


class Pycld3Detector(LanguageDetector):
    def __init__(self):
        super().__init__()
        import cld3
        self.cld3 = cld3

    def cld3_detect(self, text, return_multiple=False, return_dict=False,
                    hint_language=None, filter_unreliable=False):
        languages = []
        if return_multiple or hint_language:
            preds = sorted(self.cld3.get_frequent_languages(text, num_langs=5),
                           key=lambda i: i.probability, reverse=True)
            for pred in preds:
                if filter_unreliable and not pred.is_reliable:
                    continue
                if return_dict:
                    languages += [{"lang_code": pred.language,
                                   "lang": langcode2name(pred.language),
                                   "conf": pred.probability}]
                else:
                    languages.append(pred.language)

                if hint_language and hint_language == pred.language:
                    languages = [languages[-1]]
                    break
        else:
            pred = self.cld3.get_language(text)
            if filter_unreliable and not pred.is_reliable:
                pass
            elif return_dict:
                languages = [{"lang_code": pred.language,
                              "lang": langcode2name(pred.language),
                              "conf": pred.probability}]
            else:
                languages = [pred.language]

        # return top language only
        if not return_multiple:
            if not len(languages):
                return None
            return languages[0]
        return languages

    def detect(self, text):
        if self.boost:
            return self.cld3_detect(text, hint_language=self.hint_language) or \
                   self.default_language
        else:
            return self.cld3_detect(text) or self.default_language

    def detect_probs(self, text):
        if self.boost:
            data = self.cld3_detect(text, return_multiple=True,
                                    return_dict=True,
                                    hint_language=self.hint_language)
        else:
            data = self.cld3_detect(text, return_multiple=True,
                                    return_dict=True)
        langs = {}
        for lang in data:
            langs[lang["lang_code"]] = lang["conf"]
        return langs


class GoogleDetector(LanguageDetector):
    def __init__(self):
        super().__init__()
        from google_trans_new import google_translator
        self.translator = google_translator()

    def detect(self, text):
        tx = self.translator.detect(text)
        return tx[0] or self.default_language

    def detect_probs(self, text):
        tx = self.translator.detect(text)
        return {"lang_code": tx[0], "lang": tx[1]}


class FastLangDetector(LanguageDetector):
    def __init__(self):
        super().__init__()
        try:
            from fastlang import fastlang
        except ImportError:
            LOG.error("Run pip install fastlang")
            raise
        self._detect = fastlang

    def detect(self, text):
        return self._detect(text)["lang"]

    def detect_probs(self, text):
        return self._detect(text)["probabilities"]


class LangDetectDetector(LanguageDetector):
    def __init__(self):
        super().__init__()
        try:
            from langdetect import detect, detect_langs
        except ImportError:
            LOG.error("Run pip install langdetect")
            raise
        self._detect = detect
        self._detect_prob = detect_langs

    def detect(self, text):
        return self._detect(text)

    def detect_probs(self, text):
        langs = {}
        for lang in self._detect_prob(text):
            langs[lang.lang] = lang.prob
        return langs


class GoogleTranslator(LanguageTranslator):
    def __init__(self):
        super().__init__()
        from google_trans_new import google_translator
        self.translator = google_translator()

    def translate(self, text, target=None, source=None):
        if self.boost and not source:
            source = self.default_language
        target = target or self.internal_language
        if source:
            tx = self.translator.translate(text, lang_src=source.split("-")[0],
                                           lang_tgt=target.split("-")[0])
        else:
            tx = self.translator.translate(text, lang_tgt=target.split("-")[0])
        return tx.strip()


class AmazonTranslator(LanguageTranslator):
    def __init__(self):
        super().__init__()
        self.keys = get_private_keys()["amazon"]
        self.client = boto3.Session(aws_access_key_id=self.keys["key_id"],
                                    aws_secret_access_key=self.keys["secret_key"],
                                    region_name=self.keys["region"]).client('translate')

    def translate(self, text, target=None, source="auto"):
        target = target or self.internal_language

        response = self.client.translate_text(
            Text=text,
            SourceLanguageCode="auto",
            TargetLanguageCode=target.split("-")[0]
        )
        return response["TranslatedText"]


class AmazonDetector(LanguageDetector):
    def __init__(self):
        super().__init__()
        self.keys = get_private_keys()["amazon"]
        self.client = boto3.Session(aws_access_key_id=self.keys["key_id"],
                                    aws_secret_access_key=self.keys["secret_key"],
                                    region_name=self.keys["region"]).client('comprehend')

    def detect(self, text):
        response = self.client.detect_dominant_language(
            Text=text
        )
        return response['Languages'][0]['LanguageCode']

    def detect_probs(self, text):
        response = self.client.detect_dominant_language(
            Text=text
        )
        langs = {}
        for lang in response["Languages"]:
            langs[lang["LanguageCode"]] = lang["Score"]
        return langs


class ApertiumTranslator(LanguageTranslator):
    def __init__(self):
        super().__init__()
        # host it yourself https://github.com/apertium/apertium
        self.url = self.config.get("apertium_host") or \
                   "https://www.apertium.org/apy/translate"

    def translate(self, text, target=None, source=None, url=None):
        if self.boost and not source:
            source = self.default_language
        target = target or self.internal_language
        lang_pair = target
        if source:
            lang_pair = source + "|" + target
        r = requests.get(self.url,
                         params={"q": text, "langpair": lang_pair,
                                 "markUnknown": "no"}).json()
        if r.get("status", "") == "error":
            LOG.error(r["explanation"])
            return None
        return r["responseData"]["translatedText"]


class LibreTranslateTranslator(LanguageTranslator):
    def __init__(self):
        super().__init__()
        # host it yourself https://github.com/uav4geo/LibreTranslate
        self.url = self.config.get("libretranslate_host") or \
                   "https://libretranslate.com/translate"
        self.api_key = self.config.get("key")

    def translate(self, text, target=None, source=None, url=None):
        if self.boost and not source:
            source = self.default_language
        target = target or self.internal_language
        params = {"q": text,
                  "source": source.split("-")[0],
                  "target": target.split("-")[0]}
        if self.api_key:
            params["api_key"] = self.api_key
        r = requests.post(self.url, params=params).json()
        if r.get("error"):
            return None
        return r["translatedText"]


class LibreTranslateDetector(LanguageDetector):
    def __init__(self):
        super().__init__()
        # host it yourself https://github.com/uav4geo/LibreTranslate
        self.url = self.config.get("libretranslate_host") or \
                   "https://libretranslate.com/detect"
        self.api_key = self.config.get("key")

    def detect(self, text):
        return self.detect_probs(text)[0]["language"]

    def detect_probs(self, text):
        params = {"q": text}
        if self.api_key:
            params["api_key"] = self.api_key
        return requests.post(self.url, params=params).json()


class TranslatorFactory:
    CLASSES = {
        "google": GoogleTranslator,
        "amazon": AmazonTranslator,
        "apertium": ApertiumTranslator,
        "libretranslate": LibreTranslateTranslator
    }

    @staticmethod
    def create(module=None):
        config = Configuration.get().get("language", {})
        module = module or config.get("translation_module", "google")
        try:
            clazz = TranslatorFactory.CLASSES.get(module)
            return clazz()
        except Exception as e:
            # The translate backend failed to start. Report it and fall back to
            # default.
            LOG.exception('The selected translator backend could not be loaded, '
                          'falling back to default...')
            if module != 'google':
                return GoogleTranslator()
            else:
                raise


class DetectorFactory:
    CLASSES = {
        "amazon": AmazonDetector,
        "google": GoogleDetector,
        "cld2": Pycld2Detector,
        "cld3": Pycld3Detector,
        "fastlang": FastLangDetector,
        "detect": LangDetectDetector
    }

    @staticmethod
    def create(module=None):
        config = Configuration.get().get("language", {})
        module = module or config.get("detection_module", "fastlang")
        try:
            clazz = DetectorFactory.CLASSES.get(module)
            return clazz()
        except Exception as e:
            # The translate backend failed to start. Report it and fall back to
            # default.
            LOG.exception('The selected language detector backend could not be loaded, '
                          'falling back to default...')
            if module != 'fastlang':
                return FastLangDetector()
            else:
                raise
