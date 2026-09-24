"""Props module: milk carton, batarang, smoke puff (Task G1)."""
from __future__ import annotations

import math
import random
from typing import Sequence

import bmesh
import bpy
from mathutils import Matrix, Vector

from kit import look as L
from kit import toon
from studio import core as C


def milk(
    name: str = "milk",
    loc: Sequence[float] = (0.0, 0.0, 0.0),
    col: bpy.types.Collection | None = None,
) -> bpy.types.Object:
    """Build a milk carton prop with gable top, blue band, and 'MILK' text as one mesh."""
    bm = bmesh.new()

    # 1. Main carton box (0.12 x 0.12 x 0.24) and gable top (0.05 high, ridge along X)
    # Origin at bottom centre: x in [-0.06, 0.06], y in [-0.06, 0.06], z in [0.0, 0.24]
    v0 = bm.verts.new(Vector((-0.06, -0.06, 0.0)))
    v1 = bm.verts.new(Vector((0.06, -0.06, 0.0)))
    v2 = bm.verts.new(Vector((0.06, 0.06, 0.0)))
    v3 = bm.verts.new(Vector((-0.06, 0.06, 0.0)))

    v4 = bm.verts.new(Vector((-0.06, -0.06, 0.24)))
    v5 = bm.verts.new(Vector((0.06, -0.06, 0.24)))
    v6 = bm.verts.new(Vector((0.06, 0.06, 0.24)))
    v7 = bm.verts.new(Vector((-0.06, 0.06, 0.24)))

    v8 = bm.verts.new(Vector((-0.06, 0.0, 0.29)))
    v9 = bm.verts.new(Vector((0.06, 0.0, 0.29)))

    # Faces with outward normals (material slot 0: white)
    carton_faces = [
        bm.faces.new([v0, v3, v2, v1]),  # bottom (-Z)
        bm.faces.new([v0, v1, v5, v4]),  # back (-Y)
        bm.faces.new([v1, v2, v6, v5]),  # right (+X)
        bm.faces.new([v2, v3, v7, v6]),  # front (+Y)
        bm.faces.new([v3, v0, v4, v7]),  # left (-X)
        bm.faces.new([v4, v8, v7]),      # gable left (-X)
        bm.faces.new([v5, v6, v9]),      # gable right (+X)
        bm.faces.new([v4, v5, v9, v8]),  # gable roof (-Y)
        bm.faces.new([v6, v7, v8, v9]),  # gable roof (+Y)
    ]
    for f in carton_faces:
        f.material_index = 0

    # 2. Blue band around the carton at z 0.09-0.15 (4 thin quads 2 mm outside the faces)
    b_y_pos = bm.faces.new([
        bm.verts.new(Vector((-0.062, 0.062, 0.09))),
        bm.verts.new(Vector((0.062, 0.062, 0.09))),
        bm.verts.new(Vector((0.062, 0.062, 0.15))),
        bm.verts.new(Vector((-0.062, 0.062, 0.15))),
    ])
    b_y_neg = bm.faces.new([
        bm.verts.new(Vector((0.062, -0.062, 0.09))),
        bm.verts.new(Vector((-0.062, -0.062, 0.09))),
        bm.verts.new(Vector((-0.062, -0.062, 0.15))),
        bm.verts.new(Vector((0.062, -0.062, 0.15))),
    ])
    b_x_pos = bm.faces.new([
        bm.verts.new(Vector((0.062, 0.062, 0.09))),
        bm.verts.new(Vector((0.062, -0.062, 0.09))),
        bm.verts.new(Vector((0.062, -0.062, 0.15))),
        bm.verts.new(Vector((0.062, 0.062, 0.15))),
    ])
    b_x_neg = bm.faces.new([
        bm.verts.new(Vector((-0.062, -0.062, 0.09))),
        bm.verts.new(Vector((-0.062, 0.062, 0.09))),
        bm.verts.new(Vector((-0.062, 0.062, 0.15))),
        bm.verts.new(Vector((-0.062, -0.062, 0.15))),
    ])
    for f in [b_y_pos, b_y_neg, b_x_pos, b_x_neg]:
        f.material_index = 1

    # 3. Text "MILK" on +Y face of the band
    txt_obj = C.text(
        f"{name}_text_temp",
        "MILK",
        size=0.045,
        extrude=0.0,
        loc=(0.0, 0.063, 0.12),
        rot=(90.0, 0.0, 180.0),
        col=col,
    )
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    txt_eval = txt_obj.evaluated_get(depsgraph)
    txt_mesh = bpy.data.meshes.new_from_object(txt_eval)
    txt_mesh.transform(txt_obj.matrix_world)

    vert_map = {}
    for v in txt_mesh.vertices:
        vert_map[v.index] = bm.verts.new(v.co)
    bm.verts.ensure_lookup_table()
    for p in txt_mesh.polygons:
        face_verts = [vert_map[i] for i in p.vertices]
        try:
            f = bm.faces.new(face_verts)
            f.material_index = 2
        except ValueError:
            pass

    curve_data = txt_obj.data
    bpy.data.objects.remove(txt_obj, do_unlink=True)
    bpy.data.meshes.remove(txt_mesh)
    if curve_data and curve_data.users == 0:
        bpy.data.curves.remove(curve_data)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    mat_white = L.toon2("milk_white", "#f2f2ee", rim=0.0)
    mat_blue = L.toon2("milk_blue", "#2e6fd8", rim=0.0)
    mat_text = L.toon2("milk_text", "#f2f2ee", rim=0.0)

    mesh.materials.append(mat_white)
    mesh.materials.append(mat_blue)
    mesh.materials.append(mat_text)

    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    C.link(obj, col)
    bpy.context.view_layer.update()
    scale_x = obj.matrix_world.to_scale()[0]
    thickness = 0.004 / scale_x if scale_x != 0 else 0.004
    toon.add_outline(obj, thickness=thickness)
    return obj


