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


def _spiral(cx, cy, r, arms, turns, color, width, opacity, phase=0.0):
    import math
    out = []
    for a in range(arms):
        pts = []
        for i in range(0, 61):
            t = i / 60
            ang = phase + a * 2 * math.pi / arms + t * turns * 2 * math.pi
            rr = r * (0.08 + 0.92 * t)
            pts.append(f"{cx + rr * math.cos(ang):.1f},{cy + rr * math.sin(ang):.1f}")
        out.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="{width}" '
                   f'stroke-linecap="round" stroke-opacity="{opacity}"/>')
    return "".join(out)


R = 120  # portal layer radius (units); kit.cutout.Portal scales every layer by 1/(2R)
GRAD = ('<defs><radialGradient id="g"><stop offset="0" stop-color="#e4ff9a"/><stop offset="0.45" stop-color="#8fe83a"/>'
        '<stop offset="1" stop-color="#2f9a1e"/></radialGradient>'
        '<radialGradient id="glow"><stop offset="0.55" stop-color="#b6ff5a" stop-opacity="0.75"/>'
        '<stop offset="1" stop-color="#b6ff5a" stop-opacity="0"/></radialGradient></defs>')
PROPS.update({
    "portal_gun": (40, 96,
                   shape("M6,4 Q6,0 12,0 L28,0 Q34,0 34,4 L34,62 L6,62 Z", "#dfe3e3")
                   + shape("M11,10 L29,10 L29,46 L11,46 Z", "#7df03c", 3)
                   + line("M14,18 L14,38", 3)
                   + shape("M12,62 L28,62 L26,84 L14,84 Z", "#8c9494")
                   + shape("M15,84 L25,84 L24,94 L16,94 Z", "#3b3f3f", 3)),
    "flash": (60, 60,
              shape("M30,0 L37,22 L60,30 L37,38 L30,60 L23,38 L0,30 L23,22 Z", "#d8ff7a", 3)
              + circle(30, 30, 9, "#ffffff", 0.1)),
    "portal_glow": (2 * R + 80, 2 * R + 80, GRAD + f'<circle cx="{R+40}" cy="{R+40}" r="{R+40}" fill="url(#glow)"/>'),
    "portal_disc": (2 * R, 2 * R, GRAD + f'<circle cx="{R}" cy="{R}" r="{R}" fill="url(#g)"/>'
                    + _spiral(R, R, R * 0.98, 5, 0.9, "#e9ffb8", 9, 0.85)),
    "portal_swirl": (2 * R, 2 * R, _spiral(R, R, R * 0.95, 4, -0.7, "#227a14", 7, 0.55, 0.5)),
    "portal_rim": (2 * R + 12, 2 * R + 12,
                   f'<circle cx="{R+6}" cy="{R+6}" r="{R}" fill="none" stroke="#1f6a12" stroke-width="10"/>'
                   f'<circle cx="{R+6}" cy="{R+6}" r="{R-5}" fill="none" stroke="#e8ffb0" stroke-width="7"/>'),
})


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
