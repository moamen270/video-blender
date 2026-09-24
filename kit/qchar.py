"""Quaternius character loader and manipulation library (Task E1)."""
from __future__ import annotations

import os
import math
from dataclasses import dataclass, field
from typing import Sequence

import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

from studio import core as C
import kit.rig
import kit.toon
from kit import rig, toon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "assets", "library", "quaternius", "ultimate_animated_character")
NATIVE_HEIGHT = 3.147


@dataclass
class QChar:
    name: str
    root: bpy.types.Object
    arm: bpy.types.Object
    body: bpy.types.Object
    actions: dict[str, bpy.types.Action]  # clean name -> action, e.g. "Idle"
    scale: float  # s
    parts: dict[str, bpy.types.Object] = field(default_factory=dict)
    face: object | None = None  # set by kit.face.build_face


def strip(name: str) -> str:
    """Return name with .001 suffix removed."""
    return name.split(".")[0]


def load_character(
    file: str,
    name: str,
    *,
    height: float = 1.80,
    loc: Sequence[float] = (0, 0, 0),
    rot_z: float = 0.0,
    col: bpy.types.Collection | None = None,
) -> QChar:
    """Load a Quaternius character .blend file and set up root, scale, and actions."""
    if not file.endswith(".blend"):
        file = f"{file}.blend"
    path = os.path.join(LIB, file)

    with bpy.data.libraries.load(path, link=False) as (src, dst):
        names = list(src.actions)
        dst.objects = list(src.objects)
        dst.actions = list(names)

    actions: dict[str, bpy.types.Action] = {}
    for n, a in zip(names, dst.actions):
        clean = strip(n)
        a.name = f"{name}_{clean}"
        actions[clean] = a

    arm = next(o for o in dst.objects if o.type == "ARMATURE")
    body = next(o for o in dst.objects if o.type == "MESH")

    C.link(arm, col)
    C.link(body, col)

    arm.name = f"{name}_arm"
    if arm.data:
        arm.data.name = f"{name}_arm"

    body.name = f"{name}_body"
    if body.data:
        body.data.name = f"{name}_body"

    root = C.empty(f"{name}_root", loc=loc, rot=(0, 0, rot_z), col=col)
    s = height / NATIVE_HEIGHT

    arm.parent = root
    arm.matrix_parent_inverse = Matrix.Identity(4)
    arm.location = (0.0, 0.0, 0.0)
    arm.rotation_euler = (0.0, 0.0, math.pi)
    arm.scale = (s, s, s)

    body.parent = arm
    body.matrix_parent_inverse = Matrix.Identity(4)
    for m in body.modifiers:
        if m.type == "ARMATURE":
            m.object = arm

    if arm.animation_data:
        arm.animation_data.action = None

    qc = QChar(name=name, root=root, arm=arm, body=body, actions=actions, scale=s)
    rest(qc)
    print(f"[qchar] loaded {name} from {file} ({len(actions)} actions)", flush=True)
    return qc


def rest(qc: QChar) -> None:
    """Reset the character to rest pose and clear active action."""
    if qc.arm.animation_data:
        qc.arm.animation_data.action = None
    if qc.arm.pose:
        for pb in qc.arm.pose.bones:
            pb.rotation_mode = "QUATERNION"
            pb.location = (0.0, 0.0, 0.0)
            pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
            pb.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()


def native(qc: QChar, xyz: Sequence[float] | Vector) -> Vector:
    """Convert native character coordinates to world coordinates."""
    bpy.context.view_layer.update()
    return qc.arm.matrix_world @ Vector(xyz)


