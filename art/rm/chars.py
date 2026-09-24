"""Rick and Morty parody characters as cut-out parts (SVG), front view.

Every part is drawn in one character space (px, y down, ground at y=GROUND, centre x=CX)
and carries a pivot (the joint it rotates about) and a z order. Swappable sets
(mouths, hands, eyes) share a slot name: "mouth:A", "mouth:B", ...
"""
from __future__ import annotations

from dataclasses import dataclass, field

INK = "#1b1b1b"
W = 4.0  # outline width, character space

GROUND = 960.0
CX = 300.0


@dataclass
class Part:
    name: str
    svg: str            # inner SVG markup in character space
    pivot: tuple[float, float]
    z: float
    parent: str | None = None
    tags: list[str] = field(default_factory=list)


def st(fill: str, w: float = W, extra: str = "") -> str:
    return (f'fill="{fill}" stroke="{INK}" stroke-width="{w}" stroke-linejoin="round" '
            f'stroke-linecap="round" {extra}')


def line(d: str, w: float = W) -> str:
    return f'<path d="{d}" {st("none", w)}/>'


def shape(d: str, fill: str, w: float = W) -> str:
    return f'<path d="{d}" {st(fill, w)}/>'


def circle(x: float, y: float, r: float, fill: str, w: float = W) -> str:
    return f'<circle cx="{x}" cy="{y}" r="{r}" {st(fill, w)}/>'


def dot(x: float, y: float, r: float) -> str:
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{INK}"/>'


# --------------------------------------------------------------------------- mouths
# Rhubarb shapes: A closed (M B P), B slightly open teeth, C open, D wide open,
# E rounded, F puckered (U W), G teeth on lip (F V), H tongue (L), X rest.

def mouths(cx: float, cy: float, wd: float, lip: str, inner: str = "#5a1f1f",
           tongue: str = "#d9707a", teeth: str = "#ffffff") -> dict[str, str]:
    h = wd / 2
    m: dict[str, str] = {}
    m["X"] = line(f"M{cx-h},{cy} Q{cx},{cy+6} {cx+h},{cy}")
    m["A"] = line(f"M{cx-h*0.8},{cy+1} L{cx+h*0.8},{cy+1}")
    m["B"] = (shape(f"M{cx-h},{cy-4} Q{cx},{cy-2} {cx+h},{cy-4} Q{cx},{cy+16} {cx-h},{cy-4} Z", inner)
              + f'<path d="M{cx-h*0.8},{cy-3} Q{cx},{cy-1} {cx+h*0.8},{cy-3} L{cx+h*0.7},{cy+3} Q{cx},{cy+5} {cx-h*0.7},{cy+3} Z" fill="{teeth}"/>')
    m["C"] = (shape(f"M{cx-h},{cy-6} Q{cx},{cy-10} {cx+h},{cy-6} Q{cx+h*0.8},{cy+24} {cx},{cy+26} Q{cx-h*0.8},{cy+24} {cx-h},{cy-6} Z", inner)
              + f'<path d="M{cx-h*0.6},{cy+18} Q{cx},{cy+8} {cx+h*0.6},{cy+18} Q{cx},{cy+26} {cx-h*0.6},{cy+18} Z" fill="{tongue}"/>')
    m["D"] = (shape(f"M{cx-h*1.15},{cy-10} Q{cx},{cy-16} {cx+h*1.15},{cy-10} Q{cx+h},{cy+38} {cx},{cy+40} Q{cx-h},{cy+38} {cx-h*1.15},{cy-10} Z", inner)
              + f'<path d="M{cx-h*0.95},{cy-9} Q{cx},{cy-14} {cx+h*0.95},{cy-9} L{cx+h*0.9},{cy-2} Q{cx},{cy-6} {cx-h*0.9},{cy-2} Z" fill="{teeth}"/>'
              + f'<path d="M{cx-h*0.7},{cy+30} Q{cx},{cy+16} {cx+h*0.7},{cy+30} Q{cx},{cy+40} {cx-h*0.7},{cy+30} Z" fill="{tongue}"/>')
    m["E"] = shape(f"M{cx-h*0.6},{cy} Q{cx},{cy-12} {cx+h*0.6},{cy} Q{cx+h*0.5},{cy+22} {cx},{cy+22} Q{cx-h*0.5},{cy+22} {cx-h*0.6},{cy} Z", inner)
    m["F"] = shape(f"M{cx-h*0.3},{cy+2} Q{cx},{cy-8} {cx+h*0.3},{cy+2} Q{cx},{cy+14} {cx-h*0.3},{cy+2} Z", inner)
    m["G"] = (shape(f"M{cx-h*0.9},{cy-4} Q{cx},{cy-6} {cx+h*0.9},{cy-4} Q{cx},{cy+12} {cx-h*0.9},{cy-4} Z", inner)
              + f'<path d="M{cx-h*0.6},{cy-3} L{cx+h*0.6},{cy-3} L{cx+h*0.5},{cy+4} L{cx-h*0.5},{cy+4} Z" fill="{teeth}"/>')
    m["H"] = (shape(f"M{cx-h*0.9},{cy-6} Q{cx},{cy-10} {cx+h*0.9},{cy-6} Q{cx+h*0.7},{cy+20} {cx},{cy+22} Q{cx-h*0.7},{cy+20} {cx-h*0.9},{cy-6} Z", inner)
              + f'<path d="M{cx-h*0.4},{cy+4} Q{cx},{cy-8} {cx+h*0.4},{cy+4} L{cx+h*0.3},{cy+12} Q{cx},{cy+16} {cx-h*0.3},{cy+12} Z" fill="{tongue}"/>')
    return m


