"""Test for auto-framed shots (Task G3)."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isdir(os.path.join(ROOT, "studio")):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy
from mathutils import Vector

from studio import core as C
from kit.qchar import load_character
from kit import shots


def main() -> None:
    # 1. Reset scene
    C.reset_scene()

    # 2. Output directory
    out_dir = os.path.join(ROOT, "output", "tests", "G3")
    os.makedirs(out_dir, exist_ok=True)

    # 3. Set scene resolution to 1080x1920 BEFORE framing so aspect is 9:16
    C.render_settings(width=1080, height=1920, quality="draft", video=False, frame_end=24)

    # 4. Basic world and lighting
    C.sky(C.hex_rgb("#808890"))
    C.sun("key", energy=3.0, rot=(50, 10, 30))

    # 5. Load characters
    a = load_character("BaseCharacter.blend", "a", loc=(0, 0, 0))
    b = load_character("Suit_Male.blend", "b", loc=(1.0, 0, 0))

    # 6. Test all shot presets
    shot_types = ["wide", "full", "medium", "close", "ecu", "insert", "two_shot"]

    for shot in shot_types:
        target = [a, b] if shot == "two_shot" else a
        cam = shots.frame(f"cam_{shot}", target, shot=shot, yaw=30.0, pitch=5.0)
        res = shots.check(cam, target, shot)

        preset = shots.PRESETS[shot]
        expected_fill = preset["fraction"]
        expected_top = 1.0 - preset["headroom"]

        print(
            f"[shots] {shot}: fill={res['fill']:.4f} (exp {expected_fill:.2f}), "
            f"top={res['top']:.4f} (exp {expected_top:.2f}), "
            f"cx={res['cx']:.4f} (exp 0.50)",
            flush=True,
        )

        assert abs(res["fill"] - expected_fill) <= 0.06, (
            f"Shot {shot} fill {res['fill']:.4f} not within ±0.06 of {expected_fill:.4f}"
        )
        assert abs(res["top"] - expected_top) <= 0.04, (
            f"Shot {shot} top {res['top']:.4f} not within ±0.04 of {expected_top:.4f}"
        )
        assert abs(res["cx"] - 0.5) <= 0.06, (
            f"Shot {shot} cx {res['cx']:.4f} not within ±0.06 of 0.5"
        )

        # Render one 270x480 still per shot to output/tests/G3/
        still_path = os.path.join(out_dir, f"{shot}.png")
        bpy.context.scene.camera = cam
        bpy.context.scene.frame_set(1)
        bpy.context.scene.render.filepath = still_path
        bpy.context.scene.render.resolution_percentage = 25
        bpy.ops.render.render(write_still=True)
        bpy.context.scene.render.resolution_percentage = 100
        assert os.path.isfile(still_path), f"Still file not found: {still_path}"
        assert os.path.getsize(still_path) > 0, f"Still file is empty: {still_path}"

    # 7. Test push (moves camera closer by 12% ± 1%)
    cam_push = shots.frame("cam_push_test", a, shot="medium", yaw=30.0, pitch=5.0)
    aim = Vector((cam_push["aim_x"], cam_push["aim_y"], cam_push["aim_z"]))
    d_start = (cam_push.location - aim).length
    shots.push(cam_push, 1, 24, amount=0.12)
    bpy.context.scene.frame_set(24)
    bpy.context.view_layer.update()
    d_end = (cam_push.location - aim).length
    closer = (d_start - d_end) / d_start
    print(f"[shots] push: closer={closer * 100:.2f}% (exp 12% ± 1%)", flush=True)
    assert abs(closer - 0.12) <= 0.01, f"Expected push closer by 12% ± 1%, got {closer * 100:.2f}%"

    # 8. Test whip
    shots.whip(cam_push, 24, b, frames=4)
    assert bpy.context.scene.render.use_motion_blur is True, "Expected use_motion_blur = True"

    # 9. Pass
    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
