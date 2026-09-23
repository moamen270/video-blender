"""Test for moonlit stage, lighting, bamboo grove, and petal particles (Task T5)."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isdir(os.path.join(ROOT, "studio")):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy

from kit import pose, samurai, stage
from studio import core as C


def main() -> None:
    C.reset_scene()
    stage.build_stage()
    stage.petals()
    ronin = samurai.build_ronin()
    warlord = samurai.build_warlord()

    from kit import pose
    pose.apply_pose(ronin, pose.POSES["sheathed"])
    pose.apply_pose(warlord, pose.POSES["sheathed"])

    bpy.context.scene.frame_set(40)
    bpy.context.view_layer.update()

    C.render_settings(width=540, height=960, frame_end=672, quality="final", video=False)

    out_dir = os.path.join(ROOT, "output", "tests", "T5")
    os.makedirs(out_dir, exist_ok=True)

    cam_wide = C.camera("cam_wide", (0.0, -8.5, 1.1), (0.0, 0.0, 1.3), lens=30.0)
    cam_rev = C.camera("cam_rev", (0.0, 8.5, 1.4), (0.0, 0.0, 1.2), lens=30.0)

    for filename, cam in [("wide.png", cam_wide), ("reverse.png", cam_rev)]:
        bpy.context.scene.camera = cam
        filepath = os.path.join(out_dir, filename)
        bpy.context.scene.render.filepath = filepath
        bpy.ops.render.render(write_still=True)
        assert os.path.isfile(filepath), f"Render output missing: {filepath}"
        assert os.path.getsize(filepath) > 0, f"Render output empty: {filepath}"

    bamboo_count = sum(1 for o in bpy.data.objects if o.name.startswith("stage_bamboo"))
    ring_count = sum(1 for o in bpy.data.objects if o.name.startswith("stage_ring"))
    petal_count = sum(1 for o in bpy.data.objects if o.name.startswith("fx_petal"))

    print(f"[test] bamboo stalks: {bamboo_count}", flush=True)
    print(f"[test] bamboo rings: {ring_count}", flush=True)
    print(f"[test] petals: {petal_count}", flush=True)

    assert bamboo_count >= 40, f"bamboo stalk count {bamboo_count} < 40"

    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
