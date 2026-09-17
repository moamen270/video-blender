"""Stylised low-poly characters built from primitives with pivot "joints".

Local conventions (same for every character):
  * the character faces its local -Y (Blender's Front view); rotate `root` around Z to turn it
  * every joint is an Empty; limbs hang along the joint's -Z
  * rotating a shoulder/hip around X swings the limb forward (-X deg) / back (+X deg)

A `Rig` is just a dict of named objects so animation code can say `rig["shoulder_r"]`.
"""
from __future__ import annotations

import math

import bpy

from . import core as C

Rig = dict


DEFAULT_COLORS = {
    "body": "#e8473f", "limb": "#f2a65a", "skin": "#ffd9b3", "eye": "#ffffff",
    "pupil": "#1b1b1b", "mouth": "#7a2a2a", "accent": "#f7d94c",
}


def build_character(name: str, *, loc=(0, 0, 0), face_deg: float = 0.0, leg=0.6, body_h=0.8,
                    body_r=0.35, head_r=0.32, arm=0.5, arm_r=0.08, leg_r=0.1,
                    colors: dict | None = None, col=None) -> Rig:
    cl = {**DEFAULT_COLORS, **(colors or {})}
    m = {k: C.material(f"{name}.{k}", C.hex_rgb(v)) for k, v in cl.items()}
    m["eye"] = C.material(f"{name}.eye", C.hex_rgb(cl["eye"]), rough=0.3, emit=0.15)
    rig: Rig = {"name": name, "dims": dict(leg=leg, body_h=body_h, body_r=body_r, head_r=head_r, arm=arm)}

    root = rig["root"] = C.empty(f"{name}", loc=loc, rot=(0, 0, face_deg), col=col, size=0.4)
    hips = rig["hips"] = C.empty(f"{name}.hips", parent=root, loc=(0, 0, leg), col=col)
    rig["body"] = C.cylinder(f"{name}.body", r=body_r, depth=body_h, parent=hips, loc=(0, 0, body_h / 2),
                             mat=m["body"], col=col, bevel=body_r * 0.45)

    neck = rig["neck"] = C.empty(f"{name}.neck", parent=hips, loc=(0, 0, body_h), col=col)
    head = rig["head"] = C.sphere(f"{name}.head", r=head_r, parent=neck, loc=(0, 0, head_r * 0.85),
                                  mat=m["skin"], col=col)
    eye_r = head_r * 0.24
    for side, sx in (("l", -1), ("r", 1)):
        eye = rig[f"eye_{side}"] = C.sphere(f"{name}.eye_{side}", r=eye_r, parent=head,
                                            loc=(sx * head_r * 0.4, -head_r * 0.8, head_r * 0.12),
                                            mat=m["eye"], col=col, segments=16, rings=10)
        rig[f"pupil_{side}"] = C.sphere(f"{name}.pupil_{side}", r=eye_r * 0.5, parent=eye,
                                        loc=(0, -eye_r * 0.65, 0), mat=m["pupil"], col=col, segments=12, rings=8)
    rig["mouth"] = C.sphere(f"{name}.mouth", r=head_r * 0.18, parent=head,
                            loc=(0, -head_r * 0.93, -head_r * 0.38), scale=(1.2, 0.35, 0.45),
                            mat=m["mouth"], col=col, segments=16, rings=10)

    for side, sx in (("l", -1), ("r", 1)):
        sh = rig[f"shoulder_{side}"] = C.empty(f"{name}.shoulder_{side}", parent=hips,
                                               loc=(sx * (body_r + arm_r * 0.6), 0, body_h * 0.82), col=col)
        C.cylinder(f"{name}.upperarm_{side}", r=arm_r, depth=arm * 0.5, parent=sh, loc=(0, 0, -arm * 0.25),
                   mat=m["limb"], col=col, verts=12, bevel=arm_r * 0.5)
        el = rig[f"elbow_{side}"] = C.empty(f"{name}.elbow_{side}", parent=sh, loc=(0, 0, -arm * 0.5), col=col)
        C.cylinder(f"{name}.forearm_{side}", r=arm_r * 0.9, depth=arm * 0.5, parent=el, loc=(0, 0, -arm * 0.25),
                   mat=m["limb"], col=col, verts=12, bevel=arm_r * 0.5)
        rig[f"hand_{side}"] = C.sphere(f"{name}.hand_{side}", r=arm_r * 1.5, parent=el, loc=(0, 0, -arm * 0.5),
                                       mat=m["skin"], col=col, segments=12, rings=8)

        hp = rig[f"hip_{side}"] = C.empty(f"{name}.hip_{side}", parent=hips, loc=(sx * body_r * 0.5, 0, 0), col=col)
        C.cylinder(f"{name}.thigh_{side}", r=leg_r, depth=leg * 0.5, parent=hp, loc=(0, 0, -leg * 0.25),
                   mat=m["limb"], col=col, verts=12, bevel=leg_r * 0.5)
        kn = rig[f"knee_{side}"] = C.empty(f"{name}.knee_{side}", parent=hp, loc=(0, 0, -leg * 0.5), col=col)
        C.cylinder(f"{name}.shin_{side}", r=leg_r * 0.9, depth=leg * 0.5, parent=kn, loc=(0, 0, -leg * 0.25),
                   mat=m["limb"], col=col, verts=12, bevel=leg_r * 0.5)
        rig[f"foot_{side}"] = C.cube(f"{name}.foot_{side}", size=1.0, parent=kn,
                                     loc=(0, -leg_r * 0.9, -leg * 0.5 + leg_r * 0.55),
                                     scale=(leg_r * 2.2, leg_r * 3.4, leg_r * 1.1), mat=m["pupil"], col=col,
                                     bevel=leg_r * 0.3)
    rig["mats"] = m
    return rig


