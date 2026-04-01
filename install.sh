#!/usr/bin/env bash
# Installs the agi-cli release binary into AGI_CLI_BIN (default: /usr/local/bin).
# Override source: AGI_CLI_REPO=owner/repo AGI_CLI_BRANCH=main
set -euo pipefail

REPO="${AGI_CLI_REPO:-nateGeorge/agi-cli}"
BRANCH="${AGI_CLI_BRANCH:-main}"
BASE_URL="https://raw.githubusercontent.com/${REPO}/${BRANCH}"

BIN_DIR="${AGI_CLI_BIN:-/usr/local/bin}"
mkdir -p "$BIN_DIR" 2>/dev/null || true

echo "Resolving AGI runtime from ${BASE_URL} ..."
curl -fsSL "${BASE_URL}/agi" -o "${BIN_DIR}/agi" 2>/dev/null
chmod +x "${BIN_DIR}/agi"

DATA_DIR="${HOME}/.config/agi-cli"
FRAMES_DIR="${DATA_DIR}/frames"
mkdir -p "${FRAMES_DIR}"

echo "Syncing model shards..."
for i in 00 01 02 03 04 05 06 07 08 09 10 11; do
  curl -fsSL "${BASE_URL}/embed/frames/${i}.txt" -o "${FRAMES_DIR}/${i}.txt" 2>/dev/null
done
curl -fsSL "${BASE_URL}/embed/audio/agi_theme.m4a" -o "${DATA_DIR}/audio.m4a" 2>/dev/null

if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
  echo "" >&2
  echo "Add to PATH (e.g. in ~/.zshrc):" >&2
  echo "  export PATH=\"${BIN_DIR}:\$PATH\"" >&2
fi

echo "Installed: ${BIN_DIR}/agi"
echo "Run: agi"
