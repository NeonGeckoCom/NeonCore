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

RUN pip install wheel && \
    pip install .[docker]

COPY docker_overlay/ /
RUN chmod ugo+x /root/run.sh

CMD ["/root/run.sh"]

FROM base as default_skills
RUN neon-install-default-skills