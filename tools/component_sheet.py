"""G3 component sheets: every new component on its OWN sheet (owner rule 2026-09-26 — never a composed scene).

    python tools/component_sheet.py <project> <sheet> [<sheet> ...]
      sheets: char:<cast>            turnaround: front, 3/4, side, back, face, silhouette
              poses:<cast>:<module>  every pose in <module>.POSES on that character (3/4 view), e.g. poses:vader:kit.starwars
              set:<module>.<builder> the set empty, per mood (kit.starwars MOODS if the module has them)
              props:saber            lightsaber red / green / off (+ ignite 50 %)
              props:lamp             pull-cord lamp off / on
-> projects/<p>/design/<sheet name>.jpg (panels labelled). Neutral grey studio so dark costumes read.
"""
from __future__ import annotations

import importlib, json, math, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLENDER = "F:/blender/blender.exe"
PW, PH = 400, 600

try:
    import bpy  # noqa: F401
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False


def _blender(project: str, sheets: list[str]) -> None:
    sys.path.insert(0, ROOT)
    import bpy
    from mathutils import Vector
    from kit import cast, fight as FT, look as L, post, qchar as Q
    from studio import core as C

    out = os.path.join(ROOT, "projects", project, "design", "panels")
    os.makedirs(out, exist_ok=True)
    index = {}

    def studio(target=(0, 0, 0.9)):
        L.store_night(target=target)
        C.sky(C.hex_rgb("#9aa3b5"), 1.0)                    # light neutral backdrop: black costumes must read
        L.floor(size=12, hex_="#6c7486")

    def shot(name, cam_loc, cam_tgt, lens=50.0, w=PW, h=PH):
        sc = bpy.context.scene
        sc.camera = C.camera(f"cam_{name}", cam_loc, cam_tgt, lens=lens)
        path = os.path.join(out, f"{name}.png")
        C.render_settings(width=w, height=h, quality="final", video=False, frame_end=1, filepath=path)
        sc.render.resolution_percentage = 100
        sc.frame_set(1)
        bpy.ops.render.render(write_still=True)
        return path

    def silhouette():
        for m in bpy.data.materials:
            if m.use_nodes and not m.name.startswith("floor"):
                nt = m.node_tree
                for n in list(nt.nodes):
                    nt.nodes.remove(n)
                o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission")
                e.inputs["Color"].default_value = (0, 0, 0, 1); nt.links.new(e.outputs[0], o.inputs[0])
        C.sky((1, 1, 1), 1.0)
        f = bpy.data.objects.get("floor")
        if f:
            f.hide_render = True

    for sheet in sheets:
        kind, _, arg = sheet.partition(":")
        panels = []
        if kind == "char":
            views = [("front", (0, 4.6, 1.0)), ("3/4", (2.64, 3.77, 1.0)), ("side", (4.6, 0, 1.0)), ("back", (0, -4.6, 1.0))]
            C.reset_scene(); studio()
            qc = cast.CAST[arg](); Q.set_action(qc, "Idle", 1)
            for v, loc in views:
                panels.append((v, shot(f"{arg}_{v.replace('/', '')}", loc, (0, 0, 0.88), 50)))
            panels.append(("face", shot(f"{arg}_face", (0.55, 2.3, 1.45), (0, 0, 1.33), 50)))
            silhouette()
            panels.append(("silhouette", shot(f"{arg}_sil", (0, 4.6, 1.0), (0, 0, 0.88), 50)))
        elif kind == "poses":
            who, _, mod = arg.partition(":")
            m = importlib.import_module(mod)
            names = getattr(m, "POSE_CAST", {}).get(who, list(m.POSES))
            for pname in names:
                pose = m.POSES[pname]
                C.reset_scene(); studio()
                qc = cast.CAST[who]()
                FT.prepare(qc); FT.key_pose(qc, 1, pose)
                if qc.face is not None and pname in getattr(m, "POSE_FACE", {}):
                    from kit import face as F
                    F.set_expression(qc.face, m.POSE_FACE[pname])
                panels.append((pname, shot(f"{who}_pose_{pname}", (2.2, 3.9, 1.1), (0, 0, 0.95), 45)))
        elif kind == "set":
            mod, _, builder = arg.rpartition(".")
            m = importlib.import_module(mod)
            for mood in getattr(m, "MOODS", {"lit": None}):
                C.reset_scene()
                lights = getattr(m, builder)()
                if hasattr(m, "key_mood"):
                    m.key_mood(lights, 1, mood)
                if mood == "lamp" and hasattr(m, "PullLamp"):
                    m.PullLamp(loc=(0.0, 0.9, 3.3)).key_on(1, True)
                post.setup(threshold=0.9, strength=0.6, size=0.4)
                panels.append((f"{mood} — camera view", shot(f"set_{mood}", (0, -2.6, 1.5), (0, 0.9, 1.3), 28)))
            C.reset_scene(); lights = getattr(m, builder)(); post.setup(threshold=0.9, strength=0.6, size=0.4)
            panels.append(("lit — wide, from above", shot("set_wide", (1.6, -4.5, 3.0), (0, 3.0, 1.0), 20)))
        elif kind == "props" and arg == "saber":
            from kit import starwars as SW
            for label, colour, on in (("red (Vader)", "#ff2a2a", 1.0), ("green (Luke)", "#39ff5a", 1.0),
                                      ("igniting 50 %", "#39ff5a", 0.5), ("off (hilt)", "#39ff5a", 0.0)):
                C.reset_scene(); C.sky(C.hex_rgb("#3a4150"), 1.0); L.store_night(target=(0, 0, 0.6)); C.sky(C.hex_rgb("#3a4150"), 1.0)
                s = SW.Lightsaber("sab", colour); s.root.rotation_euler = (0, math.radians(-20), 0); s.key(1, on)
                post.setup(threshold=0.9, strength=0.6, size=0.4)
                panels.append((label, shot(f"saber_{label.split()[0]}", (0, -2.4, 0.6), (0, 0, 0.55), 40)))
            C.reset_scene(); C.sky(C.hex_rgb("#9aa3b5"), 1.0); L.store_night(target=(0, 0, 0.0)); C.sky(C.hex_rgb("#9aa3b5"), 1.0)
            s = SW.Lightsaber("sab", "#39ff5a"); s.key(1, 0.0); s.root.rotation_euler = (math.radians(90), 0, 0)
            panels.append(("hilt close-up", shot("saber_hilt", (0.0, -0.9, 0.25), (0, 0.0, 0.0), 50)))
        elif kind == "props" and arg == "lamp":
            from kit import starwars as SW
            for label, on in (("off", False), ("on", True)):
                C.reset_scene(); C.sky(C.hex_rgb("#2e3440"), 1.0)
                C.cube("ceiling", size=1, loc=(0, 0, 3.35), scale=(3, 3, 0.1), mat=L.toon2("ceil", "#5b6272", rim=0.0))
                C.cube("backdrop", size=1, loc=(0, 1.2, 1.8), scale=(3, 0.1, 3.4), mat=L.toon2("bd", "#6a7282", rim=0.0))
                sun = C.sun("k", energy=1.2, rot=(50, 0, 20))
                lamp = SW.PullLamp(loc=(0, 0, 3.3)); lamp.key_on(1, on)
                post.setup(threshold=0.9, strength=0.6, size=0.4)
                panels.append((label, shot(f"lamp_{label}", (0.4, -2.2, 2.2), (0, 0, 2.2), 35)))
        index[sheet] = panels
    json.dump(index, open(os.path.join(out, "index.json"), "w"), indent=1)


