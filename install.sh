#!/usr/bin/env bash
# Install agi-cli: curl -fsSL https://raw.githubusercontent.com/OWNER/agi-cli/main/install.sh | bash
# Optional: AGI_CLI_REPO=owner/agi-cli AGI_CLI_BRANCH=main bash
set -euo pipefail

REPO="${AGI_CLI_REPO:-YOUR_GITHUB_USER/agi-cli}"
BRANCH="${AGI_CLI_BRANCH:-main}"
BASE_URL="https://raw.githubusercontent.com/${REPO}/${BRANCH}"

if [[ "${REPO}" == *"YOUR_GITHUB_USER"* ]]; then
  echo "Set AGI_CLI_REPO to your fork, e.g.:" >&2
  echo "  curl -fsSL .../install.sh | AGI_CLI_REPO=you/agi-cli bash" >&2
  exit 1
fi

BIN_DIR="${AGI_CLI_BIN:-$HOME/.local/bin}"
mkdir -p "$BIN_DIR"

echo "Fetching agi from ${BASE_URL} ..."
curl -fsSL "${BASE_URL}/agi" -o "${BIN_DIR}/agi"
chmod +x "${BIN_DIR}/agi"

if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
  echo "" >&2
  echo "Add to PATH (e.g. in ~/.zshrc):" >&2
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\"" >&2
fi

echo "Installed: ${BIN_DIR}/agi"
echo "Run: agi"
