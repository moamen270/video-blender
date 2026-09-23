"""SAMURAI DUEL — 28 s vertical short.

A 3D toon-shaded samurai standoff and duel between the Ronin and the Warlord in a moonlit bamboo grove.
"""
from __future__ import annotations

import dataclasses
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy
from bpy.types import Object
from mathutils import Vector

from kit import fx, pose as P, samurai, stage
from studio import core as C

FPS = 24
FRAME_END = 672

# Frame constants block for scenes 1-2
F_EYES_OPEN0 = 3
F_EYES_OPEN1 = 5
F_WIDE = 25
F_WIDE_END = 60
F_DRAW_W0 = 62
F_DRAW_W_MID = 67
F_DRAW_W1 = 74
F_TWO = 79
F_DRAW_R0 = 80
F_DRAW_R_MID = 85
F_DRAW_R1 = 92
F_SCENE3 = 97
F_SCENE6 = 385


def new_cues() -> dict:
    return {
        "fps": 24,
        "frames": 672,
        "music": {
            "file": "F:/PoCs/video-builder/assets/music/japan-duel.wav",
            "gain": 0.22,
            "cut_frame": 400,
            "resume_frame": 0,
            "end_frame": 600,
        },
        "lines": [
            {
                "id": "honor",
                "frame": 536,
                "text": "You fought with honor.",
                "engine": "chatterbox",
                "voiceRef": "F:/PoCs/video-builder/assets/voices/lewis.wav",
                "emotion": 0.4,
                "speed": 0.9,
            },
            {
                "id": "cta",
                "frame": 606,
                "text": "Follow Dummy Sticky for more.",
                "engine": "kokoro",
                "voice": "am_michael",
            },
        ],
        "sfx": [],
        "contacts": [],
        "overlays": [
            {"kind": "text", "text": "Two blades. One honor.", "from": 3, "to": 56, "y": 0.18, "size": 86},
            {"kind": "fill", "color": "white", "from": 404, "to": 405},
            {"kind": "fill", "color": "black", "from": 592, "to": 672},
            {"kind": "text", "text": "Follow Dummy Sticky for more.", "from": 606, "to": 672, "y": 0.45, "size": 70},
            {"kind": "text", "text": "@DummySticky", "from": 612, "to": 672, "y": 0.53, "size": 56},
            {"kind": "text", "text": "@DummySticky", "from": 25, "to": 591, "y": 0.95, "size": 34, "alpha": 0.6},
        ],
    }


cues: dict = new_cues()


def sfx(cues: dict, frame: int, name: str, gain: float) -> None:
    cues["sfx"].append({"frame": frame, "sfx": name, "gain": gain})


def pose_with(name: str, **changes) -> P.Pose:
    return dataclasses.replace(P.POSES[name], **changes)


RONIN_KEYS = [
 (97,'chudan',0,0.0,'BEZIER'), (110,'chudan',0,0.25,'BEZIER'), (122,'block_high',0,0.25,'BEZIER'), (128,'C1',0,0.25,'BEZIER'), (131,'C1',0,0.25,'BEZIER'), (142,'chudan',0,0.25,'BEZIER'), (150,'chudan',0,0.30,'BEZIER'), (156,'slash_windup',0,0.35,'LINEAR'), (162,'C2',0,0.55,'BEZIER'), (165,'C2',0,0.55,'BEZIER'), (176,'chudan',0,0.30,'BEZIER'), (193,'chudan',0,0.30,'BEZIER'), (207,'jodan',0,0.35,'LINEAR'), (212,'C3',0,0.65,'BEZIER'), (215,'C3',0,0.65,'BEZIER'), (226,'chudan',0,0.40,'BEZIER'), (228,'chudan',0,0.40,'BEZIER'), (236,'dodge_side',-0.35,0.40,'BEZIER'), (240,'dodge_side',-0.35,0.40,'BEZIER'), (248,'chudan',0,0.40,'BEZIER'), (258,'slash_windup',0,0.45,'LINEAR'), (266,'C4',0,0.70,'BEZIER'), (269,'C4',0,0.70,'BEZIER'), (282,'chudan',0,0.40,'BEZIER'), (301,'chudan',0,0.40,'BEZIER'), (316,'parry',0,0.40,'BEZIER'), (320,'C5',0,0.40,'BEZIER'), (323,'C5',0,0.40,'BEZIER'), (332,'chudan',0,0.40,'BEZIER'), (340,'thrust_windup',0,0.35,'LINEAR'), (348,'thrust_hit',0,0.75,'BEZIER'), (352,'thrust_hit',0,0.75,'BEZIER'), (372,'chudan',0,0.0,'BEZIER'), (384,'chudan',0,0.0,'BEZIER')]
