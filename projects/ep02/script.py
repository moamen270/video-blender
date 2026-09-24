"""Episode 02: Unexpected Item (Batman vs the Self-Checkout)."""
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
from mathutils import Matrix, Vector

import kit.cape as cape
import kit.captions as captions
import kit.cast as cast
import kit.checkout as checkout
import kit.face as face
import kit.look as look
import kit.motion as motion
import kit.props as props
import kit.sets as sets
import kit.shots as shots
import studio.core as C

FPS = 24
BAT_AT = (0.0, 0.45)
PLACE_AT = (-0.50, 0.15)
LAND_AT = (-0.55, 0.08)
JOK_FAR = (-2.4, 9.5)
JOK_FROM = (-2.0, 2.4)
JOK_STOP = (-0.95, 0.40)
JOK_EXIT = (-2.4, 6.0)
KEYWORDS = {
    "unexpected",
    "item",
    "nothing",
    "yourself",
    "where",
    "wait",
    "assistant",
    "trouble",
    "bats",
    "thank",
    "vengeance",
    "night",
    "exact",
    "change",
}


def heading(from_xy: tuple[float, float] | Vector, to_xy: tuple[float, float] | Vector) -> float:
    """Calculate heading in degrees: 0 = facing +Y, 90 = facing -X."""
    dx = to_xy[0] - from_xy[0]
    dy = to_xy[1] - from_xy[1]
    return math.degrees(math.atan2(-dx, dy))


