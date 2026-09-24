"""Auto-framed camera shots, push, whip, and framing verification (Task G3)."""
from __future__ import annotations

import math
from typing import Any

import bpy
import bpy_extras
from mathutils import Vector

from studio import core as C

try:
    from kit.qchar import QChar
except ImportError:
    QChar = None

# Shot presets: (fraction of frame HEIGHT, default lens, default headroom, QChar part)
PRESETS: dict[str, dict[str, Any]] = {
    "wide": {"fraction": 0.45, "lens": 28.0, "headroom": 0.20, "part": "full"},
    "full": {"fraction": 0.75, "lens": 35.0, "headroom": 0.08, "part": "full"},
    "medium": {"fraction": 0.80, "lens": 40.0, "headroom": 0.06, "part": "medium"},
    "close": {"fraction": 0.62, "lens": 50.0, "headroom": 0.07, "part": "close"},
    "ecu": {"fraction": 0.95, "lens": 60.0, "headroom": 0.02, "part": "face"},
    "insert": {"fraction": 0.60, "lens": 50.0, "headroom": 0.20, "part": "full"},
    "two_shot": {"fraction": 0.70, "lens": 35.0, "headroom": 0.08, "part": "medium"},
}


def region(target: Any, part: str = "full") -> tuple[Vector, Vector]:
    """World bbox (min, max) of a target at the current frame."""
    if isinstance(target, Vector):
        half = Vector((0.05, 0.05, 0.05))
        return (target - half, target + half)

    if isinstance(target, (list, tuple)):
        if len(target) == 3 and all(isinstance(x, (int, float)) for x in target):
            v = Vector(target)
            half = Vector((0.05, 0.05, 0.05))
            return (v - half, v + half)

        if not target:
            half = Vector((0.05, 0.05, 0.05))
            return (-half, half)

        sub_regions = [region(t, part=part) for t in target]
        min_v = Vector((
            min(r[0].x for r in sub_regions),
            min(r[0].y for r in sub_regions),
            min(r[0].z for r in sub_regions),
        ))
        max_v = Vector((
            max(r[1].x for r in sub_regions),
            max(r[1].y for r in sub_regions),
            max(r[1].z for r in sub_regions),
        ))
        return (min_v, max_v)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()

    is_qchar = (QChar is not None and isinstance(target, QChar)) or (
        hasattr(target, "body") and hasattr(target, "parts")
    )

    pts: list[Vector] = []
    if is_qchar:
        objs = [target.body]
        if hasattr(target, "parts") and isinstance(target.parts, dict):
            # Only visible geometry: IK target empties (parts "ik.L"/"ik.R") sit wherever the last reach
            # left them and made two-shots frame half the store (senior review of output/v10).
            objs.extend(o for o in target.parts.values()
                        if o is not None and o.type in {"MESH", "CURVE", "FONT"} and not o.hide_render)
        for obj in objs:
            if obj is None:
                continue
            eval_obj = obj.evaluated_get(dg)
            if hasattr(eval_obj, "bound_box") and eval_obj.bound_box:
                mw = eval_obj.matrix_world
                for c in eval_obj.bound_box:
                    pts.append(mw @ Vector(c))
    elif isinstance(target, bpy.types.Object):
        objs = [target]
        if hasattr(target, "children_recursive"):
            objs.extend(target.children_recursive)
        for obj in objs:
            eval_obj = obj.evaluated_get(dg)
            if hasattr(eval_obj, "bound_box") and eval_obj.bound_box:
                mw = eval_obj.matrix_world
                for c in eval_obj.bound_box:
                    pts.append(mw @ Vector(c))
        if not pts:
            pts.append(target.matrix_world.translation.copy())
    else:
        half = Vector((0.05, 0.05, 0.05))
        return (-half, half)

    if not pts:
        half = Vector((0.05, 0.05, 0.05))
        return (-half, half)

    min_x = min(p.x for p in pts)
    max_x = max(p.x for p in pts)
    min_y = min(p.y for p in pts)
    max_y = max(p.y for p in pts)
    min_z = min(p.z for p in pts)
    max_z = max(p.z for p in pts)

    h = max_z - min_z
    top = max_z

    if is_qchar:
        if part == "medium":
            z_min = top - 0.62 * h
            z_max = top
        elif part == "close":
            z_min = top - 0.38 * h
            z_max = top
        elif part == "face":
            z_min = top - 0.30 * h
            z_max = top - 0.02 * h
        else:
            z_min = min_z
            z_max = max_z
    else:
        z_min = min_z
        z_max = max_z

    return (Vector((min_x, min_y, z_min)), Vector((max_x, max_y, z_max)))


