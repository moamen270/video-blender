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


SKIN = {"dummy": DUMMY, "ryu": "#d9a47a", "ken": "#e8bb92"}


def _arm_t(qc: Q.QChar, v, bone: str) -> tuple[float, Vector, Vector]:
    """(t along the bone 0..1, closest axis point, radial vector) for a rest vertex."""
    b = qc.arm.data.bones[bone]
    h, t = b.head_local, b.tail_local
    ax = t - h
    s = max(0.0, min(1.0, (v.co - h).dot(ax) / ax.length_squared))
    p = h + ax * s
    return s, p, v.co - p


def shape_arms(qc: Q.QChar, bicep: float = 0.34, forearm: float = 0.24, wrist: float = 0.22) -> None:
    """Give the pack's tube arms an anatomy (bicep bulge, forearm swell tapering to the wrist) by
    scaling rest vertices around each bone axis. Tube arms + mitten fists read as horse legs."""
    vg = qc.body.vertex_groups
    names = {g.index: g.name for g in vg}
    for v in qc.body.data.vertices:
        if not v.groups:
            continue
        g = max(v.groups, key=lambda x: x.weight)
        bone = names.get(g.group, "")
        if bone.startswith("UpperArm."):
            s, p, r = _arm_t(qc, v, bone)
            f = 1.0 + bicep * math.sin(math.pi * min(1.0, s / 0.85))
        elif bone.startswith("LowerArm."):
            s, p, r = _arm_t(qc, v, bone)
            f = 1.0 + forearm * math.sin(math.pi * min(1.0, s / 0.55)) - wrist * max(0.0, (s - 0.55) / 0.45)
        else:
            continue
        v.co = p + r * f
    qc.body.data.update()


def add_thumbs(qc: Q.QChar, skin_m: bpy.types.Material, col) -> None:
    """A small thumb on the inner-front side of each fist: a block fist reads as a hand with it."""
    for side, k in (("L", 1.0), ("R", -1.0)):
        b = qc.arm.data.bones[f"Fist.{side}"]
        h, t = b.head_local, b.tail_local
        ax = (t - h)
        # rest pose is a T-pose (arms along x, palms down): the thumb sits on the front (-y) of the fist
        pos = h + ax * 0.40 + Vector((0.0, -0.13, 0.03))
        world = qc.arm.matrix_world @ pos
        th = C.sphere(f"{qc.name}_thumb.{side}", r=0.045, loc=world, scale=(1.0, 1.0, 1.7), mat=skin_m, col=col)
        th.rotation_euler = ax.to_track_quat("Z", "Y").to_euler()
        Q.attach_part(qc, th, f"Fist.{side}", f"thumb.{side}")
        Q.outline(th, 0.008)


def fingerless_gloves(qc: Q.QChar, skin_m: bpy.types.Material, glove_m: bpy.types.Material) -> None:
    """Fist faces become skin (a hand, not a hoof); the glove is a wrap on the wrist end of the forearm
    and the back of the hand."""
    Q.assign(qc, skin_m, bones=["Fist.L", "Fist.R"])
    me = qc.body.data
    gi = list(me.materials).index(glove_m) if glove_m.name in [m.name for m in me.materials] else None
    if gi is None:
        me.materials.append(glove_m)
        gi = len(me.materials) - 1
    names = {g.index: g.name for g in qc.body.vertex_groups}

    def dominant(poly) -> str:
        return Q.dominant_bone(qc.body, poly)

    for poly in me.polygons:
        bone = dominant(poly)
        if bone.startswith("LowerArm."):
            b = qc.arm.data.bones[bone]
            ax = b.tail_local - b.head_local
            s = (poly.center - b.head_local).dot(ax) / ax.length_squared
            if s > 0.78:                                      # wrist wrap
                poly.material_index = gi
        elif bone.startswith("Fist."):
            b = qc.arm.data.bones[bone]
            ax = b.tail_local - b.head_local
            s = (poly.center - b.head_local).dot(ax) / ax.length_squared
            if s < 0.45:                                      # back of the hand, near the wrist
                poly.material_index = gi
    me.update()
    del names


