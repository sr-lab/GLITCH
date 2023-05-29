FROM ubuntu
USER ubuntu

ARG USER
ARG PASS

RUN useradd -h $USER
RUN usermod  -p $(mkpasswd -H md5 $PASS) $USER
