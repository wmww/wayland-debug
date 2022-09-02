#!/bin/bash
# This script removes all files in the resources/wayland directory except the libraries needed
# to run libwayland. It can save disk space, and is mostly used by the snap build.

# Put bash into unofficial safe mode
set -euo pipefail

# Move into the directory where this script is located
cd "$( dirname "${BASH_SOURCE[0]}" )"

if test ! -d wayland
then
    echo "No wayland directory"
    exit
fi

find wayland/ \
    -type f -a \
    -not -name "libwayland-client*.so*" -a \
    -not -name "libwayland-server*.so*" \
    | xargs rm -f

while find wayland/ -type d -empty | xargs rmdir 2>/dev/null
do
    : # no-op
done

echo "Done"
