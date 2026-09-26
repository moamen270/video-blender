"""Star Wars parody cast and props: Vader, Luke, the lightsaber (vader-vs-luke-duel, 2026-09-26).

Vader = BaseCharacter (like Batman: the approved cape) in black with a helmet sized from the measured head, a face
mask (lenses, cheek plates, grille), chest box with lights, shoulder plates and a belt. No face decals (he has a mask:
no lip sync; his lines play over the breathing). Luke = Kimono_Male (the wrap front reads as the black Jedi tunic),
sleeves kept, black boots, one black glove (right hand), sandy hair from Casual_Male.
Characters face world +y at rest (root rotation 0); parts are placed in world space at rest and bone-parented.
"""
from __future__ import annotations

import math

import bpy
from mathutils import Vector

import kit.cape
from kit import face as F
from kit import fight as FT
from kit import look as L
from kit import qchar as Q
from studio import core as C


def _head_bounds(qc: Q.QChar) -> tuple[Vector, Vector]:
    """World bbox of the body's head verts (above the Head bone's root) at rest."""
    neck = qc.arm.matrix_world @ qc.arm.data.bones["Head"].head_local
    pts = [qc.body.matrix_world @ v.co for v in qc.body.data.vertices]
    hv = [p for p in pts if p.z > neck.z + 0.04]
    lo = Vector((min(p.x for p in hv), min(p.y for p in hv), min(p.z for p in hv)))
    hi = Vector((max(p.x for p in hv), max(p.y for p in hv), max(p.z for p in hv)))
    return lo, hi


def _attach(qc, objs, bone, tag):
    for i, o in enumerate(objs):
        Q.attach_part(qc, o, bone, f"{tag}{i}")


