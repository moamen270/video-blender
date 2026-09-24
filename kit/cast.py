"""The recurring cast: Batman, Joker, and helper builders (Task E4)."""
from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Vector

import kit.cape
from kit import face as F
from kit import look as L
from kit import qchar as Q
from studio import core as C

CHEST = ["Torso", "Abdomen", "Shoulder.L", "Shoulder.R"]
DUMMY = "#1c1d24"


def _ngon_object(
    name: str,
    world_pts: list[Vector],
    centre_world: Vector,
    mat: bpy.types.Material,
    col: bpy.types.Collection | None = None,
) -> bpy.types.Object:
    """Build a mesh as a triangle fan around an appended centre vertex."""
    verts = [wpt - centre_world for wpt in world_pts]
    n = len(verts)
    verts.append(Vector((0.0, 0.0, 0.0)))
    faces = [[n, i, (i + 1) % n] for i in range(n)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    if mesh.polygons and sum(p.normal.y for p in mesh.polygons) < 0:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        for f in bm.faces:
            f.normal_flip()
        bm.to_mesh(mesh)
        mesh.update()
        bm.free()
    mesh.materials.append(mat)
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    obj.rotation_mode = "QUATERNION"
    obj.location = centre_world
    C.link(obj, col)
    return obj


def build_batman(col: bpy.types.Collection | None = None) -> Q.QChar:
    """Build Batman character."""
    qc = Q.load_character("BaseCharacter.blend", "batman", col=col)
    target_col = col or (qc.body.users_collection[0] if qc.body.users_collection else None)
    F.build_face(qc, rest="frown")
    F.set_expression(qc.face, "stern")

    suit = L.toon2("bat_suit", "#5d6470")
    dark = L.toon2("bat_dark", "#1a1d26")
    gold = L.toon2("bat_gold", "#e3b21c")
    ink = L.toon2("bat_ink", "#111318")

    Q.assign(qc, suit, materials=["Skin"])
    Q.assign(qc, dark, bones=["Head", "Neck"])
    Q.assign(qc, dark, bones=["Fist.L", "Fist.R"])
    Q.assign(qc, dark, bones=["LowerArm.L", "LowerArm.R"], absx_min=1.06)
    Q.assign(qc, dark, bones=["Foot.L", "Foot.R"])
    Q.assign(qc, dark, bones=["LowerLeg.L", "LowerLeg.R"], z_range=(-1.0, 0.40))

    belt = Q.take_part(qc, "Casual_Male.blend", "Belt", "belt", gold)
    bm = bmesh.new()
    bm.from_mesh(belt.data)
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * 0.03
    bm.to_mesh(belt.data)
    belt.data.update()
    bm.free()

    for k, side in [(1, "L"), (-1, "R")]:
        b = Q.native(qc, (k * 0.27, 0.0, 2.99))
        t = Q.native(qc, (k * 0.31, 0.0, 3.30))
        d = t - b
        ear = C.cone(
            f"batman_ear.{side}",
            r1=0.10 * qc.scale,
            r2=0.0,
            depth=d.length,
            loc=(b + t) / 2.0,
            mat=dark,
            col=target_col,
            verts=12,
        )
        ear.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        Q.attach_part(qc, ear, "Head", f"ear.{side}")

    cape = kit.cape.build_cape(qc, dark)
    dark.use_backface_culling = False

    oval_pts = F.superellipse(0.15, 0.08, 2.0, k=32)
    emblem_xz = [(x, 1.62 + z) for x, z in oval_pts]
    surf_emblem = Q.surface_points(qc, emblem_xz, bones=CHEST, offset=0.006)
    world_emblem = [Q.native(qc, pt) for pt in surf_emblem]
    centre_surf_emblem = Q.surface_points(qc, [(0.0, 1.62)], bones=CHEST, offset=0.006)[0]
    centre_world_emblem = Q.native(qc, centre_surf_emblem)
    emblem = _ngon_object("batman_emblem", world_emblem, centre_world_emblem, gold, col=target_col)
    Q.attach_part(qc, emblem, "Torso", "emblem")

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
    bat_xz = [(x * 0.236, 1.62 + z * 0.236) for x, z in bat_pts]
    surf_bat = Q.surface_points(qc, bat_xz, bones=CHEST, offset=0.012)
    world_bat = [Q.native(qc, pt) for pt in surf_bat]
    centre_surf_bat = Q.surface_points(qc, [(0.0, 1.62)], bones=CHEST, offset=0.012)[0]
    centre_world_bat = Q.native(qc, centre_surf_bat)
    bat_obj = _ngon_object("batman_bat", world_bat, centre_world_bat, ink, col=target_col)
    Q.attach_part(qc, bat_obj, "Torso", "bat")

    Q.smooth(qc)
    Q.smooth(qc, obj=cape)
    Q.outline(qc.body, 0.010)
    Q.outline(belt, 0.010)
    Q.outline(qc.parts["ear.L"], 0.010)
    Q.outline(qc.parts["ear.R"], 0.010)
    Q.outline(cape, 0.010)

    return qc


def build_joker(col: bpy.types.Collection | None = None) -> Q.QChar:
    """Build Joker character."""
    qc = Q.load_character("Suit_Male.blend", "joker", col=col)
    target_col = col or (qc.body.users_collection[0] if qc.body.users_collection else None)
    F.build_face(qc, style="grin", rest="X")
    F.set_expression(qc.face, "smug")

    Q.assign(qc, L.toon2("jok_suit", "#5b2a86"), materials=["Black"])
    Q.assign(qc, L.toon2("jok_vest", "#3e9b4f"), materials=["Shirt"])
    Q.assign(qc, L.toon2("jok_tie", "#e08a1e"), materials=["Details"])
    Q.assign(qc, L.toon2("jok_belt", "#2a1f3d"), materials=["Belt"])
    Q.assign(qc, L.toon2("jok_skin", DUMMY), materials=["Skin"])
    Q.assign(qc, L.toon2("jok_hair", "#35b24a"), materials=["Hair"])

    tag_pts = F.superellipse(0.22, 0.07, 6.0, k=32)  # readable in a two-shot
    pts_xz = [(x, 1.66 + z) for x, z in tag_pts]
    surf_tag = Q.surface_points(qc, pts_xz, bones=CHEST, offset=0.010)
    world_tag = [Q.native(qc, pt) for pt in surf_tag]
    centre_surf = Q.surface_points(qc, [(0.0, 1.66)], bones=CHEST, offset=0.010)[0]
    centre_world = Q.native(qc, centre_surf)

    mat_tag = L.toon2("tag_white", "#f2f2ee")
    tag_obj = _ngon_object("joker_tag", world_tag, centre_world, mat_tag, col=target_col)
    Q.attach_part(qc, tag_obj, "Torso", "tag")

    tag_world_width = max(p.x for p in world_tag) - min(p.x for p in world_tag)
    text_loc = centre_world + Vector((0.0, 0.004, 0.0))
    mat_ink = L.toon2("tag_ink", "#111318")
    text_obj = C.text(
        "joker_tag_text",
        "ASSISTANT",
        size=0.03,
        extrude=0.0,
        loc=text_loc,
        rot=(90, 0, 180),
        mat=mat_ink,
        col=target_col,
    )
    bpy.context.view_layer.update()
    if text_obj.dimensions.x > 0.0:
        s = (0.9 * tag_world_width) / text_obj.dimensions.x
        text_obj.scale = (s, s, s)
        bpy.context.view_layer.update()
    Q.attach_part(qc, text_obj, "Torso", "tag_text")

    Q.smooth(qc)
    Q.outline(qc.body, 0.010)

    return qc


CAST = {
    "batman": build_batman,
    "joker": build_joker,
}
