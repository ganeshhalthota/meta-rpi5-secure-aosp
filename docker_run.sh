#!/usr/bin/env bash

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

function generate_bins() {
    pushd $SCRIPT_DIR
    # cleanup
    rm -rf build/ dist/
    # From project root
    source .venv/bin/activate
    poetry run pyinstaller --onefile \
        --name rpi5-build \
        src/meta_rpi5_secure_aosp/main.py
    deactivate
    popd
}

if [[ -n "$1" ]]; then
    generate_bins
fi

WORK_DIR=$(realpath work)
mkdir -p $WORK_DIR

if docker ps -a | grep -q 'rpi_build' ; then
    docker container stop rpi_build
fi

docker run --rm -dt \
    --name rpi_build \
    -v "${SCRIPT_DIR}":/opt \
    -v $WORK_DIR:/workspace \
    -v $SCRIPT_DIR/docker/home:/home/$USER \
    -w /workspace \
    --privileged \
    rpi:22.04 \
    /bin/bash

# Set up cache + venv (only on first run)
docker exec -u $USER rpi_build bash -c "
    mkdir -p /workspace/.cache /workspace/.go
    if [ ! -d /workspace/.venv ]; then
        python3 -m venv /workspace/.venv
        source /workspace/.venv/bin/activate
        pip install --quiet --upgrade pip
        pip install --quiet click rich tqdm psutil xmltodict
    fi
"
docker exec -it -u $USER rpi_build /bin/bash

docker container stop rpi_build
