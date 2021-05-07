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
import sys
import json
from mycroft.messagebus import send_message


def main():
    """Main function, will run if executed from command line.

    Sends parameters from commandline.

    Param 1:    message string
    Param 2:    data (json string)
    """
    # Parse the command line
    if len(sys.argv) == 2:
        message_to_send = sys.argv[1]
        data_to_send = {}
    elif len(sys.argv) == 3:
        message_to_send = sys.argv[1]
        try:
            data_to_send = json.loads(sys.argv[2])
        except BaseException:
            print("Second argument must be a JSON string")
            print("Ex: python -m mycroft.messagebus.send speak "
                  "'{\"utterance\" : \"hello\"}'")
            exit()
    else:
        print("Command line interface to the mycroft-core messagebus.")
        print("Usage: python -m mycroft.messagebus.send message")
        print("       python -m mycroft.messagebus.send message JSON-string\n")
        print("Examples: python -m mycroft.messagebus.send system.wifi.setup")
        print("Ex: python -m mycroft.messagebus.send speak "
              "'{\"utterance\" : \"hello\"}'")
        exit()

    send_message(message_to_send, data_to_send)


if __name__ == '__main__':
    try:
        main()
    except IOError:
        print('Could not connect to websocket, no message sent')
