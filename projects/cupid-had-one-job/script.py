"""CUPID HAD ONE JOB — 36 s vertical short.

Pip (tiny cupid archer) vs Bruno (grumpy knight). Arrow 1 bounces off the shield, arrow 2 is
ducked (Bruno laughs), arrow 3 is a trick shot from the sky → BONK → hearts → love-struck
Bruno chases a terrified Pip off screen.

Frame numbers are the single source of truth: the audio cue sheet (cues.json) is emitted from
the same constants, so moving a beat here moves its sound too.
"""
from __future__ import annotations

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy
from mathutils import Vector

from studio import core as C, characters as CH, props as P

FPS = 24
FRAME_END = 816  # 34 s

TITLE = "Cupid Had One Job"
VOICE = "bm_george"  # Kokoro storybook narrator

# ----------------------------------------------------------------------------- timeline
# Beat A: enter                     1-96
F_WALK_IN_END = 70
# Beat B: shot 1 -> shield         96-216
F_CUT_PIP1, F_RAISE, F_DRAWN1, F_SHOT1, F_HIT1 = 96, 110, 130, 140, 150
F_ARROW1_LAND = 166
F_SMUG = 160
# Beat C: shot 2 -> duck, laugh    216-360
F_CUT_PIP2, F_DRAWN2, F_SHOT2, F_TREE_HIT = 216, 240, 252, 268
F_DUCK, F_STAND = 250, 270
F_LAUGH0, F_LAUGH1 = 280, 330
F_STOMP0, F_STOMP1 = 312, 344
# Beat D: shot 3 -> sky -> bonk    360-528
F_AIM_UP, F_DRAWN3, F_SHOT3, F_APEX, F_BONK = 360, 395, 400, 432, 464
# Beat E: hearts, love, run        464-620
F_HEARTS0, F_HEARTS1 = 480, 600
F_HEART_EYES = 500
F_DROP_SHIELD = 496
F_JIG0, F_JIG1 = 505, 556
F_CHASE0, F_CHASE1 = 560, 620
# Beat F: flee, end card           590-864
F_PIP_SCARED, F_PIP_TURN, F_PIP_RUN0, F_PIP_RUN1 = 596, 616, 624, 700
F_BRUNO_RUN1 = 740
F_END_CARD = 744

PIP_X, BRUNO_X = -1.9, 2.0
TREE_HIT = (4.6, 1.4, 1.9)

cues: list[dict] = []
lines: list[dict] = []


def sfx(frame: int, name: str, gain: float = 1.0) -> None:
    cues.append({"frame": frame, "sfx": name, "gain": gain})


def say(frame: int, text: str) -> None:
    lines.append({"frame": frame, "text": text})


# ----------------------------------------------------------------------------- helpers


def fly(arrow, f0: int, f1: int, path: list[Vector], *, stick_rot=None) -> None:
    """Keyframe an arrow along sampled world positions, nose pointing along velocity."""
    n = len(path)
    for i, p in enumerate(path):
        f = round(f0 + (f1 - f0) * i / (n - 1))
        vel = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)])
        rot = C.aim_rot(vel) if vel.length > 1e-6 else arrow.rotation_euler
        arrow.location = p
        arrow.rotation_euler = rot
        arrow.keyframe_insert("location", frame=f)
        arrow.keyframe_insert("rotation_euler", frame=f)
    C.set_interp_all(arrow, "LINEAR", "location")


def parabola(a: Vector, apex: Vector, b: Vector, n: int = 16) -> list[Vector]:
    """Quadratic Bezier through a -> apex -> b (a decent cartoon arc)."""
    ctrl = apex * 2 - (a + b) * 0.5
    out = []
    for i in range(n):
        t = i / (n - 1)
        out.append(a * (1 - t) ** 2 + ctrl * 2 * (1 - t) * t + b * t ** 2)
    return out