def build_vader(col: bpy.types.Collection | None = None) -> Q.QChar:
    """Darth Vader parody."""
    qc = Q.load_character("BaseCharacter.blend", "vader", col=col)
    tc = col or (qc.body.users_collection[0] if qc.body.users_collection else None)
    black = L.toon2("vader_black", "#16171c")
    gloss = L.toon2("vader_gloss", "#22242b")
    grey = L.toon2("vader_grey", "#7b808a")
    dark_grey = L.toon2("vader_dgrey", "#3a3d45")
    lens = L.toon2("vader_lens", "#0b0c10")
    for s in qc.body.material_slots:
        if s.material:
            s.material = black

    lo, hi = _head_bounds(qc)
    c, h = (lo + hi) / 2, (hi - lo) / 2
    front = hi.y
    parts = []
    # dome: a little bigger than the head, the helmet sits over it
    parts.append(C.sphere("vader_dome", r=1.0, loc=c + Vector((0, -0.02, 0.04)),
                          scale=(h.x * 1.12, h.y * 1.14, h.z * 1.04), mat=gloss, col=tc))
    # the flared skirt: wide at the bottom, open at the front (the face mask fills it)
    skirt = C.cone("vader_skirt", r1=h.x * 1.42, r2=h.x * 1.02, depth=h.z * 0.9,
                   loc=Vector((c.x, c.y - 0.04, lo.z + h.z * 0.28)), mat=gloss, col=tc)
    parts.append(skirt)
    # eyes: big dark lenses, outer corners dropping (the menacing slant), a small glint so they read as glass
    for s in (-1, 1):
        e = C.sphere(f"vader_eye{s}", r=1.0, loc=Vector((c.x + s * h.x * 0.38, front - 0.005, c.z + h.z * 0.08)),
                     rot=(0, s * 22, 0), scale=(h.x * 0.34, 0.022, h.z * 0.24), mat=lens, col=tc)
        parts.append(e)
        parts.append(C.sphere(f"vader_glint{s}", r=1.0, loc=Vector((c.x + s * h.x * 0.30, front + 0.016, c.z + h.z * 0.16)),
                              scale=(h.x * 0.06, 0.01, h.z * 0.04), mat=L.toon2("vader_glint", "#8d96a8", rim=0.0), col=tc))
    # cheek plates (grey) and the nose ridge
    for s in (-1, 1):
        parts.append(C.cube(f"vader_cheek{s}", size=1.0, loc=Vector((c.x + s * h.x * 0.45, front + 0.01, c.z - h.z * 0.3)),
                            rot=(0, s * 20, 0), scale=(h.x * 0.34, 0.04, h.z * 0.34), mat=grey, col=tc))
    parts.append(C.cube("vader_nose", size=1.0, loc=Vector((c.x, front + 0.035, c.z - h.z * 0.12)),
                        scale=(h.x * 0.16, 0.05, h.z * 0.32), mat=dark_grey, col=tc))
    # mouth grille: a downward triangle with three slits
    # a flat triangular plate, point down (a 3-sided cylinder turned to face the front)
    grille = C.cylinder("vader_grille", r=h.x * 0.36, depth=0.04, loc=Vector((c.x, front + 0.02, c.z - h.z * 0.5)),
                        rot=(-90, 0, 0), mat=grey, col=tc, verts=3)
    parts.append(grille)
    for k in (-1, 0, 1):
        parts.append(C.cube(f"vader_slit{k}", size=1.0, loc=Vector((c.x + k * h.x * 0.12, front + 0.058, c.z - h.z * 0.52)),
                            scale=(0.012, 0.01, h.z * 0.2), mat=lens, col=tc))
    _attach(qc, parts, "Head", "helmet")

    # chest box with lights, found on the chest surface (Batman's emblem position)
    chest = Q.native(qc, Q.surface_points(qc, [(0.0, 1.62)], bones=["Torso", "Abdomen"], offset=0.01)[0])
    box = C.cube("vader_chestbox", size=1.0, loc=chest + Vector((0, 0.02, 0.0)), scale=(0.17, 0.035, 0.12),
                 mat=dark_grey, col=tc)
    lights = [C.cube(f"vader_light{i}", size=1.0, loc=chest + Vector((-0.05 + 0.05 * i, 0.042, 0.02 - 0.03 * (i == 1))),
                     scale=(0.028, 0.012, 0.022), mat=FT.emit_mat(f"vader_l{i}", ["#ff3a30", "#36ff6a", "#3a8cff"][i], 7.0),
                     col=tc) for i in range(3)]
    _attach(qc, [box, *lights], "Torso", "chest")
    # shoulder plates
    for side, k in (("L", 1), ("R", -1)):
        b = qc.arm.data.bones[f"UpperArm.{side}"]
        p = qc.arm.matrix_world @ b.head_local
        sp = C.sphere(f"vader_shoulder.{side}", r=1.0, loc=p + Vector((0, 0.0, 0.05)), scale=(0.13, 0.13, 0.06),
                      mat=gloss, col=tc)
        Q.attach_part(qc, sp, "Torso", f"shoulder.{side}")
    # belt with two silver boxes
    hip = qc.arm.matrix_world @ qc.arm.data.bones["Abdomen"].head_local
    belt = C.cylinder("vader_belt", r=1.0, depth=0.07, loc=hip + Vector((0, 0, 0.02)), scale=(0.2, 0.15, 1.0),
                      mat=dark_grey, col=tc)
    buckles = [C.cube(f"vader_buckle{s}", size=1.0, loc=hip + Vector((s * 0.08, 0.15, 0.02)), scale=(0.06, 0.02, 0.06),
                      mat=grey, col=tc) for s in (-1, 1)]
    _attach(qc, [belt, *buckles], "Abdomen", "belt")

    cape = kit.cape.build_cape(qc, black)
    black.use_backface_culling = False
    Q.smooth(qc)
    Q.smooth(qc, obj=cape)
    Q.outline(qc.body, 0.010)
    Q.outline(cape, 0.010)
    for n in ("vader_dome", "vader_skirt"):
        Q.outline(bpy.data.objects[n], 0.008)
    return qc


