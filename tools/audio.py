"""Narration + SFX + music mix, then mux onto the rendered video.

    uv run --project F:/PoCs/video-builder/py python tools/audio.py --project cupid --out output/v3

Reads projects/<project>/cues.json (written by the scene build) so audio timing always
matches the animation frames. Produces in --out:
    voice/<id>.wav   narration
    mix.wav          full 48 kHz mix
    final.mp4        video.mp4 + mix.wav
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VB_PY = "F:/PoCs/video-builder/py"
VB_CHATTERBOX_PY = "F:/PoCs/video-builder/py-chatterbox"
FFMPEG = ("C:/Users/mmoam/AppData/Local/Microsoft/WinGet/Packages/"
          "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin/ffmpeg.exe")
SR = 48000
SFX_DIR = os.path.join(ROOT, "assets", "sfx")
VB_SFX_DIR = "F:/PoCs/video-builder/assets/sfx"
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
        vb_path = os.path.join(VB_SFX_DIR, f"{name}.wav")
        if os.path.exists(vb_path):
            path = vb_path
        else:
            if name not in SYNTH:
                raise FileNotFoundError(f"no sfx '{name}' in assets/sfx or {VB_SFX_DIR} and no synth for it")
            os.makedirs(SFX_DIR, exist_ok=True)
            sf.write(path, SYNTH[name]().astype(np.float32), SR)
    clip = load_wav(path)
    if name == "laugh":  # Bark clip is 6 s; keep ~2.4 s with a fade
        keep = int(SR * 2.4)
        clip = clip[:keep] * np.concatenate([np.ones(keep - SR // 2), np.linspace(1, 0, SR // 2)])[:len(clip[:keep])]
    return clip


def narrate(lines: list[dict], voice: str, out_dir: str) -> dict[str, np.ndarray]:
    os.makedirs(out_dir, exist_ok=True)
    scenes = []
    ids = []
    for i, l in enumerate(lines):
        lid = l.get("id", f"l{i}")
        ids.append(lid)
        scenes.append({"id": lid, "speech": l["text"], "pauseAfter": 0.0})
    req = {"voice": voice, "speed": 1.0, "scenes": scenes}
    req_path = os.path.join(out_dir, "request.json")
    with open(req_path, "w", encoding="utf-8") as fh:
        json.dump(req, fh)
    align = os.path.join(out_dir, "align.json")
    subprocess.run(["uv", "run", "vb-audio", "synth", "--request", req_path, "--out-dir", out_dir, "--out", align],
                   cwd=VB_PY, check=True)
    return {lid: load_wav(os.path.join(out_dir, f"{lid}.wav")) for lid in ids}


def chatterbox(lines: list[dict], out_dir: str) -> dict[str, np.ndarray]:
    os.makedirs(out_dir, exist_ok=True)
    scenes = []
    ids = []
    for i, l in enumerate(lines):
        lid = l.get("id", f"l{i}")
        ids.append(lid)
        scenes.append({
            "id": lid,
            "speech": l["text"],
            "pauseAfter": float(l.get("pauseAfter", 0.0)),
            "speed": float(l.get("speed", 1.0)),
            "voiceRef": l.get("voiceRef", None),
            "emotion": float(l.get("emotion", 0.5)),
            "seed": int(l.get("seed", 0)),
        })
    req = {"scenes": scenes}
    req_path = os.path.join(out_dir, "request.json")
    with open(req_path, "w", encoding="utf-8") as fh:
        json.dump(req, fh)
    res_path = os.path.join(out_dir, "chatterbox.json")
    subprocess.run(
        ["uv", "run", "vb-chatterbox", "synth", "--request", req_path, "--out-dir", out_dir, "--out", res_path],
        cwd=VB_CHATTERBOX_PY,
        check=True,
    )
    return {lid: load_wav(os.path.join(out_dir, f"{lid}.wav")) for lid in ids}


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

    lines = cues.get("lines", [])
    for i, l in enumerate(lines):
        if "id" not in l:
            l["id"] = f"l{i}"

    voices: dict[str, np.ndarray] = {}
    engines_used: set[str] = set()

    if not args.no_voice and lines:
        kokoro_by_voice: dict[str, list[dict]] = collections.defaultdict(list)
        chatterbox_lines: list[dict] = []
        for l in lines:
            engine = l.get("engine", "kokoro")
            engines_used.add(engine)
            if engine == "chatterbox":
                chatterbox_lines.append(l)
            else:
                voice = l.get("voice", cues.get("voice", "bm_george"))
                kokoro_by_voice[voice].append(l)

        for voice, v_lines in kokoro_by_voice.items():
            v_out = os.path.join(out, "voice", voice)
            voices.update(narrate(v_lines, voice, v_out))

        if chatterbox_lines:
            cb_out = os.path.join(out, "voice", "chatterbox")
            voices.update(chatterbox(chatterbox_lines, cb_out))

    # Ducking
    duck = np.ones(len(mix))
    if voices:
        for l in lines:
            lid = l["id"]
            if lid in voices:
                clip = voices[lid]
                s = int(l["frame"] / fps * SR)
                e = min(len(mix), s + len(clip))
                if e > s:
                    duck[s:e] = 0.35
        k = int(0.03 * SR)
        duck = np.convolve(duck, np.ones(k) / k, mode="same")

    # Music bed
    music_cfg = cues.get("music", {})
    music_file = music_cfg.get("file")
    music_gain = music_cfg.get("gain", 1.0)

    if music_file and os.path.exists(music_file):
        raw_music = load_wav(music_file)
        tiles = math.ceil(len(mix) / len(raw_music)) if len(raw_music) > 0 else 1
        music_clip = np.tile(raw_music, tiles)[:len(mix)]
        env = np.ones(len(mix), dtype=np.float64)

        cut = music_cfg.get("cut_frame")
        if cut is not None and cut > 0:
            c = int(cut / fps * SR)
            ramp = int(6 / fps * SR)
            c_start = max(0, c - ramp)
            ramp_len = c - c_start
            if ramp_len > 0:
                env[c_start:c] = np.linspace(1, 0, ramp)[-ramp_len:]
            env[c:] = 0.0

            resume = music_cfg.get("resume_frame", 0)
            if resume > cut:
                r = int(resume / fps * SR)
                r_end = min(len(mix), r + ramp)
                ramp_r_len = r_end - r
                if ramp_r_len > 0:
                    env[r:r_end] = np.linspace(0, 1, ramp)[:ramp_r_len]
                if r + ramp < len(mix):
                    env[r + ramp:] = 1.0

        end = music_cfg.get("end_frame")
        if end is not None and end > 0:
            e = int(end / fps * SR)
            e = min(e, len(mix))
            e_start = max(0, e - SR)
            if e > e_start:
                env[e_start:e] *= np.linspace(1, 0, e - e_start)
            if e < len(mix):
                env[e:] = 0.0
    else:
        music_path = os.path.join(MUSIC_DIR, f"{args.project}_loop.wav")
        if not os.path.exists(music_path):
            os.makedirs(MUSIC_DIR, exist_ok=True)
            sf.write(music_path, synth_music(seconds + 2).astype(np.float32), SR)
        raw_music = load_wav(music_path)
        tiles = math.ceil(len(mix) / len(raw_music)) if len(raw_music) > 0 else 1
        music_clip = np.tile(raw_music, tiles)[:len(mix)]
        env = np.ones(len(mix), dtype=np.float64)
        tail = int(SR * 2.5)
        tail = min(tail, len(env))
        if tail > 0:
            env[-tail:] = np.linspace(1, 0, tail)

    place(mix, music_clip * env * duck, 0.0, music_gain)

    # SFX
    for c in cues.get("sfx", []):
        place(mix, sfx_clip(c["sfx"]), c["frame"] / fps, c.get("gain", 1.0) * 0.8)

    # Voices
    for l in lines:
        lid = l["id"]
        if lid in voices:
            place(mix, voices[lid], l["frame"] / fps, 1.0)

    mix = mix[:int(SR * seconds)]
    peak = np.abs(mix).max() or 1.0
    mix = mix / peak * 0.89
    mix_path = os.path.join(out, "mix.wav")
    sf.write(mix_path, mix.astype(np.float32), SR)

    overlays = cues.get("overlays", [])
    if engines_used:
        eng_str = ", ".join(sorted(engines_used))
    elif lines:
        eng_str = ", ".join(sorted({l.get("engine", "kokoro") for l in lines}))
    else:
        eng_str = "none"
    print(f"[audio] mix.wav {seconds:.1f}s, {len(cues.get('sfx', []))} sfx, {len(lines)} lines ({eng_str}), {len(overlays)} overlays", flush=True)

    if args.no_mux:
        return
    video = os.path.join(out, "video.mp4")
    final = os.path.join(out, "final.mp4")

    if not overlays:
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", video, "-i", mix_path, "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", final], check=True)
    else:
        FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")
        res = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                              "stream=height", "-of", "csv=p=0", video],
                             capture_output=True, text=True, check=True)
        H = int(res.stdout.strip())
        filters = []
        for o in overlays:
            kind = o.get("kind")
            a = o["from"] - 1
            b = o["to"] - 1
            if kind == "fill":
                color = o["color"]
                filters.append(f"drawbox=x=0:y=0:w=iw:h=ih:color={color}@1:t=fill:enable='between(n,{a},{b})'")
            elif kind == "text":
                t = o["text"]
                t = t.replace("\\", "\\\\")
                t = t.replace(":", r"\:")
                t = t.replace("'", "’")
                t = t.replace("%", r"\%")
                size_px = round(o["size"] * H / 1920)
                bw = max(2, round(6 * H / 1920))
                alpha = o.get("alpha", 1)
                y = o["y"]
                fontfile_str = r"C\:/Windows/Fonts/ariblk.ttf"
                filters.append(
                    f"drawtext=fontfile='{fontfile_str}':text='{t}':fontsize={size_px}:fontcolor=white@{alpha}:"
                    f"borderw={bw}:bordercolor=black:x=(w-text_w)/2:y=h*{y}-text_h/2:enable='between(n,{a},{b})'"
                )
        script = os.path.join(out, "overlays.txt")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(",".join(filters))
        subprocess.run([
            FFMPEG, "-y", "-loglevel", "error", "-i", video, "-i", mix_path,
            "-/vf", script,
            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
            "-af", "loudnorm=I=-14:TP=-1:LRA=11",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-shortest", "-movflags", "+faststart", final
        ], check=True)

    print(f"[audio] -> {final}", flush=True)


if __name__ == "__main__":
    main()
