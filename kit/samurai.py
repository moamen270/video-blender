"""Samurai character builders: Ronin, Warlord, katana, and scabbard (Task T4)."""
from __future__ import annotations

import math
from typing import Any

import bmesh
import bpy
from mathutils import Vector

from kit import pose, rig, toon
from studio import core as C


def part(
    name: str,
    prim: Any,
    bone: str,
    mat: bpy.types.Material | None = None,
    outline: float = 0.012,
    arm: bpy.types.Object | None = None,
    col: bpy.types.Collection | None = None,
    **kw,
) -> bpy.types.Object:
    """Create a primitive with studio.core, attach it to an armature bone, and add outline."""
    if arm is None:
        arm = kw.pop("arm", None)
    if col is None:
        col = kw.pop("col", None)

    char = ""
    if arm is not None:
        char = arm.name
    elif "ronin" in name:
        char = "ronin"
    elif "warlord" in name:
        char = "warlord"

    if char and not name.startswith(f"{char}_"):
        full_name = f"{char}_{name}"
    else:
        full_name = name

    if col is None and char:
        col = C.collection(char)
    if arm is None and char:
        arm = bpy.data.objects.get(char)

    if callable(prim):
        func = prim
    elif isinstance(prim, str):
        func = getattr(C, prim)
    else:
        raise ValueError(f"Unknown primitive specification: {prim}")

    obj = func(full_name, mat=mat, col=col, **kw)

    if arm is not None:
        rig.attach(obj, arm, bone)
    if outline > 0.0:
        toon.add_outline(obj, outline)

    return obj


def build_katana(
    arm: bpy.types.Object,
    char: str,
    blade_hex: str,
    tsuba_hex: str,
    handle_hex: str,
    col: bpy.types.Collection | None = None,
) -> None:
    """Build katana parts along the sword bone: handle, tsuba, blade, and tip."""
    if col is None:
        col = C.collection(char)

    mat_handle = toon.toon(f"{char}_handle", handle_hex)
    mat_tsuba = toon.toon(f"{char}_tsuba", tsuba_hex)
    mat_blade = toon.toon(f"{char}_blade", blade_hex)

    part(
        f"{char}_katana_handle",
        C.cylinder,
        "sword",
        mat_handle,
        outline=0.012,
        arm=arm,
        col=col,
        r=0.018,
        depth=0.26,
        loc=(0.0, 0.13, 0.0),
        rot=(90.0, 0.0, 0.0),
    )
    part(
        f"{char}_katana_tsuba",
        C.cylinder,
        "sword",
        mat_tsuba,
        outline=0.012,
        arm=arm,
        col=col,
        r=0.045,
        depth=0.012,
        loc=(0.0, 0.265, 0.0),
        rot=(90.0, 0.0, 0.0),
    )
    part(
        f"{char}_katana_blade",
        C.cube,
        "sword",
        mat_blade,
        outline=0.004,
        arm=arm,
        col=col,
        size=1.0,
        scale=(0.008, 0.72, 0.034),
        loc=(0.0, 0.63, 0.0),
    )
    part(
        f"{char}_katana_tip",
        C.cone,
        "sword",
        mat_blade,
        outline=0.004,
        arm=arm,
        col=col,
        r1=0.017,
        r2=0.0,
        depth=0.07,
        loc=(0.0, 1.02, 0.0),
        rot=(-90.0, 0.0, 0.0),
        scale=(0.25, 1.0, 1.0),
    )


def _add_limb(
    arm: bpy.types.Object,
    char: str,
    bone_name: str,
    r_head: float,
    r_tail: float,
    mat: bpy.types.Material | None,
    col: bpy.types.Collection,
) -> bpy.types.Object:
    """Build limb cone and joint sphere with pose.limb, link to col, and add outline."""
    name = f"{char}_{bone_name}"
    c = pose.limb(name, arm, bone_name, r_head, r_tail, mat)
    C.link(c, col)
    toon.add_outline(c, 0.012)
    s = bpy.data.objects.get(f"{name}_joint")
    if s is not None:
        C.link(s, col)
        toon.add_outline(s, 0.012)
    return c