def build_luke(col: bpy.types.Collection | None = None) -> Q.QChar:
    """Luke Skywalker parody (Return of the Jedi black tunic)."""
    from kit import cast
    qc = Q.load_character("Kimono_Male.blend", "luke", col=col)
    tc = col or (qc.body.users_collection[0] if qc.body.users_collection else None)
    F.build_face(qc, rest="frown", paint_hex="#241812")
    F.set_expression(qc.face, "stern")
    skin = L.toon2("luke_skin", cast.SKIN["ken"])
    tunic = L.toon2("luke_tunic", "#1c1d22")
    Q.assign(qc, skin, materials=["Skin"])
    Q.assign(qc, tunic, materials=["Clothes"])
    Q.assign(qc, L.toon2("luke_belt", "#3a3b42"), materials=["Band"], z_range=(-1.0, 2.0))
    hair = L.toon2("luke_hair", "#d4a955")
    Q.assign(qc, hair, materials=["Band"], z_range=(2.0, 9.0))
    # the pack's headband tails stand straight up (they read as horns): remove them (as cast._fighter does)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(qc.body.data)
    hi_ = list(qc.body.data.materials).index(hair)
    tails = [f for f in bm.faces if f.material_index == hi_ and f.calc_center_median().z > 2.98]
    bmesh.ops.delete(bm, geom=tails, context="FACES")
    bm.to_mesh(qc.body.data); bm.free(); qc.body.data.update()
    cast.shape_arms(qc)
    cast.add_thumbs(qc, skin, tc)
    Q.assign(qc, L.toon2("luke_glove", "#121216"), bones=["Fist.R"])     # the black glove (his robot hand)
    boots = L.toon2("luke_boots", "#141418")
    Q.assign(qc, boots, bones=["Foot.L", "Foot.R"])
    Q.assign(qc, boots, bones=["LowerLeg.L", "LowerLeg.R"], z_range=(-1.0, 0.45))
    part = Q.take_part(qc, "Casual_Male.blend", "Hair", "hair", hair)
    for v in part.data.vertices:                                       # lift the fringe off the brows
        if v.co.y < 0.0:
            t = max(0.0, min(1.0, (3.0 - v.co.z) / 0.8))
            v.co.z += 0.14 * t
    part.data.update()
    Q.smooth(qc)
    Q.outline(qc.body, 0.010)
    Q.outline(part, 0.010)
    return qc


class Lightsaber:
    """A lightsaber in a character's hand: hilt + white core + coloured glow; key(frame, on=0..1) ignites/retracts.

    Built along +Z of an empty `root` that is bone-parented to the fist (grip), so it follows the hand; aim it by
    rotating root. on = blade length fraction (ignite = 0 -> 1 over ~5 frames)."""

    def __init__(self, name: str, colour: str, qc: Q.QChar | None = None, side: str = "R", length: float = 0.95):
        self.length = length
        self.root = C.empty(f"{name}_root")
        hilt_m = L.toon2(f"{name}_hilt", "#9aa0aa")
        grip_m = L.toon2(f"{name}_grip", "#1b1c20")
        self.hilt = C.cylinder(f"{name}_hilt", r=0.022, depth=0.26, loc=(0, 0, 0.0), mat=hilt_m, parent=self.root)
        C.cylinder(f"{name}_griprings", r=0.024, depth=0.1, loc=(0, 0, -0.04), mat=grip_m, parent=self.root)
        C.cylinder(f"{name}_emitter", r=0.028, depth=0.04, loc=(0, 0, 0.13), mat=hilt_m, parent=self.root)
        # blade objects have their origin at the emitter so scaling Z grows them out of the hilt
        self.blade = C.empty(f"{name}_blade", parent=self.root, loc=(0, 0, 0.15))
        C.cylinder(f"{name}_core", r=0.014, depth=1.0, loc=(0, 0, 0.5), mat=FT.emit_mat(f"{name}_core", "#ffffff", 9.0),
                   parent=self.blade)
        C.sphere(f"{name}_tip", r=0.014, loc=(0, 0, 1.0), mat=FT.emit_mat(f"{name}_core", "#ffffff", 9.0), parent=self.blade)
        C.cylinder(f"{name}_glow", r=0.034, depth=1.02, loc=(0, 0, 0.5),
                   mat=FT.emit_mat(f"{name}_glow", colour, strength=6.0, alpha=0.5), parent=self.blade)
        self.blade.scale = (1, 1, length)
        if qc is not None:
            bpy.context.view_layer.update()
            fist = qc.arm.pose.bones[f"Fist.{side}"]
            p = qc.arm.matrix_world @ fist.tail
            self.root.location = p
            from kit import rig
            rig.attach(self.root, qc.arm, f"Fist.{side}")

    def key(self, frame: int, on: float) -> None:
        """Low-level blade length key. Scenes use ignite()/retract() (docs/PROPS.md: a state change needs its action)."""
        self.blade.scale = (1, 1, max(on, 0.001) * self.length)
        self.blade.hide_render = on <= 0.001
        self.blade.keyframe_insert("scale", frame=frame)
        for o in self.blade.children:
            o.hide_render = on <= 0.001
            o.keyframe_insert("hide_render", frame=frame)

    # --- actions (docs/PROPS.md) ---------------------------------------------------------------------
    holder = None
    side = "R"

    def hold(self, qc: Q.QChar, side: str = "R") -> None:
        """Put the hilt in the fist (bone-parented at the grip point)."""
        from kit import rig
        bpy.context.view_layer.update()
        self.root.location = qc.arm.matrix_world @ qc.arm.pose.bones[f"Fist.{side}"].tail
        rig.attach(self.root, qc.arm, f"Fist.{side}")
        self.holder, self.side = qc, side

    def _thumb(self, frame: int) -> None:
        """The thumb press: a 2-frame wrist tick on the holder's fist."""
        if self.holder is None:
            raise RuntimeError("a saber is switched by its holder: call hold() first (docs/PROPS.md)")
        pb = self.holder.arm.pose.bones[f"Fist.{self.side}"]
        pb.rotation_mode = "XYZ"
        for f, a in ((frame - 3, 0.0), (frame - 1, 9.0), (frame + 1, 0.0)):
            pb.rotation_euler = (math.radians(a), 0, 0)
            pb.keyframe_insert("rotation_euler", frame=f)

    def ignite(self, frame: int, frames: int = 5) -> dict:
        """The holder's thumb press, then the blade grows over `frames`. Returns the sound cue (on `frame`)."""
        self._thumb(frame)
        self.key(frame - 1, 0.0)
        for i in range(1, frames + 1):
            self.key(frame + i - 1, i / frames)
        self.events = getattr(self, "events", []) + [("ignite", frame)]
        return {"frame": frame, "sfx": "saber_ignite"}

    def retract(self, frame: int, frames: int = 4) -> dict:
        self._thumb(frame)
        self.key(frame - 1, 1.0)
        for i in range(1, frames + 1):
            self.key(frame + i - 1, 1.0 - i / frames)
        self.events = getattr(self, "events", []) + [("retract", frame)]
        return {"frame": frame, "sfx": "saber_retract"}

    def core_points(self, n: int = 12) -> list:
        """World points along the lit blade core at the current frame ([] when off)."""
        if self.blade.scale.z <= 0.002 or self.blade.hide_render:
            return []
        m = self.blade.matrix_world
        return [m @ Vector((0, 0, (i + 0.5) / n)) for i in range(n)]


