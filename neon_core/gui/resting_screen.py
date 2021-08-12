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

import time

from threading import Lock
from neon_utils.log_utils import LOG
from mycroft_bus_client import Message, MessageBusClient
from mycroft.skills.mycroft_skill import MycroftSkill


def compare_origin(m1, m2):
    origin1 = m1.data["__from"] if isinstance(m1, Message) else m1
    origin2 = m2.data["__from"] if isinstance(m2, Message) else m2
    return origin1 == origin2


class RestingScreen:
    """
    Implementation of resting screens.
    This class handles registration and override of resting screens,
    encapsulating the system.
    """

    def __init__(self):
        skill = MycroftSkill()
        bus = MessageBusClient()
        bus.run_in_thread()
        skill.bind(bus)
        self.bus = skill.bus
        self.gui = skill.gui
        self.settings = {}
        self.schedule_event = skill.schedule_event
        self.cancel_scheduled_event = skill.cancel_scheduled_event
        self.has_show_page = False  # resets with each handler
        self.override_animations = False
        self.resting_screen = None
        
        self.screens = {}
        self.override_idle = None
        self.next = 0  # Next time the idle screen should trigger
        self.lock = Lock()
        self.override_set_time = time.monotonic()

        # Preselect Time and Date as resting screen
        self.gui["selected"] = self.settings.get("selected", "OVOSHomescreen")
        self.gui.set_on_gui_changed(self.save)
        self._init_listeners()
        self.collect()

    def _init_listeners(self):
        self.bus.on("mycroft.mark2.register_idle", self.on_register)
        self.bus.on("mycroft.mark2.reset_idle", self.restore)
        self.bus.on("mycroft.device.show.idle", self.show)
        self.bus.on("gui.page.show", self.on_gui_page_show)
        self.bus.on("gui.page_interaction", self.on_gui_page_interaction)

        self.gui.register_handler("mycroft.device.show.idle", self.show)
        self.gui.register_handler("mycroft.device.set.idle", self.set)

    def on_register(self, message):
        """Handler for catching incoming idle screens."""
        if "name" in message.data and "id" in message.data:
            self.screens[message.data["name"]] = message.data["id"]
            LOG.info("Registered {}".format(message.data["name"]))
        else:
            LOG.error("Malformed idle screen registration received")

    def save(self):
        """Handler to be called if the settings are changed by the GUI.
        Stores the selected idle screen.
        """
        LOG.debug("Saving resting screen")
        self.settings["selected"] = self.gui["selected"]
        self.gui["selectedScreen"] = self.gui["selected"]

    def collect(self):
        """Trigger collection and then show the resting screen."""
        self.bus.emit(Message("mycroft.mark2.collect_idle"))
        time.sleep(1)
        self.show()

    def set(self, message):
        """Set selected idle screen from message."""
        self.gui["selected"] = message.data["selected"]
        self.save()

    def show(self, _=None):
        """Show the idle screen or return to the skill that's overriding idle."""
        LOG.debug("Showing idle screen")
        screen = None
        if self.override_idle:
            LOG.debug("Returning to override idle screen")
            # Restore the page overriding idle instead of the normal idle
            self.bus.emit(self.override_idle[0])
        elif len(self.screens) > 0 and "selected" in self.gui:
            # TODO remove hard coded value
            LOG.info("Showing Idle screen for " "{}".format(self.gui["selected"]))
            screen = self.screens.get(self.gui["selected"])

        LOG.info(screen)
        if screen:
            self.bus.emit(Message("{}.idle".format(screen)))

    def restore(self, _=None):
        """Remove any override and show the selected resting screen."""
        if self.override_idle and time.monotonic() - self.override_idle[1] > 2:
            self.override_idle = None
            self.show()

    def stop(self):
        if time.monotonic() > self.override_set_time + 7:
            self.restore()

    def override(self, message=None):
        """Override the resting screen.
        Arguments:
            message: Optional message to use for to restore
                     the expected override screen after
                     another screen has been displayed.
        """
        self.override_set_time = time.monotonic()
        if message:
            self.override_idle = (message, time.monotonic())

    def cancel_override(self):
        """Remove the override screen."""
        self.override_idle = None

    def on_gui_page_interaction(self, _):
        """ Reset idle timer to 30 seconds when page is flipped. """
        LOG.info("Resetting idle counter to 30 seconds")
        self.start_idle_event(30)

    def on_gui_page_show(self, message):
        # Some skill other than the handler is showing a page
        self.has_show_page = True

        # If a skill overrides the animations do not show any
        override_animations = message.data.get("__animations", False)
        if override_animations:
            # Disable animations
            LOG.info("Disabling all animations for page")
            self.override_animations = True
        else:
            LOG.info("Displaying all animations for page")
            self.override_animations = False

        # If a skill overrides the idle do not switch page
        override_idle = message.data.get("__idle")
        if override_idle is True:
            # Disable idle screen
            LOG.info("Cancelling Idle screen")
            self.cancel_idle_event()
            self.override(message)
        elif isinstance(override_idle, int) and override_idle is not False:
            LOG.info(
                "Overriding idle timer to" " {} seconds".format(override_idle)
            )
            self.override(None)
            self.start_idle_event(override_idle)
        elif message.data["page"] and not message.data["page"][0].endswith(
                "idle.qml"
        ):
            # Check if the show_page deactivates a previous idle override
            # This is only possible if the page is from the same skill
            LOG.info("Cancelling idle override")
            if override_idle is False and compare_origin(
                    message, self.override_idle[0]
            ):
                # Remove the idle override page if override is set to false
                self.cancel_override()
            # Set default idle screen timer
            self.start_idle_event(30)

    def cancel_idle_event(self):
        """Cancel the event monitoring current system idle time."""
        self.next = 0
        self.cancel_scheduled_event("IdleCheck")

    def start_idle_event(self, offset=60, weak=False):
        """Start an event for showing the idle screen.
        Arguments:
            offset: How long until the idle screen should be shown
            weak: set to true if the time should be able to be overridden
        """
        with self.lock:
            if time.monotonic() + offset < self.next:
                LOG.info("No update, before next time")
                return

            LOG.info("Starting idle event")
            try:
                if not weak:
                    self.next = time.monotonic() + offset
                # Clear any existing checker
                self.cancel_scheduled_event("IdleCheck")
                time.sleep(0.5)
                self.schedule_event(
                    self.show, int(offset), name="IdleCheck"
                )
                LOG.info("Showing idle screen in " "{} seconds".format(offset))
            except Exception as e:
                LOG.exception(repr(e))
