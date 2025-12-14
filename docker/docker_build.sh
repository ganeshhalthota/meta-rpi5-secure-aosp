#!/bin/bash

function tst() {
	local cmmd="$@"
	echo "cmmd=$cmmd"
	eval $cmmd
	local ret=$?
	if [ $ret -ne 0 ] ; then
		echo "ERROR: \"$cmmd\" failed with ret=\"$ret\""
		exit 1
	fi
}

function build_docker_image() {
	local os="$1"
	tst "docker build --build-arg HOSTUSER=$USER -t rpi:$os -f Dockerfile_$os ."
}

OS=$1
if [ -z "$OS" ] ; then
	for file in $(ls Dockerfile_*) ; do
		echo "Building $file"
		OS=${file#*_}
		build_docker_image "$OS"
	done
else
	echo "Building for $OS"
	build_docker_image "$OS"
fi

tst "docker system prune --volumes -f"
