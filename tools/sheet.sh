#!/bin/sh
# tools/sheet.sh <dir> <cols> -> <dir>/sheet.png  (tiles f_*.png in name order)
FF="/c/Users/mmoam/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin/ffmpeg.exe"
d="$1"; cols="${2:-4}"
(cd "$d" && ls | grep '^f_.*png$' | sed "s|^|file '|; s|$|'|" > list.txt)
n=$(wc -l < "$d/list.txt"); rows=$(( (n + cols - 1) / cols ))
(cd "$d" && "$FF" -y -loglevel error -f concat -safe 0 -i list.txt -vf "tile=${cols}x${rows}:padding=4:color=black" -frames:v 1 sheet.png) && echo "$d/sheet.png"
