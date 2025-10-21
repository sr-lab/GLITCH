FROM python:3.14-slim-trixie

COPY . /usr/src/glitch
WORKDIR /usr/src/glitch
RUN \
    apt-get update \
        && apt-get install -y --no-install-recommends ruby \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir -e .

WORKDIR /glitch

ENTRYPOINT ["glitch"]
