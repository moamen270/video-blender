"""Test for lip sync and mouth animations (Task F3)."""
from __future__ import annotations

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isdir(os.path.join(ROOT, "studio")):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy

from studio import core as C
from kit import face, look, qchar


def main() -> None:
    # 1. Read projects/batman-joker-screen-test/voice/manifest.json
    manifest_path = os.path.join(ROOT, "projects", "tests", "batman-joker-screen-test", "voice", "manifest.json")
    assert os.path.isfile(manifest_path), f"Manifest file missing: {manifest_path}"
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    lines = manifest.get("lines", {})
    assert "bat1" in lines, "bat1 missing from manifest lines"
    assert "jok1" in lines, "jok1 missing from manifest lines"

    for lid in ("bat1", "jok1"):
        entry = lines[lid]
        sec = entry.get("seconds", 0.0)
        assert sec > 0.5, f"{lid}: expected seconds > 0.5, got {sec}"
        cues = entry.get("cues", [])
        assert len(cues) >= 5, f"{lid}: expected >= 5 cues, got {len(cues)}"
        wav = entry.get("wav", "")
        assert os.path.isfile(wav), f"{lid}: wav file not found at {wav}"

    # 2. Load character & build face (BaseCharacter, rest frown)
    C.reset_scene()
    qc = qchar.load_character("BaseCharacter.blend", "hero")
    f = face.build_face(qc, rest="frown")

    # 3. Apply lip sync for bat1 starting at frame 10
    cues_bat1 = lines["bat1"]["cues"]
    start_frame = 10
    face.apply_lipsync(f, cues_bat1, start_frame)

    # 4. Assert mouth objects visibility at each cue frame
    for i in range(len(cues_bat1)):
        cue = cues_bat1[i]
        f_cue = start_frame + round(cue["start"] * 24)
        if i + 1 < len(cues_bat1):
            f_next = start_frame + round(cues_bat1[i + 1]["start"] * 24)
            if f_cue == f_next:
                continue

        bpy.context.scene.frame_set(f_cue)
        val = cue["value"]
        expected_shape = f.rest_shape if val == "X" else val

        visible = [name for name, obj in f.mouths.items() if not obj.hide_render]
        assert len(visible) == 1, (
            f"Frame {f_cue} (cue {i} '{val}'): expected exactly 1 visible mouth, got {visible}"
        )
        assert visible[0] == expected_shape, (
            f"Frame {f_cue} (cue {i} '{val}'): expected shape '{expected_shape}', got '{visible[0]}'"
        )

    # 5. Assert auto_blink produces >= 2 blinks, no two closer than 48 frames
    blinks = face.auto_blink(f, 1, 240, [(1, "stern")])
    assert len(blinks) >= 2, f"Expected >= 2 blinks, got {len(blinks)}: {blinks}"
    for j in range(len(blinks) - 1):
        gap = blinks[j + 1] - blinks[j]
        assert gap >= 48, f"Blinks too close: frames {blinks[j]} and {blinks[j+1]} (gap {gap} < 48)"

    # 6. Render 4 face stills at frames of cues 1, 3, 5, 7
    out_dir = os.path.join(ROOT, "output", "tests", "F3")
    os.makedirs(out_dir, exist_ok=True)

    look.store_night(target=(0.0, 0.0, 1.38))
    cam = C.camera("cam", (0.0, 2.1, 1.5), (0.0, 0.0, 1.38), lens=50.0)
    bpy.context.scene.camera = cam

    for idx in (1, 3, 5, 7):
        assert idx < len(cues_bat1), f"Cue index {idx} out of range (total cues: {len(cues_bat1)})"
        cue = cues_bat1[idx]
        f_cue = start_frame + round(cue["start"] * 24)
        bpy.context.scene.frame_set(f_cue)
        bpy.context.view_layer.update()
        still_path = os.path.join(out_dir, f"cue_{idx}.png")
        C.render_settings(width=540, height=960, quality="final", video=False, frame_end=1, filepath=still_path)
        bpy.context.scene.render.filepath = still_path
        bpy.ops.render.render(write_still=True)
        assert os.path.isfile(still_path), f"Still file not found: {still_path}"
        assert os.path.getsize(still_path) > 0, f"Still file is empty: {still_path}"

    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
