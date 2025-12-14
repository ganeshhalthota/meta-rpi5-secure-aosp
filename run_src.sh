#!/bin/bash

# export HOME=/workspace
export XDG_CACHE_HOME=/workspace/.cache
export GOPATH=/workspace/.go
export GOCACHE=/workspace/.cache/go-build
source /workspace/.venv/bin/activate
python3 /opt/src/meta_rpi5_secure_aosp/main.py -w /workspace/ "$@"
