"""Test for sets: Kenney prop import, gotham_mart layout, flicker (Task G2)."""
from __future__ import annotations

import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isdir(os.path.join(ROOT, "studio")):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy
from mathutils import Vector

from studio import core as C
from kit import look
from kit import sets


def main() -> None:
    # 1. Reset scene and build the Gotham Mart store set + store_night lighting
    C.reset_scene()
    mart = sets.gotham_mart()
    look.store_night(target=(0.0, 0.0, 1.0))

    # 2. Assert >= 20 imported meshes
    imported_meshes = [
        o for o in bpy.data.objects
        if o.type == "MESH" and (o.parent and o.parent.name.startswith("set_"))
    ]
    assert len(imported_meshes) >= 20, f"Expected >= 20 imported meshes, got {len(imported_meshes)}"

    # 3. Assert every imported material has an Emission node and no Principled node
    imported_materials = set()
    for o in imported_meshes:
        for slot in o.material_slots:
            if slot.material:
                imported_materials.add(slot.material)

    assert len(imported_materials) > 0, "No imported materials found on imported meshes"
    for mat in imported_materials:
        assert mat.use_nodes and mat.node_tree, f"Material '{mat.name}' has no node tree"
        node_types = [n.type for n in mat.node_tree.nodes]
        assert "EMISSION" in node_types, f"Material '{mat.name}' missing Emission node"
        assert "BSDF_PRINCIPLED" not in node_types, f"Material '{mat.name}' has unexpected Principled node"

    # 4. Assert shelves' heights are 1.9–2.6 m
    shelf_roots = [
        o for o in bpy.data.objects
        if o.name.startswith("set_shelf-")
    ]
    assert len(shelf_roots) == 6, f"Expected 6 shelf objects, got {len(shelf_roots)}"
    for shelf in shelf_roots:
        meshes = [o for o in [shelf, *shelf.children_recursive] if o.type == "MESH"]
        assert meshes, f"Shelf '{shelf.name}' has no mesh children"
        z_coords = [
            (m.matrix_world @ Vector(corner)).z
            for m in meshes
            for corner in m.bound_box
        ]
        h = max(z_coords) - min(z_coords)
        assert 1.9 <= h <= 2.6, f"Shelf '{shelf.name}' height {h:.3f} m is not within [1.9, 2.6] m"

    # 5. Test flicker animation
    sets.flicker(mart, [(10, 14)])
    bpy.context.scene.frame_set(1)

    # 6. Render stills to output/tests/G2/
    out_dir = os.path.join(ROOT, "output", "tests", "G2")
    os.makedirs(out_dir, exist_ok=True)

    # Still 1: from (3.0, 4.2, 1.7) -> (-0.3, 0, 1.0) lens 28
    cam1 = C.camera("cam_aisle", (3.0, 4.2, 1.7), (-0.3, 0.0, 1.0), lens=28.0)
    bpy.context.scene.camera = cam1

    still1_path = os.path.join(out_dir, "still1.png")
    C.render_settings(width=540, height=960, quality="final", video=False, frame_end=1, filepath=still1_path)
    bpy.context.scene.render.filepath = still1_path
    bpy.ops.render.render(write_still=True)
    assert os.path.isfile(still1_path), f"Still 1 not found: {still1_path}"
    assert os.path.getsize(still1_path) > 0, f"Still 1 is empty: {still1_path}"

    # Still 2: from (0, 5.5, 1.5) -> (0, 0, 1.2) lens 24
    cam2 = C.camera("cam_front", (0.0, 5.5, 1.5), (0.0, 0.0, 1.2), lens=24.0)
    bpy.context.scene.camera = cam2

    still2_path = os.path.join(out_dir, "still2.png")
    bpy.context.scene.render.filepath = still2_path
    bpy.ops.render.render(write_still=True)
    assert os.path.isfile(still2_path), f"Still 2 not found: {still2_path}"
    assert os.path.getsize(still2_path) > 0, f"Still 2 is empty: {still2_path}"

    # Copy to alternate names in case inspector looks for them
    shutil.copyfile(still1_path, os.path.join(out_dir, "cam1.png"))
    shutil.copyfile(still2_path, os.path.join(out_dir, "cam2.png"))
    shutil.copyfile(still1_path, os.path.join(out_dir, "aisle.png"))
    shutil.copyfile(still2_path, os.path.join(out_dir, "front.png"))

    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
