#!/bin/sh
# tools/make.sh <project> [draft|preview|final]
#   -> projects/<project>/output/v<next>/final.mp4 (+ social.md for every platform); never overwrites
set -e
set -o pipefail
cd "$(dirname "$0")/.."
export PATH="$PATH:/c/Users/mmoam/.local/bin"
proj="$1"; q="${2:-preview}"
base="projects/$proj/output"; mkdir -p "$base"
# next version = highest existing vN in this project + 1 (older renders kept their global numbers)
last=$(ls "$base" 2>/dev/null | sed -n 's/^v\([0-9][0-9]*\)$/\1/p' | sort -n | tail -1)
n=$(( ${last:-0} + 1 ))
out="$base/v$n"; mkdir -p "$out"
echo "[make] $proj @ $q -> $out"
/f/blender/blender.exe -b --python tools/build.py -- --project "$proj" --out "$out" --quality "$q" > "$out/render.log" 2>&1
grep "\[build\]" "$out/render.log"
cp "projects/$proj/cues.json" "$out/cues.json"
uv run --project F:/PoCs/video-builder/py python tools/audio.py --project "$proj" --out "$out" 2>&1 | grep -E "\[audio\]|Error|Traceback|rror:"
[ -f "$out/final.mp4" ] || { echo "[make] FAILED: no $out/final.mp4 (see output above)"; exit 1; }
sh tools/sheet4hz.sh "$out/final.mp4" "$out/sheet_4hz.png"
python tools/social.py "$proj" --version "$n" || echo "[make] WARNING: social.md not written (see above)"
echo "[make] done: $out/final.mp4"
