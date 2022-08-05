
# Table of Contents
0. [Quick Start](#quick-start)
1. [Optional Service Account Setup](#optional-service-account-setup)  
   * [a. Google Cloud Speech](#a-google-cloud-speech-setup)  
   * [b. Amazon Polly and Translate](#b-amazon-polly-and-translate-setup)
2. [Setting Up Hardware](#setting-up-hardware)  
3. [Installing Neon](#installing-neon)  
   * [a. Development Environment](#installing-neon-in-a-development-environment)  
   * [b. User Environment](#installing-neon-in-a-userdeployment-environment)  
4. [Using Neon](#using-neon)  
   * [a. Activating the venv](#a-activating-the-venv)
   * [c. Running Tests](#c-running-tests)  
   * [d. Troubleshooting](#d-troubleshooting)  
5. [Making Changes](#making-code-changes)  
   * [a. System Overview](#a-system-overview)  
   * [b. Creating a Skill](#b-creating-a-skill)   
6. [Removing and re-installing Neon](#removing-and-re-installing-neon-ai)  

# Welcome to Neon AI
Neon AI is an open source voice assistant. Follow these instructions to start using Neon on your computer. If you are 
using a Raspberry Pi, you may use the prebuilt image available [on our website](https://neon.ai/DownloadNeonAI).

# Quick Start
The fastest method for getting started with Neon is to run the modules in Docker containers.
The `docker` directory contains everything you need to run Neon Core with default skills.

## a. Prerequisite Setup
You will need `docker` and `docker-compose` available. Docker provides updated guides for installing 
[docker](https://docs.docker.com/engine/install/) and [docker-compose](https://docs.docker.com/compose/install/).
Neon Core is only tested on Ubuntu, but should be compatible with any linux distribution that uses
[PulseAudio](https://www.freedesktop.org/wiki/Software/PulseAudio/).

> *Note*: By default, only the `root` user has permissions to interact with Docker under Ubuntu.
> To allow the current user to modify Docker containers, you can add them to the `docker` group with:
> `sudo usermod -aG docker $USER`

## b. Running Neon
You can clone the repository, or just copy the `docker` directory contents onto your local system; this document will 
assume that the repository is cloned to: `~/NeonCore`.

You can start all core modules with:
```shell
# cd into the directory containing docker-compose.yml
cd ~/NeonCore/docker
docker-compose up -d
```

Stop all modules with:
```shell
# cd into the directory containing docker-compose.yml
cd ~/NeonCore/docker
docker-compose down
```

### Optional GUI
The Mycroft GUI is an optional component that can be run on Linux host systems.
The GUI is available with instructions [on GitHub](https://github.com/MycroftAI/mycroft-gui)

## c. Interacting with Neon
With the containers running, you can interact with Neon by voice (i.e. "hey Neon, what time is it?"), or using one of 
our CLI utilities, like [mana](https://pypi.org/project/neon-mana-utils/) or the 
[neon_cli_client](https://pypi.org/project/neon-cli-client/).
You can view module logs via docker with:

```shell
docker logs -f neon-skills      # skills module
docker logs -f neon-speech      # voice module (STT and WW)
docker logs -f neon-audio       # audio module (TTS)
docker logs -f neon-gui         # gui module (Optional)
docker logs -f neon-messagebus  # messagebus module (includes signal manager)
```

## d. Skill Development
By default, the skills container includes a set of default skills to provide base functionality.
You can pass a local skill directory into the skills container to develop skills and have them
reloaded in real-time for testing. Just set the environment variable `NEON_SKILLS_DIR` before starting
the skills module. Dependency installation is handled on container start automatically.

```shell
export NEON_SKILLS_DIR=~/PycharmProjects/SKILLS
cd ~/NeonCore/docker
docker-compose up
```

To run the skills module without any bundled skills, the image referenced in `docker-compose.yml` can be changed from:

```yaml
  neon-skills:
    container_name: neon-skills
    image: ghcr.io/neongeckocom/neon_skills-default_skills:dev
```
to:
```yaml
  neon-skills:
    container_name: neon-skills
    image: ghcr.io/neongeckocom/neon_skills:dev
```

## e. Configuration
The `ngi_local_conf.yml` file included in the `docker` directory contains a default configuration
that may be modified to specify different plugins and other runtime settings.
The `docker` directory is mounted read-only to `/config` in each of the containers,
so model files may be placed there and the configuration updated to use different STT/TTS plugins with
local models.

# Optional Service Account Setup
There are several online services that may be used with Neon. Speech-to-Text (STT) and Text-to-Speech (TTS) may be run 
locally, but remote implementations are often faster and more accurate. Following are some instructions for getting 
access to Google STT and Amazon Polly TTS. During setup, these credentials will be imported and validated.
> *Note:* If you complete this setup on a Windows PC, make sure to edit any files using a text editor such as 
[Notepad++](https://notepad-plus-plus.org/) to ensure compatibility in Linux. Also check for correct file extensions 
after copying your files to your Linux PC, as Windows will hide known file extensions by default.


## a. Google Cloud Speech Setup
1. Go to: 
    > https://cloud.google.com/

1. Sign in or create a `Google account`
    >![Google](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Google1.png)


1. Go to your `Console`
    >![Google](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Google2.png)


1. Search for and select `"Cloud Speech-to-Text"` (Not to be confused with Text-to-Speech)
1. Select the option you would like to use
    >![Google](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Google3.png)


1. You will be prompted to enable billing on your account at this point because this service is paid after a free monthly 
quota
    > Google will not automatically charge your card unless you give permission to do so. 
1. In the left `Navigation Menu`, select `APIs & Services`, `Credentials`
    >![Google](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Google4.png)


1. Click `Create credendials`, `Service Account Key`
    >![Google](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Google5.png)


1. Choose any service account name for your reference. You may leave the `Role` field empty
1. Make sure key type is `JSON` and click on `Continue`
    >![Google](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Google6.png)


1.  If you did not assign a role, you would be prompted. You may continue by clicking `'CREATE WITHOUT ROLE'`
    >![Google](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Google7.png)


1. You will see a prompt and your service key will automatically download
1. Rename the downloaded file to `google.json` and move it into the same directory as neonSetup.sh

    > *Note:* The premium models are only available in US English and provide some enhancements to phone and video audio 
    which do not apply to this project. The options with Data Logging allows Google to use your audio and transcriptions to 
    train their model. You may select the option without logging to opt out (note that the option with logging is 
    discounted).

At this point, Neon can be partially tested without `Amazon translations` and `Wolfram information` skills. You may run 
setup without continuing, but Amazon and Wolfram|Alpha services are *highly* recommended.


## b. Amazon Polly and Translate Setup
1. Go to: 
    > https://aws.amazon.com/

1. Click `"Sign into the Console"` at the top right of the screen
    >![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon1.png)


1. Sign in or register for an account
1. Go to the `Services Menu` at the top left of the screen and click `IAM`
    >![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon2.png)


1. Select `Users` from the left side menu and click `Add user`
    >![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon3.png)


1. Enter a `User name` and check the box for `Programmatic access`
    >![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon4.png)


1. On the next page, Select `'Attach existing policies directly'` and search for `'AmazonPollyFullAccess'` and 
`'TranslateFullAccess'`
    >![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon5.png)
     ![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon6.png)


1. You may add tags on the next page if desired
1. Review your selections on the next page and `Create user`
    >![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon7.png)


1. On the next page you can see your `Access key ID` and `Secret access key`
1. Click the `Download .csv file` button to save your credentials to your computer
    >![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon8.png)


1. Copy or move the downloaded `accessKeys.csv` to the same directory as neonSetup.sh

    > *Note:* You will ***not*** be able to view your secret access key after it is generated, so if you need a secret 
    access key, you will have to generate a new Access key.

The Users menu lets you create new users and new access keys per user as you wish, as well as modify permissions.

# Setting Up Hardware
Before continuing, make sure you have your hardware setup ready for installation. You will need the following:
* A computer running up-to-date Ubuntu 20.04
  >   You can find our video tutorial for installing Ubuntu in a virtual machine 
  >   [here](https://neongecko.com/WindowsOptionUbuntuVirtualMachineInstall), or you can find written instructions
  >   [here](https://tutorials.ubuntu.com/tutorial/tutorial-install-ubuntu-desktop#0)
  
  > *Note:* If you prefer to use Windows for your development environment, you can install the
  > [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10). You can find our video
  > tutorial [here](https://neongecko.com/WindowsOptionSubsystemforLinux). Audio and gui functionality will be limited
  > in this case; you will only be able to interact with Neon via command line.

## System Requirements
* Speakers and a microphone recognized by Ubuntu
    >![NeonDev](https://0000.us/klatchat/app/files/neon_images/neon_setup_screens/Setup1.png)
     You can verify Ubuntu sees your devices by accessing `Settings` and then `Sound`
    * If you are unsure of which device to select, you can click `Test Speakers` to play a test tone through the selected 
    Output device
    * You can test your microphone under the `Input` tab, the Input level should move when you speak into the microphone
        > If you do not see any microphone activity, make sure the correct device is selected and the Input volume is set 
          above 50%

* Webcam (optional)
    > Some functionality requires a webcam (ex. USB Cam Skill). Most webcams also include a microphone that can be used 
    for Neon.

* An active internet connection
  >   *Note*: A connection of at least 10Mbps is recommended. On slower connections, installation may take several
  >   hours.

* At least `10GB` of available disk space (`15 GB` if installing Mimic)
  > Neon AI occupies less than 1GB itself. With dependencies, the installation takes about 5GB on an up-to-date Ubuntu
  > 20.04 system. Mimic local speech-to-text requires about 3.5 GB. Additional space is used while installing packages 
  > during installation and updates. Several gigabytes is recommended in order to keep local transcriptions and audio files.

* A system with at least 2GB RAM and 2 or more processing threads is required, with 4GB RAM and 4 threads recommended
  > Some features such as the vision service may not work on systems only meeting the minimum requirements. Responses 
  > and speech processing will take longer on lower performance systems.

# Installing Neon
This guide includes instructions for installing in both a Development environment and a User environment. User 
environment is similar to what is found on our [Raspberry Pi Image](https://neon.ai/DownloadNeonAI); packages will be 
installed from distributions and installed code should not be modified.
A developer environment will clone `NeonCore` from source and include more debugging utilities. 
Developer installations are also designed to run alongside other instances of Neon/OVOS/Mycroft.

A development environment is designed to be a testable installation of NeonAI that can be connected to an IDE   
(ex. Pycharm) for modifications and skill development. This guide assumes installation in a development environment from 
an unmodified fork of NeonAI. After installation, any changes and additions can be pushed to git or hosted on a private 
server. 
  
A user environment is designed to be an installation on a device that will be used normally as a voice assistant. You
may want to test how your changes affect performance on less powerful hardware or test how changes may be deployed as
updates.  
If you are developing in a virtual machine, installation on physical hardware in a user environment is useful for
testing audio and video I/O which can be difficult in many virtualized environments.

All the following options, such as autorun and automatic updates can be easily modified later using your voice,
profile settings, or configuration files.
  
## Installing Neon in a Development Environment
Neon "core" is a collection of modules that may be installed and modified individually. These instructions will 
outline a basic setup where the `neon_audio`, `neon_enclosure`, `neon_speech`, and any other modules are installed to their
latest stable versions. These modules may be installed as editable for further development; instructions for this can be 
found [here](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs)

1. Install required system packages
```shell
sudo apt install python3-dev python3-venv python3-pip swig libssl-dev libfann-dev portaudio19-dev git mpg123 ffmpeg
```
> *Note*: The following commands can be used to install mimic for local TTS
```shell
sudo apt install -y curl
curl https://forslund.github.io/mycroft-desktop-repo/mycroft-desktop.gpg.key | sudo apt-key add - 2> /dev/null && echo "deb http://forslund.github.io/mycroft-desktop-repo bionic main" | sudo tee /etc/apt/sources.list.d/mycroft-desktop.list
sudo apt-get update
sudo apt install mimic
```

2. Clone NeonCore from your forked repository into a local directory.

```shell
git clone https://github.com/NeonGeckoCom/NeonCore ~/NeonAI
cd ~/NeonAI
```

3. Create a virtual environment and activate it.
```shell
python3 -m venv ./.venv
. .venv/bin/activate
pip install wheel  # this speeds up subsequent 
```

4. If you have access to private Neon repositories, export your Github Personal Access Token as an environment variable
```shell
export GITHUB_TOKEN=<insert_token_here>
```

5. Install any desired requirements
```shell
pip install .[client,dev,remote]
```
  >*Note*: `dev`, `client`, and `remote` are recommended for general development installations.
  > `local` may be substituted for `remote`

6. Install the mycroft-gui package (optional)
```shell
git clone https://github.com/mycroftai/mycroft-gui
bash mycroft-gui/dev_setup.sh
rm -rf mycroft-gui
sudo apt-get install libqt5multimedia5-plugins qml-module-qtmultimedia
```
  >*Note*: dev_setup.sh is an interactive script; do not copy/paste the full block above into your terminal.

7. Create and update configuration
```shell
neon-config-import
```
Open `ngi_local_conf.yml` in your text editor of choice and make any desired changes.
If you selected `local` options above, you should change the following STT/TTS module lines:
```yaml
tts:
  module: neon_tts_mimic

stt:
  module: deepspeech_stream_local
```

You may also choose to place logs, skills, configuration files, diagnostic files, etc. in the same directory as your cloned core
(default location is `~/.local/share/neon`). This isolates logs and skills if you have multiple cores installed.
```yaml
dirVars:
  logsDir: ~/NeonCore/logs
  diagsDir: ~/NeonCore/Diagnostics
  skillsDir: ~/NeonCore/skills
  confDir: ~/NeonCore/config
```

> *Note:* You may also have a configuration file you wish to copy here to overwrite the default one.

8. Install default skills (optional)
```shell
neon-install-default-skills
```
Installation of default skills will usually occur every time neon is started, but you may want to do this manually and 
disable automatic skill installation to avoid conflicts with local development. The list of default skills may be changed
in `ngi_local_conf.yml`
```yaml
skills:
  default_skills: <url to list of skills or list of skill URL's>
```
  >*Note:* The default_skills list may include URLs with branch specs, skill names, 
  > or a link to a text file containing either of these lists.

10. Neon is now ready to run. You may start Neon with `neon-start` from a terminal; to start Neon in the background, run:
```shell
coproc neon-start >/dev/null 2>&1 &
```
   >*Note:* Starting Neon can take some time when skills are set to automatically install/update. You can speed this up
    by disabling automatic skill installation/updates in `ngi_local_conf.yml`. 
```yaml
skills:
  auto_update: false
```

## Installing Neon in a User/Deployment Environment  
Installing in a User Environment differs from a developer environment; you will not be able to modify Neon Core if you 
use this installation method.

1. Download `setup.sh` from the [NeonCore repository](https://github.com/NeonGeckoCom/NeonCore/blob/dev/setup.sh).
   >*Note*: You can download this file by right-clicking `Raw` and selecting `Save link as...`
2. Take your `setup.sh` file and place it in your home directory  
   >![NeonDev](https://0000.us/klatchat/app/files/neon_images/neon_setup_screens/Neon1.png)
3. Open a terminal in your home directory (`ctrl`+`alt`+`t`)  
4. Type in `bash setup.sh ${GITHUB_TOKEN}` and press `Enter` (where `${GITHUB_TOKEN}` is your Github token)
   >*Note*: You can find instructions on how to generate a GitHub Personal Access Token 
   > [here](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token)
   
   >![NeonDev](https://0000.us/klatchat/app/files/neon_images/neon_setup_screens/Neon2.png)  
5. Type `n` to Install in User Mode (Not Developer Mode)
6. Type `n` to Input Custom settings
    >*Note*: You may use quick settings and skip the following prompts
___
8. Type `n` to install in User mode  (`y` for full Developer mode)
8. `Autorun` is recommended (`y`) on for User Environments  
8. `Automatic updates` are recommended (`y`) on for User Environments  
8. `Local STT` is NOT recommended (`n`) IF you have google and aws keys, as remote processing is faster and more accurate 
8. `Install GUI` is recommended (`y`) so long as your device has a display
8. Find out more about OpenHAB [here](https://www.openhab.org/docs/)  
14. `Server` is NOT recommended (`n`) unless you know otherwise 
    
1. You will be prompted to confirm your settings, press `y` to continue, `n` to start over, or `b` to go back and 
   correct a previous setting
   > ![NeonDev](https://0000.us/klatchat/app/files/neon_images/neon_setup_screens/Neon3-1.png)
   
1. When setup is complete, you will be able to start Neon via `start_neon.sh` and stop Neon via: `stop_neon.sh`
  
# Using Neon  
After you have completed [Installing Neon](#installing-neon), you will have a fully functional system ready to test.

## a. Activating the venv
If you followed the [Developer instructions](#installing-neon-in-a-development-environment) and attached Neon to an IDE 
(such as PyCharm), your IDE likely configured a virtual environment in `NeonCore/venv`. 
If you followed the [User instructions](#installing-neon-in-a-userdeployment-environment), a virtual environment was 
created at `~/NeonAI/.venv`.

To interact with Neon from a terminal, you need to activate the correct virtual environment by running:
`. ~/NeonAI/.venv/bin/activate` (or the appropriate path if you installed to a different directory).
> *Note:* If you are using an IDE like PyCharm, the built-in terminal will often activate the virtual environment automatically.

You will know that your virtual environment is active by the `(.venv)` printed in your terminal. You may exit the `.venv`
shell by running `deactivate`.

## b. Terminal Commands
From your shell with the virtual environment activated, you can see a list of available terminal commands by typing `neon`
and tapping `TAB` twice. Depending on which packages were installed with Neon, you might see `neon_cli_client` which 
will launch the CLI for debugging. 

## c. Running Tests
From your shell with the virtual environment activated, `neon_skills_tests` will launch automated testing. You will be
prompted to select a test set to run (no entry will run `all`). Neon will proceed to execute and respond to a number of 
requests, corresponding to all default installed skills. After all tests have run, a summary will be printed to the terminal
followed by any logged errors.
>*Note:* More complete logs and information can be found in the Diagnostics directory
    >By default, this is at `~\NeonAI\Diagnostics\testing` for Development Machines and
     `~\Documents\NeonGecko\Diagnostics\testing` for User Machines.
     
## d. Troubleshooting
If you encounter any of the following issues while using Neon, please try these troubleshooting steps

* My computer is slow to respond
  > Check for high memory usage in `System Monitor`. If your Memory and Swap both show 100% utilization under
  > `Resources`, try exiting PyCharm and Neon AI. If there is still abnormal memory usage, open a Terminal and type in:
  ```bash
    sudo systemctl stop openhab2.service
   ```  
  > If you can determine the offending program, see if restarting the program or your computer resolves your issues. If
  > not, you may find common solutions online.
  
* Neon AI is not transcribing anything I say
  >   Check that your microphone is working and active by going to `Sound` the `Settings` Menu. Go to the `Input` tab
  >   and make sure the correct microphone is selected. Make sure the `Input Level` is up and turned on and look for
  >   activity on the `Input Level` bar when you tap the mic. If you change devices here, restart Neon AI.

* Some audio is very quiet, while other audio is louder
  >   Check that the audio level for the affected application is turned up by going to `Sound` the `Settings` Menu. Go to
  >   the `Applications` tab.
   
  >   For quiet responses from Neon, ask Neon something with a longer response (ex. "Tell me a joke"). When an
  >   application named `neon-voice` appears, make sure it is not muted and that the volume is set to the maximum. Do
  >   the same for any other applications that are too quiet; start playing something and check the Application's
  >   volume.

* AVMusic will not pause or resume
  >   If AVMusic playback is changed by something other than Neon, the skill can lose track of whether something is
  >   playing or paused. If something is paused and Neon will not resume, you may say "pause" to resume playback. "Stop"
  >   should work in any case.
  
* Errors in the log when installing or updating Neon
  >   Installation of dlib can fail if system memory is completely full; you can open System Monitor during installation
  >   or updates to monitor memory usage. A minimum 2GB RAM is required, 4GB+ recommended. Errors may also occur if system
  >   storage becomes full. You may monitor storage availability in System Monitor as well; keep in mind that cached files
  >   will be removed when installation fails, so your file system will show some available space before and after the 
  >   error occurs.
  
* Any other issues
  >   If you encounter any other issues while using Neon, they can often be solved by restarting Neon or your computer.
  >   If this does not resolve you issue, please contact support at [info@neongecko.com](mailto:info@neongecko.com).

# Making Code Changes
After completing setup and testing, you are ready to begin making changes and creating skills. An example workflow for 
making a change would be:

1. Create or modify a skill
1. Test changes in the Developer Environment (Look for errors in logs, unexpected behaviour, etc.)
1. Run `Test Neon` to check that all skills and TTS/STT behave as expected
1. Commit and Push changes to git (for collaborative development, it is often best to create a new branch for any changes)
1. Install your updated skill in a User Environment (check for any missing dependencies, invalid file paths, etc.)
1. Run complete tests using `Test Neon`
1. Check logs for any errors

## a. System Overview
There are two aspects of the Neon AI system: `core` and `skills`.

The `core` is composed of several modules, but generally includes:
  - `speech` for handling user inputs and performing speech-to-text (STT)
  - `skills` for processing user input to find intent and provide a response
  - `audio` for speaking the response generated in skills
  - `bus` for handling all communications between modules
  - `enclosure` for handling any hardware interactions like speakers, microphone, lights, and buttons

Other modules may also be running for gui functionality, etc and may be added to provide new functionality.

`skills` provide the functionality of handling user inputs and generating responses or performing actions. 


## b. Creating a Skill
Check out our three part youtube series on how to create a skill:
https://youtu.be/fxg25MaxIcE
https://youtu.be/DVSroqv6E6k
https://youtu.be/R_3Q-P3pk8o

## Additional Steps for Developers Using PyCharm
11. Next you should update your IDE in your Developer Environment
>    *Note*: This is PyCharm if you followed our setup guide.
10. In PyCharm, select `VCS` from the menu bar, and then `Update Project`
    > ![NewRelease](https://0000.us/klatchat/app/files/neon_images/neon_release_screens/NewRelease4.png)
11. You will be prompted to `Update Project`, you may leave the default settings and click `OK`
    > ![NewRelease](https://0000.us/klatchat/app/files/neon_images/neon_release_screens/NewRelease5.png)


# Removing and Re-installing Neon AI
You may wish to remove your Neon AI installation to start fresh with a new version. Below is a list of locaitons
where Neon may have saved files:
  - `~/Documents/NeonGecko`
  - `~/Pictures/NeonGecko`
  - `~/Videos/NeonGecko`
  - `~/Music/NeonGecko`
  - `~/.local/share/neon`
  - `~/.cache/neon`
  - `~/NeonAI`
  - `~/.neon`
  - `/opt/neon`
  - `/tmp/neon`

You may now [re-install Neon](#installing-neon)
   > *Note:* You may need your [credential files](#optional-service-account-setup) to complete re-installation.

# Running Docker Modules

Skills Service
```shell
docker run -d \
--name=neon_skills \
--network=host \
-v ~/.config/pulse/cookie:/tmp/pulse_cookie:ro \
-v ${XDG_RUNTIME_DIR}/pulse:${XDG_RUNTIME_DIR}/pulse:ro \
--device=/dev/snd:/dev/snd \
-e PULSE_SERVER=unix:${XDG_RUNTIME_DIR}/pulse/native \
-e PULSE_COOKIE=/tmp/pulse_cookie \
neon_skills
```
