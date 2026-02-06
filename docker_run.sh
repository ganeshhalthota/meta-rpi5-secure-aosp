#!/usr/bin/env bash
set -ex

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
CONTAINER_NAME="rpi_build"
IMAGE_NAME="rpi:22.04"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

function log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

function log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

function show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] [COMMAND] [ARGS...]

Options:
  --build-binary    Build PyInstaller binary before running
  --shell          Start interactive shell (default if no command)
  --help           Show this help message

Commands:
  If no command is provided, starts an interactive shell.
  Otherwise, runs the command inside the container.

Examples:
  $0 --shell                                    # Interactive shell
  $0 /opt/run_src.sh --stage sync --code aosp  # Run build directly
  $0 python3 /opt/src/meta_rpi5_secure_aosp/main.py --help

EOF
}

function generate_bins() {
    log_info "Building PyInstaller binary..."
    pushd "$SCRIPT_DIR" > /dev/null
    # cleanup
    rm -rf build/ dist/
    # From project root
    if [ ! -d ".venv" ]; then
        log_error "Virtual environment not found. Please run 'python3 -m venv .venv' first."
        exit 1
    fi
    source .venv/bin/activate
    poetry run pyinstaller --onefile \
        --name rpi5-build \
        src/meta_rpi5_secure_aosp/main.py
    deactivate
    popd > /dev/null
    log_info "Binary built successfully: dist/rpi5-build"
}

function cleanup_container() {
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_info "Stopping existing container: ${CONTAINER_NAME}"
        docker container stop "${CONTAINER_NAME}" > /dev/null 2>&1 || true
        docker container rm "${CONTAINER_NAME}" > /dev/null 2>&1 || true
    fi
}

function setup_container() {
    local WORK_DIR=$(realpath work)

    if [[ ! -d "${WORK_DIR}" ]]; then
        mkdir -p "$WORK_DIR"
        # Copy resources to work directory
        cp -rp resources/* ${WORK_DIR}/
    fi

    # Get current user info
    local HOST_UID=$(id -u)
    local HOST_GID=$(id -g)
    local HOST_USER=$(id -un)

    log_info "Starting container: ${CONTAINER_NAME}"
    log_info "  Workspace: ${WORK_DIR}"
    log_info "  User: ${HOST_USER} (UID=${HOST_UID}, GID=${HOST_GID})"

    docker run -d \
        --name "${CONTAINER_NAME}" \
        --rm \
        -v "${SCRIPT_DIR}/docker/home":"/home/${HOST_USER}" \
        -v "${SCRIPT_DIR}":/opt \
        -v "${WORK_DIR}":/workspace \
        -v /etc/gitconfig:/etc/gitconfig:ro \
        -w /workspace \
        --privileged \
        -e "HOST_UID=${HOST_UID}" \
        -e "HOST_GID=${HOST_GID}" \
        -e "HOST_USER=${HOST_USER}" \
        -e "SUDO_USER=${HOST_USER}" \
        "${IMAGE_NAME}" \
        sleep infinity > /dev/null

    # Set up environment inside container
    log_info "Setting up Python environment..."

    # Then run setup as the user
    docker exec -u "${HOST_USER}" "${CONTAINER_NAME}" bash -c '
        mkdir -p /workspace/.cache /workspace/.go
        if [ ! -d /workspace/.venv ]; then
            echo "Creating virtual environment..."
            python3 -m venv /workspace/.venv
            source /workspace/.venv/bin/activate
            pip install --quiet --upgrade pip
            pip install --quiet click rich tqdm psutil xmltodict
            echo "Virtual environment created successfully"
        else
            echo "Virtual environment already exists"
        fi
    '

    log_info "Container ready!"
}

function run_command() {
    local cmd="$@"
    local HOST_USER=$(id -un)

    if [ -z "$cmd" ]; then
        log_info "Starting interactive shell..."
        docker exec -it -u "${HOST_USER}" "${CONTAINER_NAME}" /bin/bash
    else
        log_info "Executing: $cmd"
        docker exec -it -u "${HOST_USER}" "${CONTAINER_NAME}" bash -c "$cmd"
    fi
}

# Parse arguments
BUILD_BINARY=false
INTERACTIVE=false
COMMAND_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --build-binary)
            BUILD_BINARY=true
            shift
            ;;
        --shell)
            INTERACTIVE=true
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            COMMAND_ARGS+=("$1")
            shift
            ;;
    esac
done

# Main execution
if [ "$BUILD_BINARY" = true ]; then
    generate_bins
fi

# Cleanup any existing container
cleanup_container

# Setup new container
setup_container

# Trap to ensure cleanup on exit
trap "cleanup_container" EXIT

# Run command or interactive shell
if [ "$INTERACTIVE" = true ] || [ ${#COMMAND_ARGS[@]} -eq 0 ]; then
    run_command
else
    run_command "${COMMAND_ARGS[@]}"
fi
