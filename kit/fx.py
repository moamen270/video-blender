"""Visual effects module: sparks, smear ribbons, camera shake, dust, and helmet split (Task T6)."""
from __future__ import annotations

import math
import random
from typing import Sequence

import bmesh
import bpy
from mathutils import Vector

from kit import toon
from studio import core as C


def sword_point(arm: bpy.types.Object, dist: float) -> Vector:
    """World point at `dist` metres along the sword bone."""
    pb = arm.pose.bones["sword"]
    return arm.matrix_world @ (pb.matrix @ Vector((0.0, dist, 0.0)))


def spark(
    point: Sequence[float] | Vector,
    frame: int,
    seed: int = 0,
) -> list[bpy.types.Object]:
    """Create clash sparks: 14 streaks, flash sphere, and point light."""
    rng = random.Random(seed)
    col = C.collection("fx")
    p = Vector(point)
    created: list[bpy.types.Object] = []

    mat_spark = toon.toon("fx_spark", "#fff2b0", emission=8.0)
    for i in range(14):
        v = Vector((rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)))
        while v.length < 1e-6:
            v = Vector((rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)))
        direction = v.normalized()
        rot_euler = direction.to_track_quat("Z", "Y").to_euler()

        streak = C.cube(
            f"fx_spark_streak_{frame}_{i}",
            scale=(0.012, 0.012, 0.07),
            mat=mat_spark,
            col=col,
        )
        for vert in streak.data.vertices:
            vert.co.x *= 0.012
            vert.co.y *= 0.012
            vert.co.z *= 0.07
        streak.scale = (1.0, 1.0, 1.0)
        streak.rotation_euler = rot_euler

        C.visible(streak, 1, False)
        if frame - 1 >= 1:
            C.visible(streak, frame - 1, False)
        C.visible(streak, frame, True)
        C.visible(streak, frame + 6, False)

        p_end = p + direction * rng.uniform(0.35, 0.6)
        C.key(streak, frame, loc=tuple(p), scale=(1.0, 1.0, 1.0))
        C.key(streak, frame + 5, loc=tuple(p_end), scale=(0.0, 0.0, 0.0))
        created.append(streak)

    # Flash sphere
    mat_flash = toon.toon("fx_flash", "#ffffff", emission=12.0)
    flash = C.sphere(
        f"fx_spark_flash_{frame}",
        r=0.05,
        loc=tuple(p),
        mat=mat_flash,
        col=col,
    )
    C.visible(flash, 1, False)
    if frame - 1 >= 1:
        C.visible(flash, frame - 1, False)
        C.key(flash, frame - 1, scale=(0.0, 0.0, 0.0))
    C.visible(flash, frame, True)
    C.key(flash, frame, scale=(1.0, 1.0, 1.0))
    C.key(flash, frame + 3, scale=(0.0, 0.0, 0.0))
    C.visible(flash, frame + 4, False)
    C.visible(flash, frame + 6, False)
    created.append(flash)

    # Point light
    light_data = bpy.data.lights.new("fx_spark_light", "POINT")
    light_data.color = (1.0, 0.9, 0.6)
    light_obj = bpy.data.objects.new("fx_spark_light", light_data)
    light_obj.location = tuple(p)
    col.objects.link(light_obj)

    for f_k, energy in [(frame - 1, 0.0), (frame, 1500.0), (frame + 3, 0.0)]:
        if f_k >= 1:
            light_data.energy = energy
            light_data.keyframe_insert("energy", frame=f_k)
    created.append(light_obj)

    return created


def smear(
    arm: bpy.types.Object,
    f0: int,
    f1: int,
    name: str,
) -> bpy.types.Object:
    """Build sword slash smear ribbon mesh sampled from f0 to f1."""
    scene = bpy.context.scene
    cur = scene.frame_current
    frame_range = list(range(max(f0, f1 - 4), f1 + 1))
    n = len(frame_range)
    samples: list[tuple[Vector, Vector]] = []
    for i, f in enumerate(frame_range):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        inner = sword_point(arm, 0.78)
        outer = sword_point(arm, 1.05)
        t = i / (n - 1) if n > 1 else 1.0
        inner_pt = outer + (inner - outer) * t
        samples.append((inner_pt, outer))
    scene.frame_set(cur)
    bpy.context.view_layer.update()

    bm = bmesh.new()
    verts_a = []
    verts_b = []
    for a, b in samples:
        va = bm.verts.new(a)
        vb = bm.verts.new(b)
        verts_a.append(va)
        verts_b.append(vb)

    for i in range(len(samples) - 1):
        bm.faces.new((verts_a[i], verts_b[i], verts_b[i + 1], verts_a[i + 1]))

    mesh = bpy.data.meshes.new(f"fx_smear_{name}")
    bm.to_mesh(mesh)
    bm.free()

    for p in mesh.polygons:
        p.use_smooth = False

    mat = toon.toon("fx_smear", "#dfe8ff", emission=1.5)
    mesh.materials.append(mat)

    obj = bpy.data.objects.new(f"fx_smear_{name}", mesh)
    col = C.collection("fx")
    col.objects.link(obj)

    C.visible(obj, 1, False)
    C.visible(obj, f1, True)
    C.visible(obj, f1 + 2, False)

    return obj