# ------------------------------------------------------------------ set: a Death Star-style corridor
def death_star_corridor(col: bpy.types.Collection | None = None, *, width: float = 4.4, height: float = 3.3,
                        depth: float = 14.0) -> dict:
    """Grey panelled corridor along +y (camera at -y looks in): floor grating, wall panels, light strips, a ceiling,
    an octagonal doorway at the end. Never a black void (border check). Returns the lights (see corridor_lights)."""
    col = col or C.collection("corridor")
    wall = L.toon2("ds_wall", "#8a93a3", rim=0.0)
    panel = L.toon2("ds_panel", "#6e7788", rim=0.0)
    floor_m = L.toon2("ds_floor", "#3c424f", rim=0.0)
    ceil = L.toon2("ds_ceiling", "#5b6272", rim=0.0)
    strip = FT.emit_mat("ds_strip", "#e8f4ff", 4.0)
    y0 = -4.0
    C.cube("ds_floor", size=1, loc=(0, y0 + depth / 2, -0.05), scale=(width + 2, depth + 4, 0.1), mat=floor_m, col=col)
    for k in range(int(depth / 0.9)):                                   # floor grating lines
        C.cube(f"ds_grate{k}", size=1, loc=(0, y0 + 0.45 + k * 0.9, 0.003), scale=(width, 0.03, 0.006),
               mat=L.toon2("ds_grate", "#2a2f39", rim=0.0), col=col)
    C.cube("ds_ceiling", size=1, loc=(0, y0 + depth / 2, height + 0.05), scale=(width + 2, depth + 4, 0.1), mat=ceil, col=col)
    for s in (-1, 1):
        x = s * width / 2
        C.cube(f"ds_wall{s}", size=1, loc=(x + s * 0.1, y0 + depth / 2, height / 2), scale=(0.2, depth + 4, height + 0.2),
               mat=wall, col=col)
        for k in range(int(depth / 1.6)):
            y = y0 + 0.8 + k * 1.6
            C.cube(f"ds_panel{s}_{k}", size=1, loc=(x - s * 0.02, y, 1.35), scale=(0.04, 1.3, 1.6), mat=panel, col=col)
            C.cube(f"ds_strip{s}_{k}", size=1, loc=(x - s * 0.04, y, 2.55), scale=(0.03, 1.1, 0.08), mat=strip, col=col)
        C.cube(f"ds_base{s}", size=1, loc=(x - s * 0.06, y0 + depth / 2, 0.12), scale=(0.12, depth + 4, 0.24),
               mat=L.toon2("ds_base", "#4a5160", rim=0.0), col=col)
    for k in range(int(depth / 1.6)):                                     # ceiling light panels
        C.cube(f"ds_ceilight{k}", size=1, loc=(0, y0 + 0.8 + k * 1.6, height - 0.01), scale=(1.2, 0.35, 0.02), mat=strip, col=col)
    end = y0 + depth
    C.cube("ds_endwall", size=1, loc=(0, end, height / 2), scale=(width + 0.4, 0.2, height + 0.2), mat=wall, col=col)
    door = C.cylinder("ds_door", r=1.15, depth=0.05, loc=(0, end - 0.12, 1.25), rot=(90, 0, 22.5),
                      mat=L.toon2("ds_door", "#454c5a", rim=0.0), col=col)
    door.data.update()
    C.torus("ds_doorframe", major=1.2, minor=0.05, loc=(0, end - 0.15, 1.25), rot=(90, 0, 0),
            mat=L.toon2("ds_doorframe", "#9aa3b3", rim=0.0), col=col)
    return corridor_lights(col)


