"""Rick's garage backdrop (flat, same line style and scale as the characters).

python art/rm/garage.py  -> assets/cutout/garage/garage.png + garage.json

Canvas units match character units (1 unit = kit.cutout.S metres). Feet stand on y = GROUND_Y.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import resvg_py
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from chars import INK, circle, line, shape  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "cutout" / "garage"
W, H = 1600, 1400
GROUND_Y = 1200      # where the characters' feet are (world z = 0)
WALL_Y = 1010        # wall meets floor (behind the characters)
CX = 800             # world x = 0
ZOOM = 2


def rect(x0, y0, x1, y1, fill, w=4.0):
    return shape(f"M{x0},{y0} L{x1},{y0} L{x1},{y1} L{x0},{y1} Z", fill, w)


def garage_svg() -> str:
    g = []
    # wall + floor
    g.append(f'<rect x="0" y="0" width="{W}" height="{WALL_Y}" fill="#93a39d"/>')
    for x in range(0, W, 200):                                   # faint wall panels
        g.append(f'<path d="M{x},0 L{x},{WALL_Y}" stroke="#86958f" stroke-width="3"/>')
    g.append(f'<rect x="0" y="{WALL_Y}" width="{W}" height="{H-WALL_Y}" fill="#8c877d"/>')
    g.append(rect(-10, WALL_Y - 22, W + 10, WALL_Y, "#6f7c77"))    # baseboard
    g.append(line(f"M-10,{WALL_Y} L{W+10},{WALL_Y}"))
    g.append(line("M300,1120 Q340,1150 330,1190 M1180,1260 Q1230,1250 1260,1290", 3))   # floor cracks
    g.append('<ellipse cx="1040" cy="1320" rx="120" ry="26" fill="#7c776d"/>')        # oil stain
    # garage door (left)
    g.append(rect(40, 330, 560, WALL_Y - 22, "#c9c4b3"))
    for y in range(330 + 162, WALL_Y - 22, 162):
        g.append(line(f"M40,{y} L560,{y}", 4))
    for y in range(330 + 40, WALL_Y - 40, 162):
        g.append(line(f"M70,{y} L530,{y}", 2.5))
    g.append(rect(270, 800, 330, 816, "#7a7a7a", 3))            # handle
    g.append(rect(28, 318, 572, 330, "#6f7c77", 3))             # header
    # shelf with boxes (upper left of the bench)
    g.append(rect(640, 300, 860, 316, "#8a5a33"))
    g.append(rect(652, 230, 730, 300, "#c49a5c"))
    g.append(rect(740, 250, 800, 300, "#b98b4f"))
    g.append(circle(830, 286, 14, "#6fd24a", 3))
    # pegboard + hanging tools
    g.append(rect(900, 400, 1500, 700, "#c9a36b"))
    for x in range(930, 1500, 40):
        for y in range(430, 700, 40):
            g.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="#8f6d3f"/>')
    g.append(shape("M960,450 L980,450 L978,600 L962,600 Z", "#b7bcc0"))               # screwdriver shaft
    g.append(shape("M956,600 L984,600 L982,650 L958,650 Z", "#d23b3b"))               # handle
    g.append(shape("M1040,450 L1110,450 L1110,480 L1085,480 L1085,640 L1065,640 L1065,480 L1040,480 Z", "#9aa1a6"))  # hammer
    g.append(shape("M1180,440 Q1215,432 1222,470 L1206,476 L1206,640 L1190,640 L1190,476 L1174,470 Q1170,450 1180,440 Z", "#b7bcc0"))  # wrench
    g.append(shape("M1290,450 L1440,450 L1440,560 L1290,560 Z", "#f2f2ee"))           # blueprint
    g.append(line("M1305,475 L1420,475 M1305,500 L1390,500 M1305,525 L1410,525", 3))
    g.append(circle(1400, 520, 22, "none", 3))
    # workbench (right)
    g.append(rect(880, 760, 1520, 796, "#8a5a33"))
    g.append(rect(900, 796, 930, WALL_Y + 60, "#6e4526"))
    g.append(rect(1470, 796, 1500, WALL_Y + 60, "#6e4526"))
    g.append(rect(1180, 796, 1440, 900, "#7a4e2b"))
    g.append(rect(1200, 816, 1420, 852, "#8a5a33", 3))
    g.append(rect(1290, 830, 1330, 838, "#3a2a1c", 2))
    # stuff on the bench
    g.append(rect(930, 700, 1060, 760, "#c93c3c"))                                     # toolbox
    g.append(line("M960,700 Q995,672 1030,700", 5))
    g.append(shape("M1110,640 L1150,640 L1150,690 L1185,752 Q1188,762 1176,762 L1084,762 Q1072,762 1075,752 L1110,690 Z", "#e8f2f4"))  # flask
    g.append(shape("M1093,722 L1167,722 L1183,752 Q1186,760 1176,760 L1084,760 Q1074,760 1077,752 Z", "#7be04e", 0.1))
    g.append(line("M1110,640 L1150,640 L1150,690 L1185,752 Q1188,762 1176,762 L1084,762 Q1072,762 1075,752 L1110,690 Z"))
    g.append(circle(1130, 740, 6, "#b8f59a", 0.1))
    g.append(shape("M1260,760 L1270,700 L1330,700 L1340,760 Z", "#3e5b7a"))             # device
    g.append(circle(1300, 728, 12, "#ffcf3a", 3))
    g.append(shape("M1400,760 L1420,640 L1432,640 L1452,760 Z", "#7a7a7a"))             # lamp arm
    g.append(shape("M1390,640 L1470,640 L1450,610 L1410,610 Z", "#4d4d4d"))
    # ceiling lamp
    g.append(line("M780,0 L780,150", 3))
    g.append(shape("M720,190 L840,190 L805,150 L755,150 Z", "#4d4d4d"))
    g.append(circle(780, 198, 14, "#fff6c9", 3))
    return "".join(g)


def export() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{garage_svg()}</svg>'
    img = Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg, zoom=ZOOM)))).convert("RGBA")
    img.save(OUT / "garage.png", optimize=True)
    (OUT / "garage.json").write_text(json.dumps({"png": "garage.png", "size": [W, H], "ground_y": GROUND_Y,
                                                 "cx": CX, "wall_y": WALL_Y}, indent=1))
    return OUT / "garage.png"


if __name__ == "__main__":
    print(export(), INK)
