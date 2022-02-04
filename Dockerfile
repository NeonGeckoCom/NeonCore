FROM python:3.8-slim as base

LABEL vendor=neon.ai \
    ai.neon.name="neon-skills"

ENV NEON_CONFIG_PATH /config

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
    ffmpeg \
    git  # TODO: git required for getting scripts, skill should be refactored to remove this dependency

ADD . /neon_core
WORKDIR /neon_core

COPY docker_overlay/asoundrc /root/.asoundrc

RUN mkdir -p /root/.config/neon
COPY docker_overlay/neon.conf /root/.config/neon/neon.conf

RUN pip install wheel && \
    pip install .

CMD ["neon", "run-skills", "-i", "/skills"]

FROM base as default_skills

RUN mkdir -p /root/.local/share/neon
COPY docker_overlay/skill_settings /root/.config/neon/skills
COPY docker_overlay/ngi_local_conf.yml /config/
RUN neon-install-default-skills
RUN rm /config/ngi_local_conf.yml