def pop_in(obj, f: int, scale=1.0, frames=6) -> None:
    C.key(obj, f, scale=(0, 0, 0))
    C.key(obj, f + frames // 2, scale=(scale * 1.35,) * 3)
    C.key(obj, f + frames, scale=(scale,) * 3)


def spawn_hearts(head, f0: int, f1: int, *, every=12, rise=1.7, col=None, tag="h") -> None:
    i = 0
    for f in range(f0, f1, every):
        origin = C.world_pos(head, f) + Vector((0, 0, 0.45))
        h = P.heart(f"fx.heart.{tag}{i}", size=0.22 + (i % 3) * 0.05, loc=origin, col=col)
        C.visible(h, 1, False)
        C.visible(h, f, True)
        pop_in(h, f, 1.0)
        wob = 0.35 if i % 2 else -0.35
        C.key(h, f, loc=origin)
        C.key(h, f + 20, loc=origin + Vector((wob, 0, rise * 0.5)))
        C.key(h, f + 40, loc=origin + Vector((-wob * 0.5, 0, rise)))
        C.key(h, f + 34, scale=(1, 1, 1))
        C.key(h, f + 42, scale=(0, 0, 0))
        C.visible(h, f + 43, False)
        i += 1


# ----------------------------------------------------------------------------- build


def build() -> None:
    C.reset_scene()
    scene = bpy.context.scene
    set_col, char_col, fx_col, cam_col = (C.collection(n) for n in ("Set", "Characters", "FX", "Cameras"))

    # ---- set
    C.sky((0.62, 0.80, 0.97), 1.0)
    C.sun(energy=3.5, rot=(48, 12, 35), angle_deg=4)
    P.ground(col=set_col)
    for i, (x, y, r) in enumerate(((-14, 26, 9), (2, 30, 11), (16, 24, 8), (-6, 18, 4.5))):
        P.hill(f"Hill{i}", loc=(x, y, -r * 0.05), r=r, col=set_col)
    P.tree("TreeHit", loc=(TREE_HIT[0], TREE_HIT[1], 0), h=3.0, col=set_col, seed=1)
    for i, (x, y, h) in enumerate(((-7, 6, 2.6), (7.5, 8, 3.2), (-3, 12, 2.4), (10, 5, 2.2), (-11, 9, 3.0))):
        P.tree(f"Tree{i}", loc=(x, y, 0), h=h, canopy="#3f9d4f" if i % 2 else "#57b85f", col=set_col, seed=i + 3)
    for i, (x, y) in enumerate(((1.0, 1.6), (-4.5, 2.2), (6, 3.5))):
        P.rock(f"Rock{i}", loc=(x, y, 0), r=0.3 + i * 0.1, col=set_col, seed=i)
    for i, (x, z) in enumerate(((-6, 9), (3, 11), (9, 8.5))):
        P.cloud(f"Cloud{i}", loc=(x, 22, z), size=1.6, col=set_col, seed=i)

    # ---- characters
    pip = CH.build_character("Pip", loc=(-3.8, 0, 0), face_deg=90, leg=0.45, body_h=0.55, body_r=0.28,
                             head_r=0.31, arm=0.42, arm_r=0.065, leg_r=0.085,
                             colors={"body": "#ff6b8a", "limb": "#ffd9b3", "skin": "#ffd9b3"}, col=char_col)
    bru = CH.build_character("Bruno", loc=(BRUNO_X, 0, 0), face_deg=-90, leg=0.75, body_h=0.95, body_r=0.45,
                             head_r=0.38, arm=0.58, arm_r=0.1, leg_r=0.12,
                             colors={"body": "#3b4a6b", "limb": "#5b6b8c", "skin": "#ffd2a8", "mouth": "#5a2020"},
                             col=char_col)
    d_pip, d_bru = pip["dims"], bru["dims"]

    bow = P.bow("Pip.bow", size=0.5, parent=pip["hand_l"], col=char_col)
    wings = P.wings("Pip.wings", parent=pip["body"], loc=(0, d_pip["body_r"] * 0.8, d_pip["body_h"] * 0.1),
                    size=0.3, col=char_col)
    P.halo("Pip.halo", parent=pip["head"], loc=(0, 0, d_pip["head_r"] * 1.45), r=0.2, col=char_col)
    P.quiver("Pip.quiver", parent=pip["body"], loc=(0.12, d_pip["body_r"] * 0.85, 0.0), rot=(15, 0, 0), col=char_col)
    shield = P.shield("Bruno.shield", r=0.34, parent=bru["hand_l"], rot=(0, 35, 0), col=char_col)
    helmet = P.helmet("Bruno.helmet", r=d_bru["head_r"] * 1.02, parent=bru["head"],
                      loc=(0, 0, d_bru["head_r"] * 0.5), col=char_col)
    C.visible(shield, 1, True)

    arrows = [P.arrow(f"Arrow{i}", col=fx_col) for i in (1, 2, 3)]
    arrow_stuck = P.arrow("Arrow3.stuck", col=fx_col)  # copy that rides on the helmet after the bonk
    for a in arrows + [arrow_stuck]:
        C.visible(a, 1, False)

    # ---- cameras
    cam_wide = C.camera("CamWide", (0.0, -7.5, 1.5), (0.0, 0, 1.15), lens=26, col=cam_col)
    cam_pip = C.camera("CamPip", (0.3, -2.3, 1.0), (-1.75, 0, 0.8), lens=45, col=cam_col)
    cam_bru = C.camera("CamBruno", (0.4, -3.1, 1.7), (2.0, 0, 1.45), lens=45, col=cam_col)
    cam_sky = C.camera("CamSky", (0.1, -7.5, 1.2), (0.1, 0, 1.5), lens=24, col=cam_col)
    cam_chase = C.camera("CamChase", (-2.0, -6.5, 1.8), (-2.5, 0, 1.0), lens=32, col=cam_col)
    cam_end = C.camera("CamEnd", (0, -7.5, 3.0), (0, 2, 3.0), lens=40, col=cam_col)

    # ======================================================================= Beat A: enter
    CH.rest_pose(pip, 1)
    CH.rest_pose(bru, 1)
    C.cut(1, cam_wide)
    say(8, "Cupid had one job.")

    # Bruno on guard, shield arm bent, breathing
    CH.arms(bru, 1, l=(-35, 0, 0), el_l=(-75, 0, 0), r=(8, 0, -8))
    CH.idle_breath(bru, 1, F_CUT_PIP1 + 30)
    CH.eyes(bru, 1, look=(0, 0))
    CH.eyes(bru, 40, look=(-0.8, -0.3))  # side-eye the newcomer

    # Pip walks in, bow arm half raised so the bow reads
    P.flap_wings(wings, 1, FRAME_END, period=8, amp=35)
    CH.walk(pip, 1, F_WALK_IN_END, (-3.8, 0), (PIP_X, 0), stride=8, amp=28, bob=0.04, swing_arms=False)
    CH.arms(pip, 1, l=(-40, 0, 0), el_l=(-20, 0, 0), r=(15, 0, 0))
    CH.arms(pip, F_WALK_IN_END, l=(-40, 0, 0), el_l=(-20, 0, 0), r=(15, 0, 0))
    P.draw_bow(bow, 1, 0.0)
    CH.mouth(pip, 1, shape="smile")
    for f in range(4, F_WALK_IN_END, 8):
        sfx(f, "step", 0.25)

    # ======================================================================= Beat B: shot 1
    C.cut(F_CUT_PIP1, cam_pip)
    say(104, "One grumpy knight. One tiny archer. What could go wrong?")
    CH.arms(pip, F_CUT_PIP1, l=(-40, 0, 0), el_l=(-20, 0, 0), r=(15, 0, 0), el_r=(0, 0, 0))
    CH.arms(pip, F_RAISE, l=(-90, 0, 0), el_l=(0, 0, 0), r=(-90, 0, 0), el_r=(10, 0, 0))
    CH.arms(pip, F_DRAWN1, l=(-90, 0, 0), el_l=(0, 0, 0), r=(-90, 0, 0), el_r=(115, 0, 0))
    CH.arms(pip, F_SHOT1, l=(-90, 0, 0), el_l=(0, 0, 0), r=(-90, 0, 0), el_r=(115, 0, 0))
    CH.arms(pip, F_SHOT1 + 4, l=(-90, 0, 0), el_l=(0, 0, 0), r=(-100, 0, 0), el_r=(20, 0, 0))
    P.draw_bow(bow, F_RAISE, 0.0)
    P.draw_bow(bow, F_DRAWN1, 1.0)
    P.draw_bow(bow, F_SHOT1, 1.0)
    P.draw_bow(bow, F_SHOT1 + 2, 0.0)
    CH.mouth(pip, F_RAISE, shape="small")
    CH.eyes(pip, F_RAISE, scale=0.9, look=(0.6, 0))
    sfx(F_SHOT1, "twang", 0.9)
    sfx(F_SHOT1 + 1, "swoosh", 0.6)

    # Bruno raises the shield just in time
    CH.arms(bru, F_SHOT1 - 8, l=(-35, 0, 0), el_l=(-75, 0, 0), r=(8, 0, -8))
    CH.arms(bru, F_HIT1 - 2, l=(-95, 0, 0), el_l=(-5, 0, 0), r=(20, 0, -10))
    CH.arms(bru, F_SMUG + 10, l=(-95, 0, 0), el_l=(-5, 0, 0), r=(20, 0, -10))
    CH.arms(bru, F_SMUG + 20, l=(-35, 0, 0), el_l=(-75, 0, 0), r=(8, 0, -8))
    C.cut(F_SHOT1 - 2, cam_wide)

    a1 = arrows[0]
    start = C.world_pos(bow["grip"], F_SHOT1)
    target = C.world_pos(shield, F_HIT1) + Vector((-0.05, 0, 0))
    C.visible(a1, F_SHOT1, True)
    fly(a1, F_SHOT1, F_HIT1, [start, target])
    # bounce off, tumble, stick in the ground
    land = Vector((0.9, -0.3, 0.0))
    fly(a1, F_HIT1, F_ARROW1_LAND, parabola(target, Vector((1.4, -0.2, 1.4)), land, 8))
    a1.rotation_euler = C.rad((-100, 0, 20))
    a1.keyframe_insert("rotation_euler", frame=F_ARROW1_LAND)
    sfx(F_HIT1, "thud", 0.9)
    sfx(F_ARROW1_LAND, "step", 0.4)
    CH.squash(bru, F_HIT1, depth=0.08, recover=8)

    # Bruno smug (camera is already on him for the impact)
    C.cut(F_HIT1 - 3, cam_bru)
    CH.mouth(bru, F_SMUG, shape="smile")
    CH.eyes(bru, F_SMUG, look=(-0.6, 0.2))
    CH.head_turn(bru, F_SMUG, roll=0)
    CH.head_turn(bru, F_SMUG + 8, roll=12)
    CH.head_turn(bru, F_SMUG + 40, roll=12)
    CH.head_turn(bru, F_SMUG + 50, roll=0)
    CH.bounce(bru, F_SMUG + 10, F_SMUG + 34, period=8, height=0.08)

    # ======================================================================= Beat C: shot 2
    C.cut(F_CUT_PIP2, cam_pip)
    CH.mouth(pip, F_CUT_PIP2, shape="small")
    CH.arms(pip, F_CUT_PIP2, l=(-90, 0, 0), el_l=(0, 0, 0), r=(-100, 0, 0), el_r=(20, 0, 0))
    CH.arms(pip, F_DRAWN2, l=(-90, 0, 0), el_l=(0, 0, 0), r=(-90, 0, 0), el_r=(115, 0, 0))
    CH.arms(pip, F_SHOT2, l=(-90, 0, 0), el_l=(0, 0, 0), r=(-90, 0, 0), el_r=(115, 0, 0))
    CH.arms(pip, F_SHOT2 + 4, l=(-90, 0, 0), el_l=(0, 0, 0), r=(-100, 0, 0), el_r=(20, 0, 0))
    P.draw_bow(bow, F_CUT_PIP2 + 4, 0.0)
    P.draw_bow(bow, F_DRAWN2, 1.0)
    P.draw_bow(bow, F_SHOT2, 1.0)
    P.draw_bow(bow, F_SHOT2 + 2, 0.0)
    sfx(F_SHOT2, "twang", 0.9)
    sfx(F_SHOT2 + 1, "swoosh", 0.6)
    C.cut(F_SHOT2 - 6, cam_wide)

    # Bruno ducks: crouch + look up
    leg = d_bru["leg"]
    for j in ("hip_l", "hip_r"):
        C.key(bru[j], F_DUCK - 4, rot=(0, 0, 0)); C.key(bru[j], F_DUCK + 6, rot=(-55, 0, 0))
        C.key(bru[j], F_STAND, rot=(-55, 0, 0)); C.key(bru[j], F_STAND + 10, rot=(0, 0, 0))
    for j in ("knee_l", "knee_r"):
        C.key(bru[j], F_DUCK - 4, rot=(0, 0, 0)); C.key(bru[j], F_DUCK + 6, rot=(85, 0, 0))
        C.key(bru[j], F_STAND, rot=(85, 0, 0)); C.key(bru[j], F_STAND + 10, rot=(0, 0, 0))
    C.key(bru["hips"], F_DUCK - 4, loc=(0, 0, leg)); C.key(bru["hips"], F_DUCK + 6, loc=(0, 0, leg * 0.5))
    C.key(bru["hips"], F_STAND, loc=(0, 0, leg * 0.5)); C.key(bru["hips"], F_STAND + 10, loc=(0, 0, leg))
    CH.head_turn(bru, F_DUCK - 4, pitch=0); CH.head_turn(bru, F_DUCK + 8, pitch=-35)
    CH.head_turn(bru, F_STAND, pitch=-35); CH.head_turn(bru, F_STAND + 10, pitch=0)
    CH.eyes(bru, F_DUCK + 6, look=(0, 1))
    sfx(F_DUCK + 2, "whoosh", 0.5)

    a2 = arrows[1]
    start = C.world_pos(bow["grip"], F_SHOT2)
    C.visible(a2, F_SHOT2, True)
    fly(a2, F_SHOT2, F_TREE_HIT, parabola(start, Vector((1.5, 0.4, 2.1)), Vector(TREE_HIT), 8))
    sfx(F_TREE_HIT, "thud", 0.6)

    # Bruno laughs, Pip stomps
    C.cut(F_LAUGH0 - 4, cam_bru)
    say(272, "Nope.")
    CH.mouth(bru, F_LAUGH0 - 6, shape="smile"); CH.mouth(bru, F_LAUGH0, shape="big")
    CH.eyes(bru, F_LAUGH0, scale=0.85, look=(0, 0.4))
    CH.head_turn(bru, F_LAUGH0, pitch=-20, roll=-6)
    CH.bounce(bru, F_LAUGH0, F_LAUGH1, period=8, height=0.12)
    for i, f in enumerate(range(F_LAUGH0, F_LAUGH1, 8)):
        CH.arms(bru, f, l=(-35, 0, 0), el_l=(-75, 0, 0), r=(-70 if i % 2 else -20, 0, -10), el_r=(-30, 0, 0))
    CH.arms(bru, F_LAUGH1 + 8, l=(-35, 0, 0), el_l=(-75, 0, 0), r=(8, 0, -8), el_r=(0, 0, 0))
    CH.mouth(bru, F_LAUGH1 + 6, shape="smile"); CH.head_turn(bru, F_LAUGH1 + 8, pitch=0, roll=0)
    sfx(F_LAUGH0, "laugh", 0.8)

    C.cut(F_STOMP0, cam_pip)
    CH.bounce(pip, F_STOMP0, F_STOMP1, period=6, height=0.14)
    CH.mouth(pip, F_STOMP0, shape="o")
    CH.eyes(pip, F_STOMP0, scale=1.1, look=(0.5, 0.4))
    for i, f in enumerate(range(F_STOMP0, F_STOMP1, 6)):
        CH.head_turn(pip, f, yaw=18 if i % 2 else -18)
    CH.head_turn(pip, F_STOMP1 + 4, yaw=0)
    P.flap_wings(wings, F_STOMP0, F_STOMP1, period=4, amp=45)
    for f in range(F_STOMP0 + 3, F_STOMP1, 6):
        sfx(f, "step", 0.5)
    say(346, "Plan B.")

    # ======================================================================= Beat D: sky shot
    CH.mouth(pip, F_AIM_UP, shape="small")
    CH.eyes(pip, F_AIM_UP, scale=1.0, look=(0.3, 0.8))
    CH.arms(pip, F_AIM_UP, l=(-90, 0, 0), el_l=(0, 0, 0), r=(-100, 0, 0), el_r=(20, 0, 0))
    CH.arms(pip, F_AIM_UP + 18, l=(-150, 0, 0), el_l=(0, 0, 0), r=(-150, 0, 0), el_r=(20, 0, 0))
    CH.arms(pip, F_DRAWN3, l=(-150, 0, 0), el_l=(0, 0, 0), r=(-150, 0, 0), el_r=(115, 0, 0))
    CH.arms(pip, F_SHOT3, l=(-150, 0, 0), el_l=(0, 0, 0), r=(-150, 0, 0), el_r=(115, 0, 0))
    CH.arms(pip, F_SHOT3 + 4, l=(-150, 0, 0), el_l=(0, 0, 0), r=(-160, 0, 0), el_r=(20, 0, 0))
    CH.arms(pip, F_SHOT3 + 30, l=(-60, 0, 0), el_l=(-20, 0, 0), r=(-40, 0, 0), el_r=(-30, 0, 0))  # hand over eyes
    CH.head_turn(pip, F_AIM_UP + 18, pitch=-40); CH.head_turn(pip, F_SHOT3 + 30, pitch=-30)
    P.draw_bow(bow, F_AIM_UP + 18, 0.0); P.draw_bow(bow, F_DRAWN3, 1.0)
    P.draw_bow(bow, F_SHOT3, 1.0); P.draw_bow(bow, F_SHOT3 + 2, 0.0)
    sfx(F_SHOT3, "twang", 1.0)
    sfx(F_SHOT3 + 1, "swoosh", 0.7)
    sfx(F_APEX + 8, "whoosh", 0.7)

    C.cut(F_SHOT3 - 2, cam_sky)
    # camera tilts up with the arrow, then back down onto Bruno
    for f, tgt in ((F_SHOT3 - 2, (0.1, 0, 1.5)), (F_APEX, (0.3, 0, 6.0)), (F_BONK - 6, (2.0, 0, 2.2))):
        C.point_at(cam_sky, tgt)
        cam_sky.keyframe_insert("rotation_euler", frame=f)

    a3 = arrows[2]
    start = C.world_pos(bow["grip"], F_SHOT3)
    helmet_top = C.world_pos(helmet, F_BONK) + Vector((0, 0, 0.28))
    C.visible(a3, F_SHOT3, True)
    fly(a3, F_SHOT3, F_BONK, parabola(start, Vector((0.2, 0, 7.0)), helmet_top, 20))
    C.visible(a3, F_BONK + 1, False)
    # the stuck copy lives on the helmet from the bonk on
    arrow_stuck.parent = helmet
    arrow_stuck.location = (0.05, 0.05, 0.36)
    arrow_stuck.rotation_euler = C.rad((-95, 0, 15))
    C.visible(arrow_stuck, F_BONK + 1, True)

    # Bruno watches it come down
    C.cut(F_BONK - 12, cam_bru)
    CH.head_turn(bru, F_SHOT3 + 10, pitch=0); CH.head_turn(bru, F_SHOT3 + 24, pitch=-45)
    CH.head_turn(bru, F_BONK - 8, pitch=-50); CH.head_turn(bru, F_BONK, pitch=0)
    CH.eyes(bru, F_SHOT3 + 24, scale=1.0, look=(0, 1)); CH.mouth(bru, F_SHOT3 + 24, shape="o")
    CH.eyes(bru, F_BONK - 6, scale=1.4, look=(0, 1))
    CH.arms(bru, F_SHOT3 + 24, l=(-35, 0, 0), el_l=(-75, 0, 0), r=(8, 0, -8))

    # BONK
    CH.squash(bru, F_BONK, depth=0.28, recover=12)
    C.key(helmet, F_BONK - 1, loc=(0, 0, d_bru["head_r"] * 0.5))
    C.key(helmet, F_BONK + 4, loc=(0, 0, d_bru["head_r"] * 0.5 + 0.35))
    C.key(helmet, F_BONK + 10, loc=(0, 0, d_bru["head_r"] * 0.5 - 0.05))
    C.key(helmet, F_BONK + 14, loc=(0, 0, d_bru["head_r"] * 0.5))
    CH.eyes(bru, F_BONK + 2, scale=0.7, look=(0.6, 0.2)); CH.eyes(bru, F_BONK + 8, scale=1.0, look=(-0.6, 0.2))
    CH.mouth(bru, F_BONK + 2, shape="flat")
    sfx(F_BONK, "bonk", 1.0)
    sfx(F_BONK + 3, "ding", 0.5)
    say(472, "Bullseye.")

    # dizzy stars orbit the head, head wobbles
    orbit = C.empty("fx.orbit", parent=bru["head"], loc=(0, 0, d_bru["head_r"] * 1.55), col=fx_col)
    for i in range(3):
        a = math.radians(i * 120)
        P.star(f"fx.star{i}", size=0.11, parent=orbit, loc=(math.cos(a) * 0.45, math.sin(a) * 0.45, 0), col=fx_col)
    C.visible(orbit, 1, False); C.visible(orbit, F_BONK + 2, True); C.visible(orbit, F_JIG0, False)
    C.key(orbit, F_BONK + 2, rot=(0, 0, 0)); C.key(orbit, F_JIG0, rot=(0, 0, 360 * 3), interp="LINEAR")
    C.set_interp_all(orbit, "LINEAR", "rotation_euler")
    for i, f in enumerate(range(F_BONK + 2, F_JIG0, 6)):
        CH.head_turn(bru, f, roll=14 if i % 2 else -14)
    CH.head_turn(bru, F_JIG0 + 4, roll=0)

    # ======================================================================= Beat E: hearts
    spawn_hearts(bru["head"], F_HEARTS0, F_HEARTS1, every=12, col=fx_col, tag="a")
    for f in range(F_HEARTS0, F_HEARTS1, 12):
        sfx(f, "pop", 0.35)

    # pupils become hearts
    for s in ("l", "r"):
        he = P.heart(f"Bruno.hearteye_{s}", size=0.17, parent=bru[f"eye_{s}"], loc=(0, -0.09, 0), col=fx_col, emit=0.6)
        C.visible(he, 1, False); C.visible(he, F_HEART_EYES, True)
        pop_in(he, F_HEART_EYES, 1.0)
        C.key(bru[f"pupil_{s}"], F_HEART_EYES - 1, scale=(1, 1, 1))
        C.key(bru[f"pupil_{s}"], F_HEART_EYES + 1, scale=(0, 0, 0))
    CH.eyes(bru, F_HEART_EYES, scale=1.3, look=(0, 0))
    CH.mouth(bru, F_HEART_EYES + 4, shape="big")
    sfx(F_HEART_EYES, "chime", 0.6)

    # shield drops
    ground_shield = P.shield("Bruno.shield.ground", r=0.34, col=fx_col)
    C.visible(ground_shield, 1, False)
    drop_from = C.world_pos(shield, F_DROP_SHIELD)
    C.visible(shield, F_DROP_SHIELD, False); C.visible(ground_shield, F_DROP_SHIELD, True)
    C.key(ground_shield, F_DROP_SHIELD, loc=drop_from, rot=(0, 30, 0))
    C.key(ground_shield, F_DROP_SHIELD + 8, loc=(drop_from.x - 0.3, drop_from.y - 0.35, 0.03), rot=(0, 0, 25))
    C.key(ground_shield, F_DROP_SHIELD + 12, loc=(drop_from.x - 0.35, drop_from.y - 0.4, 0.12), rot=(0, 0, 25))
    C.key(ground_shield, F_DROP_SHIELD + 16, loc=(drop_from.x - 0.38, drop_from.y - 0.42, 0.03), rot=(0, 0, 25))
    sfx(F_DROP_SHIELD + 8, "thud", 0.5)

    # love jig: sway + open arms
    for i, f in enumerate(range(F_JIG0, F_JIG1, 8)):
        C.key(bru["hips"], f, rot=(0, 12 if i % 2 else -12, 0), loc=(0, 0, leg + (0.06 if i % 2 else 0)))
    C.key(bru["hips"], F_JIG1 + 2, rot=(0, 0, 0), loc=(0, 0, leg))
    CH.arms(bru, F_JIG0, l=(-35, 0, 0), el_l=(-75, 0, 0), r=(8, 0, -8))
    CH.arms(bru, F_JIG0 + 10, l=(-60, 55, 0), el_l=(0, 0, 0), r=(-60, -55, 0), el_r=(0, 0, 0))
    CH.arms(bru, F_CHASE0, l=(-80, 30, 0), el_l=(0, 0, 0), r=(-80, -30, 0), el_r=(0, 0, 0))
    CH.head_turn(bru, F_JIG0 + 10, roll=10, pitch=5)
    say(540, "Mission... accomplished?")

    # Bruno runs at Pip with open arms
    C.cut(F_CHASE0 - 4, cam_wide)
    CH.walk(bru, F_CHASE0, F_CHASE1, (BRUNO_X, 0), (-0.9, 0), stride=6, amp=30, bob=0.05, run=True, swing_arms=False)
    for f in range(F_CHASE0, F_CHASE1, 6):
        sfx(f, "step", 0.45)

    # ======================================================================= Beat F: flee
    C.cut(F_PIP_SCARED - 6, cam_pip)
    CH.arms(pip, F_PIP_SCARED - 10, l=(-60, 0, 0), el_l=(-20, 0, 0), r=(-40, 0, 0), el_r=(-30, 0, 0))
    CH.arms(pip, F_PIP_SCARED, l=(-120, 40, 0), el_l=(-20, 0, 0), r=(-120, -40, 0), el_r=(-20, 0, 0))
    CH.head_turn(pip, F_PIP_SCARED, pitch=0)
    CH.eyes(pip, F_PIP_SCARED - 6, scale=1.0, look=(0.3, 0))
    CH.eyes(pip, F_PIP_SCARED, scale=1.7, look=(0.8, 0.2))
    CH.mouth(pip, F_PIP_SCARED, shape="big")
    C.key(pip["hips"], F_PIP_SCARED, loc=(0, 0, d_pip["leg"]))
    C.key(pip["hips"], F_PIP_SCARED + 3, loc=(0, 0, d_pip["leg"] + 0.25))
    C.key(pip["hips"], F_PIP_SCARED + 8, loc=(0, 0, d_pip["leg"]))
    sfx(F_PIP_SCARED, "boing", 0.7)

    C.cut(F_PIP_TURN, cam_chase)
    C.key(cam_chase, F_PIP_TURN, loc=(-2.0, -6.5, 1.8), interp="LINEAR")
    C.key(cam_chase, F_BRUNO_RUN1, loc=(-7.0, -6.5, 1.8), interp="LINEAR")
    CH.face(pip, F_PIP_TURN, 90); CH.face(pip, F_PIP_RUN0, -90)
    CH.arms(pip, F_PIP_RUN0, l=(-40, 0, 0), el_l=(-60, 0, 0), r=(-40, 0, 0), el_r=(-60, 0, 0))
    CH.walk(pip, F_PIP_RUN0, F_PIP_RUN1, (PIP_X, 0), (-9.5, 0), stride=5, amp=34, bob=0.05, run=True, swing_arms=False)
    P.flap_wings(wings, F_PIP_RUN0, F_PIP_RUN1, period=4, amp=45)
    CH.walk(bru, F_CHASE1, F_BRUNO_RUN1, (-0.9, 0), (-10.5, 0), stride=6, amp=30, bob=0.05, run=True, swing_arms=False)
    spawn_hearts(bru["head"], F_CHASE1, F_BRUNO_RUN1 - 30, every=10, rise=1.4, col=fx_col, tag="b")
    for f in range(F_PIP_RUN0, F_BRUNO_RUN1, 6):
        sfx(f, "step", 0.35)
    say(716, "Love hurts.")

    # end card
    C.cut(F_END_CARD - 4, cam_end)
    t1 = P.sign("Title", "CUPID HAD" + chr(10) + "ONE JOB", loc=(0, 2, 3.6), size=0.8, col=fx_col)
    t2 = P.sign("Credit", "made in Blender  x  Claude", loc=(0, 2, 2.45), size=0.27, color="#ffe26a", col=fx_col)
    for t, f in ((t1, F_END_CARD), (t2, F_END_CARD + 14)):
        C.visible(t, 1, False); C.visible(t, f, True)
        pop_in(t, f, 1.0, frames=8)
    sfx(F_END_CARD, "chime", 0.8)

    # ----------------------------------------------------------------- render + cue sheet
    C.render_settings(frame_end=FRAME_END, quality="preview")
    scene.camera = cam_wide
    out = {
        "fps": FPS, "frames": FRAME_END, "voice": VOICE,
        "sfx": sorted(cues, key=lambda c: c["frame"]),
        "lines": sorted(lines, key=lambda l: l["frame"]),
        "music": {"file": "music.wav", "gain": 0.16},
    }
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cues.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"[cupid] built: {len(bpy.data.objects)} objects, {FRAME_END} frames, {len(cues)} sfx, {len(lines)} lines")


if __name__ == "__main__":
    build()
