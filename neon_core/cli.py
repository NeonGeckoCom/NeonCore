# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2025 Neongecko.com Inc.
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

from threading import Thread

import click

from click_default_group import DefaultGroup
from neon_utils.packaging_utils import get_neon_core_version


@click.group("neon", cls=DefaultGroup,
             no_args_is_help=True, invoke_without_command=True,
             help="Neon Core Commands\n\n"
                  "See also: neon COMMAND --help")
@click.option("--version", "-v", is_flag=True, required=False,
              help="Print the current version")
def neon_core_cli(version: bool = False):
    if version:
        click.echo(f"Neon version {get_neon_core_version()}")


@neon_core_cli.command(help="Start Neon Core")
def start_neon():
    from neon_core.run_neon import start_neon
    click.echo("Starting Neon")
    Thread(target=start_neon, daemon=False).start()
    click.echo("Neon Started")


@neon_core_cli.command(help="Stop Neon Core")
def stop_neon():
    from neon_core.run_neon import stop_neon
    click.echo("Stopping Neon")
    stop_neon()
    click.echo("Neon Stopped")


@neon_core_cli.command(help="Send Diagnostics")
@click.option("--no-transcripts", is_flag=True, default=False,
              help="Skip upload of transcript files")
@click.option("--no-logs", is_flag=True, default=False,
              help="Skip upload of log files")
@click.option("--no-config", is_flag=True, default=False,
              help="Skip upload of configuration files")
def upload_diagnostics(no_transcripts, no_logs, no_config):
    from neon_core.util.diagnostic_utils import send_diagnostics
    click.echo("Uploading Diagnostics")
    send_diagnostics(not no_logs, not no_transcripts, not no_config)
    click.echo("Diagnostic Upload Complete")


@neon_core_cli.command(help="Install Default Skills")
def install_default_skills():
    from neon_core.util.skill_utils import install_skills_default
    click.echo("Installing Default Skills")
    install_skills_default()
    click.echo("Default Skills Installed")


@neon_core_cli.command(help="Ensure default resource files are available")
def update_default_resources():
    from neon_core.util.skill_utils import update_default_resources
    click.echo("Updating Default Resources")
    update_default_resources()


@neon_core_cli.command(help="Start Neon Skills module")
def run_skills():
    from neon_utils.configuration_utils import init_config_dir
    init_config_dir()

    from neon_core.util.skill_utils import update_default_resources
    update_default_resources()

    from neon_core.skills.__main__ import main
    click.echo("Starting Skills Service")
    main()
    click.echo("Skills Service Shutdown")
