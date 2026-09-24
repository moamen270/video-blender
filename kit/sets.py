"""Kenney prop import, gotham_mart layout, and lighting flicker (Task G2)."""
from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from typing import Sequence

import bpy
from mathutils import Matrix, Vector

from studio import core as C
from kit import look
from kit import toon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = ROOT + "/assets/library/kenney/kenney_mini-market/Models/GLB format"
K = 2.4


@dataclass
class Mart:
    root: bpy.types.Object
    tube: bpy.types.Object
    tube_light: bpy.types.Object
    anchors: dict[str, Vector] = field(
        default_factory=lambda: {
            "checkout": Vector((0.0, 0.0, 0.0)),
            "aisle_entry": Vector((-2.4, 3.2, 0.0)),
            "aisle_mid": Vector((-2.4, 1.6, 0.0)),
        }
    )


def prop(
    model: str,
    *,
    loc: Sequence[float] = (0.0, 0.0, 0.0),
    rot_z: float = 0.0,
    scale: float = K,
    col: bpy.types.Collection | None = None,
    tint: float = 1.0,
) -> bpy.types.Object:
    """Import a Kenney glTF model as a scaled, toon-shaded prop with outline."""
    before_objs = set(bpy.data.objects)
    before_mats = set(bpy.data.materials)

    filepath = os.path.join(PACK, f"{model}.glb")
    if not os.path.isfile(filepath):
        filepath = f"{PACK}/{model}.glb"

    bpy.ops.import_scene.gltf(filepath=filepath)

    new_objs = set(bpy.data.objects) - before_objs
    new_mats = set(bpy.data.materials) - before_mats

    # Convert every new material with look.toon_tex (once per material)
    mat_map: dict[bpy.types.Material, bpy.types.Material] = {}
    for mat in new_mats:
        mat_map[mat] = look.toon_tex(mat, tint=tint)

    for obj in new_objs:
        if obj.type == "MESH":
            for slot in obj.material_slots:
                if slot.material in mat_map:
                    slot.material = mat_map[slot.material]

    # Empty name f"set_{model}_{n}"
    prefix = f"set_{model}_"
    max_idx = -1
    for o in bpy.data.objects:
        if o.name.startswith(prefix):
            suffix = o.name[len(prefix):].split(".")[0]
            if suffix.isdigit():
                max_idx = max(max_idx, int(suffix))
    n = max_idx + 1
    empty_name = f"set_{model}_{n}"

    root_empty = C.empty(empty_name, loc=loc, rot=(0.0, 0.0, rot_z), col=col)
    root_empty.scale = (scale, scale, scale)

    # Parent every imported top-level object to the new empty
    top_level = [o for o in new_objs if o.parent is None or o.parent not in new_objs]
    for o in top_level:
        o.parent = root_empty
        o.matrix_parent_inverse = Matrix.Identity(4)

    # Link to col if specified
    if col is not None:
        for o in new_objs:
            C.link(o, col)

    # Add outline 0.006 (world) to every mesh
    bpy.context.view_layer.update()
    for o in new_objs:
        if o.type == "MESH":
            ws = o.matrix_world.to_scale()[0]
            thickness = 0.006 / ws if ws > 1e-6 else 0.006
            toon.add_outline(o, thickness=thickness)

    return root_empty


