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

""" DisplayManager

This module provides basic "state" for the visual representation associated
with this Mycroft instance.  The current states are:
   ActiveSkill - The skill that last interacted with the display via the
                 Enclosure API.

Currently, a wakeword sets the ActiveSkill to "wakeword", which will auto
clear after 10 seconds.

A skill is set to Active when it matches an intent, outputs audio, or
changes the display via the EnclosureAPI()

A skill is automatically cleared from Active two seconds after audio
output is spoken, or 2 seconds after resetting the display.

So it is common to have '' as the active skill.
"""

import json
from threading import Timer

import os

from mycroft.messagebus import get_messagebus
from mycroft.util import get_ipc_directory
from mycroft.util.log import LOG


def _write_data(dictionary):
    """ Writes the dictionary of state data to the IPC directory.

    Args:
        dictionary (dict): information to place in the 'disp_info' file
    """

    managerIPCDir = os.path.join(get_ipc_directory(), "managers")
    # change read/write permissions based on if file exists or not
    path = os.path.join(managerIPCDir, "disp_info")
    permission = "r+" if os.path.isfile(path) else "w+"

    if permission == "w+" and os.path.isdir(managerIPCDir) is False:
        os.makedirs(managerIPCDir)
        os.chmod(managerIPCDir, 0o777)

    try:
        with open(path, permission) as dispFile:

            # check if file is empty
            if os.stat(str(dispFile.name)).st_size != 0:
                data = json.load(dispFile)

            else:
                data = {}
                LOG.info("Display Manager is creating " + dispFile.name)

            for key in dictionary:
                data[key] = dictionary[key]

            dispFile.seek(0)
            dispFile.write(json.dumps(data))
            dispFile.truncate()

        os.chmod(path, 0o777)

    except Exception as e:
        LOG.error(e)
        LOG.error("Error found in display manager file, deleting...")
        os.remove(path)
        _write_data(dictionary)


def _read_data():
    """ Writes the dictionary of state data from the IPC directory.
    Returns:
        dict: loaded state information
    """
    managerIPCDir = os.path.join(get_ipc_directory(), "managers")

    path = os.path.join(managerIPCDir, "disp_info")
    permission = "r" if os.path.isfile(path) else "w+"

    if permission == "w+" and os.path.isdir(managerIPCDir) is False:
        os.makedirs(managerIPCDir)

    data = {}
    try:
        with open(path, permission) as dispFile:

            if os.stat(str(dispFile.name)).st_size != 0:
                data = json.load(dispFile)

    except Exception as e:
        LOG.error(e)
        os.remove(path)
        _read_data()

    return data


class DisplayManager:
    """ The Display manager handles the basic state of the display,
    be it a mark-1 or a mark-2 or even a future Mark-3.
    """
    def __init__(self, name=None):
        self.name = name or ""

    def set_active(self, skill_name=None):
        """ Sets skill name as active in the display Manager
        Args:
            string: skill_name
        """
        name = skill_name if skill_name is not None else self.name
        _write_data({"active_skill": name})

    def get_active(self):
        """ Get the currenlty active skill from the display manager
        Returns:
            string: The active skill's name
        """
        data = _read_data()
        active_skill = ""

        if "active_skill" in data:
            active_skill = data["active_skill"]

        return active_skill

    def remove_active(self):
        """ Clears the active skill """
        LOG.debug("Removing active skill...")
        _write_data({"active_skill": ""})


def init_display_manager_bus_connection():
    """ Connects the display manager to the messagebus """
    LOG.info("Connecting display manager to messagebus")

    # Should remove needs to be an object so it can be referenced in functions
    # [https://stackoverflow.com/questions/986006/how-do-i-pass-a-variable-by-reference]
    display_manager = DisplayManager()
    should_remove = [True]

    def check_flag(flag):
        if flag[0] is True:
            display_manager.remove_active()

    def set_delay(event=None):
        should_remove[0] = True
        Timer(2, check_flag, [should_remove]).start()

    def set_remove_flag(event=None):
        should_remove[0] = False

    def remove_wake_word():
        data = _read_data()
        if "active_skill" in data and data["active_skill"] == "wakeword":
            display_manager.remove_active()

    def set_wakeword_skill(event=None):
        display_manager.set_active("wakeword")
        Timer(10, remove_wake_word).start()

    bus = get_messagebus()
    bus.on('recognizer_loop:audio_output_end', set_delay)
    bus.on('recognizer_loop:audio_output_start', set_remove_flag)
    bus.on('recognizer_loop:record_begin', set_wakeword_skill)
