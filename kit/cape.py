"""Skinned cape with baked spring motion (Task F1)."""
from __future__ import annotations

import math

import bpy
from mathutils import Matrix, Quaternion, Vector

from kit import qchar as Q
from studio import core as C

NUM_COLS = 17
NUM_ROWS = 10


def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between two scalars."""
    return a + (b - a) * t


def P(u: float, v: float) -> Vector:
    """Evaluate native cape coordinates at parameter (u, v)."""
    zb = 0.30 + 0.12 * abs(math.sin(2.0 * math.pi * u))
    z = _lerp(2.02, zb, v)
    x = u * _lerp(0.36, 0.62, v)
    y = _lerp(0.20, 0.55, v) - _lerp(0.04, 0.12, v) * (u ** 2)
    return Vector((x, y, z))


def add_cape_bones(qc: Q.QChar) -> dict[str, list[str]]:
    """Create 3 chains x 3 deform bones in qc.arm."""
    bpy.context.view_layer.objects.active = qc.arm
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = qc.arm.data.edit_bones

    chains = {"R": -1.0, "C": 0.0, "L": 1.0}
    result: dict[str, list[str]] = {"R": [], "C": [], "L": []}
    torso_eb = edit_bones["Torso"]

    for c, u_c in chains.items():
        for j in range(3):
            bname = f"cape.{c}.{j}"
            eb = edit_bones.new(bname)
            eb.head = P(u_c, j / 3.0)
            eb.tail = P(u_c, (j + 1) / 3.0)
            eb.roll = 0.0
            eb.use_deform = True
            if j == 0:
                eb.parent = torso_eb
                eb.use_connect = False
            else:
                eb.parent = edit_bones[f"cape.{c}.{j - 1}"]
                eb.use_connect = True
            result[c].append(bname)

    bpy.ops.object.mode_set(mode="OBJECT")
    return result


def build_cape(qc: Q.QChar, mat: bpy.types.Material) -> bpy.types.Object:
    """Build the skinned cape mesh in native coordinates with vertex groups and modifiers."""
    add_cape_bones(qc)

    num_cols = NUM_COLS
    num_rows = NUM_ROWS
    verts: list[Vector] = []
    for r in range(num_rows):
        v = r / (num_rows - 1)
        for c in range(num_cols):
            u = -1.0 + 2.0 * c / (num_cols - 1)
            verts.append(P(u, v))

    faces: list[list[int]] = []
    for r in range(num_rows - 1):
        for c in range(num_cols - 1):
            i0 = r * num_cols + c
            i1 = r * num_cols + (c + 1)
            i2 = (r + 1) * num_cols + (c + 1)
            i3 = (r + 1) * num_cols + c
            faces.append([i0, i1, i2, i3])

    mesh_name = f"{qc.name}_cape"
    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    mesh.materials.append(mat)

    cape = bpy.data.objects.new(mesh_name, mesh)
    cape.parent = qc.arm
    cape.matrix_parent_inverse = Matrix.Identity(4)
    cape.location = (0.0, 0.0, 0.0)
    cape.rotation_euler = (0.0, 0.0, 0.0)
    cape.scale = (1.0, 1.0, 1.0)

    target_col = qc.body.users_collection[0] if qc.body.users_collection else None
    C.link(cape, target_col)

    vg_torso = cape.vertex_groups.new(name="Torso")
    vgs: dict[str, bpy.types.VertexGroup] = {}
    for ch in ["R", "C", "L"]:
        for j in range(3):
            bname = f"cape.{ch}.{j}"
            vgs[bname] = cape.vertex_groups.new(name=bname)

    for r in range(num_rows):
        v = r / (num_rows - 1)
        s = 3.0 * v
        w_j = [max(0.0, 1.0 - abs(s - (j + 0.5))) for j in range(3)]
        sum_wj = sum(w_j)
        if sum_wj > 0.0:
            w_j = [w / sum_wj for w in w_j]
        else:
            w_j = [0.0, 0.0, 0.0]

        wT = max(0.0, 1.0 - v / 0.15)

        for c in range(num_cols):
            u = -1.0 + 2.0 * c / (num_cols - 1)
            idx = r * num_cols + c

            if u <= 0.0:
                wR = -u
                wC = 1.0 + u
                wL = 0.0
            else:
                wR = 0.0
                wC = 1.0 - u
                wL = u
            wc = {"R": wR, "C": wC, "L": wL}

            if wT >= 0.001:
                vg_torso.add([idx], wT, "REPLACE")

            for ch in ["R", "C", "L"]:
                w_ch = wc[ch]
                if w_ch <= 0.0:
                    continue
                for j in range(3):
                    w = (1.0 - wT) * w_ch * w_j[j]
                    if w >= 0.001:
                        vgs[f"cape.{ch}.{j}"].add([idx], w, "REPLACE")

    mod_arm = cape.modifiers.new("Armature", "ARMATURE")
    mod_arm.object = qc.arm

    mod_thick = cape.modifiers.new("thick", "SOLIDIFY")
    mod_thick.thickness = 0.012 / qc.scale
    mod_thick.offset = 0.0

    qc.parts["cape"] = cape
    return cape


def bake_cape(
    qc: Q.QChar,
    start: int,
    end: int,
    *,
    stiffness: float = 0.06,  # senior sweep 2026-09-24: 0.06 / 0.25 -> tip trails ~0.17 m at a walk,
    drag: float = 0.25,       # swings to the legs on a stop and settles in ~18 frames
    max_forward: float = 0.02,
) -> None:
    """Bake damped spring secondary motion for cape bones."""
    A = qc.arm
    scene = bpy.context.scene

    A.animation_data_create()

    chains = ["R", "C", "L"]
    all_bones: list[str] = []
    for c in chains:
        for j in range(3):
            all_bones.append(f"cape.{c}.{j}")

    rest_torso_inv = A.data.bones["Torso"].matrix_local.inverted()
    rest_bone = {b: A.data.bones[b].matrix_local for b in all_bones}
    bone_len = {b: A.data.bones[b].length for b in all_bones}

    X: dict[str, dict[int, Vector]] = {}
    Xprev: dict[str, dict[int, Vector]] = {}

    for f in range(start, end + 1):
        scene.frame_set(f)
        Mw = A.matrix_world.copy()
        Mt = A.pose.bones["Torso"].matrix.copy()

        def rigid(b_name: str) -> Matrix:
            return Mt @ rest_torso_inv @ rest_bone[b_name]

        fwd = (qc.root.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()
        sw = Mw.to_scale()[0]
        Minv3 = Mw.inverted().to_3x3()

        for c in chains:
            h0 = rigid(f"cape.{c}.0").translation
            t0 = rigid(f"cape.{c}.0") @ Vector((0.0, bone_len[f"cape.{c}.0"], 0.0))
            t1 = rigid(f"cape.{c}.1") @ Vector((0.0, bone_len[f"cape.{c}.1"], 0.0))
            t2 = rigid(f"cape.{c}.2") @ Vector((0.0, bone_len[f"cape.{c}.2"], 0.0))

            X_0 = Mw @ h0
            T = {1: Mw @ t0, 2: Mw @ t1, 3: Mw @ t2}

            if f == start:
                X[c] = {1: T[1].copy(), 2: T[2].copy(), 3: T[3].copy()}
                Xprev[c] = {1: T[1].copy(), 2: T[2].copy(), 3: T[3].copy()}
            else:
                for k in (1, 2, 3):
                    vel = (X[c][k] - Xprev[c][k]) * (1.0 - drag)
                    Xnew = X[c][k] + vel + stiffness * (T[k] - X[c][k])
                    Xprev[c][k] = X[c][k].copy()
                    X[c][k] = Xnew

            # Body collision
            for k in (1, 2, 3):
                e = (X[c][k] - T[k]).dot(fwd)
                if e > max_forward:
                    X[c][k] -= (e - max_forward) * fwd

            # Length constraint
            for k in (1, 2, 3):
                prev_pt = X_0 if k == 1 else X[c][k - 1]
                diff = X[c][k] - prev_pt
                if diff.length > 1e-6:
                    dir_vec = diff.normalized()
                else:
                    dir_vec = (T[k] - prev_pt).normalized()
                X[c][k] = prev_pt + dir_vec * (bone_len[f"cape.{c}.{k - 1}"] * sw)

            # Bone rotations
            M_prev: Matrix | None = None
            for j in range(3):
                b = f"cape.{c}.{j}"
                p = "Torso" if j == 0 else f"cape.{c}.{j - 1}"
                M_parent = Mt if j == 0 else M_prev
                Rest_p_inv = rest_torso_inv if j == 0 else rest_bone[p].inverted()
                Rest_b = rest_bone[b]

                M0 = M_parent @ Rest_p_inv @ Rest_b
                R0 = M0.to_quaternion()
                y0 = (M0.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()

                pt_j = X_0 if j == 0 else X[c][j]
                pt_next = X[c][j + 1]
                d = (Minv3 @ (pt_next - pt_j)).normalized()

                q = y0.rotation_difference(d)
                basis = R0.inverted() @ q @ R0

                pb = A.pose.bones[b]
                pb.rotation_mode = "QUATERNION"
                pb.rotation_quaternion = basis
                pb.keyframe_insert("rotation_quaternion", frame=f)

                M_j = Matrix.Translation(M0.translation) @ (q @ R0).to_matrix().to_4x4()
                M_prev = M_j
