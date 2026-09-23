"""Test for toon shader and outline modifier (Task T1)."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isdir(os.path.join(ROOT, "studio")):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy

from studio import core as C
from kit import toon


def main() -> None:
    C.reset_scene()

    sph = C.sphere("sphere", r=0.6, loc=(-0.8, 0, 0.6), mat=toon.toon("t_red", "#c0392b"))
    cu = C.cube("cube", size=1.0, loc=(0.8, 0, 0.5), mat=toon.toon("t_blue", "#2e86de"))

    toon.add_outline(sph)
    toon.add_outline(cu)

    C.sky(C.hex_rgb("#20242e"))
    C.sun("key", energy=3.0, rot=(50, 0, 30))

    cam = C.camera("cam", (0, -5, 1.5), (0, 0, 0.5), lens=40)
    bpy.context.scene.camera = cam

    C.render_settings(width=540, height=960, frame_end=1, quality="final", video=False)

    out_dir = os.path.join(ROOT, "output", "tests", "T1")
    os.makedirs(out_dir, exist_ok=True)
    still_path = os.path.join(out_dir, "still.png")
    bpy.context.scene.render.filepath = still_path
    bpy.ops.render.render(write_still=True)

    assert os.path.isfile(still_path), f"File not found: {still_path}"
    assert os.path.getsize(still_path) > 0, f"File is empty: {still_path}"

    for obj in (sph, cu):
        assert "outline" in obj.modifiers, f"{obj.name} has no 'outline' modifier"
        mod = obj.modifiers["outline"]
        assert mod.type == "SOLIDIFY", f"{obj.name} modifier type is {mod.type}, expected SOLIDIFY"
        assert len(obj.material_slots) == 2, f"{obj.name} has {len(obj.material_slots)} material slots, expected 2"

    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
