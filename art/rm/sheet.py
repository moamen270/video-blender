"""Preview sheet: assemble cut-out parts to SVG and rasterise to PNG (no Blender).

python art/rm/sheet.py [out.png] [path/to/chars.py]
"""
from __future__ import annotations

import sys
from pathlib import Path

import resvg_py

import importlib.util

_src = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "chars.py"
_spec = importlib.util.spec_from_file_location("chars", _src)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["chars"] = _mod
_spec.loader.exec_module(_mod)
CHARS, Part = _mod.CHARS, _mod.Part


def assemble(parts: list[Part], mouth: str = "X", hands: str = "open", extra: set[str] | None = None) -> str:
    keep = []
    for p in parts:
        if ":" in p.name:
            slot, key = p.name.split(":")
            want = mouth if slot == "mouth" else hands
            if key != want:
                continue
        if p.name == "drool" and extra is not None and "drool" not in extra:
            continue
        keep.append(p)
    keep.sort(key=lambda p: p.z)
    return "".join(f'<g id="{p.name}">{p.svg}</g>' for p in keep)


def sheet(out: Path) -> None:
    cells = []
    x = 0
    for name, fn in CHARS.items():
        parts = fn()
        cells.append(f'<g transform="translate({x},60)">{assemble(parts)}'
                     f'<text x="300" y="40" font-size="36" text-anchor="middle" font-family="Arial">{name}</text></g>')
        x += 600
    # mouth chart: head crops
    y0 = 1130
    for row, (name, fn) in enumerate(CHARS.items()):
        parts = fn()
        head_y = 500 if name == "morty" else 300
        for i, m in enumerate("XABCDEFGH"):
            g = assemble([p for p in parts if p.parent in ("head", "neck", "eye.L", "eye.R") or p.name in ("head",)
                          or p.name.startswith("mouth")], mouth=m)
            tx, ty = i * 260 - 170, y0 + row * 400 - head_y + 190
            cells.append(f'<g transform="translate({tx},{ty}) scale(1)"><g transform="translate(300,{head_y}) scale(0.85) translate(-300,-{head_y})">{g}</g></g>'
                         f'<text x="{i*260+130}" y="{y0+row*400+330}" font-size="28" text-anchor="middle" font-family="Arial">{m}</text>')
    W_, H_ = 2340, 1950
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_}" height="{H_}" viewBox="0 0 {W_} {H_}">'
           f'<rect width="100%" height="100%" fill="#e9e4da"/>{"".join(cells)}</svg>')
    out.write_bytes(bytes(resvg_py.svg_to_bytes(svg_string=svg)))
    print(out)


if __name__ == "__main__":
    sheet(Path(sys.argv[1] if len(sys.argv) > 1 else "tmp/rm_sheet.png"))
