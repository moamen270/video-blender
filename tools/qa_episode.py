"""QA check for a rendered episode: hook, dead time, and length.

Usage:
    python tools/qa_episode.py --out output/vN [--report <path>]
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

FFMPEG = (
    "C:/Users/mmoam/AppData/Local/Microsoft/WinGet/Packages/"
    "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin/ffmpeg.exe"
)
if not os.path.exists(FFMPEG):
    FFMPEG = "ffmpeg"


def decode_frames_gray(video_path: str, width: int = 90, height: int = 160) -> np.ndarray:
    """Decode video to 90x160 grayscale raw frames with ffmpeg."""
    cmd = [
        FFMPEG,
        "-v", "error",
        "-i", video_path,
        "-vf", f"scale={width}:{height},format=gray",
        "-f", "rawvideo",
        "-",
    ]
    res = subprocess.run(cmd, capture_output=True, check=True)
    raw = res.stdout
    frame_bytes = width * height
    total_frames = len(raw) // frame_bytes
    if total_frames == 0:
        return np.zeros((0, height, width), dtype=np.uint8)
    return np.frombuffer(raw[:total_frames * frame_bytes], dtype=np.uint8).reshape((total_frames, height, width))


def compute_motion(frames: np.ndarray) -> np.ndarray:
    """Compute motion per frame: mean |frame f - frame f-1| (1-indexed, motion[1]=motion[2])."""
    num_frames = len(frames)
    motion = np.zeros(num_frames + 1, dtype=np.float32)
    if num_frames < 2:
        return motion
    frames_f = frames.astype(np.float32)
    diff = np.abs(frames_f[1:] - frames_f[:-1])
    motion_per_frame = np.mean(diff, axis=(1, 2))
    motion[2:] = motion_per_frame
    motion[1] = motion[2]
    return motion


def compute_audio_rms(mix_path: str, total_frames: int, fps: int = 24) -> tuple[np.ndarray, float]:
    """Compute audio RMS in dBFS per video frame window and RMS over the first 0.3 s."""
    data, sr = sf.read(mix_path, dtype="float32", always_2d=True)
    mono = data.mean(axis=1).astype(np.float64)

    # Audio RMS over first 0.3 s
    samples_03 = int(round(0.3 * sr))
    chunk_03 = mono[:samples_03]
    if len(chunk_03) > 0:
        rms_03 = float(np.sqrt(np.mean(chunk_03 ** 2)))
        dbfs_03 = 20.0 * math.log10(rms_03) if rms_03 > 1e-9 else -120.0
    else:
        dbfs_03 = -120.0

    # Audio RMS per frame (1/fps s window)
    audio_rms = np.full(total_frames + 1, -120.0, dtype=np.float32)
    for f in range(1, total_frames + 1):
        s_start = int(round((f - 1) * sr / fps))
        s_end = int(round(f * sr / fps))
        chunk = mono[s_start:s_end]
        if len(chunk) > 0:
            rms_f = float(np.sqrt(np.mean(chunk ** 2)))
            audio_rms[f] = 20.0 * math.log10(rms_f) if rms_f > 1e-9 else -120.0

    return audio_rms, dbfs_03


def in_beats(frame_idx: int, beats: list) -> bool:
    """Check if frame_idx falls within any cues['beats'] range [a, b]."""
    for b in beats:
        if isinstance(b, (list, tuple)) and len(b) >= 2:
            try:
                a, b_end = float(b[0]), float(b[1])
                if a <= frame_idx <= b_end:
                    return True
            except (ValueError, TypeError):
                continue
        elif isinstance(b, dict):
            a = b.get("from", b.get("start", b.get("start_frame", b.get("a"))))
            b_end = b.get("to", b.get("end", b.get("end_frame", b.get("b"))))
            if a is not None and b_end is not None:
                try:
                    if float(a) <= frame_idx <= float(b_end):
                        return True
                except (ValueError, TypeError):
                    continue
    return False


def main() -> None:
    argv = sys.argv[1:]
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]

    ap = argparse.ArgumentParser(description="QA check for rendered episode")
    ap.add_argument("--out", required=True, help="Rendered output folder (e.g. output/vN)")
    ap.add_argument("--report", default=None, help="Report JSON path (default: <out>/qa.json)")
    args = ap.parse_args(argv)

    out_dir = os.path.abspath(args.out)
    if not os.path.isdir(out_dir):
        raise FileNotFoundError(f"Output directory not found: {out_dir}")

    report_path = os.path.abspath(args.report) if args.report else os.path.join(out_dir, "qa.json")

    video_path = os.path.join(out_dir, "final.mp4")
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    mix_path = os.path.join(out_dir, "mix.wav")
    if not os.path.isfile(mix_path):
        raise FileNotFoundError(f"Audio mix file not found: {mix_path}")

    cues_path = os.path.join(out_dir, "cues.json")
    cues = {}
    if os.path.isfile(cues_path):
        with open(cues_path, "r", encoding="utf-8") as fh:
            cues = json.load(fh)

    fps = int(cues.get("fps", 24))
    if fps <= 0:
        fps = 24

    beats = cues.get("beats") or []
    captions = cues.get("captions") or []
    overlays = cues.get("overlays") or []

    # 1. Decode video frames & compute motion
    frames = decode_frames_gray(video_path, width=90, height=160)
    total_frames = len(frames)
    if total_frames == 0:
        raise RuntimeError(f"Could not decode any frames from {video_path}")

    motion = compute_motion(frames)

    # 2. Audio RMS per frame & first 0.3 s
    audio_rms, hook_audio_dbfs = compute_audio_rms(mix_path, total_frames, fps=fps)

    # 3. Hook check:
    # - max motion over frames 2-12 > 1.0
    hook_motion_frames = motion[2 : min(13, total_frames + 1)]
    max_motion_2_12 = float(np.max(hook_motion_frames)) if len(hook_motion_frames) > 0 else 0.0
    motion_pass = max_motion_2_12 > 1.0

    # - audio RMS over the first 0.3 s > -40 dBFS
    audio_pass = hook_audio_dbfs > -40.0

    # - an overlay or caption starts at frame <= 3
    text_frames = []
    for item in list(overlays) + list(captions):
        if not isinstance(item, dict):
            continue
        f_start = None
        for key in ("from", "start_frame", "frame", "start"):
            if key in item and item[key] is not None:
                f_start = item[key]
                break
        if f_start is not None:
            try:
                text_frames.append(int(round(float(f_start))))
            except (ValueError, TypeError):
                pass

    first_text_frame = min(text_frames) if text_frames else None
    text_pass = (first_text_frame is not None) and (first_text_frame <= 3)

    hook_pass = bool(motion_pass and audio_pass and text_pass)

    # 4. Dead time check: windows of >= 12 consecutive frames with motion < 0.4 and RMS < -45 dBFS,
    # excluding frames inside cues["beats"] ranges [a, b]
    dead_windows: list[list[int]] = []
    run_start = None

    for f in range(1, total_frames + 1):
        is_dead = (motion[f] < 0.4) and (audio_rms[f] < -45.0) and not in_beats(f, beats)
        if is_dead:
            if run_start is None:
                run_start = f
        else:
            if run_start is not None:
                if (f - run_start) >= 12:
                    dead_windows.append([run_start, f - 1])
                run_start = None

    if run_start is not None:
        if (total_frames + 1 - run_start) >= 12:
            dead_windows.append([run_start, total_frames])

    dead_time_pass = (len(dead_windows) == 0)

    # 5. Length check: 25-40 s
    duration_s = total_frames / fps
    length_pass = bool(25.0 <= duration_s <= 40.0)

    # Overall pass
    overall_pass = bool(hook_pass and dead_time_pass and length_pass)

    report_data = {
        "hook": {
            "pass": bool(hook_pass),
            "motion_max": round(float(max_motion_2_12), 3),
            "motion_pass": bool(motion_pass),
            "audio_rms_dbfs": round(float(hook_audio_dbfs), 1),
            "audio_pass": bool(audio_pass),
            "first_text_frame": first_text_frame,
            "text_pass": bool(text_pass),
        },
        "dead_time": dead_windows,
        "length": round(float(duration_s), 2),
        "pass": bool(overall_pass),
    }

    report_dir = os.path.dirname(report_path)
    if report_dir:
        os.makedirs(report_dir, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report_data, fh, indent=2)

    hook_status = "PASS" if hook_pass else "FAIL"
    dt_status = "PASS" if dead_time_pass else "FAIL"
    len_status = "PASS" if length_pass else "FAIL"
    overall_status = "PASS" if overall_pass else "FAIL"

    text_str = f"frame {first_text_frame}" if first_text_frame is not None else "none"
    print(f"[qa] hook {hook_status} (motion={max_motion_2_12:.2f}, audio={hook_audio_dbfs:.1f} dBFS, text={text_str})", flush=True)

    dt_detail = f"{len(dead_windows)} windows"
    if dead_windows:
        dt_detail += f": {dead_windows}"
    print(f"[qa] dead_time {dt_status} ({dt_detail})", flush=True)

    print(f"[qa] length {len_status} ({duration_s:.1f}s)", flush=True)
    print(f"[qa] {overall_status}", flush=True)


if __name__ == "__main__":
    main()
