"""SF01 "Who Gets the Last Hadouken" — Ryu vs Ken parody, an endless ~18 s loop (owner-approved script).

Beats: white fade-in on the wind-up -> both HADOUKEN, balls meet and fizzle ("0 DAMAGE") -> stare ->
Ryu "Mine was stronger." -> Ken "No. Mine was." -> charge 2 (beach balls) -> soap-bubble pop -> eye
close-ups + drum -> charge 3 (giant balls, shake, cracks, lantern flicker) -> one tiny spark, "pip" ->
panting "...Mine." / "Mine." -> flash to white (= frame 1: the loop).

Timing comes from the voice files: each shared shout is end-aligned so both "KEN" land on the release frame.
"""
from __future__ import annotations

import json
import math
import os
import random
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isdir(os.path.join(ROOT, "studio")):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy
import numpy as np
from mathutils import Vector

from kit import cast
from kit import face as F
from kit import fight as FT
from kit import fx
from kit import post
from kit import props
from kit import look as L
import studio.core as C

FPS = 24
RYU_AT, KEN_AT = Vector((-0.70, -0.30, 0.0)), Vector((0.70, 0.50, 0.0))   # staged on a diagonal: Ryu front-left
RYU_FACE, KEN_FACE = -20.0, 250.0   # world facing (deg): toward each other, cheated 45 deg toward the camera


def active_span(wav: str) -> tuple[float, float]:
    """(first, last) second where the voice is above -40 dB of its peak."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-f", "f32le", "-ac", "1", "-ar", "24000", "-"],
                         capture_output=True, check=True).stdout
    x = np.abs(np.frombuffer(raw, dtype=np.float32))
    env = np.convolve(x, np.ones(240) / 240, mode="same")
    idx = np.where(env > env.max() * 0.01)[0]
    return idx[0] / 24000, idx[-1] / 24000


def ken_onset(wav: str) -> float:
    """Second where 'ken' starts in a shouted 'Hadouken': the quietest 20 ms (the 'k' closure) in the
    0.9 s before the voice ends, ignoring the last 15 % (measured: aligning on the voice end put KEN up to
    0.6 s early, because some takes ring on after the word)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-f", "f32le", "-ac", "1", "-ar", "24000", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    e = np.sqrt(np.convolve(x ** 2, np.ones(480) / 480, mode="same"))
    act = np.where(e > e.max() * 0.05)[0]
    z = act[-1]
    a = max(act[0], z - int(0.9 * 24000))
    seg = e[a:z]
    return (a + int(np.argmin(seg[:int(len(seg) * 0.85)]))) / 24000


