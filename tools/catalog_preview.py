"""Render preview thumbnails for library/catalog.json items that have a Blender preview recipe.

    blender -b --python tools/catalog_preview.py -- [--ids character/ryu,set/gotham-mart] [--kind rig] [--force]

Writes library/previews/<id with / -> __>.jpg (360x640, the vertical Shorts frame) and sets item["preview"]["image"].
Recipes: character (kit.cast CAST), rig (Quaternius .blend), pose (kit.fight pose on a cast member), samurai,
samurai_pose, prop, fx, set. Audio previews (waveforms) are made by tools/catalog.py, not here.
Existing images are kept unless --force (a preview is re-rendered only when the component changed).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy
from mathutils import Vector

from kit import cast, fight, look, post, qchar, shots
from studio import core as C

CATALOG = os.path.join(ROOT, "library", "catalog.json")
PREV = os.path.join(ROOT, "library", "previews")
THREEQ = ((2.64, 3.77, 1.05), (0.0, 0.0, 0.9), 50.0)   # tools/turnaround.py 3/4 view (character faces +y)
BLENDER_RECIPES = {"character", "rig", "pose", "samurai", "samurai_pose", "prop", "fx", "set"}


def image_path(item_id: str) -> str:
    return os.path.join(PREV, item_id.replace("/", "__") + ".jpg")


def scene_objects_bbox(kinds=("MESH", "CURVE"), exclude=()) -> tuple[Vector, Vector]:
    bpy.context.view_layer.update()
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in bpy.context.scene.objects:
        if o.type in kinds and not o.hide_render and o.name not in exclude:
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    return lo, hi


def fit_camera(direction=(0.55, 1.0, 0.45), lens=50.0, margin=1.25, exclude=()) -> bpy.types.Object:
    """Camera looking at the bbox of everything (but `exclude`) from `direction`, framing it in the vertical frame."""
    lo, hi = scene_objects_bbox(exclude=exclude)
    center, size = (lo + hi) / 2, max((hi - lo).length, 0.05)
    vfov = 2 * math.atan(18.0 / lens)
    dist = margin * size / (2 * math.tan(vfov / 2)) * 1.1
    d = Vector(direction).normalized()
    return C.camera("cam_prev", tuple(center + d * dist), tuple(center), lens=lens)


def studio_look(target=(0, 0, 0.9)) -> str:
    """Night studio lights + floor; returns the floor's name (to keep it out of auto-framing)."""
    look.store_night(target=target)
    return look.floor().name


def toon_rig(qc: qchar.QChar) -> None:
    """Raw Quaternius materials render near-black under our lights: convert them to the kit's toon look."""
    for slot in qc.body.material_slots:
        if slot.material:
            look.toon_tex(slot.material)
    # the pack's "Skin" is a near-black placeholder (base 0.013) that every cast builder replaces
    qchar.assign(qc, look.toon2(f"{qc.name}_skin", cast.DUMMY), materials=["Skin"])


def standin() -> qchar.QChar:
    qc = qchar.load_character("BaseCharacter", "standin")
    toon_rig(qc)
    qchar.set_action(qc, "Idle", 1)
    return qc


