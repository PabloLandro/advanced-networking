FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    mininet \
    python3 \
    python3-yaml \
    iproute2 \
    net-tools \
    iputils-ping \
    bridge-utils \
    traceroute \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /assignment
