"""Unit tests for word timings, captions, and trimmed lines (Task G5)."""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
tools_dir = os.path.join(ROOT, "tools")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

import numpy as np

import audio
from kit import captions


def test_manifest_words() -> None:
    manifest_path = os.path.join(ROOT, "projects", "ep02", "voice", "manifest.json")
    assert os.path.isfile(manifest_path), f"Manifest file missing: {manifest_path}"
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    lines = manifest.get("lines", {})
    assert lines, "No lines in ep02 manifest"

    # If manifest does not have words yet (e.g. voice.py not run beforehand),
    # populate words from alignment files without synthesizing audio
    if any("words" not in entry for entry in lines.values()):
        import voice
        old_argv = sys.argv
        sys.argv = ["voice.py", "--project", "ep02"]
        try:
            voice.main()
        finally:
            sys.argv = old_argv
        with open(manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        lines = manifest.get("lines", {})

    for lid, entry in lines.items():
        assert "words" in entry, f"Line '{lid}' missing 'words' in ep02 manifest"
        words = entry["words"]
        assert isinstance(words, list), f"Line '{lid}' words must be a list"
        assert len(words) > 0, f"Line '{lid}' has empty 'words'"
        for w in words:
            assert "w" in w, f"Missing 'w' in word {w} of line {lid}"
            assert "start" in w, f"Missing 'start' in word {w} of line {lid}"
            assert "end" in w, f"Missing 'end' in word {w} of line {lid}"
            assert w["end"] >= w["start"], f"Invalid timing in word {w} of line {lid}"


def test_groups_b_vengeance() -> None:
    manifest_path = os.path.join(ROOT, "projects", "ep02", "voice", "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    lines = manifest["lines"]
    assert "b_vengeance" in lines, "Line 'b_vengeance' not found in ep02 manifest"
    b_words = lines["b_vengeance"]["words"]

    grps = captions.groups(b_words, start_frame=100, fps=24, keywords=("vengeance", "night"))
    assert len(grps) > 0, "groups() returned empty list for b_vengeance"

    collected_words = []
    for g in grps:
        assert "text" in g and "start_frame" in g and "end_frame" in g and "hi" in g
        assert g["start_frame"] <= g["end_frame"], f"Invalid frame range in group: {g}"
        words_in_grp = g["text"].split()
        assert 1 <= len(words_in_grp) <= 3, (
            f"Group has {len(words_in_grp)} words, expected <= 3: {g['text']}"
        )
        assert not g["text"].endswith(","), f"Group text has trailing comma: {g['text']}"
        collected_words.extend(words_in_grp)

    expected_words = [w["w"].rstrip(",").upper() for w in b_words]
    assert collected_words == expected_words, (
        f"Words mismatch:\nGot:      {collected_words}\nExpected: {expected_words}"
    )
    assert grps[0]["hi"] is True, f"Expected hi=True for group with 'vengeance': {grps[0]}"


def test_build_caption_filters() -> None:
    test_captions = [
        {"start_frame": 24, "end_frame": 48, "text": "I AM VENGEANCE", "hi": True},
        {"start_frame": 48, "end_frame": 72, "text": "I AM THE NIGHT", "hi": False},
    ]
    c_filters = audio.build_caption_filters(test_captions, fps=24, width=1080, height=1920)
    assert len(c_filters) == 2, f"Expected 2 filters, got {len(c_filters)}"
    for f in c_filters:
        assert "between(t," in f, f"Filter missing 'between(t,': {f}"
        assert "drawtext=" in f, f"Filter missing 'drawtext=': {f}"
    assert "#ffd400" in c_filters[0], f"First filter missing yellow #ffd400: {c_filters[0]}"
    assert "white" in c_filters[1], f"Second filter missing white: {c_filters[1]}"


def test_dur_trim() -> None:
    sr = 48000
    clip = np.ones(sr * 2, dtype=np.float32)
    dur = 1.0
    trimmed = audio.trim_clip(clip, dur, sr=sr)
    expected_samples = int(dur * sr)
    assert len(trimmed) == expected_samples, (
        f"Expected length {expected_samples}, got {len(trimmed)}"
    )
    fade_samples = int(round(0.020 * sr))
    assert np.allclose(trimmed[:expected_samples - fade_samples], 1.0)
    assert abs(trimmed[-1]) < 1e-5, f"Expected trimmed[-1] == 0.0, got {trimmed[-1]}"
    fade_region = trimmed[expected_samples - fade_samples:]
    expected_fade = np.linspace(1.0, 0.0, fade_samples)
    assert np.allclose(fade_region, expected_fade), "Fade region is not linear 1.0 -> 0.0"

    short_clip = np.ones(int(0.5 * sr), dtype=np.float32)
    trimmed_short = audio.trim_clip(short_clip, 1.0, sr=sr)
    assert len(trimmed_short) == len(short_clip)


def main() -> None:
    test_manifest_words()
    test_groups_b_vengeance()
    test_build_caption_filters()
    test_dur_trim()
    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
