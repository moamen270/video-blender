"""NLA actions, walking, and turning library (Task F2)."""
from __future__ import annotations

import math
from typing import Sequence

import bpy
from mathutils import Vector

from studio import core as C
from kit import qchar as Q

_SPEED: dict[tuple[str, str], float] = {}
_FOOT_TRACK: dict[tuple[str, str], dict] = {}
_LANDING_PHASES: dict[tuple[str, str], list[int]] = {}


def play(
    qc: Q.QChar,
    action: str | bpy.types.Action,
    start: int,
    frames: int | float,
    *,
    blend_in: float = 0,
) -> bpy.types.NlaStrip:
    """Create a new NLA track on top and add a strip playing action."""
    arm = qc.arm
    ad = arm.animation_data_create()
    act = qc.actions[action] if isinstance(action, str) else action
    act_name = action if isinstance(action, str) else act.name
    track_name = f"{act_name}@{start}"
    track = ad.nla_tracks.new()
    track.name = track_name

    strip = track.strips.new(track_name, int(start), act)

    action_length = act.frame_range[1] - act.frame_range[0]
    if action_length > 0:
        strip.repeat = frames / action_length
    strip.blend_in = float(blend_in)
    strip.extrapolation = "HOLD_FORWARD"
    strip.blend_type = "REPLACE"
    return strip


def foot_track(qc: Q.QChar, action: str | bpy.types.Action = "Walk") -> dict:
    """Sample and cache native armature-space heads of Foot.L and Foot.R for phase 0..L."""
    act = qc.actions[action] if isinstance(action, str) else action
    act_name = action if isinstance(action, str) else act.name
    cache_key = (qc.name, act_name)
    if (qc.name, action) in _FOOT_TRACK:
        return _FOOT_TRACK[(qc.name, action)]
    if cache_key in _FOOT_TRACK:
        return _FOOT_TRACK[cache_key]

    arm = qc.arm
    ad = arm.animation_data_create()
    prev_action = ad.action
    prev_slot = getattr(ad, "action_slot", None)
    track_mutes = [(track, track.mute) for track in ad.nla_tracks]
    for track in ad.nla_tracks:
        track.mute = True

    ad.action = act
    if hasattr(ad, "action_slot"):
        if ad.action_slot is None and hasattr(act, "slots") and len(act.slots) > 0:
            try:
                ad.action_slot = act.slots[0]
            except Exception:
                pass

    f0 = int(round(act.frame_range[0]))
    f1 = int(round(act.frame_range[1]))
    L = f1 - f0
    scene = bpy.context.scene

    L_track: list[tuple[float, float]] = []
    R_track: list[tuple[float, float]] = []
    for p in range(L + 1):
        scene.frame_set(f0 + p)
        bpy.context.view_layer.update()
        hL = arm.pose.bones["Foot.L"].head
        hR = arm.pose.bones["Foot.R"].head
        L_track.append((float(hL.y), float(hL.z)))
        R_track.append((float(hR.y), float(hR.z)))

    ad.action = prev_action
    if hasattr(ad, "action_slot"):
        try:
            ad.action_slot = prev_slot
        except Exception:
            pass
    for track, mute in track_mutes:
        track.mute = mute

    result = {"len": L, "L": L_track, "R": R_track}
    _FOOT_TRACK[(qc.name, action)] = result
    _FOOT_TRACK[cache_key] = result
    return result


def ground_speed(qc: Q.QChar, action: str | bpy.types.Action = "Walk") -> float:
    """World metres per frame of a looping locomotion action."""
    act = qc.actions[action] if isinstance(action, str) else action
    act_name = action if isinstance(action, str) else act.name
    cache_key = (qc.name, act_name)
    if (qc.name, action) in _SPEED:
        return _SPEED[(qc.name, action)]
    if cache_key in _SPEED:
        return _SPEED[cache_key]

    tr = foot_track(qc, action)
    L = tr["len"]
    deltas: list[float] = []
    landing_phases: list[int] = []

    for side in ("L", "R"):
        pts = tr[side]
        min_z = min(pt[1] for pt in pts)
        planted_threshold = min_z + 0.03
        is_planted = [pt[1] <= planted_threshold for pt in pts]

        for p in range(L):
            if is_planted[p] and is_planted[p + 1]:
                deltas.append(abs(pts[p + 1][0] - pts[p][0]))

        for p in range(L):
            if is_planted[p]:
                prev_p = (p - 1) % L
                if not is_planted[prev_p]:
                    landing_phases.append(p)

    landing_phases.sort()
    _LANDING_PHASES[(qc.name, action)] = landing_phases
    _LANDING_PHASES[cache_key] = landing_phases

    speed_native = (sum(deltas) / len(deltas)) if deltas else 0.0
    speed_world = speed_native * qc.scale
    _SPEED[(qc.name, action)] = speed_world
    _SPEED[cache_key] = speed_world
    return speed_world


