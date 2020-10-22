#!/bin/bash
# This script downloads the latest Wayland protocols from their git repos.
# It is intended to be run periodically by a developer, and the resulting
# changes should be committed to git.

# Put bash into unofficial safe mode
set -euo pipefail
IFS=$'\n\t'

# Declare the array of git repos containing protocols
declare -a REPOS=(
    "core          https://gitlab.freedesktop.org/wayland/wayland.git"
    "standard      https://gitlab.freedesktop.org/wayland/wayland-protocols.git"
    "mir           https://github.com/MirServer/mir.git"
    "wlroots       https://github.com/swaywm/wlroots.git"
    "wlr-protocols https://github.com/swaywm/wlr-protocols.git"
    "plasma-wayland-protocols https://invent.kde.org/libraries/plasma-wayland-protocols")

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Set the directory to download the protocols to
PROTOCOL_DIR="${SCRIPT_DIR}/protocols"

# Clear out the protocol directory
echo "Cleaning out ${PROTOCOL_DIR}…"
rm -Rf "${PROTOCOL_DIR}"
mkdir -p "${PROTOCOL_DIR}"

echo "Cloning ${#REPOS[@]} repos into ${PROTOCOL_DIR}…"
# Clone the repos and delete the .git for each
for REPO in "${REPOS[@]}"
do
    # Get the name of the directory to clone into and the git URL
    REPO_NAME=$(echo "${REPO}" | awk '{print $1}')
    REPO_URL=$(echo "${REPO}" | awk '{print $2}')

    # Clone the repo into a subdirectory of the protocol directory
    echo "Cloning ${REPO_URL} into ${PROTOCOL_DIR}/${REPO_NAME}…"
    git -C "${PROTOCOL_DIR}" clone --depth=1 "${REPO_URL}" "${REPO_NAME}"

    # Remove the repo's .git
    rm -Rf "${PROTOCOL_DIR}/${REPO_NAME}/.git"
done

echo "Deleting unneeded files…"
# Delete everything but XML and licenses
find "${PROTOCOL_DIR}" -type f -and -not -iname '*.xml' -and -not -iname 'COPYING*' -and -not -iname 'LICENSE*' | xargs rm
# Special case this directory we don't need
rm -Rf "${PROTOCOL_DIR}/core/tests"
# Delete XML files that aren't Wayland protocols
find "${PROTOCOL_DIR}" -iname '*.xml' | xargs grep -L '^<protocol name=.*>$' | xargs rm
# Remove any directories that are now empty
find "${PROTOCOL_DIR}" -type d -empty | xargs rmdir

# Save a readme file into the protocol directory
echo "Generating README…"
echo "CONTENTS AUTOMATICALLY DOWNLOADED - DO NOT EDIT
To update, run ${BASH_SOURCE[0]}
Last updated $(date) [$(date +'%s')]" > "${PROTOCOL_DIR}/README"

echo "Done"
