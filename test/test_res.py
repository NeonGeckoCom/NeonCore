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

import os
import sys
import unittest

from os.path import join, isfile

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class ResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pass

    def test_resolve_resource_file(self):
        import neon_core  # Ensure neon_core is imported
        from mycroft.util.file_utils import resolve_resource_file
        for file in ("hey-neon.pb", "hey-neon.pb.params"):
            self.assertTrue(isfile(resolve_resource_file(join("precise_models",
                                                              file))))
        for file in ("acknowledge.mp3", "beep.wav", "loaded.wav",
                     "start_listening.wav"):
            self.assertTrue(isfile(resolve_resource_file(join("snd",
                                                              file))))
        for file in ("neon_logo.png", "SYSTEM_AnimatedImageFrame.qml",
                     "SYSTEM_HtmlFrame.qml", "SYSTEM_TextFrame.qml",
                     "SYSTEM_UrlFrame.qml", "WebViewHtmlFrame.qml",
                     "WebViewUrlFrame.qml"):
            self.assertTrue(isfile(resolve_resource_file(join("ui",
                                                              file))))
        for file in ("cancel.voc", "i didn't catch that.dialog",
                     "neon.voc", "no.voc", "not.loaded.dialog",
                     "not connected to the internet.dialog",
                     "phonetic_spellings.txt", "skill.error.dialog",
                     "skills updated.dialog", "yes.voc"):
            self.assertTrue(isfile(resolve_resource_file(join("text", "en-us",
                                                              file))))

        for lang in ("en-au", "en-us", "en-uk", "uk-ua", "ru-ru"):
            self.assertTrue(isfile(resolve_resource_file(join("text", lang,
                                                              "neon.voc"))))


if __name__ == '__main__':
    unittest.main()
