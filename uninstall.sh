#!/usr/bin/env bash
# Removes agi-cli binary and cached data.
set -euo pipefail

removed=0

for bin_dir in /usr/local/bin "${HOME}/.local/bin"; do
  if [[ -f "${bin_dir}/agi" ]]; then
    rm -f "${bin_dir}/agi"
    echo "Removed ${bin_dir}/agi"
    removed=1
  fi
done

if [[ -n "${AGI_CLI_BIN:-}" && -f "${AGI_CLI_BIN}/agi" ]]; then
  rm -f "${AGI_CLI_BIN}/agi"
  echo "Removed ${AGI_CLI_BIN}/agi"
  removed=1
fi

DATA_DIR="${HOME}/.config/agi-cli"
if [[ -d "$DATA_DIR" ]]; then
  rm -rf "$DATA_DIR"
  echo "Removed ${DATA_DIR}"
  removed=1
fi

if (( removed == 0 )); then
  echo "Nothing to remove — agi-cli does not appear to be installed."
else
  echo "agi-cli uninstalled."
fi
