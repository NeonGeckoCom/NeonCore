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

from mycroft.lock import Lock
from mycroft.util import wait_for_exit_signal, reset_sigint_handler

from neon_audio.service import NeonPlaybackService
from neon_messagebus.service import NeonBusService
from neon_core.skills.service import NeonSkillService
from neon_gui.service import NeonGUIService
from neon_speech.service import NeonSpeechClient


def main():
    reset_sigint_handler()
    # Create PID file, prevent multiple instances of this service
    # TODO should also detect old services Locks
    lock = Lock("NeonCore")

    # launch websocket listener
    bus = NeonBusService(daemonic=True)
    bus.start()
    bus.started.wait(30)

    # launch GUI websocket listener
    gui = NeonGUIService(daemonic=True)
    gui.start()

    # launch skills service
    skills = NeonSkillService(daemonic=True)
    skills.start()

    # launch speech service
    speech = NeonSpeechClient(daemonic=True)
    speech.start()

    # launch audio playback service
    audio = NeonPlaybackService(daemonic=True)
    audio.start()

    wait_for_exit_signal()

    for service in (audio, speech, skills, gui, bus):
        service.shutdown()
        if service.is_alive():
            print(f"{service} not shutdown")
        try:
            service.join()
        except Exception as e:
            print(e)
    lock.delete()
    print("Stopped!!")


if __name__ == "__main__":
    main()
