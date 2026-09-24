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
