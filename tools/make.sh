#!/bin/sh
# tools/make.sh <project> [draft|preview|final]  -> output/v<next>/final.mp4  (never overwrites)
set -e
set -o pipefail
cd "$(dirname "$0")/.."
export PATH="$PATH:/c/Users/mmoam/.local/bin"
proj="$1"; q="${2:-preview}"
n=1; while [ -d "output/v$n" ]; do n=$((n+1)); done
out="output/v$n"; mkdir -p "$out"
echo "[make] $proj @ $q -> $out"
/f/blender/blender.exe -b --python tools/build.py -- --project "$proj" --out "$out" --quality "$q" > "$out/render.log" 2>&1
grep "\[build\]" "$out/render.log"
cp "projects/$proj/cues.json" "$out/cues.json"
uv run --project F:/PoCs/video-builder/py python tools/audio.py --project "$proj" --out "$out" 2>&1 | grep -E "\[audio\]|Error|Traceback|rror:"
[ -f "$out/final.mp4" ] || { echo "[make] FAILED: no $out/final.mp4 (see output above)"; exit 1; }
echo "[make] done: $out/final.mp4"
