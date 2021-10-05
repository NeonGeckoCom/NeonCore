# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Daemon launched at startup to handle skill activities.

In this repo, you will not find an entry called mycroft-skills in the bin
directory.  The executable gets added to the bin directory when installed
(see setup.py)
"""
import time

from neon_core.skills.skill_manager import NeonSkillManager
from neon_core.skills.intent_service import NeonIntentService
from neon_core.skills.fallback_skill import FallbackSkill

from neon_utils.net_utils import check_online
from neon_utils.configuration_utils import get_neon_skills_config, get_neon_lang_config

from mycroft.lock import Lock
from mycroft.util import reset_sigint_handler, start_message_bus_client, wait_for_exit_signal
from mycroft.util.lang import set_default_lang
from mycroft.util.time import set_default_tz
from mycroft.util.log import LOG
from mycroft.util.process_utils import ProcessStatus, StatusCallbackMap
from mycroft.skills.api import SkillApi
from mycroft.skills.event_scheduler import EventScheduler
from mycroft.skills.msm_wrapper import MsmException


def on_started():
    LOG.info('Skills service is starting up.')


def on_alive():
    LOG.info('Skills service is alive.')


def on_ready():
    LOG.info('Skills service is ready.')


def on_error(e='Unknown'):
    LOG.info('Skills service failed to launch ({})'.format(repr(e)))


def on_stopping():
    LOG.info('Skills service is shutting down...')


def main(alive_hook=on_alive, started_hook=on_started, ready_hook=on_ready,
         error_hook=on_error, stopping_hook=on_stopping, watchdog=None):
    reset_sigint_handler()
    # Create PID file, prevent multiple instances of this service
    Lock('skills')
    # config = Configuration.get()
    # Set the active lang to match the configured one
    set_default_lang(get_neon_lang_config().get('internal', 'en-us'))

    # Set the default timezone to match the configured one
    set_default_tz()

    # Connect this process to the Mycroft message bus
    bus = start_message_bus_client("SKILLS")
    _register_intent_services(bus)
    event_scheduler = EventScheduler(bus)
    callbacks = StatusCallbackMap(on_started=started_hook,
                                  on_alive=alive_hook,
                                  on_ready=ready_hook,
                                  on_error=error_hook,
                                  on_stopping=stopping_hook)
    status = ProcessStatus('skills', bus, callbacks)

    SkillApi.connect_bus(bus)
    skill_manager = _initialize_skill_manager(bus, watchdog)

    status.set_started()
    if get_neon_skills_config().get("wait_for_internet", True):
        _wait_for_internet_connection()
    else:
        LOG.info("Online check disabled, device may be offline")

    if skill_manager is None:
        skill_manager = _initialize_skill_manager(bus, watchdog)

    skill_manager.start()
    while not skill_manager.is_alive():
        time.sleep(0.1)
    status.set_alive()

    while not skill_manager.is_all_loaded():
        time.sleep(0.1)
    status.set_ready()

    wait_for_exit_signal()
    status.set_stopping()
    shutdown(skill_manager, event_scheduler)


def _register_intent_services(bus):
    """Start up the all intent services and connect them as needed.

    Arguments:
        bus: messagebus client to register the services on
    """
    service = NeonIntentService(bus)
    # Register handler to trigger fallback system
    bus.on(
        'mycroft.skills.fallback',
        FallbackSkill.make_intent_failure_handler(bus)
    )
    return service


def _initialize_skill_manager(bus, watchdog):
    """Create a thread that monitors the loaded skills, looking for updates

    Returns:
        SkillManager instance or None if it couldn't be initialized
    """
    try:
        skill_manager = NeonSkillManager(bus, watchdog)
        skill_manager.load_priority()
    except MsmException:
        # skill manager couldn't be created, wait for network connection and
        # retry
        skill_manager = None
        LOG.info(
            'MSM is uninitialized and requires network connection to fetch '
            'skill information\nWill retry after internet connection is '
            'established.'
        )

    return skill_manager


def _wait_for_internet_connection():
    while not check_online():
        time.sleep(1)


def shutdown(skill_manager, event_scheduler):
    LOG.info('Shutting down Skills service')
    if event_scheduler is not None:
        event_scheduler.shutdown()
    # Terminate all running threads that update skills
    if skill_manager is not None:
        skill_manager.stop()
        skill_manager.join()
    LOG.info('Skills service shutdown complete!')


if __name__ == "__main__":
    main()
