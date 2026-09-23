"""Test for armature and IK rig (Task T2)."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isdir(os.path.join(ROOT, "studio")):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy
from mathutils import Vector

from kit import rig
from studio import core as C


def main() -> None:
    C.reset_scene()
    arm = rig.build_armature("test")
    angles = rig.calibrate_poles(arm)

    # Bone count and names check
    expected_names = [b[0] for b in rig.BONES]
    assert len(arm.data.bones) == 26, f"Expected 26 bones, got {len(arm.data.bones)}"
    actual_names = list(arm.data.bones.keys())
    missing = set(expected_names) - set(actual_names)
    extra = set(actual_names) - set(expected_names)
    assert set(actual_names) == set(expected_names), (
        f"Bone names do not match expected: missing={missing}, extra={extra}"
    )
    print(f"[test] bone count: {len(arm.data.bones)}", flush=True)

    # Pole calibration error check
    for bone_name, (angle, err) in angles.items():
        print(f"[test] pole {bone_name}: angle={angle:.1f} deg, err={err:.4f} m", flush=True)
        assert err <= 0.01, f"Calibration error for {bone_name} too large: {err} > 0.01"

    # IK reach test
    target = Vector((0.25, 0.45, 1.3))
    grip_rest_head = arm.data.bones["grip.R"].head_local
    sword_pb = arm.pose.bones["sword"]
    sword_pb.location = target - grip_rest_head
    sword_pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    wrist_pos = arm.pose.bones["forearm.R"].tail
    reach_err = (wrist_pos - target).length
    print(f"[test] IK reach error: {reach_err:.4f} m", flush=True)
    assert reach_err <= 0.02, f"IK reach error too large: {reach_err} > 0.02"

    # Reset sword before foot test
    sword_pb.location = (0.0, 0.0, 0.0)
    sword_pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # Foot test
    foot_ik_pb = arm.pose.bones["foot_ik.R"]
    foot_ik_pb.location.y += 0.3
    bpy.context.view_layer.update()

    bone_y_z = arm.pose.bones["foot.R"].matrix.col[1].z
    print(f"[test] foot.R Y axis Z component: {bone_y_z:.4f}", flush=True)
    assert abs(bone_y_z) < 0.05, f"Foot not horizontal: abs({bone_y_z}) >= 0.05"

    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
