"""Test for hand reach, hold, release, and throw (Task G4)."""
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
from mathutils import Vector

from studio import core as C
from kit import look
from kit import toon
from kit.qchar import load_character
from kit.motion import hold, play, reach, release, setup_ik, throw


def main() -> None:
    C.reset_scene()
    qc = load_character("BaseCharacter.blend", "hero")
    play(qc, "Idle", 1, 100)
    setup_ik(qc)

    target = Vector((0.35, 0.45, 1.0))
    reach(qc, "R", target, 20, 40)

    scene = bpy.context.scene

    # Frame 30: world head of Fist.R is within 0.03 m of the target
    scene.frame_set(30)
    bpy.context.view_layer.update()
    fist_r_head = (qc.arm.matrix_world @ qc.arm.pose.bones["Fist.R"].head).copy()
    reach_dist = (fist_r_head - target).length
    print(f"[reach] measured reach distance at frame 30 = {reach_dist:.4f} m", flush=True)
    assert reach_dist < 0.03, (
        f"Assertion failed: Fist.R head at frame 30 is {reach_dist:.4f} m from target (expected < 0.03 m)"
    )

    # Frame 1 and 50: constraint influence is 0
    scene.frame_set(1)
    bpy.context.view_layer.update()
    pb_r = qc.arm.pose.bones["LowerArm.R"]
    con_r = next(c for c in pb_r.constraints if c.type == "IK")
    assert abs(con_r.influence - 0.0) < 1e-4, (
        f"Assertion failed: expected constraint influence 0 at frame 1, got {con_r.influence}"
    )

    scene.frame_set(50)
    bpy.context.view_layer.update()
    assert abs(con_r.influence - 0.0) < 1e-4, (
        f"Assertion failed: expected constraint influence 0 at frame 50, got {con_r.influence}"
    )

    # Box prop at (0.35, 0.45, 1.0)
    box = C.cube("box", size=0.1, loc=(0.35, 0.45, 1.0), mat=toon.toon("box_mat", "#e3b21c"))
    held = hold(qc, box, "R", 30)

    # Frame 30 measurements
    scene.frame_set(30)
    bpy.context.view_layer.update()
    fist_30 = (qc.arm.matrix_world @ qc.arm.pose.bones["Fist.R"].head).copy()
    held_pos_30 = held.matrix_world.translation.copy()
    dist_30 = (held_pos_30 - fist_30).length

    # Frame 45: held moved with the hand (distance to Fist.R head same as frame 30 ± 0.01) and box is hidden
    scene.frame_set(45)
    bpy.context.view_layer.update()
    fist_45 = (qc.arm.matrix_world @ qc.arm.pose.bones["Fist.R"].head).copy()
    held_pos_45 = held.matrix_world.translation.copy()
    dist_45 = (held_pos_45 - fist_45).length
    dist_diff = abs(dist_45 - dist_30)
    assert dist_diff < 0.01, (
        f"Assertion failed: distance to Fist.R head changed by {dist_diff:.4f} m (frame 30: {dist_30:.4f}, frame 45: {dist_45:.4f})"
    )
    assert box.hide_render is True, "Assertion failed: expected box to be hidden at frame 45"
    assert held.hide_render is False, "Assertion failed: expected held to be visible at frame 45"

    # release(held, 45) leaves a visible copy where the hand was
    box2 = release(held, 45)
    scene.frame_set(45)
    bpy.context.view_layer.update()
    box2_pos_45 = box2.matrix_world.translation.copy()
    rel_pos_diff = (box2_pos_45 - held_pos_45).length
    assert rel_pos_diff < 0.001, (
        f"Assertion failed: box2 position {box2_pos_45} differs from held {held_pos_45} by {rel_pos_diff:.4f} m"
    )
    assert box2.hide_render is False, "Assertion failed: expected box2 to be visible at frame 45"
    assert held.hide_render is True, "Assertion failed: expected held to be hidden at frame 45"

    # throw(box2, 50, 60, …) passes through the apex
    p0 = box2_pos_45
    p1 = Vector((0.0, 1.5, 0.5))
    arc = 0.25
    throw(box2, 50, 60, p0, p1, arc=arc, spin=720.0)

    # Apex is at midpoint frame 55
    scene.frame_set(55)
    bpy.context.view_layer.update()
    pos_55 = box2.matrix_world.translation.copy()
    chord_mid = 0.5 * (p0 + p1)
    expected_apex = chord_mid + Vector((0.0, 0.0, arc))
    apex_err = (pos_55 - expected_apex).length
    assert apex_err < 0.001, (
        f"Assertion failed: box2 at frame 55 is at {pos_55}, expected apex {expected_apex} (err {apex_err:.4f})"
    )

    # Render frames 1, 30, 45 to output/tests/G4/
    look.store_night(target=(0.0, 0.5, 1.0))
    look.floor()
    cam = C.camera("cam", (1.6, 2.8, 1.3), (0.2, 0.4, 1.0), lens=40.0)
    scene.camera = cam

    out_dir = os.path.join(ROOT, "output", "tests", "G4")
    os.makedirs(out_dir, exist_ok=True)

    render_frames = [1, 30, 45]
    for rf in render_frames:
        scene.frame_set(rf)
        bpy.context.view_layer.update()
        still_path = os.path.join(out_dir, f"reach_{rf}.png")
        C.render_settings(width=540, height=960, quality="final", video=False, frame_end=1, filepath=still_path)
        scene.render.filepath = still_path
        bpy.ops.render.render(write_still=True)
        assert os.path.isfile(still_path), f"Still not found: {still_path}"
        assert os.path.getsize(still_path) > 0, f"Still is empty: {still_path}"

    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
