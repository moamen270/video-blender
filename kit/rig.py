"""Armature rig, IK constraints, pole calibration, and bone attachment (Task T2)."""
from __future__ import annotations

import math
from typing import Sequence

import bpy
from mathutils import Matrix, Vector

BoneEntry = tuple[str, tuple[float, float, float], tuple[float, float, float], str | None, bool, bool]

BONES: list[BoneEntry] = [
    # Control bones (11)
    ("mover", (0.0, 0.0, 0.0), (0.0, 0.2, 0.0), None, False, False),
    ("hips_ctrl", (0.0, 0.0, 0.95), (0.0, 0.2, 0.95), "mover", False, False),
    ("sword", (0.0, 0.0, 0.0), (0.0, 1.05, 0.0), "mover", False, False),
    ("grip.R", (0.0, 0.20, 0.0), (0.0, 0.30, 0.0), "sword", False, False),
    ("grip.L", (0.0, 0.06, 0.0), (0.0, 0.16, 0.0), "sword", False, False),
    ("foot_ik.R", (0.11, 0.0, 0.08), (0.11, 0.2, 0.08), None, False, False),
    ("foot_ik.L", (-0.11, 0.0, 0.08), (-0.11, 0.2, 0.08), None, False, False),
    ("pole_arm.R", (0.35, -0.5, 1.2), (0.35, -0.3, 1.2), "mover", False, False),
    ("pole_arm.L", (-0.35, -0.5, 1.2), (-0.35, -0.3, 1.2), "mover", False, False),
    ("pole_leg.R", (0.11, 0.6, 0.5), (0.11, 0.8, 0.5), "mover", False, False),
    ("pole_leg.L", (-0.11, 0.6, 0.5), (-0.11, 0.8, 0.5), "mover", False, False),
    # Deform bones (15)
    ("pelvis", (0.0, 0.0, 0.95), (0.0, 0.0, 1.05), "hips_ctrl", False, True),
    ("spine", (0.0, 0.0, 1.05), (0.0, 0.0, 1.28), "pelvis", True, True),
    ("chest", (0.0, 0.0, 1.28), (0.0, 0.0, 1.50), "spine", True, True),
    ("neck", (0.0, 0.0, 1.50), (0.0, 0.0, 1.58), "chest", True, True),
    ("head", (0.0, 0.0, 1.58), (0.0, 0.0, 1.84), "neck", True, True),
    ("upperarm.R", (0.20, 0.0, 1.46), (0.24, -0.03, 1.18), "chest", False, True),
    ("forearm.R", (0.24, -0.03, 1.18), (0.26, 0.06, 0.94), "upperarm.R", True, True),
    ("upperarm.L", (-0.20, 0.0, 1.46), (-0.24, -0.03, 1.18), "chest", False, True),
    ("forearm.L", (-0.24, -0.03, 1.18), (-0.26, 0.06, 0.94), "upperarm.L", True, True),
    ("thigh.R", (0.11, 0.0, 0.95), (0.11, 0.03, 0.52), "pelvis", False, True),
    ("shin.R", (0.11, 0.03, 0.52), (0.11, 0.0, 0.08), "thigh.R", True, True),
    ("foot.R", (0.11, 0.0, 0.08), (0.11, 0.16, 0.08), "shin.R", True, True),
    ("thigh.L", (-0.11, 0.0, 0.95), (-0.11, 0.03, 0.52), "pelvis", False, True),
    ("shin.L", (-0.11, 0.03, 0.52), (-0.11, 0.0, 0.08), "thigh.L", True, True),
    ("foot.L", (-0.11, 0.0, 0.08), (-0.11, 0.16, 0.08), "shin.L", True, True),
]