def dominant_bone(obj: bpy.types.Object, poly) -> str:
    """Return the vertex group name with largest weight sum over polygon's vertices; '' if none."""
    group_weights: dict[str, float] = {}
    vg = obj.vertex_groups
    mesh = obj.data
    vert_indices = poly.vertices if hasattr(poly, "vertices") else [v.index for v in poly.verts]
    for v_idx in vert_indices:
        for g in mesh.vertices[v_idx].groups:
            if g.group < len(vg):
                name = vg[g.group].name
                group_weights[name] = group_weights.get(name, 0.0) + g.weight
    if not group_weights:
        return ""
    best_name = max(group_weights, key=group_weights.get)
    if group_weights[best_name] <= 0.0:
        return ""
    return best_name


def assign(
    qc: QChar,
    mat: bpy.types.Material,
    *,
    materials: list[str] | None = None,
    bones: list[str] | None = None,
    z_range: tuple[float, float] | None = None,
    absx_min: float | None = None,
    obj: bpy.types.Object | None = None,
) -> int:
    """Assign material to matching polygons of obj (or qc.body)."""
    target = obj if obj is not None else qc.body
    mesh = target.data

    slot_idx = -1
    for idx, m in enumerate(mesh.materials):
        if m == mat:
            slot_idx = idx
            break
    if slot_idx == -1:
        mesh.materials.append(mat)
        slot_idx = len(mesh.materials) - 1

    stripped_materials = {strip(m) for m in materials} if materials is not None else None
    bones_set = set(bones) if bones is not None else None

    count = 0
    for poly in mesh.polygons:
        if stripped_materials is not None:
            if poly.material_index < len(mesh.materials) and mesh.materials[poly.material_index] is not None:
                cur_mat = strip(mesh.materials[poly.material_index].name)
                if cur_mat not in stripped_materials:
                    continue
            else:
                continue

        if bones_set is not None:
            db = dominant_bone(target, poly)
            if db not in bones_set:
                continue

        if z_range is not None:
            z0, z1 = z_range
            if not (z0 <= poly.center.z <= z1):
                continue

        if absx_min is not None:
            if not (abs(poly.center.x) >= absx_min):
                continue

        poly.material_index = slot_idx
        count += 1

    mesh.update()
    print(f"[qchar] assign {mat.name}: {count} polygons", flush=True)
    return count


def delete_faces(
    qc: QChar,
    materials: list[str],
    obj: bpy.types.Object | None = None,
) -> int:
    """Delete polygons whose stripped material name is in materials."""
    target = obj if obj is not None else qc.body
    stripped_targets = {strip(m) for m in materials}
    mesh = target.data

    bm = bmesh.new()
    bm.from_mesh(mesh)

    mats = mesh.materials
    faces_to_delete = []
    for face in bm.faces:
        if face.material_index < len(mats) and mats[face.material_index] is not None:
            if strip(mats[face.material_index].name) in stripped_targets:
                faces_to_delete.append(face)

    count = len(faces_to_delete)
    if faces_to_delete:
        bmesh.ops.delete(bm, geom=faces_to_delete, context="FACES")
        bm.to_mesh(mesh)
        mesh.update()
    bm.free()
    return count


