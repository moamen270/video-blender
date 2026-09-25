"""Fighting-game poses for Quaternius rigs (Ryu/Ken): stance, hadouken thrust, charge, tired.

Poses are written in the character's native armature space (front = -y, up = +z, ~3.15 units tall):
feet through the rig's own leg IK (Foot.* bones), hips through the Body bone, hands through IK
empties (kit.motion.setup_ik). key_pose() keys everything at one frame, so a timeline is a list of
(frame, pose) pairs with Blender's easing in between.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import bpy
from mathutils import Matrix, Vector

from kit import motion as M
from kit import qchar as Q


@dataclass
class Pose:
    foot_l: tuple = (0.26, 0.05, 0.02)
    foot_r: tuple = (-0.26, 0.05, 0.02)
    hips: tuple = (0.0, 0.0, 0.0)          # Body bone offset (native units)
    hand_l: tuple | None = None            # IK target, native; None = animation/rest arm
    hand_r: tuple | None = None
    torso: tuple = (0.0, 0.0, 0.0)         # Torso bone euler degrees (x = lean fwd/back, z = twist)
    head: tuple = (0.0, 0.0, 0.0)          # Head bone euler degrees
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------- the pose library
STANCE = Pose(foot_l=(0.40, -0.38, 0.02), foot_r=(-0.34, 0.34, 0.02), hips=(0.0, 0.0, -0.22),
              hand_l=(0.30, -0.80, 1.72), hand_r=(0.02, -0.62, 1.52), torso=(8, 0, -12))
STANCE_LOW = Pose(foot_l=(0.40, -0.38, 0.02), foot_r=(-0.34, 0.34, 0.02), hips=(0.0, 0.0, -0.30),
                  hand_l=(0.30, -0.78, 1.64), hand_r=(0.02, -0.60, 1.44), torso=(10, 0, -12))
CHARGE = Pose(foot_l=(0.44, -0.46, 0.02), foot_r=(-0.40, 0.40, 0.02), hips=(0.0, 0.10, -0.32),
              hand_l=(-0.30, 0.18, 1.34), hand_r=(-0.42, 0.28, 1.14), torso=(-6, 0, 28), head=(0, 0, -14))
THRUST = Pose(foot_l=(0.44, -0.50, 0.02), foot_r=(-0.40, 0.44, 0.02), hips=(0.0, -0.12, -0.30),
              hand_l=(0.06, -1.30, 1.66), hand_r=(-0.06, -1.30, 1.50), torso=(16, 0, -6))
TIRED = Pose(foot_l=(0.38, -0.20, 0.02), foot_r=(-0.34, 0.24, 0.02), hips=(0.0, 0.0, -0.26),
             hand_l=(0.36, -0.38, 0.95), hand_r=(-0.30, -0.36, 0.95), torso=(24, 0, 0), head=(-6, 0, 0))


def _arm_to_world(qc: Q.QChar, p) -> Vector:
    return qc.arm.matrix_world @ Vector(p)


def _set_bone_arm_loc(qc: Q.QChar, bone: str, arm_loc: Vector) -> None:
    pb = qc.arm.pose.bones[bone]
    m = pb.matrix.copy()
    m.translation = arm_loc
    pb.matrix = m
    bpy.context.view_layer.update()


def prepare(qc: Q.QChar) -> None:
    """IK empties for the hands + quaternion bones; call once after building the character."""
    M.setup_ik(qc)
    for n in ("Body", "Foot.L", "Foot.R", "Torso", "Head"):
        qc.arm.pose.bones[n].rotation_mode = "XYZ"
    qc.arm.animation_data_create()


def key_pose(qc: Q.QChar, frame: int, pose: Pose, *, hand_weight: float = 1.0, bob: float = 0.0) -> None:
    """Key the full pose at `frame` (bob = extra hip height offset, native units)."""
    rest = qc.arm.data.bones
    for bone, p in (("Foot.L", pose.foot_l), ("Foot.R", pose.foot_r)):
        pb = qc.arm.pose.bones[bone]
        pb.location = (0, 0, 0)
        bpy.context.view_layer.update()
        _set_bone_arm_loc(qc, bone, Vector(p))
        pb.keyframe_insert("location", frame=frame)
    body = qc.arm.pose.bones["Body"]
    body.location = (0, 0, 0)
    bpy.context.view_layer.update()
    _set_bone_arm_loc(qc, "Body", rest["Body"].head_local + Vector(pose.hips) + Vector((0, 0, bob)))
    body.keyframe_insert("location", frame=frame)
    for bone, e in (("Torso", pose.torso), ("Head", pose.head)):
        pb = qc.arm.pose.bones[bone]
        pb.rotation_euler = tuple(math.radians(a) for a in e)
        pb.keyframe_insert("rotation_euler", frame=frame)
    for side, h in (("L", pose.hand_l), ("R", pose.hand_r)):
        emp = qc.parts[f"ik.{side}"]
        con = next(c for c in qc.arm.pose.bones[f"LowerArm.{side}"].constraints if c.type == "IK")
        if h is None:
            con.influence = 0.0
        else:
            emp.location = _arm_to_world(qc, h)
            emp.keyframe_insert("location", frame=frame)
            con.influence = hand_weight
        con.keyframe_insert("influence", frame=frame)


def hand_world(qc: Q.QChar, frame: int, side: str) -> Vector:
    """Evaluated world position of a fist at `frame`."""
    bpy.context.scene.frame_set(frame)
    return qc.arm.matrix_world @ qc.arm.pose.bones[f"Fist.{side}"].tail


def between_hands(qc: Q.QChar, frame: int) -> Vector:
    return (hand_world(qc, frame, "L") + hand_world(qc, frame, "R")) / 2


# ---------------------------------------------------------------- materials, fireball, stage
def emit_mat(name: str, hex_: str, strength: float = 2.5, alpha: float = 1.0) -> bpy.types.Material:
    """Unlit emission (optionally translucent, blended)."""
    from studio import core as C
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*C.hex_rgb(hex_), 1.0)
    e.inputs["Strength"].default_value = strength
    if alpha < 1.0:
        t = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        mix.inputs[0].default_value = alpha
        nt.links.new(t.outputs[0], mix.inputs[1])
        nt.links.new(e.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "BLENDED"
        m.use_backface_culling = False
    else:
        nt.links.new(e.outputs[0], out.inputs["Surface"])
    return m


class Fireball:
    """Hadouken ball: bright core + soft shell + two spinning rings under one empty.
    key(frame, loc, size): size = core radius in metres (0 hides it)."""

    def __init__(self, name: str, core_hex: str, glow_hex: str, col=None):
        from studio import core as C
        self.root = C.empty(f"{name}.root", col=col)
        self.root.scale = (0, 0, 0)
        self.core = C.icosphere(f"{name}.core", r=1.0, subdiv=3, mat=emit_mat(f"{name}_core", core_hex, 2.2), col=col, smooth=True)
        self.shell = C.icosphere(f"{name}.shell", r=1.45, subdiv=3, mat=emit_mat(f"{name}_shell", glow_hex, 1.6, 0.35),
                                 col=col, smooth=True)
        self.rings = []
        for i, rot in enumerate(((90, 0, 0), (90, 60, 0))):
            self.rings.append(C.torus(f"{name}.ring{i}", major=1.25, minor=0.07, rot=rot,
                                      mat=emit_mat(f"{name}_ring", glow_hex, 2.4), col=col))
        for o in (self.core, self.shell, *self.rings):
            o.parent = self.root

    def key(self, frame: int, loc, size: float) -> None:
        self.root.location = loc
        self.root.scale = (size, size, size)
        self.root.keyframe_insert("location", frame=frame)
        self.root.keyframe_insert("scale", frame=frame)

    def spin(self, start: int, end: int, turns_per_s: float = 3.0) -> None:
        from studio import core as C
        for i, ring in enumerate(self.rings):
            ring.rotation_mode = "XYZ"
            z0 = ring.rotation_euler.z
            ring.keyframe_insert("rotation_euler", frame=start)
            ring.rotation_euler.z = z0 + (1 if i == 0 else -1) * 2 * math.pi * turns_per_s * (end - start) / 24
            ring.keyframe_insert("rotation_euler", frame=end)
            C.set_interp_all(ring, "LINEAR", "rotation_euler")


def rooftop_sunset(col=None) -> dict:
    """A generic Japanese rooftop at sunset (not a copy of any game stage): planks, low parapet,
    lanterns, gradient sky cylinder with a sun, mountain and pagoda silhouettes. Feet at z = 0."""
    from kit import look as L
    from studio import core as C
    objs = {}
    sky = bpy.data.materials.new("sky_sunset")
    sky.use_nodes = True
    nt = sky.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = -8.0, 12.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (*C.hex_rgb("#ffb35c"), 1)
    els[1].position, els[1].color = 1.0, (*C.hex_rgb("#3b2a66"), 1)
    mid = els.new(0.45)
    mid.color = (*C.hex_rgb("#f06a5a"), 1)
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    sky.use_backface_culling = False
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=26, depth=40, location=(0, 0, 12), end_fill_type="NOTHING")
    cyl = bpy.context.active_object
    cyl.name = "sky"
    cyl.data.materials.append(sky)
    objs["sky"] = cyl
    C.sky(C.hex_rgb("#f5a05a"), 0.35)
    objs["sun"] = C.cylinder("sun_disc", r=2.2, depth=0.05, loc=(10, 22, 3.2), rot=(90, 0, 0),
                             mat=emit_mat("sun_disc", "#ffe2a0", 1.6))
    far = L.toon2("far_sil", "#6a4378", rim=0.0)
    near = L.toon2("near_sil", "#3f2a4e", rim=0.0)
    C.cone("mountain", r1=9, r2=0, depth=7, loc=(-6, 20, -1.0), mat=far)
    C.cone("mountain_cap", r1=2.0, r2=0, depth=1.55, loc=(-6, 19.2, 1.9), mat=L.toon2("snow", "#f0e4ff", rim=0.0))
    C.cone("mountain2", r1=7, r2=0, depth=4.5, loc=(9, 21, -1.2), mat=far)
    for i, (x, h) in enumerate(((-9, 3.2), (4.5, 2.4), (13, 2.8))):
        for k in range(3):
            w = 1.5 - 0.35 * k
            C.cube(f"pagoda{i}_body{k}", size=1, loc=(x, 15, h * 0.35 + k * 1.0), scale=(w * 0.7, w * 0.7, 0.8), mat=near)
            C.cone(f"pagoda{i}_roof{k}", r1=w * 1.1, r2=0.05, depth=0.5, loc=(x, 15, h * 0.35 + k * 1.0 + 0.55),
                   verts=4, mat=near)
    for i in range(14):
        C.cube(f"roofline{i}", size=1, loc=(-14 + i * 2.2, 12, -0.9 + (i % 3) * 0.25),
               scale=(1.9, 1.2, 1.8 + (i % 4) * 0.3), mat=near)
    wood = L.toon2("planks", "#9a6a44", rim=0.0)
    wood_dk = L.toon2("planks_dk", "#6e4a30", rim=0.0)
    C.cube("roof_floor", size=1, loc=(0, 0.5, -0.15), scale=(9.0, 6.0, 0.3), mat=wood)
    for i in range(12):
        C.cube(f"plank_gap{i}", size=1, loc=(0, -2.3 + i * 0.5, 0.004), scale=(9.0, 0.03, 0.01), mat=wood_dk)
    stone = L.toon2("parapet", "#b9a58c", rim=0.0)
    C.cube("parapet_back", size=1, loc=(0, 3.4, 0.25), scale=(9.0, 0.3, 0.5), mat=stone)
    C.cube("parapet_l", size=1, loc=(-4.4, 0.8, 0.25), scale=(0.3, 5.5, 0.5), mat=stone)
    C.cube("parapet_r", size=1, loc=(4.4, 0.8, 0.25), scale=(0.3, 5.5, 0.5), mat=stone)
    post_m = L.toon2("post", "#4a3226", rim=0.0)
    for x in (-3.6, 3.6):
        C.cylinder(f"lantern_post{x}", r=0.05, depth=2.6, loc=(x, 3.1, 1.3), mat=post_m)
    lan = emit_mat("lantern", "#ff5a3a", 1.6)
    objs["lanterns"] = []
    for i in range(7):
        x = -3.0 + i * 1.0
        sag = 0.25 * (1 - ((x / 3.6) ** 2))
        objs["lanterns"].append(C.icosphere(f"lantern{i}", r=0.16, subdiv=2, loc=(x, 3.1, 2.45 - sag), scale=(1, 1, 1.3),
                                            mat=lan, smooth=True))
    return objs


def sunset_lights(target=(0, 0, 1.0)) -> dict:
    from studio import core as C
    key = C.sun("key_sunset", energy=3.4, angle_deg=4.0)
    key.location = (6, 12, 5)
    key.data.color = C.hex_rgb("#ffc890")
    C.point_at(key, target)
    fill = C.sun("fill_cool", energy=1.4, angle_deg=8.0)
    fill.location = (-6, -8, 4)
    fill.data.color = C.hex_rgb("#9aa8ff")
    C.point_at(fill, target)
    C._set_enum(bpy.context.scene.view_settings, "view_transform", ["Standard"])
    return {"key": key, "fill": fill}
