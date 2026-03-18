#!/usr/bin/env bash
# Update files copied from the Picard repository.
# See registry_lib/picard/README.md for details.

set -euo pipefail

REPO="metabrainz/picard"
BRANCH="master"
BASE_URL="https://raw.githubusercontent.com/${REPO}/refs/heads/${BRANCH}/picard/plugin3"
DEST_DIR="$(dirname "$0")/../registry_lib/picard"

FILES=(
    constants.py
    validator.py
)

for file in "${FILES[@]}"; do
    echo "Downloading ${file}..."
    curl -fsSL "${BASE_URL}/${file}" -o "${DEST_DIR}/${file}"
done

echo "Done. Review changes with: git diff registry_lib/picard/"
