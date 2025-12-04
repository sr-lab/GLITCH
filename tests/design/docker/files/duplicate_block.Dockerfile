FROM ubuntu:20.04
USER ubuntu

RUN wget https://repo.continuum.io/archive/Anaconda3-5.0.1-Linux-x86_64.sh && \
        gpg Anaconda3-5.0.1-Linux-x86_64.sh && \
        sh Anaconda3-5.0.1-Linux-x86_64.sh
CMD ['echo', "Hello"]

FROM ubuntu:20.04
USER ubuntu

RUN wget https://repo.continuum.io/archive/Anaconda3-5.0.1-Linux-x86_64.sh && \
        gpg Anaconda3-5.0.1-Linux-x86_64.sh && \
        sh Anaconda3-5.0.1-Linux-x86_64.sh
CMD ['echo', "Hello"]