def take_part(
    qc: QChar,
    file: str,
    material: str,
    part: str,
    mat: bpy.types.Material,
) -> bpy.types.Object:
    """Extract a part from another character file, retarget to qc.arm, and assign mat."""
    if not file.endswith(".blend"):
        file = f"{file}.blend"
    path = os.path.join(LIB, file)

    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = list(src.objects)

    mesh_obj = next(o for o in dst.objects if o.type == "MESH")
    other_objs = [o for o in dst.objects if o != mesh_obj]

    old_mesh_data = mesh_obj.data
    mesh_obj.data = old_mesh_data.copy()
    if old_mesh_data.users == 0:
        bpy.data.meshes.remove(old_mesh_data)

    part_name = f"{qc.name}_{part}"
    mesh_obj.name = part_name
    mesh_obj.data.name = part_name

    body_cols = qc.body.users_collection
    target_col = body_cols[0] if body_cols else bpy.context.scene.collection
    C.link(mesh_obj, target_col)

    stripped_wanted = strip(material)
    bm = bmesh.new()
    bm.from_mesh(mesh_obj.data)
    mats = mesh_obj.data.materials
    faces_to_delete = []
    for face in bm.faces:
        if face.material_index < len(mats) and mats[face.material_index] is not None:
            if strip(mats[face.material_index].name) != stripped_wanted:
                faces_to_delete.append(face)
        else:
            faces_to_delete.append(face)
    if faces_to_delete:
        bmesh.ops.delete(bm, geom=faces_to_delete, context="FACES")
        loose_verts = [v for v in bm.verts if not v.link_faces]
        if loose_verts:
            bmesh.ops.delete(bm, geom=loose_verts, context="VERTS")
        bm.to_mesh(mesh_obj.data)
        mesh_obj.data.update()
    bm.free()

    mesh_obj.data.materials.clear()
    mesh_obj.data.materials.append(mat)
    for p in mesh_obj.data.polygons:
        p.material_index = 0

    mesh_obj.parent = qc.arm
    mesh_obj.matrix_parent_inverse = Matrix.Identity(4)
    mesh_obj.location = (0.0, 0.0, 0.0)
    mesh_obj.rotation_euler = (0.0, 0.0, 0.0)
    mesh_obj.scale = (1.0, 1.0, 1.0)

    arm_mods = [m for m in mesh_obj.modifiers if m.type == "ARMATURE"]
    if arm_mods:
        arm_mods[0].object = qc.arm
        for m in arm_mods[1:]:
            mesh_obj.modifiers.remove(m)
    else:
        m = mesh_obj.modifiers.new("Armature", "ARMATURE")
        m.object = qc.arm

    for o in other_objs:
        arm_data = o.data if o.type == "ARMATURE" else None
        bpy.data.objects.remove(o, do_unlink=True)
        if arm_data and arm_data.users == 0:
            bpy.data.armatures.remove(arm_data)

    qc.parts[part] = mesh_obj
    return mesh_obj


def attach_part(qc: QChar, obj: bpy.types.Object, bone: str, part: str) -> None:
    """Parent an object to a character bone in rest pose."""
    kit.rig.attach(obj, qc.arm, bone)
    qc.parts[part] = obj


