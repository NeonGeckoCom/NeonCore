FROM python:3.10-slim as base

LABEL vendor=neon.ai \
    ai.neon.name="neon-skills"

ENV OVOS_CONFIG_BASE_FOLDER neon
ENV OVOS_CONFIG_FILENAME neon.yaml
ENV XDG_CONFIG_HOME /config

RUN  apt-get update && \
     apt-get install -y \
     curl \
     gpg

RUN  curl https://forslund.github.io/mycroft-desktop-repo/mycroft-desktop.gpg.key | \
     gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/mycroft-desktop.gpg --import - && \
     chmod a+r /etc/apt/trusted.gpg.d/mycroft-desktop.gpg && \
     echo "deb http://forslund.github.io/mycroft-desktop-repo bionic main" \
     > /etc/apt/sources.list.d/mycroft-mimic.list


RUN apt-get update && \
    apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    swig \
    libssl-dev \
    libfann-dev \
    portaudio19-dev \
    libsndfile1 \
    libpulse-dev \
    alsa-utils \
    libasound2-plugins \
    pulseaudio-utils \
    ffmpeg \
    mimic \
    sox \
    git

# TODO: git required for getting scripts, skill should be refactored to remove this dependency
# TODO: sox, mimic required for demo skill, audio service should be refactored to handle TTS engines/voices in request

ADD . /neon_core
WORKDIR /neon_core

RUN pip install wheel && \
    pip install .[docker]

COPY docker_overlay/ /
RUN chmod ugo+x /root/run.sh && \
    neon update-default-resources

CMD ["/root/run.sh"]

FROM base as default_skills
RUN pip install .[skills_required,skills_essential,skills_default,skills_extended]
# Default skills from configuration are installed at container creation
