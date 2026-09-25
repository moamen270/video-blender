"""Narration + SFX + music mix, then mux onto the rendered video.

    uv run --project F:/PoCs/video-builder/py python tools/audio.py --project cupid-had-one-job --out projects/cupid-had-one-job/output/v3

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
# Chatterbox is the default engine (owner decision 2026-09-24, ends the D13 trial); Kokoro only when a line or
# the casting sheet says engine: "kokoro" (generic voices such as machines/narrators).
DEFAULT_ENGINE = "chatterbox"
SFX_BANK_PATH = os.path.join(ROOT, "assets", "sfx_bank.json")
VOICE_RMS_DB = -16.0  # every line is normalised to this RMS (active samples) before mixing
with open(SFX_BANK_PATH, "r", encoding="utf-8") as _fh:
    BANK = json.load(_fh)

ALIASES = {
    "boom": "big_clash",
}

_SFX_CACHE: dict[str, np.ndarray] = {}


# --------------------------------------------------------------------------- io

def load_audio(path: str) -> np.ndarray:
    res = subprocess.run(
        [FFMPEG, "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
        capture_output=True,
        check=True,
    )
    return np.frombuffer(res.stdout, dtype=np.float32)


def load_wav(path: str) -> np.ndarray:
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    if sr != SR:
        x_old = np.linspace(0, 1, len(mono), endpoint=False)
        x_new = np.linspace(0, 1, int(len(mono) * SR / sr), endpoint=False)
        mono = np.interp(x_new, x_old, mono).astype(np.float32)
    return mono


def sfx_clip(name: str, occurrence: int = 0) -> np.ndarray:
    lookup_name = ALIASES.get(name, name)
    if lookup_name not in BANK["sounds"]:
        raise KeyError(f"sfx '{name}' is not in assets/sfx_bank.json (synthesis is disabled)")
    files = BANK["sounds"][lookup_name]["files"]
    rel_path = files[occurrence % len(files)]
    if rel_path in _SFX_CACHE:
        return _SFX_CACHE[rel_path]

    full_path = os.path.join(ROOT, rel_path)
    data = load_audio(full_path)

    above = np.where(np.abs(data) > 0.02)[0]
    if len(above) > 0:
        data = data[above[0]:]

    active = data[np.abs(data) > 0.01]
    if len(active) > 0:
        rms = np.sqrt(np.mean(active ** 2))
        if rms > 1e-9:
            target_rms = 10 ** (BANK.get("target_rms_db", -20) / 20)
            data = data * (target_rms / rms)

    peak = np.abs(data).max() if len(data) > 0 else 0.0
    if peak > 0.98:
        data = data * (0.98 / peak)

    _SFX_CACHE[rel_path] = data.astype(np.float32)
    return _SFX_CACHE[rel_path]


def narrate(lines: list[dict], voice: str, out_dir: str) -> dict[str, np.ndarray]:
    os.makedirs(out_dir, exist_ok=True)
    scenes = []
    ids = []
    for i, l in enumerate(lines):
        lid = l.get("id", f"l{i}")
        ids.append(lid)
        scenes.append({"id": lid, "speech": l["text"], "pauseAfter": 0.0})
    req = {"voice": voice, "speed": float(lines[0].get("speed", 1.0)) if lines else 1.0, "scenes": scenes}  # one speed per call
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

def trim_clip(clip: np.ndarray, dur: float, sr: int = SR) -> np.ndarray:
    """Cut clip to dur seconds with a 20 ms linear fade-out."""
    max_len = int(round(dur * sr))
    if len(clip) <= max_len:
        return clip
    trimmed = clip[:max_len].copy()
    fade_len = min(int(round(0.020 * sr)), len(trimmed))
    if fade_len > 0:
        trimmed[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)
    return trimmed


def build_caption_filters(
    captions: list[dict],
    fps: float | int,
    width: int,
    height: int,
) -> list[str]:
    """Build ffmpeg drawtext filters for caption overlays."""
    fontfile_str = r"C\:/Windows/Fonts/ariblk.ttf"
    size_px = round(72 * width / 1080)
    bw = max(1, round(5 * width / 1080))
    filters = []
    for c in captions:
        t = c.get("text", "")
        t = t.replace("\\", "\\\\")
        t = t.replace(":", r"\:")
        t = t.replace("'", "’")
        t = t.replace("%", r"\%")
        color = "#ffd400" if c.get("hi") else "white"
        t_start = round(c["start_frame"] / fps, 3)
        t_end = round(c["end_frame"] / fps, 3)
        filters.append(
            f"drawtext=fontfile='{fontfile_str}':text='{t}':fontsize={size_px}:fontcolor={color}:"
            f"borderw={bw}:bordercolor=black:x=(w-text_w)/2:y=0.70*h-text_h/2:enable='between(t,{t_start},{t_end})'"
        )
    return filters


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
            lid = l["id"]
            if "wav" in l:
                voices[lid] = load_wav(l["wav"])
                continue
            engine = l.get("engine", DEFAULT_ENGINE)
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

    # Same loudness for every character: TTS engines/references differ by ~8 dB (senior review of v7).
    voice_rms = 10 ** (VOICE_RMS_DB / 20)
    for lid, clip in voices.items():
        active = clip[np.abs(clip) > 0.01]
        if len(active) > 0:
            clip = clip * (voice_rms / max(np.sqrt(np.mean(active ** 2)), 1e-9))
            peak = np.abs(clip).max()
            voices[lid] = clip * (0.98 / peak) if peak > 0.98 else clip

    # Ducking
    duck = np.ones(len(mix))
    if voices:
        for l in lines:
            lid = l["id"]
            if lid in voices:
                clip = voices[lid]
                if "dur" in l:
                    clip = trim_clip(clip, float(l["dur"]))
                s = int(l["frame"] / fps * SR)
                e = min(len(mix), s + len(clip))
                if e > s:
                    duck[s:e] = 0.35
        k = int(0.03 * SR)
        duck = np.convolve(duck, np.ones(k) / k, mode="same")

    # Music bed
    music_cfg = cues.get("music") or {}
    music_file = music_cfg.get("file")
    music_gain = music_cfg.get("gain", 1.0)
    if music_file and not os.path.exists(music_file):
        for candidate in (
            os.path.join(ROOT, music_file),
            os.path.join(ROOT, "projects", args.project, music_file),
        ):
            if os.path.exists(candidate):
                music_file = candidate
                break
    if not music_cfg:
        music_file = None                                # a cue sheet without "music" = no music bed
    elif not music_file or not os.path.exists(music_file):
        raise FileNotFoundError("music file not found (synthesis is disabled)")

    raw_music = load_audio(music_file) if music_file else np.zeros(SR, dtype=np.float32)
    start_s = music_cfg.get("start_s", 0)
    if start_s and start_s > 0:
        raw_music = raw_music[int(start_s * SR):]

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

    place(mix, music_clip * env * duck, 0.0, music_gain)

    # SFX
    sfx_counts: dict[str, int] = collections.defaultdict(int)
    files_used: set[str] = set()
    for c in cues.get("sfx", []):
        raw_name = c["sfx"]
        sound_name = ALIASES.get(raw_name, raw_name)
        if sound_name not in BANK["sounds"]:
            raise KeyError(f"sfx '{raw_name}' is not in assets/sfx_bank.json (synthesis is disabled)")
        entry = BANK["sounds"][sound_name]
        files = entry["files"]
        occ = sfx_counts[sound_name]
        sfx_counts[sound_name] += 1
        files_used.add(files[occ % len(files)])

        entry_gain = entry.get("gain", 1.0)
        cue_gain = c.get("gain", 1.0)
        placement_gain = entry_gain * cue_gain

        clip = sfx_clip(raw_name, occ)
        if "dur" in c:                                   # long beds (hiss, rumble) cut to the beat they cover
            clip = trim_clip(clip, float(c["dur"]))
        place(mix, clip, c["frame"] / fps, placement_gain)

    print(f"[audio] sfx bank: {len(BANK['sounds'])} sounds, {len(files_used)} files used", flush=True)

    # Voices
    for l in lines:
        lid = l["id"]
        if lid in voices:
            clip = voices[lid]
            if "dur" in l:
                clip = trim_clip(clip, float(l["dur"]))
            place(mix, clip, l["frame"] / fps, 1.0)

    mix = mix[:int(SR * seconds)]
    peak = np.abs(mix).max() or 1.0
    mix = mix / peak * 0.89
    mix_path = os.path.join(out, "mix.wav")
    sf.write(mix_path, mix.astype(np.float32), SR)

    overlays = cues.get("overlays", [])
    captions = cues.get("captions", [])
    if engines_used:
        eng_str = ", ".join(sorted(engines_used))
    elif lines:
        eng_str = ", ".join(sorted({l.get("engine", DEFAULT_ENGINE) for l in lines}))
    else:
        eng_str = "none"
    print(f"[audio] mix.wav {seconds:.1f}s, {len(cues.get('sfx', []))} sfx, {len(lines)} lines ({eng_str}), {len(overlays)} overlays", flush=True)

    if args.no_mux:
        return
    video = os.path.join(out, "video.mp4")
    final = os.path.join(out, "final.mp4")

    grade = cues.get("grade")  # optional ffmpeg colour-grade filter chain, applied before overlays/captions
    if not overlays and not captions and not grade:
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", video, "-i", mix_path, "-c:v", "copy",
                        "-af", "loudnorm=I=-14:TP=-1:LRA=11",   # same target as the overlay branch
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                        "-shortest", "-movflags", "+faststart", final], check=True)
    else:
        FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")
        res_h = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                                "stream=height", "-of", "csv=p=0", video],
                               capture_output=True, text=True, check=True)
        H = int(res_h.stdout.strip())
        res_w = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                                "stream=width", "-of", "csv=p=0", video],
                               capture_output=True, text=True, check=True)
        W = int(res_w.stdout.strip())
        filters = [grade] if grade else []
        for o in overlays:
            kind = o.get("kind")
            a = o["from"] - 1
            b = o["to"] - 1
            if kind == "fill":
                color = o["color"]
                filters.append(f"drawbox=x=0:y=0:w=iw:h=ih:color={color}@1:t=fill:enable='between(n,{a},{b})'")
            elif kind == "box":                          # rectangle in frame fractions (HUD bars, panels)
                bx, by, bw_, bh = (o[k] for k in ("x", "y", "w", "h"))
                t = "fill" if o.get("fill", True) else str(max(2, round(o.get("border", 4) * H / 1920)))
                filters.append(f"drawbox=x=iw*{bx}:y=ih*{by}:w=iw*{bw_}:h=ih*{bh}:color={o['color']}@{o.get('alpha', 1)}:"
                               f"t={t}:enable='between(n,{a},{b})'")
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
        if captions:
            filters.extend(build_caption_filters(captions, fps, W, H))
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