def build_armature(name: str) -> bpy.types.Object:
    """Create and configure the samurai character armature object."""
    arm_data = bpy.data.armatures.new(name + "_arm")
    arm = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)

    bpy.ops.object.mode_set(mode="EDIT")
    for b_name, head, tail, parent_name, connect, deform in BONES:
        eb = arm_data.edit_bones.new(b_name)
        eb.head = Vector(head)
        eb.tail = Vector(tail)
        eb.roll = 0.0
        eb.use_deform = deform
        if parent_name is not None:
            eb.parent = arm_data.edit_bones[parent_name]
            eb.use_connect = connect
    bpy.ops.object.mode_set(mode="OBJECT")

    for pb in arm.pose.bones:
        if pb.name == "sword":
            pb.rotation_mode = "QUATERNION"
        else:
            pb.rotation_mode = "XYZ"

    # IK constraints
    ik_configs = [
        ("forearm.R", "grip.R", "pole_arm.R"),
        ("forearm.L", "grip.L", "pole_arm.L"),
        ("shin.R", "foot_ik.R", "pole_leg.R"),
        ("shin.L", "foot_ik.L", "pole_leg.L"),
    ]
    for bone_name, subtarget, pole_subtarget in ik_configs:
        con = arm.pose.bones[bone_name].constraints.new("IK")
        con.name = "IK"
        con.target = arm
        con.subtarget = subtarget
        con.pole_target = arm
        con.pole_subtarget = pole_subtarget
        con.chain_count = 2

    # COPY_ROTATION constraints for feet
    cr_configs = [
        ("foot.R", "foot_ik.R"),
        ("foot.L", "foot_ik.L"),
    ]
    for bone_name, subtarget in cr_configs:
        con = arm.pose.bones[bone_name].constraints.new("COPY_ROTATION")
        con.name = "COPY_ROTATION"
        con.target = arm
        con.subtarget = subtarget
        con.target_space = "WORLD"
        con.owner_space = "WORLD"

    return arm


def calibrate_poles(arm: bpy.types.Object) -> dict[str, tuple[float, float]]:
    """Calibrate IK pole angles for arms and legs.

    Returns a dict mapping bone name to (angle_deg, error_m).
    """
    results: dict[str, tuple[float, float]] = {}
    sword_pb = arm.pose.bones["sword"]

    configs: list[tuple[str, str | None]] = [
        ("forearm.R", "grip.R"),
        ("forearm.L", "grip.L"),
        ("shin.R", None),
        ("shin.L", None),
    ]

    for bone_name, grip_bone in configs:
        if grip_bone is not None:
            wrist_rest = arm.data.bones[bone_name].tail_local
            grip_rest_head = arm.data.bones[grip_bone].head_local
            sword_pb.location = wrist_rest - grip_rest_head
            sword_pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        else:
            sword_pb.location = (0.0, 0.0, 0.0)
            sword_pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)

        con = arm.pose.bones[bone_name].constraints["IK"]
        best_err = float("inf")
        best_deg = 0.0
        rest_joint = arm.data.bones[bone_name].head_local

        for deg in [-180.0, -90.0, 0.0, 90.0]:
            con.pole_angle = math.radians(deg)
            bpy.context.view_layer.update()
            joint_pos = arm.pose.bones[bone_name].head
            err = (joint_pos - rest_joint).length
            if err < best_err:
                best_err = err
                best_deg = deg

        coarse_best = best_deg
        start_deg = int(round(coarse_best - 45))
        end_deg = int(round(coarse_best + 45))
        for deg_int in range(start_deg, end_deg + 1):
            deg = float(deg_int)
            con.pole_angle = math.radians(deg)
            bpy.context.view_layer.update()
            joint_pos = arm.pose.bones[bone_name].head
            err = (joint_pos - rest_joint).length
            if err < best_err:
                best_err = err
                best_deg = deg

        con.pole_angle = math.radians(best_deg)
        bpy.context.view_layer.update()
        results[bone_name] = (best_deg, best_err)
        print(f"[rig] pole {bone_name} = {best_deg:.1f} (err {best_err:.3f})", flush=True)

    sword_pb.location = (0.0, 0.0, 0.0)
    sword_pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    return results


def set_left_hand(arm: bpy.types.Object, frame: int, on_grip: bool) -> None:
    """Key the influence of forearm.L IK constraint."""
    con = arm.pose.bones["forearm.L"].constraints["IK"]
    con.influence = 1.0 if on_grip else 0.0
    con.keyframe_insert("influence", frame=frame)


def attach(obj: bpy.types.Object, arm: bpy.types.Object, bone_name: str) -> None:
    """Parent an object to a bone without moving it (precondition: arm at origin, rest pose)."""
    bpy.context.view_layer.update()
    pb = arm.pose.bones[bone_name]
    m = arm.matrix_world @ pb.matrix @ Matrix.Translation((0.0, pb.bone.length, 0.0))
    basis = obj.matrix_world.copy()
    obj.parent = arm
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    obj.matrix_parent_inverse = m.inverted()
    obj.matrix_basis = basis
