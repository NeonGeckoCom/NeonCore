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
import socketserver
import http.server

from tempfile import gettempdir
from os.path import isdir, join, dirname
from threading import Thread, Event
from neon_utils.logger import LOG

_HTTP_SERVER: socketserver.TCPServer = None


class QmlFileHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        mimetype = self.guess_type(self.path)
        is_file = not self.path.endswith('/')
        if is_file and any([mimetype.startswith(prefix) for
                           prefix in ("text/", "application/octet-stream")]):
            self.send_header('Content-Type', "text/plain")
            self.send_header('Content-Disposition', 'inline')
        super().end_headers()


def start_qml_http_server(skills_dir: str, port: int = 8000):
    if not isdir(skills_dir):
        os.makedirs(skills_dir)
    system_dir = join(dirname(dirname(__file__)), "res")

    qml_dir = join(gettempdir(), "neon", "qml")
    if not isdir(qml_dir):
        os.makedirs(qml_dir)

    served_skills_dir = join(qml_dir, "skills")
    served_system_dir = join(qml_dir, "system")

    # If serving from a temporary linked directory, create a fresh symlink
    if skills_dir != served_skills_dir:
        LOG.info(f"Linking {skills_dir} to {served_skills_dir}")
        if os.path.exists(served_skills_dir) or os.path.islink(served_skills_dir):
            os.remove(served_skills_dir)
        os.symlink(skills_dir, served_skills_dir)

    if os.path.exists(served_system_dir) or os.path.islink(served_system_dir):
        os.remove(served_system_dir)
    os.symlink(system_dir, served_system_dir)
    started_event = Event()
    http_daemon = Thread(target=_initialize_http_server,
                         args=(started_event, qml_dir, port),
                         daemon=True)
    http_daemon.start()
    started_event.wait(30)
    return _HTTP_SERVER


def _initialize_http_server(started: Event, directory: str, port: int):
    global _HTTP_SERVER
    os.chdir(directory)
    handler = QmlFileHandler
    http_server = socketserver.TCPServer(("", port), handler)
    _HTTP_SERVER = http_server
    started.set()
    http_server.serve_forever()