def surface_points(
    qc: QChar,
    pts_xz: list[tuple[float, float]],
    *,
    bones: list[str],
    materials: list[str] | None = None,
    offset: float = 0.006,
    side: str = "front",
) -> list[Vector]:
    """Return native points on the body surface by raycasting against rest mesh."""
    mesh = qc.body.data
    verts = [v.co for v in mesh.vertices]
    stripped_materials = {strip(m) for m in materials} if materials is not None else None
    bones_set = set(bones)

    polys = []
    for p in mesh.polygons:
        db = dominant_bone(qc.body, p)
        if db not in bones_set:
            continue
        if stripped_materials is not None:
            if p.material_index < len(mesh.materials) and mesh.materials[p.material_index] is not None:
                if strip(mesh.materials[p.material_index].name) not in stripped_materials:
                    continue
            else:
                continue
        p_verts = list(p.vertices)
        if len(p_verts) == 3:
            polys.append(tuple(p_verts))
        elif len(p_verts) == 4:
            polys.append((p_verts[0], p_verts[1], p_verts[2]))
            polys.append((p_verts[0], p_verts[2], p_verts[3]))
            polys.append((p_verts[1], p_verts[2], p_verts[3]))
            polys.append((p_verts[1], p_verts[3], p_verts[0]))
        else:
            for i in range(1, len(p_verts) - 1):
                polys.append((p_verts[0], p_verts[i], p_verts[i + 1]))

    if polys:
        try:
            bvh = BVHTree.FromPolygons(verts, polys, all_triangles=True, epsilon=0.0005)
        except Exception:
            try:
                bvh = BVHTree.FromPolygons(verts, polys)
            except Exception:
                bvh = None
    else:
        bvh = None

    if side == "front":
        ray_dir = Vector((0.0, 1.0, 0.0))
        y_start = -3.0
    else:
        ray_dir = Vector((0.0, -1.0, 0.0))
        y_start = 3.0

    def cast_one(qx: float, qz: float) -> Vector | None:
        if bvh is None:
            return None
        loc, normal, index, dist = bvh.ray_cast(Vector((qx, y_start, qz)), ray_dir)
        if loc is None:
            return None
        if side == "front" and loc.y > 0.0:
            return None
        if side == "back" and loc.y < 0.0:
            return None
        return loc

    jitters = [
        (0.0, 0.0),
        (0.001, 0.0),
        (-0.001, 0.0),
        (0.0, 0.001),
        (0.0, -0.001),
        (0.001, 0.001),
        (-0.001, -0.001),
        (0.002, 0.0),
        (-0.002, 0.0),
        (0.0005, 0.0),
        (-0.0005, 0.0),
    ]

    raw_hits: list[float | None] = []
    for x, z in pts_xz:
        hit_y: float | None = None
        for dx, dz in jitters:
            loc = cast_one(x + dx, z + dz)
            if loc is not None:
                hit_y = loc.y
                break
        if hit_y is None:
            print(f"[qchar] miss ({x:.3f}, {z:.3f})", flush=True)
        raw_hits.append(hit_y)

    valid_with_pts = [((px, pz), hy) for (px, pz), hy in zip(pts_xz, raw_hits) if hy is not None]
    if valid_with_pts:
        avg_y = sum(hy for _, hy in valid_with_pts) / len(valid_with_pts)
    else:
        avg_y = -0.21 if side == "front" else 0.20

    results: list[Vector] = []
    for (x, z), h_y in zip(pts_xz, raw_hits):
        if h_y is not None:
            actual_hit_y = h_y
        elif valid_with_pts:
            actual_hit_y = min(valid_with_pts, key=lambda item: (item[0][0] - x) ** 2 + (item[0][1] - z) ** 2)[1]
        else:
            actual_hit_y = avg_y

        if side == "front":
            res_y = actual_hit_y - offset
        else:
            res_y = actual_hit_y + offset
        results.append(Vector((x, res_y, z)))

    return results


def set_action(qc: QChar, action: str, frame: int | None = None) -> None:
    """Assign an action to the character's armature and optionally set the frame."""
    arm = qc.arm
    arm.animation_data_create()
    act = qc.actions[action]
    arm.animation_data.action = act
    if hasattr(arm.animation_data, "action_slot"):
        if arm.animation_data.action_slot is None and hasattr(act, "slots") and len(act.slots) > 0:
            try:
                arm.animation_data.action_slot = act.slots[0]
            except Exception:
                pass
    if frame is not None:
        bpy.context.scene.frame_set(frame)


def outline(obj: bpy.types.Object, world_thickness: float = 0.010) -> None:
    """Add toon outline scaled to world thickness."""
    bpy.context.view_layer.update()
    scale_x = obj.matrix_world.to_scale()[0]
    thickness = world_thickness / scale_x if scale_x != 0 else world_thickness
    kit.toon.add_outline(obj, thickness=thickness)


def height_now(qc: QChar) -> float:
    """Evaluated (evaluated_depsgraph_get) world z-extent of qc.body."""
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = qc.body.evaluated_get(depsgraph)
    mw = eval_obj.matrix_world
    zs: list[float] = []
    try:
        mesh = eval_obj.to_mesh()
        zs = [(mw @ v.co).z for v in mesh.vertices]
        eval_obj.to_mesh_clear()
    except Exception:
        pass
    if not zs:
        try:
            zs = [(mw @ v.co).z for v in eval_obj.data.vertices]
        except Exception:
            pass
    if not zs:
        zs = [(mw @ Vector(c)).z for c in eval_obj.bound_box]
    if not zs:
        return 0.0
    return max(zs) - min(zs)
