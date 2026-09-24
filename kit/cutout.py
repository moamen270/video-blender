"""2D cut-out puppets: flat textured planes on a pivot hierarchy (Rick and Morty style).

Parts come from art/rm/export.py (assets/cutout/<char>/rig.json + PNGs). The picture plane is
world XZ (camera looks along +Y); each part is a plane hung on a pivot empty at its joint, and a
pivot hangs from its parent part's pivot, so rotating "sleeve.L" swings the forearm and hand.
Draw order = depth: a part with a higher z sits closer to the camera (more negative Y).

Angles are screen degrees, positive = counter-clockwise as seen by the camera.
"""
from __future__ import annotations

import json
import math
import os
import random

import bpy

import studio.core as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUTOUT = os.path.join(ROOT, "assets", "cutout")
S = 1.0 / 400.0          # metres per character unit: Morty ~1.45 m, Rick ~2.1 m
DZ = 0.002               # metres of depth per z step
FPS = C.FPS

_MATS: dict[str, bpy.types.Material] = {}


def flat_material(path: str) -> bpy.types.Material:
    """Unlit image material with straight alpha, blended."""
    if path in _MATS:
        return _MATS[path]
    img = bpy.data.images.load(path, check_existing=True)
    img.alpha_mode = "STRAIGHT"
    mat = bpy.data.materials.new("cut_" + os.path.basename(os.path.dirname(path)) + "_" + os.path.basename(path))
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Linear"
    tex.extension = "CLIP"
    emi = nt.nodes.new("ShaderNodeEmission")
    tra = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tex.outputs["Color"], emi.inputs["Color"])
    nt.links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    nt.links.new(tra.outputs[0], mix.inputs[1])
    nt.links.new(emi.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    else:  # Blender < 4.2
        mat.blend_method = "BLEND"
    mat.use_backface_culling = False
    _MATS[path] = mat
    return mat


def _quad(name: str, x0: float, x1: float, z0: float, z1: float) -> bpy.types.Mesh:
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for i, co in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = co
    me.update()
    return me


def _slot(name: str) -> str:
    return name.split(":")[0]


class Puppet:
    """A built cut-out character. Use the methods to animate it."""

    def __init__(self, char: str, *, tag: str | None = None, loc: tuple[float, float] = (0.0, 0.0),
                 depth: float = 0.0, scale: float = 1.0, col=None):
        rig = json.loads(open(os.path.join(CUTOUT, char, "rig.json"), encoding="utf-8").read())
        self.char = char
        self.tag = tag or char
        self.rig = rig
        cx, ground = rig["cx"], rig["ground"]
        self.parts = {p["name"]: p for p in rig["parts"]}
        self.root = C.empty(f"{self.tag}.root", loc=(loc[0], depth, loc[1]))
        self.root.scale = (scale, scale, scale)
        if col is not None:
            C.link(self.root, col)
        self.pivots: dict[str, bpy.types.Object] = {}
        self.slots: dict[str, dict[str, bpy.types.Object]] = {}
        self.current: dict[str, str] = {}
        self.base_loc: dict[str, tuple[float, float, float]] = {}

        # one pivot per slot (swap sets share the pivot of their first member)
        for p in rig["parts"]:
            sl = _slot(p["name"])
            if sl in self.pivots:
                continue
            px, py = p["pivot"]
            self.pivots[sl] = bpy.data.objects.new(f"{self.tag}.{sl}", None)
            self.pivots[sl].empty_display_size = 0.03
            self.pivots[sl]["world_px"] = ((px - cx) * S, (ground - py) * S)
        for sl, e in self.pivots.items():
            (col or bpy.context.scene.collection).objects.link(e)
        # parent pivots, locations relative to the parent pivot
        for p in rig["parts"]:
            sl = _slot(p["name"])
            e = self.pivots[sl]
            if e.parent is not None:
                continue
            par = self.pivots.get(p["parent"]) if p["parent"] else self.root
            wx, wz = e["world_px"]
            if par is self.root:
                e.parent = self.root
                e.location = (wx, 0.0, wz)
            else:
                pwx, pwz = par["world_px"]
                e.parent = par
                e.location = (wx - pwx, 0.0, wz - pwz)
            self.base_loc[sl] = tuple(e.location)
        # planes
        for p in rig["parts"]:
            sl = _slot(p["name"])
            px, py = p["pivot"]
            x0, y0, x1, y1 = p["box"]
            me = _quad(f"{self.tag}.{p['name']}", (x0 - px) * S, (x1 - px) * S, (py - y1) * S, (py - y0) * S)
            ob = bpy.data.objects.new(f"{self.tag}.{p['name']}", me)
            ob.data.materials.append(flat_material(os.path.join(CUTOUT, char, p["png"])))
            (col or bpy.context.scene.collection).objects.link(ob)
            ob.parent = self.pivots[sl]
            ob.location = (0.0, -p["z"] * DZ, 0.0)
            if ":" in p["name"]:
                self.slots.setdefault(sl, {})[p["name"].split(":")[1]] = ob
        # rest pose keyed at frame 1 so later poses ease out of it instead of leaking backwards
        for e in self.pivots.values():
            e.keyframe_insert("rotation_euler", index=1, frame=1)
            e.keyframe_insert("location", frame=1)
            e.keyframe_insert("scale", frame=1)
        # default swaps
        for sl, keys in self.slots.items():
            first = "X" if "X" in keys else ("open" if "open" in keys else next(iter(keys)))
            self.swap(sl, first, 1)

    # ------------------------------------------------------------------ basics
    def at(self, frame: int, x: float, z: float = 0.0, interp: str | None = None) -> None:
        self.root.location.x, self.root.location.z = x, z
        self.root.keyframe_insert("location", frame=frame)
        if interp:
            C.set_interp_at(self.root, frame, interp)

    def face(self, frame: int, sign: int) -> None:
        """Face screen-left (-1) or screen-right (+1): mirror the whole puppet."""
        self.root.scale.x = abs(self.root.scale.x) * (1 if sign >= 0 else -1)
        self.root.keyframe_insert("scale", frame=frame)
        for fc in C.fcurves(self.root):
            if fc.data_path == "scale":
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"

    def rot(self, part: str, frame: int, deg: float) -> None:
        e = self.pivots[part]
        e.rotation_euler.y = -math.radians(deg)
        e.keyframe_insert("rotation_euler", index=1, frame=frame)

    def pose(self, frame: int, **angles: float) -> None:
        """pose(12, head=5, **{"sleeve.L": -30}) — part names with dots go through **{...}."""
        for part, deg in angles.items():
            self.rot(part, frame, deg)

    def shift(self, part: str, frame: int, dx: float = 0.0, dz: float = 0.0) -> None:
        """Offset a pivot from its rest place, in character units (x right, z up)."""
        e = self.pivots[part]
        bx, by, bz = self.base_loc[part]
        e.location = (bx + dx * S, by, bz + dz * S)
        e.keyframe_insert("location", frame=frame)

    def squash(self, part: str, frame: int, sx: float = 1.0, sz: float = 1.0) -> None:
        e = self.pivots[part]
        e.scale = (sx, 1.0, sz)
        e.keyframe_insert("scale", frame=frame)

    def swap(self, slot: str, key: str, frame: int) -> None:
        for k, ob in self.slots[slot].items():
            on = k == key
            ob.hide_render = not on
            ob.hide_viewport = not on
            ob.keyframe_insert("hide_render", frame=frame)
            ob.keyframe_insert("hide_viewport", frame=frame)
        self.current[slot] = key

    def show(self, part: str, frame: int, on: bool) -> None:
        C.visible(self.pivots[part], frame, on)

    # ------------------------------------------------------------------ face
    def eyes(self) -> list[str]:
        return [n for n in ("eye.L", "eye.R") if n in self.pivots]

    def look(self, frame: int, dx: float, dz: float = 0.0) -> None:
        """Move both pupils (character units, keep within ~ +-12 for Morty, +-9 for Rick)."""
        for n in ("pupil.L", "pupil.R"):
            if n in self.pivots:
                self.shift(n, frame, dx, dz)

    def blink(self, frame: int, hold: int = 1) -> None:
        for e in self.eyes():
            self.squash(e, frame - 1, 1.0, 1.0)
            self.squash(e, frame + 1, 1.0, 0.1)
            self.squash(e, frame + 1 + hold, 1.0, 0.1)
            self.squash(e, frame + 3 + hold, 1.0, 1.0)

    def auto_blink(self, start: int, end: int, seed: int = 0, every: tuple[float, float] = (2.2, 4.5)) -> list[int]:
        rnd = random.Random(seed)
        f = start + int(rnd.uniform(0.6, 1.6) * FPS)
        out = []
        while f < end - 6:
            self.blink(f)
            out.append(f)
            f += int(rnd.uniform(*every) * FPS)
        return out

    def brows(self, frame: int, deg: float = 0.0, lift: float = 0.0) -> None:
        """Brow attitude: deg > 0 = angry (inner ends down), < 0 = worried; lift in char units."""
        if "brow" in self.pivots:                        # unibrow: lift + squash
            self.shift("brow", frame, 0.0, lift)
            self.squash("brow", frame, 1.0, 1.0 + max(-0.4, min(0.6, -deg / 40.0)))
        for n, s in (("brow.L", -1), ("brow.R", 1)):
            if n in self.pivots:
                self.rot(n, frame, s * deg)
                self.shift(n, frame, 0.0, lift)

    def lipsync(self, cues: list[dict], start: int, slot: str = "mouth") -> int:
        """Swap mouths from Rhubarb cues (seconds) starting at `start`; returns the end frame."""
        end = start
        for c in cues:
            f = start + int(round(float(c["start"]) * FPS))
            self.swap(slot, c["value"], f)
            end = start + int(round(float(c["end"]) * FPS))
        self.swap(slot, "X", end)
        return end

    # ------------------------------------------------------------------ body
    def breathe(self, start: int, end: int, period: float = 3.2, amount: float = 0.012) -> None:
        """Slow idle: torso squash and a small head counter-bob."""
        step = int(period * FPS / 2)
        f, up = start, True
        while f <= end:
            self.squash("torso", f, 1.0, 1.0 + (amount if up else 0.0))
            up = not up
            f += step

    def hand(self, side: str, kind: str, frame: int) -> None:
        self.swap(f"hand.{side}", kind, frame)

    def _pv(self, slot: str) -> tuple[float, float]:
        """Rest pivot of a slot in world metres relative to the root (x right, z up)."""
        p = next(p for p in self.rig["parts"] if _slot(p["name"]) == slot)
        return ((p["pivot"][0] - self.rig["cx"]) * S, (self.rig["ground"] - p["pivot"][1]) * S)

    def reach(self, side: str, frame: int, target: tuple[float, float], bend: int = 1,
              grip: float = 26.0) -> tuple[float, float]:
        """2-link IK: put the grip point (`grip` char units below the wrist, along the forearm) on the
        world point `target` (x, z). Assumes the torso/hips are at rest and the puppet is not mirrored.
        bend = +1 elbow bends one way, -1 the other. Returns (upper, fore) screen degrees."""
        sc = self.root.scale.z
        rx, rz = self.root.location.x, self.root.location.z
        sh, el, wr = self._pv(f"sleeve.{side}"), self._pv(f"forearm.{side}"), self._pv(f"hand.{side}")
        u0 = (el[0] - sh[0], el[1] - sh[1])
        v0 = (wr[0] - el[0], wr[1] - el[1])
        l1 = math.hypot(*u0) * sc
        v_len = math.hypot(*v0)
        l2 = (v_len + grip * S) * sc
        tx, tz = target[0] - (rx + sh[0] * sc), target[1] - (rz + sh[1] * sc)
        d = min(max(math.hypot(tx, tz), abs(l1 - l2) + 1e-4), l1 + l2 - 1e-4)
        base = math.atan2(tz, tx)
        cos_a = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
        a = math.acos(max(-1.0, min(1.0, cos_a)))
        a1 = base + bend * a                                    # upper arm absolute angle
        ex, ez = l1 * math.cos(a1), l1 * math.sin(a1)
        a2 = math.atan2(tz - ez, tx - ex)                       # forearm absolute angle
        r_up = math.degrees(a1 - math.atan2(u0[1], u0[0]))
        r_fo = math.degrees(a2 - math.atan2(v0[1], v0[0])) - r_up
        r_up = (r_up + 180) % 360 - 180
        r_fo = (r_fo + 180) % 360 - 180
        self.rot(f"sleeve.{side}", frame, r_up)
        self.rot(f"forearm.{side}", frame, r_fo)
        return r_up, r_fo

    def grip_world(self, side: str, frame: int, grip: float = 26.0) -> tuple[float, float]:
        """World (x, z) of the grip point at `frame` (evaluates the scene)."""
        bpy.context.scene.frame_set(frame)
        e = self.pivots[f"hand.{side}"]
        m = e.matrix_world
        p = m @ __import__("mathutils").Vector((0.0, 0.0, -grip * S))
        return (p.x, p.z)

    def prop(self, name: str, slot: str, *, at: tuple[float, float] = (0.0, -30.0), deg: float = 0.0,
             z: float = 30, visible_from: int | None = 1) -> bpy.types.Object:
        """Hang a prop (assets/cutout/props/<name>.png) on a pivot; `at` = centre offset in char units."""
        meta = json.loads(open(os.path.join(CUTOUT, "props", "props.json"), encoding="utf-8").read())[name]
        w, h = meta["size"]
        me = _quad(f"{self.tag}.prop.{name}.{slot}", -w / 2 * S, w / 2 * S, -h / 2 * S, h / 2 * S)
        ob = bpy.data.objects.new(me.name, me)
        ob.data.materials.append(flat_material(os.path.join(CUTOUT, "props", meta["png"])))
        self.root.users_collection[0].objects.link(ob)
        ob.parent = self.pivots[slot]
        ob.location = (at[0] * S, -z * DZ, at[1] * S)
        ob.rotation_euler.y = -math.radians(deg)
        if visible_from is not None:
            if visible_from > 1:
                C.visible(ob, 1, False)
            C.visible(ob, visible_from, True)
        return ob


def backdrop(name: str = "garage", depth: float = 1.0) -> bpy.types.Object:
    """Flat set painting from assets/cutout/<name>/<name>.json, feet line at world z = 0."""
    meta = json.loads(open(os.path.join(CUTOUT, name, f"{name}.json"), encoding="utf-8").read())
    w, h = meta["size"]
    cx, gy = meta["cx"], meta["ground_y"]
    me = _quad(f"set.{name}", (0 - cx) * S, (w - cx) * S, (gy - h) * S, gy * S)
    ob = bpy.data.objects.new(me.name, me)
    ob.data.materials.append(flat_material(os.path.join(CUTOUT, name, meta["png"])))
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (0.0, depth, 0.0)
    return ob


def set_linear_constant_bools() -> None:
    """Boolean visibility keys must hold (Blender already steps them, this is a safety net)."""
    for ob in bpy.data.objects:
        if ob.animation_data and ob.animation_data.action:
            for fc in C.fcurves(ob):
                if fc.data_path in ("hide_render", "hide_viewport"):
                    for kp in fc.keyframe_points:
                        kp.interpolation = "CONSTANT"


def ortho_camera(name: str, center: tuple[float, float], height: float, *, y: float = -10.0) -> bpy.types.Object:
    """Orthographic camera looking along +Y; `height` = metres of world visible vertically (9:16 frame)."""
    cam_data = bpy.data.cameras.new(name)
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = height          # the larger dimension (vertical in 1080x1920)
    cam_data.clip_start, cam_data.clip_end = 0.1, 100.0
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (center[0], y, center[1])
    cam.rotation_euler = (math.radians(90), 0.0, 0.0)
    return cam


def key_camera(cam: bpy.types.Object, frame: int, center: tuple[float, float], height: float,
               interp: str = "BEZIER") -> None:
    cam.location.x, cam.location.z = center
    cam.keyframe_insert("location", frame=frame)
    cam.data.ortho_scale = height
    cam.data.keyframe_insert("ortho_scale", frame=frame)
    C.set_interp_at(cam, frame, interp)
    C.set_interp_at(cam.data, frame, interp)
