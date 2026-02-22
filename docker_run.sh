#!/usr/bin/env bash
set -e

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
CONTAINER_NAME="rpi_build"
DOCKERFILE="docker/Dockerfile_24.04"

if [ ! -f "$SCRIPT_DIR/$DOCKERFILE" ]; then
    log_error "Dockerfile not found at $SCRIPT_DIR/$DOCKERFILE"
    exit 1
fi

DOCKERFILE_SHA=$(sha256sum "$SCRIPT_DIR/$DOCKERFILE" | awk '{print $1}')
IMAGE_NAME="rpi5-${DOCKERFILE_SHA}"

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
Usage: $0 [OPTIONS] [ARGS...]

Options:
  --build-binary    Build PyInstaller binary before running
  --shell          Start interactive shell (default if no command)
  --help           Show this help message

Commands:
  If no command is provided, starts an interactive shell.
  If args are provided, they are passed directly to the python builder application.

Examples:
  $0 --shell                                   # Interactive shell
  $0 --stage sync --code aosp                  # Pass args to python app directly
  $0 --help                                    # Pass --help to python app directly

EOF
}

function check_and_build_image() {
    if ! docker images -q "$IMAGE_NAME" | grep -q .; then
        log_info "Docker image $IMAGE_NAME not found. Building..."
        local host_user=$(id -un)
        if ! docker build --build-arg HOSTUSER="$host_user" -t "$IMAGE_NAME" -f "$SCRIPT_DIR/$DOCKERFILE" "$SCRIPT_DIR/docker"; then
             log_error "Failed to build docker image."
             exit 1
        fi
        log_info "Docker image built successfully."
        docker system prune --volumes -f > /dev/null 2>&1 || true
    else
        log_info "Using existing docker image: $IMAGE_NAME"
    fi
}

function cleanup_container() {
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_info "Stopping existing container: ${CONTAINER_NAME}"
        docker container stop "${CONTAINER_NAME}" > /dev/null 2>&1 || true
        docker container rm "${CONTAINER_NAME}" > /dev/null 2>&1 || true
    fi
}

function setup_container() {
    local work_dir=$(realpath work)

    if [[ ! -d "${work_dir}" ]]; then
        mkdir -p "$work_dir"
        # Copy resources to work directory
        cp -rp resources/* ${work_dir}/
    fi

    # Get current user info
    local host_uid=$(id -u)
    local host_gid=$(id -g)
    local host_user=$(id -un)

    log_info "Starting container: ${CONTAINER_NAME}"
    log_info "  Workspace: ${work_dir}"
    log_info "  User: ${host_user} (UID=${host_uid}, GID=${host_gid})"

    # Ensure poetry.lock, pyproject.toml, and .venv exist so docker doesn't map them as root directories
    touch "$SCRIPT_DIR/poetry.lock" "$SCRIPT_DIR/pyproject.toml"
    mkdir -p "$SCRIPT_DIR/.venv"

    docker run -d \
        --name "${CONTAINER_NAME}" \
        --rm \
        -v "${SCRIPT_DIR}/docker/home":"/home/${host_user}" \
        -v "${SCRIPT_DIR}":/opt:rw \
        -v /etc/gitconfig:/etc/gitconfig:ro \
        -w /opt/work \
        --privileged \
        -e "HOST_UID=${host_uid}" \
        -e "HOST_GID=${host_gid}" \
        -e "HOST_USER=${host_user}" \
        -e "SUDO_USER=${host_user}" \
        "${IMAGE_NAME}" \
        sleep infinity > /dev/null

    # Set up environment inside container
    log_info "Setting up Python environment with Poetry..."

    # Then run setup as the user
    docker exec -u "${host_user}" "${CONTAINER_NAME}" bash -c '
        mkdir -p /opt/work/.cache /opt/work/.go
    '

    log_info "Container ready!"
}

function run_command() {
    local cmd="$@"
    local host_user=$(id -un)

    if [ -z "$cmd" ] && [ "$INTERACTIVE" = true ]; then
        log_info "Starting interactive shell..."
        docker exec -it -w /opt -u "${host_user}" "${CONTAINER_NAME}" /bin/bash
    elif [ -z "$cmd" ]; then
        log_info "Starting interactive shell..."
        docker exec -it -w /opt -u "${host_user}" "${CONTAINER_NAME}" /bin/bash
    else
        log_info "Executing python builder application with args: $cmd"
        # We invoke run_src.sh to handle virtual environment activation inside the container
        docker exec -it -w /opt -u "${host_user}" "${CONTAINER_NAME}" bash -c "/opt/run_src.sh $cmd"
    fi
}

# Parse arguments
INTERACTIVE=false
COMMAND_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --shell)
            INTERACTIVE=true
            shift
            ;;
        *)
            COMMAND_ARGS+=("$1")
            shift
            ;;
    esac
done

# Ensure docker image is available
check_and_build_image

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