WARLORD_KEYS = [
 (97,'chudan',0,0.0,'BEZIER'), (106,'chudan',0,0.55,'BEZIER'), (114,'chudan',0,1.10,'BEZIER'), (122,'jodan',0,1.20,'LINEAR'), (128,'C1',0,1.25,'BEZIER'), (131,'C1',0,1.25,'BEZIER'), (142,'chudan',0,1.00,'BEZIER'), (157,'parry',0,1.00,'BEZIER'), (162,'C2',0,1.00,'BEZIER'), (165,'C2',0,1.00,'BEZIER'), (176,'chudan',0,0.90,'BEZIER'), (193,'chudan',0,0.90,'BEZIER'), (207,'block_high',0,0.90,'BEZIER'), (212,'C3',0,0.90,'BEZIER'), (215,'C3',0,0.90,'BEZIER'), (222,'chudan',0,0.90,'BEZIER'), (230,'thrust_windup',0,0.85,'LINEAR'), (238,'thrust_hit',0,1.35,'BEZIER'), (242,'thrust_hit',0,1.35,'BEZIER'), (250,'chudan',0,1.00,'BEZIER'), (260,'block_mid',0,1.00,'BEZIER'), (266,'C4',0,0.95,'BEZIER'), (269,'C4',0,0.95,'BEZIER'), (282,'chudan',0,0.80,'BEZIER'), (301,'chudan',0,0.80,'BEZIER'), (314,'jodan',0,0.90,'LINEAR'), (320,'C5',0,1.25,'BEZIER'), (323,'C5',0,1.25,'BEZIER'), (334,'stagger',0,1.00,'BEZIER'), (346,'dodge_back',0,0.70,'BEZIER'), (350,'dodge_back',0,0.70,'BEZIER'), (372,'chudan',0,0.0,'BEZIER'), (384,'chudan',0,0.0,'BEZIER')]
CLASHES = {  # id: (frame, attacker, defender, attacker_pose, attacker_blade, defender_pose, defender_blade, height, big, windup_frame)
 'C1': (128, 'warlord', 'ronin', 'overhead_hit', (20,0,0), 'block_high', (10,-80,0), 1.55, False, 122),
 'C2': (162, 'ronin', 'warlord', 'slash_hit', (10,-40,0), 'parry', (45,-60,0), 1.35, False, 156),
 'C3': (212, 'ronin', 'warlord', 'overhead_hit', (20,0,0), 'block_high', (10,-80,0), 1.55, False, 207),
 'C4': (266, 'ronin', 'warlord', 'slash_hit', (10,-40,0), 'block_mid', (70,-15,0), 1.25, True, 258),
 'C5': (320, 'warlord', 'ronin', 'overhead_hit', (20,0,0), 'parry', (45,-60,0), 1.45, False, 314)}
MISSES = [(238, 'warlord', 230), (348, 'ronin', 340)]  # (frame, attacker, windup_frame): thrusts that miss