def gotham_mart(col: bpy.types.Collection | None = None) -> Mart:
    """Build the Gotham Mart store set layout."""
    root = C.empty("mart_root", col=col)

    # 1. Floor tiles at half scale (a Kenney tile is a 2x2 checker: 1.2 m squares at K read as a chessboard),
    #    darkened for 3 A.M.; 10 x 10 tiles cover x -6..6, y -3..9 (senior review of the G2 stills).
    FK = K / 2
    tile0 = prop("floor", loc=(0.0, 0.0, 0.0), scale=FK, col=col, tint=0.55)
    tile0.parent = root
    tile0.matrix_parent_inverse = Matrix.Identity(4)

    bpy.context.view_layer.update()
    tile_meshes = [o for o in [tile0, *tile0.children_recursive] if o.type == "MESH"]
    pts = [m.matrix_world @ Vector(c) for m in tile_meshes for c in m.bound_box]
    bmin_x = min(p.x for p in pts)
    bmin_y = min(p.y for p in pts)

    # Reposition tile0 to (ix=0, iy=0) target:
    tile0.location = (-6.0 - bmin_x, -3.0 - bmin_y, 0.0)

    # Place remaining 24 floor tiles
    for ix in range(10):
        for iy in range(10):
            if ix == 0 and iy == 0:
                continue
            x = -6.0 + ix * 1.2 - bmin_x
            y = -3.0 + iy * 1.2 - bmin_y
            t = prop("floor", loc=(x, y, 0.0), scale=FK, col=col, tint=0.55)
            t.parent = root
            t.matrix_parent_inverse = Matrix.Identity(4)

    # 2. Back wall: wall x5 along y = -3.0, x = -4.8 .. 4.8, rot_z 0
    wall_xs = [-4.8, -2.4, 0.0, 2.4, 4.8]
    for x in wall_xs:
        # the wall model is 0.6 deep (1.44 m at K), centred on its origin: front face at y = -3.0
        w = prop("wall", loc=(x, -3.72, 0.0), rot_z=0.0, scale=K, col=col, tint=0.7)
        w.parent = root
        w.matrix_parent_inverse = Matrix.Identity(4)

    # 3. Freezers along the back wall: freezers-standing at x = -4.8, -2.4, 2.4, 4.8, y = -2.9, rot_z 180
    freezer_xs = [-4.8, -2.4, 2.4, 4.8]
    for x in freezer_xs:
        # spans local y 0..0.5 behind its origin -> at rot 180: world y -3.0..-1.8, front at -1.8
        fz = prop("freezers-standing", loc=(x, -1.8, 0.0), rot_z=180.0, scale=K, col=col, tint=0.9)
        fz.parent = root
        fz.matrix_parent_inverse = Matrix.Identity(4)

    # 4. Left aisle: shelf-boxes at x = -3.6, y = 1.2, 3.1, 5.0, rot_z 90
    shelf_boxes_ys = [1.2, 3.1, 5.0]
    for y in shelf_boxes_ys:
        sb = prop("shelf-boxes", loc=(-3.6, y, 0.0), rot_z=90.0, scale=K, col=col)
        sb.parent = root
        sb.matrix_parent_inverse = Matrix.Identity(4)

    # 5. Right aisle: shelf-bags at x = +3.6, same y, rot_z 90
    shelf_bags_ys = [1.2, 3.1, 5.0]
    for y in shelf_bags_ys:
        sg = prop("shelf-bags", loc=(3.6, y, 0.0), rot_z=90.0, scale=K, col=col)
        sg.parent = root
        sg.matrix_parent_inverse = Matrix.Identity(4)

    # 6. Sign "GOTHAM MART" (C.text, extrude 0.02, emission #ff3344 strength 2)
    # Centred at (0, -2.85, 2.15), scaled so it is 2.4 wide, facing +Y (rot (90, 0, 180))
    sign_mat = look.toon2("mart_sign_mat", "#ff3344", emission=2.0)
    sign = C.text(
        "mart_sign",
        "GOTHAM MART",
        size=1.0,
        extrude=0.02,
        loc=(0.0, -2.85, 2.15),
        rot=(90.0, 0.0, 180.0),  # (90, 0, 0) faces -Y and reads mirrored from the store side
        mat=sign_mat,
        col=col,
        align="CENTER",
        parent=root,
    )
    bpy.context.view_layer.update()
    if sign.dimensions.x > 1e-4:
        s = 2.4 / sign.dimensions.x
        sign.scale = (s, s, s)

    # 7. Tube light: box 1.2 x 0.08 x 0.05 at (0, 0.35, 2.6), emission #e6f4ff strength 4,
    # plus an AREA light (shape RECTANGLE, size 1.2 x 0.12, energy 80, colour #dff2ff)
    # at (0, 0.35, 2.55) pointing down
    tube_mat = look.toon2("tube_mat", "#e6f4ff", emission=4.0)
    tube = C.cube(
        "tube",
        size=1.0,
        scale=(1.2, 0.08, 0.05),
        loc=(0.0, 0.35, 2.6),
        mat=tube_mat,
        col=col,
        parent=root,
    )

    light_data = bpy.data.lights.new("tube_area", "AREA")
    light_data.shape = "RECTANGLE"
    light_data.size = 1.2
    light_data.size_y = 0.12
    light_data.energy = 80.0
    light_data.color = C.hex_rgb("#dff2ff")
    tube_light = bpy.data.objects.new("tube_area", light_data)
    C.link(tube_light, col)
    tube_light.parent = root
    tube_light.location = (0.0, 0.35, 2.55)
    tube_light.rotation_euler = (0.0, 0.0, 0.0)

    bpy.context.view_layer.update()

    return Mart(
        root=root,
        tube=tube,
        tube_light=tube_light,
        anchors={
            "checkout": Vector((0.0, 0.0, 0.0)),
            "aisle_entry": Vector((-2.4, 3.2, 0.0)),
            "aisle_mid": Vector((-2.4, 1.6, 0.0)),
        },
    )


