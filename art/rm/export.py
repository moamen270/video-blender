"""Export cut-out parts to PNGs + rig.json for kit/cutout.py (Blender).

python art/rm/export.py            -> assets/cutout/<char>/<part>.png, assets/cutout/<char>/rig.json

Each part is rasterised alone on the character canvas at ZOOM px per character unit, then cropped
to its alpha bounding box. rig.json keeps the box in character units so Blender can place the
plane exactly where the part was drawn.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import resvg_py
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from chars import CHARS, CX, GROUND  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "cutout"
ZOOM = 4          # px per character unit (Rick's head ~ 1000 px wide -> sharp in close-ups)
CANVAS = (600, 1000)
PAD = 2           # px


def render_part(svg_inner: str) -> Image.Image:
    w, h = CANVAS
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
           f"{svg_inner}</svg>")
    png = bytes(resvg_py.svg_to_bytes(svg_string=svg, zoom=ZOOM))
    return Image.open(io.BytesIO(png)).convert("RGBA")


def export(name: str) -> Path:
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    rig = {"name": name, "units_per_px": 1.0 / ZOOM, "ground": GROUND, "cx": CX, "parts": []}
    for p in CHARS[name]():
        img = render_part(p.svg)
        box = img.getchannel("A").getbbox()
        if box is None:
            raise SystemExit(f"{name}/{p.name}: empty part")
        x0, y0, x1, y1 = box
        x0, y0 = max(0, x0 - PAD), max(0, y0 - PAD)
        x1, y1 = min(img.width, x1 + PAD), min(img.height, y1 + PAD)
        fname = p.name.replace(":", "__") + ".png"
        img.crop((x0, y0, x1, y1)).save(d / fname, optimize=True)
        rig["parts"].append({
            "name": p.name, "png": fname,
            "box": [x0 / ZOOM, y0 / ZOOM, x1 / ZOOM, y1 / ZOOM],   # character units
            "pivot": list(p.pivot), "z": p.z, "parent": p.parent, "tags": p.tags,
        })
    (d / "rig.json").write_text(json.dumps(rig, indent=1))
    return d


if __name__ == "__main__":
    for n in (sys.argv[1:] or list(CHARS)):
        print(export(n), len(json.loads((OUT / n / "rig.json").read_text())["parts"]), "parts")
