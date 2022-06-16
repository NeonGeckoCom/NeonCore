#!/bin/bash

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

export GITHUB_TOKEN="${1}"

installerDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export installerDir
sourceDir="$( cd "$( dirname "${installerDir}" )" && pwd )"

# Preferences
export devMode=false         # false will enable fullscreen gui, isolated directories, and other device management
export autoStart=false      # enables neonAI to run at login of installUser
export autoUpdate=false     # enables neonAI to check for updates at runtime
export devName=${HOSTNAME}  # device name used to identify uploads
export installServer=true   # enables neonAI server module

export sttModule="google_cloud_streaming"
export ttsModule="amazon"

localDeps="false"
installGui="false"
options=("core_modules")
options+=("test")
if [ "${localDeps}" == "true" ]; then
  options+=("local")
else
  options+=("remote")
fi

if [ "${installServer}" == "true" ]; then
  options+=("server")
else
  options+=("client")
fi

if [ "${devMode}" == "true" ]; then
  options+=("dev")
fi
optStr=$(printf ",%s" "${options[@]}")
optStr="[${optStr:1}]"

# Create install directory if specified and doesn't exist
if [ ! -d "${installerDir}" ]; then
  echo "Creating Install Directory: ${installerDir}"
  mkdir -p "${installerDir}"
fi

# Make venv if not in one
if [ -z "${VIRTUAL_ENV}" ]; then
  echo "Creating new Virtual Environment"
  cd "${installerDir}" || exit 10
  python3 -m venv .venv
  . .venv/bin/activate
fi

## Actual Installation bits
# Add Mimic apt repository
sudo apt install -y curl
curl https://forslund.github.io/mycroft-desktop-repo/mycroft-desktop.gpg.key | sudo apt-key add - 2> /dev/null && echo "deb http://forslund.github.io/mycroft-desktop-repo bionic main" | sudo tee /etc/apt/sources.list.d/mycroft-desktop.list
sudo apt-get update

# Install system dependencies
sudo apt install -y python3-dev python3-venv python3-pip swig libssl-dev libfann-dev portaudio19-dev git mpg123 ffmpeg mimic libpulse-dev


# Do GUI install
if [ "${installGui}" == "true" ]; then
  if [ -d mycroft-gui ]; then
    rm -rf mycroft-gui
  fi
  git clone https://github.com/mycroftai/mycroft-gui
  bash mycroft-gui/dev_setup.sh
  rm -rf mycroft-gui
fi


echo "${GITHUB_TOKEN}">~/token.txt
pip install --upgrade pip~=21.3
pip install wheel

cd "${sourceDir}" || exit 10
pip install ".${optStr}"  # --use-deprecated=legacy-resolver

export NEON_CONFIG_PATH="${sourceDir}"
export NEON_LOG_DIR="~/.local/share/neon/logs"
neon-config-import

# Install Default Skills
neon-install-default-skills

exit 0
