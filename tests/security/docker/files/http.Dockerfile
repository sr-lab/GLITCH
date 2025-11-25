FROM python as builder
USER builder

ARG URL
RUN curl http://$URL.com