def _build_saya(
    arm: bpy.types.Object,
    char: str,
    saya_hex: str,
    col: bpy.types.Collection,
) -> bpy.types.Object:
    """Build the scabbard (saya) attached to pelvis."""
    start = Vector((-0.16, 0.25, 1.00))
    end = Vector((-0.16, -0.45, 0.85))
    mid = (start + end) * 0.5
    delta = end - start
    rot_euler = delta.to_track_quat("Z", "Y").to_euler()
    rot_deg = tuple(math.degrees(a) for a in rot_euler)
    mat_saya = toon.toon(f"{char}_saya", saya_hex)

    return part(
        f"{char}_saya",
        C.cylinder,
        "pelvis",
        mat_saya,
        outline=0.012,
        arm=arm,
        col=col,
        r=0.025,
        depth=0.80,
        loc=tuple(mid),
        rot=rot_deg,
    )


def build_ronin() -> bpy.types.Object:
    """Build the Ronin hero character."""
    col = C.collection("ronin")
    arm = rig.build_armature("ronin")
    C.link(arm, col)
    rig.calibrate_poles(arm)

    # Materials
    mat_skin = toon.toon("ronin_skin", "#f1c9a0")
    mat_hair = toon.toon("ronin_hair", "#1a1a1a")
    mat_white = toon.toon("ronin_headband", "#f4f4f4")
    mat_eye = toon.toon("ronin_eye", "#101010")
    mat_kimono = toon.toon("ronin_kimono", "#dfe6f2")
    mat_collar = toon.toon("ronin_collar", "#3a4a6b")
    mat_obi = toon.toon("ronin_obi", "#2b3550")
    mat_hakama = toon.toon("ronin_hakama", "#2e2f38")
    mat_foot = toon.toon("ronin_foot", "#1b1b1b")

    # Head & hair
    part("ronin_head", C.sphere, "head", mat_skin, outline=0.012, arm=arm, col=col, r=0.14, loc=(0.0, 0.0, 1.70))
    part("ronin_hair_cap", C.sphere, "head", mat_hair, outline=0.012, arm=arm, col=col, r=0.158, loc=(0.0, -0.02, 1.74), scale=(1.0, 1.0, 0.62))
    part("ronin_topknot", C.cylinder, "head", mat_hair, outline=0.012, arm=arm, col=col, r=0.035, depth=0.10, loc=(0.0, -0.07, 1.86), rot=(60.0, 0.0, 0.0))
    part("ronin_headband", C.torus, "head", mat_white, outline=0.012, arm=arm, col=col, major=0.15, minor=0.016, loc=(0.0, 0.0, 1.80))

    # Eyes & brows (outline 0.004)
    for side, sign in (("R", 1.0), ("L", -1.0)):
        part(
            f"ronin_eye.{side}",
            C.sphere,
            "head",
            mat_eye,
            outline=0.004,
            arm=arm,
            col=col,
            r=0.022,
            loc=(sign * 0.05, 0.128, 1.71),
            scale=(1.0, 0.5, 1.4),
        )
        part(
            f"ronin_brow.{side}",
            C.cube,
            "head",
            mat_hair,
            outline=0.004,
            arm=arm,
            col=col,
            size=1.0,
            scale=(0.055, 0.012, 0.012),
            loc=(sign * 0.05, 0.132, 1.755),
            rot=(0.0, -sign * 12.0, 0.0),
        )

    # Neck
    part("ronin_neck", C.cylinder, "neck", mat_skin, outline=0.012, arm=arm, col=col, r=0.05, depth=0.10, loc=(0.0, 0.0, 1.54))

    # Torso
    part("ronin_chest", C.cone, "chest", mat_kimono, outline=0.012, arm=arm, col=col, r1=0.20, r2=0.17, depth=0.24, loc=(0.0, 0.0, 1.38), scale=(1.0, 0.65, 1.0))
    part("ronin_belly", C.cone, "spine", mat_kimono, outline=0.012, arm=arm, col=col, r1=0.17, r2=0.19, depth=0.24, loc=(0.0, 0.0, 1.16), scale=(1.0, 0.65, 1.0))

    # Collar (outline 0.004)
    for side, sign in (("R", 1.0), ("L", -1.0)):
        part(
            f"ronin_collar.{side}",
            C.cube,
            "chest",
            mat_collar,
            outline=0.004,
            arm=arm,
            col=col,
            size=1.0,
            scale=(0.05, 0.02, 0.20),
            loc=(sign * 0.05, 0.125, 1.40),
            rot=(0.0, sign * 25.0, 0.0),
        )

    # Obi
    part("ronin_obi", C.cylinder, "pelvis", mat_obi, outline=0.012, arm=arm, col=col, r=0.19, depth=0.09, loc=(0.0, 0.0, 1.02), scale=(1.0, 0.68, 1.0))

    # Limbs
    for side in ("R", "L"):
        _add_limb(arm, "ronin", f"upperarm.{side}", 0.075, 0.10, mat_kimono, col)
        _add_limb(arm, "ronin", f"forearm.{side}", 0.045, 0.04, mat_skin, col)
        wrist_pos = arm.data.bones[f"forearm.{side}"].tail_local
        part(
            f"ronin_hand.{side}",
            C.sphere,
            f"forearm.{side}",
            mat_skin,
            outline=0.012,
            arm=arm,
            col=col,
            r=0.05,
            loc=tuple(wrist_pos),
        )
        _add_limb(arm, "ronin", f"thigh.{side}", 0.11, 0.15, mat_hakama, col)
        _add_limb(arm, "ronin", f"shin.{side}", 0.15, 0.17, mat_hakama, col)

    # Feet
    for side, sign in (("R", 1.0), ("L", -1.0)):
        part(
            f"ronin_foot.{side}",
            C.cube,
            f"foot.{side}",
            mat_foot,
            outline=0.012,
            arm=arm,
            col=col,
            size=1.0,
            scale=(0.09, 0.22, 0.06),
            loc=(sign * 0.11, 0.07, 0.04),
        )

    # Katana
    build_katana(arm, "ronin", "#d9dde6", "#c9a227", "#20304f", col=col)

    # Saya
    _build_saya(arm, "ronin", "#121212", col)

    # World placement
    arm.location = (-1.5, 0.0, 0.0)
    arm.rotation_euler.z = math.radians(-90.0)

    return arm


