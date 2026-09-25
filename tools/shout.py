"""Build shouted special-move calls from voiced takes (Chatterbox cannot hold a vowel or say a
made-up word on its own): trim a word out of a carrier phrase, split it at the stop consonant
("Hadou|ken" at the silent 'k' closure), time-stretch the first part with a rising pitch, glue a
"KEN!" onto it, and write Rhubarb lip-sync cues for every result.

    uv run --project F:/PoCs/video-builder/py python tools/shout.py --project ryu-vs-ken-last-hadouken

Reads projects/<p>/shouts.json:
  {"id": {"src": "<line id>", "word": "Hadouken!",            # word to cut from the take
          "hold": 2.6, "rise": 1.12, "crack": false,          # optional: stretch the part before the split
          "tail_src": "<line id>", "tail_word": "Ken!",       # optional: a separate release word
          "gain_db": 0}}
Writes projects/<p>/voice/derived/<id>.wav and projects/<p>/voice/derived.json
({id: {wav, seconds, cues}}).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile

import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RHUBARB = "F:/PoCs/tools/Rhubarb-Lip-Sync-1.14.0-Windows/rhubarb.exe"
SR = 24000


def load(path: str) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def ff(x: np.ndarray, af: str) -> np.ndarray:
    """Run an ffmpeg audio filter over a clip."""
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        sf.write(a, x, SR)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af", af, "-ar", str(SR), b], check=True)
        return sf.read(b, dtype="float32")[0]


def word_span(entry: dict, word: str) -> tuple[float, float]:
    ws = [w for w in entry["words"] if w["w"].strip(",.!?").lower() == word.strip(",.!?").lower()]
    if not ws:
        raise SystemExit(f"word {word!r} not in {[w['w'] for w in entry['words']]}")
    return ws[-1]["start"], ws[-1]["end"]


def cut(x: np.ndarray, a: float, b: float, pad: float = 0.04) -> np.ndarray:
    return x[max(0, int((a - pad) * SR)):min(len(x), int((b + pad) * SR))]


def split_at_stop(x: np.ndarray, lo: float = 0.40, hi: float = 0.85) -> int:
    """Index of the quietest 20 ms window between lo..hi of the clip (the closure before a stop)."""
    win = int(0.02 * SR)
    a, b = int(len(x) * lo), int(len(x) * hi)
    rms = [np.sqrt(np.mean(x[i:i + win] ** 2)) for i in range(a, b - win, win // 2)]
    return a + int(np.argmin(rms)) * (win // 2) + win // 2


def fade(x: np.ndarray, ms: float = 12) -> np.ndarray:
    n = min(len(x) // 2, int(ms / 1000 * SR))
    y = x.copy()
    y[:n] *= np.linspace(0, 1, n)
    y[-n:] *= np.linspace(1, 0, n)
    return y


def stretch_rise(x: np.ndarray, hold: float, rise: float, crack: bool) -> np.ndarray:
    """Stretch to `hold` seconds, pitch climbing from 1.0 to `rise` over 4 crossfaded chunks."""
    tempo = len(x) / SR / hold
    long = ff(x, f"rubberband=tempo={tempo:.4f}:formant=preserved")
    chunks = np.array_split(long, 4)
    out = None
    for i, c in enumerate(chunks):
        p = 1.0 + (rise - 1.0) * i / 3
        c = ff(c, f"rubberband=pitch={p:.4f}:formant=preserved")
        if crack and i == 3:
            c = ff(c, "vibrato=f=7:d=0.35")
        out = c if out is None else crossfade(out, c, 0.03)
    return out


def crossfade(a: np.ndarray, b: np.ndarray, sec: float) -> np.ndarray:
    n = min(int(sec * SR), len(a), len(b))
    return np.concatenate([a[:-n], a[-n:] * np.linspace(1, 0, n) + b[:n] * np.linspace(0, 1, n), b[n:]])


def rhubarb(wav: str, text: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as d:
        t, o = os.path.join(d, "t.txt"), os.path.join(d, "o.json")
        open(t, "w", encoding="utf-8").write(text)
        subprocess.run([RHUBARB, "-f", "json", "-o", o, "--dialogFile", t, "--extendedShapes", "GHX", wav],
                       check=True, capture_output=True)
        return json.load(open(o, encoding="utf-8"))["mouthCues"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    pdir = os.path.join(ROOT, "projects", args.project)
    spec = json.load(open(os.path.join(pdir, "shouts.json"), encoding="utf-8"))
    man = json.load(open(os.path.join(pdir, "voice", "manifest.json"), encoding="utf-8"))["lines"]
    out_dir = os.path.join(pdir, "voice", "derived")
    os.makedirs(out_dir, exist_ok=True)
    res = {}
    for sid, s in spec.items():
        src = man[s["src"]]
        a, b = word_span(src, s["word"])
        word = cut(load(src["wav"]), a, b)
        text = s.get("text", s["word"])
        if "hold" in s:
            k = split_at_stop(word)
            head = stretch_rise(word[:k], s["hold"], s.get("rise", 1.1), s.get("crack", False))
            if "tail_src" in s:
                t_src = man[s["tail_src"]]
                ta, tb = word_span(t_src, s["tail_word"])
                tail = cut(load(t_src["wav"]), ta, tb)
                if s.get("tail_split"):                      # take only the part after the stop
                    tail = tail[split_at_stop(tail):]
            else:
                tail = word[k:]
            tail = ff(tail, f"volume={s.get('tail_gain_db', 3)}dB")
            y = np.concatenate([fade(head), np.zeros(int(0.03 * SR), np.float32), fade(tail)])
        else:
            y = fade(word)
        if s.get("gain_db"):
            y = ff(y, f"volume={s['gain_db']}dB")
        y = y / max(1e-6, float(np.max(np.abs(y)))) * 0.95
        path = os.path.join(out_dir, f"{sid}.wav")
        sf.write(path, y.astype(np.float32), SR)
        res[sid] = {"wav": path.replace("\\", "/"), "seconds": round(len(y) / SR, 2), "cues": rhubarb(path, text)}
        print(f"[shout] {sid}: {res[sid]['seconds']} s, {len(res[sid]['cues'])} cues", flush=True)
    json.dump(res, open(os.path.join(pdir, "voice", "derived.json"), "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
