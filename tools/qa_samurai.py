"""Samurai animation QA checks (Task T10).

Runs inside Blender headless on the built scene:
    blender -b output/vN/scene.blend --python tools/qa_samurai.py -- --cues projects/samurai/cues.json --out output/vN/qa.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import Any

import bpy
from mathutils import Vector


def wpos(arm: bpy.types.Object, bone: str, attr: str = "head") -> Vector:
    """Helper: world position of a bone head or tail."""
    return arm.matrix_world @ getattr(arm.pose.bones[bone], attr)


def blade(arm: bpy.types.Object) -> tuple[Vector, Vector]:
    """Helper: world positions of blade start (0.26 m) and tip (1.05 m)."""
    pb = arm.pose.bones["sword"]
    a = arm.matrix_world @ (pb.matrix @ Vector((0.0, 0.26, 0.0)))
    b = arm.matrix_world @ (pb.matrix @ Vector((0.0, 1.05, 0.0)))
    return a, b


def seg_dist(p: Vector, a: Vector, b: Vector) -> float:
    """Helper: distance from point p to segment ab (clamp t to [0, 1])."""
    ab = b - a
    l2 = ab.dot(ab)
    if l2 == 0.0:
        return (p - a).length
    t = max(0.0, min(1.0, (p - a).dot(ab) / l2))
    proj = a + ab * t
    return (p - proj).length


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Samurai QA checks")
    parser.add_argument("--cues", required=True, help="Path to cues.json")
    parser.add_argument("--out", required=True, help="Path to output qa.json")
    args = parser.parse_args(argv)

    with open(args.cues, "r", encoding="utf-8") as f:
        cues: dict[str, Any] = json.load(f)

    ronin = bpy.data.objects["ronin"]
    warlord = bpy.data.objects["warlord"]
    arms = {"ronin": ronin, "warlord": warlord}
    scene = bpy.context.scene

    results: list[dict[str, Any]] = []

    def check(name: str, frame: int, value: float, limit: float | int, ok: bool) -> None:
        results.append({
            "check": name,
            "frame": frame,
            "value": round(value, 4),
            "limit": limit,
            "ok": bool(ok),
        })

    # 1 Contact: for each contact in cues['contacts']
    for c in cues["contacts"]:
        scene.frame_set(c["frame"])
        M = Vector(c["point"])
        sides = [c["attacker"], c["defender"]] if c["kind"] == "clash" else [c["attacker"]]
        for s in sides:
            d = seg_dist(M, *blade(arms[s]))
            check(f"contact {c['id']} {s}", c["frame"], d, 0.03, d <= 0.03)

    # 2 Grip: frame list
    grip_frames = set([c["frame"] for c in cues["contacts"]] + list(range(97, 601, 6)))

    # 3 Foot slide: tracking state
    prev_pos: dict[tuple[str, str], Vector] = {}
    prev_z: dict[tuple[str, str], float] = {}
    slide_counts: dict[tuple[str, str], int] = {
        (name, foot): 0 for name in ("ronin", "warlord") for foot in ("foot.R", "foot.L")
    }

    # 4 Pass-through: tracking state
    passthrough_failures = 0

    # 5 Dead time: tracking state
    prev_bone_heads: dict[str, dict[str, Vector]] = {}
    is_still: dict[int, bool] = {}

    # Single pass over frames 1..672
    for f in range(1, 673):
        scene.frame_set(f)

        # 2 Grip check
        if f in grip_frames:
            for name, arm in arms.items():
                grip_r = arm.pose.bones["grip.R"]
                if grip_r.head.x >= -0.05:
                    d = (wpos(arm, "forearm.R", "tail") - wpos(arm, "grip.R")).length
                    check(f"grip.R {name}", f, d, 0.03, d <= 0.03)
                con = arm.pose.bones["forearm.L"].constraints.get("IK")
                if con and con.influence > 0.99:
                    d_left = (wpos(arm, "forearm.L", "tail") - wpos(arm, "grip.L")).length
                    check(f"grip.L {name}", f, d_left, 0.03, d_left <= 0.03)

        # 3 Foot slide check
        for name, arm in arms.items():
            for foot in ("foot.R", "foot.L"):
                p = wpos(arm, foot)
                key = (name, foot)
                if p.z <= 0.085 and prev_pos.get(key) is not None and prev_z.get(key, 1.0) <= 0.085:
                    d = math.hypot(p.x - prev_pos[key].x, p.y - prev_pos[key].y)
                    if d > 0.01:
                        check(f"slide {name} {foot}", f, d, 0.01, False)
                        slide_counts[key] += 1
                prev_pos[key] = p.copy()
                prev_z[key] = p.z

        # 4 No pass-through check
        if 97 <= f <= 600:
            if not (395 <= f <= 410):
                d = (wpos(ronin, "chest") - wpos(warlord, "chest")).length
                if d < 0.45:
                    check("pass-through", f, d, 0.45, False)
                    passthrough_failures += 1

        # 5 Dead time: compute bone head movement
        if f == 96:
            prev_bone_heads["ronin"] = {b: wpos(ronin, b, "head") for b in ronin.pose.bones.keys()}
            prev_bone_heads["warlord"] = {b: wpos(warlord, b, "head") for b in warlord.pose.bones.keys()}
        elif 97 <= f <= 444:
            if "ronin" not in prev_bone_heads:
                scene.frame_set(f - 1)
                prev_bone_heads["ronin"] = {b: wpos(ronin, b, "head") for b in ronin.pose.bones.keys()}
                prev_bone_heads["warlord"] = {b: wpos(warlord, b, "head") for b in warlord.pose.bones.keys()}
                scene.frame_set(f)
            curr_ronin = {b: wpos(ronin, b, "head") for b in ronin.pose.bones.keys()}
            curr_warlord = {b: wpos(warlord, b, "head") for b in warlord.pose.bones.keys()}
            max_r = max((curr_ronin[b] - prev_bone_heads["ronin"][b]).length for b in curr_ronin)
            max_w = max((curr_warlord[b] - prev_bone_heads["warlord"][b]).length for b in curr_warlord)
            is_still[f] = (max_r < 0.005 and max_w < 0.005)
            prev_bone_heads["ronin"] = curr_ronin
            prev_bone_heads["warlord"] = curr_warlord

    # 3 Foot slide summary rows
    for name in ("ronin", "warlord"):
        for foot in ("foot.R", "foot.L"):
            count = slide_counts[(name, foot)]
            check(f"slide {name} {foot} total", 0, count, 0, count == 0)

    # 4 Pass-through summary row
    check("pass-through total", 0, passthrough_failures, 0, passthrough_failures == 0)

    # 5 Dead time: find runs and record failures + summary row
    still_runs: list[tuple[int, int]] = []
    run_start: int | None = None
    for f in range(97, 445):
        if is_still.get(f, False):
            if run_start is None:
                run_start = f
        else:
            if run_start is not None:
                still_runs.append((run_start, f - 1))
                run_start = None
    if run_start is not None:
        still_runs.append((run_start, 444))

    dead_time_failures = 0
    for start_frame, end_frame in still_runs:
        run_len = end_frame - start_frame + 1
        if start_frame >= 406 and end_frame <= 444:
            continue
        if run_len <= 4:
            continue
        if run_len >= 36:
            check("dead time", start_frame, run_len, 36, False)
            dead_time_failures += 1

    check("dead time total", 0, dead_time_failures, 0, dead_time_failures == 0)

    # Write output JSON
    n_failed = sum(1 for r in results if not r["ok"])
    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"checks": results, "failed": n_failed, "total": len(results)}, f, indent=1)

    print(f"[qa] {len(results)} checks, {n_failed} failed", flush=True)
    failures = [r for r in results if not r["ok"]]
    for i, r in enumerate(failures):
        if i < 60:
            print(f"[qa] FAIL {r['check']} f{r['frame']} value={r['value']} limit={r['limit']}", flush=True)
        else:
            print("[qa] ... more", flush=True)
            break

    if n_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
