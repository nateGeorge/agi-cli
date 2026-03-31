#!/usr/bin/env bash
# Emit a JSON manifest stub for CI / packaging hooks.
set -euo pipefail
printf '{"artifact":"agi-cli","version":"0.9.7-rc.2","entrypoint":"agi","configs":["config/default.yaml","config/rce-7b.yaml"]}\n'