# --------------------------------------------------------------------------- hands
def hand(x: float, y: float, skin: str, kind: str, side: int) -> str:
    """Simple 4-finger cartoon hand at wrist (x, y), pointing down; side = -1 left, +1 right."""
    s = side
    if kind == "fist":
        return shape(f"M{x-14},{y} Q{x-20},{y+30} {x},{y+34} Q{x+20},{y+30} {x+14},{y} Z", skin) + \
            line(f"M{x-8*s},{y+14} Q{x},{y+18} {x+8*s},{y+14}", 3)
    if kind == "point":
        return (shape(f"M{x-13},{y} Q{x-18},{y+26} {x},{y+30} Q{x+18},{y+26} {x+13},{y} Z", skin)
                + shape(f"M{x-4},{y+26} L{x-4},{y+62} Q{x},{y+68} {x+4},{y+62} L{x+4},{y+26}", skin, 4))
    # open
    return (shape(f"M{x-14},{y} Q{x-22},{y+22} {x-16},{y+44} Q{x-12},{y+50} {x-8},{y+44} "
                  f"L{x-6},{y+52} Q{x-1},{y+58} {x+3},{y+50} L{x+5},{y+54} Q{x+11},{y+58} {x+13},{y+46} "
                  f"Q{x+20},{y+22} {x+14},{y} Z", skin)
            + shape(f"M{x+14*s},{y+10} Q{x+28*s},{y+18} {x+24*s},{y+28} Q{x+18*s},{y+30} {x+14*s},{y+24}", skin, 4))


# --------------------------------------------------------------------------- Morty
MORTY = dict(skin="#f7d2b5", hair="#6b4424", shirt="#f3dd3f", pants="#3d5fa3", shoe="#f2f2f2",
             eye="#ffffff", sole="#bdbdbd")


