#!/bin/bash
# This script clones/pulls and builds libwayland in debug mode. It can be run from any directory. If
# anything goes wrong, feel free to rm -Rf resources/wayland and run again.

# Put bash into unofficial safe mode
set -euo pipefail
IFS=$'\n\t'

# Move into the directory where this script is located
cd "$( dirname "${BASH_SOURCE[0]}" )"

# Get the latest libwayland and move into the wayland directory
if ! test -d wayland
then
    git clone https://gitlab.freedesktop.org/wayland/wayland.git
fi

cd wayland
git pull

if ! test -d build
then
    echo "Running meson…"
    meson --buildtype=debug build
fi

echo "Building…"
ninja -C build

echo "Done"