def key_root(
    qc: Q.QChar,
    frame: int,
    *,
    loc: Sequence[float] | Vector | None = None,
    heading: float | None = None,
) -> None:
    """Key qc.root location and/or rotation z (heading in degrees) with LINEAR interpolation."""
    if loc is not None:
        C.key(qc.root, frame, loc=tuple(loc))
    if heading is not None:
        qc.root.rotation_euler.z = math.radians(heading)
        qc.root.keyframe_insert("rotation_euler", index=2, frame=frame)
    C.set_interp_at(qc.root, frame, "LINEAR")


def walk_to(
    qc: Q.QChar,
    start: int,
    to_xy: Sequence[float] | Vector,
    *,
    action: str = "Walk",
    turn_frames: int = 6,
    blend: int = 6,
) -> tuple[int, list[int]]:
    """Animate qc walking from current location to to_xy, extracting root motion from the action."""
    ad = qc.arm.animation_data_create()
    had_tracks = len(ad.nla_tracks) > 0

    scene = bpy.context.scene
    scene.frame_set(start)
    bpy.context.view_layer.update()

    p0 = qc.root.location.copy()
    to_v = Vector((to_xy[0], to_xy[1]))
    d = to_v - p0.xy
    dist = d.length

    current_heading = math.degrees(qc.root.rotation_euler.z)
    if dist > 1e-6:
        u = d.normalized()
        heading = math.degrees(math.atan2(-d.x, d.y))
    else:
        u = Vector((0.0, 0.0))
        heading = current_heading

    key_root(qc, start, heading=current_heading)
    key_root(qc, start + turn_frames, heading=heading)
    key_root(qc, start, loc=p0)

    tr = foot_track(qc, action)
    L = tr["len"]
    cum = 0.0
    f = start
    prev_sup: str | None = None
    steps: list[int] = []

    while True:
        if f - start > 20 * L:
            raise RuntimeError(f"walk_to did not reach target within {20 * L} frames")
        p = (f - start) % L
        sup = "L" if tr["L"][p][1] <= tr["R"][p][1] else "R"
        if prev_sup is not None and sup != prev_sup:
            steps.append(f)
        prev_sup = sup

        delta = max(0.0, tr[sup][p + 1][0] - tr[sup][p][0]) * qc.scale
        if had_tracks and (f - start) < blend:
            delta *= (f - start + 1) / blend
        cum += delta
        f += 1
        if cum >= dist:
            key_root(qc, f, loc=(to_xy[0], to_xy[1], p0.z))
            break
        else:
            loc_xy = p0.xy + u * cum
            key_root(qc, f, loc=(loc_xy.x, loc_xy.y, p0.z))

    n = f - start
    play(qc, action, start, n + blend, blend_in=blend if had_tracks else 0)
    play(qc, "Idle", start + n, 240, blend_in=blend)
    return (start + n, steps)


def turn_to(qc: Q.QChar, frame: int, heading: float, frames: int = 8) -> None:
    """Key current heading at frame and target heading at frame + frames."""
    scene = bpy.context.scene
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    current_heading = math.degrees(qc.root.rotation_euler.z)
    key_root(qc, frame, heading=current_heading)
    key_root(qc, frame + frames, heading=heading)