def build() -> None:
    """Build the full Unexpected Item episode scene."""
    manifest_path = os.path.join(ROOT, "projects", "ep02", "voice", "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as fh:
        man = json.load(fh)["lines"]

    def L(line_id: str) -> int:
        return math.ceil(man[line_id]["seconds"] * FPS)

    # Timeline before step 10
    F_SLAM = 5
    M1 = 1
    B_NOTH = M1 + L("m_unexpected") + 1
    TURN = B_NOTH + L("b_nothing") + 1
    M2 = TURN + 4
    THROW = M2 + L("m_unexpected") - 12
    B_SHOW = THROW + 20
    PULL = B_SHOW + L("b_show") + 2
    M_PLACE = PULL + 4
    PLACE = M_PLACE + 18
    M_CUT = M_PLACE + L("m_place") + 1
    GRAB = M_CUT + 30
    B_WHERE = GRAB + 6
    M_WAIT = B_WHERE + L("b_where") + 3
    BEAT = M_WAIT + L("m_wait") + 1
    WHIP = BEAT + 20
    JOK_WALK = WHIP - 18
    END = 1000  # Placeholder until computed in step 10

    # 1. Scene
    C.reset_scene()
    mart = sets.gotham_mart()
    ck = checkout.build_checkout()
    look.store_night(target=(0.0, 0.0, 1.0))
    scene = bpy.context.scene

    # 2. Characters
    bat = cast.build_batman()
    jok = cast.build_joker()
    motion.key_root(bat, 1, loc=(*BAT_AT, 0.0), heading=180.0)
    motion.key_root(jok, 1, loc=(*JOK_FAR, 0.0), heading=180.0)
    motion.key_root(jok, JOK_WALK - 1, loc=(*JOK_FAR, 0.0))
    motion.key_root(jok, JOK_WALK, loc=(*JOK_FROM, 0.0))
    motion.setup_ik(bat)
    motion.setup_ik(jok)
    motion.play(bat, "Idle", 1, END + 10)
    motion.play(jok, "Idle", 1, END + 10)

    # 3. Hook — the slam
    milk = props.milk("milk")
    S = ck.anchors["scanner"]
    motion.reach_path(
        bat,
        "R",
        [
            (1, S + Vector((0.0, 0.05, 0.45))),
            (F_SLAM, S + Vector((0.0, 0.03, 0.22))),
            (F_SLAM + 10, S + Vector((0.0, 0.03, 0.22))),
        ],
        blend_in=1,
        blend_out=6,
    )
    scene.frame_set(1)
    bpy.context.view_layer.update()
    hand = bat.arm.matrix_world @ bat.arm.pose.bones["Fist.R"].tail
    milk.location = hand - Vector((0.0, 0.0, 0.14))
    held = motion.hold(bat, milk, "R", 1)
    m_scan = motion.release(held, F_SLAM + 2, place=S)
    m_scan.rotation_euler = (0.0, 0.0, 0.0)
    checkout.screen_state(ck, F_SLAM + 2, "error")
    checkout.lamp(ck, F_SLAM + 2, "red")

    # 4. Turn to the empty bagging area
    motion.turn_to(bat, TURN, 130.0, frames=8)

    # 5. Batarang throw
    motion.play(bat, "Punch", THROW, 18, blend_in=3)
    motion.play(bat, "Idle", THROW + 18, END + 10, blend_in=4)
    bt = props.batarang("batarang")
    scene.frame_set(THROW + 7)
    bpy.context.view_layer.update()
    p0 = bat.arm.matrix_world @ bat.arm.pose.bones["Fist.R"].tail
    p1 = Vector((*LAND_AT, 0.83))
    motion.throw(bt, THROW + 7, THROW + 12, p0, p1, arc=0.15, spin=720.0)
    C.key(bt, THROW + 12, rot=(60.0, 0.0, 20.0))
    C.visible(bt, 1, False)
    C.visible(bt, THROW + 7, True)

    # 6. Pull the batarang out
    motion.turn_to(bat, PULL - 8, 150.0, frames=6)
    motion.reach_path(
        bat,
        "R",
        [
            (PULL, p1 + Vector((0.0, 0.0, 0.05))),
            (PULL + 10, Vector((*BAT_AT, 0.0)) + Vector((-0.25, -0.10, 1.0))),
        ],
        blend_in=5,
        blend_out=6,
    )
    hb = motion.hold(bat, bt, "R", PULL)
    C.visible(hb, PULL + 14, False)

    # 7. Place the milk
    motion.reach_path(
        bat,
        "R",
        [
            (PLACE, S + Vector((0.0, 0.03, 0.20))),
            (PLACE + 8, S + Vector((0.0, 0.03, 0.20))),
            (PLACE + 22, Vector((*PLACE_AT, 1.0))),
            (PLACE + 28, Vector((*PLACE_AT, 1.0))),
        ],
        blend_in=5,
        blend_out=6,
    )
    h2 = motion.hold(bat, m_scan, "R", PLACE + 6)
    m_bag = motion.release(h2, PLACE + 26, place=(*PLACE_AT, 0.81))
    m_bag.rotation_euler = (0.0, 0.0, 0.0)

    # 8. Grab the screen
    motion.turn_to(bat, M_CUT, 180.0, frames=6)
    SL = ck.anchors["screen_L"] + Vector((0.0, 0.06, -0.02))
    SR = ck.anchors["screen_R"] + Vector((0.0, 0.06, -0.02))
    motion.reach_path(bat, "L", [(GRAB, SL), (M_WAIT - 4, SL)], blend_in=4, blend_out=6)
    motion.reach_path(bat, "R", [(GRAB, SR), (M_WAIT - 4, SR)], blend_in=4, blend_out=6)
    checkout.screen_state(ck, M_WAIT, "wait")

    # 9. The beat
    sets.flicker(
        mart,
        [
            (BEAT + 3, BEAT + 5),
            (BEAT + 9, BEAT + 10),
            (BEAT + 14, BEAT + 18),
        ],
    )

    # 10. The Joker
    motion.key_root(jok, JOK_WALK, heading=heading(JOK_FROM, JOK_STOP))
    jw_end, jsteps = motion.walk_to(jok, JOK_WALK, JOK_STOP)

    # Compute timeline values that depend on jw_end
    J_TROUB = max(WHIP + 8, jw_end - 12)
    SCAN = J_TROUB + L("j_trouble") + 2
    M_THANKS = SCAN + 20
    AWAY = M_THANKS + 30
    B_VENG = M_THANKS + L("m_thanks") + 4
    SMOKE = B_VENG + L("b_vengeance") + 4
    M_FINAL = SMOKE + 22
    END = M_FINAL + L("m_unexpected") + 1
    scene.frame_end = END

    # face Batman (both in profile for the two-shot); the milk is then at his right-front
    motion.turn_to(jok, jw_end, heading(JOK_STOP, BAT_AT), frames=6)
    motion.turn_to(bat, J_TROUB - 4, heading(BAT_AT, JOK_STOP), frames=8)

    scene.frame_set(SCAN)
    bpy.context.view_layer.update()
    shoulder_head = jok.arm.matrix_world @ jok.arm.pose.bones["UpperArm.R"].head
    target_pos = S + Vector((0.0, 0.0, 0.2))
    dir_to_s = (target_pos - shoulder_head).normalized()
    W = shoulder_head + dir_to_s * 0.5

    motion.reach_path(
        jok,
        "R",
        [
            (SCAN, Vector((*PLACE_AT, 0.95))),
            (SCAN + 8, Vector((*PLACE_AT, 0.95))),
            (SCAN + 16, W),
            (SCAN + 22, W),
        ],
        blend_in=5,
        blend_out=8,
    )
    hj = motion.hold(jok, m_bag, "R", SCAN + 6)
    checkout.screen_state(ck, SCAN + 18, "thanks")
    checkout.lamp(ck, SCAN + 18, "green")
    motion.walk_to(jok, AWAY, JOK_EXIT, action="Walk_Carry")

    # 11. "I am vengeance"
    motion.turn_to(bat, B_VENG - 10, 180.0, frames=8)

    # 12. Smoke bomb
    motion.play(bat, "Shoot_OneHanded", SMOKE, 13, blend_in=3)
    motion.play(bat, "Idle", SMOKE + 13, END + 10, blend_in=4)
    props.smoke_puff("smoke", Vector((*BAT_AT, 0.0)), SMOKE + 6, count=11, radius=0.7, seed=3)
    motion.key_root(bat, SMOKE + 13, loc=(*BAT_AT, 0.0), heading=180.0)
    motion.key_root(bat, SMOKE + 14, loc=(-0.72, 0.0, 0.81), heading=0.0)
    checkout.screen_state(ck, M_FINAL - 2, "error")
    checkout.lamp(ck, M_FINAL - 2, "red")

    # 13. Faces
    face.set_expression(bat.face, "stern", 1)
    face.change_expression(bat.face, THROW - 2, "stern", "angry")
    face.change_expression(bat.face, PULL, "angry", "stern")
    face.change_expression(bat.face, GRAB - 2, "stern", "angry")
    face.change_expression(bat.face, BEAT, "angry", "deadpan")
    face.change_expression(bat.face, J_TROUB, "deadpan", "suspicious")
    face.change_expression(bat.face, B_VENG - 6, "suspicious", "deadpan")
    face.change_expression(bat.face, SMOKE + 30, "deadpan", "surprised")

    face.set_expression(jok.face, "smug", 1)

    face.apply_lipsync(bat.face, man["b_nothing"]["cues"], B_NOTH)
    face.apply_lipsync(bat.face, man["b_show"]["cues"], B_SHOW)
    face.apply_lipsync(bat.face, man["b_where"]["cues"], B_WHERE)
    face.apply_lipsync(bat.face, man["b_vengeance"]["cues"], B_VENG)
    face.apply_lipsync(jok.face, man["j_trouble"]["cues"], J_TROUB)

    bat_blink_schedule = [
        (1, "stern"),
        (THROW - 2, "angry"),
        (PULL, "stern"),
        (GRAB - 2, "angry"),
        (BEAT, "deadpan"),
        (J_TROUB, "suspicious"),
        (B_VENG - 6, "deadpan"),
        (SMOKE + 30, "surprised"),
    ]
    face.auto_blink(bat.face, 1, END, bat_blink_schedule, seed=1)
    face.auto_blink(jok.face, JOK_WALK, END, [(1, "smug")], seed=2)

    # 14. Cameras
    C.render_settings(width=1080, height=1920, frame_end=END, quality="preview", video=True)

    def bat_face(at: int) -> Vector:
        """World centre of Batman's face at a frame (native (0, -0.45, 2.45))."""
        scene.frame_set(at)
        bpy.context.view_layer.update()
        return bat.arm.matrix_world @ Vector((0.0, -0.45, 2.45))

    cam_hook = shots.frame(
        "cam_hook",
        [S + Vector((0.0, 0.0, 0.30)), ck.parts["ck_scanner"]],
        shot="insert",
        yaw=60.0,
        pitch=25.0,
        at=1,
    )
    C.cut(1, cam_hook)

    cam_wide = shots.frame(
        "cam_wide",
        [bat, ck.parts["ck_monitor"], ck.parts["ck_bag_base"]],
        shot="wide",
        yaw=-35.0,
        pitch=12.0,
        at=40,
    )
    C.cut(40, cam_wide)

    cam_bag = shots.frame(
        "cam_bag",
        [ck.parts["ck_bag_plate"], ck.parts["ck_bag"], bat_face(TURN + 8)],
        shot="insert",
        yaw=150.0,
        pitch=15.0,
        at=TURN,
    )
    shots.push(cam_bag, TURN, THROW - 4, 0.15)
    C.cut(TURN, cam_bag)

    cam_throw = shots.frame(
        "cam_throw",
        [bat, ck.parts["ck_bag_plate"]],
        shot="full",
        yaw=75.0,
        pitch=5.0,
        at=THROW - 4,
    )
    C.cut(THROW - 4, cam_throw)

    cam_2s = shots.frame(
        "cam_2s",
        [bat, ck.parts["ck_monitor"], ck.parts["ck_bag_plate"]],
        shot="full",
        yaw=-120.0,
        pitch=10.0,
        at=PULL - 2,
    )
    C.cut(PULL - 2, cam_2s)

    def machine_pov(name: str, at: int, lens: float) -> bpy.types.Object:
        """The self-checkout's point of view: in front of its screen, looking at Batman's face."""
        scene.frame_set(at)
        bpy.context.view_layer.update()
        face_c = bat.arm.matrix_world @ Vector((0.0, -0.45, 2.45))
        # behind the monitor; clip_start past the monitor so the camera "is" the screen
        # (in front of it the face is only ~0.2 m away - senior review of v11)
        eye = ck.anchors["screen"] + Vector((0.0, -0.45, 0.05))
        cam = C.camera(name, tuple(eye), tuple(face_c), lens=lens)
        cam.data.clip_start = 0.52
        return cam

    cam_ecu = machine_pov("cam_ecu", GRAB + 6, 26.0)
    # the monitor box itself is hidden during the two POV shots (its tilted top edge peeked in as a black
    # line); its screen planes are separate objects keyed by screen_state and are clipped by clip_start
    mon = ck.parts["ck_monitor"]
    for f, hidden in ((1, False), (GRAB, True), (M_WAIT, False), (B_VENG - 6, True), (SMOKE - 2, False)):
        mon.hide_render = hidden
        mon.keyframe_insert("hide_render", frame=f)
    C.set_interp_all(mon, "CONSTANT")
    C.cut(GRAB, cam_ecu)

    cam_screen = shots.frame(
        "cam_screen",
        [ck.parts["ck_monitor"]],
        shot="insert",
        yaw=-50.0,
        pitch=18.0,
        at=M_WAIT,
    )
    C.cut(M_WAIT, cam_screen)

    cam_beat = shots.frame(
        "cam_beat",
        bat,
        shot="close",
        yaw=-140.0,
        pitch=0.0,
        at=M_WAIT + 44,
    )
    C.cut(M_WAIT + 44, cam_beat)

    cam_whip = C.camera(
        "cam_whip",
        cam_beat.location.copy(),
        cam_beat.location + Vector((0.0, 1.0, 0.0)),
        lens=cam_beat.data.lens,
    )
    cam_whip.rotation_euler = cam_beat.rotation_euler.copy()
    cam_whip.data.sensor_fit = cam_beat.data.sensor_fit
    cam_whip.data.sensor_height = cam_beat.data.sensor_height

    scene.frame_set(WHIP + 5)
    bpy.context.view_layer.update()
    target_whip = jok.root.matrix_world.translation.copy() + Vector((0.0, 0.0, 1.2))
    shots.whip(cam_whip, WHIP, target_whip, frames=5)
    C.cut(WHIP, cam_whip)

    cam_jok = shots.frame(
        "cam_jok",
        jok,
        shot="medium",
        yaw=-148.0,
        pitch=3.0,
        at=J_TROUB,
    )
    C.cut(WHIP + 6, cam_jok)

    cam_2s_j = shots.frame(
        "cam_2s_j",
        [jok, bat],
        shot="two_shot",
        yaw=5.0,
        pitch=10.0,
        at=SCAN - 4,
    )
    C.cut(SCAN - 4, cam_2s_j)

    cam_veng = machine_pov("cam_veng", B_VENG, 30.0)
    cam_veng["aim_x"], cam_veng["aim_y"], cam_veng["aim_z"] = tuple(bat.arm.matrix_world @ Vector((0.0, -0.45, 2.45)))
    shots.push(cam_veng, B_VENG - 6, SMOKE - 2, 0.12)
    C.cut(B_VENG - 6, cam_veng)

    cam_end = shots.frame(
        "cam_end",
        [bat, ck.parts["ck_monitor"], ck.parts["ck_bag_base"]],
        shot="wide",
        yaw=-60.0,
        pitch=12.0,
        at=SMOKE - 2,
    )
    C.cut(SMOKE - 2, cam_end)

    # 15. Cape bake (LAST animation call)
    cape.bake_cape(bat, 1, SMOKE + 13)
    cape.bake_cape(bat, SMOKE + 14, END)

    # 16. cues.json
    lines_cues = [
        {
            "id": "m_unexpected@M1",
            "frame": M1,
            "text": man["m_unexpected"]["text"],
            "wav": man["m_unexpected"]["wav"],
        },
        {
            "id": "b_nothing@B_NOTH",
            "frame": B_NOTH,
            "text": man["b_nothing"]["text"],
            "wav": man["b_nothing"]["wav"],
        },
        {
            "id": "m_unexpected@M2",
            "frame": M2,
            "text": man["m_unexpected"]["text"],
            "wav": man["m_unexpected"]["wav"],
        },
        {
            "id": "b_show@B_SHOW",
            "frame": B_SHOW,
            "text": man["b_show"]["text"],
            "wav": man["b_show"]["wav"],
        },
        {
            "id": "m_place@M_PLACE",
            "frame": M_PLACE,
            "text": man["m_place"]["text"],
            "wav": man["m_place"]["wav"],
        },
        {
            "id": "m_unexpected@M_CUT",
            "frame": M_CUT,
            "text": man["m_unexpected"]["text"],
            "wav": man["m_unexpected"]["wav"],
            "dur": 1.40,  # "item" ends at 1.40 s (word timings); 1.45 let the start of "in" through
        },
        {
            "id": "b_where@B_WHERE",
            "frame": B_WHERE,
            "text": man["b_where"]["text"],
            "wav": man["b_where"]["wav"],
        },
        {
            "id": "m_wait@M_WAIT",
            "frame": M_WAIT,
            "text": man["m_wait"]["text"],
            "wav": man["m_wait"]["wav"],
        },
        {
            "id": "j_trouble@J_TROUB",
            "frame": J_TROUB,
            "text": man["j_trouble"]["text"],
            "wav": man["j_trouble"]["wav"],
        },
        {
            "id": "m_thanks@M_THANKS",
            "frame": M_THANKS,
            "text": man["m_thanks"]["text"],
            "wav": man["m_thanks"]["wav"],
        },
        {
            "id": "b_vengeance@B_VENG",
            "frame": B_VENG,
            "text": man["b_vengeance"]["text"],
            "wav": man["b_vengeance"]["wav"],
        },
        {
            "id": "m_unexpected@M_FINAL",
            "frame": M_FINAL,
            "text": man["m_unexpected"]["text"],
            "wav": man["m_unexpected"]["wav"],
        },
    ]

    sfx_cues = [
        {"frame": F_SLAM, "sfx": "slam"},
        {"frame": F_SLAM + 2, "sfx": "error_beep"},
        {"frame": M2 - 2, "sfx": "error_beep"},
        {"frame": THROW + 7, "sfx": "swoosh"},
        {"frame": THROW + 12, "sfx": "thunk"},
        {"frame": GRAB, "sfx": "grab", "gain": 1.6},
        {"frame": BEAT + 3, "sfx": "flicker"},
        {"frame": BEAT + 14, "sfx": "flicker"},
        {"frame": SCAN + 17, "sfx": "scan_beep", "gain": 1.6},
        {"frame": SCAN + 21, "sfx": "success", "gain": 1.5},
        {"frame": SMOKE + 6, "sfx": "poof"},
        {"frame": M_FINAL - 2, "sfx": "error_beep"},
    ]

    jok_steps1 = motion.foot_events(jok, JOK_WALK, jw_end + 8)
    # exit steps only until Batman speaks (they cluttered the punchline); drop a foot landing within 4 frames
    # of the previous one (both feet settle together when stopping) - measured in the v13 mix
    jok_steps2 = [f for f in motion.foot_events(jok, AWAY, END) if f < B_VENG - 4]
    last = -99
    for f in sorted(set(jok_steps1 + jok_steps2)):
        if f - last >= 5:
            sfx_cues.append({"frame": f, "sfx": "step_hard", "gain": 0.3})
            last = f

    sfx_cues.sort(key=lambda s: s["frame"])

    all_captions = []
    caption_lines = [
        (M1, man["m_unexpected"]["words"]),
        (B_NOTH, man["b_nothing"]["words"]),
        (M2, man["m_unexpected"]["words"]),
        (B_SHOW, man["b_show"]["words"]),
        (M_PLACE, man["m_place"]["words"]),
        (M_CUT, [w for w in man["m_unexpected"]["words"] if w["start"] < 1.40]),
        (B_WHERE, man["b_where"]["words"]),
        (M_WAIT, man["m_wait"]["words"]),
        (J_TROUB, man["j_trouble"]["words"]),
        (M_THANKS, man["m_thanks"]["words"]),
        (B_VENG, man["b_vengeance"]["words"]),
        (M_FINAL, man["m_unexpected"]["words"]),
    ]
    for start_f, words in caption_lines:
        all_captions.extend(captions.groups(words, start_f, fps=FPS, keywords=KEYWORDS))

    all_captions.sort(key=lambda c: c["start_frame"])
    for cur, nxt in zip(all_captions, all_captions[1:]):
        cur["end_frame"] = min(cur["end_frame"], nxt["start_frame"] - 1)

    cues = {
        "fps": FPS,
        "frames": END,
        "music": {
            "file": os.path.join(ROOT, "assets", "library", "music", "Mystery Sax.mp3"),
            "start_s": 0,
            "gain": 0.25,
            "cut_frame": BEAT,
            "resume_frame": WHIP,
            "end_frame": END,
        },
        "lines": lines_cues,
        "sfx": sfx_cues,
        "captions": all_captions,
        "overlays": [
            {
                "kind": "text",
                "text": "His deadliest enemy yet.",
                "from": 1,
                "to": 50,
                "y": 0.16,
                "size": 64,
            },
            {
                "kind": "text",
                "text": "@DummySticky",
                "from": 25,
                "to": END,
                "y": 0.95,
                "size": 34,
                "alpha": 0.6,
            },
        ],
        "beats": [[BEAT, WHIP]],
    }

    cues_path = os.path.join(ROOT, "projects", "ep02", "cues.json")
    with open(cues_path, "w", encoding="utf-8") as fh:
        json.dump(cues, fh, indent=1)

    # 17. Print
    seconds = END / FPS
    print(
        f"[ep02] END={END} ({seconds:.1f} s) F_SLAM={F_SLAM} B_NOTH={B_NOTH} TURN={TURN} "
        f"THROW={THROW} PULL={PULL} PLACE={PLACE} GRAB={GRAB} BEAT={BEAT} WHIP={WHIP} "
        f"jw_end={jw_end} SCAN={SCAN} B_VENG={B_VENG} SMOKE={SMOKE} M_FINAL={M_FINAL}",
        flush=True,
    )


if __name__ == "__main__":
    build()
