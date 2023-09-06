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

import shutil

from os import makedirs
from os.path import expanduser, isdir, exists, join, isfile
from ovos_utils.xdg_utils import xdg_config_home


def export_user_config(output_path: str, config_path: str = None) -> str:
    """
    Export user configuration to an archive for backup/migration
    @param output_path: Directory to write output archive to
    @param config_path: Configuration path to export (else use XDG)
    @return: Path to generated output file
    """
    output_path = join(expanduser(output_path), "neon_export")
    if exists(output_path) and not isdir(output_path):
        raise FileExistsError(f"Expected output directory but got file: "
                              f"{output_path}")
    if exists(f"{output_path}.zip"):
        raise FileExistsError(f"Export already exists: {output_path}.zip")
    config_path = config_path or join(xdg_config_home(), "neon")
    shutil.copytree(config_path, output_path)
    output_file = shutil.make_archive(output_path, "zip", config_path,
                                      config_path)
    shutil.rmtree(output_path)
    return output_file


def import_user_config(input_file: str, config_path: str = None) -> str:
    """
    Export user configuration to an archive for backup/migration
    @param input_file: Exported configuration archive to import
    @param config_path: Configuration path to import to (else use XDG)
    @return: Path configuration was imported to
    """
    input_file = expanduser(input_file)
    if not isfile(input_file):
        raise FileNotFoundError(f"Invalid input file: {input_file}")
    config_path = config_path or join(xdg_config_home(), "neon")
    shutil.unpack_archive(input_file, config_path, "zip")
    return config_path
