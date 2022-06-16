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

import json
import socket

from neon_utils import LOG
from neon_utils.metrics_utils import report_metric
from neon_utils.configuration_utils import NGIConfig


def send_diagnostics(allow_logs=True, allow_transcripts=True, allow_config=True):
    """
    Uploads diagnostics to the configured server. Default data includes start.log and basic system information.
    If logs are allowed, current core logs will be uploaded.
    If transcripts are allowed, recent transcripts will be uploaded.
    If config is allowed, local and user configuration files will be uploaded.
    :param allow_logs: Allows uploading current log files
    :param allow_transcripts: Allows uploading recent transcriptions
    :param allow_config: Allows uploading Neon config files
    """
    LOG.info(f"Sending Diagnostics: logs={allow_logs} transcripts={allow_transcripts} config={allow_config}")
    # Get Configurations
    local_configuration = NGIConfig("ngi_local_conf").content
    user_configuration = NGIConfig("ngi_user_info").content
    # auth_configuration = NGIConfig("ngi_auth_vars").content
    if allow_config:
        configs = {"local": local_configuration,
                   "user": user_configuration}
    else:
        configs = None

    # Get Logs
    # logs_dir = os.path.expanduser(local_configuration["dirVars"]["logsDir"])
    # startup_log = os.path.join(logs_dir, "start.log")
    # if os.path.isfile(startup_log):
    #     with open(startup_log, 'r') as start:
    #         startup = start.read()
    #         # Catch a very large log and take last 100000 chars, rounded to a full line
    #         if len(startup) > 100000:
    #             startup = startup[-100000:].split("\n", 1)[1]
    # else:
    #     startup = None
    # if allow_logs:
    #     logs = dict()
    #     try:
    #         LOG.info(f"Reading logs from: {logs_dir}")
    #         for log in glob.glob(f'{logs_dir}/*.log'):
    #             if os.path.basename(log) == "start.log":
    #                 pass
    #             with open(log, 'r') as f:
    #                 contents = f.read()
    #                 # Catch a very large log and take last 100000 chars, rounded to a full line
    #                 if len(contents) > 100000:
    #                     contents = contents[-100000:].split("\n", 1)[1]
    #                 logs[os.path.basename(os.path.splitext(log)[0])] = contents
    #         # TODO: + last few archived logs, testing logs DM
    #     except Exception as e:
    #         LOG.error(e)
    # else:
    logs = None

    # transcript_file = os.path.join(os.path.expanduser(local_configuration["dirVars"]["docsDir"]),
    #                                "csv_files", "full_ts.csv")
    # if allow_transcripts and os.path.isfile(transcript_file):
    #     with open(transcript_file, "r") as f:
    #         lines = f.readlines()
    #         try:
    #             transcripts = lines[-500:]
    #         except Exception as e:
    #             LOG.error(e)
    #             transcripts = lines
    #         transcripts = "".join(transcripts)
    # else:
    transcripts = None

    data = {"host": socket.gethostname(),
            "startup": None,
            "configurations": json.dumps(configs) if configs else None,
            "logs": json.dumps(logs) if logs else None,
            "transcripts": transcripts}
    report_metric("diagnostics", **data)
    return data


def cli_send_diags():
    """
    CLI Entry Point to Send Diagnostics
    """
    LOG.warning(f"This function is deprecated. Use `neon upload-diagnostics`")
    import argparse
    parser = argparse.ArgumentParser(description="Upload Neon Diagnostics Files", add_help=True)
    parser.add_argument("--no-transcripts", dest="transcripts", default=True, action='store_false',
                        help="Disable upload of all transcribed input")
    parser.add_argument("--no-logs", dest="logs", default=True, action='store_false',
                        help="Disable upload of Neon log files (NOTE: start_neon.log is always uploaded)")
    parser.add_argument("--no-config", dest="config", default=True, action='store_false',
                        help="Disable upload of Neon config files")

    args = parser.parse_args()
    send_diagnostics(args.logs, args.transcripts, args.config)