def build() -> None:
    C.reset_scene()
    FT.rooftop_sunset()
    FT.sunset_lights()
    ryu = cast.build_ryu()
    ken = cast.build_ken()
    ryu.root.location, ryu.root.rotation_euler = RYU_AT, (0, 0, math.radians(RYU_FACE - 90))
    ken.root.location, ken.root.rotation_euler = KEN_AT, (0, 0, math.radians(KEN_FACE - 90))
    bpy.context.view_layer.update()
    for q in (ryu, ken):
        FT.prepare(q)

    man = json.load(open(os.path.join(ROOT, "projects", "sf01", "voice", "manifest.json"), encoding="utf-8"))["lines"]
    used = ["r_h1", "k_h1", "r_mine", "k_mine", "r_h2", "k_h2", "r_h3", "k_h3", "k_mine2", "r_mine2"]
    span = {k: active_span(man[k]["wav"]) for k in used}

    def f(sec: float) -> int:
        return int(round(sec * FPS))

    kon = {k: ken_onset(man[k]["wav"]) for k in ("r_h1", "k_h1", "r_h2", "k_h2", "r_h3", "k_h3")}

    def pair_starts(rel: int, a: str, b: str) -> tuple[int, int]:
        """Start frames so both lines' measured 'KEN' onset lands on `rel`."""
        return rel - f(kon[a]), rel - f(kon[b])

    def tail(a: str, b: str) -> int:
        """Frames the shouts ring on after 'KEN' starts."""
        return max(f(span[a][1] - kon[a]), f(span[b][1] - kon[b]))

    # ------------------------------------------------------------ timeline
    REL1 = 2 + max(f(kon["r_h1"]), f(kon["k_h1"]))
    S_R1, S_K1 = pair_starts(REL1, "r_h1", "k_h1")
    MEET1 = REL1 + 12
    L1 = MEET1 + 30                                        # Ryu: "Mine was stronger."
    L2 = L1 + f(span["r_mine"][1]) + 3                     # Ken cuts in
    CH2 = L2 + f(span["k_mine"][1]) + 6
    REL2 = CH2 + 6 + max(f(kon["r_h2"] - span["r_h2"][0]), f(kon["k_h2"] - span["k_h2"][0]))
    S_R2, S_K2 = pair_starts(REL2, "r_h2", "k_h2")
    MEET2 = REL2 + 10
    ECU_R, ECU_K = MEET2 + 10, MEET2 + 17
    CH3 = MEET2 + 26
    REL3 = CH3 + 6 + max(f(kon["r_h3"] - span["r_h3"][0]), f(kon["k_h3"] - span["k_h3"][0]))
    S_R3, S_K3 = pair_starts(REL3, "r_h3", "k_h3")
    MEET3 = REL3 + tail("r_h3", "k_h3") + 1               # the collision after "KEN!!" ends -> true silence
    L3 = MEET3 + 22                                        # Ken: "...Mine."
    L4 = L3 + f(span["k_mine2"][1] - span["k_mine2"][0]) + 6   # Ryu: "Mine."
    END = L4 + f(span["r_mine2"][1]) + 9
    bpy.context.scene.frame_end = END

    # ------------------------------------------------------------ poses
    def stance_bob(q, a: int, b: int, amp: float = 0.045, period: int = 12, pose=FT.STANCE) -> None:
        for i, fr in enumerate(range(a, b + 1, period // 2)):
            FT.key_pose(q, fr, pose, bob=amp if i % 2 == 0 else -amp)

    for q in (ryu, ken):
        FT.key_pose(q, 1, FT.CHARGE)                      # frame 1: already winding up (hook = action)
        FT.key_pose(q, REL1 - 4, FT.CHARGE)
        FT.key_pose(q, REL1, FT.THRUST)
        FT.key_pose(q, MEET1 + 4, FT.THRUST)
        stance_bob(q, MEET1 + 12, CH2 - 2)
        FT.key_pose(q, CH2 + 6, FT.CHARGE)
        FT.key_pose(q, REL2 - 3, FT.CHARGE, bob=-0.05)
        FT.key_pose(q, REL2, FT.THRUST)
        FT.key_pose(q, MEET2 + 4, FT.THRUST)
        stance_bob(q, MEET2 + 10, CH3 - 2, pose=FT.STANCE_LOW)
        FT.key_pose(q, CH3 + 6, FT.CHARGE)
        for i, fr in enumerate(range(CH3 + 8, REL3 - 2, 3)):     # straining tremble
            FT.key_pose(q, fr, FT.CHARGE, bob=-0.06 + (0.025 if i % 2 else -0.025))
        FT.key_pose(q, REL3, FT.THRUST)
        FT.key_pose(q, MEET3 + 3, FT.THRUST)
        stance_bob(q, MEET3 + 10, END, amp=0.06, period=8, pose=FT.TIRED)    # panting
    # the stare at the fizzle: heads dip toward the smoke, then turn back to each other
    for q in (ryu, ken):
        stare = FT.Pose(**{**FT.THRUST.__dict__, "head": (18, 0, 0)})
        FT.key_pose(q, MEET1 + 8, stare)
        FT.key_pose(q, MEET1 + 18, stare)

    # ------------------------------------------------------------ faces, lip sync, blinks
    sched = {ryu.name: [], ken.name: []}

    class _E:                                   # every expression change is recorded for auto_blink
        @staticmethod
        def set_expression(face, name, frame):
            q = ryu if face is ryu.face else ken
            sched[q.name].append((frame, name))
            F.set_expression(face, name, frame)
    E = _E
    E.set_expression(ryu.face, "stern", 1)
    E.set_expression(ken.face, "smug", 1)
    for q, expr in ((ryu, "angry"), (ken, "angry")):
        E.set_expression(q.face, expr, 2)
        E.set_expression(q.face, expr, REL1 + 2)
    E.set_expression(ryu.face, "deadpan", MEET1 + 6)
    E.set_expression(ken.face, "deadpan", MEET1 + 6)
    E.set_expression(ryu.face, "stern", L1 - 2)
    E.set_expression(ken.face, "smug", L2 - 2)
    for q in (ryu, ken):
        E.set_expression(q.face, "angry", CH2 + 2)
    E.set_expression(ryu.face, "suspicious", MEET2 + 4)
    E.set_expression(ken.face, "suspicious", MEET2 + 4)
    E.set_expression(ryu.face, "angry", ECU_R)
    E.set_expression(ken.face, "angry", ECU_K)
    E.set_expression(ryu.face, "deadpan", MEET3 + 6)
    E.set_expression(ken.face, "deadpan", MEET3 + 6)
    lines = [("r_h1", ryu, S_R1), ("k_h1", ken, S_K1), ("r_mine", ryu, L1), ("k_mine", ken, L2),
             ("r_h2", ryu, S_R2), ("k_h2", ken, S_K2), ("r_h3", ryu, S_R3), ("k_h3", ken, S_K3),
             ("k_mine2", ken, L3), ("r_mine2", ryu, L4)]
    for lid, q, start in lines:
        F.apply_lipsync(q.face, man[lid]["cues"], max(1, start), fps=FPS)
    F.auto_blink(ryu.face, 1, END, sorted(sched[ryu.name]), seed=5)
    F.auto_blink(ken.face, 1, END, sorted(sched[ken.name]), seed=9)

    # ------------------------------------------------------------ fireballs
    rb = FT.Fireball("ryu_ball", "#eaf6ff", "#4aa8ff")
    kb = FT.Fireball("ken_ball", "#fff4dc", "#ff8a2a")
    for b in (rb, kb):
        b.key(1, (0, 0, -5), 0.0)
        b.spin(1, END)

    def grow_at_hands(ball, q, a: int, b: int, s0: float, s1: float, pull: Vector | None = None) -> None:
        for fr in range(a, b + 1, 2):
            t = (fr - a) / max(1, b - a)
            p = FT.between_hands(q, fr)
            if pull is not None:
                p = p.lerp(pull, t * 0.85)
            ball.key(fr, p, s0 + (s1 - s0) * (t ** 1.6))

    def fly(ball, q, rel: int, meet: int, centre: Vector, size: float) -> None:
        ball.key(rel, FT.between_hands(q, rel), size)
        ball.key(meet, centre, size)

    centre = (FT.between_hands(ryu, REL1) + FT.between_hands(ken, REL1)) / 2
    # 1: normal hadoukens, meet and fizzle
    grow_at_hands(rb, ryu, 2, REL1 - 1, 0.03, 0.13)
    grow_at_hands(kb, ken, 2, REL1 - 1, 0.03, 0.13)
    fly(rb, ryu, REL1, MEET1, centre + Vector((-0.12, 0, 0)), 0.13)
    fly(kb, ken, REL1, MEET1, centre + Vector((0.12, 0, 0)), 0.13)
    for b in (rb, kb):
        b.key(MEET1 + 4, b.root.location, 0.0)
    puff = props.smoke_puff("fizzle", centre - Vector((0, 0, 0.25)), MEET1, count=6, radius=0.12, r_range=(0.05, 0.10),
                            hex_="#b8b0a8", rise=0.35, height=0.25, seed=3)
    for o in puff:                                        # gone before the close-ups (render visibility wins)
        for fr, hide in ((1, False), (MEET1 + 20, True)):
            o.hide_render = hide
            o.keyframe_insert("hide_render", frame=fr)
    # 2: beach balls, soap-bubble pop, one falling sparkle
    grow_at_hands(rb, ryu, CH2 + 6, REL2 - 1, 0.02, 0.30)
    grow_at_hands(kb, ken, CH2 + 6, REL2 - 1, 0.02, 0.30)
    c2 = (FT.between_hands(ryu, REL2) + FT.between_hands(ken, REL2)) / 2
    fly(rb, ryu, REL2, MEET2, c2 + Vector((-0.28, 0, 0)), 0.30)
    fly(kb, ken, REL2, MEET2, c2 + Vector((0.28, 0, 0)), 0.30)
    for b in (rb, kb):
        b.key(MEET2 + 1, b.root.location, 0.34)
        b.key(MEET2 + 3, b.root.location, 0.0)
    spark_m = FT.emit_mat("sparkle", "#fffbe0", 3.0)
    sp = C.icosphere("sparkle2", r=0.025, subdiv=1, mat=spark_m)
    sp.location = c2 + Vector((0, 0, 0.1))
    sp.scale = (0, 0, 0)
    sp.keyframe_insert("scale", frame=MEET2 + 1)
    sp.scale = (1, 1, 1)
    sp.keyframe_insert("scale", frame=MEET2 + 3)
    sp.keyframe_insert("location", frame=MEET2 + 3)
    sp.location = c2 + Vector((0.05, 0, -0.35))
    sp.keyframe_insert("location", frame=MEET2 + 18)
    sp.scale = (0, 0, 0)
    sp.keyframe_insert("scale", frame=MEET2 + 20)
    # 3: giant balls bulging into each other; everything cuts at the meet; one tiny spark drifts down
    c3 = (FT.between_hands(ryu, REL3) + FT.between_hands(ken, REL3)) / 2
    grow_at_hands(rb, ryu, CH3 + 6, REL3 - 1, 0.02, 0.58, pull=c3 + Vector((-0.45, 0, 0.25)))
    grow_at_hands(kb, ken, CH3 + 6, REL3 - 1, 0.02, 0.58, pull=c3 + Vector((0.45, 0, 0.25)))
    rb.key(MEET3, c3 + Vector((-0.34, 0, 0.25)), 0.62)
    kb.key(MEET3, c3 + Vector((0.34, 0, 0.25)), 0.62)
    for b in (rb, kb):
        b.key(MEET3 + 1, b.root.location, 0.0)
    tiny = C.icosphere("tiny_spark", r=0.018, subdiv=1, mat=spark_m)
    tiny.location = c3 + Vector((0, 0, 0.3))
    tiny.scale = (0, 0, 0)
    tiny.keyframe_insert("scale", frame=MEET3)
    tiny.scale = (1, 1, 1)
    tiny.keyframe_insert("scale", frame=MEET3 + 1)
    tiny.keyframe_insert("location", frame=MEET3 + 1)
    for i, fr in enumerate(range(MEET3 + 5, MEET3 + 26, 5)):              # snowflake drift
        tiny.location = c3 + Vector((0.05 * (1 if i % 2 else -1), 0, 0.3 - 0.07 * (i + 1)))
        tiny.keyframe_insert("location", frame=fr)
    tiny.scale = (0, 0, 0)
    tiny.keyframe_insert("scale", frame=MEET3 + 28)
    # floor cracks under each fighter during charge 3
    crack_m = L.toon2("crack", "#2a1a12", rim=0.0)
    rng = random.Random(4)
    for q, at in ((ryu, RYU_AT), (ken, KEN_AT)):
        for i in range(5):
            ang = rng.uniform(0, math.pi)
            cr = C.cube(f"crack_{q.name}_{i}", size=1, loc=(at.x + rng.uniform(-0.3, 0.3), at.y + rng.uniform(-0.3, 0.3), 0.012),
                        rot=(0, 0, math.degrees(ang)), scale=(0.0, 0.02, 0.005), mat=crack_m)
            cr.keyframe_insert("scale", frame=CH3 + 10 + i * 4)
            cr.scale = (rng.uniform(0.4, 0.9), 0.02, 0.005)
            cr.keyframe_insert("scale", frame=CH3 + 14 + i * 4)
    # lanterns flicker hard during charge 3
    lan = bpy.data.materials["lantern"].node_tree.nodes["Emission"].inputs["Strength"]
    lan.keyframe_insert("default_value", frame=CH3)
    for i, fr in enumerate(range(CH3 + 4, MEET3, 3)):
        lan.default_value = 0.4 if i % 2 else 3.0
        lan.keyframe_insert("default_value", frame=fr)
    lan.default_value = 1.6
    lan.keyframe_insert("default_value", frame=MEET3 + 1)

    # ------------------------------------------------------------ cameras (auto-framed on the pose at that frame)
    from kit import shots as SH
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1920          # framing fits this aspect
    both = [ryu, ken]
    cam_open = SH.frame("cam_open", both, shot="full", yaw=172, pitch=6, at=REL1 + 2, lens=30, side_offset=0.12)
    cam_wide = SH.frame("cam_wide", both, shot="full", yaw=176, pitch=8, at=MEET1 + 14, lens=30, side_offset=0.12)
    cam_cu_r = SH.frame("cam_cu_ryu", ryu, shot="close", yaw=-112, pitch=4, at=L1 + 4)
    cam_cu_k = SH.frame("cam_cu_ken", ken, shot="close", yaw=162, pitch=4, at=L2 + 4)
    cam_ch2 = SH.frame("cam_ch2", both, shot="full", yaw=172, pitch=10, at=REL2 - 2, lens=30, side_offset=0.12)
    cam_ecu_r = SH.frame("cam_ecu_ryu", ryu, shot="ecu", yaw=-108, pitch=2, at=ECU_R + 2)
    cam_ecu_k = SH.frame("cam_ecu_ken", ken, shot="ecu", yaw=160, pitch=2, at=ECU_K + 2)
    cam_mega = SH.frame("cam_mega", [ryu, ken, rb.shell, kb.shell], shot="full", yaw=174, pitch=14, at=REL3 - 3, lens=26, side_offset=0.12)
    cam_end = SH.frame("cam_end", both, shot="full", yaw=176, pitch=6, at=L3 + 4, lens=32, side_offset=0.12)
    C.cut(1, cam_open)
    C.cut(MEET1 + 6, cam_wide)
    C.cut(L1 - 4, cam_cu_r)
    C.cut(L2 - 3, cam_cu_k)
    C.cut(CH2 - 2, cam_ch2)
    C.cut(ECU_R, cam_ecu_r)
    C.cut(ECU_K, cam_ecu_k)
    C.cut(CH3 - 1, cam_mega)
    C.cut(MEET3 + 8, cam_end)
    fx.shake(cam_mega, CH3 + 10, MEET3, amp=0.05, seed=7)

    # ------------------------------------------------------------ post: glow + loop flash
    mix = post.setup(threshold=0.9, strength=0.55, size=0.35)
    post.flash(mix, 1, 1.0)
    post.flash(mix, 7, 0.0)
    post.flash(mix, END - 7, 0.0)
    post.flash(mix, END, 1.0)

    # ------------------------------------------------------------ cue sheet (voices, SFX, HUD)
    cue_lines = [{"id": lid, "frame": max(1, st), "text": man[lid]["text"], "wav": man[lid]["wav"]} for lid, _, st in lines]
    sfx = [
        {"frame": REL1, "sfx": "hado_fire", "gain": 0.8}, {"frame": REL1 + 1, "sfx": "hado_fire", "gain": 0.7},
        {"frame": MEET1, "sfx": "fizzle", "gain": 0.6},
        {"frame": CH2 + 6, "sfx": "charge_hum", "gain": 0.5}, {"frame": CH2 + 26, "sfx": "charge_hum", "gain": 0.6},
        {"frame": REL2, "sfx": "hado_fire", "gain": 0.9}, {"frame": MEET2, "sfx": "bubble_pop", "gain": 0.9},
        {"frame": ECU_R, "sfx": "drum_hit", "gain": 0.9}, {"frame": ECU_K, "sfx": "drum_hit", "gain": 0.9},
        {"frame": CH3 + 6, "sfx": "mega_rumble", "gain": 0.35, "dur": (MEET3 - CH3 - 6) / FPS},
        {"frame": MEET3 + 12, "sfx": "pip", "gain": 0.8},
    ]
    gold, dark = "#f2c200", "#1b1b1f"
    hud = [
        {"kind": "box", "x": 0.05, "y": 0.055, "w": 0.38, "h": 0.024, "color": dark, "from": 1, "to": END},
        {"kind": "box", "x": 0.57, "y": 0.055, "w": 0.38, "h": 0.024, "color": dark, "from": 1, "to": END},
        {"kind": "box", "x": 0.055, "y": 0.058, "w": 0.37, "h": 0.018, "color": gold, "from": 1, "to": END},
        {"kind": "box", "x": 0.575, "y": 0.058, "w": 0.37, "h": 0.018, "color": gold, "from": 1, "to": END},
        {"kind": "text", "text": "99", "size": 64, "y": 0.068, "from": 1, "to": END},
        {"kind": "text", "text": "0 DAMAGE", "size": 96, "y": 0.30, "from": MEET1 + 3, "to": MEET1 + 30},
        {"kind": "text", "text": "0 DAMAGE", "size": 96, "y": 0.30, "from": MEET2 + 3, "to": MEET2 + 9},
    ]
    cues = {"fps": FPS, "frames": END, "lines": cue_lines, "sfx": sfx, "overlays": hud,
            "beats": [[MEET1 + 4, L1 - 2], [MEET3 + 1, L3]]}
    json.dump(cues, open(os.path.join(ROOT, "projects", "sf01", "cues.json"), "w", encoding="utf-8"), indent=1)
    json.dump({"REL1": REL1, "MEET1": MEET1, "L1": L1, "L2": L2, "CH2": CH2, "REL2": REL2, "MEET2": MEET2, "ECU_R": ECU_R,
               "ECU_K": ECU_K, "CH3": CH3, "REL3": REL3, "MEET3": MEET3, "L3": L3, "L4": L4, "END": END},
              open(os.path.join(ROOT, "projects", "sf01", "beats.json"), "w"), indent=1)
    print(f"[sf01] END={END} ({END / FPS:.1f}s) REL1={REL1} MEET1={MEET1} L1={L1} L2={L2} CH2={CH2} REL2={REL2} "
          f"CH3={CH3} REL3={REL3} MEET3={MEET3} L3={L3} L4={L4}", flush=True)