def foot_events(qc: Q.QChar, start: int, end: int, *, eps: float = 0.006) -> list[int]:
    """Frames where a foot touches down, measured on the final evaluated animation.

    Call after every motion call of the character (like the cape bake). A touchdown is the first
    frame of a run where the foot's world z is within `eps` of its lowest z over [start, end].
    Used for footstep SFX: measured contacts land on the frame, unlike phase guesses.
    """
    scene = bpy.context.scene
    arm = qc.arm
    zs: dict[str, list[float]] = {"Foot.L": [], "Foot.R": []}
    for f in range(start, end + 1):
        scene.frame_set(f)
        for b in zs:
            zs[b].append((arm.matrix_world @ arm.pose.bones[b].head).z)
    frames: set[int] = set()
    for b, arr in zs.items():
        low = min(arr) + eps
        for i, z in enumerate(arr):
            if z <= low and i > 0 and arr[i - 1] > low:
                frames.add(start + i)
    return sorted(frames)


# --------------------------------------------------------------------------- IK and props (Task G4)
from mathutils import Matrix


def setup_ik(qc: Q.QChar) -> dict[str, bpy.types.Object]:
    """Set up IK target empties and constraints for both hands (Task G4)."""
    bpy.context.view_layer.update()
    qc.arm.animation_data_create()
    empties: dict[str, bpy.types.Object] = {}
    col = qc.root.users_collection[0] if qc.root.users_collection else None

    for side in ("L", "R"):
        empty_name = f"{qc.name}_ik.{side}"
        pos = qc.arm.matrix_world @ qc.arm.pose.bones[f"Fist.{side}"].head
        empty = C.empty(empty_name, loc=pos, col=col)
        pb = qc.arm.pose.bones[f"LowerArm.{side}"]
        con = pb.constraints.new("IK")
        con.target = empty
        con.chain_count = 2
        con.use_tail = True
        con.influence = 0.0
        con.keyframe_insert("influence", frame=1)
        empties[side] = empty
        qc.parts[f"ik.{side}"] = empty

    return empties


def reach(
    qc: Q.QChar,
    side: str,
    target: Sequence[float] | Vector,
    start: int,
    end: int,
    *,
    blend: int = 5,
) -> None:
    """Key hand reach toward world target using IK target empty and constraint influence."""
    empty = qc.parts.get(f"ik.{side}") or bpy.data.objects.get(f"{qc.name}_ik.{side}")
    if empty is None:
        raise RuntimeError(f"IK target empty for {qc.name} side {side} not found. Call setup_ik first.")

    t_vec = Vector(target)

    for fc in C.fcurves(empty):
        if fc.data_path == "location":
            for kp in fc.keyframe_points:
                if kp.co.x < (start - blend) - 0.5:
                    kp.interpolation = "CONSTANT"

    empty.location = t_vec
    empty.keyframe_insert("location", frame=start - blend)
    empty.keyframe_insert("location", frame=end)
    C.set_interp_at(empty, start - blend, "CONSTANT")

    pb = qc.arm.pose.bones[f"LowerArm.{side}"]
    con = next((c for c in pb.constraints if c.type == "IK" and getattr(c, "target", None) == empty), None)
    if con is None:
        con = next(c for c in pb.constraints if c.type == "IK")

    qc.arm.animation_data_create()
    con.influence = 0.0
    con.keyframe_insert("influence", frame=start - blend)
    con.influence = 1.0
    con.keyframe_insert("influence", frame=start)
    con.influence = 1.0
    con.keyframe_insert("influence", frame=end)
    con.influence = 0.0
    con.keyframe_insert("influence", frame=end + blend)


def hold(
    qc: Q.QChar,
    prop: bpy.types.Object,
    side: str,
    frame: int,
) -> bpy.types.Object:
    """Duplicate prop, attach to character hand bone at frame, and swap visibility."""
    scene = bpy.context.scene
    scene.frame_set(frame)
    bpy.context.view_layer.update()

    held = prop.copy()
    if held.animation_data:
        held.animation_data_clear()

    cols = list(prop.users_collection)
    if cols:
        for col in cols:
            col.objects.link(held)
    else:
        scene.collection.objects.link(held)

    held.parent = qc.arm
    held.parent_type = "BONE"
    held.parent_bone = f"Fist.{side}"
    held.matrix_parent_inverse = Matrix.Identity(4)
    bpy.context.view_layer.update()
    held.matrix_world = prop.matrix_world.copy()
    bpy.context.view_layer.update()

    has_f1 = False
    for fc in C.fcurves(prop):
        if fc.data_path == "hide_render":
            for kp in fc.keyframe_points:
                if abs(kp.co.x - 1) < 0.5:
                    has_f1 = True
                    break
    if not has_f1:
        C.visible(prop, 1, True)

    C.visible(held, 1, False)
    C.visible(held, frame, True)
    C.visible(prop, frame, False)
    return held


