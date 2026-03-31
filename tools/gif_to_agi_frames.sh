#!/usr/bin/env bash
# Convert a local GIF to agi-cli frame files (00.txt, 01.txt, …).
# Requires: ffmpeg, chafa (brew install ffmpeg chafa)
set -euo pipefail

usage() {
  echo "usage: $0 path/to/animation.gif [output_dir]" >&2
  echo "  default output: ./frames next to this repo, or set second arg" >&2
  exit 1
}

[[ -n "${1:-}" ]] || usage
GIF="$1"
OUT="${2:-$(cd "$(dirname "$0")/.." && pwd)/frames}"

command -v ffmpeg >/dev/null || { echo "need ffmpeg" >&2; exit 1; }
command -v chafa >/dev/null || { echo "need chafa (brew install chafa)" >&2; exit 1; }
[[ -f "$GIF" ]] || { echo "not a file: $GIF" >&2; exit 1; }

mkdir -p "$OUT"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# ~4 fps, modest width — tune for terminal columns (~60–70 wide with agi padding).
ffmpeg -hide_banner -loglevel error -y -i "$GIF" -vf "fps=4,scale=420:-1" "$TMP/f_%04d.png"

n=0
shopt -s nullglob
for png in $(ls "$TMP"/f_*.png | LC_ALL=C sort); do
  chafa -f symbols --symbols ascii+extra -c none --size 58x18 "$png" | perl -pe 's/\e\[[0-9;]*m//g' > "$OUT/$(printf '%02d.txt' "$n")"
  n=$((n + 1))
done
shopt -u nullglob

echo "Wrote $n frames to $OUT"
