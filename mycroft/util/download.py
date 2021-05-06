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
from threading import Thread

import os
import requests
from os.path import exists, dirname
import subprocess

_running_downloads = {}


def _get_download_tmp(dest):
    tmp_base = dest + '.part'
    if not exists(tmp_base):
        return tmp_base
    else:
        i = 1
        while(True):
            tmp = tmp_base + '.' + str(i)
            if not exists(tmp):
                return tmp
            else:
                i += 1


class Downloader(Thread):
    """
        Downloader is a thread based downloader instance when instanciated
        it will download the provided url to a file on disk.

        When the download is complete or failed the `.done` property will
        be set to true and the `.status` will indicate the status code.
        200 = Success.

        Args:
            url:            Url to download
            dest:           Path to save data to
            complet_action: Function to run when download is complete.
                            `func(dest)`
    """

    def __init__(self, url, dest, complete_action=None, header=None):
        super(Downloader, self).__init__()
        self.url = url
        self.dest = dest
        self.complete_action = complete_action
        self.status = None
        self.done = False
        self._abort = False
        self.header = header

        # Create directories as needed
        if not exists(dirname(dest)):
            os.makedirs(dirname(dest))

        #  Start thread
        self.daemon = True
        self.start()

    def perform_download(self, dest):

        cmd = ['wget', '-c', self.url, '-O', dest,
               '--tries=20', '--read-timeout=5']
        if self.header:
            cmd += ['--header={}'.format(self.header)]
        return subprocess.call(cmd)

    def run(self):
        """
            Does the actual download.
        """
        tmp = _get_download_tmp(self.dest)
        self.status = self.perform_download(tmp)

        if not self._abort and self.status == 0:
            self.finalize(tmp)
        else:
            self.cleanup(tmp)
        self.done = True
        arg_hash = hash(self.url + self.dest)

        #  Remove from list of currently running downloads
        if arg_hash in _running_downloads:
            _running_downloads.pop(arg_hash)

    def finalize(self, tmp):
        """
            Move the .part file to the final destination and perform any
            actions that should be performed at completion.
        """
        os.rename(tmp, self.dest)
        if self.complete_action:
            self.complete_action(self.dest)

    def cleanup(self, tmp):
        """
            Cleanup after download attempt
        """
        if exists(tmp):
            os.remove(self.dest + '.part')
        if self.status == 200:
            self.status = -1

    def abort(self):
        """
            Abort download process
        """
        self._abort = True


def download(url, dest, complete_action=None, header=None):
    global _running_downloads
    arg_hash = hash(url + dest)
    if arg_hash not in _running_downloads:
        _running_downloads[arg_hash] = Downloader(url, dest, complete_action,
                                                  header)
    return _running_downloads[arg_hash]