def frame(
    name: str,
    target: Any,
    *,
    shot: str,
    yaw: float,
    pitch: float = 0.0,
    at: int | None = None,
    lens: float | None = None,
    headroom: float | None = None,
    side_offset: float = 0.0,
) -> bpy.types.Object:
    """Create and return an auto-framed camera targeting region."""
    if at is not None:
        bpy.context.scene.frame_set(at)

    preset = PRESETS.get(shot, {"fraction": 0.75, "lens": 35.0, "headroom": 0.08, "part": "full"})
    fraction = float(preset["fraction"])
    used_lens = float(preset["lens"] if lens is None else lens)
    used_headroom = float(preset["headroom"] if headroom is None else headroom)
    part = str(preset["part"])

    min_v, max_v = region(target, part=part)
    rh = max_v.z - min_v.z
    if rh <= 0.0:
        rh = 0.1

    H = rh / fraction
    vfov = 2.0 * math.atan(18.0 / used_lens)
    d = H / (2.0 * math.tan(vfov / 2.0))

    rad_yaw = math.radians(yaw)
    rad_pitch = math.radians(pitch)
    u_h = Vector((-math.sin(rad_yaw), math.cos(rad_yaw), 0.0))

    corners = [
        Vector((x, y, z))
        for x in (min_v.x, max_v.x)
        for y in (min_v.y, max_v.y)
        for z in (min_v.z, max_v.z)
    ]
    projections = [c.dot(u_h) for c in corners]
    extent = max(projections) - min(projections)
    d += 0.5 * extent

    center = 0.5 * (min_v + max_v)
    up = Vector((0.0, 0.0, 1.0))
    right = Vector((-math.cos(rad_yaw), -math.sin(rad_yaw), 0.0))

    aim = center - up * (0.5 * H - used_headroom * H - 0.5 * rh) + right * (side_offset * H)

    dir_cam = math.cos(rad_pitch) * u_h + math.sin(rad_pitch) * up
    cam_loc = aim + d * dir_cam

    if name in bpy.data.objects:
        old_obj = bpy.data.objects[name]
        old_data = old_obj.data
        bpy.data.objects.remove(old_obj, do_unlink=True)
        if old_data and old_data.users == 0:
            bpy.data.cameras.remove(old_data)

    cam = C.camera(name, cam_loc, aim, lens=used_lens)

    scene = bpy.context.scene
    target_cx = 0.5 + side_offset
    target_top = 1.0 - used_headroom

    cam_up = right.cross(-dir_cam).normalized()
    r = scene.render
    aspect = (r.resolution_x * r.pixel_aspect_x) / (r.resolution_y * r.pixel_aspect_y) if r.resolution_y else (9.0 / 16.0)

    best_score = float("inf")
    best_aim = aim.copy()
    best_d = d

    for _ in range(12):
        bpy.context.view_layer.update()
        projected = [
            bpy_extras.object_utils.world_to_camera_view(scene, cam, c)
            for c in corners
        ]
        cur_top = max(p.y for p in projected)
        cur_bottom = min(p.y for p in projected)
        cur_fill = cur_top - cur_bottom
        cur_min_x = min(p.x for p in projected)
        cur_max_x = max(p.x for p in projected)
        cur_cx = 0.5 * (cur_min_x + cur_max_x)

        err_x = cur_cx - target_cx
        err_y = cur_top - target_top
        err_fill = cur_fill - fraction

        score = max(abs(err_x) / 0.06, abs(err_y) / 0.04, abs(err_fill) / 0.06)
        if score < best_score:
            best_score = score
            best_aim = aim.copy()
            best_d = d

        if abs(err_x) <= 0.015 and abs(err_y) <= 0.01 and abs(err_fill) <= 0.015:
            break

        if cur_fill > 0.0 and abs(err_fill) > 0.005:
            scale_d = 1.0 + 0.5 * (err_fill / fraction)
            scale_d = max(0.85, min(1.15, scale_d))
            d *= scale_d

        v_span = 2.0 * d * math.tan(vfov / 2.0)
        h_span = v_span * aspect

        shift = right * (0.5 * err_x * h_span) + cam_up * (0.5 * err_y * v_span)
        aim = aim + shift
        cam_loc = aim + d * dir_cam
        cam.location = cam_loc
        C.point_at(cam, aim)

    if (aim - best_aim).length > 1e-5 or abs(d - best_d) > 1e-5:
        aim = best_aim
        d = best_d
        cam_loc = aim + d * dir_cam
        cam.location = cam_loc
        C.point_at(cam, aim)

    cam["aim_x"] = float(aim.x)
    cam["aim_y"] = float(aim.y)
    cam["aim_z"] = float(aim.z)

    bpy.context.view_layer.update()
    return cam


