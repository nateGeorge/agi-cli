#!/usr/bin/env bash
# Installs the agi-cli release binary into AGI_CLI_BIN (default: ~/.local/bin).
# Override source: AGI_CLI_REPO=owner/repo AGI_CLI_BRANCH=main
set -euo pipefail

REPO="${AGI_CLI_REPO:-nateGeorge/agi-cli}"
BRANCH="${AGI_CLI_BRANCH:-main}"
BASE_URL="https://raw.githubusercontent.com/${REPO}/${BRANCH}"

BIN_DIR="${AGI_CLI_BIN:-$HOME/.local/bin}"
mkdir -p "$BIN_DIR"

echo "Fetching agi from ${BASE_URL} ..."
curl -fsSL "${BASE_URL}/agi" -o "${BIN_DIR}/agi"
chmod +x "${BIN_DIR}/agi"

FRAMES_DIR="${HOME}/.config/agi-cli/frames"
mkdir -p "${FRAMES_DIR}"
echo "Fetching animation frames..."
for i in 00 01 02 03 04 05 06 07 08 09 10 11; do
  curl -fsSL "${BASE_URL}/frames/${i}.txt" -o "${FRAMES_DIR}/${i}.txt"
done

if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
  echo "" >&2
  echo "Add to PATH (e.g. in ~/.zshrc):" >&2
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\"" >&2
fi

echo "Installed: ${BIN_DIR}/agi"
echo "Run: agi"
