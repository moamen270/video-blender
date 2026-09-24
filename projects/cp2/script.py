"""Checkpoint 2 screen test: Batman walks in with spring cape, turns, speaks; Joker answers."""
from __future__ import annotations

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isdir(os.path.join(ROOT, "studio")):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy

import kit.cape as cape
import kit.cast as cast
import kit.face as face
import kit.look as look
import kit.motion as motion
import studio.core as C

BAT_START = (-2.5, 0.2)
BAT_STOP = (-0.40, 0.2)
JOK_AT = (0.45, 0.0)


def build() -> None:
    """Build checkpoint 2 screen test scene."""
    # 1. Environment
    C.reset_scene()
    look.store_night(target=(0.0, 0.0, 1.0))
    look.floor(size=14.0)
    C.plane(
        "wall",
        size=14.0,
        loc=(0, -3.0, 7.0),
        rot=(90, 0, 0),
        mat=look.toon2("wall", "#161b27", rim=0.0),
    )

    # 2. Characters
    bat = cast.build_batman()
    jok = cast.build_joker()
    bat.root.location = (*BAT_START, 0)
    jok.root.location = (*JOK_AT, 0)
    motion.key_root(bat, 1, loc=(*BAT_START, 0), heading=-90.0)
    motion.key_root(jok, 1, loc=(*JOK_AT, 0), heading=0.0)

    # 3. Voice manifest
    manifest_path = os.path.join(ROOT, "projects", "cp2", "voice", "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as fh:
        man = json.load(fh)["lines"]
    L1 = math.ceil(man["bat1"]["seconds"] * 24)
    L2 = math.ceil(man["jok1"]["seconds"] * 24)

    # 4. Motion
    walk_end, steps = motion.walk_to(bat, 1, BAT_STOP)
    motion.turn_to(bat, walk_end + 2, 0.0, frames=8)
    motion.play(jok, "Idle", 1, 400)

    # 5. Timeline
    LINE1 = walk_end + 18
    ANGRY = LINE1 + L1 - 10
    LINE2 = LINE1 + L1 + 14
    END = LINE2 + L2 + 18
    scene = bpy.context.scene
    scene.frame_end = END

    # 6. Faces
    face.set_expression(bat.face, "stern", 1)
    face.change_expression(bat.face, ANGRY, "stern", "angry")
    face.apply_lipsync(bat.face, man["bat1"]["cues"], LINE1)
    face.set_expression(jok.face, "smug", 1)
    face.apply_lipsync(jok.face, man["jok1"]["cues"], LINE2)
    face.auto_blink(bat.face, 1, END, [(1, "stern"), (ANGRY, "angry")], seed=1)
    face.auto_blink(jok.face, 1, END, [(1, "smug")], seed=2)

    # 7. Cameras
    cam_wide = C.camera("cam_wide", (0.0, 5.6, 1.15), (-0.2, 0.0, 0.9), lens=35)
    C.cut(1, cam_wide)

    cam_bat = C.camera("cam_bat", (-0.15, 2.3, 1.40), (-0.40, 0.2, 1.22), lens=50)
    C.cut(LINE1 - 8, cam_bat)

    cam_jok = C.camera("cam_jok", (0.20, 2.3, 1.40), (0.45, 0.0, 1.22), lens=50)
    C.cut(LINE2 - 6, cam_jok)

    cam_two = C.camera("cam_two", (0.0, 3.6, 1.30), (0.0, 0.0, 1.0), lens=40)
    C.cut(LINE2 + L2 + 8, cam_two)

    # 8. Cape bake
    cape.bake_cape(bat, 1, END)

    # 9. Cues
    cues = {
        "fps": 24,
        "frames": END,
        "music": {
            "file": "F:/PoCs/blender-video/assets/library/music/Hidden Agenda.mp3",
            "start_s": 0,
            "gain": 0.22,
        },
        "lines": [
            {
                "id": "bat1",
                "frame": LINE1,
                "text": man["bat1"]["text"],
                "wav": man["bat1"]["wav"],
            },
            {
                "id": "jok1",
                "frame": LINE2,
                "text": man["jok1"]["text"],
                "wav": man["jok1"]["wav"],
            },
        ],
        "sfx": [{"frame": f, "sfx": "step_hard", "gain": 0.35} for f in motion.foot_events(bat, 1, walk_end + 20)],
        "overlays": [],
    }
    cues_path = os.path.join(ROOT, "projects", "cp2", "cues.json")
    with open(cues_path, "w", encoding="utf-8") as fh:
        json.dump(cues, fh, indent=1)

    # 10. Print
    print(f"[cp2] walk_end={walk_end} LINE1={LINE1} LINE2={LINE2} END={END}", flush=True)


if __name__ == "__main__":
    build()
