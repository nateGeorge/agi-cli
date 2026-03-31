#!/usr/bin/env bash
# Environment sanity checks for interactive sessions (non-exhaustive).
set -euo pipefail
echo "agi-cli verify_env"
echo "  shell: ${BASH_VERSION:-unknown}"
echo "  uname: $(uname -a)"
echo "  tty:   $(tty 2>/dev/null || echo n/a)"
if command -v tput >/dev/null 2>&1; then
  echo "  term:  ${TERM:-unknown} ($(tput cols 2>/dev/null || echo '?')x$(tput lines 2>/dev/null || echo '?'))"
else
  echo "  term:  ${TERM:-unknown} (tput unavailable)"
fi
echo "OK"
