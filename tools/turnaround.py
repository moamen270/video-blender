"""Render turnaround stills and lineup for character review (Task E4)."""
from __future__ import annotations

import argparse
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(ROOT, "studio")):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy

from kit import cast, look, qchar, toon
from studio import core as C

VIEWS = [
    ("front", (0.0, 4.6, 1.05), (0.0, 0.0, 0.9), 50.0),
    ("threeq", (2.64, 3.77, 1.05), (0.0, 0.0, 0.9), 50.0),
    ("side", (4.6, 0.0, 1.05), (0.0, 0.0, 0.9), 50.0),
    ("back", (0.0, -4.6, 1.05), (0.0, 0.0, 0.9), 50.0),
    ("face", (0.0, 2.10, 1.50), (0.0, 0.0, 1.38), 50.0),
    ("sil", (0.0, 4.6, 1.05), (0.0, 0.0, 0.9), 50.0),
]


def main() -> None:
    argv = sys.argv
    raw_args = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser(description="Render character turnarounds.")
    parser.add_argument("--cast", default="batman,joker", help="Comma-separated cast names")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--lineup", dest="lineup", action="store_true", default=True, help="Render lineup")
    parser.add_argument("--no-lineup", dest="lineup", action="store_false", help="Skip lineup")
    args = parser.parse_args(raw_args)

    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    cast_names = [name.strip() for name in args.cast.split(",") if name.strip()]

    for name in cast_names:
        if name not in cast.CAST:
            raise ValueError(f"Unknown character '{name}' in CAST registry")

        C.reset_scene()
        qc = cast.CAST[name]()
        look.store_night(target=(0.0, 0.0, 0.9))
        floor = look.floor()
        qchar.set_action(qc, "Idle", 1)
        bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()

        for v_name, cam_pos, look_at, lens in VIEWS:
            filepath = os.path.join(out_dir, f"{name}_{v_name}.png")
            cam = C.camera(f"cam_{v_name}", cam_pos, look_at, lens=lens)
            bpy.context.scene.camera = cam

            if v_name == "sil":
                black_mat = toon.toon("sil_black", "#000000", emission=1.0)
                old_override = bpy.context.view_layer.material_override
                bpy.context.view_layer.material_override = black_mat
                floor.hide_render = True
                C.sky((1.0, 1.0, 1.0), 1.0)
                C.render_settings(
                    width=540,
                    height=960,
                    quality="final",
                    video=False,
                    frame_end=1,
                    filepath=filepath,
                )
                bpy.context.scene.render.resolution_percentage = 25
                bpy.context.scene.render.filepath = filepath
                bpy.ops.render.render(write_still=True)
                print(f"[turnaround] {filepath}", flush=True)

                bpy.context.view_layer.material_override = old_override
                floor.hide_render = False
                C.sky(C.hex_rgb("#0b0f18"), 1.0)
                bpy.context.scene.render.resolution_percentage = 100
            else:
                C.render_settings(
                    width=540,
                    height=960,
                    quality="final",
                    video=False,
                    frame_end=1,
                    filepath=filepath,
                )
                bpy.context.scene.render.filepath = filepath
                bpy.ops.render.render(write_still=True)
                print(f"[turnaround] {filepath}", flush=True)

            cam_data = cam.data
            bpy.data.objects.remove(cam, do_unlink=True)
            if cam_data and cam_data.users == 0:
                bpy.data.cameras.remove(cam_data)

    if args.lineup:
        C.reset_scene()
        batman = cast.build_batman()
        batman.root.location = (-0.55, 0.0, 0.0)
        batman.root.rotation_euler = (0.0, 0.0, math.radians(-12.0))
        qchar.set_action(batman, "Idle", 1)

        joker = cast.build_joker()
        joker.root.location = (0.55, 0.0, 0.0)
        joker.root.rotation_euler = (0.0, 0.0, math.radians(12.0))
        qchar.set_action(joker, "Idle", 1)

        look.store_night(target=(0.0, 0.0, 0.95))
        look.floor()

        cam = C.camera("cam_lineup", (0.6, 4.2, 1.2), (0.0, 0.0, 0.95), lens=40.0)
        bpy.context.scene.camera = cam

        lineup_path = os.path.join(out_dir, "lineup.png")
        C.render_settings(
            width=1080,
            height=1350,
            quality="final",
            video=False,
            frame_end=1,
            filepath=lineup_path,
        )
        bpy.context.scene.render.filepath = lineup_path
        bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()
        bpy.ops.render.render(write_still=True)
        print(f"[turnaround] {lineup_path}", flush=True)


if __name__ == "__main__":
    main()
