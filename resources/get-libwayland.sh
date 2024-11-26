#!/bin/bash
# This script clones/pulls and builds libwayland in debug mode. It can be run from any directory. If
# anything goes wrong, feel free to rm -Rf resources/wayland and run again.

LIBWAYLAND_VERSION=1.23.1
LIBWAYLAND_REPO="https://gitlab.freedesktop.org/wayland/wayland.git"

# Put bash into unofficial safe mode
set -euo pipefail

# Move into the directory where this script is located
cd "$( dirname "${BASH_SOURCE[0]}" )"

# Wipe the libwayland directory if it already exists
if test -d wayland
then
    echo "Wiping wayland and re-cloning…"
    rm -rf wayland/
fi

# Get libwayland and move into its directory
git clone --depth 1 --branch "$LIBWAYLAND_VERSION" "$LIBWAYLAND_REPO"
cd wayland

# Apply patches
git apply ../libwayland-patches/*.patch

echo "Running meson…"
meson setup --buildtype=debug -Dtests=false -Ddocumentation=false -Ddtd_validation=false build

echo "Building…"
ninja -C build

echo "Done"
