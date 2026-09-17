"""Reusable props and set dressing. Each function returns the top-level object (or a dict).

Props attached to a character are parented to a hand/head object, so they follow the rig.
"""
from __future__ import annotations

import math
import random

import bpy

from . import core as C


# --------------------------------------------------------------------------- equipment


def bow(name: str, *, size=0.6, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), col=None) -> dict:
    """Bow parented to a hand. When the arm is raised forward (shoulder X=-90) the hand's local
    -Z points forward and local -Y points up, so the limb spans local Y and bulges along -Z.
    The string's middle point is animatable: key `string.data.splines[0].points[1].co`."""
    wood = C.material(f"{name}.wood", C.hex_rgb("#8b5a2b"), rough=0.7)
    twine = C.material(f"{name}.string", C.hex_rgb("#f1e9d2"), rough=0.9)
    grip = C.empty(f"{name}", parent=parent, loc=loc, rot=rot, col=col)
    limb = C.curve_arc(f"{name}.limb", [(0, -size, 0), (0, 0, -size * 0.35), (0, size, 0)],
                       bevel=size * 0.05, parent=grip, mat=wood, col=col)
    string = C.curve_arc(f"{name}.string", [(0, -size, 0), (0, 0, 0), (0, size, 0)],
                         bevel=size * 0.012, parent=grip, mat=twine, col=col, bezier=False)
    return {"grip": grip, "limb": limb, "string": string, "size": size}


def draw_bow(b: dict, frame: int, pull: float) -> None:
    """pull 0 = slack, 1 = fully drawn (string middle moves back toward the archer, local +Z)."""
    pt = b["string"].data.splines[0].points[1]
    pt.co = (0, 0, b["size"] * 0.75 * pull, 1.0)
    pt.keyframe_insert("co", frame=frame)


def arrow(name: str, *, length=0.8, r=0.012, col=None, tip_color="#c9ced6", fletch_color="#e8473f") -> bpy.types.Object:
    """Arrow whose local +Y is the flight direction, origin at the tip."""
    shaft_m = C.material(f"{name}.shaft", C.hex_rgb("#d9b277"), rough=0.6)
    tip_m = C.material(f"{name}.tip", C.hex_rgb(tip_color), rough=0.3, metal=0.6)
    fl_m = C.material(f"{name}.fletch", C.hex_rgb(fletch_color), rough=0.8)
    root = C.empty(name, col=col, size=0.1)
    C.cylinder(f"{name}.shaft", r=r, depth=length, parent=root, loc=(0, -length / 2, 0), rot=(90, 0, 0),
               mat=shaft_m, col=col, verts=8)
    C.cone(f"{name}.tip", r1=r * 3.2, r2=0.0, depth=length * 0.12, parent=root, loc=(0, -length * 0.06, 0),
           rot=(-90, 0, 0), mat=tip_m, col=col, verts=8)
    for i, ang in enumerate((0, 120, 240)):
        C.cube(f"{name}.fletch{i}", size=1.0, parent=root, loc=(0, -length * 0.9, 0), rot=(0, ang, 0),
               scale=(r * 0.5, length * 0.12, r * 6), mat=fl_m, col=col)
        # move each fletch outward from the shaft along its own rotated Z
        f = bpy.data.objects[f"{name}.fletch{i}"]
        a = math.radians(ang)
        f.location = (math.sin(a) * r * 5, -length * 0.9, math.cos(a) * r * 5)
    return root


def shield(name: str, *, r=0.32, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), col=None,
           color="#3b6fd6", rim="#e6c25a") -> bpy.types.Object:
    face = C.material(f"{name}.face", C.hex_rgb(color), rough=0.4, metal=0.2)
    rim_m = C.material(f"{name}.rim", C.hex_rgb(rim), rough=0.3, metal=0.7)
    o = C.cylinder(f"{name}", r=r, depth=0.05, parent=parent, loc=loc, rot=rot, mat=face, col=col, verts=32, bevel=0.02)
    C.torus(f"{name}.rim", major=r, minor=0.03, parent=o, mat=rim_m, col=col)
    C.sphere(f"{name}.boss", r=r * 0.22, parent=o, loc=(0, 0, 0.03), mat=rim_m, col=col, segments=16, rings=10)
    return o


