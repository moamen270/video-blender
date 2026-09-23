# SAMURAI DUEL in Blender — implementation plan

Owner: Moamen. Senior (plans, runs commands, reviews): Claude Code. Worker (writes ALL code): Gemini Flash via agy.
Written 2026-09-23. Repo: `F:/PoCs/blender-video`, branch `samurai-blender`.

This file is the single source of truth for the worker. Read it fully before every task.
Tasks are in §9. Do exactly one task at a time, only the task you were given.

---

## 0. Goal and definition of done

Remake the video-builder "samurai-duel" story (`F:/PoCs/video-builder/projects/samurai-duel/manifest.json`)
as a **3D toon-shaded Blender short**, 1080x1920, 24 fps, 672 frames (28 s), with voice, SFX, music,
hook text and CTA — built 100 % from code, no manual Blender UI work, free and local only.

Done when `sh tools/make.sh samurai final` produces `output/vN/final.mp4` and:
1. `tools/qa_samurai.py` passes (blades meet at every contact, hands on the grip, feet do not slide).
2. The senior's review of the contact sheets finds no blocking issue (§10).

Purpose of the experiment: decide whether Blender is a good engine for agent-made videos. So also
keep code clean and reusable (`kit/` is a library for future videos, `projects/samurai/` is only this video).

---

## 1. How we work (worker protocol)

- You CANNOT run commands. The senior runs every command in §9 "Check" and sends you the output.
- You may edit ONLY the files listed in your task. Any other change is reverted automatically.
- If something in the task is unclear or impossible, reply with a first line `BLOCKED: <exact question>`
  and nothing else. Do not guess.
- When done, reply with: `DONE <task id>` then a list of files you changed and 3-10 lines on what you did.
- Never delete or overwrite anything in `output/` (every render is a new `output/vN`).
- Python 3.13 inside Blender 5.2.2 (`F:/blender/blender.exe`). Only the Python standard library,
  `bpy`, `bmesh`, `mathutils` inside Blender scripts. `numpy` + `soundfile` only in `tools/audio.py`.
- Code style: type hints, short docstrings, 4-space indent, no `print` except lines that start with
  a tag in brackets, e.g. `print("[rig] built ronin", flush=True)`.
- Do not use `bpy.ops` except: `bpy.ops.object.mode_set`, `bpy.ops.wm.save_as_mainfile`,
  `bpy.ops.render.render`, and the `bpy.ops.mesh.primitive_*` calls already used inside `studio/core.py`.
  Build meshes with the helpers in `studio/core.py` or with `bmesh`.

### Blender 5.2 facts you must respect (learned the hard way)
- Video output: set `image_settings.media_type = "VIDEO"` BEFORE `file_format = "FFMPEG"` (already in `C.render_settings`).
- Actions are slotted: never use `action.fcurves`; use `C.fcurves(obj)` from `studio/core.py`.
- `hide_render` does not propagate to children: use `C.visible(obj, frame, on)`; always key frame 1 first.
- Engine enum: use `C._set_enum(r, "engine", ["BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"])` (already in `C.render_settings`).
- ffmpeg 9: no glob input; `-vsync` is now `-fps_mode`.
- Bloom is no longer an EEVEE setting. Do not try to enable it.
- An object parented to a bone (`parent_type="BONE"`) is placed relative to the bone's TAIL. Always use
  `kit.rig.attach()` (§4.4), never set bone parents by hand.

---

## 2. Existing code you reuse (read, do not change unless the task says so)

| File | What you use from it |
|---|---|
| `studio/core.py` | `reset_scene, collection, link, material, hex_rgb, empty, sphere, icosphere, cylinder, cone, cube, plane, torus, key, fcurves, set_interp_at, set_interp_all, visible, camera, point_at, cut, sun, sky, render_settings, FPS (=24)` |
| `tools/build.py` | runs `projects/<p>/script.py:build()`, saves `scene.blend`, renders `video.mp4`; supports `--frames a-b` and `--no-render` |
| `tools/make.sh` | next `output/vN`, build+render, then `tools/audio.py` |
| `tools/audio.py` | reads `projects/<p>/cues.json`, mixes SFX + music + Kokoro narration, muxes `final.mp4` |
| `tools/sheet.sh` | tiles PNG frames into a contact sheet |
| `projects/cupid/script.py` | example of a project script (frame constants, `cues` list, `build()`) |

Read `studio/core.py` fully before your first task.

---

## 3. Conventions (used everywhere)

