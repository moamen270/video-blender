"""Test for decal face module (Task E3)."""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isdir(os.path.join(ROOT, "studio")):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy
from mathutils import Euler

from studio import core as C
from kit import look
from kit.face import (
    Face,
    EXPRESSIONS,
    build_face,
    set_expression,
    key_mouth,
    blink,
)
from kit.qchar import (
    load_character,
    rest,
    strip,
)


def main() -> None:
    # 1. Reset scene, load BaseCharacter hero, build_face with rest="frown"
    C.reset_scene()
    a = load_character("BaseCharacter.blend", "hero")
    f = build_face(a, rest="frown")

    # 2. Assert 2 eyes + 2 brows, no Face polygons on a.body, 10 mouth objects,
    # and at frame 1 only hero_mouth_frown has hide_render == False.
    assert len(f.eyes) == 2, f"Expected 2 eyes, got {len(f.eyes)}"
    assert set(f.eyes.keys()) == {"L", "R"}, f"Expected eyes keys {{'L', 'R'}}, got {set(f.eyes.keys())}"
    assert len(f.brows) == 2, f"Expected 2 brows, got {len(f.brows)}"
    assert set(f.brows.keys()) == {"L", "R"}, f"Expected brows keys {{'L', 'R'}}, got {set(f.brows.keys())}"

    body_mats = a.body.data.materials
    for p in a.body.data.polygons:
        if p.material_index < len(body_mats) and body_mats[p.material_index] is not None:
            assert strip(body_mats[p.material_index].name) != "Face", "Found polygon on a.body with stripped material 'Face'"

    expected_mouths = {"X", "A", "B", "C", "D", "E", "F", "G", "H", "frown"}
    assert set(f.mouths.keys()) == expected_mouths, f"Expected mouth shapes {expected_mouths}, got {set(f.mouths.keys())}"
    assert len(f.mouths) == 10, f"Expected 10 mouth objects, got {len(f.mouths)}"

    bpy.context.scene.frame_set(1)
    for name, obj in f.mouths.items():
        if name == "frown":
            assert obj.hide_render is False, f"Expected {obj.name} hide_render == False at frame 1"
        else:
            assert obj.hide_render is True, f"Expected {obj.name} hide_render == True at frame 1"

    # 3. Every eye/brow/mouth object's world position y > 0.20 and z between 1.15 and 1.60.
    bpy.context.view_layer.update()
    all_face_objs = [*f.eyes.values(), *f.brows.values(), *f.mouths.values()]
    assert len(all_face_objs) == 14, f"Expected 14 face objects, got {len(all_face_objs)}"
    for obj in all_face_objs:
        wpos = obj.matrix_world.translation
        assert wpos.y > 0.20, f"{obj.name} world y = {wpos.y:.4f}, expected > 0.20"
        assert 1.15 <= wpos.z <= 1.60, f"{obj.name} world z = {wpos.z:.4f}, expected between 1.15 and 1.60"

    # 4. Brow sign: angry gives inner < outer - 0.005; surprised gives inner > outer.
    set_expression(f, "angry")
    bpy.context.view_layer.update()
    for side, brow in f.brows.items():
        c = brow.matrix_world.translation
        mw = brow.matrix_world
        w_verts = [mw @ v.co for v in brow.data.vertices]
        inner_zs = [v.z for v in w_verts if abs(v.x) < abs(c.x)]
        outer_zs = [v.z for v in w_verts if abs(v.x) > abs(c.x)]
        assert len(inner_zs) > 0, f"No inner vertices found for brow {side}"
        assert len(outer_zs) > 0, f"No outer vertices found for brow {side}"
        inner = sum(inner_zs) / len(inner_zs)
        outer = sum(outer_zs) / len(outer_zs)
        assert inner < outer - 0.005, (
            f"Angry brow {side}: expected inner < outer - 0.005, got inner={inner:.4f}, outer={outer:.4f}"
        )

    set_expression(f, "surprised")
    bpy.context.view_layer.update()
    for side, brow in f.brows.items():
        c = brow.matrix_world.translation
        mw = brow.matrix_world
        w_verts = [mw @ v.co for v in brow.data.vertices]
        inner_zs = [v.z for v in w_verts if abs(v.x) < abs(c.x)]
        outer_zs = [v.z for v in w_verts if abs(v.x) > abs(c.x)]
        assert len(inner_zs) > 0, f"No inner vertices found for brow {side}"
        assert len(outer_zs) > 0, f"No outer vertices found for brow {side}"
        inner = sum(inner_zs) / len(inner_zs)
        outer = sum(outer_zs) / len(outer_zs)
        assert inner > outer, (
            f"Surprised brow {side}: expected inner > outer, got inner={inner:.4f}, outer={outer:.4f}"
        )

    # 5. Follows the head: world position of eye L before/after rotating pose bone Head 25°
    bpy.context.view_layer.update()
    eye_l = f.eyes["L"]
    pos_before = eye_l.matrix_world.translation.copy()

    pb_head = a.arm.pose.bones["Head"]
    pb_head.rotation_mode = "QUATERNION"
    pb_head.rotation_quaternion = Euler((math.radians(25.0), 0.0, 0.0)).to_quaternion()
    bpy.context.view_layer.update()

    pos_after = eye_l.matrix_world.translation.copy()
    diff = (pos_after - pos_before).length
    assert diff > 0.02, f"Expected eye L movement > 0.02 m, got {diff:.4f} m"

    rest(a)
    set_expression(f, "neutral")
    bpy.context.view_layer.update()

    # 6. Reset scene, load Suit_Male grinner, build_face with style="grin", rest="X"
    C.reset_scene()
    g = load_character("Suit_Male.blend", "grinner")
    fg = build_face(g, style="grin", rest="X")
    expected_grin_mouths = {"X", "A", "B", "C", "D", "E", "F", "G", "H"}
    assert set(fg.mouths.keys()) == expected_grin_mouths, (
        f"Expected mouth shapes {expected_grin_mouths}, got {set(fg.mouths.keys())}"
    )
    assert len(fg.mouths) == 9, f"Expected 9 mouth objects, got {len(fg.mouths)}"

    # 7. Render stills (540x540) to output/tests/E3/
    out_dir = os.path.join(ROOT, "output", "tests", "E3")
    os.makedirs(out_dir, exist_ok=True)

    look.store_night(target=(0.0, 0.0, 1.4))
    cam = C.camera("cam", (0.0, 1.35, 1.46), (0.0, 0.0, 1.42), lens=50.0)
    bpy.context.scene.camera = cam

    # Grinner expressions (mouth X)
    expr_names = ["neutral", "stern", "angry", "surprised", "suspicious", "smug", "deadpan"]
    for ename in expr_names:
        set_expression(fg, ename)
        key_mouth(fg, 1, "X")
        bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()
        still_path = os.path.join(out_dir, f"expr_{ename}.png")
        C.render_settings(width=540, height=540, quality="final", video=False, frame_end=1, filepath=still_path)
        bpy.context.scene.render.filepath = still_path
        bpy.ops.render.render(write_still=True)
        assert os.path.isfile(still_path), f"Still file not found: {still_path}"
        assert os.path.getsize(still_path) > 0, f"Still file is empty: {still_path}"

    # Grinner mouth shapes (neutral expression)
    set_expression(fg, "neutral")
    mouth_shapes = ["X", "A", "B", "C", "D", "E", "F"]
    for shape in mouth_shapes:
        key_mouth(fg, 1, shape)
        bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()
        still_path = os.path.join(out_dir, f"mouth_{shape}.png")
        C.render_settings(width=540, height=540, quality="final", video=False, frame_end=1, filepath=still_path)
        bpy.context.scene.render.filepath = still_path
        bpy.ops.render.render(write_still=True)
        assert os.path.isfile(still_path), f"Still file not found: {still_path}"
        assert os.path.getsize(still_path) > 0, f"Still file is empty: {still_path}"

    # Rebuild hero (rest frown) and render hero_stern.png and hero_D.png
    C.reset_scene()
    hero = load_character("BaseCharacter.blend", "hero")
    fh = build_face(hero, rest="frown")
    look.store_night(target=(0.0, 0.0, 1.4))
    cam = C.camera("cam", (0.0, 1.35, 1.46), (0.0, 0.0, 1.42), lens=50.0)
    bpy.context.scene.camera = cam

    # hero_stern.png
    set_expression(fh, "stern")
    key_mouth(fh, 1, "frown")
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    still_path = os.path.join(out_dir, "hero_stern.png")
    C.render_settings(width=540, height=540, quality="final", video=False, frame_end=1, filepath=still_path)
    bpy.context.scene.render.filepath = still_path
    bpy.ops.render.render(write_still=True)
    assert os.path.isfile(still_path), f"Still file not found: {still_path}"
    assert os.path.getsize(still_path) > 0, f"Still file is empty: {still_path}"

    # hero_D.png
    set_expression(fh, "neutral")
    key_mouth(fh, 1, "D")
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    still_path = os.path.join(out_dir, "hero_D.png")
    C.render_settings(width=540, height=540, quality="final", video=False, frame_end=1, filepath=still_path)
    bpy.context.scene.render.filepath = still_path
    bpy.ops.render.render(write_still=True)
    assert os.path.isfile(still_path), f"Still file not found: {still_path}"
    assert os.path.getsize(still_path) > 0, f"Still file is empty: {still_path}"

    # 8. Test PASS
    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
