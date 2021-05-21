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
from mycroft.display.services import DisplayBackend
from mycroft.util.log import LOG
from mycroft.messagebus import Message
import imutils
import cv2
import numpy as np


class OpenCVService(DisplayBackend):
    """
        Display backend for opencv package.
    """
    def __init__(self, bus, config, name="opencv"):
        super().__init__(bus, config, name)
        self.bus.on("opencv.display", self._display)
        self.current_image = None

    def _display(self, message=None):
        self._prepare_window()
        self._is_displaying = True
        cv2.imshow("OpenCV Display", self.current_image)
        cv2.waitKey(0)

    def _prepare_window(self):
        if self._is_displaying:
            cv2.destroyWindow("OpenCV Display")

        cv2.namedWindow("OpenCV Display", cv2.WND_PROP_FULLSCREEN)
        if self.fullscreen:
            cv2.setWindowProperty("OpenCV Display", cv2.WND_PROP_FULLSCREEN,
                                  cv2.WINDOW_FULLSCREEN)
        else:
            cv2.setWindowProperty("OpenCV Display", cv2.WND_PROP_FULLSCREEN,
                                  not cv2.WINDOW_FULLSCREEN)
            cv2.resizeWindow("OpenCV Display", self.width, self.height)

    def handle_display(self, picture):
        LOG.info('Call OpenCVDisplay')
        path = picture.replace("file://", "")
        image = cv2.imread(path)
        image = imutils.resize(image, self.width, self.height)
        self.current_image = image
        # NOTE message is needed because otherwise opencv will block
        self.bus.emit(Message("opencv.display"))

    def handle_fullscreen(self, new_value, old_value):
        # re-render
        self._display()

    def handle_height_change(self, new_value, old_value):
        # re-render
        self._display()

    def handle_width_change(self, new_value, old_value):
        # re-render
        self._display()

    def handle_clear(self):
        """
            Clear Display.
        """
        # Create a black image
        image = np.zeros((512, 512, 3), np.uint8)
        if not self.fullscreen:
            image = imutils.resize(image, self.width, self.height)
        self.current_image = image
        self._display()

    def handle_close(self):
        LOG.info('OpenCVDisplayClose')
        cv2.destroyAllWindows()
        self._is_displaying = False


def load_service(base_config, bus):
    backends = base_config.get('backends', [])
    services = [(b, backends[b]) for b in backends
                if backends[b]['type'] == 'opencv']
    instances = [OpenCVService(bus, s[1], s[0]) for s in services]
    return instances
