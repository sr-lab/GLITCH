FROM python:3-slim

COPY . /usr/src/glitch
WORKDIR /usr/src/glitch
RUN python -m pip install -e .

WORKDIR /glitch

ENTRYPOINT ["glitch"]
