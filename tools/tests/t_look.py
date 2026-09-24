"""Test for look-dev: toon v2 material, lighting, floor (Task E2)."""
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
from kit import look
from kit import toon


def main() -> None:
    C.reset_scene()
    look.store_night(target=(0.0, 0.0, 0.6))
    look.floor()

    colors = [
        ("dummy", "#1c1d24"),
        ("suit_grey", "#5d6470"),
        ("purple", "#5b2a86"),
        ("yellow", "#e3b21c"),
        ("green", "#35b24a"),
    ]
    xs = [-1.6, -0.8, 0.0, 0.8, 1.6]

    # Row 1 (y = 0, z = 1.25): spheres r = 0.3 with toon2 + kit.toon.add_outline(obj, 0.010)
    for (name, hex_code), x in zip(colors, xs):
        mat = look.toon2(f"t2_{name}", hex_code)
        sph = C.sphere(f"r1_{name}", r=0.3, loc=(x, 0.0, 1.25), mat=mat)
        toon.add_outline(sph, 0.010)

    # Row 2 (y = 0, z = 0.45): the same spheres with the OLD kit.toon.toon material + outline (comparison)
    for (name, hex_code), x in zip(colors, xs):
        mat_old = toon.toon(f"t1_{name}", hex_code)
        sph_old = C.sphere(f"r2_{name}", r=0.3, loc=(x, 0.0, 0.45), mat=mat_old)
        toon.add_outline(sph_old, 0.010)

    # Row 3 (y = 0, z = 2.05): five dummy-coloured spheres with rim_width 0.50, 0.58, 0.66, 0.74, 0.82 (material names rimtest_<w>)
    rim_widths = [0.50, 0.58, 0.66, 0.74, 0.82]
    for w, x in zip(rim_widths, xs):
        w_str = f"{w:.2f}"
        mat = look.toon2(f"rimtest_{w_str}", "#1c1d24", rim_width=w)
        C.sphere(f"r3_{w_str}", r=0.3, loc=(x, 0.0, 2.05), mat=mat)

    # Camera C.camera("cam", (0, 6.0, 1.25), (0, 0, 1.25), lens=35)
    cam = C.camera("cam", (0.0, 6.0, 1.25), (0.0, 0.0, 1.25), lens=35.0)
    bpy.context.scene.camera = cam

    # Render 1080x1080 -> output/tests/E2/look.png
    out_dir = os.path.join(ROOT, "output", "tests", "E2")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "look.png")

    C.render_settings(width=1080, height=1080, quality="final", video=False, frame_end=1, filepath=out_path)
    bpy.context.scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)

    # Assert every toon2 material has exactly one node of each type:
    # SHADERTORGB, LAYER_WEIGHT, MIX, VALTORGB, EMISSION; ramp has 3 elements;
    # the file exists and is > 10 kB.
    toon2_materials = [m for m in bpy.data.materials if m.name in look._CACHE]
    assert len(toon2_materials) == 11, f"Expected 11 toon2 materials, got {len(toon2_materials)}"

    for mat in toon2_materials:
        assert mat.use_nodes and mat.node_tree, f"Material '{mat.name}' has no node tree"
        node_types = [n.type for n in mat.node_tree.nodes]
        for expected_type in ("SHADERTORGB", "LAYER_WEIGHT", "MIX", "VALTORGB", "EMISSION"):
            count = node_types.count(expected_type)
            assert count == 1, (
                f"Material '{mat.name}' has {count} nodes of type {expected_type}, expected 1"
            )

        ramp_node = next(n for n in mat.node_tree.nodes if n.type == "VALTORGB")
        ramp_elements = ramp_node.color_ramp.elements
        assert len(ramp_elements) == 3, (
            f"Material '{mat.name}' ramp has {len(ramp_elements)} elements, expected 3"
        )

    assert os.path.isfile(out_path), f"Render file does not exist: {out_path}"
    file_size = os.path.getsize(out_path)
    assert file_size > 10 * 1024, f"Render file {out_path} is {file_size} bytes, expected > 10 kB"

    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