def batarang(
    name: str = "batarang",
    loc: Sequence[float] = (0.0, 0.0, 0.0),
    col: bpy.types.Collection | None = None,
) -> bpy.types.Object:
    """Build a batarang prop scaled to width 0.30, extruded 0.012, origin at centre."""
    bat_half = [
        (0.00, 0.08),
        (0.04, 0.08),
        (0.055, 0.18),
        (0.08, 0.08),
        (0.15, 0.11),
        (0.30, 0.17),
        (0.50, 0.21),
        (0.46, 0.08),
        (0.40, 0.00),
        (0.35, 0.05),
        (0.30, -0.04),
        (0.24, 0.00),
        (0.19, -0.08),
        (0.13, -0.05),
        (0.06, -0.13),
        (0.00, -0.20),
    ]
    bat_mirrored = [(-x, z) for x, z in reversed(bat_half[1:-1])]
    bat_pts = bat_half + bat_mirrored

    # Scaled to width 0.30 (native width is 1.0, so scale factor is 0.30)
    # y = outline's z, origin at the centre
    min_z = min(pz for _, pz in bat_pts)
    max_z = max(pz for _, pz in bat_pts)
    cz = (min_z + max_z) / 2.0
    pts_2d = [(px * 0.30, (pz - cz) * 0.30) for px, pz in bat_pts]

    bm = bmesh.new()
    verts = [bm.verts.new(Vector((x, y, -0.006))) for x, y in pts_2d]
    face = bm.faces.new(verts)
    res = bmesh.ops.extrude_face_region(bm, geom=[face])
    extruded_verts = [ele for ele in res["geom"] if isinstance(ele, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=Vector((0.0, 0.0, 0.012)), verts=extruded_verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    mat = L.toon2("batarang", "#1a1d26", rim=0.0)
    mesh.materials.append(mat)

    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    C.link(obj, col)
    bpy.context.view_layer.update()
    scale_x = obj.matrix_world.to_scale()[0]
    thickness = 0.003 / scale_x if scale_x != 0 else 0.003
    toon.add_outline(obj, thickness=thickness)
    return obj


def smoke_puff(
    name: str,
    center: Sequence[float] | Vector,
    frame: int,
    *,
    count: int = 9,
    radius: float = 0.9,
    seed: int = 0,
    col: bpy.types.Collection | None = None,
) -> list[bpy.types.Object]:
    """Create animated smoke puff icospheres scaling and rising over time."""
    rng = random.Random(seed)
    mat = L.toon2("smoke", "#9aa0ab", rim=0.0)
    objs: list[bpy.types.Object] = []
    c_vec = Vector(center)

    for i in range(count):
        r_sph = rng.uniform(0.25, 0.45)
        dx = rng.uniform(-radius, radius)
        dy = rng.uniform(-radius * 0.6, radius * 0.6)
        dz = rng.uniform(0.1, 1.3)
        loc = c_vec + Vector((dx, dy, dz))

        obj = C.icosphere(
            f"{name}_{i}",
            r=r_sph,
            subdiv=2,
            loc=loc,
            mat=mat,
            col=col,
            smooth=True,
        )
        bpy.context.view_layer.update()
        scale_x = obj.matrix_world.to_scale()[0]
        thickness = 0.008 / scale_x if scale_x != 0 else 0.008
        toon.add_outline(obj, thickness=thickness)

        # Scale keys
        C.key(obj, frame - 1, scale=(0.0, 0.0, 0.0))
        C.key(obj, frame + 3, scale=(1.15, 1.15, 1.15))
        C.key(obj, frame + 6, scale=(1.0, 1.0, 1.0))
        C.key(obj, frame + 30 + i, scale=(1.0, 1.0, 1.0))
        C.key(obj, frame + 42 + i, scale=(0.0, 0.0, 0.0))

        # Z location keys
        C.key(obj, frame, loc=(loc.x, loc.y, loc.z))
        C.key(obj, frame + 42, loc=(loc.x, loc.y, loc.z + 0.25))

        objs.append(obj)

    return objs
