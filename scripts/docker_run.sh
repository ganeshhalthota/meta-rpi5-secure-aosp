#!/usr/bin/env bash
set -e

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
        if ! docker build --build-arg HOSTUSER="$host_user" -t "$IMAGE_NAME" -f "$PROJECT_DIR/$DOCKERFILE" "$PROJECT_DIR/docker"; then
             log_error "Failed to build docker image."
             exit 1
        fi
        log_info "Docker image built successfully."
        docker system prune --volumes -f > /dev/null 2>&1 || true
    else
        log_info "Using existing docker image: $IMAGE_NAME"
    fi
}

function start_container() {
    local cmd="$@"
    local work_dir="$PROJECT_DIR/work"

    # Ensure cache/config directories exist and are writable by the host user.
    # These may have been created previously by a root-run container, so we
    # proactively chown them to avoid Poetry/virtualenv permission errors.
    # Create cache directories if they don't exist
    mkdir -p .cache/pypoetry .cache/pip .cache/tmp
    mkdir -p "${work_dir}/.cache/pypoetry"
    mkdir -p "${work_dir}/.cache/pip"
    mkdir -p "${work_dir}/.cache/tmp"
    mkdir -p "${work_dir}/.cache/go-build"
    mkdir -p "${work_dir}/.cache/.go"

    # Best-effort ownership fixup (no-op if user lacks permission).
    chown -R "$(id -u):$(id -g)" "${work_dir}/.cache" 2>/dev/null || true

    # Get current user info
    local host_uid=$(id -u)
    local host_gid=$(id -g)
    local host_user=$(id -un)
    local host_home="${HOME}"

    log_info "Starting container: ${CONTAINER_NAME}"
    log_info "  Workspace: ${work_dir}"
    log_info "  User: ${host_user} (UID=${host_uid}, GID=${host_gid})"

    # Build optional SSH mount: repo sync authenticates to Gerrit via SSH and
    # needs the host user's key pair.  Mount read-only so the container cannot
    # modify the host's SSH directory.
    local ssh_mount=()
    if [[ -d "${host_home}/.ssh" ]]; then
        ssh_mount=(-v "${host_home}/.ssh":"/home/${host_user}/.ssh":ro)
        log_info "  SSH keys: ${host_home}/.ssh (read-only)"
    else
        log_warn "  SSH keys: ${host_home}/.ssh not found - repo sync over SSH may fail"
    fi

    # pip and poetry config mounting
    local pip_conf=()
    if [[ -d "${host_home}/.pip" ]]; then
        pip_conf=(-v "${host_home}/.pip":"/home/${host_user}/.pip":ro)
        log_info "  pip config: ${host_home}/.pip (read-only)"
    else
        log_warn "  pip config: ${host_home}/.pip not found - pip commands may fail"
    fi

    DOCKER_ARGS="-it --rm \
        --name ${CONTAINER_NAME} \
        -v ${PROJECT_DIR}/docker/home:/home/${host_user} \
        ${ssh_mount[@]} \
        ${pip_conf[@]} \
        -v ${PROJECT_DIR}:/app:rw \
        -v /etc/gitconfig:/etc/gitconfig:ro \
        -v ${work_dir}:/app/work \
        -v ${work_dir}/.cache/tmp:/tmp \
        --privileged \
        -e POETRY_CACHE_DIR=/app/work/.cache/pypoetry \
        -e PIP_CACHE_DIR=/app/work/.cache/pip \
        -e XDG_CACHE_HOME=/app/work/.cache \
        -e GOPATH=/app/work/.go \
        -e GOCACHE=/app/work/.cache/go-build \
        -e TMPDIR=/tmp \
        -e USER_ID=${host_uid} \
        -e GROUP_ID=${host_gid} \
        -e USERNAME=${host_user} \
        ${IMAGE_NAME}"

    if [ -z "$cmd" ] && [ "$INTERACTIVE" = true ]; then
        log_info "Starting interactive shell..."
        docker run ${DOCKER_ARGS} /bin/bash
    else
        log_info "Executing python builder application with args: $cmd"
        docker run ${DOCKER_ARGS} \
            /bin/bash -c "cd /app/ && \
                          poetry lock && \
                          poetry install && \
                          poetry run rpi5-build -w /app/work/ $cmd"
    fi
}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
PROJECT_DIR=$(dirname "$SCRIPT_DIR")
CONTAINER_NAME="rpi_build"
DOCKERFILE="docker/Dockerfile_24.04"

if [ ! -f "$PROJECT_DIR/$DOCKERFILE" ]; then
    log_error "Dockerfile not found at $PROJECT_DIR/$DOCKERFILE"
    exit 1
fi

DOCKERFILE_SHA=$(sha256sum "$PROJECT_DIR/$DOCKERFILE" | awk '{print $1}')
IMAGE_NAME="rpi5-${DOCKERFILE_SHA:0:12}"

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

# Setup new container
start_container "${COMMAND_ARGS[@]}"
