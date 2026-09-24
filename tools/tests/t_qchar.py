"""Test for Quaternius character loader (Task E1)."""
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
from kit.qchar import (
    load_character,
    rest,
    native,
    assign,
    delete_faces,
    take_part,
    surface_points,
    set_action,
    height_now,
    strip,
)


def main() -> None:
    # 1. Reset scene and load BaseCharacter
    C.reset_scene()
    a = load_character("BaseCharacter.blend", "base")

    # 2. Check evaluated height
    h = height_now(a)
    assert abs(h - 1.80) < 0.01, f"Expected height ~1.80, got {h:.4f}"

    # 3. Face points forward: mean WORLD y of all vertices used by polygons with material Face > 0.15
    bpy.context.view_layer.update()
    mesh_a = a.body.data
    face_vert_indices = set()
    for poly in mesh_a.polygons:
        if poly.material_index < len(mesh_a.materials) and mesh_a.materials[poly.material_index] is not None:
            if strip(mesh_a.materials[poly.material_index].name) == "Face":
                face_vert_indices.update(poly.vertices)

    assert len(face_vert_indices) > 0, "No vertices found with material 'Face'"
    mw = a.body.matrix_world
    mean_world_y = sum((mw @ mesh_a.vertices[idx].co).y for idx in face_vert_indices) / len(face_vert_indices)
    assert mean_world_y > 0.15, f"Expected face mean WORLD y > 0.15, got {mean_world_y:.4f}"

    # 4. Character's right is +X: native(a, a.arm.data.bones["Fist.R"].head_local).x > 0.5
    fist_r_world = native(a, a.arm.data.bones["Fist.R"].head_local)
    assert fist_r_world.x > 0.5, f"Expected Fist.R world x > 0.5, got {fist_r_world.x:.4f}"

    # 5. Load Suit_Male at (1.5, 0, 0), check actions and object names
    b = load_character("Suit_Male.blend", "suit", loc=(1.5, 0, 0))
    expected_actions = {"Idle", "Walk", "Run", "Punch", "PickUp", "Victory"}
    assert expected_actions <= set(b.actions), f"Actions missing from suit: {expected_actions - set(b.actions)}"
    assert b.actions["Idle"] is not a.actions["Idle"], "Expected separate Action objects for characters a and b"
    for obj in bpy.data.objects:
        assert not obj.name.startswith("CharacterArmature"), f"Object {obj.name} starts with 'CharacterArmature'"
        assert obj.name != "Body", f"Object {obj.name} equals 'Body'"

    # 6. Assign glove material to Fist bones
    m = toon.toon("t_glove", "#1a1d26")
    n = assign(a, m, bones=["Fist.L", "Fist.R"])
    assert n > 50, f"Expected assign to affect > 50 polygons, affected {n}"

    # 7. Take belt part from Casual_Male
    belt = take_part(a, "Casual_Male.blend", "Belt", "belt", toon.toon("t_belt", "#e3b21c"))
    assert len(belt.data.polygons) >= 20, f"Belt has {len(belt.data.polygons)} polygons, expected >= 20"
    arm_mods = [mod for mod in belt.modifiers if mod.type == "ARMATURE"]
    assert len(arm_mods) == 1, f"Belt has {len(arm_mods)} ARMATURE modifiers, expected 1"
    assert arm_mods[0].object == a.arm, f"Belt ARMATURE modifier target is {arm_mods[0].object}, expected {a.arm}"
    assert len(belt.vertex_groups) >= 1, f"Belt has {len(belt.vertex_groups)} vertex groups, expected >= 1"
    for obj in bpy.data.objects:
        assert not obj.name.startswith("CharacterArmature"), f"Object {obj.name} starts with 'CharacterArmature'"
        assert obj.name != "Body", f"Object {obj.name} equals 'Body'"

    # 8. Belt follows the rig: evaluated world position of belt vertex 0 moves > 0.1 m when Body bone moves
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_belt = belt.evaluated_get(depsgraph)
    eval_mesh = eval_belt.to_mesh()
    p0 = (eval_belt.matrix_world @ eval_mesh.vertices[0].co).copy()
    eval_belt.to_mesh_clear()

    a.arm.pose.bones["Body"].location = (0.0, 0.3, 0.0)
    bpy.context.view_layer.update()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_belt = belt.evaluated_get(depsgraph)
    eval_mesh = eval_belt.to_mesh()
    p1 = (eval_belt.matrix_world @ eval_mesh.vertices[0].co).copy()
    eval_belt.to_mesh_clear()

    move_dist = (p1 - p0).length
    assert move_dist > 0.1, f"Belt vertex 0 moved {move_dist:.4f} m, expected > 0.1 m"
    rest(a)

    # 9. Delete hair faces from suit
    k = delete_faces(b, ["Hair"])
    assert k > 1000, f"Expected delete_faces to delete > 1000 faces, deleted {k}"
    b_mats = b.body.data.materials
    for p in b.body.data.polygons:
        if p.material_index < len(b_mats) and b_mats[p.material_index] is not None:
            assert strip(b_mats[p.material_index].name) != "Hair", "Found polygon with stripped material name 'Hair'"

    # 10. Surface points on Torso and Abdomen
    pts = surface_points(a, [(0.0, 1.6), (0.1, 1.5)], bones=["Torso", "Abdomen"])
    assert len(pts) == 2, f"Expected 2 surface points, got {len(pts)}"
    for i, pt in enumerate(pts):
        assert -0.30 <= pt.y <= -0.15, f"pts[{i}].y = {pt.y:.4f}, expected between -0.30 and -0.15"

    # 11. Set Idle action on b at frame 1
    set_action(b, "Idle", 1)

    # 12. Render one still
    C.sky(C.hex_rgb("#808890"))
    C.sun("key", energy=3.0)
    cam = C.camera("cam", (0.75, 5.0, 1.0), (0.75, 0, 0.9), lens=40)
    bpy.context.scene.camera = cam

    out_dir = os.path.join(ROOT, "output", "tests", "E1")
    os.makedirs(out_dir, exist_ok=True)
    still_path = os.path.join(out_dir, "still.png")

    C.render_settings(width=540, height=960, quality="final", video=False, frame_end=1, filepath=still_path)
    bpy.ops.render.render(write_still=True)

    assert os.path.isfile(still_path), f"Still file not found: {still_path}"
    assert os.path.getsize(still_path) > 0, f"Still file is empty: {still_path}"

    # 13. Pass
    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
