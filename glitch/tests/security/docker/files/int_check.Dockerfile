FROM ubuntu
USER ubuntu
RUN wget https://repo.continuum.io/archive/Anaconda3-5.0.1-Linux-x86_64.sh
RUN wget https://repo.continuum.io/archive/Anaconda3-5-Linux-x86_64.sh

RUN gpg Anaconda3-5.0.1-Linux-x86_64.sh