def _fighter(name: str, *, gi: str, lapel_hex: str, belt: str, hair_file: str, hair: str, headband: str | None,
             gloves: str, skin: str, expression: str, hair_lift: float = 0.0,
             col: bpy.types.Collection | None = None) -> Q.QChar:
    """Street-fighter build on Quaternius Kimono_Male: gi colour, belt, headband or none, hair from
    another pack model, gloves, bare feet."""
    qc = Q.load_character("Kimono_Male.blend", name, col=col)
    target_col = col or (qc.body.users_collection[0] if qc.body.users_collection else None)
    dummy = skin == DUMMY
    # decal eyes/brows: white on the black dummy head, dark ink on skin tones
    F.build_face(qc, rest="frown", paint_hex="#f4f4ef" if dummy else "#241812")
    F.set_expression(qc.face, expression)
    skin_m = L.toon2(f"{name}_skin", skin)
    gi_m = L.toon2(f"{name}_gi", gi)
    Q.assign(qc, skin_m, materials=["Skin"])
    Q.assign(qc, gi_m, materials=["Clothes"])
    # sleeveless gi (the torn-off sleeves are the character): arms are bare, shoulders keep the gi
    # (after the recolour the gi faces carry gi_m, so select by that material, not the pack's "Clothes")
    Q.assign(qc, skin_m, materials=[gi_m.name], bones=["UpperArm.L", "UpperArm.R", "LowerArm.L", "LowerArm.R"])
    # V-neck: a skin triangle on the chest (the low-poly chest is too coarse to select faces for it)
    tri = [(-0.185, 2.07), (0.185, 2.07), (0.0, 1.62)]
    surf = Q.surface_points(qc, tri, bones=CHEST, offset=0.008)
    centre = Q.native(qc, Q.surface_points(qc, [(0.0, 1.92)], bones=CHEST, offset=0.008)[0])
    vneck = _ngon_object(f"{name}_vneck", [Q.native(qc, pt) for pt in surf], centre, skin_m, col=target_col)
    Q.attach_part(qc, vneck, "Torso", "vneck")
    # lapels: two overlapping strips along the V edges, a shade darker than the gi
    lapel = L.toon2(f"{name}_lapel", lapel_hex)
    for k, side in ((1, "L"), (-1, "R")):
        quad = [(k * 0.215, 2.06), (k * 0.155, 2.06), (-k * 0.02, 1.60), (k * 0.04, 1.60)]
        surf = Q.surface_points(qc, quad, bones=CHEST, offset=0.012)
        world = [Q.native(qc, pt) for pt in surf]
        centre = Q.native(qc, Q.surface_points(qc, [(k * 0.10, 1.83)], bones=CHEST, offset=0.012)[0])
        strip = _ngon_object(f"{name}_lapel.{side}", world, centre, lapel, col=target_col)
        Q.attach_part(qc, strip, "Torso", f"lapel.{side}")
    # the pack's red "Band" material is both the belt (low) and the headband (high)
    Q.assign(qc, L.toon2(f"{name}_belt", belt), materials=["Band"], z_range=(-1.0, 2.0))
    hair_m = L.toon2(f"{name}_hair", hair)
    if headband:
        band_m = L.toon2(f"{name}_band", headband)
        Q.assign(qc, band_m, materials=["Band"], z_range=(2.0, 9.0))
        # the pack's headband tails stand straight up (they read as bunny ears): remove them
        bm = bmesh.new()
        bm.from_mesh(qc.body.data)
        bi = list(qc.body.data.materials).index(band_m)
        tails = [f for f in bm.faces if f.material_index == bi and f.calc_center_median().z > 2.98]
        bmesh.ops.delete(bm, geom=tails, context="FACES")
        bm.to_mesh(qc.body.data)
        bm.free()
        qc.body.data.update()
    else:
        Q.assign(qc, hair_m, materials=["Band"], z_range=(2.0, 9.0))
    shape_arms(qc)
    fingerless_gloves(qc, skin_m, L.toon2(f"{name}_gloves", gloves))
    add_thumbs(qc, skin_m, target_col)
    Q.assign(qc, skin_m, bones=["Foot.L", "Foot.R"])            # barefoot
    part = Q.take_part(qc, hair_file, "Hair", "hair", hair_m)
    if hair_lift:
        # raise the fringe so the brows (decals at z 2.47-2.75) stay visible; the crown moves less
        for v in part.data.vertices:
            if v.co.y < 0.0:                                 # front half only
                t = max(0.0, min(1.0, (3.0 - v.co.z) / 0.8))  # 1 at the fringe, 0 at the crown
                v.co.z += hair_lift * t
        part.data.update()
    Q.smooth(qc)
    Q.outline(qc.body, 0.010)
    Q.outline(part, 0.010)
    return qc


def build_ryu(col: bpy.types.Collection | None = None, skin: str = "skin") -> Q.QChar:
    """Ryu parody: white gi, black belt, red headband, red gloves, dark spiky hair."""
    return _fighter("ryu", gi="#efece2", lapel_hex="#cfc9b8", belt="#1b1b1f", hair_file="Casual3_Male.blend", hair="#2a1d16",
                    headband="#d0262b", gloves="#b3261e", skin=SKIN["ryu"] if skin == "skin" else DUMMY,
                    expression="stern", col=col)


def build_ken(col: bpy.types.Collection | None = None, skin: str = "skin") -> Q.QChar:
    """Ken parody: red gi, black belt, no headband, blond swept hair, dark gloves."""
    return _fighter("ken", gi="#c8242b", lapel_hex="#94161c", belt="#1b1b1f", hair_file="Casual_Male.blend",
                    hair="#f1c54a", hair_lift=0.22,
                    headband=None, gloves="#2a2a2e", skin=SKIN["ken"] if skin == "skin" else DUMMY,
                    expression="smug", col=col)


CAST = {
    "batman": build_batman,
    "joker": build_joker,
    "ryu": build_ryu,
    "ken": build_ken,
    "ryu_dummy": lambda col=None: build_ryu(col, skin="dummy"),
    "ken_dummy": lambda col=None: build_ken(col, skin="dummy"),
    "vader": lambda col=None: __import__("kit.starwars", fromlist=["x"]).build_vader(col),
    "luke": lambda col=None: __import__("kit.starwars", fromlist=["x"]).build_luke(col),
}
