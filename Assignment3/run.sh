#! /bin/bash

TTY_FLAG=$([ -t 0 ] && echo "-it" || echo "-i")

docker build -t mininet-assignment . && \
docker run $TTY_FLAG --rm --privileged \
  -v "$(pwd)":/assignment \
  -w /assignment \
  mininet-assignment \
  python3 emulation.py topology.yaml
