FROM ubuntu:20.04
USER ubuntu

RUN foo bar --a b \
        --c d