def _compose(project: str) -> list[str]:
    from PIL import Image, ImageDraw, ImageFont
    d = os.path.join(ROOT, "projects", project, "design")
    index = json.load(open(os.path.join(d, "panels", "index.json")))
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 20)
    outs = []
    for sheet, panels in index.items():
        ims = [Image.open(p).convert("RGB") for _, p in panels]
        cols = min(len(ims), 5 if len(ims) > 6 else len(ims))
        rows = math.ceil(len(ims) / cols)
        w, h = max(i.width for i in ims), max(i.height for i in ims)
        S = Image.new("RGB", (cols * w + (cols + 1) * 10, rows * (h + 34) + 10 + 44), (24, 26, 32))
        dr = ImageDraw.Draw(S)
        dr.text((10, 10), sheet, font=font, fill=(255, 214, 90))
        for i, ((label, _), im) in enumerate(zip(panels, ims)):
            x, y = 10 + (i % cols) * (w + 10), 44 + (i // cols) * (h + 34)
            S.paste(im, (x, y + 30))
            dr.text((x, y + 4), label, font=font, fill=(230, 232, 238))
        name = sheet.replace(":", "_").replace(".", "_")
        path = os.path.join(d, f"{name}.jpg")
        S.save(path, quality=88)
        outs.append(path)
    return outs


def main() -> None:
    if IN_BLENDER:
        argv = sys.argv[sys.argv.index("--") + 1:]
        _blender(argv[0], argv[1:])
        return
    project, sheets = sys.argv[1], sys.argv[2:]
    r = subprocess.run([BLENDER, "-b", "--python", os.path.abspath(__file__), "--", project, *sheets])
    if r.returncode:
        sys.exit(r.returncode)
    for p in _compose(project):
        print(f"[sheet] {p}")


if __name__ == "__main__":
    main()
