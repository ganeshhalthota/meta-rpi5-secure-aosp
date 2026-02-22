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

# Activate virtual environment
if [ -f /opt/.venv/bin/activate ]; then
    source /opt/.venv/bin/activate
else
    echo "Error: Virtual environment not found at /opt/.venv"
    exit 1
fi

# Run the builder with all passed arguments
exec python3 /opt/src/meta_rpi5_secure_aosp/main.py -w /opt/work/ "$@"
