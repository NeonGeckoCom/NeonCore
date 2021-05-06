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
import json
import threading
import time

import requests

from mycroft.api import DeviceApi, is_paired, is_disabled
from mycroft.configuration import Configuration
from mycroft.session import SessionManager
from mycroft.util.log import LOG
from mycroft.version import CORE_VERSION_STR
from copy import copy


def report_metric(name, data):
    """
    Report a general metric to the Mycroft servers

    Args:
        name (str): Name of metric. Must use only letters and hyphens
        data (dict): JSON dictionary to report. Must be valid JSON
    """
    if is_disabled():
        return
    try:
        if is_paired() and Configuration().get()['opt_in']:
            DeviceApi().report_metric(name, data)
    except requests.RequestException as e:
        LOG.error('Metric couldn\'t be uploaded, due to a network error ({})'
                  .format(e))


def report_timing(ident, system, timing, additional_data=None):
    """
        Create standardized message for reporting timing.

        ident (str):            identifier of user interaction
        system (str):           system the that's generated the report
        timing (stopwatch):     Stopwatch object with recorded timing
        additional_data (dict): dictionary with related data
    """
    additional_data = additional_data or {}
    report = copy(additional_data)
    report['id'] = ident
    report['system'] = system
    report['start_time'] = timing.timestamp
    report['time'] = timing.time

    report_metric('timing', report)


class Stopwatch:
    """
        Simple time measuring class.
    """
    def __init__(self):
        self.timestamp = None
        self.time = None

    def start(self):
        """
            Start a time measurement
        """
        self.timestamp = time.time()

    def lap(self):
        cur_time = time.time()
        start_time = self.timestamp
        self.timestamp = cur_time
        return cur_time - start_time

    def stop(self):
        """
            Stop a running time measurement. returns the measured time
        """
        cur_time = time.time()
        start_time = self.timestamp
        self.time = cur_time - start_time
        return self.time

    def __enter__(self):
        """
            Start stopwatch when entering with-block.
        """
        self.start()

    def __exit__(self, tpe, value, tb):
        """
            Stop stopwatch when exiting with-block.
        """
        self.stop()

    def __str__(self):
        cur_time = time.time()
        if self.timestamp:
            return str(self.time or cur_time - self.timestamp)
        else:
            return 'Not started'


class MetricsAggregator:
    """
    MetricsAggregator is not threadsafe, and multiple clients writing the
    same metric "concurrently" may result in data loss.
    """

    def __init__(self):
        self._counters = {}
        self._timers = {}
        self._levels = {}
        self._attributes = {}
        self.attr("version", CORE_VERSION_STR)

    def increment(self, name, value=1):
        cur = self._counters.get(name, 0)
        self._counters[name] = cur + value

    def timer(self, name, value):
        cur = self._timers.get(name)
        if not cur:
            self._timers[name] = []
            cur = self._timers[name] = []
        cur.append(value)

    def level(self, name, value):
        self._levels[name] = value

    def clear(self):
        self._counters = {}
        self._timers = {}
        self._levels = {}
        self._attributes = {}
        self.attr("version", CORE_VERSION_STR)

    def attr(self, name, value):
        self._attributes[name] = value

    def flush(self):
        publisher = MetricsPublisher()
        payload = {
            'counters': self._counters,
            'timers': self._timers,
            'levels': self._levels,
            'attributes': self._attributes
        }
        self.clear()
        count = (len(payload['counters']) + len(payload['timers']) +
                 len(payload['levels']))
        if count > 0:
            # LOG.debug(json.dumps(payload))

            def publish():
                publisher.publish(payload)

            threading.Thread(target=publish).start()


class MetricsPublisher:
    def __init__(self, url=None, enabled=False):
        conf = Configuration().get()['server']
        self.url = url or conf['url']
        self.enabled = enabled or conf['metrics']
        if conf.get("disabled", True):
            self.enabled = False

    def publish(self, events):
        if 'session_id' not in events:
            session_id = SessionManager.get().session_id
            events['session_id'] = session_id
        if self.enabled:
            requests.post(
                self.url,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(events), verify=False)