def flicker(mart: Mart, frames: list[tuple[int, int]]) -> None:
    """Animate tube emission strength and area light energy to flicker OFF during frame ranges."""
    tube_mat = None
    if mart.tube and mart.tube.data and mart.tube.data.materials:
        tube_mat = mart.tube.data.materials[0]

    emit_socket = None
    if tube_mat and tube_mat.use_nodes and tube_mat.node_tree:
        for n in tube_mat.node_tree.nodes:
            if n.type == "EMISSION" and "Strength" in n.inputs:
                emit_socket = n.inputs["Strength"]
                break

    light_data = mart.tube_light.data if mart.tube_light else None

    all_frames = []
    for a, b in frames:
        # Key ON at a - 1
        if emit_socket:
            emit_socket.default_value = 4.0
            emit_socket.keyframe_insert("default_value", frame=a - 1)
        if light_data:
            light_data.energy = 80.0
            light_data.keyframe_insert("energy", frame=a - 1)

        # Key OFF at a
        if emit_socket:
            emit_socket.default_value = 0.1
            emit_socket.keyframe_insert("default_value", frame=a)
        if light_data:
            light_data.energy = 0.0
            light_data.keyframe_insert("energy", frame=a)

        # Key ON at b
        if emit_socket:
            emit_socket.default_value = 4.0
            emit_socket.keyframe_insert("default_value", frame=b)
        if light_data:
            light_data.energy = 80.0
            light_data.keyframe_insert("energy", frame=b)

        all_frames.extend([a - 1, a, b])

    anim_owners = [
        light_data,
        mart.tube_light,
        tube_mat.node_tree if tube_mat else None,
        tube_mat,
    ]
    for owner in anim_owners:
        if owner and hasattr(owner, "animation_data") and owner.animation_data and owner.animation_data.action:
            act = owner.animation_data.action
            fcs = []
            try:
                for layer in act.layers:
                    for strip in layer.strips:
                        for bag in strip.channelbags:
                            fcs.extend(bag.fcurves)
            except AttributeError:
                pass
            if not fcs and hasattr(act, "fcurves"):
                fcs = list(act.fcurves)
            for fc in fcs:
                for kp in fc.keyframe_points:
                    for f in all_frames:
                        if abs(kp.co.x - f) < 0.5:
                            kp.interpolation = "CONSTANT"