def push(cam: bpy.types.Object, start: int, end: int, amount: float = 0.12) -> None:
    """Keys camera location at start and moved amount * distance toward aim point at end."""
    aim = Vector((cam["aim_x"], cam["aim_y"], cam["aim_z"]))
    loc_start = cam.location.copy()
    loc_end = loc_start + (aim - loc_start) * amount

    cam.location = loc_start
    cam.keyframe_insert("location", frame=start)
    cam.location = loc_end
    cam.keyframe_insert("location", frame=end)


def whip(cam: bpy.types.Object, frame: int, to_target: Any, frames: int = 4) -> None:
    """Keys camera rotation at frame and pointing at to_target at frame + frames."""
    cam.keyframe_insert("rotation_euler", frame=frame)

    if isinstance(to_target, Vector):
        tgt = to_target
    elif isinstance(to_target, (list, tuple)) and len(to_target) == 3 and all(isinstance(x, (int, float)) for x in to_target):
        tgt = Vector(to_target)
    elif hasattr(to_target, "root"):
        min_v, max_v = region(to_target)
        tgt = 0.5 * (min_v + max_v)
    elif isinstance(to_target, bpy.types.Object):
        if hasattr(to_target, "bound_box") and to_target.bound_box:
            min_v, max_v = region(to_target)
            tgt = 0.5 * (min_v + max_v)
        else:
            tgt = to_target.matrix_world.translation.copy()
    else:
        min_v, max_v = region(to_target)
        tgt = 0.5 * (min_v + max_v)

    C.point_at(cam, tgt)
    cam.keyframe_insert("rotation_euler", frame=frame + frames)
    cam["aim_x"] = float(tgt.x)
    cam["aim_y"] = float(tgt.y)
    cam["aim_z"] = float(tgt.z)

    bpy.context.scene.render.use_motion_blur = True


def check(cam: bpy.types.Object, target: Any, shot: str) -> dict[str, float]:
    """Projects region corners with world_to_camera_view -> top, bottom, cx, fill."""
    preset = PRESETS.get(shot)
    part = preset["part"] if preset else shot

    min_v, max_v = region(target, part=part)
    corners = [
        Vector((x, y, z))
        for x in (min_v.x, max_v.x)
        for y in (min_v.y, max_v.y)
        for z in (min_v.z, max_v.z)
    ]

    bpy.context.view_layer.update()
    scene = bpy.context.scene

    projected = [
        bpy_extras.object_utils.world_to_camera_view(scene, cam, c)
        for c in corners
    ]

    top = max(p.y for p in projected)
    bottom = min(p.y for p in projected)
    min_x = min(p.x for p in projected)
    max_x = max(p.x for p in projected)
    cx = 0.5 * (min_x + max_x)
    fill = top - bottom

    return {
        "top": float(top),
        "bottom": float(bottom),
        "cx": float(cx),
        "fill": float(fill),
    }