def helmet(name: str, *, r=0.36, parent=None, loc=(0, 0, 0), col=None, color="#9aa4b2", plume="#e8473f") -> bpy.types.Object:
    steel = C.material(f"{name}.steel", C.hex_rgb(color), rough=0.35, metal=0.8)
    plume_m = C.material(f"{name}.plume", C.hex_rgb(plume), rough=0.9)
    o = C.sphere(f"{name}", r=r, parent=parent, loc=loc, scale=(1, 1, 0.75), mat=steel, col=col)
    C.cylinder(f"{name}.brim", r=r * 1.08, depth=0.05, parent=o, loc=(0, 0, -0.06), mat=steel, col=col, verts=32)
    C.cube(f"{name}.nose", size=1.0, parent=o, loc=(0, -r * 0.95, -0.35), scale=(0.06, 0.05, 0.4), mat=steel, col=col)
    C.sphere(f"{name}.plume", r=r * 0.35, parent=o, loc=(0, 0.1, r * 1.05), scale=(0.5, 1.6, 1.0), mat=plume_m, col=col)
    return o


def wings(name: str, *, parent=None, loc=(0, 0, 0), size=0.35, col=None, color="#fff6e8") -> dict:
    m = C.material(f"{name}.feather", C.hex_rgb(color), rough=0.9, emit=0.1)
    pair = {}
    for side, sx in (("l", -1), ("r", 1)):
        piv = C.empty(f"{name}.{side}", parent=parent, loc=loc, col=col)
        C.sphere(f"{name}.{side}.feather", r=size, parent=piv, loc=(sx * size * 0.9, 0, size * 0.3),
                 scale=(1.0, 0.18, 0.55), rot=(0, sx * -20, 0), mat=m, col=col, segments=16, rings=10)
        pair[side] = piv
    return pair