# --------------------------------------------------------------------------- poses & cycles


def rest_pose(rig: Rig, frame: int) -> None:
    """Key every joint to neutral so later motion has a defined start."""
    for j in ("shoulder_l", "shoulder_r", "elbow_l", "elbow_r", "hip_l", "hip_r", "knee_l", "knee_r", "neck"):
        C.key(rig[j], frame, rot=(0, 0, 0))
    C.key(rig["hips"], frame, loc=(0, 0, rig["dims"]["leg"]), rot=(0, 0, 0), scale=(1, 1, 1))
    C.key(rig["head"], frame, rot=(0, 0, 0))


def arms(rig: Rig, frame: int, *, l=(0, 0, 0), r=(0, 0, 0), el_l=(0, 0, 0), el_r=(0, 0, 0)) -> None:
    C.key(rig["shoulder_l"], frame, rot=l)
    C.key(rig["shoulder_r"], frame, rot=r)
    C.key(rig["elbow_l"], frame, rot=el_l)
    C.key(rig["elbow_r"], frame, rot=el_r)


def walk(rig: Rig, f0: int, f1: int, start, end, *, stride=10, amp=32, bob=0.05, arm_amp=25,
         run=False, swing_arms=True) -> None:
    """Move `root` from `start` to `end` (world XY) with a leg/arm cycle in between."""
    leg = rig["dims"]["leg"]
    root = rig["root"]
    C.key(root, f0, loc=(start[0], start[1], 0), interp="LINEAR")
    C.key(root, f1, loc=(end[0], end[1], 0), interp="LINEAR")
    if run:
        amp, arm_amp, bob = amp * 1.4, arm_amp * 1.6, bob * 1.8
    f, n = f0, 0
    while f <= f1:
        s = 1 if n % 2 == 0 else -1
        C.key(rig["hip_l"], f, rot=(-s * amp, 0, 0))
        C.key(rig["hip_r"], f, rot=(s * amp, 0, 0))
        C.key(rig["knee_l"], f, rot=(0 if s < 0 else 0, 0, 0))
        C.key(rig["knee_r"], f, rot=(0 if s > 0 else 0, 0, 0))
        if swing_arms:
            C.key(rig["shoulder_l"], f, rot=(s * arm_amp, 0, 0))
            C.key(rig["shoulder_r"], f, rot=(-s * arm_amp, 0, 0))
        C.key(rig["hips"], f, loc=(0, 0, leg))
        half = f + stride // 2
        if half <= f1:
            # passing position: knees bend, body bobs up
            C.key(rig["knee_l"], half, rot=(45 if s > 0 else 0, 0, 0))
            C.key(rig["knee_r"], half, rot=(45 if s < 0 else 0, 0, 0))
            C.key(rig["hips"], half, loc=(0, 0, leg + bob))
        f += stride
        n += 1
    # settle
    C.key(rig["hip_l"], f1 + 6, rot=(0, 0, 0))
    C.key(rig["hip_r"], f1 + 6, rot=(0, 0, 0))
    C.key(rig["knee_l"], f1 + 6, rot=(0, 0, 0))
    C.key(rig["knee_r"], f1 + 6, rot=(0, 0, 0))
    C.key(rig["hips"], f1 + 6, loc=(0, 0, leg))