def release(
    held: bpy.types.Object,
    frame: int,
    *,
    place: Sequence[float] | Vector | None = None,
) -> bpy.types.Object:
    """Release a held prop into world space at frame, optionally placing it at place."""
    scene = bpy.context.scene
    scene.frame_set(frame)
    bpy.context.view_layer.update()

    obj = held.copy()
    if obj.animation_data:
        obj.animation_data_clear()

    cols = list(held.users_collection)
    if cols:
        for col in cols:
            col.objects.link(obj)
    else:
        scene.collection.objects.link(obj)

    obj.parent = None
    obj.matrix_parent_inverse = Matrix.Identity(4)

    mw = held.matrix_world.copy()
    if place is not None:
        mw.translation = Vector(place)
    obj.matrix_world = mw
    bpy.context.view_layer.update()

    C.visible(held, frame, False)
    C.visible(obj, 1, False)
    C.visible(obj, frame, True)
    return obj


def throw(
    obj: bpy.types.Object,
    start: int,
    end: int,
    p0: Sequence[float] | Vector,
    p1: Sequence[float] | Vector,
    *,
    arc: float = 0.25,
    spin: float = 720.0,
) -> None:
    """Animate object thrown along a parabolic arc with z-axis spin."""
    p0_v = Vector(p0)
    p1_v = Vector(p1)
    total_frames = end - start

    for f in range(start, end + 1):
        t = (f - start) / total_frames if total_frames > 0 else 0.0
        pt = (1.0 - t) * p0_v + t * p1_v
        pt.z += 4.0 * arc * t * (1.0 - t)
        obj.location = pt
        obj.keyframe_insert("location", frame=f)

    obj.rotation_euler.z = 0.0
    obj.keyframe_insert("rotation_euler", index=2, frame=start)
    obj.rotation_euler.z = math.radians(spin)
    obj.keyframe_insert("rotation_euler", index=2, frame=end)
    C.set_interp_at(obj, start, "LINEAR")
    C.set_interp_at(obj, end, "LINEAR")
    for fc in C.fcurves(obj):
        if fc.data_path == "rotation_euler" and fc.array_index == 2:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def reach_path(
    qc: Q.QChar,
    side: str,
    points: list[tuple[int, Sequence[float] | Vector]],
    *,
    blend_in: int = 5,
    blend_out: int = 5,
) -> None:
    """One continuous IK reach through several (frame, world target) points.

    Use this instead of back-to-back `reach` calls (their influence keys would overwrite each other):
    the IK target glides between the points (Bezier), influence is 0 -> 1 over `blend_in` frames before
    the first point and 1 -> 0 over `blend_out` frames after the last one.
    """
    empty = qc.parts.get(f"ik.{side}") or bpy.data.objects.get(f"{qc.name}_ik.{side}")
    if empty is None:
        raise RuntimeError(f"IK target empty for {qc.name} side {side} not found. Call setup_ik first.")
    points = sorted(points, key=lambda p: p[0])
    f0, p0 = points[0]
    f1 = points[-1][0]
    for fc in C.fcurves(empty):
        if fc.data_path == "location":
            for kp in fc.keyframe_points:
                if kp.co.x < (f0 - blend_in) - 0.5:
                    kp.interpolation = "CONSTANT"
    empty.location = Vector(p0)
    empty.keyframe_insert("location", frame=f0 - blend_in)
    C.set_interp_at(empty, f0 - blend_in, "CONSTANT")
    for f, p in points:
        empty.location = Vector(p)
        empty.keyframe_insert("location", frame=f)
    pb = qc.arm.pose.bones[f"LowerArm.{side}"]
    con = next((c for c in pb.constraints if c.type == "IK" and getattr(c, "target", None) == empty), None)
    if con is None:
        con = next(c for c in pb.constraints if c.type == "IK")
    for f, v in ((f0 - blend_in, 0.0), (f0, 1.0), (f1, 1.0), (f1 + blend_out, 0.0)):
        con.influence = v
        con.keyframe_insert("influence", frame=f)
