"""Test for pose library, kinematics, and character pose rendering (Task T3)."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isdir(os.path.join(ROOT, "studio")):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy

from kit import pose, rig, toon
from studio import core as C


def main() -> None:
    C.reset_scene()
    arm = rig.build_armature("ronin")
    rig.calibrate_poles(arm)

    grey_mat = toon.toon("grey", "#b8bec9")
    tip_mat = toon.toon("red_tip", "#e74c3c")

    # Capsule body on deform bones (except pelvis/spine/chest/neck/head)
    limb_specs = [
        ("upperarm.R", 0.075, 0.10),
        ("forearm.R", 0.045, 0.04),
        ("upperarm.L", 0.075, 0.10),
        ("forearm.L", 0.045, 0.04),
        ("thigh.R", 0.11, 0.15),
        ("shin.R", 0.15, 0.17),
        ("foot.R", 0.05, 0.05),
        ("thigh.L", 0.11, 0.15),
        ("shin.L", 0.15, 0.17),
        ("foot.L", 0.05, 0.05),
    ]

    for bone_name, r_head, r_tail in limb_specs:
        pose.limb(f"ronin_{bone_name}", arm, bone_name, r_head, r_tail, grey_mat)

    # Head, chest, sword mesh parts
    head_mesh = C.sphere("ronin_head", r=0.14, loc=(0, 0, 1.70), mat=grey_mat)
    rig.attach(head_mesh, arm, "head")

    chest_mesh = C.cone("ronin_chest", r1=0.2, r2=0.17, depth=0.45, loc=(0, 0, 1.27), mat=grey_mat)
    rig.attach(chest_mesh, arm, "chest")

    sword_mesh = C.cube("ronin_sword", size=1.0, scale=(0.02, 1.05, 0.04), loc=(0, 0.525, 0), mat=grey_mat)
    rig.attach(sword_mesh, arm, "sword")

    sword_tip = C.sphere("sword_tip", r=0.03, loc=(0, 1.05, 0), mat=tip_mat)
    rig.attach(sword_tip, arm, "sword")

    # Add outline on all mesh parts
    for obj in list(bpy.data.objects):
        if obj.type == "MESH":
            toon.add_outline(obj)

    # Sign tests
    bpy.context.view_layer.update()
    rest_head_y = arm.pose.bones["head"].head.y

    # Lean sign test
    pose.apply_pose(arm, pose.Pose(lean=20))
    bpy.context.view_layer.update()
    head_y = arm.pose.bones["head"].head.y
    if not (head_y > rest_head_y + 0.1):
        raise AssertionError(
            f"lean=20 sign test failed: measured head world y = {head_y:.4f}, expected > {rest_head_y + 0.1:.4f}"
        )

    # Twist sign test
    pose.apply_pose(arm, pose.Pose(twist=30))
    bpy.context.view_layer.update()
    upperarm_y = arm.pose.bones["upperarm.R"].head.y
    if not (upperarm_y > 0.05):
        raise AssertionError(
            f"twist=30 sign test failed: measured upperarm.R head y = {upperarm_y:.4f}, expected > 0.05"
        )

    # Side sign test
    pose.apply_pose(arm, pose.Pose(side=15))
    bpy.context.view_layer.update()
    head_x = arm.pose.bones["head"].head.x
    if not (head_x > 0.1):
        raise AssertionError(
            f"side=15 sign test failed: measured head world x = {head_x:.4f}, expected > 0.1"
        )

    # Render scene setup
    C.sky(C.hex_rgb("#20242e"))
    C.sun("key", energy=3.0, rot=(50, 0, 30))
    cam = C.camera("cam", (2.2, 3.2, 1.4), (0, 0, 1.0), lens=35)
    bpy.context.scene.camera = cam
    C.render_settings(width=540, height=960, frame_end=1, quality="final", video=False)

    out_dir = os.path.join(ROOT, "output", "tests", "T3")
    os.makedirs(out_dir, exist_ok=True)

    failed_poses: list[tuple[str, float]] = []

    for name, p in pose.POSES.items():
        pose.apply_pose(arm, p)
        bpy.context.view_layer.update()

        wrist = arm.pose.bones["forearm.R"].tail
        grip = arm.pose.bones["grip.R"].head
        err = (wrist - grip).length
        print(f"[test] {name}: grip err {err:.3f}", flush=True)

        if name not in ("rest", "sheathed") and err > 0.03:
            failed_poses.append((name, err))

        still_path = os.path.join(out_dir, f"{name}.png")
        bpy.context.scene.render.filepath = still_path
        bpy.ops.render.render(write_still=True)

    if failed_poses:
        print(f"[test] {len(failed_poses)} poses failed grip reach check (err > 0.03):", flush=True)
        for name, err in failed_poses:
            p = pose.POSES[name]
            try:
                d = pose.reach_ok(arm, p)
                print(f"[test]   {name}: grip err {err:.3f}, reach_ok {d:.3f}", flush=True)
            except ValueError as ex:
                print(f"[test]   {name}: grip err {err:.3f}, reach_ok error: {ex}", flush=True)
        raise AssertionError(f"Poses failed grip reach test: {[n for n, _ in failed_poses]}")

    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