def face(rig: Rig, frame: int, deg: float) -> None:
    C.key(rig["root"], frame, rot=(0, 0, deg))


def idle_breath(rig: Rig, f0: int, f1: int, *, period=36, amount=0.02) -> None:
    leg = rig["dims"]["leg"]
    f = f0
    while f <= f1:
        C.key(rig["hips"], f, loc=(0, 0, leg))
        if f + period // 2 <= f1:
            C.key(rig["hips"], f + period // 2, loc=(0, 0, leg + amount))
        f += period


def bounce(rig: Rig, f0: int, f1: int, *, period=8, height=0.18, lean=0.0) -> None:
    """Hopping laugh / stomp: hips go up-down with a little squash on landing."""
    leg = rig["dims"]["leg"]
    f = f0
    while f <= f1:
        C.key(rig["hips"], f, loc=(0, 0, leg), scale=(1.08, 1.08, 0.9), rot=(lean, 0, 0))
        top = f + period // 2
        if top <= f1:
            C.key(rig["hips"], top, loc=(0, 0, leg + height), scale=(0.95, 0.95, 1.08), rot=(lean, 0, 0))
        f += period
    C.key(rig["hips"], f1 + 4, loc=(0, 0, leg), scale=(1, 1, 1), rot=(0, 0, 0))


def squash(rig: Rig, frame: int, *, depth=0.25, recover=10) -> None:
    """Impact squash-and-stretch on the hips, then spring back."""
    leg = rig["dims"]["leg"]
    C.key(rig["hips"], frame - 1, loc=(0, 0, leg), scale=(1, 1, 1))
    C.key(rig["hips"], frame + 2, loc=(0, 0, leg * (1 - depth)), scale=(1 + depth, 1 + depth, 1 - depth))
    C.key(rig["hips"], frame + recover // 2, loc=(0, 0, leg * 1.05), scale=(0.95, 0.95, 1.1))
    C.key(rig["hips"], frame + recover, loc=(0, 0, leg), scale=(1, 1, 1))


def eyes(rig: Rig, frame: int, *, scale=1.0, look=(0, 0)) -> None:
    """Eye size (surprise) and pupil offset (look direction, in eye radii)."""
    hr = rig["dims"]["head_r"]
    er = hr * 0.24
    for s in ("l", "r"):
        C.key(rig[f"eye_{s}"], frame, scale=(scale, scale, scale))
        C.key(rig[f"pupil_{s}"], frame, loc=(look[0] * er * 0.5, -er * 0.65, look[1] * er * 0.5))


def mouth(rig: Rig, frame: int, *, shape="flat") -> None:
    shapes = {"flat": (1.2, 0.35, 0.45), "smile": (1.4, 0.35, 0.6), "o": (0.8, 0.5, 1.1), "big": (1.6, 0.5, 1.4),
              "small": (0.6, 0.3, 0.3)}
    C.key(rig["mouth"], frame, scale=shapes[shape])


def head_turn(rig: Rig, frame: int, *, yaw=0.0, pitch=0.0, roll=0.0) -> None:
    C.key(rig["neck"], frame, rot=(pitch, roll, yaw))
