#!/bin/sh
# tools/sheet4hz.sh <video.mp4> [out.png]  -> the WHOLE video at 4 frames per second in one image
# (owner rule 2026-09-24: every render keeps this sheet). 16 columns, each tile 135x240 with its timestamp.
# Never overwrites: exits if the output already exists.
FF="/c/Users/mmoam/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin/ffmpeg.exe"
FP="/c/Users/mmoam/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin/ffprobe.exe"
v="$1"; out="${2:-$(dirname "$v")/sheet_4hz.png}"
[ -f "$v" ] || { echo "[sheet4hz] no video: $v"; exit 1; }
[ -f "$out" ] && { echo "[sheet4hz] exists, kept: $out"; exit 0; }
dur=$("$FP" -v error -show_entries format=duration -of csv=p=0 "$v")
n=$(awk -v d="$dur" 'BEGIN { printf "%d", d * 4 + 0.999 }')
cols=16; rows=$(( (n + cols - 1) / cols ))
"$FF" -y -loglevel error -i "$v" -vf "fps=4,scale=135:240,drawtext=fontfile='C\:/Windows/Fonts/arialbd.ttf':text='%{pts\:hms}':x=4:y=4:fontsize=13:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=2,tile=${cols}x${rows}:padding=2:color=black" -frames:v 1 "$out" \
  && echo "[sheet4hz] $out ($n frames, ${cols}x${rows})"