def build(item: dict) -> bpy.types.Object:
    """Build the recipe's scene and return the camera."""
    r = item["preview"]
    rec = r["recipe"]
    if rec in ("character", "pose"):
        qc = cast.CAST[r["cast"]]()
        if rec == "pose":
            fight.prepare(qc)
            fight.key_pose(qc, 1, getattr(fight, r["pose"]))
        else:
            qchar.set_action(qc, "Idle", 1)
        studio_look()
        return C.camera("cam_prev", *THREEQ[:2], lens=THREEQ[2])
    if rec == "rig":
        qc = qchar.load_character(r["file"], "rig")
        toon_rig(qc)
        qchar.set_action(qc, "Idle", 1)
        if not item.get("notes") and item["id"] == "rig/basecharacter":
            item["notes"] = "actions: " + ", ".join(sorted(qc.actions))
        studio_look()
        return C.camera("cam_prev", *THREEQ[:2], lens=THREEQ[2])
    if rec in ("samurai", "samurai_pose"):
        from kit import pose as P, samurai
        arm = samurai.build_ronin() if rec == "samurai_pose" else getattr(samurai, r["builder"])()
        if rec == "samurai_pose":
            P.apply_pose(arm, P.POSES[r["pose"]])
        floor = studio_look()
        bpy.context.view_layer.update()
        return fit_camera(direction=(0.8, -1.0, 0.25), lens=40.0, margin=1.1, exclude={floor})
    if rec == "prop":
        from kit import checkout, props
        {"milk": lambda: props.milk(), "batarang": lambda: props.batarang(),
         "checkout": lambda: checkout.build_checkout()}[r["builder"]]()
        look.store_night(target=(0, 0, 0.5))
        C.sky(C.hex_rgb("#8a93a8"), 1.0)   # light backdrop: dark props (batarang) must read
        flat = r["builder"] == "batarang"
        return fit_camera(direction=(0.0, 0.3, 1.0) if flat else (0.55, 1.0, 0.45), margin=2.2 if flat else 1.25)
    if rec == "fx":
        C.sky(C.hex_rgb("#141824"), 1.0)
        if r["builder"] == "fireball":
            fb = fight.Fireball("fb", "#eaf6ff", "#4aa8ff")
            fb.key(1, (0, 0, 1.0), 0.3)
            post.setup(threshold=0.9, strength=0.55, size=0.35)
            return C.camera("cam_prev", (0.0, 2.4, 1.0), (0, 0, 1.0), lens=50)
        if r["builder"] == "leaves":
            fight.sunset_lights()
            fight.Leaves(n=40, size=(0.065, 0.11)).animate(lambda f: 2.0, 1, 48)
            bpy.context.scene.frame_set(12)
            return C.camera("cam_prev", (0.0, 5.5, 1.3), (0, 0, 1.2), lens=35)
    if rec == "set":
        b = r["builder"]
        if b == "gotham_mart":
            from kit import checkout, sets
            sets.gotham_mart(); checkout.build_checkout()
            look.store_night(target=(0, 0.45, 1.0), facing_deg=180.0)
            s = standin(); s.root.location = (0.0, 0.45, 0.0); s.root.rotation_euler.z = math.pi
            return shots.frame("cam_prev", s, shot="wide", yaw=-125.0, pitch=10.0, at=1)
        if b == "rooftop_sunset":
            fight.rooftop_sunset(); fight.sunset_lights()
            s = standin()
            return shots.frame("cam_prev", s, shot="wide", yaw=176.0, pitch=8.0, at=1)
        if b == "bamboo_stage":
            from kit import stage
            stage.build_stage()
            standin()
            return C.camera("cam_prev", (0, -6.2, 1.0), (0, 0, 1.8), lens=28)
    raise ValueError(f"no recipe for {item['id']}: {r}")


def render(item: dict, force: bool) -> str:
    path = image_path(item["id"])
    if os.path.exists(path) and not force:
        return "kept"
    C.reset_scene()
    cam = build(item)
    scene = bpy.context.scene
    scene.camera = cam
    C.render_settings(width=360, height=640, quality="final", video=False, frame_end=1, filepath=path)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 85
    scene.render.filepath = path
    if scene.frame_current not in (1, 12):
        scene.frame_set(1)
    bpy.ops.render.render(write_still=True)
    item["preview"]["image"] = os.path.relpath(path, ROOT).replace("\\", "/")
    return "rendered"


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default=""); ap.add_argument("--kind", default=""); ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(PREV, exist_ok=True)
    cat = json.load(open(CATALOG, encoding="utf-8"))
    want = set(filter(None, a.ids.split(",")))
    done = failed = 0
    for item in cat["items"]:
        r = item.get("preview") or {}
        if r.get("recipe") not in BLENDER_RECIPES: continue
        if want and item["id"] not in want: continue
        if a.kind and item["kind"] != a.kind: continue
        try:
            res = render(item, a.force)
            if os.path.exists(image_path(item["id"])):
                item["preview"]["image"] = os.path.relpath(image_path(item["id"]), ROOT).replace("\\", "/")
            print(f"[preview] {item['id']}: {res}", flush=True); done += 1
        except Exception as e:  # keep going; report at the end
            failed += 1
            print(f"[preview] {item['id']}: FAILED {e}", flush=True)
            traceback.print_exc()
        json.dump(cat, open(CATALOG, "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
    print(f"[preview] done {done}, failed {failed}", flush=True)


if __name__ == "__main__":
    main()
