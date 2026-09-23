"""Test for FX module: sparks, smear ribbon, camera shake, dust, and helmet split (Task T6)."""
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

from kit import fx, samurai, stage
from kit import pose as P
from studio import core as C


def main() -> None:
    C.reset_scene()
    stage.build_stage()
    ronin = samurai.build_ronin()
    warlord = samurai.build_warlord()

    P.key_pose(ronin, P.POSES["slash_windup"], 4, mover=(0.9, 0.0))
    P.key_pose(ronin, P.POSES["slash_hit"], 10, mover=(0.9, 0.0), interp="BEZIER")

    P.key_pose(warlord, P.POSES["block_mid"], 1)
    P.hold(warlord, P.POSES["block_mid"], 1, 30)

    scene = bpy.context.scene
    scene.frame_set(10)
    bpy.context.view_layer.update()
    M = (fx.sword_point(ronin, 0.75) + fx.sword_point(warlord, 0.5)) / 2.0
    fx.spark(M, 10, seed=1)

    fx.smear(ronin, 4, 10, "test")
    fx.helmet_split(warlord, 20)
    fx.dust(Vector((1.5, 0.0, 0.0)), 20)

    cam = C.camera("cam", (0.0, -5.2, 1.25), (0.0, 0.0, 1.2), lens=35.0)
    scene.camera = cam
    fx.shake(cam, 10, 16)

    out_dir = os.path.join(ROOT, "output", "tests", "T6")
    os.makedirs(out_dir, exist_ok=True)

    C.render_settings(width=540, height=960, frame_end=30, quality="final", video=False)

    for f in [8, 10, 12, 22, 30]:
        scene.frame_set(f)
        filepath = os.path.join(out_dir, f"f_{f:03d}.png")
        scene.render.filepath = filepath
        bpy.ops.render.render(write_still=True)
        assert os.path.isfile(filepath), f"Render output missing: {filepath}"
        assert os.path.getsize(filepath) > 0, f"Render output empty: {filepath}"

    fx_count = sum(1 for o in bpy.data.objects if o.name.startswith("fx_"))
    print(f"[test] fx objects count: {fx_count}", flush=True)
    assert fx_count >= 20, f"fx object count {fx_count} < 20"

    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
