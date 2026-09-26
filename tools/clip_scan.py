"""Scan a folder of game voice clips: which ones are TALKING (usable for a voice reference) and which are only sounds
(jumps, grunts, laughs, breaths). Writes <folder>/../clips_<name>.csv (file, seconds, loud95, kind, heard).

    cd F:/PoCs/video-builder/py-chatterbox && uv run python F:/PoCs/blender-video/tools/clip_scan.py <folder> <name>

Speech recognition = the wav2vec2 model our Chatterbox read-back uses (vb_chatterbox.align.transcribe, GPU).
Rule (checked by hand on Disney Infinity 3.0 Luke/Vader, 2026-09-26):
- The Sounds Resource packs name effort sounds with a dash (LUK0028-4.wav) and voice lines without (LUK0102.wav).
  The ASR turns grunts/laughs into syllables ("fa fa fa", "ha ha"), so a dash file is always "sound".
- A plain file is "talking" when the ASR heard >= 3 letters that are not only vowels/h ("a a a", "oh").
Pick reference clips from "talking" rows (calm lines for the dialogue ref, the loudest lines for the shout ref),
then build the reference with tools/make_ref.py.
"""
import csv, glob, os, re, sys

import numpy as np
import soundfile as sf
import torch
from vb_chatterbox.align import transcribe


def kind(file: str, heard: str) -> str:
    if "-" in os.path.splitext(file)[0]:
        return "sound"
    t = heard.replace(" ", "")
    return "talking" if len(t) >= 3 and not re.fullmatch(r"[ahoeu ]+", heard) else "sound"


def main() -> None:
    folder, name = sys.argv[1], sys.argv[2]
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    rows = []
    for f in sorted(glob.glob(os.path.join(folder, "*.wav"))):
        x, sr = sf.read(f, dtype="float32", always_2d=True)
        x = x.mean(1)
        d = len(x) / sr
        win = max(sr // 10, 1)
        e = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, mode="same")) if len(x) > win else np.abs(x)
        heard = transcribe(x, sr, dev) if d >= 0.25 else ""
        rows.append({"file": os.path.basename(f), "seconds": round(d, 2), "loud95": round(float(np.percentile(e, 95)), 3),
                     "kind": kind(f, heard), "heard": heard})
    out = os.path.join(os.path.dirname(os.path.normpath(folder)), f"clips_{name}.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "seconds", "loud95", "kind", "heard"])
        w.writeheader()
        w.writerows(rows)
    t = sum(r["kind"] == "talking" for r in rows)
    print(f"[clip_scan] {name}: {len(rows)} clips, {t} talking, {len(rows) - t} sounds -> {out}")


if __name__ == "__main__":
    main()
