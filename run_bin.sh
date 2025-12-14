#!/bin/bash

mkdir -p /workspace/.cache
export HOME=/workspace
export XDG_CACHE_HOME=/workspace/.cache
export GOPATH=/workspace/.go
export GOCACHE=/workspace/.cache/go-build

/opt/dist/rpi5-build -w /workspace/ "$@"
