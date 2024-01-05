#!/bin/bash
# This script clones/pulls and builds libwayland in debug mode. It can be run from any directory. If
# anything goes wrong, feel free to rm -Rf resources/wayland and run again.

# Put bash into unofficial safe mode
set -euo pipefail

# Move into the directory where this script is located
cd "$( dirname "${BASH_SOURCE[0]}" )"

# If our last attempt resulted in an incomplete build, wipe it and start over
if test -d wayland -a ! -f wayland/build-complete
then
    echo "Wiping wayland and re-cloning…"
    rm -Rf wayland/
fi

# Get the latest libwayland and move into the wayland directory
if ! test -d wayland
then
    git clone --depth 1 https://gitlab.freedesktop.org/wayland/wayland.git
fi

cd wayland
git reset --hard origin/main
git pull

# Apply patches
git apply ../libwayland-patches/*.patch

if ! test -d build
then
    echo "Running meson…"
    meson setup --buildtype=debug -Dtests=false -Ddocumentation=false -Ddtd_validation=false build
fi

echo "Building…"
ninja -C build

# Touching this file means meson is in a good state, and we don't have to re-clone next time
touch build-complete
echo "Done"
