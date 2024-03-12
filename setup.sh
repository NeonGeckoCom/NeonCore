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

echo "WARNING: This script is no longer supported and will be removed with core version 24.05.x"

# Check if run as root
if [ "${USER}" == "root" ]; then
  read -r -p "Installing as root may cause problems, would you like to continue? [y/N]" -n1 input
  if [[ ${input} != "Y" && ${input} != "y" ]]; then
    echo "Please Run again as a standard user."
    exit 0
  fi
fi

# Check platform
modelFile=/proc/device-tree/model

# Determine if device is a Raspberry Pi
if [ -f ${modelFile} ] && [ "$(grep "Raspberry Pi" "${modelFile}")" ]; then
  raspberryPi="true"
else
  raspberryPi="false"
fi
export raspberryPi


# Define installation directory
installerDir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
if [ "${installerDir}" == "${HOME}" ]; then
  installerDir="${installerDir}/NeonAI"
fi
export installerDir

# Preferences
export devMode=true         # false will enable fullscreen gui, isolated directories, and other device management
export autoStart=false      # enables neonAI to run at login of installUser
export autoUpdate=false     # enables neonAI to check for updates at runtime
export devName=${HOSTNAME}  # device name used to identify uploads
export installServer=false  # enables neonAI server module
export sttModule="google_cloud_streaming"
export ttsModule="amazon"

installGui=false


askYesNo(){
    while true; do
        read -r -p "${1} [Yes/No/Back]" -n1 input
        case ${input} in
            [Yy] ) #Yes
            return 0
            ;;
            [Nn] ) # No
            return 1
            ;;
            [Dd] ) # Developer
            if [ "${1}" == "Install in Developer Mode?" ]; then
                return 0
            else
                echo -e "\nPlease Respond Yes, No, or Back to Continue installation\n"
            fi
            ;;
            [Uu] ) # User
            if [ "${1}" == "Install in Developer Mode?" ]; then
                return 1
            else
                echo -e "\nPlease Respond Yes, No, or Back to Continue installation\n"
            fi
            ;;
            [Bb] ) # Back
            echo -e "\nBack\n"
            export i=$((i -= 2))
            return 2
            ;;
            [Cc] ) # Complete
            export listOpts=(
            "developer"
            "quick"
            "confirmSettings"
            )
            export i=1
            return 2
            ;;
            * )     # Invalid Response
                echo -e "\nPlease Respond Yes, No, or Back to Continue installation\n"
            ;;
        esac
    done
}

askWrapper(){
    case "${1}" in
    "developer")
        askYesNo "Install in Developer Mode?"
        result=${?}
        if [ ${result} == 0 ]; then
            export devMode=true
            echo -e "\nInstalling in Developer Mode\n"
        elif [ ${result} == 1 ]; then
            export devMode=false
            echo -e "\nInstalling in User Mode\n"
        fi

        if [ "${devMode}" == "true" ]; then
            export autoStart=false
            export autoUpdate=false
        else
            export autoStart=true
            export autoUpdate=true
        fi
    ;;
    "autorun")
        askYesNo "Autorun Neon at system startup?"
        result=${?}
        if  [ ${result} == 0 ]; then
            export autoStart=true
            echo -e "\nNeon will be added to startup.\n"
        elif  [ ${result} == 1 ]; then
            export autoStart=false
            echo -e "\nNeon will not start up automatically.\n"
        fi
    ;;
    "autoupdate")
        askYesNo "Check for updates automatically?"
        result=${?}
        if  [ ${result} == 0 ]; then
            export autoUpdate=true
            echo -e "\nYour device will check for updates at startup and periodically.\n"
        elif  [ ${result} == 1 ]; then
            export autoUpdate=false
            echo -e "\nYour device will not update unless asked to.\n"
        fi
    ;;
    "localSpeech")
        askYesNo "Use local STT (Deepspeech)/TTS (Mimic)?"
        result=${?}
        if  [ ${result} == 0 ]; then
            localDeps='true'
            export sttModule="deepspeech_stream_local"
            export ttsModule="neon_tts_mimic"
            echo -e "\nDeepspeech and Mimic will be used.\n"
        elif  [ ${result} == 1 ]; then
            localDeps='false'
            echo -e "\nGoogle STT and Amazon TTS plugins will be used.\n"
        fi
    ;;
    "gui")
        askYesNo "Install GUI (requires KDE or Ubuntu 20.04+)?"
        result=${?}
        if [ ${result} == 0 ]; then
            installGui='true'
            echo -e "\nGUI will be installed.\n"
        elif [ ${result} == 1 ]; then
            echo -e "\nNo GUI.\n"
        fi
    ;;
    "server")
        askYesNo "Configure as a server? (No if unsure)"
                result=${?}
        if [ ${result} == 0 ]; then
            installServer='true'
            echo -e "\nServer module will be installed.\n"
        elif [ ${result} == 1 ]; then
            echo -e "\nClient device.\n"
        fi
    ;;
    "confirmSettings")
        # Write out Install Settings
        echo -e "\n\e[92mConfirm Installation Settings\e[39m
        Developer Mode         : ${devMode}
        Run Neon at Login      : ${autoStart}
        Automatic Neon Updates : ${autoUpdate}
        Install GUI            : ${installGui}
        STT Engine             : ${sttModule}
        TTS Engine             : ${ttsModule}
        Server                 : ${installServer}
        Pi                     : ${raspberryPi}"

        askYesNo "Continue with these settings?"
        result=${?}
        if [ ${result} == 0 ]; then
            echo -e "\nProceeding with installation."
        elif  [ ${result} == 1 ]; then
            echo -e "\n"
            getOptions
        fi
    ;;
    "quick")
        askYesNo "Use quick settings?"
        result=${?}
        if  [ ${result} == 0 ]; then
            echo -e "\nUsing quick settings.\n"
            installGui="true"

            export listOpts=(
            "developer"
            "quick"
            "confirmSettings"
            )

        elif  [ ${result} == 1 ]; then
        echo -e "\nUsing custom settings.\n"
           export listOpts=(
            "developer"
            "quick"
            "autorun"
            "autoupdate"
            "localSpeech"
            "gui"
            "server"
            "confirmSettings"
            )
        fi
    ;;
    esac

}