def corridor_lights(col=None) -> dict:
    """Cool overhead key + blue fill + world. key_mood(frame, 'lit'|'dark') switches them (keyed)."""
    key = C.sun("ds_key", energy=2.6, rot=(35, 0, 15), angle_deg=6.0, col=col)
    key.data.color = C.hex_rgb("#eef4ff")
    fill = C.sun("ds_fill", energy=0.9, rot=(70, 0, 200), angle_deg=10.0, col=col)
    fill.data.color = C.hex_rgb("#8fb0ff")
    C.sky(C.hex_rgb("#4d5566"), 1.0)
    return {"key": key, "fill": fill}


MOODS = {  # key, fill, world strength, strip emission, exposure (toon shading keeps a floor: exposure does the dark)
    "lit": (2.6, 0.9, 1.0, 4.0, 0.0),
    "dark": (0.0, 0.5, 0.3, 0.6, -2.4),   # dim blue emergency level: dark but never flat black (border check)
    "lamp": (0.0, 0.35, 0.3, 0.4, -1.4),  # warm point light from the bulb does the rest
}


def key_mood(lights: dict, frame: int, mood: str) -> None:
    k, f, w, s, ev = MOODS[mood]
    vs = bpy.context.scene.view_settings
    vs.exposure = ev; vs.keyframe_insert("exposure", frame=frame)
    lights["key"].data.energy = k; lights["key"].data.keyframe_insert("energy", frame=frame)
    lights["fill"].data.energy = f; lights["fill"].data.keyframe_insert("energy", frame=frame)
    bg = next(n for n in bpy.context.scene.world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Strength"].default_value = w; bg.inputs["Strength"].keyframe_insert("default_value", frame=frame)
    m = bpy.data.materials.get("ds_strip")
    if m:
        em = next(n for n in m.node_tree.nodes if n.type == "EMISSION")
        em.inputs["Strength"].default_value = s; em.inputs["Strength"].keyframe_insert("default_value", frame=frame)
    for d in (lights["key"].data, lights["fill"].data, bpy.context.scene):   # moods switch, they don't fade
        for fc in C.fcurves(d):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


# ------------------------------------------------------------------ prop: a bare bulb on a pull cord
class PullLamp:
    """A bare bulb hanging from the ceiling on a flex, with a pull cord and bead. key_on(frame, on) switches the bulb
    glow + a warm point light; swing(frame, amp_deg, frames) keys a damped swing (the pull)."""

    def __init__(self, loc=(0.0, 0.6, 3.3), drop: float = 1.05, col=None):
        self.pivot = C.empty("lamp_pivot", loc=loc, col=col)
        self.pivot.rotation_mode = "XYZ"
        flex_m = L.toon2("lamp_flex", "#1b1c20", rim=0.0)
        C.cylinder("lamp_flex", r=0.008, depth=drop, loc=(0, 0, -drop / 2), mat=flex_m, parent=self.pivot, col=col)
        C.cylinder("lamp_socket", r=0.035, depth=0.09, loc=(0, 0, -drop - 0.02), mat=L.toon2("lamp_socket", "#2a2b30"),
                   parent=self.pivot, col=col)
        self.glass = FT.emit_mat("lamp_bulb", "#fff1c8", 0.4)
        self.bulb = C.sphere("lamp_bulb", r=0.07, loc=(0, 0, -drop - 0.12), scale=(1, 1, 1.2), mat=self.glass,
                             parent=self.pivot, col=col)
        C.cylinder("lamp_cord", r=0.004, depth=0.55, loc=(0.03, 0, -drop - 0.33), mat=L.toon2("lamp_cord", "#d9d2c0", rim=0.0),
                   parent=self.pivot, col=col)
        self.bead = C.sphere("lamp_bead", r=0.018, loc=(0.03, 0, -drop - 0.62), mat=L.toon2("lamp_bead", "#c9a54a"),
                             parent=self.pivot, col=col)
        ld = bpy.data.lights.new("lamp_light", "POINT")
        ld.energy, ld.color, ld.shadow_soft_size = 0.0, C.hex_rgb("#ffcf8a"), 0.05
        self.light = bpy.data.objects.new("lamp_light", ld)
        C.link(self.light, col)
        self.light.parent = self.pivot
        self.light.location = (0, 0, -drop - 0.12)

    def key_on(self, frame: int, on: bool, energy: float = 900.0) -> None:
        em = next(n for n in self.glass.node_tree.nodes if n.type == "EMISSION")
        em.inputs["Strength"].default_value = 12.0 if on else 0.4
        em.inputs["Strength"].keyframe_insert("default_value", frame=frame)
        self.light.data.energy = energy if on else 0.0
        self.light.data.keyframe_insert("energy", frame=frame)

    def pull(self, qc: Q.QChar, frame: int, side: str = "R") -> dict:
        """The only way to switch the lamp (docs/PROPS.md): the fist is on the bead 3 frames before `frame`, pulls it
        down 8 cm by `frame` (state toggles + click there) and lets go; then the lamp swings. Keys the hand's IK target
        (kit.fight.prepare must have run; key the reach before this). Returns the sound cue."""
        bpy.context.scene.frame_set(frame - 3)
        bpy.context.view_layer.update()
        bead0 = self.bead.matrix_world.translation.copy()
        emp = qc.parts[f"ik.{side}"]
        con = next(c for c in qc.arm.pose.bones[f"LowerArm.{side}"].constraints if c.type == "IK")
        emp.location = bead0; emp.keyframe_insert("location", frame=frame - 3)
        con.influence = 1.0; con.keyframe_insert("influence", frame=frame - 3)
        emp.location = bead0 - Vector((0, 0, 0.08)); emp.keyframe_insert("location", frame=frame)
        bl = self.bead.location.copy()                     # the bead follows the hand down, then springs back
        self.bead.keyframe_insert("location", frame=frame - 3)
        self.bead.location = bl - Vector((0, 0, 0.08)); self.bead.keyframe_insert("location", frame=frame)
        self.bead.location = bl; self.bead.keyframe_insert("location", frame=frame + 3)
        self.state = not getattr(self, "state", False)
        self.key_on(frame - 1, not self.state)
        self.key_on(frame, self.state)
        for fc in C.fcurves(self.light.data):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
        self.swing(frame)
        self.events = getattr(self, "events", []) + [("pull", frame, qc.name, side)]
        return {"frame": frame, "sfx": "pull_cord_click"}

    def swing(self, frame: int, amp_deg: float = 14.0, frames: int = 60, period: int = 22) -> None:
        for i in range(0, frames + 1, 2):
            a = amp_deg * math.exp(-3.0 * i / frames) * math.sin(2 * math.pi * i / period)
            self.pivot.rotation_euler = (math.radians(a), math.radians(a * 0.3), 0)
            self.pivot.keyframe_insert("rotation_euler", frame=frame + i)


# ------------------------------------------------------------------ poses (kit.fight.Pose, native space: front = -y, up = +z,
# ~3.15 units tall; x+ = the character's left; head/torso X: + = tip FORWARD (look down), - = look up/back).
# Named for the script beats of vader-vs-luke-duel.
from kit.fight import Pose  # noqa: E402

_FEET_GUARD = dict(foot_l=(0.36, -0.30, 0.02), foot_r=(-0.30, 0.30, 0.02))
_FEET_STAND = dict(foot_l=(0.26, 0.02, 0.02), foot_r=(-0.26, 0.02, 0.02))
POSES = {
    # blades crossed, both hands on the hilt at chest height (the frame-1 / loop pose)
    "saber_guard": Pose(**_FEET_GUARD, hips=(0, 0, -0.18), hand_l=(0.06, -0.62, 1.62), hand_r=(-0.04, -0.58, 1.55),
                        torso=(6, 0, -8)),
    # leaning into the bind (the clash / "I AM YOUR—")
    "saber_press": Pose(foot_l=(0.40, -0.45, 0.02), foot_r=(-0.34, 0.42, 0.02), hips=(0, -0.08, -0.24),
                        hand_l=(0.06, -0.86, 1.72), hand_r=(-0.04, -0.82, 1.66), torso=(16, 0, -8)),
    # one hand raised: "hold on a second" (before both switch off)
    "hand_up": Pose(**_FEET_STAND, hand_r=(-0.40, -0.45, 2.55), hand_l=(0.36, -0.05, 1.05), torso=(0, 0, 0)),
    # Luke: hand cupped to the ear ("YOU'RE MY WHAT?!")
    "ear_cup": Pose(**_FEET_STAND, hand_l=(0.66, -0.12, 2.45), hand_r=(-0.34, -0.40, 1.45), torso=(8, 10, 0)),
    # Luke in the dark: arms out, feeling for the way
    "lost": Pose(**_FEET_STAND, hand_l=(0.40, -0.88, 1.75), hand_r=(-0.40, -0.88, 1.75), torso=(6, 0, 0), head=(0, 0, 20)),
    # Vader looks around in the dark
    "look_around": Pose(**_FEET_STAND, hand_l=(0.34, -0.10, 1.10), hand_r=(-0.34, -0.10, 1.10), head=(0, 30, 0)),
    # Vader reaches up for the pull cord
    "pull_cord": Pose(**_FEET_STAND, hand_r=(-0.72, -0.25, 3.20), hand_l=(0.34, -0.05, 1.05), torso=(-6, 0, 0),
                      head=(-25, 0, 0)),
    # Vader straightens up, formal, hands at the belt ("Luke. I am your father.")
    "formal": Pose(**_FEET_STAND, hand_l=(0.26, -0.30, 1.28), hand_r=(-0.26, -0.30, 1.28), torso=(-5, 0, 0)),
    # Luke: "NOOOO!" head back, fists down
    "no_scream": Pose(foot_l=(0.30, 0.0, 0.02), foot_r=(-0.30, 0.0, 0.02), hips=(0, 0, -0.10),
                      hand_l=(0.55, -0.05, 1.40), hand_r=(-0.55, -0.05, 1.40), torso=(-20, 0, 0), head=(-40, 0, 0)),
    # Vader leans in over the hum ("...WHAT?") with a hand to the side of his helmet
    "lean_in": Pose(**_FEET_STAND, hand_l=(0.55, -0.25, 2.50), hand_r=(-0.30, -0.60, 1.55), torso=(18, 0, -10)),
}

# which character uses which pose (G3 pose sheets show only these)
POSE_CAST = {
    "vader": ["saber_guard", "saber_press", "hand_up", "look_around", "pull_cord", "formal", "lean_in"],
    "luke": ["saber_guard", "saber_press", "ear_cup", "lost", "no_scream"],
}

# face per pose (kit.face EXPRESSIONS; Vader has no face)
POSE_FACE = {"ear_cup": "suspicious", "lost": "surprised", "no_scream": "surprised", "saber_press": "angry"}
