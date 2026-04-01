#!/usr/bin/env bash
# Convert a local GIF to agi-cli frame files (00.txt, 01.txt, …).
# Uses chafa symbols + color for tonal detail (not flat silhouette).
# Requires: ffmpeg, chafa (brew install ffmpeg chafa)
#
# Env (optional):
#   CHAFA_SIZE    — default 76x32 (fits ~80-col terminals with agi indent)
#   CHAFA_SYMBOLS — default "block,braille,extra" (avoid "all" — rare glyphs → tofu □ in many fonts)
#   CHAFA_COLORS  — default "256" (widely supported; "full" for 24-bit if your font/terminal handles it)
set -euo pipefail

usage() {
  echo "usage: $0 path/to/animation.gif [output_dir]" >&2
  echo "  default output: ./embed/frames next to this repo, or set second arg" >&2
  exit 1
}

[[ -n "${1:-}" ]] || usage
GIF="$1"
OUT="${2:-$(cd "$(dirname "$0")/.." && pwd)/embed/frames}"

CHAFA_SIZE="${CHAFA_SIZE:-76x32}"
CHAFA_SYMBOLS="${CHAFA_SYMBOLS:-block,braille,extra}"
CHAFA_COLORS="${CHAFA_COLORS:-256}"

command -v ffmpeg >/dev/null || { echo "need ffmpeg" >&2; exit 1; }
command -v chafa >/dev/null || { echo "need chafa (brew install chafa)" >&2; exit 1; }
[[ -f "$GIF" ]] || { echo "not a file: $GIF" >&2; exit 1; }

mkdir -p "$OUT"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Higher-res source frames; rasterized to terminal cell grid.
ffmpeg -hide_banner -loglevel error -y -i "$GIF" -vf "fps=4,scale=720:-1" "$TMP/f_%04d.png"

n=0
shopt -s nullglob
for png in $(ls "$TMP"/f_*.png | LC_ALL=C sort); do
  # 256-color ANSI; preserve escapes (do not strip). Mono: add -c none and pipe through perl strip in a fork.
  chafa -f symbols \
    --symbols "$CHAFA_SYMBOLS" \
    --colors "$CHAFA_COLORS" \
    --size "$CHAFA_SIZE" \
    "$png" | perl -pe 's/\e\[\?25[hl]//g' > "$OUT/$(printf '%02d.txt' "$n")"
  n=$((n + 1))
done
shopt -u nullglob

echo "Wrote $n frames to $OUT (size=$CHAFA_SIZE symbols=$CHAFA_SYMBOLS colors=$CHAFA_COLORS)"
