# Table of Contents
0. [Quick Start](#quick-start)
   * [a. Prerequisite Setup](#a-prerequisite-setup)
   * [b. Running Neon](#b-running-neon)
   * [c. Interacting with Neon](#c-interacting-with-neon)
   * [d. Skill Development](#d-skill-development)
   * [e. Persistent Data](#e-persistent-data) 
5. [Making Changes](#making-code-changes)  
   * [a. System Overview](#a-system-overview)  
   * [b. Creating a Skill](#b-creating-a-skill)   

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
> 
> `sudo usermod -aG docker $USER && newgrp`

## b. Running Neon
You can clone the repository, or just copy the `docker` directory contents onto your local system; this document will 
assume that the repository is cloned to: `~/NeonCore`.

> *Note*: The `docker` directory includes required hidden files. If you copy files, make sure to include any hidden
> files. In must Ubuntu distros, you can toggle hidden file visibility in the file explorer with `CTRL` + `h`.

> *Note*: If you run `docker` commands with `sudo`, make sure to use the `-E` flag to preserve runtime envvars.

> *Note*: Some Docker implementations don't handle relative paths.
> If you encounter errors, try updating the paths in `.env` to absolute paths.
> Also note that any environment variables will override the default values in `.env`.
> In BASH shells, you can list all current envvars with `env`

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

## e. Persistent Data
The `xdg/config` directory is mounted to each of the Neon containers as `XDG_CONFIG_HOME`.
`xdg/config/neon/neon.yaml` can be modified to change core configuration values.
`xdg/config/neon/skills` contains settings files for each loaded skill

The `xdg/data` directory is mounted to each of the Neon containers as `XDG_DATA_HOME`.
`xdg/data/neon/filesystem` contains skill filesystem files.
`xdg/data/neon/resources` contains user skill resource files.

The `xdg/cache` directory is mounted to each of the Neon containers as `XDG_CACHE_HOME`.
Any cache information should be recreated as needed if manually removed and includes things like
STT/TTS model files, TTS audio files, and other downloaded files.

> *Note*: When Docker creates files on the host filesystem, they are owned by `root`.
> In order to modify anything in the `xdg` directory, you may need to take ownership with:
> `sudo chown -R $USER:$USER xdg`

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
