"""Build a Chatterbox voice reference from chosen game clips: concatenate them (0.25 s gaps), save <out>_orig.wav,
(mono 24 kHz, loudnorm -20 LUFS: skill voice-casting), then the MODIFIED reference <out>.wav (rubberband pitch, formant shifted: owner voice policy, a clone is never the
original voice). References live in assets/library/voices_ref/ (git-ignored: never commit them).

    python tools/make_ref.py <clip folder> <out name> --pitch 0.95 --clips VDR0127,VDR0191,...

Choose the clips from tools/clip_scan.py output ("talking" rows only): calm lines for <char>_ref, the loudest
emotional lines for <char>_shout_ref. Aim for 12-18 s. Record the clip list in assets/cast/voices.json notes.
"""
import argparse, os, subprocess

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(ROOT, "assets", "library", "voices_ref")
SR = 24000


def load(path: str) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder"); ap.add_argument("name")
    ap.add_argument("--clips", required=True); ap.add_argument("--pitch", type=float, required=True)
    a = ap.parse_args()
    gap = np.zeros(int(0.25 * SR), np.float32)
    parts = []
    for c in a.clips.split(","):
        c = c.strip()
        parts += [load(os.path.join(a.folder, c if c.endswith(".wav") else c + ".wav")), gap]
    x = np.concatenate(parts[:-1])
    orig = os.path.join(REFS, f"{a.name}_orig.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", "loudnorm=I=-20:TP=-2", "-ar", str(SR), orig],
                   input=x.tobytes(), check=True)
    out = os.path.join(REFS, f"{a.name}.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", orig, "-af", f"rubberband=pitch={a.pitch}:formant=shifted,loudnorm=I=-20:TP=-2", "-ar", str(SR), out],
                   check=True)
    print(f"[make_ref] {a.name}: {len(x) / SR:.1f} s from {len(parts) // 2} clips, pitch {a.pitch} -> {out}")


if __name__ == "__main__":
    main()
