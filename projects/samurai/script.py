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
F_EYES_OPEN0 = 8
F_EYES_OPEN1 = 10
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
    P.hold(ronin, P.POSES["chudan"], F_SCENE3, FRAME_END)
    P.hold(warlord, P.POSES["chudan"], F_SCENE3, FRAME_END)


def cameras() -> dict[str, Object]:
    cam_eyes = C.camera("cam_eyes", (-0.78, -0.05, 1.71), (-1.5, 0.0, 1.70), lens=60.0)
    cam_wide = C.camera("cam_wide", (0.0, -8.5, 1.1), (0.0, 0.0, 2.0), lens=30.0)
    C.key(cam_wide, F_WIDE, loc=(0.0, -8.5, 1.1))
    C.key(cam_wide, F_WIDE_END, loc=(0.0, -7.3, 1.1))
    cam_draw = C.camera("cam_draw", (1.2, -1.3, 1.1), (1.3, -0.1, 1.0), lens=40.0)
    cam_two = C.camera("cam_two", (0.0, -5.5, 1.3), (0.0, 0.0, 1.6), lens=30.0)

    C.cut(1, cam_eyes)
    C.cut(F_WIDE, cam_wide)
    C.cut(F_DRAW_W0 - 1, cam_draw)
    C.cut(F_TWO, cam_two)

    return {
        "cam_eyes": cam_eyes,
        "cam_wide": cam_wide,
        "cam_draw": cam_draw,
        "cam_two": cam_two,
    }


def build() -> None:
    C.reset_scene()
    stage.build_stage()
    stage.petals()
    ronin = samurai.build_ronin()
    warlord = samurai.build_warlord()
    cues = new_cues()
    scenes_1_2(ronin, warlord, cues)
    hold_rest(ronin, warlord)
    for arm in (ronin, warlord):
        P.auto_steps(arm, cues)
    cams = cameras()
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