def morty() -> list[Part]:
    c = MORTY
    P: list[Part] = []
    # legs (pants tubes) + shoes
    for side, x in ((-1, CX - 34), (1, CX + 34)):
        n = "L" if side < 0 else "R"
        P.append(Part(f"leg.{n}",
                      shape(f"M{x-30},{790} L{x-27},{925} L{x+27},{925} L{x+30},{790} Z", c["pants"]),
                      (x, 800), 10, "hips"))
        P.append(Part(f"shoe.{n}",
                      shape(f"M{x-30+side*-4},{922} Q{x-34+side*-6},{958} {x+side*14},{960} "
                            f"Q{x+34+side*14},{960} {x+30},{922} Z", c["shoe"]),
                      (x, 925), 11, f"leg.{n}"))
    P.append(Part("hips", shape(f"M{CX-68},{770} L{CX-66},{812} L{CX+66},{812} L{CX+68},{770} Z", c["pants"]),
                  (CX, 790), 12))
    # arms: upper (sleeve) + forearm + hand
    for side in (-1, 1):
        n = "L" if side < 0 else "R"
        sx = CX + side * 70
        P.append(Part(f"forearm.{n}",
                      shape(f"M{sx+side*8-9},{700} L{sx+side*14-9},{770} L{sx+side*14+9},{770} L{sx+side*8+9},{700} Z", c["skin"]),
                      (sx + side * 8, 702), 14, f"sleeve.{n}"))
        for kind in ("open", "fist", "point"):
            P.append(Part(f"hand.{n}:{kind}", hand(sx + side * 14, 766, c["skin"], kind, side),
                          (sx + side * 14, 768), 15, f"forearm.{n}", ["swap"]))
        # round shoulder cap centred on the pivot, tucked behind the torso: no corner shows when it swings
        xa = sx - side * 4
        P.append(Part(f"sleeve.{n}",
                      shape(f"M{xa-22},{668} A22,22 0 0 1 {xa+22},{668} L{xa+side*14+18},{708} L{xa+side*14-18},{708} Z", c["shirt"]),
                      (xa, 668), 12.5, "torso"))
    P.append(Part("torso",
                  shape(f"M{CX-40},{632} Q{CX-72},{636} {CX-76},{664} L{CX-70},{782} Q{CX},{790} {CX+70},{782} "
                        f"L{CX+76},{664} Q{CX+72},{636} {CX+40},{632} Q{CX},{646} {CX-40},{632} Z", c["shirt"]),
                  (CX, 780), 13, "hips"))
    P.append(Part("neck", shape(f"M{CX-13},{600} L{CX-13},{638} Q{CX},{644} {CX+13},{638} L{CX+13},{600} Z", c["skin"]),
                  (CX, 636), 12, "torso"))
    # head: ears, skull, hair, face
    HY = 500
    head = (shape(f"M{CX-122},{505} Q{CX-146},{495} {CX-140},{522} Q{CX-134},{546} {CX-114},{540}", c["skin"])
            + shape(f"M{CX+122},{505} Q{CX+146},{495} {CX+140},{522} Q{CX+134},{546} {CX+114},{540}", c["skin"])
            + shape(f"M{CX},{386} C{CX+80},{386} {CX+128},{420} {CX+126},{498} "
                    f"C{CX+124},{568} {CX+84},{612} {CX},{614} C{CX-84},{612} {CX-124},{568} {CX-126},{498} "
                    f"C{CX-128},{420} {CX-80},{386} {CX},{386} Z", c["skin"]))
    P.append(Part("head", head, (CX, 604), 20, "neck"))
    hair = shape(f"M{CX-127},{492} C{CX-134},{410} {CX-76},{376} {CX},{376} C{CX+76},{376} {CX+134},{410} {CX+127},{492} "
                 f"Q{CX+116},{470} {CX+112},{452} C{CX+60},{444} {CX+20},{442} {CX+4},{430} "
                 f"Q{CX-8},{448} {CX-30},{446} C{CX-70},{446} {CX-100},{452} {CX-112},{452} Q{CX-116},{470} {CX-127},{492} Z",
                 c["hair"])
    P.append(Part("hair", hair, (CX, 500), 26, "head"))
    for side in (-1, 1):
        n = "L" if side < 0 else "R"
        ex = CX + side * 46
        P.append(Part(f"eye.{n}", circle(ex, HY, 40, c["eye"]), (ex, HY), 21, "head"))
        P.append(Part(f"pupil.{n}", dot(ex, HY, 5.5), (ex, HY), 22, f"eye.{n}"))
        P.append(Part(f"brow.{n}", line(f"M{ex-22},{HY-50} Q{ex},{HY-56} {ex+22},{HY-50}", 4), (ex, HY - 52), 23, "head"))
    P.append(Part("nose", line(f"M{CX-4},{548} Q{CX+10},{553} {CX+2},{560}", 4), (CX, 552), 23, "head"))
    for k, svg in mouths(CX, 582, 54, c["skin"]).items():
        P.append(Part(f"mouth:{k}", svg, (CX, 582), 24, "head", ["swap"]))
    return P