def shake(
    cam: bpy.types.Object,
    f0: int,
    f1: int,
    amp: float = 0.06,
    seed: int = 3,
) -> None:
    """Add camera shake keyframes decaying linearly from frame f0 to f1.

    If the camera already has location keyframes (e.g. from a push-in),
    evaluates cam.location at each frame before adding the shake offset,
    preserving existing camera travel.
    """
    rng = random.Random(seed)
    scene = bpy.context.scene
    has_loc_keys = any(fc.data_path == "location" for fc in C.fcurves(cam))

    if has_loc_keys:
        cur = scene.frame_current
        base_locs: dict[int, Vector] = {}
        for f in range(max(1, f0 - 1), f1 + 2):
            scene.frame_set(f)
            bpy.context.view_layer.update()
            base_locs[f] = cam.location.copy()
        scene.frame_set(cur)

        if f0 - 1 >= 1 and (f0 - 1) in base_locs:
            cam.location = base_locs[f0 - 1]
            cam.keyframe_insert("location", frame=f0 - 1)

        for f in range(f0, f1 + 1):
            k = 1.0 - (f - f0) / max(1, f1 - f0)
            offset = Vector((rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0) * 0.3, rng.uniform(-1.0, 1.0))) * (amp * k)
            cam.location = base_locs[f] + offset
            cam.keyframe_insert("location", frame=f)

        if (f1 + 1) in base_locs:
            cam.location = base_locs[f1 + 1]
            cam.keyframe_insert("location", frame=f1 + 1)
    else:
        base = cam.location.copy()
        for f in range(f0, f1 + 1):
            k = 1.0 - (f - f0) / max(1, f1 - f0)
            offset = Vector((rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0) * 0.3, rng.uniform(-1.0, 1.0))) * (amp * k)
            cam.location = base + offset
            cam.keyframe_insert("location", frame=f)

        cam.location = base
        if f0 - 1 >= 1:
            cam.keyframe_insert("location", frame=f0 - 1)
        cam.keyframe_insert("location", frame=f1 + 1)


def dust(
    point: Sequence[float] | Vector,
    frame: int,
) -> list[bpy.types.Object]:
    """Create 8 dust puffs expanding and sinking over 10 frames."""
    col = C.collection("fx")
    p = Vector(point)
    mat_dust = toon.toon("fx_dust", "#6b7085", emission=0.0)
    created: list[bpy.types.Object] = []

    for i in range(8):
        angle = 2.0 * math.pi * i / 8.0
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        x0 = p.x + 0.05 * cos_a
        y0 = p.y + 0.05 * sin_a
        z0 = p.z

        x10 = p.x + 0.25 * cos_a
        y10 = p.y + 0.25 * sin_a
        z10 = p.z - 0.02

        s = C.sphere(
            f"fx_dust_{frame}_{i}",
            r=0.06,
            scale=(1.0, 1.0, 0.4),
            loc=(x0, y0, z0),
            mat=mat_dust,
            col=col,
        )

        C.visible(s, 1, False)
        if frame - 1 >= 1:
            C.visible(s, frame - 1, False)
        C.visible(s, frame, True)
        C.visible(s, frame + 11, False)

        C.key(s, frame, loc=(x0, y0, z0), scale=(1.0, 1.0, 0.4))
        C.key(s, frame + 10, loc=(x10, y10, z10), scale=(0.0, 0.0, 0.0))

        created.append(s)

    return created


def helmet_split(
    arm: bpy.types.Object,
    frame: int,
) -> list[bpy.types.Object]:
    """Split the warlord helmet into pieces falling in parabolic arcs."""
    scene = bpy.context.scene
    scene.frame_set(frame)
    bpy.context.view_layer.update()

    parts = [o for o in bpy.data.objects if o.name.startswith("warlord_helmet_")]
    head_c = arm.matrix_world @ arm.pose.bones["head"].head
    col = C.collection("fx")
    duplicates: list[bpy.types.Object] = []

    for part in parts:
        mw = part.matrix_world.copy()
        dup = part.copy()
        dup.data = part.data
        col.objects.link(dup)
        dup.parent = None
        dup.matrix_world = mw
        dup.name = "fx_" + part.name

        for m in list(dup.modifiers):
            if m.name == "outline":
                dup.modifiers.remove(m)

        inv_arm_m = arm.matrix_world.inverted()
        lx = (inv_arm_m @ mw.translation).x - (inv_arm_m @ head_c).x
        side = 1.0 if lx >= 0.0 else -1.0
        dir_vec = (arm.matrix_world.to_3x3() @ Vector((side, 0.0, 0.0))).normalized()

        C.visible(dup, 1, False)
        if frame - 1 >= 1:
            C.visible(dup, frame - 1, False)
        C.visible(dup, frame, True)

        init_rot = mw.to_euler()
        for k in range(0, 17, 2):
            f_k = frame + k
            t = k / 16.0
            pos = (
                mw.translation
                + dir_vec * 0.35 * t
                + Vector((0.0, 0.0, -(mw.translation.z - 0.1) * t * t + 0.25 * t * (1.0 - t) * 4.0))
            )

            rot = init_rot.copy()
            d_rot = math.radians(90.0) * t * side
            if abs(dir_vec.x) > abs(dir_vec.y):
                rot.y += d_rot
            else:
                rot.x += d_rot

            dup.location = pos
            dup.rotation_euler = rot
            dup.keyframe_insert("location", frame=f_k)
            dup.keyframe_insert("rotation_euler", frame=f_k)

        C.visible(part, 1, True)
        C.visible(part, frame, False)

        duplicates.append(dup)

    return duplicates
