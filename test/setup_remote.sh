#!/bin/bash

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

export GITHUB_TOKEN="${1}"

installerDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/NeonAI"
export installerDir

# Preferences
export devMode=false         # false will enable fullscreen gui, isolated directories, and other device management
export autoStart=false      # enables neonAI to run at login of installUser
export autoUpdate=false     # enables neonAI to check for updates at runtime
export devName=${HOSTNAME}  # device name used to identify uploads
export installServer=false  # enables neonAI server module

export sttModule="google_cloud_streaming"
export ttsModule="polly"

## Actual Installation bits
sudo apt install -y python3-dev python3-venv swig libssl-dev libfann-dev portaudio19-dev git

echo "${GITHUB_TOKEN}">~/token.txt
pip install --upgrade pip~=21.1
pip install wheel
python "${installerDir}/../parse_requirements.py" requirements/requirements.txt
python "${installerDir}/../parse_requirements.py" requirements/remote_speech_processing.txt
python "${installerDir}/../parse_requirements.py" requirements/client.txt
pip install -r requirements/requirements.txt
pip install -r requirements/remote_speech_processing.txt
pip install -r requirements/client.txt

# TODO: Below is for testing only DM
pip install --upgrade git+https://github.com/NeonDaniel/neon-skill-utils@FEAT_HandleConfigFromSetup
neon-config-import

# Setup Completed
echo "Setup Complete"
exit 0
