"""Narration + SFX + music mix, then mux onto the rendered video.

    uv run --project F:/PoCs/video-builder/py python tools/audio.py --project cupid --out output/v3

Reads projects/<project>/cues.json (written by the scene build) so audio timing always
matches the animation frames. Produces in --out:
    voice/<id>.wav   Kokoro narration (via video-builder's vb-audio)
    mix.wav          full 48 kHz mix
    final.mp4        video.mp4 + mix.wav
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VB_PY = "F:/PoCs/video-builder/py"
FFMPEG = ("C:/Users/mmoam/AppData/Local/Microsoft/WinGet/Packages/"
          "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin/ffmpeg.exe")
SR = 48000
SFX_DIR = os.path.join(ROOT, "assets", "sfx")
MUSIC_DIR = os.path.join(ROOT, "assets", "music")


# --------------------------------------------------------------------------- synth helpers

def _env(n: int, attack: float, decay: float) -> np.ndarray:
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t / decay)


def synth_twang() -> np.ndarray:
    n = int(SR * 0.45)
    t = np.arange(n) / SR
    f = 140 * np.exp(-t * 6) + 90
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, 0.12)
    tone += 0.35 * np.sin(2 * np.pi * np.cumsum(f * 2.02) / SR) * _env(n, 0.002, 0.08)
    noise = np.random.default_rng(1).normal(0, 1, n) * _env(n, 0.001, 0.02) * 0.4
    return 0.8 * (tone + noise)


def synth_bonk() -> np.ndarray:
    n = int(SR * 0.7)
    t = np.arange(n) / SR
    f = 420 * np.exp(-t * 18) + 160
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.001, 0.18)
    ring = sum(np.sin(2 * np.pi * (fr * t)) * _env(n, 0.001, 0.25) * g
               for fr, g in ((1230, 0.25), (1870, 0.15), (2740, 0.08)))
    return 0.9 * (body + ring)


def synth_step() -> np.ndarray:
    n = int(SR * 0.12)
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 1, n)
    # crude low-pass by moving average for a soft grass thump
    k = 24
    noise = np.convolve(noise, np.ones(k) / k, mode="same")
    return 1.6 * noise * _env(n, 0.002, 0.03)


def synth_boing() -> np.ndarray:
    n = int(SR * 0.5)
    t = np.arange(n) / SR
    f = 300 + 180 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 3) + 200 * np.exp(-t * 4)
    return 0.7 * np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.005, 0.2)


def synth_music(seconds: float, bpm: float = 118) -> np.ndarray:
    """A light plucked arpeggio loop (C  G  Am  F), stereo-safe mono."""
    beat = 60 / bpm
    step = beat / 2
    chords = [(261.63, 329.63, 392.0), (196.0, 246.94, 293.66), (220.0, 261.63, 329.63), (174.61, 220.0, 261.63)]
    n = int(SR * seconds)
    out = np.zeros(n)
    i, t0 = 0, 0.0
    while t0 < seconds:
        chord = chords[(i // 8) % 4]
        note = chord[[0, 1, 2, 1][i % 4]] * (2 if i % 8 in (5, 6) else 1)
        ln = int(SR * step * 1.6)
        s = int(t0 * SR)
        ln = min(ln, n - s)
        if ln <= 0:
            break
        t = np.arange(ln) / SR
        pluck = (np.sin(2 * np.pi * note * t) + 0.3 * np.sin(2 * np.pi * note * 2 * t)) * np.exp(-t * 7)
        out[s:s + ln] += pluck * 0.5
        if i % 8 == 0:  # soft bass on the bar
            bl = int(SR * beat * 1.5)
            bl = min(bl, n - s)
            tb = np.arange(bl) / SR
            out[s:s + bl] += np.sin(2 * np.pi * chord[0] / 2 * tb) * np.exp(-tb * 3) * 0.4
        i += 1
        t0 += step
    return out


SYNTH = {"twang": synth_twang, "bonk": synth_bonk, "step": synth_step, "boing": synth_boing}


# --------------------------------------------------------------------------- io

def load_wav(path: str) -> np.ndarray:
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    if sr != SR:
        x_old = np.linspace(0, 1, len(mono), endpoint=False)
        x_new = np.linspace(0, 1, int(len(mono) * SR / sr), endpoint=False)
        mono = np.interp(x_new, x_old, mono).astype(np.float32)
    return mono


def sfx_clip(name: str) -> np.ndarray:
    path = os.path.join(SFX_DIR, f"{name}.wav")
    if not os.path.exists(path):
        if name not in SYNTH:
            raise FileNotFoundError(f"no sfx '{name}' in assets/sfx and no synth for it")
        os.makedirs(SFX_DIR, exist_ok=True)
        sf.write(path, SYNTH[name]().astype(np.float32), SR)
    clip = load_wav(path)
    if name == "laugh":  # Bark clip is 6 s; keep ~2.4 s with a fade
        keep = int(SR * 2.4)
        clip = clip[:keep] * np.concatenate([np.ones(keep - SR // 2), np.linspace(1, 0, SR // 2)])[:len(clip[:keep])]
    return clip


def narrate(lines: list[dict], voice: str, out_dir: str) -> dict[str, np.ndarray]:
    os.makedirs(out_dir, exist_ok=True)
    req = {"voice": voice, "speed": 1.0,
           "scenes": [{"id": f"l{i}", "speech": l["text"], "pauseAfter": 0.0} for i, l in enumerate(lines)]}
    req_path = os.path.join(out_dir, "request.json")
    with open(req_path, "w", encoding="utf-8") as fh:
        json.dump(req, fh)
    align = os.path.join(out_dir, "align.json")
    subprocess.run(["uv", "run", "vb-audio", "synth", "--request", req_path, "--out-dir", out_dir, "--out", align],
                   cwd=VB_PY, check=True)
    return {f"l{i}": load_wav(os.path.join(out_dir, f"l{i}.wav")) for i in range(len(lines))}


def place(mix: np.ndarray, clip: np.ndarray, at_sec: float, gain: float) -> None:
    s = int(at_sec * SR)
    e = min(s + len(clip), len(mix))
    if e > s:
        mix[s:e] += clip[:e - s] * gain


# --------------------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-voice", action="store_true")
    ap.add_argument("--no-mux", action="store_true")
    args = ap.parse_args()

    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(ROOT, "projects", args.project, "cues.json"), encoding="utf-8") as fh:
        cues = json.load(fh)
    fps, frames = cues["fps"], cues["frames"]
    seconds = frames / fps
    mix = np.zeros(int(SR * seconds) + SR, dtype=np.float64)

    # music bed with tail fade
    music_path = os.path.join(MUSIC_DIR, f"{args.project}_loop.wav")
    if not os.path.exists(music_path):
        os.makedirs(MUSIC_DIR, exist_ok=True)
        sf.write(music_path, synth_music(seconds + 2).astype(np.float32), SR)
    music = load_wav(music_path)[:len(mix)]
    fade = np.ones(len(music))
    tail = int(SR * 2.5)
    fade[-tail:] = np.linspace(1, 0, tail)
    place(mix, music * fade, 0.0, cues["music"]["gain"])

    for c in cues["sfx"]:
        place(mix, sfx_clip(c["sfx"]), c["frame"] / fps, c.get("gain", 1.0) * 0.8)

    if not args.no_voice and cues["lines"]:
        voices = narrate(cues["lines"], cues["voice"], os.path.join(out, "voice"))
        for i, l in enumerate(cues["lines"]):
            place(mix, voices[f"l{i}"], l["frame"] / fps, 1.0)

    mix = mix[:int(SR * seconds)]
    peak = np.abs(mix).max() or 1.0
    mix = mix / peak * 0.89
    mix_path = os.path.join(out, "mix.wav")
    sf.write(mix_path, mix.astype(np.float32), SR)
    print(f"[audio] mix.wav {seconds:.1f}s, {len(cues['sfx'])} sfx, {len(cues['lines'])} lines", flush=True)

    if args.no_mux:
        return
    video = os.path.join(out, "video.mp4")
    final = os.path.join(out, "final.mp4")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", video, "-i", mix_path, "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", final], check=True)
    print(f"[audio] -> {final}", flush=True)


if __name__ == "__main__":
    main()
