"""Hand props, same style/scale as the characters.

python art/rm/props.py -> assets/cutout/props/<name>.png + props.json (size in character units)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import resvg_py
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from chars import circle, line, shape  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "cutout" / "props"
ZOOM = 4

# name -> (width, height, svg drawn in a w x h box)
PROPS = {
    "remote": (44, 84,
               shape("M8,14 Q8,6 16,6 L28,6 Q36,6 36,14 L36,76 Q36,80 32,80 L12,80 Q8,80 8,76 Z", "#5d6670")
               + circle(22, 26, 9, "#e33b3b", 3)
               + line("M15,48 L29,48 M15,58 L29,58", 3)
               + line("M30,6 L36,-4", 3) + circle(36, -4, 3, "#9bd35a", 2)),
}


def export() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {}
    for name, (w, h, svg) in PROPS.items():
        pad = 12
        doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w+2*pad}" height="{h+2*pad}" '
               f'viewBox="{-pad} {-pad} {w+2*pad} {h+2*pad}">{svg}</svg>')
        img = Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=doc, zoom=ZOOM)))).convert("RGBA")
        img.save(OUT / f"{name}.png", optimize=True)
        meta[name] = {"png": f"{name}.png", "size": [w + 2 * pad, h + 2 * pad]}
    (OUT / "props.json").write_text(json.dumps(meta, indent=1))
    print(OUT, list(meta))


if __name__ == "__main__":
    export()
