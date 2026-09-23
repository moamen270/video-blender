"""Test for samurai character builders, meshes, and rendering (Task T4)."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isdir(os.path.join(ROOT, "studio")):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy

from kit import pose, samurai, toon
from studio import core as C


def main() -> None:
    C.reset_scene()

    ronin = samurai.build_ronin()
    warlord = samurai.build_warlord()

    pose.apply_pose(ronin, pose.POSES["chudan"])
    pose.apply_pose(warlord, pose.POSES["chudan"])
    bpy.context.view_layer.update()

    C.sky(C.hex_rgb("#3a3f4b"))
    C.sun("key", energy=3.0, rot=(55, 0, 160))
    C.sun("rim", energy=1.5, rot=(60, 0, -20))

    ground_mat = toon.toon("ground", "#2a2f3a")
    C.plane("ground", size=20.0, mat=ground_mat)

    out_dir = os.path.join(ROOT, "output", "tests", "T4")
    os.makedirs(out_dir, exist_ok=True)

    C.render_settings(width=540, height=960, frame_end=1, quality="final", video=False)

    renders = [
        ("three_quarter.png", C.camera("cam_three_quarter", (3.5, -5.5, 1.6), (0.0, 0.0, 1.1), lens=35.0)),
        ("side.png", C.camera("cam_side", (0.0, -7.0, 1.2), (0.0, 0.0, 1.1), lens=30.0)),
        ("face_ronin.png", C.camera("cam_fr", (-0.3, -1.1, 1.72), (-1.45, 0.0, 1.68), lens=35.0)),
        ("face_warlord.png", C.camera("cam_fw", (0.3, -1.1, 1.72), (1.45, 0.0, 1.68), lens=35.0)),
    ]

    for filename, cam in renders:
        bpy.context.scene.camera = cam
        bpy.context.scene.render.filepath = os.path.join(out_dir, filename)
        bpy.ops.render.render(write_still=True)

    ronin_count = sum(1 for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("ronin_"))
    warlord_count = sum(1 for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("warlord_"))

    print(f"[test] ronin mesh parts: {ronin_count}", flush=True)
    print(f"[test] warlord mesh parts: {warlord_count}", flush=True)

    assert ronin_count >= 25, f"ronin mesh count {ronin_count} < 25"
    assert warlord_count >= 25, f"warlord mesh count {warlord_count} < 25"

    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