def build_warlord() -> bpy.types.Object:
    """Build the Warlord oni character."""
    col = C.collection("warlord")
    arm = rig.build_armature("warlord")
    C.link(arm, col)
    rig.calibrate_poles(arm)

    # Materials
    mat_head = toon.toon("warlord_head", "#222222")
    mat_menpo = toon.toon("warlord_red", "#b3121f")
    mat_fang = toon.toon("warlord_fangs", "#f4f4f4")
    mat_eyes = toon.toon("warlord_eyes", "#ffcc33", emission=3.0)
    mat_dark = toon.toon("warlord_dark", "#1c1c1c")
    mat_armour = toon.toon("warlord_armour", "#8e1b1b")
    mat_horns = toon.toon("warlord_horns", "#d4a017")
    mat_lamellar = toon.toon("warlord_lamellar", "#1a1a1a")
    mat_forearm = toon.toon("warlord_forearm", "#3a3a3a")
    mat_hakama = toon.toon("warlord_hakama", "#3b0d0d")
    mat_foot = toon.toon("warlord_foot", "#111111")

    # Head
    part("warlord_head", C.sphere, "head", mat_head, outline=0.012, arm=arm, col=col, r=0.14, loc=(0.0, 0.0, 1.70))
    part("warlord_menpo", C.sphere, "head", mat_menpo, outline=0.012, arm=arm, col=col, r=0.12, loc=(0.0, 0.08, 1.66), scale=(1.0, 0.7, 0.9))

    # Fangs & eyes (outline 0.004)
    for side, sign in (("R", 1.0), ("L", -1.0)):
        part(
            f"warlord_fang.{side}",
            C.cone,
            "head",
            mat_fang,
            outline=0.004,
            arm=arm,
            col=col,
            r1=0.015,
            r2=0.0,
            depth=0.05,
            loc=(sign * 0.03, 0.14, 1.61),
            rot=(180.0, 0.0, 0.0),
        )
        part(
            f"warlord_eye.{side}",
            C.sphere,
            "head",
            mat_eyes,
            outline=0.004,
            arm=arm,
            col=col,
            r=0.02,
            loc=(sign * 0.045, 0.13, 1.71),
        )

    # Helmet parts
    part("warlord_helmet_dome", C.sphere, "head", mat_dark, outline=0.012, arm=arm, col=col, r=0.16, loc=(0.0, 0.0, 1.77), scale=(1.0, 1.0, 0.7))
    shikoro = C.cone(
        "warlord_helmet_shikoro",
        r1=0.26,
        r2=0.16,
        depth=0.14,
        loc=(0.0, -0.03, 1.60),
        mat=mat_armour,
        col=col,
    )
    bm = bmesh.new()
    bm.from_mesh(shikoro.data)
    verts = [v for v in bm.verts if v.co.y > 0.0]
    bmesh.ops.delete(bm, geom=verts, context="VERTS")
    bm.to_mesh(shikoro.data)
    bm.free()
    rig.attach(shikoro, arm, "head")
    toon.add_outline(shikoro, 0.012)

    part(
        "warlord_helmet_horn.R",
        C.cone,
        "head",
        mat_horns,
        outline=0.012,
        arm=arm,
        col=col,
        r1=0.03,
        r2=0.0,
        depth=0.24,
        loc=(0.10, 0.04, 1.93),
        rot=(0.0, 35.0, 0.0),
    )
    part(
        "warlord_helmet_horn.L",
        C.cone,
        "head",
        mat_horns,
        outline=0.012,
        arm=arm,
        col=col,
        r1=0.03,
        r2=0.0,
        depth=0.24,
        loc=(-0.10, 0.04, 1.93),
        rot=(0.0, -35.0, 0.0),
    )

    # Do (chest armour)
    part("warlord_do", C.cube, "chest", mat_armour, outline=0.012, arm=arm, col=col, size=1.0, scale=(0.46, 0.30, 0.44), loc=(0.0, 0.0, 1.30))

    # Lamellar lines (4 cubes)
    for i, z in enumerate((1.16, 1.24, 1.32, 1.40)):
        part(
            f"warlord_lamellar_{i}",
            C.cube,
            "chest",
            mat_lamellar,
            outline=0.012,
            arm=arm,
            col=col,
            size=1.0,
            scale=(0.47, 0.305, 0.012),
            loc=(0.0, 0.0, z),
        )

    # Sode (shoulder plates)
    for side, sign in (("R", 1.0), ("L", -1.0)):
        part(
            f"warlord_sode.{side}",
            C.cube,
            f"upperarm.{side}",
            mat_armour,
            outline=0.012,
            arm=arm,
            col=col,
            size=1.0,
            scale=(0.20, 0.07, 0.22),
            loc=(sign * 0.29, 0.0, 1.36),
        )

    # Kusazuri (skirt plates: 5 cubes around waist at z=0.90)
    kusazuri_angles = [0.0, 40.0, -40.0, 90.0, -90.0]
    for idx, a in enumerate(kusazuri_angles):
        a_rad = math.radians(a)
        px = 0.20 * math.sin(a_rad)
        py = 0.20 * math.cos(a_rad)
        part(
            f"warlord_kusazuri_{idx}",
            C.cube,
            "pelvis",
            mat_armour,
            outline=0.012,
            arm=arm,
            col=col,
            size=1.0,
            scale=(0.12, 0.03, 0.22),
            loc=(px, py, 0.90),
            rot=(0.0, 0.0, -a),
        )

    # Limbs
    for side in ("R", "L"):
        _add_limb(arm, "warlord", f"upperarm.{side}", 0.07, 0.065, mat_dark, col)
        _add_limb(arm, "warlord", f"forearm.{side}", 0.055, 0.05, mat_forearm, col)
        wrist_pos = arm.data.bones[f"forearm.{side}"].tail_local
        part(
            f"warlord_hand.{side}",
            C.sphere,
            f"forearm.{side}",
            mat_dark,
            outline=0.012,
            arm=arm,
            col=col,
            r=0.055,
            loc=tuple(wrist_pos),
        )
        _add_limb(arm, "warlord", f"thigh.{side}", 0.11, 0.13, mat_hakama, col)
        _add_limb(arm, "warlord", f"shin.{side}", 0.13, 0.12, mat_hakama, col)

    # Feet
    for side, sign in (("R", 1.0), ("L", -1.0)):
        part(
            f"warlord_foot.{side}",
            C.cube,
            f"foot.{side}",
            mat_foot,
            outline=0.012,
            arm=arm,
            col=col,
            size=1.0,
            scale=(0.09, 0.22, 0.06),
            loc=(sign * 0.11, 0.07, 0.04),
        )

    # Katana
    build_katana(arm, "warlord", "#b8bcc6", "#7a0f0f", "#111111", col=col)

    # Saya
    _build_saya(arm, "warlord", "#3b0d0d", col)

    # World placement
    arm.location = (1.5, 0.0, 0.0)
    arm.rotation_euler.z = math.radians(90.0)

    return arm
