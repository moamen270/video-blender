"""Decal face module: eyes, brows, mouth shapes, expressions, and blink (Task E3)."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Sequence

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

from kit import qchar, toon
from studio import core as C


@dataclass
class Face:
    eyes: dict[str, bpy.types.Object]     # "L", "R" (character's left/right)
    brows: dict[str, bpy.types.Object]    # "L", "R"
    mouths: dict[str, bpy.types.Object]   # shape name -> object
    rest_shape: str                       # mouth shape shown when silent
    base: dict[str, Matrix]               # object name -> matrix_basis right after building


def _sgn(v: float) -> float:
    if v > 0.0:
        return 1.0
    if v < 0.0:
        return -1.0
    return 0.0


def superellipse(
    a: float,
    b: float,
    n: float = 4.0,
    k: int = 24,
) -> list[tuple[float, float]]:
    """Return k points along superellipse (a * sgn(cos t) * |cos t|^(2/n), b * sgn(sin t) * |sin t|^(2/n))."""
    pts: list[tuple[float, float]] = []
    for i in range(k):
        t = 2.0 * math.pi * i / k
        ct = math.cos(t)
        st = math.sin(t)
        x = a * _sgn(ct) * (abs(ct) ** (2.0 / n))
        z = b * _sgn(st) * (abs(st) ** (2.0 / n))
        pts.append((x, z))
    return pts


def band(
    x0: float,
    x1: float,
    zc: Callable[[float], float],
    half: Callable[[float], float],
    k: int = 13,
) -> list[tuple[float, float]]:
    """Return 2k points along band from x0 to x1 with top edge zc+half and bottom edge zc-half."""
    pts: list[tuple[float, float]] = []
    for i in range(k):
        t = i / (k - 1) if k > 1 else 0.0
        x = x0 + (x1 - x0) * t
        pts.append((x, zc(x) + half(x)))
    for i in reversed(range(k)):
        t = i / (k - 1) if k > 1 else 0.0
        x = x0 + (x1 - x0) * t
        pts.append((x, zc(x) - half(x)))
    return pts


_GRIN_T: dict[str, float] = {
    "X": 0.10,
    "A": 0.06,
    "B": 0.10,
    "C": 0.13,
    "D": 0.15,
    "E": 0.13,
    "F": 0.08,
    "G": 0.10,
    "H": 0.13,
}


def _mouth_faces(verts: list[Vector], *, is_band: bool) -> list[list[int]]:
    """Triangulate a mouth outline without relying on n-gon tessellation.

    The outlines are conformed to the curved head (non-planar) and bands are concave with
    coincident tips, which Blender's n-gon fill renders with holes. Bands (top edge left->right,
    then bottom edge right->left, k points each) become a quad strip; convex superellipses become
    a fan around an appended centre vertex (mutates `verts`).
    """
    n = len(verts)
    if is_band:
        k = n // 2
        return [[i, i + 1, n - 2 - i, n - 1 - i] for i in range(k - 1)]
    verts.append(sum(verts, Vector()) / n)
    return [[n, i, (i + 1) % n] for i in range(n)]


def mouth_outlines(style: str = "plain", rest: str = "X") -> dict[str, list[tuple[float, float]]]:
    """Return 2D mouth outline points (x, z) in native units around mouth centre."""
    if style == "plain":
        b_outline = superellipse(0.10, 0.028, 4.0)
        c_outline = superellipse(0.11, 0.05, 3.0)
        outlines: dict[str, list[tuple[float, float]]] = {
            "X": superellipse(0.10, 0.012, 6.0),
            "frown": band(
                -0.11,
                0.11,
                lambda x: 0.02 - 0.04 * ((x / 0.11) ** 2),
                lambda x: 0.013,
            ),
            "A": superellipse(0.11, 0.015, 6.0),
            "B": b_outline,
            "C": c_outline,
            "D": superellipse(0.12, 0.08, 2.5),
            "E": superellipse(0.075, 0.07, 2.0),
            "F": superellipse(0.045, 0.045, 2.0),
            "G": list(b_outline),
            "H": list(c_outline),
        }
    elif style == "grin":
        outlines = {}
        for shape, t in _GRIN_T.items():
            top = lambda x: 0.02 + 0.05 * ((x / 0.30) ** 2)
            bottom = lambda x, t_val=t: top(x) - t_val * (1.0 - ((x / 0.30) ** 2))
            zc = lambda x, t_val=t: (top(x) + bottom(x, t_val)) / 2.0
            half = lambda x, t_val=t: (top(x) - bottom(x, t_val)) / 2.0
            outlines[shape] = band(-0.30, 0.30, zc, half)
    else:
        raise ValueError(f"Unknown mouth style '{style}'")

    if rest not in outlines:
        raise ValueError(f"Rest shape '{rest}' not supported for style '{style}'")

    return outlines


EXPRESSIONS: dict[str, dict[str, float]] = {
    "neutral": {
        "brow_tilt": 0.0,
        "brow_dz": 0.0,
        "eye_sz": 1.0,
        "eye_sx": 1.0,
    },
    "stern": {
        "brow_tilt": 14.0,
        "brow_dz": -0.012,
        "eye_sz": 0.80,
        "eye_sx": 1.0,
    },
    "angry": {
        "brow_tilt": 24.0,
        "brow_dz": -0.018,
        "eye_sz": 0.70,
        "eye_sx": 1.0,
    },
    "surprised": {
        "brow_tilt": -6.0,
        "brow_dz": 0.025,
        "eye_sz": 1.15,
        "eye_sx": 1.10,
    },
    "suspicious": {
        "brow_tilt": 0.0,
        "brow_tilt_L": 18.0,
        "brow_tilt_R": -4.0,
        "brow_dz": 0.0,
        "brow_dz_L": -0.015,
        "brow_dz_R": 0.010,
        "eye_sz": 0.45,
        "eye_sx": 1.0,
    },
    "smug": {
        "brow_tilt": 0.0,
        "brow_tilt_L": -10.0,
        "brow_tilt_R": 10.0,
        "brow_dz": 0.0,
        "brow_dz_L": 0.020,
        "brow_dz_R": 0.0,
        "eye_sz": 0.60,
        "eye_sx": 1.0,
    },
    "deadpan": {
        "brow_tilt": 0.0,
        "brow_dz": -0.010,
        "eye_sz": 0.50,
        "eye_sx": 1.0,
    },
}


def build_face(
    qc: qchar.QChar,
    *,
    style: str = "plain",
    rest: str = "X",
    paint_hex: str = "#f4f4ef",
) -> Face:
    """Build decal face: eyes/brows extracted from mesh, mouth shapes, expressions."""
    paint = toon.toon(f"{qc.name}_paint", paint_hex, emission=1.0)

    # Find the Face islands
    bm = bmesh.new()
    bm.from_mesh(qc.body.data)

    face_mat_indices = {
        idx
        for idx, m in enumerate(qc.body.data.materials)
        if m is not None and qchar.strip(m.name) == "Face"
    }
    face_bm_faces = [f for f in bm.faces if f.material_index in face_mat_indices]

    face_set = set(face_bm_faces)
    islands: list[list[bmesh.types.BMFace]] = []
    while face_set:
        start = face_set.pop()
        island = [start]
        queue = [start]
        while queue:
            cur = queue.pop()
            for edge in cur.edges:
                for nbr in edge.link_faces:
                    if nbr in face_set:
                        face_set.remove(nbr)
                        island.append(nbr)
                        queue.append(nbr)
        islands.append(island)

    if len(islands) != 4:
        bm.free()
        raise RuntimeError(f"Expected exactly 4 Face islands, found {len(islands)}")

    body_cols = qc.body.users_collection
    target_col = body_cols[0] if body_cols else bpy.context.scene.collection

    eyes: dict[str, bpy.types.Object] = {}
    brows: dict[str, bpy.types.Object] = {}
    base: dict[str, Matrix] = {}

    island_objs: list[tuple[bpy.types.Object, str, str]] = []

    for island in islands:
        island_verts = sorted({v for f in island for v in f.verts}, key=lambda v: v.index)
        native_centre = sum((v.co for v in island_verts), Vector((0.0, 0.0, 0.0))) / len(island_verts)
        max_native_z = max(v.co.z for v in island_verts)

        kind = "brow" if max_native_z > 2.66 else "eye"
        side = "L" if native_centre.x > 0.0 else "R"
        part = f"{kind}.{side}"
        obj_name = f"{qc.name}_{part}"

        loc = qchar.native(qc, native_centre)
        verts_world_offsets = [qchar.native(qc, v.co) - loc for v in island_verts]

        v_to_idx = {v: idx for idx, v in enumerate(island_verts)}
        reindexed_faces = [[v_to_idx[v] for v in f.verts] for f in island]

        mesh = bpy.data.meshes.new(obj_name)
        mesh.from_pydata(verts_world_offsets, [], reindexed_faces)
        mesh.update()
        mesh.materials.append(paint)

        obj = bpy.data.objects.new(obj_name, mesh)
        obj.rotation_mode = "QUATERNION"
        obj.location = loc
        C.link(obj, target_col)

        island_objs.append((obj, kind, side))

    # Delete Face polygons from qc.body
    bmesh.ops.delete(bm, geom=face_bm_faces, context="FACES")
    bm.to_mesh(qc.body.data)
    qc.body.data.update()
    bm.free()

    # Attach each island object to bone Head
    for obj, kind, side in island_objs:
        part = f"{kind}.{side}"
        qchar.attach_part(qc, obj, "Head", part)
        base[obj.name] = obj.matrix_basis.copy()
        if kind == "eye":
            eyes[side] = obj
        else:
            brows[side] = obj

    # Build mouths
    shapes = mouth_outlines(style, rest)
    mouths: dict[str, bpy.types.Object] = {}
    mouth_loc = qchar.native(qc, (0.0, -0.50, 2.34))

    for shape, outline_pts in shapes.items():
        pts_xz = [(x, 2.34 + z) for x, z in outline_pts]
        surf_pts = qchar.surface_points(qc, pts_xz, bones=["Head"], materials=["Skin"], offset=0.008)
        world_pts = [qchar.native(qc, pt) for pt in surf_pts]
        verts = [wpt - mouth_loc for wpt in world_pts]
        faces = _mouth_faces(verts, is_band=(style == "grin" or shape == "frown"))

        m_name = f"{qc.name}_mouth_{shape}"
        m_mesh = bpy.data.meshes.new(m_name)
        m_mesh.from_pydata(verts, [], faces)
        m_mesh.update()
        m_mesh.materials.append(paint)

        m_obj = bpy.data.objects.new(m_name, m_mesh)
        m_obj.rotation_mode = "QUATERNION"
        m_obj.location = mouth_loc
        C.link(m_obj, target_col)

        qchar.attach_part(qc, m_obj, "Head", f"mouth_{shape}")
        C.visible(m_obj, 1, shape == rest)
        base[m_obj.name] = m_obj.matrix_basis.copy()
        mouths[shape] = m_obj

    face = Face(
        eyes=eyes,
        brows=brows,
        mouths=mouths,
        rest_shape=rest,
        base=base,
    )
    qc.face = face
    print(f"[face] built {qc.name} face ({len(mouths)} mouths)", flush=True)
    return face


def set_expression(face: Face, name: str | dict, frame: int | None = None) -> None:
    """Apply facial expression to eyes and brows, optionally keyframing."""
    expr = EXPRESSIONS[name] if isinstance(name, str) else name
    eye_sx = expr.get("eye_sx", 1.0)
    eye_sz = expr.get("eye_sz", 1.0)
    brow_tilt = expr.get("brow_tilt", 0.0)
    brow_dz = expr.get("brow_dz", 0.0)

    # Brows
    for side in ("L", "R"):
        obj = face.brows.get(side)
        if obj is None:
            continue
        base_loc, base_rot, base_scale = face.base[obj.name].decompose()
        dz = expr.get(f"brow_dz_{side}", brow_dz)
        tilt = expr.get(f"brow_tilt_{side}", brow_tilt)

        loc = Vector((base_loc.x, base_loc.y, base_loc.z + dz))
        angle = math.radians(tilt if side == "L" else -tilt)
        q_rot = Quaternion(Vector((0.0, 1.0, 0.0)), angle)
        rot = q_rot @ base_rot
        scale = base_scale.copy()

        obj.location = loc
        if obj.rotation_mode == "QUATERNION":
            obj.rotation_quaternion = rot
        else:
            obj.rotation_euler = rot.to_euler(obj.rotation_mode)
        obj.scale = scale
        obj.matrix_basis = Matrix.LocRotScale(loc, rot, scale)

        if frame is not None:
            obj.keyframe_insert("location", frame=frame)
            if obj.rotation_mode == "QUATERNION":
                obj.keyframe_insert("rotation_quaternion", frame=frame)
            else:
                obj.keyframe_insert("rotation_euler", frame=frame)
            obj.keyframe_insert("scale", frame=frame)

    # Eyes
    for side in ("L", "R"):
        obj = face.eyes.get(side)
        if obj is None:
            continue
        base_loc, base_rot, base_scale = face.base[obj.name].decompose()
        loc = base_loc.copy()
        rot = base_rot.copy()
        scale = Vector((base_scale.x * eye_sx, base_scale.y, base_scale.z * eye_sz))

        obj.location = loc
        if obj.rotation_mode == "QUATERNION":
            obj.rotation_quaternion = rot
        else:
            obj.rotation_euler = rot.to_euler(obj.rotation_mode)
        obj.scale = scale
        obj.matrix_basis = Matrix.LocRotScale(loc, rot, scale)

        if frame is not None:
            obj.keyframe_insert("location", frame=frame)
            if obj.rotation_mode == "QUATERNION":
                obj.keyframe_insert("rotation_quaternion", frame=frame)
            else:
                obj.keyframe_insert("rotation_euler", frame=frame)
            obj.keyframe_insert("scale", frame=frame)


def key_mouth(face: Face, frame: int, shape: str) -> None:
    """Set visibility keyframes for all mouth shapes at frame."""
    for s_name, obj in face.mouths.items():
        C.visible(obj, frame, s_name == shape)


def blink(face: Face, frame: int, expression: str = "neutral") -> None:
    """Animate a 4-frame eye blink at the specified frame."""
    expr = EXPRESSIONS[expression] if isinstance(expression, str) else expression
    eye_sx = expr.get("eye_sx", 1.0)
    base_sz = expr.get("eye_sz", 1.0)

    factors = [(0, 1.0), (1, 0.5), (2, 0.08), (4, 1.0)]
    for side in ("L", "R"):
        obj = face.eyes.get(side)
        if obj is None:
            continue
        base_loc, base_rot, base_scale = face.base[obj.name].decompose()
        for df, factor in factors:
            f = frame + df
            sz = base_sz * factor
            cur_scale = Vector((base_scale.x * eye_sx, base_scale.y, base_scale.z * sz))
            obj.scale = cur_scale
            obj.matrix_basis = Matrix.LocRotScale(base_loc, base_rot, cur_scale)
            obj.keyframe_insert("scale", frame=f)


def apply_lipsync(face: Face, cues: list[dict], start_frame: int, fps: int = 24) -> int:
    """Keyframe mouth shapes from Rhubarb mouth cues, returning the final end frame."""
    if not cues:
        return start_frame
    for cue in cues:
        f = start_frame + round(cue["start"] * fps)
        val = cue["value"]
        shape = face.rest_shape if val == "X" else val
        key_mouth(face, f, shape)
    last = cues[-1]
    end_frame = start_frame + round(last["end"] * fps)
    key_mouth(face, end_frame, face.rest_shape)
    return end_frame


def change_expression(
    face: Face,
    frame: int,
    from_name: str | dict,
    to_name: str | dict,
    frames: int = 4,
) -> None:
    """Transition between two expressions over frames."""
    set_expression(face, from_name, frame)
    set_expression(face, to_name, frame + frames)


def auto_blink(
    face: Face,
    start: int,
    end: int,
    schedule: Sequence[tuple[int, str]],
    *,
    seed: int = 0,
    gap: tuple[int, int] = (48, 110),
) -> list[int]:
    """Generate and animate natural blinks avoiding expression changes."""
    rng = random.Random(seed)
    sorted_schedule = sorted(schedule, key=lambda s: s[0])
    blink_frames: list[int] = []

    f = start + 12
    while f < end - 4:
        if any(abs(f - s_frame) <= 6 for s_frame, _ in sorted_schedule):
            f += rng.randint(*gap)
            continue

        expr = "neutral"
        for s_frame, s_expr in sorted_schedule:
            if s_frame <= f:
                expr = s_expr
            else:
                break

        blink(face, f, expr)
        blink_frames.append(f)
        f += rng.randint(*gap)

    return blink_frames

