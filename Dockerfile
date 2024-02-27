FROM python:3.10-slim

# Set ENV variables
ENV LANG C.UTF-8
ENV SHELL=/bin/bash
ENV DEBIAN_FRONTEND=noninteractive

ENV APT_INSTALL="apt-get install -y --no-install-recommends"
ENV PIP_INSTALL="python -m pip --no-cache-dir install --upgrade"

RUN apt-get update && \
    $APT_INSTALL rsync openssh-client && \
    # cleanup apt cache
    rm -rf /var/lib/apt/lists/*

RUN $PIP_INSTALL dagster-cloud[serverless]