def solve_clashes(arms: dict, cues) -> dict:
    bpy.context.view_layer.update()
    solved = {}
    table_map = {"ronin": RONIN_KEYS, "warlord": WARLORD_KEYS}
    for cid, row in CLASHES.items():
        frame, attacker, defender, attacker_pose, attacker_blade, defender_pose, defender_blade, height, big, windup_frame = row
        att_arm = arms[attacker]
        dfn_arm = arms[defender]

        att_row = next(r for r in table_map[attacker] if r[0] == frame and r[1] == cid)
        att_mover = (att_row[2], att_row[3])
        dfn_row = next(r for r in table_map[defender] if r[0] == frame and r[1] == cid)
        dfn_mover = (dfn_row[2], dfn_row[3])

        att_w = P.to_world(att_arm, (att_mover[0], att_mover[1], 0))
        dfn_w = P.to_world(dfn_arm, (dfn_mover[0], dfn_mover[1], 0))
        d = att_w - dfn_w
        d.z = 0
        d.normalize()
        M = dfn_w + d * 0.40
        M.z = height

        att_grip = P.sword_through(
            P.to_local(att_arm, M) - Vector((att_mover[0], att_mover[1], 0)),
            attacker_blade,
            0.75,
        )
        dfn_grip = P.sword_through(
            P.to_local(dfn_arm, M) - Vector((dfn_mover[0], dfn_mover[1], 0)),
            defender_blade,
            0.50,
        )

        att_pose = pose_with(attacker_pose, grip=att_grip, blade=attacker_blade)
        dfn_pose = pose_with(defender_pose, grip=dfn_grip, blade=defender_blade)

        for side, arm, pose in (("att", att_arm, att_pose), ("dfn", dfn_arm, dfn_pose)):
            try:
                P.reach_ok(arm, pose)
            except ValueError as e:
                print(f"[reach] {cid} {side}: {e}", flush=True)

        solved[(cid, "att")] = att_pose
        solved[(cid, "dfn")] = dfn_pose

        fx.spark(M, frame, seed=int(cid[1]))
        sfx(cues, frame, "sword_clash", 0.9)
        if big:
            sfx(cues, frame, "boom", 0.5)
        sfx(cues, windup_frame, "sword_swing", 0.6)
        cues["contacts"].append({
            "id": cid,
            "frame": frame,
            "kind": "clash",
            "point": [round(M.x, 4), round(M.y, 4), round(M.z, 4)],
            "attacker": attacker,
            "defender": defender,
        })
    return solved


def play_keys(arm, name, table, solved):
    for f, pose_name, mx, my, interp in table:
        if pose_name in CLASHES:
            side = "att" if CLASHES[pose_name][1] == name else "dfn"
            pose = solved[(pose_name, side)]
        else:
            pose = P.POSES[pose_name]
        P.key_pose(arm, pose, f, mover=(mx, my), interp=interp)


def scenes_3_5(ronin, warlord, cues):
    arms = {"ronin": ronin, "warlord": warlord}
    solved = solve_clashes(arms, cues)
    play_keys(ronin, "ronin", RONIN_KEYS, solved)
    play_keys(warlord, "warlord", WARLORD_KEYS, solved)
    for f, att, wf in MISSES:
        sfx(cues, wf, "sword_swing", 0.6)
        sfx(cues, f, "swoosh", 0.6)
    for cid, row in CLASHES.items():
        fx.smear(arms[row[1]], row[9], row[0], cid)
    for f, att, wf in MISSES:
        fx.smear(arms[att], wf, f, f"miss{f}")


def scenes_1_2(ronin: Object, warlord: Object, cues: dict) -> None:
    # Ronin draw
    P.key_pose(ronin, P.POSES["sheathed"], 1)
    P.hold(ronin, P.POSES["sheathed"], 1, F_DRAW_R0)
    C.set_interp_at(ronin, F_DRAW_R0, "LINEAR")
    P.key_pose(ronin, P.POSES["draw_mid"], F_DRAW_R_MID, interp="LINEAR")
    P.key_pose(ronin, P.POSES["chudan"], F_DRAW_R1)

    # Warlord draw
    P.key_pose(warlord, P.POSES["sheathed"], 1)
    P.hold(warlord, P.POSES["sheathed"], 1, F_DRAW_W0)
    C.set_interp_at(warlord, F_DRAW_W0, "LINEAR")
    P.key_pose(warlord, P.POSES["draw_mid"], F_DRAW_W_MID, interp="LINEAR")
    P.key_pose(warlord, P.POSES["chudan"], F_DRAW_W1)

    # Ronin eyes blink open
    for eye in ("ronin_eye.R", "ronin_eye.L"):
        o = bpy.data.objects[eye]
        closed = (o.scale.x, o.scale.y, o.scale.z * 0.1)
        opened = tuple(o.scale)
        o.scale = closed
        o.keyframe_insert("scale", frame=1)
        o.keyframe_insert("scale", frame=F_EYES_OPEN0)
        o.scale = opened
        o.keyframe_insert("scale", frame=F_EYES_OPEN1)

    # SFX
    sfx(cues, 9, "whoosh", 0.3)
    sfx(cues, F_DRAW_W0 + 1, "sword_draw", 0.75)
    sfx(cues, F_DRAW_R0 + 1, "sword_draw", 0.75)


