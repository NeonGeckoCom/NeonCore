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

"""Events with respect for montonic time.

The MonotonicEvent class defined here wraps the normal class ensuring that
changes in system time are handled.
"""
from threading import Event
from time import sleep, monotonic

from mycroft.util.log import LOG


class MonotonicEvent(Event):
    """Event class with monotonic timeout.

    Normal Event doesn't do wait timeout in a monotonic manner and may be
    affected by changes in system time. This class wraps the Event class
    wait() method with logic guards ensuring monotonic operation.
    """
    def wait_timeout(self, timeout):
        """Handle timeouts in a monotonic way.

        Repeatingly wait as long the event hasn't been set and the
        monotonic time doesn't indicate a timeout.

        Arguments:
            timeout: timeout of wait in seconds

        Returns:
            True if Event has been set, False if timeout expired
        """
        result = False
        end_time = monotonic() + timeout

        while not result and (monotonic() < end_time):
            # Wait however many seconds are left until the timeout has passed
            sleep(0.1)  # Mainly a precaution to not busy wait
            remaining_time = end_time - monotonic()
            LOG.debug('Will wait for {} sec for Event'.format(remaining_time))
            result = super().wait(remaining_time)

        return result

    def wait(self, timeout=None):
        if timeout is None:
            ret = super().wait()
        else:
            ret = self.wait_timeout(timeout)
        return ret
