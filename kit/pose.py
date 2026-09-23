"""Pose library, pose application, keyframing, and kinematics helpers (Task T3)."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Sequence

import bpy
from mathutils import Matrix, Quaternion, Vector

from kit import rig
from studio import core as C

# Torso orientation constants
LEAN_SIGN: int = -1
TWIST_SIGN: int = 1
SIDE_SIGN: int = -1
LEAN_AXIS: str = "X"
TWIST_AXIS: str = "Y"
SIDE_AXIS: str = "Z"


@dataclass
class Pose:
    hips: tuple = (0, 0, 0)          # offset of hips_ctrl from its rest, metres (x right, y fwd, z up)
    lean: float = 0                  # torso pitch, deg, + = forward
    twist: float = 0                 # torso yaw, deg, + = chest turns toward the character's LEFT
    side: float = 0                  # torso roll, deg, + = bends toward the character's RIGHT
    grip: tuple = (0, 0.35, 1.05)    # where the RIGHT hand holds the sword (= grip.R head), relative to mover
    blade: tuple = (35, 0, 0)        # (pitch, yaw, roll) deg of the blade direction, see below
    two_hands: bool = True           # left hand on grip.L?
    feet: tuple = ((0.12, 0.22), (-0.12, -0.22))   # (right foot x,y), (left foot x,y) relative to mover
    head: tuple = (0, 0)             # head (pitch, yaw) deg, + pitch = look down, + yaw = look left


def blade_quat(pitch: float, yaw: float, roll: float) -> Quaternion:
    """Quaternion rotation for blade direction."""
    rx = Matrix.Rotation(math.radians(pitch), 4, "X")
    rz = Matrix.Rotation(math.radians(-yaw), 4, "Z")
    ry = Matrix.Rotation(math.radians(roll), 4, "Y")
    return (rz @ rx @ ry).to_quaternion()


POSES: dict[str, Pose] = {
    "rest": Pose(
        hips=(0, 0, 0),
        lean=0,
        twist=0,
        grip=(0.26, 0.06, 0.94),
        blade=(-80, 0, 0),
        two_hands=False,
        feet=((0.11, 0), (-0.11, 0)),
    ),
    "sheathed": Pose(
        hips=(0, 0, 0),
        lean=5,
        twist=0,
        grip=(-0.16, 0.313, 1.013),
        blade=(-12, 180, 0),
        two_hands=False,
        feet=((0.14, 0.12), (-0.14, -0.12)),
    ),
    "chudan": Pose(
        hips=(0, 0, -0.08),
        lean=8,
        twist=0,
        grip=(0.02, 0.34, 1.05),
        blade=(35, 0, 0),
        two_hands=True,
        feet=((0.12, 0.22), (-0.12, -0.22)),
    ),
    "jodan": Pose(
        hips=(0, -0.05, -0.05),
        lean=-6,
        twist=0,
        grip=(0.02, 0.08, 1.72),
        blade=(130, 0, 0),
        two_hands=True,
        feet=((0.12, 0.22), (-0.12, -0.22)),
    ),
    "overhead_hit": Pose(
        hips=(0, 0.15, -0.20),
        lean=22,
        twist=0,
        grip=(0.0, 0.55, 1.15),
        blade=(-10, 0, 0),
        two_hands=True,
        feet=((0.12, 0.50), (-0.12, -0.20)),
    ),
    "slash_windup": Pose(
        hips=(0, -0.05, -0.08),
        lean=0,
        twist=-30,
        grip=(0.32, 0.08, 1.52),
        blade=(115, 40, 0),
        two_hands=True,
        feet=((0.12, 0.22), (-0.12, -0.22)),
    ),
    "slash_hit": Pose(
        hips=(0, 0.10, -0.15),
        lean=15,
        twist=25,
        grip=(-0.22, 0.48, 1.02),
        blade=(-20, -50, 0),
        two_hands=True,
        feet=((0.12, 0.45), (-0.12, -0.20)),
    ),
    "thrust_windup": Pose(
        hips=(0, -0.10, -0.12),
        lean=0,
        twist=-10,
        grip=(0.10, 0.05, 1.10),
        blade=(5, 0, 0),
        two_hands=True,
        feet=((0.12, 0.22), (-0.12, -0.25)),
    ),
    "thrust_hit": Pose(
        hips=(0, 0.28, -0.20),
        lean=18,
        twist=5,
        grip=(0.0, 0.62, 1.25),
        blade=(0, 0, 0),
        two_hands=True,
        feet=((0.12, 0.65), (-0.12, -0.20)),
    ),
    "block_high": Pose(
        hips=(0, 0, -0.10),
        lean=0,
        twist=0,
        grip=(0.25, 0.32, 1.55),
        blade=(10, -80, 0),
        two_hands=True,
        feet=((0.12, 0.22), (-0.12, -0.22)),
    ),
    "block_mid": Pose(
        hips=(0, 0, -0.10),
        lean=5,
        twist=0,
        grip=(0.05, 0.34, 1.00),
        blade=(70, -15, 0),
        two_hands=True,
        feet=((0.12, 0.22), (-0.12, -0.22)),
    ),
    "parry": Pose(
        hips=(0, 0.05, -0.10),
        lean=8,
        twist=20,
        grip=(-0.20, 0.40, 1.20),
        blade=(45, -60, 0),
        two_hands=True,
        feet=((0.12, 0.30), (-0.12, -0.20)),
    ),
    "dodge_side": Pose(
        hips=(-0.30, 0, -0.15),
        lean=5,
        twist=0,
        grip=(-0.10, 0.25, 0.95),
        blade=(25, 0, 0),
        two_hands=True,
        feet=((-0.05, 0.20), (-0.45, -0.15)),
    ),
    "dodge_back": Pose(
        hips=(0, -0.32, -0.10),
        lean=-12,
        twist=0,
        grip=(0.02, 0.00, 1.05),
        blade=(45, 0, 0),
        two_hands=True,
        feet=((0.12, -0.05), (-0.12, -0.55)),
    ),
    "stagger": Pose(
        hips=(0, -0.15, 0),
        lean=-15,
        twist=15,
        grip=(0.30, 0.20, 1.10),
        blade=(20, 50, 0),
        two_hands=False,
        feet=((0.12, 0.10), (-0.12, -0.40)),
    ),
    "iai_follow": Pose(
        hips=(0, 0.10, -0.30),
        lean=25,
        twist=-20,
        grip=(0.45, 0.45, 1.20),
        blade=(0, 80, 0),
        two_hands=False,
        feet=((0.18, 0.55), (-0.15, -0.35)),
    ),
    "kneel": Pose(
        hips=(0, 0.05, -0.50),
        lean=30,
        twist=0,
        grip=(0.30, 0.30, 0.75),
        blade=(-25, 30, 0),
        two_hands=False,
        feet=((0.12, 0.35), (-0.12, -0.45)),
    ),
}


def apply_pose(
    arm: bpy.types.Object,
    pose: Pose,
    mover: tuple[float, float] = (0.0, 0.0),
) -> None:
    """Apply a pose to the armature without calling view_layer.update."""
    arm.pose.bones["mover"].location = (mover[0], mover[1], 0.0)
    arm.pose.bones["hips_ctrl"].location = Vector(pose.hips)

    axis_map = {"X": 0, "Y": 1, "Z": 2}
    for bone_name in ("spine", "chest"):
        pb = arm.pose.bones[bone_name]
        euler = [0.0, 0.0, 0.0]
        euler[axis_map[LEAN_AXIS]] += LEAN_SIGN * math.radians(pose.lean) / 2.0
        euler[axis_map[TWIST_AXIS]] += TWIST_SIGN * math.radians(pose.twist) / 2.0
        euler[axis_map[SIDE_AXIS]] += SIDE_SIGN * math.radians(pose.side) / 2.0
        pb.rotation_euler = tuple(euler)

    arm.pose.bones["head"].rotation_euler = (
        math.radians(pose.head[0]),
        math.radians(pose.head[1]),
        0.0,
    )

    q = blade_quat(*pose.blade)
    d = q @ Vector((0.0, 1.0, 0.0))
    sword_pb = arm.pose.bones["sword"]
    sword_pb.location = Vector(pose.grip) - d * 0.20
    sword_pb.rotation_quaternion = q

    rest_r = arm.data.bones["foot_ik.R"].head_local
    fx_r, fy_r = pose.feet[0]
    arm.pose.bones["foot_ik.R"].location = (
        mover[0] + fx_r - rest_r.x,
        mover[1] + fy_r - rest_r.y,
        0.0,
    )

    rest_l = arm.data.bones["foot_ik.L"].head_local
    fx_l, fy_l = pose.feet[1]
    arm.pose.bones["foot_ik.L"].location = (
        mover[0] + fx_l - rest_l.x,
        mover[1] + fy_l - rest_l.y,
        0.0,
    )

    arm.pose.bones["forearm.L"].constraints["IK"].influence = 1.0 if pose.two_hands else 0.0


def key_pose(
    arm: bpy.types.Object,
    pose: Pose,
    frame: int,
    mover: tuple[float, float] = (0.0, 0.0),
    interp: str = "BEZIER",
) -> None:
    """Apply pose and keyframe all controlled channels at frame."""
    apply_pose(arm, pose, mover=mover)

    arm.pose.bones["mover"].keyframe_insert("location", frame=frame)
    arm.pose.bones["hips_ctrl"].keyframe_insert("location", frame=frame)
    arm.pose.bones["spine"].keyframe_insert("rotation_euler", frame=frame)
    arm.pose.bones["chest"].keyframe_insert("rotation_euler", frame=frame)
    arm.pose.bones["head"].keyframe_insert("rotation_euler", frame=frame)
    arm.pose.bones["sword"].keyframe_insert("location", frame=frame)
    arm.pose.bones["sword"].keyframe_insert("rotation_quaternion", frame=frame)
    arm.pose.bones["foot_ik.R"].keyframe_insert("location", frame=frame)
    arm.pose.bones["foot_ik.L"].keyframe_insert("location", frame=frame)
    arm.pose.bones["forearm.L"].constraints["IK"].keyframe_insert("influence", frame=frame)

    C.set_interp_at(arm, frame, interp)


def hold(
    arm: bpy.types.Object,
    pose: Pose,
    f0: int,
    f1: int,
    mover: tuple[float, float] = (0.0, 0.0),
) -> None:
    """Hold a pose between frames f0 and f1."""
    key_pose(arm, pose, f0, mover=mover, interp="BEZIER")
    key_pose(arm, pose, f1, mover=mover, interp="BEZIER")


def auto_steps(
    arm: bpy.types.Object,
    cues: dict[str, Any],
    step_height: float = 0.10,
) -> None:
    """Add middle step lift keys for moving feet and planted constant keys for stationary feet."""
    cues.setdefault("sfx", [])
    changed_curves: set[bpy.types.FCurve] = set()

    for foot in ("foot_ik.R", "foot_ik.L"):
        data_path = f'pose.bones["{foot}"].location'
        curves: dict[int, bpy.types.FCurve] = {}
        for fc in C.fcurves(arm):
            if fc.data_path == data_path and fc.array_index in (0, 1, 2):
                curves[fc.array_index] = fc

        if 0 not in curves or 1 not in curves or 2 not in curves:
            continue

        fc_x = curves[0]
        fc_y = curves[1]
        fc_z = curves[2]

        frames = sorted({int(round(kp.co.x)) for kp in fc_x.keyframe_points})
        for fa, fb in zip(frames[:-1], frames[1:]):
            if fb - fa < 2:
                continue

            xa = fc_x.evaluate(fa)
            ya = fc_y.evaluate(fa)
            xb = fc_x.evaluate(fb)
            yb = fc_y.evaluate(fb)

            h_dist = math.hypot(xb - xa, yb - ya)
            if h_dist > 0.05:
                mid = round((fa + fb) / 2)
                mid_x = (xa + xb) / 2.0
                mid_y = (ya + yb) / 2.0

                fc_x.keyframe_points.insert(mid, mid_x)
                fc_y.keyframe_points.insert(mid, mid_y)
                fc_z.keyframe_points.insert(mid, step_height)

                changed_curves.add(fc_x)
                changed_curves.add(fc_y)
                changed_curves.add(fc_z)

                cues["sfx"].append({"frame": fb, "sfx": "step", "gain": 0.35})
            else:
                for fc in (fc_x, fc_y, fc_z):
                    for kp in fc.keyframe_points:
                        if abs(kp.co.x - fa) < 0.5:
                            kp.interpolation = "CONSTANT"
                    changed_curves.add(fc)

    for fc in changed_curves:
        fc.update()


def to_local(arm: bpy.types.Object, p: Sequence[float] | Vector) -> Vector:
    """Transform world point to armature-space (character-local) position.

    Mover offsets are NOT subtracted; grip in poses is relative to mover,
    so callers use sword_through(to_local(arm, M) - Vector((mover_x, mover_y, 0)), ...).
    """
    return arm.matrix_world.inverted() @ Vector(p)


def to_world(arm: bpy.types.Object, p: Sequence[float] | Vector) -> Vector:
    """Transform armature-space (character-local) position to world position."""
    return arm.matrix_world @ Vector(p)


def sword_through(
    point_local: Sequence[float] | Vector,
    blade: Sequence[float],
    dist: float,
) -> tuple[float, float, float]:
    """Calculate grip position that makes the blade pass through point_local at dist from butt."""
    q = blade_quat(*blade)
    d = q @ Vector((0.0, 1.0, 0.0))
    butt = Vector(point_local) - d * dist
    grip = butt + d * 0.20
    return (grip.x, grip.y, grip.z)


def reach_ok(arm: bpy.types.Object, pose: Pose) -> float:
    """Check whether the right hand reach is within shoulder arm limits."""
    shoulder = Vector((0.20, 0.0, 1.46)) + Vector(pose.hips)
    dist = (Vector(pose.grip) - shoulder).length
    if dist > 0.52:
        raise ValueError(f"reach {dist:.3f} > 0.52 for grip {pose.grip}")
    return dist


def limb(
    name: str,
    arm: bpy.types.Object,
    bone: str,
    r_head: float,
    r_tail: float,
    mat: bpy.types.Material | None,
) -> bpy.types.Object:
    """Build a limb capsule (cone along bone + sphere joint at head) and attach to bone."""
    b = arm.data.bones[bone]
    head = b.head_local.copy()
    tail = b.tail_local.copy()
    delta = tail - head
    length = delta.length
    mid = (head + tail) * 0.5
    rot_euler = delta.to_track_quat("Z", "Y").to_euler()
    rot_deg = tuple(math.degrees(a) for a in rot_euler)

    c = C.cone(
        name,
        r1=r_head,
        r2=r_tail,
        depth=length,
        loc=tuple(mid),
        rot=rot_deg,
        mat=mat,
    )
    s = C.sphere(
        f"{name}_joint",
        r=r_head,
        loc=tuple(head),
        mat=mat,
    )
    rig.attach(c, arm, bone)
    rig.attach(s, arm, bone)
    return c
