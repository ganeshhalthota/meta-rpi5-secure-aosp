#!/usr/bin/env bash
#
# Wrapper script to run the RPi5 AOSP builder inside the container
# This script sets up the environment and executes the Python builder
#

set -e

# Setup environment variables
export XDG_CACHE_HOME=/workspace/.cache
export GOPATH=/workspace/.go
export GOCACHE=/workspace/.cache/go-build

# Activate virtual environment
if [ -f /workspace/.venv/bin/activate ]; then
    source /workspace/.venv/bin/activate
else
    echo "Error: Virtual environment not found at /workspace/.venv"
    exit 1
fi

# Run the builder with all passed arguments
exec python3 /opt/src/meta_rpi5_secure_aosp/main.py -w /workspace/ "$@"
