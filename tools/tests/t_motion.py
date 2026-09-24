"""Test for character motion: NLA actions, walking, turning (Task F2)."""
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
from kit.qchar import load_character
from kit.motion import foot_track, ground_speed, key_root, play, turn_to, walk_to


def main() -> None:
    C.reset_scene()
    qc = load_character("Suit_Male.blend", "walker")

    play(qc, "Idle", 1, 30)
    end, steps = walk_to(qc, 10, (0, 3.0))

    sp = ground_speed(qc, "Walk")

    scene = bpy.context.scene

    # (a) at frame end the root world position is within 0.001 m of (0, 3.0); 30 < end − 10 < 80;
    scene.frame_set(end)
    bpy.context.view_layer.update()
    root_pos = qc.root.matrix_world.translation
    root_dist = math.hypot(root_pos.x - 0.0, root_pos.y - 3.0)
    assert root_dist < 0.001, (
        f"Assertion (a) failed: root position at end ({root_pos.x:.4f}, {root_pos.y:.4f}) "
        f"is {root_dist:.4f} m from (0, 3.0)"
    )
    walk_frames = end - 10
    assert 30 < walk_frames < 80, (
        f"Assertion (a) failed: expected 30 < end - 10 < 80, got {walk_frames} (end={end})"
    )

    # (b) foot lock — for every f in 17 … end − 2: lo = the foot (Foot.L / Foot.R) with the lower WORLD z at
    # f; if the same foot is also the lower one at f + 1, its horizontal world displacement between f and f + 1 is
    # < 0.006 m (print the largest value);
    pos_L: dict[int, Vector] = {}
    pos_R: dict[int, Vector] = {}
    for f in range(17, end):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        pos_L[f] = (qc.arm.matrix_world @ qc.arm.pose.bones["Foot.L"].head).copy()
        pos_R[f] = (qc.arm.matrix_world @ qc.arm.pose.bones["Foot.R"].head).copy()

    max_lo_disp = 0.0
    checked_count = 0
    for f in range(17, end - 1):
        lo_f = "Foot.L" if pos_L[f].z <= pos_R[f].z else "Foot.R"
        lo_next = "Foot.L" if pos_L[f + 1].z <= pos_R[f + 1].z else "Foot.R"
        if lo_f == lo_next:
            checked_count += 1
            curr_pos = pos_L[f] if lo_f == "Foot.L" else pos_R[f]
            next_pos = pos_L[f + 1] if lo_f == "Foot.L" else pos_R[f + 1]
            disp = math.hypot(next_pos.x - curr_pos.x, next_pos.y - curr_pos.y)
            if disp > max_lo_disp:
                max_lo_disp = disp
            assert disp < 0.006, (
                f"Assertion (b) failed: {lo_f} horizontal displacement at frame {f}->{f+1} "
                f"is {disp:.4f} m >= 0.006 m"
            )

    assert checked_count > 0, "Assertion (b) failed: no frames had the same lower foot"

    # (c) len(steps) >= 3, strictly increasing, consecutive gaps between 10 and 20 frames;
    assert len(steps) >= 3, f"Assertion (c) failed: expected len(steps) >= 3, got {len(steps)}: {steps}"
    for i in range(len(steps) - 1):
        assert steps[i] < steps[i + 1], (
            f"Assertion (c) failed: steps not strictly increasing at index {i}: {steps[i]} >= {steps[i+1]}"
        )
        gap = steps[i + 1] - steps[i]
        assert 10 <= gap <= 20, (
            f"Assertion (c) failed: gap {gap} between steps[{i}]={steps[i]} and steps[{i+1}]={steps[i+1]} "
            f"not in [10, 20]"
        )

    # (d) the top NLA track's strip action is the walker's Idle action;
    ad = qc.arm.animation_data
    assert ad is not None and len(ad.nla_tracks) > 0, "Assertion (d) failed: no NLA tracks found on qc.arm"
    top_track = ad.nla_tracks[-1]
    assert len(top_track.strips) > 0, f"Assertion (d) failed: top track {top_track.name} has no strips"
    top_strip = top_track.strips[0]
    expected_idle = qc.actions["Idle"]
    assert top_strip.action == expected_idle, (
        f"Assertion (d) failed: expected top NLA strip action to be {expected_idle.name}, "
        f"got {top_strip.action.name if top_strip.action else None}"
    )

    # (e) turn_to(qc, end + 12, 90); at end + 20 the root heading is 90° ± 0.5.
    turn_to(qc, end + 12, 90)
    scene.frame_set(end + 20)
    bpy.context.view_layer.update()
    actual_heading = math.degrees(qc.root.rotation_euler.z)
    assert abs(actual_heading - 90.0) <= 0.5, (
        f"Assertion (e) failed: expected root heading ~90.0 at frame {end + 20}, got {actual_heading:.2f}"
    )

    # Render frames 12, 24, 36, end, end + 20 (camera (4.0, 1.5, 1.1) → (0, 1.5, 0.9), lens 35, 540x960, store_night, floor) to output/tests/F2/.
    look.store_night(target=(0.0, 1.5, 0.9))
    look.floor()
    cam = C.camera("cam", (4.0, 1.5, 1.1), (0.0, 1.5, 0.9), lens=35.0)
    scene.camera = cam

    out_dir = os.path.join(ROOT, "output", "tests", "F2")
    os.makedirs(out_dir, exist_ok=True)

    render_frames = [12, 24, 36, end, end + 20]
    for rf in render_frames:
        scene.frame_set(rf)
        bpy.context.view_layer.update()
        still_path = os.path.join(out_dir, f"motion_{rf}.png")
        C.render_settings(width=540, height=960, quality="final", video=False, frame_end=1, filepath=still_path)
        scene.render.filepath = still_path
        bpy.ops.render.render(write_still=True)
        assert os.path.isfile(still_path), f"Still not found: {still_path}"
        assert os.path.getsize(still_path) > 0, f"Still is empty: {still_path}"

    print(f"[motion] ground_speed = {sp:.4f} m/frame", flush=True)
    print(f"[motion] largest planted foot speed = {max_lo_disp:.4f} m/frame", flush=True)
    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