def flap_wings(w: dict, f0: int, f1: int, *, period=8, amp=35) -> None:
    f = f0
    while f <= f1:
        C.key(w["l"], f, rot=(0, -amp, 0))
        C.key(w["r"], f, rot=(0, amp, 0))
        if f + period // 2 <= f1:
            C.key(w["l"], f + period // 2, rot=(0, amp * 0.6, 0))
            C.key(w["r"], f + period // 2, rot=(0, -amp * 0.6, 0))
        f += period


def halo(name: str, *, parent=None, loc=(0, 0, 0), r=0.22, col=None) -> bpy.types.Object:
    m = C.material(f"{name}.gold", C.hex_rgb("#ffd54a"), rough=0.2, metal=0.5, emit=2.5)
    return C.torus(f"{name}", major=r, minor=r * 0.12, parent=parent, loc=loc, rot=(8, 0, 0), mat=m, col=col)


def quiver(name: str, *, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), col=None) -> bpy.types.Object:
    m = C.material(f"{name}.leather", C.hex_rgb("#6b3f1f"), rough=0.8)
    o = C.cylinder(f"{name}", r=0.08, depth=0.45, parent=parent, loc=loc, rot=rot, mat=m, col=col, verts=12)
    for i in range(3):
        a = i * 2.1
        C.cylinder(f"{name}.a{i}", r=0.01, depth=0.5, parent=o, loc=(math.cos(a) * 0.035, math.sin(a) * 0.035, 0.35),
                   mat=C.material("arrow.shaft.shared", C.hex_rgb("#d9b277")), col=col, verts=6)
    return o


# --------------------------------------------------------------------------- fx meshes


def heart(name: str, *, size=0.25, parent=None, loc=(0, 0, 0), col=None, color="#ff4f7d", emit=1.2) -> bpy.types.Object:
    """Heart facing -Y (camera side), built from two spheres and a rotated cube on an empty."""
    m = C.material("fx.heart", C.hex_rgb(color), rough=0.35, emit=emit)
    root = C.empty(name, parent=parent, loc=loc, col=col, size=0.05)
    C.sphere(f"{name}.l", r=size * 0.32, parent=root, loc=(-size * 0.27, 0, size * 0.28), mat=m, col=col, segments=16, rings=10)
    C.sphere(f"{name}.r", r=size * 0.32, parent=root, loc=(size * 0.27, 0, size * 0.28), mat=m, col=col, segments=16, rings=10)
    C.cube(f"{name}.v", size=1.0, parent=root, loc=(0, 0, size * 0.02), rot=(0, 45, 0),
           scale=(size * 0.5, size * 0.28, size * 0.5), mat=m, col=col)
    return root


def star(name: str, *, size=0.12, parent=None, loc=(0, 0, 0), col=None) -> bpy.types.Object:
    m = C.material("fx.star", C.hex_rgb("#ffe26a"), rough=0.3, emit=2.0)
    return C.icosphere(f"{name}", r=size, subdiv=1, parent=parent, loc=loc, mat=m, col=col)


# --------------------------------------------------------------------------- set dressing


def ground(*, size=80, color="#7cc46b", col=None) -> bpy.types.Object:
    m = C.material("set.grass", C.hex_rgb(color), rough=0.95)
    return C.plane("Ground", size=size, mat=m, col=col)


def hill(name: str, *, loc, r=6.0, flat=0.35, color="#6db35e", col=None) -> bpy.types.Object:
    m = C.material("set.hill", C.hex_rgb(color), rough=0.95)
    return C.sphere(name, r=r, loc=loc, scale=(1.0, 0.8, flat), mat=m, col=col, segments=32, rings=16)


def tree(name: str, *, loc, h=2.2, canopy="#3f9d4f", trunk="#7a4b24", col=None, seed=0) -> bpy.types.Object:
    rnd = random.Random(seed)
    tm = C.material("set.trunk", C.hex_rgb(trunk), rough=0.9)
    cm = C.material(f"set.canopy.{canopy}", C.hex_rgb(canopy), rough=0.9)
    t = C.cylinder(name, r=h * 0.06, depth=h * 0.5, loc=(loc[0], loc[1], h * 0.25), mat=tm, col=col, verts=10)
    for i in range(3):
        C.icosphere(f"{name}.c{i}", r=h * (0.32 - i * 0.05), subdiv=1, parent=t,
                    loc=(rnd.uniform(-0.15, 0.15) * h, rnd.uniform(-0.15, 0.15) * h, h * (0.35 + i * 0.22)),
                    mat=cm, col=col, smooth=False)
    return t


def rock(name: str, *, loc, r=0.35, col=None, seed=0) -> bpy.types.Object:
    rnd = random.Random(seed)
    m = C.material("set.rock", C.hex_rgb("#9c9a94"), rough=0.9)
    return C.icosphere(name, r=r, subdiv=1, loc=(loc[0], loc[1], r * 0.45),
                       scale=(rnd.uniform(0.8, 1.3), rnd.uniform(0.8, 1.3), rnd.uniform(0.5, 0.8)),
                       rot=(0, 0, rnd.uniform(0, 360)), mat=m, col=col)


def cloud(name: str, *, loc, size=1.0, col=None, seed=0) -> bpy.types.Object:
    rnd = random.Random(seed)
    m = C.material("set.cloud", C.hex_rgb("#ffffff"), rough=1.0, emit=0.6)
    root = C.empty(name, loc=loc, col=col)
    for i in range(4):
        C.sphere(f"{name}.{i}", r=size * rnd.uniform(0.45, 0.8), parent=root,
                 loc=(rnd.uniform(-1, 1) * size, 0, rnd.uniform(-0.2, 0.3) * size), mat=m, col=col, segments=16, rings=10)
    return root


def sign(name: str, body: str, *, loc, rot=(90, 0, 0), size=0.5, color="#ffffff", emit=1.5, col=None) -> bpy.types.Object:
    m = C.material(f"{name}.text", C.hex_rgb(color), rough=0.4, emit=emit)
    return C.text(name, body, size=size, extrude=size * 0.08, loc=loc, rot=rot, mat=m, col=col)
