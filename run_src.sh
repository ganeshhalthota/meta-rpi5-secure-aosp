#!/usr/bin/env bash
#
# Wrapper script to run the RPi5 AOSP builder inside the container
# This script sets up the environment and executes the Python builder
#

set -e

# Setup environment variables
export XDG_CACHE_HOME=/opt/work/.cache
export GOPATH=/opt/work/.go
export GOCACHE=/opt/work/.cache/go-build

# Run the builder with all passed arguments
poetry run rpi5-build -w /opt/work/ "$@"