# --------------------------------------------------------------------------- Rick
RICK = dict(skin="#efd9c9", hair="#a9d8ea", coat="#f4f6f6", coat_sh="#d6dcdd", shirt="#8fc3d6",
            pants="#8a6a45", shoe="#3a2a1c", eye="#ffffff", brow="#8fb9c8", drool="#9bd35a")


def rick() -> list[Part]:
    c = RICK
    P: list[Part] = []
    for side, x in ((-1, CX - 36), (1, CX + 36)):
        n = "L" if side < 0 else "R"
        P.append(Part(f"leg.{n}", shape(f"M{x-30},{700} L{x-26},{925} L{x+26},{925} L{x+30},{700} Z", c["pants"]),
                      (x, 712), 10, "hips"))
        P.append(Part(f"shoe.{n}",
                      shape(f"M{x-28+side*-4},{920} Q{x-36+side*-8},{960} {x+side*16},{960} "
                            f"Q{x+36+side*16},{960} {x+28},{920} Z", c["shoe"]),
                      (x, 924), 11, f"leg.{n}"))
    P.append(Part("hips", shape(f"M{CX-68},{680} L{CX-68},{722} L{CX+68},{722} L{CX+68},{680} Z", c["pants"]),
                  (CX, 700), 12))
    # sweater torso
    P.append(Part("torso",
                  shape(f"M{CX-40},{452} Q{CX-78},{458} {CX-82},{490} L{CX-72},{700} L{CX+72},{700} "
                        f"L{CX+82},{490} Q{CX+78},{458} {CX+40},{452} Q{CX},{470} {CX-40},{452} Z", c["shirt"]),
                  (CX, 690), 13, "hips"))
    # lab coat panels (open front), flaring to the knees
    for side in (-1, 1):
        n = "L" if side < 0 else "R"
        s = side
        P.append(Part(f"coat.{n}",
                      shape(f"M{CX+s*36},{454} Q{CX+s*80},{458} {CX+s*88},{492} L{CX+s*104},{800} "
                            f"Q{CX+s*70},{812} {CX+s*30},{806} L{CX+s*34},{600} L{CX+s*22},{470} Z", c["coat"])
                      + line(f"M{CX+s*36},{454} L{CX+s*58},{530} L{CX+s*34},{560}", 4)
                      + shape(f"M{CX+s*56},{640} L{CX+s*90},{640} L{CX+s*92},{690} L{CX+s*58},{692} Z", c["coat_sh"], 4),
                      (CX + s * 60, 470), 17, "torso"))
    for side in (-1, 1):
        n = "L" if side < 0 else "R"
        sx = CX + side * 80
        P.append(Part(f"forearm.{n}",
                      shape(f"M{sx+side*14-15},{580} L{sx+side*22-14},{690} L{sx+side*22+14},{690} L{sx+side*14+15},{580} Z", c["coat"]),
                      (sx + side * 14, 584), 18, f"sleeve.{n}"))
        for kind in ("open", "fist", "point"):
            P.append(Part(f"hand.{n}:{kind}", hand(sx + side * 22, 688, c["skin"], kind, side),
                          (sx + side * 22, 690), 19, f"forearm.{n}", ["swap"]))
        xa = sx - side * 4
        P.append(Part(f"sleeve.{n}",
                      shape(f"M{xa-24},{498} A24,24 0 0 1 {xa+24},{498} L{xa+side*12+22},{592} L{xa+side*12-22},{592} Z", c["coat"]),
                      (xa, 498), 16.5, "torso"))
    P.append(Part("neck", shape(f"M{CX-15},{420} L{CX-15},{462} Q{CX},{470} {CX+15},{462} L{CX+15},{420} Z", c["skin"]),
                  (CX, 458), 12, "torso"))
    # head: long face, ears
    head = (shape(f"M{CX-92},{290} Q{CX-116},{282} {CX-112},{310} Q{CX-106},{334} {CX-88},{326}", c["skin"])
            + shape(f"M{CX+92},{290} Q{CX+116},{282} {CX+112},{310} Q{CX+106},{334} {CX+88},{326}", c["skin"])
            + shape(f"M{CX},{182} C{CX+62},{182} {CX+98},{214} {CX+96},{290} "
                    f"C{CX+94},{364} {CX+70},{432} {CX},{436} C{CX-70},{432} {CX-94},{364} {CX-96},{290} "
                    f"C{CX-98},{214} {CX-62},{182} {CX},{182} Z", c["skin"]))
    P.append(Part("head", head, (CX, 428), 20, "neck"))
    # spiky hair behind the head
    # irregular spikes sweeping up and out (bigger at the upper sides), valleys hug the skull
    spikes = [(-128, 292), (-176, 226), (-150, 150), (-178, 92), (-96, 104), (-72, 30), (-22, 88),
              (18, 22), (44, 92), (104, 40), (104, 118), (180, 96), (150, 160), (184, 232), (128, 290)]
    base = [(-98, 266), (-102, 214), (-96, 170), (-86, 140), (-60, 128), (-40, 120), (-6, 116),
            (22, 116), (50, 120), (72, 128), (90, 146), (98, 176), (104, 214), (100, 262), (96, 300)]
    pts = [f"{CX-96},{310}"]
    for (sx_, sy_), (bx, by) in zip(spikes, base):
        pts.append(f"{CX+sx_},{sy_}")
        pts.append(f"{CX+bx},{by}")
    pts.append(f"{CX+96},{310}")
    P.append(Part("hair_back", shape("M" + " L".join(pts) + " Z", c["hair"]), (CX, 300), 19, "head"))
    # hairline fringe on the forehead
    P.append(Part("hair",
                  shape(f"M{CX-96},{262} Q{CX-92},{196} {CX-40},{184} Q{CX},{178} {CX+40},{184} "
                        f"Q{CX+92},{196} {CX+96},{262} Q{CX+84},{226} {CX+56},{214} L{CX+40},{226} "
                        f"L{CX+20},{210} L{CX},{224} L{CX-20},{210} L{CX-40},{226} L{CX-56},{214} "
                        f"Q{CX-84},{226} {CX-96},{262} Z", c["hair"]),
                  (CX, 230), 26, "head"))
    HY = 288
    for side in (-1, 1):
        n = "L" if side < 0 else "R"
        ex = CX + side * 32
        P.append(Part(f"eye.{n}",
                      circle(ex, HY, 25, c["eye"], 4)
                      + line(f"M{ex-18},{HY+31} Q{ex},{HY+38} {ex+18},{HY+31}", 3)   # eye bags
                      + line(f"M{ex-10},{HY+41} Q{ex},{HY+44} {ex+10},{HY+41}", 2.5)
                      + line(f"M{ex+side*30},{HY-4} L{ex+side*42},{HY-8} M{ex+side*30},{HY+6} L{ex+side*42},{HY+8}", 2.5),
                      (ex, HY), 21, "head"))
        P.append(Part(f"pupil.{n}", dot(ex - side * 2, HY + 1, 3.5), (ex, HY), 22, f"eye.{n}"))
    # the unibrow
    P.append(Part("brow",
                  shape(f"M{CX-70},{258} Q{CX-40},{236} {CX-6},{252} Q{CX},{246} {CX+6},{252} "
                        f"Q{CX+40},{236} {CX+70},{258} Q{CX+40},{248} {CX+4},{262} Q{CX},{258} {CX-4},{262} "
                        f"Q{CX-40},{248} {CX-70},{258} Z", c["brow"], 4),
                  (CX, 252), 23, "head"))
    P.append(Part("nose", line(f"M{CX+2},{300} Q{CX+18},{330} {CX+12},{346} Q{CX+2},{352} {CX-6},{346}", 4),
                  (CX, 330), 23, "head"))
    for k, svg in mouths(CX, 388, 70, c["skin"]).items():
        P.append(Part(f"mouth:{k}", svg, (CX, 388), 24, "head", ["swap"]))
    P.append(Part("drool", shape(f"M{CX+30},{392} Q{CX+40},{410} {CX+34},{428} Q{CX+28},{436} {CX+26},{424} "
                                 f"Q{CX+28},{408} {CX+26},{396} Z", c["drool"], 3),
                  (CX + 30, 392), 25, "head"))
    return P


CHARS = {"morty": morty, "rick": rick}