- Units: metres, degrees in all public function arguments (convert with `math.radians` inside).
- **Character-local space** (= the armature's own space): **+X = the character's right, +Y = forward
  (where the character looks), +Z = up**, origin on the ground between the feet at rest.
- World: ground is z = 0. The fight line is the world X axis.
  - Ronin armature object at world `(-1.5, 0, 0)`, `rotation_euler.z = radians(-90)` → faces world +X.
  - Warlord armature object at world `(+1.5, 0, 0)`, `rotation_euler.z = radians(+90)` → faces world −X.
  - The armature OBJECT never moves after placement. All movement is bone animation (§4.2 `mover`).
- Every "pose" number is in character-local space relative to the `mover` bone (§4.2).
- Frames are integers, 24 fps. All frame numbers live as constants at the top of `projects/samurai/script.py`.

---

## 4. `kit/` library — architecture

```
kit/
  __init__.py      empty
  toon.py          toon materials + inverted-hull outline            (T1)
  rig.py           armature, IK, pole calibration, attach()          (T2)
  pose.py          Pose, POSES library, apply/key poses, sword_at    (T3)
  samurai.py       build_ronin(), build_warlord(), swords, saya      (T4)
  stage.py         moonlit bamboo stage, lights, moon, petals        (T5)
  fx.py            sparks, smear, shake, dust, helmet split          (T6)
projects/samurai/
  script.py        timeline + choreography + cameras + cues.json     (T7-T9)
tools/
  tests/t_*.py     one test script per task, run headless            (each task)
  qa_samurai.py    automatic contact/IK/foot checks                  (T10)
  audio.py         extended: chatterbox, sfx dirs, ducking, overlays (T11)
```

### 4.1 Toon look (`kit/toon.py`)
- `toon(name, base_hex, shadow_hex=None, emission=0.0) -> Material`
  Node tree (create with `mat.use_nodes = True`, clear all nodes, then add):
  `ShaderNodeBsdfDiffuse` → `ShaderNodeShaderToRGB` → `ShaderNodeValToRGB` (color ramp) →
  `ShaderNodeEmission` (Strength 1.0) → `ShaderNodeOutputMaterial`.
  Color ramp: `interpolation = "CONSTANT"`; element 0 at position 0.0 = shadow colour; element 1 at
  position 0.35 = base colour. Shadow colour default = base colour × 0.45 (per channel).
  If `emission > 0`, instead of the ramp chain use a plain `ShaderNodeEmission` with the base colour and
  that strength (used for moon, sparks, glowing eyes).
  Cache materials by name in a module dict: calling `toon()` twice with the same name returns the same material.
- `outline_material() -> Material`: emission black `(0,0,0,1)`, `use_backface_culling = True`. Name `"outline"`.
- `add_outline(obj, thickness=0.012)`: append `outline_material()` as a second material slot; add a
  `SOLIDIFY` modifier named `"outline"` with `thickness=thickness`, `offset=1.0`,
  `use_flip_normals=True`, `material_offset=1` (use the slot index of the outline material), `use_rim=False`.
  Skip objects whose name starts with `fx_` (effects have no outline).

### 4.2 Rig (`kit/rig.py`)
`build_armature(name: str) -> bpy.types.Object` creates armature data + object (linked to the
scene collection), enters EDIT mode (`view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="EDIT")`),
creates the bones below, returns to OBJECT mode, then adds constraints (§4.3).
All bones `roll = 0`. `connect` = `use_connect`. `deform` = `use_deform`.

Control bones (all `deform=False`). They all point +Y with length 0.2 so that **their local axes equal
character-local axes** — setting `pose_bone.location` on them moves them in character-local metres.

| bone | head | tail | parent |
|---|---|---|---|
| `mover` | (0,0,0) | (0,0.2,0) | — |
| `hips_ctrl` | (0,0,0.95) | (0,0.2,0.95) | mover |
| `sword` | (0,0,0) | (0,1.05,0) | mover  ← length 1.05 = whole katana, butt at head, tip at tail |
| `grip.R` | (0,0.20,0) | (0,0.30,0) | sword |
| `grip.L` | (0,0.06,0) | (0,0.16,0) | sword |
| `foot_ik.R` | (0.11,0,0.08) | (0.11,0.2,0.08) | — |
| `foot_ik.L` | (-0.11,0,0.08) | (-0.11,0.2,0.08) | — |
| `pole_arm.R` | (0.35,-0.5,1.2) | (0.35,-0.3,1.2) | mover |
| `pole_arm.L` | (-0.35,-0.5,1.2) | (-0.35,-0.3,1.2) | mover |
| `pole_leg.R` | (0.11,0.6,0.5) | (0.11,0.8,0.5) | mover |
| `pole_leg.L` | (-0.11,0.6,0.5) | (-0.11,0.8,0.5) | mover |

Note: the `sword` bone's length is 1.05 (not 0.2); it still points +Y with roll 0 so its axes are
character-local too. Its local +Y runs along the blade.

Deform bones (`deform=True`):

| bone | head | tail | parent | connect |
|---|---|---|---|---|
| `pelvis` | (0,0,0.95) | (0,0,1.05) | hips_ctrl | no |
| `spine` | (0,0,1.05) | (0,0,1.28) | pelvis | yes |
| `chest` | (0,0,1.28) | (0,0,1.50) | spine | yes |
| `neck` | (0,0,1.50) | (0,0,1.58) | chest | yes |
| `head` | (0,0,1.58) | (0,0,1.84) | neck | yes |
| `upperarm.R` | (0.20,0,1.46) | (0.24,-0.03,1.18) | chest | no |
| `forearm.R` | (0.24,-0.03,1.18) | (0.26,0.06,0.94) | upperarm.R | yes |
| `upperarm.L` | (-0.20,0,1.46) | (-0.24,-0.03,1.18) | chest | no |
| `forearm.L` | (-0.24,-0.03,1.18) | (-0.26,0.06,0.94) | upperarm.L | yes |
| `thigh.R` | (0.11,0,0.95) | (0.11,0.03,0.52) | pelvis | no |
| `shin.R` | (0.11,0.03,0.52) | (0.11,0,0.08) | thigh.R | yes |
| `foot.R` | (0.11,0,0.08) | (0.11,0.16,0.08) | shin.R | yes |
| `thigh.L` | (-0.11,0,0.95) | (-0.11,0.03,0.52) | pelvis | no |
| `shin.L` | (-0.11,0.03,0.52) | (-0.11,0,0.08) | thigh.L | yes |
| `foot.L` | (-0.11,0,0.08) | (-0.11,0.16,0.08) | shin.L | yes |

Set `rotation_mode = "XYZ"` on every pose bone except `sword`, which uses `"QUATERNION"`.

### 4.3 Constraints
- `forearm.R`: `IK` constraint, `target = arm`, `subtarget = "grip.R"`, `pole_target = arm`,
  `pole_subtarget = "pole_arm.R"`, `chain_count = 2`, `pole_angle` from calibration. Same for `.L` with
  `grip.L`, `pole_arm.L`. Name the constraints `"IK"`.
- `shin.R`: `IK` → `foot_ik.R`, pole `pole_leg.R`, `chain_count = 2`. Same for `.L`.
- `foot.R`: `COPY_ROTATION` from `foot_ik.R` (world space both). Same for `.L`.
- **Pole calibration** `calibrate_poles(arm)`: for each IK constraint, try `pole_angle` in
  `[-180, -90, 0, 90]` degrees. For arms, first set the `sword` pose bone so that the grip bone's head lies
  exactly on the rest wrist (forearm tail): `sword.location = wrist_rest - grip_rest_head` with identity
  rotation. Legs need no setup (foot_ik rests on the ankle). After each try:
  `bpy.context.view_layer.update()`, read the elbow/knee (`pose.bones["forearm.R"].head`, armature space)
  and measure its distance to the rest elbow/knee (`data.bones[...].head_local`). Keep the angle with
  the smallest distance. Print `[rig] pole forearm.R = -90 (err 0.000)`. Reset `sword` location/rotation
  to zero at the end.
- `set_left_hand(arm, frame, on_grip: bool)`: keys the influence of `forearm.L`'s IK constraint
  (1.0 = hand on the grip, 0.0 = arm hangs in rest pose). Key with
  `con.keyframe_insert("influence", frame=frame)` (data path through the pose bone).

### 4.4 `attach(obj, arm, bone_name)`
Parent a mesh to a bone WITHOUT moving it. Precondition: the armature object is still at the world
origin with identity rotation and no animation (true inside the character builders).
```python
def attach(obj, arm, bone_name):
    bpy.context.view_layer.update()
    pb = arm.pose.bones[bone_name]
    m = arm.matrix_world @ pb.matrix @ Matrix.Translation((0.0, pb.bone.length, 0.0))
    basis = obj.matrix_world.copy()
    obj.parent = arm
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    obj.matrix_parent_inverse = m.inverted()
    obj.matrix_basis = basis
```
So: **build every body part at its rest position in character-local coordinates, then `attach()` it.**

### 4.5 Poses (`kit/pose.py`)
```python
@dataclass
class Pose:
    hips: tuple = (0, 0, 0)          # offset of hips_ctrl from its rest, metres (x right, y fwd, z up)
    lean: float = 0                  # torso pitch, deg, + = forward
    twist: float = 0                 # torso yaw, deg, + = chest turns toward the character's LEFT
    side: float = 0                  # torso roll, deg, + = bends toward the character's RIGHT
    grip: tuple = (0, 0.35, 1.05)    # where the RIGHT hand holds the sword (= grip.R head), relative to mover
    blade: tuple = (35, 0, 0)        # (pitch, yaw, roll) deg of the blade direction, see below
    two_hands: bool = True           # left hand on grip.L?
    feet: tuple = ((0.12, 0.22), (-0.12, -0.22))   # (right foot x,y), (left foot x,y) relative to mover
    head: tuple = (0, 0)             # head (pitch, yaw) deg, + pitch = look down, + yaw = look left
```
Blade direction: start with the blade along +Y (forward, horizontal). `pitch` rotates it up
(+90 = straight up, −45 = forward-down). `yaw` swings it toward the character's RIGHT for positive values
(so +90 = pointing right, −90 = pointing left, 180 = pointing backward). `roll` spins the edge.
```python
def blade_quat(pitch, yaw, roll) -> Quaternion:
    rx = Matrix.Rotation(math.radians(pitch), 4, "X")
    rz = Matrix.Rotation(math.radians(-yaw), 4, "Z")
    ry = Matrix.Rotation(math.radians(roll), 4, "Y")
    return (rz @ rx @ ry).to_quaternion()
```
Sword bone placement from a pose: `sword.location = grip - blade_dir * 0.20` (the butt is 0.20 behind
the right hand along the blade), `sword.rotation_quaternion = blade_quat(...)`, where
`blade_dir = blade_quat(...) @ Vector((0, 1, 0))`.

Torso: `lean`, `twist`, `side` are split half on `spine`, half on `chest` (rotation_euler).
The axis signs of vertical bones are not obvious — the T3 test decides them: `lean=+20` must move the
head forward (+Y), `twist=+30` must move the right shoulder forward (+Y), `side=+15` must move the head
to the right (+X). Put the signs in three module constants `LEAN_SIGN, TWIST_SIGN, SIDE_SIGN` (±1) and
the axis choice in `LEAN_AXIS="X", TWIST_AXIS="Y", SIDE_AXIS="Z"` so they are easy to flip.

Functions:
- `apply_pose(arm, pose, mover=(0,0))` — sets `mover.location = (mover[0], mover[1], 0)`, hips, torso,
  head, sword, feet (`foot_ik.* location = (mover_x + fx - rest_x, mover_y + fy - rest_y, 0)` —
  foot_ik bones are NOT children of mover, so add the mover offset), left-hand influence.
- `key_pose(arm, pose, frame, mover=(0,0), interp="BEZIER")` — `apply_pose` then keyframes every channel
  it set (location/rotation of mover, hips_ctrl, spine, chest, head, sword, foot_ik.R, foot_ik.L and the
  left IK influence) at `frame`, then sets the interpolation of all keys at that frame to `interp`
  (use `C.set_interp_at(arm, frame, interp)`).
- `hold(arm, pose, f0, f1, mover)` — key the same pose at f0 and f1 (hit-stop, standoffs).
- `auto_steps(arm, cues, step_height=0.10)` — call once after all key poses of a character. For each
  foot, walk its keyframes in order; if between two consecutive keys the foot moves more than 0.05 m on
  the ground, insert a key at the middle frame with the middle x,y and z = step_height, and append
  `{"frame": <last key frame>, "sfx": "step", "gain": 0.35}` to `cues`. Keys at the same position stay
  planted (no sliding).
- `to_local(arm, world_point) -> Vector` / `to_world(arm, local_point) -> Vector` — through
  `arm.matrix_world` (the armature object never moves, so no frame is needed).
- `sword_through(point_local, blade, dist) -> tuple` — returns the `grip` that makes the blade with
  direction `blade` pass through `point_local` at `dist` metres from the butt:
  `butt = point - dir*dist; grip = butt + dir*0.20`.
- `reach_ok(arm, pose, mover) -> float` — distance from the right shoulder (upperarm.R head + hips
  offset, approx.) to `grip`; must be ≤ 0.52 (arm length). Raise `ValueError` with the numbers if not.

`POSES: dict[str, Pose]` — the library. Start values (the T3 pose sheet will be reviewed and tuned):

| name | hips | lean | twist | grip | blade (p,y,r) | two_hands | feet R / L |
|---|---|---|---|---|---|---|---|
| `rest` | (0,0,0) | 0 | 0 | (0.26,0.06,0.94) | (-80,0,0) | False | (0.11,0) / (-0.11,0) |
| `sheathed` | (0,0,-0.03) | 5 | 0 | (-0.10,0.28,0.98) | (-20,180,0) | False | (0.14,0.12) / (-0.14,-0.12) |
| `chudan` (mid guard) | (0,0,-0.08) | 8 | 0 | (0.02,0.34,1.05) | (35,0,0) | True | (0.12,0.22) / (-0.12,-0.22) |
| `jodan` (overhead wind-up) | (0,-0.05,-0.05) | -6 | 0 | (0.02,0.08,1.72) | (130,0,0) | True | (0.12,0.22) / (-0.12,-0.22) |
| `overhead_hit` | (0,0.15,-0.20) | 22 | 0 | (0.0,0.55,1.15) | (-10,0,0) | True | (0.12,0.50) / (-0.12,-0.20) |
| `slash_windup` | (0,-0.05,-0.08) | 0 | -30 | (0.32,0.08,1.52) | (115,40,0) | True | (0.12,0.22) / (-0.12,-0.22) |
| `slash_hit` | (0,0.10,-0.15) | 15 | 25 | (-0.22,0.48,1.02) | (-20,-50,0) | True | (0.12,0.45) / (-0.12,-0.20) |
| `thrust_windup` | (0,-0.10,-0.12) | 0 | -10 | (0.10,0.05,1.10) | (5,0,0) | True | (0.12,0.22) / (-0.12,-0.25) |
| `thrust_hit` | (0,0.28,-0.20) | 18 | 5 | (0.0,0.62,1.25) | (0,0,0) | True | (0.12,0.65) / (-0.12,-0.20) |
| `block_high` | (0,0,-0.10) | 0 | 0 | (0.25,0.32,1.55) | (10,-80,0) | True | (0.12,0.22) / (-0.12,-0.22) |
| `block_mid` | (0,0,-0.10) | 5 | 0 | (0.05,0.34,1.00) | (70,-15,0) | True | (0.12,0.22) / (-0.12,-0.22) |
| `parry` | (0,0.05,-0.10) | 8 | 20 | (-0.20,0.40,1.20) | (45,-60,0) | True | (0.12,0.30) / (-0.12,-0.20) |
| `dodge_side` | (-0.30,0,-0.15) | 5 | 0 | (-0.10,0.25,0.95) | (25,0,0) | True | (-0.05,0.20) / (-0.45,-0.15) |
| `dodge_back` | (0,-0.32,-0.10) | -12 | 0 | (0.02,0.00,1.05) | (45,0,0) | True | (0.12,-0.05) / (-0.12,-0.55) |
| `stagger` | (0,-0.15,0) | -15 | 15 | (0.30,0.20,1.10) | (20,50,0) | False | (0.12,0.10) / (-0.12,-0.40) |
| `iai_follow` (after the pass) | (0,0.10,-0.30) | 25 | -20 | (0.45,0.45,1.20) | (0,80,0) | False | (0.18,0.55) / (-0.15,-0.35) |
| `kneel` | (0,0.05,-0.50) | 30 | 0 | (0.30,0.30,0.60) | (-40,30,0) | False | (0.12,0.35) / (-0.12,-0.45) |

Feet in this table are relative to the mover. Positive y of the right foot = right foot forward.

### 4.6 Characters (`kit/samurai.py`)
`build_ronin() -> arm` and `build_warlord() -> arm`: call `rig.build_armature`, `rig.calibrate_poles`,
then build parts with `studio/core.py` primitives at REST coordinates (armature still at origin),
`attach()` each part to the listed bone, `toon.add_outline()` on each part (thickness 0.012; 0.004 for
blades, eyes and thin parts), then place the armature object in the world (§3) and return it.
Name every object `<char>_<part>` (e.g. `ronin_head`). Put a character's objects in its own collection.

Ronin — the hero (pale kimono, visible face):

| part | primitive & rest placement | bone | colour |
|---|---|---|---|
| head | sphere r 0.14 at (0,0,1.70) | head | skin #f1c9a0 |
| hair cap | sphere r 0.146 at (0,-0.02,1.74) scale (1,1,0.62) | head | #1a1a1a |
| topknot | cylinder r 0.035 depth 0.10 at (0,-0.07,1.86), rot (60,0,0) | head | #1a1a1a |
| headband | torus major 0.142 minor 0.016 at (0,0,1.76) | head | #f4f4f4 |
| eye R / L | sphere r 0.022 at (±0.05,0.128,1.71) scale (1,0.5,1.4) | head | #101010 |
| brow R / L | cube size 1 scale (0.055,0.012,0.012) at (±0.05,0.132,1.755) rot (0,±12,0) (inner end lower) | head | #1a1a1a |
| neck | cylinder r 0.05 depth 0.10 at (0,0,1.54) | neck | skin |
| chest | cone r1 0.20 r2 0.17 depth 0.24 at (0,0,1.38) scale (1,0.65,1) | chest | kimono #dfe6f2 |
| belly | cone r1 0.17 r2 0.19 depth 0.24 at (0,0,1.16) scale (1,0.65,1) | spine | kimono |
| collar | cube scale (0.05,0.02,0.20) at (±0.05,0.125,1.40) rot (0,±25,0) | chest | #3a4a6b |
| obi | cylinder r 0.19 depth 0.09 at (0,0,1.02) scale (1,0.68,1) | pelvis | #2b3550 |
| upper arm | limb (§4.7) r 0.075→0.10 (wide sleeve) | upperarm.* | kimono |
| forearm | limb r 0.045→0.04 | forearm.* | skin |
| hand | sphere r 0.05 at the forearm tail | forearm.* | skin |
| thigh | limb r 0.11→0.15 (hakama) | thigh.* | #2e2f38 |
| shin | limb r 0.15→0.17 | shin.* | #2e2f38 |
| foot | cube scale (0.09,0.22,0.06) centred at (±0.11,0.07,0.04) | foot.* | #1b1b1b |
| katana | §4.8, colours: blade #d9dde6 emission 0.3, tsuba #c9a227, handle #20304f | sword | |
| saya (scabbard) | cylinder r 0.025 depth 0.80 at (-0.16,-0.10,0.95), rot so it runs from front-up (-0.16,0.25,1.00) to back-down (-0.16,-0.45,0.85) | pelvis | #121212 |

Warlord — the oni (red lamellar armour, faceless mask, horns):

| part | primitive & rest placement | bone | colour |
|---|---|---|---|
| head | sphere r 0.14 at (0,0,1.70) | head | #222222 |
| menpo mask | sphere r 0.12 at (0,0.06,1.66) scale (1,0.7,0.9) | head | #b3121f |
| fangs | 2 cones r 0.015 depth 0.05 at (±0.03,0.14,1.61) pointing down (rot 180,0,0) | head | #f4f4f4 |
| eyes | sphere r 0.02 at (±0.045,0.13,1.71) | head | #ffcc33 emission 3.0 |
| kabuto dome | sphere r 0.16 at (0,0,1.77) scale (1,1,0.7) | head | #1c1c1c |
| shikoro (neck guard) | cone r1 0.26 r2 0.16 depth 0.14 at (0,-0.02,1.66) | head | #8e1b1b |
| horns | 2 cones r1 0.03 r2 0 depth 0.24 at (±0.10,0.04,1.93), rot (0,∓35,0) (tips outward) | head | #d4a017 |
| do (chest armour) | cube scale (0.46,0.30,0.44) at (0,0,1.30) | chest | #8e1b1b |
| lamellar lines | 4 cubes scale (0.47,0.305,0.012) at z 1.16,1.24,1.32,1.40 | chest | #1a1a1a |
| sode (shoulder plates) | cube scale (0.20,0.07,0.22) at (±0.29,0,1.36) | upperarm.* | #8e1b1b |
| kusazuri (skirt plates) | 5 cubes scale (0.12,0.03,0.22) around the waist at z 0.90 (front, front-left, front-right, left, right) | pelvis | #8e1b1b |
| upper arm | limb r 0.07→0.065 | upperarm.* | #1c1c1c |
| forearm | limb r 0.055→0.05 | forearm.* | #3a3a3a |
| hand | sphere r 0.055 | forearm.* | #1c1c1c |
| thigh / shin | limb r 0.11→0.13 / 0.13→0.12 | thigh.* / shin.* | #3b0d0d |
| foot | as ronin | foot.* | #111111 |
| katana | §4.8, blade #b8bcc6, tsuba #7a0f0f, handle #111111 | sword | |
| saya | as ronin | pelvis | #3b0d0d |

Keep the warlord's helmet parts (kabuto dome, shikoro, horns) as separate objects whose names start
with `warlord_helmet_` — the ending splits the helmet (§6 T9).

### 4.7 `limb(name, arm, bone, r_head, r_tail, mat)`
A truncated cone whose axis runs from the bone's rest head to its rest tail
(`arm.data.bones[bone].head_local` / `tail_local`). Build with `C.cone(r1=r_head, r2=r_tail,
depth=length)`, place its centre at the midpoint and rotate it with
`(tail-head).to_track_quat("Z", "Y").to_euler()` (a cone's axis is its local Z). Add a sphere of radius
`r_head` at the head to hide the joint gap. Then `attach()` both.

### 4.8 Katana (built along the `sword` bone's rest: butt at (0,0,0), +Y to tip at (0,1.05,0))
- handle: cylinder r 0.018 depth 0.26, axis along Y, centred at (0,0.13,0).
- tsuba: cylinder r 0.045 depth 0.012, axis along Y, at (0,0.265,0).
- blade: cube scale (0.008, 0.72, 0.034) centred at (0,0.63,0) (thin in X, edge in Z).
- tip: cone r1 0.017 r2 0 depth 0.07, axis +Y, at (0,1.02,0), scale (0.25,1,1).
All attached to `sword`. Outline 0.004 on blade and tip.

### 4.9 Stage (`kit/stage.py`)
`build_stage(seed=7)`:
- world: `C.sky(hex_rgb("#0b1026"), 1.0)`.
- ground: plane size 60 at z 0, toon #1e2433.
- moon: circle made with `C.cylinder(r=2.6, depth=0.05)` at (1.0, 30, 11) rotated to face −Y
  (rot (90,0,0)), toon #f3ecd2 emission 2.0.
- distant hills: 6 spheres r 6-10 scaled (1,0.5,0.35), y 25-40, z 0, toon #11172b (no outline).
- bamboo: 36 stalks, random from `random.Random(seed)`: x in [-9, 9], y in [6, 18] (behind the fight
  line) plus 12 stalks with y in [-14, -9] (in front, only visible from the reverse shots);
  each stalk = cylinder r 0.05-0.08, height 6-9, toon #2f5d3a, with 5 thin darker rings (torus) every 1.2 m.
  Skip any stalk within 3 m of the origin.
- lights: key moonlight `C.sun("key", energy=2.5, rot=(55, 0, 160))`, rim `C.sun("rim", energy=1.5,
  rot=(60, 0, -20))`. Tint: `light.data.color = (0.75, 0.82, 1.0)` for both.
- `petals(count=50, f0=1, f1=672, seed=11)`: small planes 0.04×0.03, toon #f4b6c8 emission 0.4, name
  `fx_petal_i`, no outline. Each falls from z 4.5 to 0 over 120-200 frames with sine drift in x (amplitude
  0.4, 2 cycles) and a slow spin, starting at a random frame in [f0-100, f1], x in [-4,4], y in [-2,4].
  Key location every 12 frames (BEZIER).

### 4.10 Effects (`kit/fx.py`) — all objects named `fx_*`, no outlines
- `spark(point, frame, seed)`: 14 streaks (cube scale (0.012,0.012,0.10)) toon #fff2b0 emission 8,
  each aimed outward on a random direction (`to_track_quat("Z","Y")`), keyed: frame-1 invisible,
  frame scale 1 at the point, frame+5 moved 0.35-0.6 m outward and scale 0; plus a flash sphere
  r 0.12 emission 12 keyed scale 0 → 1.4 (frame) → 0 (frame+3); plus a point light (energy 0 → 1500 → 0
  over frame-1, frame, frame+3). Use `C.visible` for show/hide.
- `smear(arm, f0, f1, name)`: sample the sword every frame from f0 to f1 (`scene.frame_set(f)`), take the
  world points at 0.45 m and 1.05 m along the blade, and build one ribbon mesh (quads between consecutive
  samples) with `bmesh`; material toon #ffffff emission 2.5; visible only on frames f1-1 .. f1+2.
- `shake(cam, f0, f1, amp=0.06, seed=3)`: add keyed random offsets to the camera location on every frame
  f0..f1, amplitude decaying linearly to 0, then key the original location at f1+1.
- `helmet_split(arm, frame)`: for every `warlord_helmet_*` object: store its world matrix at `frame`,
  key it visible and parented until `frame`, then drive a detached duplicate (`obj.copy()` linked to the
  scene, no parent, `matrix_world` = stored) that is hidden before `frame` and shown from `frame`; the
  left half falls toward local −X and the right half toward +X (split objects into two groups by the sign
  of their world x offset from the head centre; horns go with their side) with a 16-frame parabola to the
  ground and a 90° roll. Hide the originals from `frame`.
- `dust(point, frame)`: 8 flattened spheres toon #6b7085, expanding 0 → 0.25 m and sinking over 10 frames.

---

## 5. Story, timeline and cameras (`projects/samurai/script.py`)

Constants at the top (24 fps). Scene ranges are inclusive.

| # | scene | frames | what happens | camera(s) |
|---|---|---|---|---|
| 1a | cold open | 1-24 | Extreme close-up of the ronin's eyes: closed (eye scale z 0.1) until f8, snap open f8-10. Hook text on screen f3-56. | `cam_eyes`: 0.75 m in front of the ronin's face, lens 60 |
| 1b | standoff | 25-60 | Wide: both in `sheathed`, 3.0 m apart, petals falling between them, slow push-in. | `cam_wide`: (0,-8.5,1.1) look at (0,0,1.3), lens 30; key y -8.5 at f25 → -7.3 at f60 |
| 2 | draw | 61-96 | f61-78 close-up of the warlord's hand drawing (sheathed → chudan f62-74, sword_draw SFX at f63); f79-96 two-shot, ronin draws f80-90 (SFX f81). | `cam_draw`: near the warlord's left hip; `cam_two`: (0,-5.5,1.3) look (0,0,1.2), lens 35 |
| 3 | first contact | 97-192 | Warlord steps in 0.45 m (f97-118). `jodan` f112-122, `overhead_hit` at **C1 f128** onto the ronin's `block_high` (ronin reaches block at f122). Hit-stop hold f128-131. Both recover to `chudan` by f142. Ronin `slash_windup` f150-156, `slash_hit` at **C2 f162** vs warlord `parry` (reached f157). Recover by f176, hold. | `cam_side`: (0,-5.2,1.25) lens 35, looks at the midpoint of the two movers |
| 4 | flurry | 193-300 | Ronin `jodan` f200-207 → `overhead_hit` **C3 f212** vs warlord `block_high`. Cut f214. Warlord `thrust_windup` f222-230 → `thrust_hit` f238; ronin `dodge_side` STARTS f228 and is complete by f236 — clear miss (no contact). Ronin `slash_windup` f250-258 → `slash_hit` **C4 f266** vs warlord `block_mid` — biggest clash, camera shake f266-276. | `cam_ots_ronin` (behind the ronin's right shoulder) f193-213; `cam_ots_warlord` f214-265; `cam_side` f266-300 |
| 5 | the opening | 301-384 | Warlord `jodan` f305-314 → `overhead_hit` **C5 f320** vs ronin `parry` (deflects to the ronin's left); warlord `stagger` f322-334. Ronin `thrust_windup` f334-340 → `thrust_hit` f348; warlord `dodge_back` starts f338 — near miss. Both back off to 3.0 m apart by f372, `chudan`, hold until f384. | `cam_side`; slow push f355-384 |
| 6 | fatal strike | 385-444 | Both charge: movers advance so that they PASS each other on their right sides (each mover x = +0.35) between f385 and f404. At **C6 f404** the ronin's blade passes through the warlord's head/helmet point (1.72 m high) — this is a hit, not a clash. Frames f404-405 are pure white (post overlay). Then both hold follow-through, back to back: ronin `iai_follow`, warlord `overhead_hit`, f406-444. Music cut to silence at f400. | `cam_low`: (0,-6.5,0.35) look at (0,0,1.1), lens 28 |
| 7 | the fall | 445-516 | f462: `helmet_split`. Warlord `kneel` f470-486 (armor_clank f486), then falls forward: `hips_ctrl` goes down to z -0.8 and lean to 80 over f490-500 (thud f500, dust at the chest point). | `cam_fall`: medium on the warlord from the front-left |
| 8 | honor | 517-600 | Ronin straightens to `chudan` f517-530, head turns back toward the warlord. Line "You fought with honor." at f536 (chatterbox). Sheath: `sheathed` pose f560-590, `click` SFX f590. Black from f592 (post overlay). | `cam_honor`: low front close-up on the ronin, lens 50 |
| 9 | CTA | 601-672 | Black screen, text "Follow Dummy Sticky for more." + "@DummySticky", narrator Kokoro `am_michael` line "Follow Dummy Sticky for more." at f606. | (render anything; covered by black) |

**Contacts** (the core of the video). For each clash contact Ck the script computes a world meeting
point `M` in front of the defender (between the fighters, height 1.2-1.6 m), then sets BOTH fighters'
`grip` with `sword_through(to_local(arm, M), blade, dist)` using attacker `dist=0.75`, defender
`dist=0.50`, and each fighter's blade angles from the pose at that frame. So both blades pass exactly
through `M`, and `fx.spark(M, frame)` goes exactly there. Register each contact in `cues["contacts"]`
as `{"id": "C1", "frame": 128, "kind": "clash", "point": [x,y,z], "attacker": "warlord", "defender": "ronin"}`.
C6 is `"kind": "hit"`, only the ronin's blade must pass the point.

Movement rules (from 21 versions of the 2D duel — do not repeat these mistakes):
- The feet move. Every exchange starts with the attacker stepping in (mover +0.3 to +0.5 m) and ends
  with a step back. `auto_steps` makes the steps.
- Timing: wind-up is slow (6-10 frames, BEZIER), the strike is fast (the key before the hit uses
  `interp="LINEAR"`, 4-6 frames), the hit holds 3 frames (hit-stop), the recovery is slow (10-14 frames).
- A dodge starts BEFORE the attack arrives and misses by a visible margin (≥ 0.25 m).
- Anger/aggression ramps: the warlord's lean and step length grow with each exchange.

`cues.json` written by `build()` (extends the cupid format):
```json
{
  "fps": 24, "frames": 672,
  "music": {"file": "F:/PoCs/video-builder/assets/music/japan-duel.wav", "gain": 0.22,
            "cut_frame": 400, "resume_frame": 0, "end_frame": 600},
  "lines": [
    {"id": "honor", "frame": 536, "text": "You fought with honor.", "engine": "chatterbox",
     "voiceRef": "F:/PoCs/video-builder/assets/voices/lewis.wav", "emotion": 0.4, "speed": 0.9},
    {"id": "cta", "frame": 606, "text": "Follow Dummy Sticky for more.", "engine": "kokoro", "voice": "am_michael"}
  ],
  "sfx": [ {"frame": 63, "sfx": "sword_draw", "gain": 0.75}, ... ],
  "contacts": [ ... ],
  "overlays": [
    {"kind": "text", "text": "Two blades. One honor.", "from": 3, "to": 56, "y": 0.18, "size": 86},
    {"kind": "fill", "color": "white", "from": 404, "to": 405},
    {"kind": "fill", "color": "black", "from": 592, "to": 672},
    {"kind": "text", "text": "Follow Dummy Sticky for more.", "from": 606, "to": 672, "y": 0.45, "size": 70},
    {"kind": "text", "text": "@DummySticky", "from": 612, "to": 672, "y": 0.53, "size": 56},
    {"kind": "text", "text": "@DummySticky", "from": 25, "to": 591, "y": 0.95, "size": 34, "alpha": 0.6}
  ]
}
```
SFX per event (names resolve in `assets/sfx/` then `F:/PoCs/video-builder/assets/sfx/`):
clash → `sword_clash` gain 0.9 at the contact frame (C4 also `boom` gain 0.5); every strike →
`sword_swing` gain 0.6 at the first frame of the fast part; C6 → `slash` gain 1.0; draws → `sword_draw`;
steps → `step` (from `auto_steps`); fall → `armor_clank` f486, `thud` f500; sheath → `click` f590.

---

## 6. Audio and post (`tools/audio.py`, T11)
Extend, keep the cupid behaviour working:
1. SFX lookup order: `assets/sfx/<name>.wav`, then `F:/PoCs/video-builder/assets/sfx/<name>.wav`, then the
   synth table.
2. Music: if `cues["music"]["file"]` exists use that file (loop it if too short); apply gain; fade to 0
   over 6 frames ending at `cut_frame`; silence until `end_frame` unless `resume_frame > cut_frame`.
3. Lines: group by engine. `kokoro` lines → existing `narrate()` with each line's `voice`.
   `chatterbox` lines → write a request `{"scenes": [{"id", "speech", "pauseAfter": 0, "speed",
   "voiceRef", "emotion", "seed": 0}]}` and run
   `uv run vb-chatterbox synth --request <req> --out-dir <out>/voice --out <out>/voice/chatterbox.json`
   with `cwd="F:/PoCs/video-builder/py-chatterbox"`; the wav is `<out>/voice/<id>.wav`.
4. Ducking: while any line plays, multiply the music by 0.35 (30 ms ramps).
5. Normalise the mix to peak 0.89 (as now), write `mix.wav`.
6. Mux with overlays: build an ffmpeg `-vf` chain from `cues["overlays"]`:
   - `fill` → `drawbox=x=0:y=0:w=iw:h=ih:color=<color>@1:t=fill:enable='between(n,<from-1>,<to-1>)'`
     (ffmpeg `n` is 0-based, our frames are 1-based).
   - `text` → `drawtext=fontfile='C\:/Windows/Fonts/ariblk.ttf':text='<text>':fontsize=<size>:fontcolor=white@<alpha or 1>:borderw=6:bordercolor=black:x=(w-text_w)/2:y=h*<y>-text_h/2:enable='between(n,<from-1>,<to-1>)'`.
     Escape `'` and `:` in the text.
   Video codec for the mux becomes `-c:v libx264 -crf 18 -pix_fmt yuv420p` (re-encode because of the filters),
   then add `-af loudnorm=I=-14:TP=-1:LRA=11` on the audio.

---

## 7. QA (`tools/qa_samurai.py`, T10) — runs inside Blender on the built `scene.blend`
`blender -b output/vN/scene.blend --python tools/qa_samurai.py -- --cues projects/samurai/cues.json --out output/vN/qa.json`
Checks, each producing `{"check", "frame", "value", "limit", "ok"}`:
1. **Contact**: for every contact frame, the distance from `M` to each required blade segment
   (world points at 0.26 m and 1.05 m along the `sword` bone) ≤ 0.03 m.
2. **Grip**: at every contact frame and every 6th frame, the right wrist (`forearm.R` tail, world) is within
   0.03 m of `grip.R` head; same for the left hand when its IK influence is 1.
3. **Foot slide**: for every frame, a foot whose z ≤ 0.09 (planted) must not move more than 0.01 m from the
   previous frame.
4. **No pass-through**: at every frame, the distance between the two `chest` bone heads is ≥ 0.45 m
   (except f395-410, the pass).
5. **Dead time**: no window of 36 frames between f97 and f444 where every bone of both characters
   moves less than 0.005 m per frame (except the planned holds f406-444).
Print `[qa] <n> checks, <k> failed`, write the JSON, and exit with code 1 if anything failed.

---

## 8. Commands the senior runs (you never run them)
```sh
B=/f/blender/blender.exe
$B -b --factory-startup --python-exit-code 1 --python tools/tests/t_toon.py          # per-task tests
$B -b --python tools/build.py -- --project samurai --out output/vN --quality draft --frames 97-192
sh tools/make.sh samurai preview      # full preview video
sh tools/make.sh samurai final        # final
sh tools/sheet.sh <dir> 6             # contact sheet
```

---

## 9. Tasks (in order)

Every task: create or edit only the listed files; the test script it names must print `[test] PASS` at the
end or raise an exception. Stills from tests go to `output/tests/<task>/` (test scripts create the folder).

**T1 — toon materials.** Files: `kit/__init__.py`, `kit/toon.py`, `tools/tests/t_toon.py`.
Test: reset scene (`C.reset_scene()`), add a sphere and a cube with toon materials and outlines, a sun,
a camera at (0,-5,1.5) looking at (0,0,0.5) (`C.camera`), render one still at 540x960 EEVEE to
`output/tests/T1/still.png` (render settings: `C.render_settings(quality="preview", video=False, frame_end=1)`,
then set `scene.render.filepath` and `bpy.ops.render.render(write_still=True)`).
Check: senior looks at the still — two flat tones per object and a black outline.

**T2 — rig.** Files: `kit/rig.py`, `tools/tests/t_rig.py`.
Test: build an armature, calibrate poles, assert: 26 bones exist (11 control + 15 deform) with the §4.2 names; every pole error
≤ 0.01 m; moving `sword` so `grip.R` sits at (0.25,0.45,1.3) makes the `forearm.R` tail land within 0.02 m
of it after `view_layer.update()`; moving `foot_ik.R` +0.3 in y keeps `foot.R` horizontal (its y axis z
component < 0.05). Print the calibrated angles.

**T3 — poses.** Files: `kit/pose.py`, `tools/tests/t_pose.py`.
Test: the three sign assertions of §4.5; for every pose in `POSES`: apply it, assert the right wrist is within
0.03 m of grip (IK reached — if not, print the distance and the pose name; do not fail for `rest`/`sheathed`
where `reach_ok` is skipped); build a simple capsule body (limb() on every deform bone with the §4.6 ronin radii
and one grey toon material, plus a 1.05 m box on the sword bone) and render one still per pose
(camera at 3/4 front: (2.2,3.2,1.4) look at (0,0,1.0), lens 35) to `output/tests/T3/<pose>.png`.
Check: senior makes a pose sheet and reviews each pose; expect a follow-up with tuned numbers.

**T4 — characters.** Files: `kit/samurai.py`, `tools/tests/t_chars.py`.
Test: build both characters in `chudan` at their §3 world places, stage-less, grey world; render 3 stills:
front 3/4, side (camera on −Y), close-up of both heads → `output/tests/T4/`. Assert both have ≥ 25 mesh parts.

**T5 — stage.** Files: `kit/stage.py`, `tools/tests/t_stage.py`.
Test: stage + both characters in `sheathed`; render the `cam_wide` still (§5) and a reverse shot from +Y.

**T6 — effects.** Files: `kit/fx.py`, `tools/tests/t_fx.py`.
Test: both characters, a clash at f10 (spark at their blade crossing computed as in §5), `smear` for a slash
f4-10, `helmet_split` at f20, render frames 8, 10, 12, 22, 30 at draft size.

**T7 — script part 1 (scenes 1-2, frames 1-96).** Files: `projects/samurai/script.py`.
Structure like `projects/cupid/script.py`: frame constants, `cues` dict (§5 format), `build()` that
resets the scene, builds stage + characters, keys all poses, cameras, cuts, petals, writes `cues.json`,
sets `scene.frame_end = 672`. In this task implement frames 1-96 only; later scenes keep the characters
in `chudan`. Check: draft render `--frames 1-96`, sheet every 6 frames.

**T8 — script part 2 (scenes 3-5, frames 97-384).** Same file. All contacts C1-C5 with sparks, smears,
shake, steps. Check: draft render 97-384 + dense frames around each contact (contact-2 … contact+3).

**T9 — script part 3 (scenes 6-9, frames 385-672).** Same file. The pass, C6, helmet split, fall, honor, sheath.

**T10 — QA.** Files: `tools/qa_samurai.py`. Check: runs on the T9 scene; failures are fixed in
`script.py`/`kit/pose.py` in follow-ups until it passes.

**T11 — audio + post.** Files: `tools/audio.py`. Check: `sh tools/make.sh samurai preview`, the senior
listens via the waveform/cue list and watches frames of the overlays.

**T12 — final.** No code unless the review asks for it. `sh tools/make.sh samurai final`.

---

## 10. Review (senior)
After each task the senior checks the test output and stills and answers with either `ACCEPT T<n>` or a
numbered fix list. After T9/T12 the senior reviews the whole video:
- 2 Hz contact sheet of the full video + dense strips around C1-C6.
- `qa.json` all ok.
- Hook in the first second, readable text, CTA, watermark.
- Audio: every clash has a sound at its frame, music cut before C6, line intelligible.
Findings and time spent go into `docs/SAMURAI_LOG.md` (written by the senior) — the evidence for the
"is Blender the right engine?" decision.
