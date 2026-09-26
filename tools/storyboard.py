"""Pitch PoC: storyboard stills from a JSON spec (docs/PIPELINE.md phase 1, gate G1).

    python tools/storyboard.py <project> [--only A1,B2]     # renders projects/<p>/poc/<id>.jpg + poc/board.jpg

Spec: projects/<p>/poc/storyboard.json
{
  "set": "corridor",                       # corridor | rooftop | none   (+ "set_opts": {"shaft": [x, y]}, also per panel)
  "cast": {"vader": "vader_standin", "luke": "luke_standin"},   # name -> builder (STANDINS below or kit.cast.CAST)
  "rows": [["A1", "A2"], ["B1", "B2"]],    # board layout (row = pitch)
  "panels": [{
    "id": "A1", "title": "A — hook", "caption": "what happens", "overlay": "HOOK TEXT on the image",
    "light": "normal | dark",
    "who": [{"name": "vader", "at": [x, y], "face": deg_world_or_name, "z": 0,
             "pose": "STANCE" | {"base": "STANCE", "hand_r": [x, y, z], ...} | null,
             "action": ["Jump", 12], "hide": ["Fist.R"], "tilt": [x_deg, y_deg]}],
    "sabers": [{"who": "vader", "hand": "R" | "from": [x, y, z], "dir": [x, y, z], "color": "#ff2a2a", "length": 0.95}],
    "extras": [{"type": "sphere|cube|cone|cylinder|text|hand", "loc": [x, y, z], "anchor": "luke:Head",
                "rot": [deg], "scale": [..], "r": 0.1, "color": "#hex", "emit": 0, "body": "TEXT", "size": 0.3}],
    "camera": {"frame": ["vader", "luke"], "shot": "two_shot", "yaw": 0, "pitch": 5}
              | {"loc": [x, y, z], "target": [x, y, z], "lens": 35},
    "post": {"split": {"angle": 35, "shift": [40, 60]}}      # image-space gags applied after the render
  }]
}
Stand-ins are PoC-only (not library items): they only have to make the joke readable. Poses are kit.fight poses in
the character's native space (front = -y, up = +z, ~3.15 units tall); after loading, a character with root z = 0 faces world +y. The world "face" angle follows the Ryu vs Ken
convention (root z = face - 90). Output 540x960 JPEG per panel; the board adds titles/captions (PIL).
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLENDER = "F:/blender/blender.exe"
W, H = 540, 960

try:
    import bpy  # noqa: F401
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False


# ============================================================ Blender side
def _blender_main(project: str, only: set[str]) -> None:
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import bpy
    from mathutils import Vector
    from kit import cast, fight, look, post, qchar as Q, shots
    from studio import core as C

    pdir = os.path.join(ROOT, "projects", project, "poc")
    spec = json.load(open(os.path.join(pdir, "storyboard.json"), encoding="utf-8"))

    def mat(name, hex_, emit=0.0):
        return fight.emit_mat(name, hex_, strength=emit) if emit else look.toon2(name, hex_)

    def bone_rest_world(qc, bone):
        return qc.arm.matrix_world @ qc.arm.data.bones[bone].head_local

    def vader_standin():
        qc = cast.build_batman()
        black = look.toon2("vader_black", "#15161a")
        for o in [qc.body, *qc.parts.values()]:
            if o.type == "MESH":
                for s in o.material_slots:
                    if s.material and "outline" not in s.material.name.lower():
                        s.material = black
        for p in ("ear.L", "ear.R", "emblem", "bat"):
            if p in qc.parts:
                qc.parts[p].hide_render = True
        if qc.face is not None:                       # Vader has a mask, not eyes
            for o in bpy.data.objects:
                if o.name.startswith("batman") and ("eye" in o.name or "brow" in o.name or "mouth" in o.name):
                    o.hide_render = True
        # the chibi head is big: place the helmet from the head's measured bounds (body verts above the neck)
        neck = bone_rest_world(qc, "Head")
        pts = [qc.body.matrix_world @ v.co for v in qc.body.data.vertices]
        hv = [p for p in pts if p.z > neck.z + 0.04]
        lo = Vector((min(p.x for p in hv), min(p.y for p in hv), min(p.z for p in hv)))
        hi = Vector((max(p.x for p in hv), max(p.y for p in hv), max(p.z for p in hv)))
        c, half = (lo + hi) / 2, (hi - lo) / 2
        chest = qc.parts["emblem"].matrix_world.to_translation()       # Batman's emblem sits on the chest surface
        grey = look.toon2("vader_grey", "#6a6e78")
        dome = C.sphere("vader_dome", r=1.0, loc=c + Vector((0, -0.02, 0.03)), scale=(half.x * 1.1, half.y * 1.12, half.z * 1.02), mat=black)
        flare = C.cone("vader_flare", r1=half.x * 1.3, r2=half.x * 1.05, depth=half.z * 0.7,
                       loc=Vector((c.x, c.y - 0.03, lo.z + half.z * 0.3)), mat=black)
        mask = C.cone("vader_mask", r1=half.x * 0.42, r2=half.x * 0.12, depth=0.08,
                      loc=Vector((c.x, hi.y + 0.03, c.z - half.z * 0.35)), rot=(-90, 0, 0), mat=grey)
        eyes = [C.sphere(f"vader_eye{s}", r=half.x * 0.2, loc=Vector((c.x + half.x * 0.38 * s, hi.y + 0.02, c.z + half.z * 0.1)),
                         scale=(1.2, 0.5, 0.9), mat=mat("vader_eyeglass", "#2a2f3a")) for s in (-1, 1)]
        box = C.cube("vader_chestbox", size=1.0, loc=chest + Vector((0, 0.03, 0.02)), scale=(0.16, 0.04, 0.11), mat=grey)
        lights = [C.cube(f"vader_light{i}", size=0.03, loc=chest + Vector((-0.045 + 0.045 * i, 0.055, 0.03)),
                         mat=mat(f"vader_l{i}", ["#ff3030", "#30ff60", "#3080ff"][i], 8.0)) for i in range(3)]
        for i, o in enumerate([dome, flare, mask, *eyes]):
            Q.attach_part(qc, o, "Head", f"helmet{i}")
        for i, o in enumerate([box, *lights]):
            Q.attach_part(qc, o, "Torso", f"chest{i}")
        return qc

    def luke_standin():
        return cast._fighter("luke", gi="#1d1d22", lapel_hex="#2c2c33", belt="#111114", hair_file="Casual_Male.blend",
                             hair="#d8b060", hair_lift=0.12, headband=None, gloves="#15151a",
                             skin=cast.SKIN["ken"], expression="stern")

    standins = {"vader_standin": vader_standin, "luke_standin": luke_standin}

    def build_set(kind, opts, light):
        if kind == "corridor":
            wall, floor_c, strip = ("#2a3140", "#232833", "#9fd8ff") if light == "dark" else ("#6f7a8e", "#4a5263", "#d8f2ff")
            look.floor(size=30, hex_=floor_c)
            wm = look.toon2("wall", wall)
            for x in (-3.2, 3.2):
                C.cube(f"wall{x}", size=1, loc=(x, 2, 3), scale=(0.2, 16, 6), mat=wm)
                for k in range(6):
                    C.cube(f"strip{x}{k}", size=1, loc=(x * 0.97, -5 + 2.4 * k, 2.6), scale=(0.05, 1.2, 0.08),
                           mat=mat("strip", strip, 3.0 if light != "dark" else 1.2))
            C.cube("backwall", size=1, loc=(0, 9, 3), scale=(7, 0.2, 6), mat=wm)
            for k in range(5):
                C.cube(f"slot{k}", size=1, loc=(-2 + k, 8.85, 3.5), scale=(0.25, 0.05, 2.2),
                       mat=mat("slot", strip, 2.5 if light != "dark" else 1.0))
            if opts.get("shaft"):
                sx, sy = opts["shaft"]
                C.cylinder("shaft", r=1.1, depth=0.02, loc=(sx, sy, 0.012), mat=mat("shaft_dark", "#0c0f16"))
                C.torus("shaft_rim", major=1.12, minor=0.04, loc=(sx, sy, 0.02), mat=mat("rim", "#ffb040", 3.0))
            C.sky(C.hex_rgb("#1a2030" if light == "dark" else "#56627a"), 1.0)
        elif kind == "rooftop":
            fight.rooftop_sunset()
        if light == "dark":
            C.sky(C.hex_rgb("#0e1422"), 1.0)
            s = C.sun("moon", energy=0.25, rot=(55, 0, 30)); s.data.color = C.hex_rgb("#6a8cff")
        elif kind == "rooftop":
            fight.sunset_lights()
        else:
            look.store_night(target=(0, 0, 1.0))
            C.sky(C.hex_rgb("#56627a"), 1.0)

    def pose_of(p):
        if p is None:
            return None
        if isinstance(p, str):
            return getattr(fight, p)
        base = getattr(fight, p.get("base", "STANCE"))
        kw = {k: (tuple(v) if isinstance(v, list) else v) for k, v in p.items() if k != "base"}
        from dataclasses import replace
        return replace(base, **kw)

    def resolve(anchor, chars):
        name, _, bone = anchor.partition(":")
        qc = chars[name]
        pb = qc.arm.pose.bones[bone or "Head"]
        return qc.arm.matrix_world @ pb.head

    def add_extra(e, chars, i):
        loc = Vector(e.get("loc", (0, 0, 0)))
        if e.get("anchor"):
            loc = resolve(e["anchor"], chars) + loc
        m = mat(f"x{i}", e.get("color", "#cccccc"), e.get("emit", 0))
        t, rot, sc = e["type"], tuple(e.get("rot", (0, 0, 0))), tuple(e.get("scale", (1, 1, 1)))
        if t == "sphere":
            C.sphere(f"x{i}", r=e.get("r", 0.1), loc=loc, rot=rot, scale=sc, mat=m)
        elif t == "cube":
            C.cube(f"x{i}", size=e.get("r", 0.1) * 2, loc=loc, rot=rot, scale=sc, mat=m)
        elif t == "cone":
            C.cone(f"x{i}", r1=e.get("r", 0.1), r2=e.get("r2", 0.0), depth=e.get("depth", 0.3), loc=loc, rot=rot, mat=m)
        elif t == "cylinder":
            C.cylinder(f"x{i}", r=e.get("r", 0.05), depth=e.get("depth", 0.3), loc=loc, rot=rot, scale=sc, mat=m)
        elif t == "text":
            o = C.text(f"x{i}", e["body"], size=e.get("size", 0.3), loc=loc, rot=rot, mat=m)
            o.data.align_x = "CENTER"
        elif t == "hand":                                    # a severed hand: palm + 4 fingers + thumb
            skin = mat(f"x{i}", e.get("color", cast.SKIN["ken"]))
            C.sphere(f"x{i}palm", r=0.05, loc=loc + Vector((0, 0, 0.07)), scale=(1.1, 0.7, 1.0), mat=skin)
            for k in range(4):
                a = math.radians(-50 + k * 33)
                C.cylinder(f"x{i}f{k}", r=0.012, depth=0.09, loc=loc + Vector((0.05 * math.sin(a), 0.03 * math.cos(a), 0.03)),
                           rot=(math.degrees(0.5 * math.cos(a)), math.degrees(-0.6 * math.sin(a)), 0), mat=skin)
        else:
            raise ValueError(f"unknown extra type {t}")

    def saber(s, chars, i):
        bpy.context.view_layer.update()
        if "from" in s:                                      # a free saber (held by an extra, or dropped)
            start = Vector(s["from"])
        else:
            qc = chars[s["who"]]
            start = qc.arm.matrix_world @ qc.arm.pose.bones[f"Fist.{s.get('hand', 'R')}"].tail
        d = Vector(s.get("dir", (0, 0, 1))).normalized()
        L = s.get("length", 0.95)
        q = d.to_track_quat("Z", "Y").to_euler()
        rot = tuple(math.degrees(a) for a in q)
        C.cylinder(f"hilt{i}", r=0.022, depth=0.24, loc=start + d * 0.02, rot=rot, mat=mat("hilt", "#8a8f99"))
        col = s.get("color", "#ff2a2a")
        C.cylinder(f"core{i}", r=0.013, depth=L, loc=start + d * (0.14 + L / 2), rot=rot, mat=mat(f"core{i}", "#ffffff", 8))
        C.cylinder(f"glow{i}", r=0.03, depth=L + 0.02, loc=start + d * (0.14 + L / 2), rot=rot,
                   mat=fight.emit_mat(f"glow{i}", col, strength=6.0, alpha=0.55))

    for panel in spec["panels"]:
        if only and panel["id"] not in only:
            continue
        C.reset_scene()
        light = panel.get("light", "normal")
        build_set(spec.get("set", "corridor"), {**spec.get("set_opts", {}), **panel.get("set_opts", {})}, light)
        chars = {}
        for w in panel.get("who", []):
            b = spec["cast"][w["name"]]
            qc = standins[b]() if b in standins else cast.CAST[b]()
            chars[w["name"]] = qc
        pos = {w["name"]: Vector((*w["at"], w.get("z", 0.0))) for w in panel.get("who", [])}
        for w in panel.get("who", []):
            qc = chars[w["name"]]
            face = w.get("face", 0.0)
            if isinstance(face, str):
                d = pos[face] - pos[w["name"]]
                face = math.degrees(math.atan2(d.y, d.x))
            qc.root.location = pos[w["name"]]
            tx, ty = w.get("tilt", (0, 0))
            qc.root.rotation_euler = (math.radians(tx), math.radians(ty), math.radians(face - 90))
            bpy.context.view_layer.update()
            if w.get("action"):                             # a Quaternius clip at a frame (no IK over it)
                Q.set_action(qc, w["action"][0])
            else:
                fight.prepare(qc)
            p = pose_of(w.get("pose", "STANCE" if not w.get("action") else None))
            if p is not None:
                fight.key_pose(qc, 1, p)
            for bone in w.get("hide", []):
                qc.arm.pose.bones[bone].scale = (0.001, 0.001, 0.001)
        frame = 1
        acts = [w["action"][1] for w in panel.get("who", []) if w.get("action")]
        if acts:
            frame = acts[0]
        bpy.context.scene.frame_set(frame)
        for i, s in enumerate(panel.get("sabers", [])):
            saber(s, chars, i)
        for i, e in enumerate(panel.get("extras", [])):
            add_extra(e, chars, i)
        cam_spec = panel.get("camera", {})
        if "frame" in cam_spec:
            tgt = [chars[n] for n in cam_spec["frame"]]
            cam = shots.frame("cam", tgt if len(tgt) > 1 else tgt[0], shot=cam_spec.get("shot", "two_shot"),
                              yaw=cam_spec.get("yaw", 0.0), pitch=cam_spec.get("pitch", 5.0), at=frame,
                              lens=cam_spec.get("lens"))
        else:
            cam = C.camera("cam", tuple(cam_spec["loc"]), tuple(cam_spec["target"]), lens=cam_spec.get("lens", 35))
        sc = bpy.context.scene
        sc.camera = cam
        post.setup(threshold=0.9, strength=0.6, size=0.4)
        path = os.path.join(pdir, f"{panel['id']}.jpg")
        C.render_settings(width=W, height=H, quality="final", video=False, frame_end=max(frame, 1), filepath=path)
        sc.render.resolution_percentage = 100
        sc.render.image_settings.file_format = "JPEG"
        sc.render.image_settings.quality = 88
        sc.frame_set(frame)
        bpy.ops.render.render(write_still=True)
        print(f"[storyboard] {panel['id']} -> {path}", flush=True)


# ============================================================ driver side (plain Python + PIL)
def _font(size: int, bold: bool = True):
    from PIL import ImageFont
    for f in (("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"), "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def _post(img, p):
    """Image-space gags: 'split' = the frame is cut along a diagonal and the upper part slides off."""
    from PIL import Image, ImageDraw
    if "split" in p:
        ang = math.radians(p["split"].get("angle", 30)); dx, dy = p["split"].get("shift", (40, 60))
        w, h = img.size
        mask = Image.new("L", img.size, 0)
        cy = h * p["split"].get("at", 0.5); k = math.tan(ang)
        ImageDraw.Draw(mask).polygon([(0, 0), (w, 0), (w, cy - k * w / 2), (0, cy + k * w / 2)], fill=255)
        out = img.copy()
        top = Image.new("RGB", img.size, (0, 0, 0)); top.paste(img, (0, 0), mask)
        out.paste(img.crop((0, 0, w, h)), (0, 0))
        out.paste(Image.new("RGB", img.size, (0, 0, 0)), (0, 0), mask)   # gap behind the moving part
        m2 = Image.new("L", img.size, 0); m2.paste(mask, (dx, -dy))
        t2 = Image.new("RGB", img.size); t2.paste(top, (dx, -dy))
        out.paste(t2, (0, 0), m2)
        ImageDraw.Draw(out).line([(0, cy + k * w / 2), (w, cy - k * w / 2)], fill=(255, 255, 255), width=3)
        img = out
    return img


def _overlay(img, text):
    from PIL import ImageDraw
    d = ImageDraw.Draw(img); f = _font(34)
    lines = _wrap(d, text, f, W - 60)
    y = 70
    for ln in lines:
        tw = d.textlength(ln, font=f)
        d.text(((W - tw) / 2, y), ln, font=f, fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
        y += 42
    return img


def board(project: str) -> str:
    from PIL import Image, ImageDraw
    pdir = os.path.join(ROOT, "projects", project, "poc")
    spec = json.load(open(os.path.join(pdir, "storyboard.json"), encoding="utf-8"))
    panels = {p["id"]: p for p in spec["panels"]}
    rows = spec.get("rows") or [[p["id"] for p in spec["panels"]]]
    cols = max(len(r) for r in rows)
    tw, cap_h, head_h, pad = W // 2, 150, 50, 16
    th = H // 2
    sheet = Image.new("RGB", (pad + cols * (tw + pad), pad + len(rows) * (head_h + th + cap_h + pad)), (24, 26, 32))
    d = ImageDraw.Draw(sheet)
    for r, row in enumerate(rows):
        y0 = pad + r * (head_h + th + cap_h + pad)
        for c, pid in enumerate(row):
            p = panels[pid]; x0 = pad + c * (tw + pad)
            img = Image.open(os.path.join(pdir, f"{pid}.jpg")).convert("RGB")
            img = _post(img, p.get("post", {}))
            if p.get("overlay"):
                img = _overlay(img, p["overlay"])
            img.save(os.path.join(pdir, f"{pid}_final.jpg"), quality=90)
            d.text((x0, y0 + 12), p.get("title", pid), font=_font(17), fill=(255, 214, 90))
            sheet.paste(img.resize((tw, th)), (x0, y0 + head_h))
            yy = y0 + head_h + th + 8
            for ln in _wrap(d, p.get("caption", ""), _font(16, False), tw)[:7]:
                d.text((x0, yy), ln, font=_font(16, False), fill=(225, 228, 235)); yy += 20
    out = os.path.join(pdir, "board.jpg")
    sheet.save(out, quality=90)
    return out


def main() -> None:
    if IN_BLENDER:
        argv = sys.argv[sys.argv.index("--") + 1:]
        _blender_main(argv[0], set(filter(None, (argv[1] if len(argv) > 1 else "").split(","))))
        return
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("--only", default=""); ap.add_argument("--board-only", action="store_true")
    a = ap.parse_args()
    if not a.board_only:
        r = subprocess.run([BLENDER, "-b", "--python", os.path.abspath(__file__), "--", a.project, a.only])
        if r.returncode:
            sys.exit(r.returncode)
    print(f"[storyboard] board: {board(a.project)}")


if __name__ == "__main__":
    main()
