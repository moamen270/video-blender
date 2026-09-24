"""Voice lines synthesis and Rhubarb lip sync manifest generator (Task F3).

Run:
    uv run --project F:/PoCs/video-builder/py python tools/voice.py --project cp2
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import subprocess
import sys

import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tools_dir = os.path.join(ROOT, "tools")
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

import audio

RHUBARB = "F:/PoCs/tools/Rhubarb-Lip-Sync-1.14.0-Windows/rhubarb.exe"


def compute_hash(line: dict) -> str:
    """Compute sha1 hash of line specification fields."""
    payload = {
        "text": line.get("text"),
        "engine": line.get("engine", "kokoro"),
        "voice": line.get("voice"),
        "voiceRef": line.get("voiceRef"),
        "emotion": line.get("emotion"),
        "speed": line.get("speed"),
        "seed": line.get("seed"),
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha1(encoded).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    project = args.project
    p_dir = os.path.join(ROOT, "projects", project)
    if not os.path.isdir(p_dir):
        p_dir = os.path.join(ROOT, project)
        project = os.path.basename(os.path.normpath(p_dir))

    lines_file = os.path.join(p_dir, "lines.json")
    with open(lines_file, "r", encoding="utf-8") as fh:
        lines = json.load(fh)
    # Casting sheet: a line with "character" gets that character's voice settings; the line's own keys win.
    with open(os.path.join(ROOT, "assets", "cast", "voices.json"), "r", encoding="utf-8") as fh:
        cast = json.load(fh)["characters"]
    for i, l in enumerate(lines):
        voice = cast.get(l.get("character", ""), {})
        lines[i] = {**{k: v for k, v in voice.items() if k != "notes"}, **l}
        ref = lines[i].get("voiceRef")
        if ref and not os.path.isabs(ref):
            lines[i]["voiceRef"] = os.path.join(ROOT, ref).replace("\\", "/")

    out_dir = os.path.join(p_dir, "voice")
    os.makedirs(out_dir, exist_ok=True)
    manifest_path = os.path.join(out_dir, "manifest.json")

    prev_manifest: dict = {}
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as fh:
                prev_manifest = json.load(fh)
        except Exception:
            prev_manifest = {}
    prev_lines = prev_manifest.get("lines", {})

    # Determine which lines need re-synthesis
    lines_to_synth: list[dict] = []
    for i, l in enumerate(lines):
        lid = l.get("id", f"l{i}")
        l["id"] = lid
        wav_path = os.path.join(out_dir, f"{lid}.wav")
        h = compute_hash(l)
        prev = prev_lines.get(lid, {})
        if (not os.path.isfile(wav_path)) or (prev.get("hash") != h):
            lines_to_synth.append(l)

    # Synthesize changed lines grouped by engine
    if lines_to_synth:
        kokoro_by_voice: dict[str, list[dict]] = collections.defaultdict(list)
        chatterbox_lines: list[dict] = []
        for l in lines_to_synth:
            engine = l.get("engine", "kokoro")
            if engine == "chatterbox":
                chatterbox_lines.append(l)
            else:
                voice = l.get("voice", "bm_george")
                kokoro_by_voice[voice].append(l)

        for voice, v_lines in kokoro_by_voice.items():
            audio.narrate(v_lines, voice, out_dir)

        if chatterbox_lines:
            audio.chatterbox(chatterbox_lines, out_dir)

    # Load alignment tokens from align.json and chatterbox.json
    align_tokens: dict[str, list[dict]] = {}
    for jname in ("align.json", "chatterbox.json"):
        jpath = os.path.join(out_dir, jname)
        if os.path.isfile(jpath):
            try:
                with open(jpath, "r", encoding="utf-8") as fh:
                    jdata = json.load(fh)
                    for sc in jdata.get("scenes", []):
                        sid = sc.get("sceneId")
                        if sid and "tokens" in sc:
                            align_tokens[sid] = sc["tokens"]
            except Exception:
                pass

    # Rhubarb per line and build manifest
    new_manifest_lines = dict(prev_lines)

    for i, l in enumerate(lines):
        lid = l["id"]
        h = compute_hash(l)
        wav_path = os.path.abspath(os.path.join(out_dir, f"{lid}.wav")).replace("\\", "/")
        txt_path = os.path.join(out_dir, f"{lid}.txt")
        rhubarb_json_path = os.path.join(out_dir, f"{lid}.rhubarb.json")

        is_unchanged = (
            l not in lines_to_synth
            and lid in prev_lines
            and prev_lines[lid].get("hash") == h
            and os.path.isfile(rhubarb_json_path)
            and "cues" in prev_lines[lid]
        )

        if is_unchanged:
            entry = dict(prev_lines[lid])
        else:
            with open(txt_path, "w", encoding="utf-8") as fh:
                fh.write(l["text"])

            subprocess.run(
                [
                    RHUBARB,
                    "-q",
                    "-f", "json",
                    "-o", rhubarb_json_path,
                    "--dialogFile", txt_path,
                    wav_path,
                ],
                check=True,
            )

            with open(rhubarb_json_path, "r", encoding="utf-8") as fh:
                rhubarb_data = json.load(fh)
            mouth_cues = rhubarb_data.get("mouthCues", [])

            info = sf.info(wav_path)
            seconds = round(float(info.duration), 2)

            entry = {
                "wav": wav_path,
                "seconds": seconds,
                "hash": h,
                "text": l["text"],
                "character": l.get("character", ""),
                "cues": mouth_cues,
            }

        if "words" not in entry or (l in lines_to_synth):
            tokens = align_tokens.get(lid, [])
            entry["words"] = [
                {"w": tok.get("text", tok.get("w", "")), "start": tok["start"], "end": tok["end"]}
                for tok in tokens
            ]

        new_manifest_lines[lid] = entry
        sec = entry["seconds"]
        n_cues = len(entry["cues"])
        print(f"[voice] {lid} {sec}s {n_cues} cues", flush=True)

    manifest_data = {"lines": new_manifest_lines}
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest_data, fh, indent=2)


if __name__ == "__main__":
    main()