getOptions(){
    export listOpts=(
    "developer"
    "quick"
    )

    export i=0
    while [ ${i} -lt ${#listOpts[@]} ]; do
        if [ ${i} -lt 0 ]; then
            i=0
        fi
        askWrapper "${listOpts[i]}"
        export i=$((i + 1))
    done
}

doInstall(){
    # Add piwheels if pi
    if  find . | grep -q "x86" <<< "$(lscpu)" ; then
        arm=false
    else
        arm=true
        echo -e "[global]\nextra-index-url=https://www.piwheels.org/simple\n">pip.conf
        sudo my pip.conf /etc
    fi

  # Build optional dependency string for pip installation
    options=("core_modules")
    if [ "${localDeps}" == "true" ]; then
      if [ "${arm}" == "true" ]; then
        echo "Local Dependencies not supported on ARM; remote STT/TTS will be used."
        options+=("remote")
      else
        options+=("local")
      fi
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
    pipStr="git+https://${GITHUB_TOKEN}@github.com/NeonGeckoCom/NeonCore#egg=neon_core${optStr}"

    # Create install directory if specified and doesn't exist
    if [ ! -d "${installerDir}" ]; then
      echo "Creating Install Directory: ${installerDir}"
      mkdir -p "${installerDir}"
    fi

    # Add Mimic apt repository
    sudo apt install -y curl
    curl https://forslund.github.io/mycroft-desktop-repo/mycroft-desktop.gpg.key | sudo apt-key add - 2> /dev/null && echo "deb http://forslund.github.io/mycroft-desktop-repo bionic main" | sudo tee /etc/apt/sources.list.d/mycroft-desktop.list
    sudo apt-get update

    # Install system dependencies
    sudo apt install -y python3-dev python3-venv python3-pip swig libssl-dev libfann-dev portaudio19-dev libsndfile1 \
    git mpg123 ffmpeg mimic libpulse-dev

    # Make venv if not in one
    if [ -z "${VIRTUAL_ENV}" ]; then
      echo "Creating new Virtual Environment"
      cd "${installerDir}" || exit 10
      python3 -m venv .venv
      . .venv/bin/activate || exit 11
    fi

    # TODO: Patching json_database/OSM, default log directory here:
    mkdir ~/.local/share/json_database
    mkdir ~/.local/share/icons
    sudo mkdir /var/log/mycroft
    sudo chmod 777 /var/log/mycroft

    # Do GUI install
    if [ "${installGui}" == "true" ]; then
      if [ "${raspberryPi}" == "true" ]; then
        sudo apt install xorg
      fi
      if [ -d mycroft-gui ]; then
        rm -rf mycroft-gui
      fi
      git clone https://github.com/mycroftai/mycroft-gui
      bash mycroft-gui/dev_setup.sh
      rm -rf mycroft-gui
      sudo apt-get install libqt5multimedia5-plugins qml-module-qtmultimedia
    fi

    echo "${GITHUB_TOKEN}">~/token.txt
    pip install --upgrade pip~=21.3
    pip install wheel
    pip install "${pipStr}"
    neon-config-import

start_script="#!/bin/bash

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
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\"
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

. \"${VIRTUAL_ENV}/bin/activate\"
coproc neon-start >/dev/null 2>&1
exit 0
"

stop_script="#!/bin/bash

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
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\"
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

. \"${VIRTUAL_ENV}/bin/activate\"
neon-stop
exit 0
"

    # Copy shortcut files
    if [ ${raspberryPi} == "false" ]; then
      echo "${start_script}">start_neon.sh
      echo "${stop_script}">stop_neon.sh
      sudo chmod ugo+x start_neon.sh
      sudo chmod ugo+x stop_neon.sh
    fi

    # Install Default Skills
    neon-install-default-skills

    # Setup Completed
    echo "Setup Complete"
    exit 0
}

touch "neon_setup.log"
if [ -n "${1}" ]; then
  export GITHUB_TOKEN="${1}"
fi

# Warn and exit if no github token is available for dependency gathering
if [ -z "${GITHUB_TOKEN}" ]; then
  echo "GITHUB_TOKEN not defined! cancelling setup."
  exit 10
fi

getOptions
doInstall | tee -a "neon_setup.log"
