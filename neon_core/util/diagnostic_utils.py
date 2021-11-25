# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
#
# Notice of License - Duplicating this Notice of License near the start of any file containing
# a derivative of this software is a condition of license for this software.
# Friendly Licensing:
# No charge, open source royalty free use of the Neon AI software source and object is offered for
# educational users, noncommercial enthusiasts, Public Benefit Corporations (and LLCs) and
# Social Purpose Corporations (and LLCs). Developers can contact developers@neon.ai
# For commercial licensing, distribution of derivative works or redistribution please contact licenses@neon.ai
# Distributed on an "AS IS” basis without warranties or conditions of any kind, either express or implied.
# Trademarks of Neongecko: Neon AI(TM), Neon Assist (TM), Neon Communicator(TM), Klat(TM)
# Authors: Guy Daniels, Daniel McKnight, Regina Bloomstine, Elon Gasper, Richard Leeds
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2021: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending
import json
import socket
import glob
import os

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
    logs_dir = os.path.expanduser(local_configuration["dirVars"]["logsDir"])
    startup_log = os.path.join(logs_dir, "start.log")
    if os.path.isfile(startup_log):
        with open(startup_log, 'r') as start:
            startup = start.read()
            # Catch a very large log and take last 100000 chars, rounded to a full line
            if len(startup) > 100000:
                startup = startup[-100000:].split("\n", 1)[1]
    else:
        startup = None
    if allow_logs:
        logs = dict()
        try:
            for log in glob.glob(f'{logs_dir}/*.log'):
                if os.path.basename(log) == "start.log":
                    pass
                with open(log, 'r') as f:
                    contents = f.read()
                    # Catch a very large log and take last 100000 chars, rounded to a full line
                    if len(contents) > 100000:
                        contents = contents[-100000:].split("\n", 1)[1]
                    logs[os.path.basename(os.path.splitext(log)[0])] = contents
            # TODO: + last few archived logs, testing logs DM
        except Exception as e:
            LOG.error(e)
    else:
        logs = None

    transcript_file = os.path.join(os.path.expanduser(local_configuration["dirVars"]["docsDir"]),
                                   "csv_files", "full_ts.csv")
    if allow_transcripts and os.path.isfile(transcript_file):
        with open(transcript_file, "r") as f:
            lines = f.readlines()
            try:
                transcripts = lines[-500:]
            except Exception as e:
                LOG.error(e)
                transcripts = lines
            transcripts = "".join(transcripts)
    else:
        transcripts = None

    data = {"host": socket.gethostname(),
            "startup": startup,
            "configurations": json.dumps(configs) if configs else None,
            "logs": json.dumps(logs) if logs else None,
            "transcripts": transcripts}
    report_metric("diagnostics", **data)
    return data


def cli_send_diags():
    """
    CLI Entry Point to Send Diagnostics
    """
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
