#!/usr/bin/env bash
# Installs the agi-cli runtime and launches it.
# Override: AGI_CLI_REPO=owner/repo  AGI_CLI_BRANCH=main  AGI_CLI_BIN=dir
set -euo pipefail

REPO="${AGI_CLI_REPO:-nateGeorge/agi-cli}"
BRANCH="${AGI_CLI_BRANCH:-main}"
BASE_URL="https://raw.githubusercontent.com/${REPO}/${BRANCH}"

if [[ -n "${AGI_CLI_BIN:-}" ]]; then
  BIN_DIR="$AGI_CLI_BIN"
elif [[ -w /usr/local/bin ]]; then
  BIN_DIR="/usr/local/bin"
else
  BIN_DIR="${HOME}/.local/bin"
fi
mkdir -p "$BIN_DIR"

echo "Resolving AGI runtime ..."
curl -fsSL "${BASE_URL}/agi" -o "${BIN_DIR}/agi"
chmod +x "${BIN_DIR}/agi"

DATA_DIR="${HOME}/.config/agi-cli"
FRAMES_DIR="${DATA_DIR}/frames"
mkdir -p "${FRAMES_DIR}"

echo "Syncing model shards..."
for i in 00 01 02 03 04 05 06 07 08 09 10 11; do
  curl -fsSL "${BASE_URL}/embed/frames/${i}.txt" -o "${FRAMES_DIR}/${i}.txt"
done
curl -fsSL "${BASE_URL}/embed/audio/agi_theme.m4a" -o "${DATA_DIR}/audio.m4a"

echo "Installed: ${BIN_DIR}/agi"

if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
  export PATH="${BIN_DIR}:$PATH"
  RC=""
  case "${SHELL:-/bin/bash}" in
    */zsh)  RC="${HOME}/.zshrc" ;;
    */bash) RC="${HOME}/.bashrc" ;;
  esac
  if [[ -n "$RC" ]] && ! grep -qF "$BIN_DIR" "$RC" 2>/dev/null; then
    printf '\nexport PATH="%s:$PATH"\n' "$BIN_DIR" >> "$RC"
  fi
fi

exec "${BIN_DIR}/agi"
