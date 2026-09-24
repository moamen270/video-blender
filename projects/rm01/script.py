"""RM01 screen test: Rick and Morty cut-out puppets in the garage — rig, acting, lip sync, cuts.

Placeholder Kokoro voices (casting comes later). Beats:
  r1  Rick hands Morty a remote: "Morty, hold this. And whatever you do, don't press the red button."
  m1  Morty, worried: "W-wait, Rick, what does the red button do?"
  r2  Rick, deadpan: "It's red, Morty. Red means don't."
  tag Morty looks down at the remote; his thumb creeps toward the button. Rick's eyes snap to him.
"""
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

import kit.cutout as K
import studio.core as C

FPS = C.FPS
MORTY_X, RICK_X = -0.40, 0.42


def build() -> None:
    C.reset_scene()
    K.backdrop("garage", depth=1.0)
    morty = K.Puppet("morty", loc=(MORTY_X, 0.0), depth=-0.3)
    rick = K.Puppet("rick", loc=(RICK_X, 0.0), depth=0.0)

    man = json.load(open(os.path.join(ROOT, "projects", "rm01", "voice", "manifest.json"), encoding="utf-8"))["lines"]

    def n_frames(lid: str) -> int:
        return math.ceil(man[lid]["seconds"] * FPS)

    R1 = 14
    M1 = R1 + n_frames("r1") + 8
    R2 = M1 + n_frames("m1") + 10
    TAG = R2 + n_frames("r2") + 6
    END = TAG + 64

    def wf(lid: str, start: int, word: str, which: int = 0) -> int:
        """Frame where `word` (case/punctuation-insensitive) starts in line `lid` placed at `start`."""
        hits = [w for w in man[lid]["words"] if w["w"].strip(",.?!").lower() == word.lower()]
        return start + int(round(hits[which]["start"] * FPS))

    # ------------------------------------------------------------ idle life
    morty.breathe(1, END, period=2.8)
    rick.breathe(1, END, period=3.6)
    morty.auto_blink(1, END, seed=3)
    rick.auto_blink(1, END - 70, seed=8, every=(2.8, 5.0))   # none during the tag glare
    morty.look(1, 20, 0)          # both look at each other from the start
    rick.look(1, -13, -3)
    rick.brows(1, 6, 0)          # Rick's resting face: slightly annoyed

    # ------------------------------------------------------------ r1: the handover
    rick.lipsync(man["r1"]["cues"], R1)
    remote_rick = rick.prop("remote", "hand.L", at=(0, -22), deg=0, z=18.6, visible_from=1)
    rick.hand("L", "fist", 1)
    # reach out on "hold" with a small anticipation
    f_hold = wf("r1", R1, "hold")
    meet = (0.02, 0.70)                     # where the hands meet (world x, z)
    rick.rot("sleeve.L", f_hold - 8, 0)
    rick.rot("forearm.L", f_hold - 8, 0)
    rick.rot("sleeve.L", f_hold - 4, 6)     # anticipation: a small pull back
    rick.reach("L", f_hold + 6, (meet[0] - 0.02, meet[1] + 0.03), bend=1)   # overshoot
    rick.reach("L", f_hold + 10, meet, bend=1)
    rick.rot("head", f_hold - 2, 0)
    rick.rot("head", f_hold + 4, 4)
    # Morty takes it on "this"
    f_this = wf("r1", R1, "this")
    morty.rot("sleeve.R", f_this - 6, 0)
    morty.rot("forearm.R", f_this - 6, 0)
    morty.reach("R", f_this + 4, meet, bend=-1)
    morty.look(f_this - 4, 14, -18)           # glance at the remote
    f_swap = f_this + 6
    remote_morty = morty.prop("remote", "hand.R", at=(0, -22), deg=0, z=14.6, visible_from=f_swap)
    C.visible(remote_rick, f_swap, False)
    morty.hand("R", "fist", f_swap)
    rick.hand("L", "open", f_swap)
    # arms settle: Rick pulls back, Morty holds it in front of his chest
    rick.reach("L", f_swap + 3, meet, bend=1)
    rick.rot("sleeve.L", f_swap + 12, -4)
    rick.rot("forearm.L", f_swap + 12, 0)
    morty.reach("R", f_swap + 3, meet, bend=-1)
    morty.reach("R", f_swap + 14, (MORTY_X + 0.17, 0.58), bend=-1)
    morty.look(f_swap + 8, 20, 0)
    rick.rot("head", f_swap + 10, 0)
    # the warning: brows down, lean in, finger up on "don't"
    f_and = wf("r1", R1, "and")
    f_dont = wf("r1", R1, "don't")
    f_red = wf("r1", R1, "red")
    rick.brows(f_and, 6, 0)
    rick.brows(f_and + 6, 22, -3)
    rick.rot("head", f_and + 2, 0)
    rick.rot("head", f_and + 8, 5)          # leans toward Morty
    rick.rot("sleeve.R", f_dont - 8, 0)
    rick.rot("forearm.R", f_dont - 8, 0)
    rick.rot("sleeve.R", f_dont + 2, 125)   # finger up
    rick.rot("forearm.R", f_dont + 2, 50)
    rick.hand("R", "point", f_dont - 2)
    rick.rot("sleeve.R", f_red, 121)        # small beats on "red" / "button"
    rick.rot("sleeve.R", f_red + 4, 128)
    rick.rot("sleeve.R", f_red + 9, 124)
    morty.brows(f_dont - 4, 0, 0)
    morty.brows(f_dont + 4, -18, 6)         # Morty gets worried
    r1_end = R1 + n_frames("r1")
    rick.rot("sleeve.R", r1_end + 4, 124)
    rick.rot("forearm.R", r1_end + 4, 50)
    rick.rot("sleeve.R", r1_end + 14, 0)
    rick.rot("forearm.R", r1_end + 14, 0)
    rick.hand("R", "open", r1_end + 12)
    rick.rot("head", r1_end + 4, 5)
    rick.rot("head", r1_end + 14, 0)

    # ------------------------------------------------------------ m1: Morty's question
    morty.lipsync(man["m1"]["cues"], M1)
    f_wait = wf("m1", M1, "w-wait")
    f_rick = wf("m1", M1, "rick")
    f_do = wf("m1", M1, "do")
    morty.rot("head", f_wait - 2, 0)
    morty.rot("head", f_wait + 3, -4)       # flinch back
    morty.rot("head", f_rick + 2, 3)
    morty.rot("sleeve.L", f_rick - 4, 0)
    morty.rot("forearm.L", f_rick - 4, 0)
    morty.rot("sleeve.L", f_rick + 6, -38)  # free hand out: "what does it do?"
    morty.rot("forearm.L", f_rick + 6, -45)
    morty.hand("L", "open", 1)
    morty.brows(f_do - 2, -18, 6)
    morty.brows(f_do + 3, -24, 10)          # peak worry on "do?"
    morty.rot("head", f_do + 3, 5)
    m1_end = M1 + n_frames("m1")
    morty.rot("sleeve.L", m1_end + 10, -30)
    morty.rot("forearm.L", m1_end + 10, -35)
    rick.brows(M1 + 4, 22, -3)
    rick.brows(M1 + 12, 10, 0)              # Rick: unimpressed

    # ------------------------------------------------------------ r2: deadpan answer
    rick.lipsync(man["r2"]["cues"], R2)
    f_red2 = wf("r2", R2, "red", 1)
    f_means = wf("r2", R2, "means")
    rick.rot("head", f_red2 - 2, 0)
    rick.rot("head", f_red2 + 4, -3)
    rick.rot("head", f_means + 6, 2)
    morty.rot("sleeve.L", R2 + 4, -30)
    morty.rot("sleeve.L", R2 + 12, 0)
    morty.rot("forearm.L", R2 + 4, -35)
    morty.rot("forearm.L", R2 + 12, 0)
    morty.brows(R2 + 30, -12, 3)

    # ------------------------------------------------------------ tag: temptation
    morty.look(TAG, 20, 0)
    morty.look(TAG + 6, 10, -22)             # eyes drop to the remote
    morty.brows(TAG + 6, -6, 0)
    morty.rot("head", TAG + 2, 0)
    morty.rot("head", TAG + 10, -6)
    morty.reach("R", TAG + 10, (MORTY_X + 0.17, 0.58), bend=-1)
    morty.reach("R", TAG + 26, (MORTY_X + 0.13, 0.64), bend=-1)   # lifts it to look closer
    rick.look(TAG + 20, -13, -3)
    rick.look(TAG + 24, -13, -10)             # Rick's eyes snap to the remote
    rick.brows(TAG + 24, 10, 0)
    rick.brows(TAG + 28, 28, -4)
    rick.squash("eye.L", TAG + 24, 1.0, 1.0)
    rick.squash("eye.R", TAG + 24, 1.0, 1.0)
    rick.squash("eye.L", TAG + 28, 1.0, 0.55)   # narrow glare
    rick.squash("eye.R", TAG + 28, 1.0, 0.55)
    morty.look(TAG + 34, 22, 4)             # Morty notices Rick staring
    morty.brows(TAG + 34, -26, 10)
    morty.swap("mouth", "E", TAG + 36)
    morty.swap("mouth", "X", TAG + 48)

    K.set_linear_constant_bools()

    # ------------------------------------------------------------ cameras (ortho, 9:16)
    two = K.ortho_camera("cam_two", (0.0, 1.20), 2.9)
    rick_mcu = K.ortho_camera("cam_rick", (RICK_X - 0.05, 1.50), 1.9)
    morty_mcu = K.ortho_camera("cam_morty", (MORTY_X + 0.08, 0.95), 1.5)
    tag_cam = K.ortho_camera("cam_tag", (0.0, 1.20), 2.9)
    K.key_camera(tag_cam, TAG, (0.0, 1.20), 2.9)
    K.key_camera(tag_cam, END, (-0.04, 1.18), 2.45)          # slow push-in for the tag
    C.cut(1, two)
    C.cut(f_and - 3, rick_mcu)
    C.cut(M1 - 3, morty_mcu)
    C.cut(R2 - 4, two)
    C.cut(TAG, tag_cam)

    bpy.context.scene.frame_end = END

    cues = {
        "fps": FPS, "frames": END,
        "music": {"file": "F:/PoCs/blender-video/assets/library/music/Mystery Sax.mp3", "start_s": 0, "gain": 0.12},
        "lines": [{"id": lid, "frame": f, "text": man[lid]["text"], "wav": man[lid]["wav"]}
                  for lid, f in (("r1", R1), ("m1", M1), ("r2", R2))],
        "sfx": [], "overlays": [],
    }
    with open(os.path.join(ROOT, "projects", "rm01", "cues.json"), "w", encoding="utf-8") as fh:
        json.dump(cues, fh, indent=1)
