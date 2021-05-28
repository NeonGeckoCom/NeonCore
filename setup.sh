#!/bin/bash

sudo apt install python3-dev python3-venv swig libssl-dev libfann-dev portaudio19-dev git

git clone https://github.com/mycroftai/mycroft-gui
bash mycroft-gui/setup.sh
export GITHUB_TOKEN="{$1}"

pip install "git+https://${GITHUB_TOKEN}@github.com/NeonDaniel/NeonCore#egg=neon_core[dev,client]"