def hold_rest(ronin: Object, warlord: Object) -> None:
    P.hold(ronin, P.POSES["chudan"], F_SCENE6, FRAME_END, mover=(0, 0.0))
    P.hold(warlord, P.POSES["chudan"], F_SCENE6, FRAME_END, mover=(0, 0.0))


def cameras(ronin: Object, warlord: Object) -> dict[str, Object]:
    cam_eyes = C.camera("cam_eyes", (-0.45, -0.05, 1.70), (-1.5, 0, 1.70), lens=50)
    cam_wide = C.camera("cam_wide", (0, -6.2, 1.0), (0, 0, 1.8), lens=28)
    C.key(cam_wide, F_WIDE, loc=(0, -6.2, 1.0))
    C.key(cam_wide, F_WIDE_END, loc=(0, -5.2, 1.0))
    cam_draw = C.camera("cam_draw", (1.0, -1.8, 1.3), (1.4, 0, 1.15), lens=35)
    cam_two = C.camera("cam_two", (0.0, -5.5, 1.3), (0.0, 0.0, 1.6), lens=30.0)

    cam_side = C.camera("cam_side", (0, -5.0, 1.1), (0, 0, 1.5), lens=32)
    cam_ots_ronin = C.camera("cam_ots_ronin", (-3.6, -1.6, 2.0), (0.4, 0, 1.2), lens=35)
    cam_ots_warlord = C.camera("cam_ots_warlord", (3.4, 1.6, 2.0), (-0.4, 0, 1.2), lens=35)

    scene = bpy.context.scene
    for f in range(97, 385, 3):
        scene.frame_set(f)
        r = ronin.matrix_world @ ronin.pose.bones["mover"].head
        w = warlord.matrix_world @ warlord.pose.bones["mover"].head
        mid_x = (r.x + w.x) / 2
        y = -5.0 if f < 355 else -5.0 + (f - 355) / (384 - 355) * 0.8
        cam_side.location = (mid_x, y, 1.1)
        cam_side.keyframe_insert("location", frame=f)

    fx.shake(cam_side, 266, 276, amp=0.06)

    C.cut(1, cam_eyes)
    C.cut(F_WIDE, cam_wide)
    C.cut(F_DRAW_W0 - 1, cam_draw)
    C.cut(F_TWO, cam_two)
    C.cut(F_SCENE3, cam_side)
    C.cut(193, cam_ots_ronin)
    C.cut(214, cam_ots_warlord)
    C.cut(266, cam_side)
    C.cut(F_SCENE6, cam_two)

    return {
        "cam_eyes": cam_eyes,
        "cam_wide": cam_wide,
        "cam_draw": cam_draw,
        "cam_two": cam_two,
        "cam_side": cam_side,
        "cam_ots_ronin": cam_ots_ronin,
        "cam_ots_warlord": cam_ots_warlord,
    }


def build() -> None:
    C.reset_scene()
    stage.build_stage()
    stage.petals()
    ronin = samurai.build_ronin()
    warlord = samurai.build_warlord()
    cues = new_cues()
    scenes_1_2(ronin, warlord, cues)
    scenes_3_5(ronin, warlord, cues)
    hold_rest(ronin, warlord)
    for arm in (ronin, warlord):
        P.auto_steps(arm, cues)
    cams = cameras(ronin, warlord)
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = FRAME_END
    cues["sfx"].sort(key=lambda c: c["frame"])
    cues_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cues.json")
    with open(cues_path, "w", encoding="utf-8") as fh:
        json.dump(cues, fh, indent=1)
    print("[samurai] built", len(cues["sfx"]), "sfx", flush=True)


if __name__ == "__main__":
    build()
