# EP02 "Unexpected Item" — implementation plan (checkpoint 1: characters + look)

Owner: Moamen. Senior (plans, runs checks, reviews): Claude Code. Worker (writes ALL code): Gemini Flash via agy.
Written 2026-09-24. Repo `F:/PoCs/blender-video`, branch `ep02-unexpected-item`.
Script: `content/scripts/02-unexpected-item.md`. Production rules: `docs/PRODUCTION_PLAN.md`.

This file is the single source of truth for the worker. Read §1–§3 and the section of your task fully.
Do exactly the one task you were given (§9).

---

## 0. Goal and checkpoints

Batman vs the self-checkout, ~31 s, 1080x1920, 24 fps — the first episode made with **real skinned
characters** (Quaternius, CC0) instead of primitives glued to bones.

| checkpoint | what the owner sees | tasks |
|---|---|---|
| **1 (this file)** | look-dev test + first Batman and Joker stills (turnaround sheets) | E1–E4 |
| 2 | fixed turnarounds, cape with spring motion, expressions + mouth shapes on camera | later |
| 3 | grey animatic of the whole episode (store set, shots, timing, voices) | later |
| 4 | final video with SFX, music, captions | later |

The code is a library for every future episode: `kit/qchar.py`, `kit/look.py`, `kit/face.py` are generic;
`kit/cast.py` holds the recurring cast (Batman, Joker, more later).

---

## 1. Worker protocol

- You CANNOT run commands. The supervisor runs the task's check after you finish and sends you the output
  when it fails.
- Edit ONLY the files listed in your task. Any other change is reverted automatically.
- If something is unclear or impossible, reply with a first line `BLOCKED: <exact question>` and nothing else.
- When done, reply: `DONE <task id>`, the files you changed, and 3–10 lines on what you did.
- Python 3.13 inside Blender 5.2.2. Only the standard library, `bpy`, `bmesh`, `mathutils` in Blender code.
- Style: type hints, short docstrings, 4-space indent. Prints only as tagged lines (`print("[qchar] ...", flush=True)`).
- No `bpy.ops` except `object.mode_set`, `wm.save_as_mainfile`, `render.render`, and the
  `mesh.primitive_*` calls already inside `studio/core.py` (use `C.cone`, `C.cube`, ... from there).
- Everything in `.agy/BRIEF.md` applies (Blender 5.2 facts, owner rules).

---

## 2. Facts about the Quaternius characters (measured by the senior — trust these numbers)

Folder: `F:/PoCs/blender-video/assets/library/quaternius/ultimate_animated_character/` (52 `.blend` files, CC0).

Every file contains exactly two objects and 17 actions:
- `CharacterArmature` (ARMATURE, at the origin, no rotation, scale 1) with 23 bones:
  `Bone` (root), `Body`, `Hips`, `Abdomen`, `Torso`, `Neck`, `Head`,
  `Shoulder.L/.R`, `UpperArm.L/.R`, `LowerArm.L/.R`, `Fist.L/.R`,
  `UpperLeg.L/.R`, `LowerLeg.L/.R`, `Foot.L/.R`, `PoleTarget.L/.R`.
- `Body` (MESH) parented to the armature with identity transform; modifiers `Armature` (object =
  CharacterArmature) and `Auto Smooth` (geometry nodes). Mesh coordinates = armature coordinates. No UV maps.
- Actions (clean names): `Death, Defeat, Idle, Jump, PickUp, Punch, RecieveHit, Roll, Run, Run_Carry,
  Shoot_OneHanded, SitDown, StandUp, SwordSlash, Victory, Walk, Walk_Carry` (note the spelling `RecieveHit`).
  Frame ranges start at 0 (Idle 0–100, Walk 0–30, Punch 0–18, PickUp 0–30).

**Native space** (the armature's own coordinates, used in this plan as "native"):
- Body height 3.147 = the bald `BaseCharacter` (feet at z = 0, top of the head skin z ≈ 3.147); hair/hats add
  up to ≈ 0.16 (Suit_Male top 3.307). The rest pose is a T-pose (arms along ±X).
- The character **faces −Y**. The character's **left is +X** (bones `*.L` have x > 0).
- Head: a rounded box, native z 2.10–3.13, half-width ≈ 0.49. Its **front is flat at y = −0.492** for
  z 2.25–2.85, |x| ≤ 0.40. Bone `Head`: head (0, 0.003, 2.167) → tail (0, 0.003, 2.808).
- Face paint (material `Face`, 100 % weighted to `Head`): 4 separate islands —
  eyes at |x| 0.203–0.284, z 2.470–2.647; brows at |x| 0.144–0.369, z 2.674–2.758.
- Torso: front surface y ≈ −0.21 (z 1.2–1.7), back y ≈ +0.20 (z 1.6–1.7), +0.32 at the seat (z 1.1–1.2).
  Arms at z ≈ 1.87 in the T-pose. Top of the shoulders ≈ z 2.0.
- Materials are named after the part, per file (a second loaded file gets `.001` suffixes — always compare
  names with the suffix stripped: `name.split(".")[0]`):
  - `BaseCharacter`: `Skin` (whole body), `Face`.
  - `Suit_Male`: `Skin` (head + hands), `Black` (jacket, trousers), `Shirt` (white shirt front), `Details`
    (tie, buttons), `Belt`, `Face`, `Hair`.
  - `Casual_Male`: `Shirt`, `Skin`, `Pants`, `Belt`, `Face`, `Hair`.
  - `Worker_Male`: `Skin`, `Shirt`, `Vest`, `Pants`, `Hat`, `Face`.
- Dominant vertex groups: `Face`, `Hair`, `Hat` → 100 % `Head`. Hands → `Fist.L/.R`. Head skin → `Head`/`Neck`.

---

## 3. Conventions

- A character is placed and moved ONLY through its **root empty** (`<name>_root`). Root space = our usual
  character-local space: **+X = the character's right, +Y = forward, +Z = up**, metres, origin between the feet.
- Inside the root: the armature object has `rotation_euler = (0, 0, π)` and uniform scale
  `s = height / 3.147` (default height 1.80 → s = 0.57197; the same scale for every character — hair adds height). This turns native −Y (face) into root +Y and
  native +X (character's left) into root −X, so the convention above holds.
- Convert native → world with `qc.arm.matrix_world @ Vector(native_xyz)` (call
  `bpy.context.view_layer.update()` first). Every native number in this plan is converted that way.
- **Build order for every character** (builders in `kit/cast.py`):
  1. `load_character(...)` at the origin, root rotation 0, rest pose, no action.
  2. `build_face(...)` (uses the original material names `Skin`/`Face`).
  3. Recolour (`assign`), extra parts (`take_part`, rigid parts attached to bones).
  4. Outlines last (`outline()`), because the outline material must be the LAST material slot.
  5. Only then the caller moves the root and assigns actions.
- Outline thickness is given in WORLD metres (default 0.010) and converted to the object's local units.
- Tests save stills under `output/tests/<task>/` (create the folder). Test stills may be overwritten by
  the next run of the same test; nothing else in `output/` is ever touched.

---

## 4. `kit/qchar.py` — Quaternius character loader (task E1)

```python
LIB: str               # ROOT + "/assets/library/quaternius/ultimate_animated_character"
NATIVE_HEIGHT = 3.147   # bald body (BaseCharacter); hair/hats are extra

@dataclass
class QChar:
    name: str
    root: bpy.types.Object
    arm: bpy.types.Object
    body: bpy.types.Object
    actions: dict[str, bpy.types.Action]      # clean name -> action, e.g. "Idle"
    scale: float                              # s
    parts: dict[str, bpy.types.Object] = field(default_factory=dict)
    face: object | None = None                # set by kit.face.build_face
```

Functions (all public, in this order in the file):

1. `strip(name: str) -> str` — returns `name.split(".")[0]`.
2. `load_character(file: str, name: str, *, height: float = 1.80, loc=(0, 0, 0), rot_z: float = 0.0,
   col=None) -> QChar` (`rot_z` in degrees, like every public angle)
   - `path = os.path.join(LIB, file)`.
   - `with bpy.data.libraries.load(path, link=False) as (src, dst):` save `names = list(src.actions)`,
     then `dst.objects = list(src.objects)` and `dst.actions = list(names)`.
   - After the block: `actions = {strip(n): a for n, a in zip(names, dst.actions)}`.
     Rename each action to `f"{name}_{clean}"`.
   - Link both objects to `col` (or the scene collection if `col` is None).
     The armature object: rename to `f"{name}_arm"` (and its data). The mesh: `f"{name}_body"` (and its data).
   - `root = C.empty(f"{name}_root", loc=loc, rot=(0, 0, rot_z), col=col)`.
   - `arm.parent = root`; `arm.location = (0, 0, 0)`; `arm.rotation_euler = (0, 0, math.pi)`;
     `arm.scale = (s, s, s)` with `s = height / NATIVE_HEIGHT`.
   - Remove any assigned action: `if arm.animation_data: arm.animation_data.action = None`.
   - Call `rest(qc)`; print `[qchar] loaded <name> from <file> (<n> actions)`; return the QChar.
3. `rest(qc) -> None` — `qc.arm.animation_data.action = None` if animation data exists; for every pose
   bone: `rotation_mode = "QUATERNION"`, location (0,0,0), rotation_quaternion (1,0,0,0), scale (1,1,1);
   then `bpy.context.view_layer.update()`.
4. `native(qc, xyz) -> Vector` — `view_layer.update()` then `qc.arm.matrix_world @ Vector(xyz)`.
5. `dominant_bone(obj, poly) -> str` — the vertex group name with the largest SUM of weights over the
   polygon's vertices; `""` if none.
6. `assign(qc, mat, *, materials=None, bones=None, z_range=None, absx_min=None, obj=None) -> int`
   - Works on `obj` (default `qc.body`). A polygon matches when ALL given filters match:
     `materials`: `strip(current material name)` is in the list; `bones`: `dominant_bone` is in the list;
     `z_range=(z0, z1)`: `z0 <= poly.center.z <= z1` (native, `poly.center` is already native);
     `absx_min`: `abs(poly.center.x) >= absx_min`.
   - Find the slot of `mat` in `obj.data.materials` or append it; set `poly.material_index`.
   - Return the number of polygons changed; print `[qchar] assign <mat.name>: <n> polygons`.
7. `delete_faces(qc, materials: list[str], obj=None) -> int` — bmesh: delete the polygons whose stripped
   material name is in `materials` (`bmesh.ops.delete(bm, geom=faces, context="FACES")`), write back,
   return the count.
8. `take_part(qc, file: str, material: str, part: str, mat) -> bpy.types.Object`
   - Load ONLY the objects of `file` (same `libraries.load` pattern, no actions).
   - Take its mesh object, make it a single-user copy of its data, rename object+data `f"{qc.name}_{part}"`,
     link it to the collection of `qc.body`.
   - Delete (bmesh) every polygon whose stripped material name is NOT `material`.
   - Clear its materials and append `mat` as the only material.
   - `obj.parent = qc.arm`, `obj.matrix_parent_inverse = Matrix.Identity(4)`, location (0,0,0),
     rotation (0,0,0), scale (1,1,1). Make sure it has exactly one `ARMATURE` modifier with `object = qc.arm`
     (keep its vertex groups — the bone names match).
   - Remove the other loaded object(s) (the file's armature) with `bpy.data.objects.remove(o, do_unlink=True)`
     and remove its armature data if it has no users.
   - Store in `qc.parts[part]`; return it.
9. `attach_part(qc, obj, bone: str, part: str) -> None` — `kit.rig.attach(obj, qc.arm, bone)`;
   `qc.parts[part] = obj`. Precondition: character at the origin in rest pose (builders guarantee it).
10. `surface_points(qc, pts_xz, *, bones: list[str], materials: list[str] | None = None, offset: float = 0.006,
    side: str = "front") -> list[Vector]`
    - Returns NATIVE points on the body surface. Build a `mathutils.bvhtree.BVHTree.FromPolygons(verts, polys)`
      from the REST mesh data of `qc.body` (native coordinates), using only polygons whose `dominant_bone` is in
      `bones` and (if given) whose stripped material is in `materials`.
    - For each `(x, z)`: `side="front"` casts a ray from `(x, -3.0, z)` in direction `(0, 1, 0)`, and the
      result is `(x, hit.y - offset, z)`; `side="back"` casts from `(x, 3.0, z)` in direction `(0, -1, 0)`
      and returns `(x, hit.y + offset, z)`. If a ray misses, use the nearest hit of the other points'
      average y (never crash); print a `[qchar] miss` line.
11. `set_action(qc, action: str, frame: int | None = None) -> None` — `arm.animation_data_create()`,
    `arm.animation_data.action = qc.actions[action]`; if `arm.animation_data.action_slot` is None, set it
    to `qc.actions[action].slots[0]`; if `frame` is given: `bpy.context.scene.frame_set(frame)`.
12. `outline(obj, world_thickness: float = 0.010) -> None` — `kit.toon.add_outline(obj,
    thickness=world_thickness / obj.matrix_world.to_scale()[0])` (call `view_layer.update()` first).
13. `height_now(qc) -> float` — evaluated (`evaluated_depsgraph_get`) world z-extent of `qc.body`.

### Test `tools/tests/t_qchar.py` (E1)
Same header as `tools/tests/t_toon.py` (ROOT on `sys.path`). Steps and assertions:
1. `C.reset_scene()`; `a = load_character("BaseCharacter.blend", "base")`.
2. `abs(height_now(a) - 1.80) < 0.01`.
3. Face points forward: mean WORLD y of all vertices used by polygons with material `Face` > 0.15.
4. Character's right is +X: `native(a, a.arm.data.bones["Fist.R"].head_local).x > 0.5`.
5. `b = load_character("Suit_Male.blend", "suit", loc=(1.5, 0, 0))`; `{"Idle", "Walk", "Run", "Punch",
   "PickUp", "Victory"} <= set(b.actions)`; `b.actions["Idle"] is not a.actions["Idle"]`;
   no object name in `bpy.data.objects` starts with `"CharacterArmature"` or equals `"Body"`.
6. `m = toon.toon("t_glove", "#1a1d26")`; `n = assign(a, m, bones=["Fist.L", "Fist.R"])`; `n > 50`.
7. `belt = take_part(a, "Casual_Male.blend", "Belt", "belt", toon.toon("t_belt", "#e3b21c"))`: it has ≥ 20
   polygons, one ARMATURE modifier whose object is `a.arm`, ≥ 1 vertex group; still no object named
   `CharacterArmature*` or `Body` afterwards.
8. Belt follows the rig: evaluated world position of belt vertex 0 before/after setting
   `a.arm.pose.bones["Body"].location = (0, 0.3, 0)` + `view_layer.update()` moves > 0.1 m. Then `rest(a)`.
9. `k = delete_faces(b, ["Hair"])`; `k > 1000`; no polygon of `b.body` has a stripped material name `Hair`.
10. `pts = surface_points(a, [(0.0, 1.6), (0.1, 1.5)], bones=CHEST)`: every `pts[i].y` is
    between −0.30 and −0.15.
11. `set_action(b, "Idle", 1)`.
12. Render one still: `look`-independent — `C.sky(C.hex_rgb("#808890"))`, `C.sun("key", energy=3.0)`,
    camera `C.camera("cam", (0.75, 5.0, 1.0), (0.75, 0, 0.9), lens=40)`, `render_settings(width=540,
    height=960, quality="final", video=False, frame_end=1)` → `output/tests/E1/still.png`.
13. `print("[test] PASS")`.

---

## 5. `kit/look.py` — look-dev: toon v2, lights, grade (task E2)

1. `toon2(name, base_hex, *, shadow_hex=None, hi_hex=None, rim_hex="#8ab4ff", rim=0.8, rim_width=0.70,
   emission=0.0) -> Material` — cached by name like `kit/toon.py`. If `emission > 0`: return
   `kit.toon.toon(name, base_hex, emission=emission)`. Otherwise build this node tree:
   - `ShaderNodeBsdfDiffuse` (Color (1,1,1,1)) → `ShaderNodeShaderToRGB` → `.outputs["Color"]` →
     `ShaderNodeRGBToBW` (output `"Val"`) = light amount **L**.
   - `ShaderNodeValToRGB` named `"ramp"`, `interpolation = "CONSTANT"`, input `"Fac"` = L, 3 elements:
     position 0.00 = shadow, 0.30 = base, 0.85 = highlight.
     Defaults: `shadow = lerp(base * 0.5, hex_rgb("#1b2440"), 0.35)` (cool), `highlight = lerp(base,
     hex_rgb("#fff1d6"), 0.22)` (warm). `lerp(a, b, t) = a + (b - a) * t` per channel.
   - Rim mask: `ShaderNodeLayerWeight` (input `"Blend"` = 0.5) output `"Facing"` → `ShaderNodeMath`
     `GREATER_THAN` (second value = `rim_width`) = A. `ShaderNodeMath GREATER_THAN` (L, 0.30) = B.
     `ShaderNodeMath MULTIPLY` (A, B) → `ShaderNodeMath MULTIPLY` (…, `rim`) = mask.
   - `ShaderNodeMix`, `data_type = "RGBA"`, `blend_type = "MIX"`; link by socket identifier:
     `inputs["Factor_Float"]` ← mask, `inputs["A_Color"]` ← ramp Color, `inputs["B_Color"]` = rim colour
     (default value), `outputs["Result_Color"]` → `ShaderNodeEmission` (Strength 1.0) → Material Output.
     (Look sockets up by `identifier`, e.g. `next(s for s in node.inputs if s.identifier == "A_Color")`.)
   - `mat.diffuse_color = (*base, 1)`.
2. `store_night(target=(0.0, 0.0, 1.0), facing_deg=0.0, *, col=None) -> dict[str, bpy.types.Object]`
   "Gotham Mart, 3 A.M." light rig. Rotate every offset below about Z by `facing_deg` and add `target`:
   - `C.sky(C.hex_rgb("#0b0f18"), 1.0)`.
   - `key = C.sun("key", energy=3.2, angle_deg=5.0, col=col)`, colour `#e4f0ff`, placed at offset
     (1.86, 3.65, 2.87) (35° up, 27° to the side of the front), `C.point_at(key, target)`.
     (Measured: toon light L ≈ 0.72·energy/π·N·L for this colour; front faces land at L ≈ 0.55–0.65.)
   - `rim = C.sun("rim", energy=3.5, angle_deg=2.0, col=col)`, colour `#8ab4ff`, offset (−2.0, −3.5, 2.0),
     `C.point_at(rim, target)`.
   - `C._set_enum(scene.view_settings, "view_transform", ["Standard"])`, `look = "None"`, exposure 0, gamma 1.
   - Return `{"key": key, "rim": rim}`.
3. `floor(size=8.0, hex_="#2b3040", col=None) -> Object` — `C.plane("floor", size=size, mat=toon2("floor", hex_, rim=0.0))`.
   Rule: rim is for characters only; sets and props use `rim=0.0` (flat surfaces seen at a grazing angle would
   turn completely rim-coloured).

### Test `tools/tests/t_look.py` (E2)
- `C.reset_scene()`; `store_night(target=(0, 0, 0.6))`; `floor()`.
- Colours (in this order): dummy `#1c1d24`, suit grey `#5d6470`, purple `#5b2a86`, yellow `#e3b21c`,
  green `#35b24a`. Column x positions: −1.6, −0.8, 0, 0.8, 1.6.
- Row 1 (y = 0, z = 1.25): spheres r = 0.3 with `toon2` + `kit.toon.add_outline(obj, 0.010)`.
- Row 2 (y = 0, z = 0.45): the same spheres with the OLD `kit.toon.toon` material + outline (comparison).
- Row 3 (y = 0, z = 2.05): five dummy-coloured spheres with `rim_width` 0.50, 0.58, 0.66, 0.74, 0.82
  (material names `rimtest_<w>`).
- Camera `C.camera("cam", (0, 6.0, 1.25), (0, 0, 1.25), lens=35)`; render 1080x1080
  (`render_settings(width=1080, height=1080, quality="final", video=False, frame_end=1)`) →
  `output/tests/E2/look.png`.
- Assert every `toon2` material has exactly one node of each type: `SHADERTORGB`, `LAYER_WEIGHT`, `MIX`,
  `VALTORGB`, `EMISSION`; ramp has 3 elements; the file exists and is > 10 kB. Print `[test] PASS`.

---

## 6. `kit/face.py` — decal face: eyes, brows, mouth shapes, expressions (task E3)

```python
@dataclass
class Face:
    eyes: dict[str, bpy.types.Object]     # "L", "R" (character's left/right)
    brows: dict[str, bpy.types.Object]    # "L", "R"
    mouths: dict[str, bpy.types.Object]   # shape name -> object
    rest_shape: str                       # mouth shape shown when silent
    base: dict[str, Matrix]               # object name -> matrix_basis right after building
```

### 6.1 `build_face(qc, *, style="plain", rest="X", paint_hex="#f4f4ef") -> Face`
Precondition: character at the origin, rest pose, original materials (call it BEFORE any `assign`).
1. `paint = kit.toon.toon(f"{qc.name}_paint", paint_hex, emission=1.0)` (flat, always bright).
2. Eyes and brows: bmesh of `qc.body`; polygons with stripped material `Face`; split into islands
   (polygons sharing an edge). Expect exactly 4 islands, else raise `RuntimeError`.
   For each island: native centre = mean of its vertices; **brow** if its max native z > 2.66, else **eye**;
   side **"L"** if centre x > 0 else **"R"** (native +X = character's left).
   Create a new mesh object `f"{qc.name}_eye.L"` / `f"{qc.name}_brow.R"` etc.: vertex positions =
   `native(qc, co) - native(qc, centre)` (world offsets), `obj.location = native(qc, centre)`, same polygons,
   material `paint`, linked to the collection of `qc.body`. Then delete those polygons from `qc.body`
   (`context="FACES"`) and `attach_part(qc, obj, "Head", obj_name_without_prefix)`.
3. Mouths: shapes are 2D outlines `(x, z)` in NATIVE units around the mouth centre (0, 2.34), built by §6.2.
   For each shape: native points `(x, 2.34 + z)` → `surface_points(qc, pts, bones=["Head"],
   materials=["Skin"], offset=0.008)` → world with `native()`. Object `f"{qc.name}_mouth_{shape}"`,
   location = world point of native `(0, -0.50, 2.34)`, one n-gon polygon made of the points (relative to
   the location), material `paint`, `attach_part(qc, obj, "Head", f"mouth_{shape}")`.
   Visibility at frame 1: `C.visible(obj, 1, shape == rest)`.
4. Store `base[obj.name] = obj.matrix_basis.copy()` for every eye, brow and mouth object.
5. `qc.face = face`; return it.

### 6.2 Mouth outlines (native units, relative to the mouth centre)
Superellipse helper: `superellipse(a, b, n=4.0, k=24)` returns k points
`(a * sgn(cos t) * |cos t|^(2/n), b * sgn(sin t) * |sin t|^(2/n))` for `t = 2π i / k`.
Band helper: `band(x0, x1, zc, half, k=13)` — along `x_i` from x0 to x1 (k points), top edge
`zc(x_i) + half(x_i)`, then back along the bottom edge `zc(x_i) - half(x_i)` (2k points, closed).

`style="plain"` shapes (Rhubarb names; G reuses B's outline, H reuses C's):
| shape | outline |
|---|---|
| `X` | superellipse(0.10, 0.012, 6) |
| `frown` | band(−0.11, 0.11, zc = 0.02 − 0.04·(x/0.11)², half = 0.013) |
| `A` | superellipse(0.11, 0.015, 6) |
| `B`, `G` | superellipse(0.10, 0.028, 4) |
| `C`, `H` | superellipse(0.11, 0.05, 3) |
| `D` | superellipse(0.12, 0.08, 2.5) |
| `E` | superellipse(0.075, 0.07, 2) |
| `F` | superellipse(0.045, 0.045, 2) |

`style="grin"` shapes: every shape is a crescent `band(−0.30, 0.30, zc, half)` with
`top(x) = 0.02 + 0.05·(x/0.30)²`, `bottom(x) = top(x) − t·(1 − (x/0.30)²)` written as
`zc = (top + bottom) / 2`, `half = (top − bottom) / 2`, and centre thickness `t` per shape:
X 0.10, A 0.06, B 0.10, C 0.13, D 0.15, E 0.13, F 0.08, G 0.10, H 0.13 (thicker dips below the flat
face front, z < 2.2).
`rest` may be `"X"` or `"frown"` (plain) — the rest shape object must exist.

### 6.3 Expressions
`EXPRESSIONS: dict[str, dict]` with keys `brow_tilt` (deg, **positive = inner end DOWN**), `brow_dz` (m),
`eye_sz`, `eye_sx` (scale factors), optional per-side overrides `brow_tilt_L/_R`, `brow_dz_L/_R`:
| name | brow_tilt | brow_dz | eye_sz | eye_sx |
|---|---|---|---|---|
| `neutral` | 0 | 0 | 1.0 | 1.0 |
| `stern` | 14 | −0.012 | 0.80 | 1.0 |
| `angry` | 24 | −0.018 | 0.70 | 1.0 |
| `surprised` | −6 | 0.025 | 1.15 | 1.10 |
| `suspicious` | L 18 / R −4 | L −0.015 / R 0.010 | 0.45 | 1.0 |
| `smug` | L −10 / R 10 | L 0.020 / R 0 | 0.60 | 1.0 |
| `deadpan` | 0 | −0.010 | 0.50 | 1.0 |

`set_expression(face, name, frame=None)`: for every part start from `base[obj.name]` (decompose to
loc/rot/scale). Brows: location z += dz; rotation about the Y axis of **+tilt for brow "L", −tilt for brow
"R"** (degrees → radians; objects are world-aligned at build time, so Y is the face normal). Eyes: scale
x *= eye_sx, z *= eye_sz. Write `matrix_basis`; if `frame` is given, key `location`, `rotation_euler`,
`scale` of the 4 parts at that frame. (The test checks the sign — if it fails, the rule above is the truth.)

`key_mouth(face, frame, shape)`: `C.visible(obj, frame, name == shape)` for every mouth object.

`blink(face, frame, expression="neutral")`: eye z-scale keyed = base value at `frame`, ×0.5 at `frame+1`,
×0.08 at `frame+2`, base at `frame+4` (base = that expression's eye_sz).

### Test `tools/tests/t_face.py` (E3)
1. `C.reset_scene()`; `a = load_character("BaseCharacter.blend", "hero")`; `f = build_face(a, rest="frown")`.
2. 2 eyes + 2 brows; no polygon of `a.body` has stripped material `Face`; 10 mouth objects
   (X, A, B, C, D, E, F, G, H, frown); at frame 1 only `hero_mouth_frown` has `hide_render == False`.
3. Every eye/brow/mouth object's world position y > 0.20 (in front of the face) and z between 1.15 and 1.60.
4. Brow sign: `set_expression(f, "angry")`, `view_layer.update()`; for each brow take its mesh vertices in
   world space and the brow's world centre c; inner = mean z of the vertices with |x| < |c.x|, outer = mean z
   of the vertices with |x| > |c.x|; assert `inner < outer - 0.005`. Then `set_expression(f, "surprised")`:
   assert `inner > outer`. (The original brows are horizontal 3D bars, so neutral gives inner ≈ outer.)
5. Follows the head: world position of eye L before/after rotating pose bone `Head` 25° about its local X
   (`rotation_quaternion` from `Euler((radians(25), 0, 0))`) differs by > 0.02 m. Then `rest(a)`
   and `set_expression(f, "neutral")`.
6. `C.reset_scene()`; `g = load_character("Suit_Male.blend", "grinner")`;
   `build_face(g, style="grin", rest="X")`; assert 9 mouth objects (X, A–H).
7. Stills (540x540, `store_night` lights from `kit.look`, camera `C.camera("cam", (0, 1.35, 1.46),
   (0, 0, 1.42), lens=50)`): for the grinner: `expr_<name>.png` for all 7 expressions (mouth X), then
   `mouth_<shape>.png` for X, A, B, C, D, E, F (expression neutral) → `output/tests/E3/`.
   Rebuild the hero (reset, load, build_face rest frown) and render `hero_stern.png` and `hero_D.png`.
8. `print("[test] PASS")`.

---

## 7. `kit/cast.py` — the recurring cast (task E4)

Common: `CHEST = ["Torso", "Abdomen", "Shoulder.L", "Shoulder.R"]` (measured: the big chest-centre
quad is dominated by `Shoulder.L`, so a Torso/Abdomen-only filter misses it). `DUMMY = "#1c1d24"` (the skin of every character — our "dummy" house style: black body, white
eyes). All materials via `kit.look.toon2`. Every builder follows the build order of §3 and returns the QChar.
Smoothing (look-dev decision, senior test 2026-09-24): add to `kit/qchar.py`
`smooth(qc, obj=None, levels=1)` — on `obj` (default `qc.body`): remove a modifier named `"Auto Smooth"` if
present, add a `SUBSURF` modifier named `"smooth"` (levels = render_levels = `levels`) and move it to index 1
(right after `Armature`, with `obj.modifiers.move(from, to)`), set `use_smooth = True` on every polygon.
Builders call `smooth()` on the body right before the outlines (the outline must stay the LAST modifier).
`CAST = {"batman": build_batman, "joker": build_joker}`.

### 7.1 `build_batman(col=None) -> QChar`
1. `qc = load_character("BaseCharacter.blend", "batman", col=col)`; `build_face(qc, rest="frown")`;
   `set_expression(qc.face, "stern")`.
2. Materials: `suit = toon2("bat_suit", "#5d6470")`, `dark = toon2("bat_dark", "#1a1d26")`,
   `gold = toon2("bat_gold", "#e3b21c")`, `ink = toon2("bat_ink", "#111318")`.
3. Recolour, in this order: `assign(qc, suit, materials=["Skin"])`; `assign(qc, dark, bones=["Head", "Neck"])`;
   `assign(qc, dark, bones=["Fist.L", "Fist.R"])`; `assign(qc, dark, bones=["LowerArm.L", "LowerArm.R"],
   absx_min=1.06)`; `assign(qc, dark, bones=["Foot.L", "Foot.R"])`; `assign(qc, dark,
   bones=["LowerLeg.L", "LowerLeg.R"], z_range=(-1.0, 0.40))`.
4. Belt: `take_part(qc, "Casual_Male.blend", "Belt", "belt", gold)`, then inflate it (it was made for Casual's
   trousers and sits flush with the bare body): bmesh of the belt mesh, `v.co += v.normal * 0.03` for every
   vertex (native units, normals from `bm.normal_update()`), write back.
5. Ears: for side sign `k = +1` (native +X) and `k = −1`: native base `(k*0.27, 0.0, 2.99)`, tip
   `(k*0.31, 0.0, 3.30)`; world `b = native(base)`, `t = native(tip)`; `C.cone(f"batman_ear.{L|R}",
   r1=0.10*s, r2=0.0, depth=(t-b).length, loc=(b+t)/2, mat=dark, verts=12)`, then set
   `ear.rotation_euler = (t-b).to_track_quat("Z", "Y").to_euler()` (radians, assigned directly); `attach_part(qc, ear, "Head", "ear.L"/"ear.R")`.
   (k = +1 is the character's LEFT.)
6. Cape (one bmesh sheet, native coordinates, then converted with `native()`): grid of 17 columns
   `u = -1 … 1` and 10 rows `v = 0 … 1`. Bottom edge `zb(u) = 0.30 + 0.12·|sin(2πu)|` (5 bat points).
   Vertex: `z = lerp(2.02, zb(u), v)`, `x = u · lerp(0.36, 0.62, v)`,
   `y = lerp(0.20, 0.55, v) − lerp(0.04, 0.12, v) · u²` (native +Y is the BACK). Quads between neighbours.
   Object `batman_cape` (origin = world point of native (0, 0.20, 2.02)), material `dark`,
   `use_backface_culling = False` on `dark`; a `SOLIDIFY` modifier named `"thick"` (thickness 0.012 world,
   offset 0) added BEFORE the outline; `attach_part(qc, cape, "Torso", "cape")`.
7. Chest emblem (Torso front, centre native (0, 1.62)): oval = superellipse(0.15, 0.08, 2, k=32) points
   → `surface_points(qc, …, bones=CHEST, offset=0.006)`; bat = the points below ×0.236
   (centred on the same centre) → `surface_points(…, offset=0.012)`. Objects `batman_emblem` (gold) and
   `batman_bat` (ink), each one n-gon, both `attach_part(…, "Torso", …)`. No outline on either.
   Bat outline, right half (x, z) from the top centre; mirror it (x → −x, reverse order, skip the two
   points on x = 0) to close the polygon:
   `(0.00,0.08) (0.04,0.08) (0.055,0.18) (0.08,0.08) (0.15,0.11) (0.30,0.17) (0.50,0.21) (0.46,0.08)
   (0.40,0.00) (0.35,0.05) (0.30,-0.04) (0.24,0.00) (0.19,-0.08) (0.13,-0.05) (0.06,-0.13) (0.00,-0.20)`
   (then multiply every coordinate by 0.88 × 0.268 = 0.236).
8. `smooth(qc)` on the body; `smooth(qc, obj=cape)`. Outlines (0.010 world) on: body, belt, ears, cape.
   Not on face parts, emblem, bat.

### 7.2 `build_joker(col=None) -> QChar`
1. `qc = load_character("Suit_Male.blend", "joker", col=col)`; `build_face(qc, style="grin", rest="X")`;
   `set_expression(qc.face, "smug")`.
2. Recolour: `Black` → `toon2("jok_suit", "#5b2a86")`; `Shirt` → `toon2("jok_vest", "#3e9b4f")`;
   `Details` → `toon2("jok_tie", "#e08a1e")`; `Belt` → `toon2("jok_belt", "#2a1f3d")`;
   `Skin` → `toon2("jok_skin", DUMMY)`; `Hair` → `toon2("jok_hair", "#35b24a")`.
3. Name tag across the chest: rounded rectangle superellipse(0.17, 0.055, 6, k=32) centred at
   native (0.0, 1.66) → `surface_points(…, bones=CHEST, offset=0.010)` (the jacket front is
   at the same depth as BaseCharacter's chest); object `joker_tag`, material `toon2("tag_white", "#f2f2ee")`,
   `attach_part(…, "Torso", "tag")`. Text: `C.text("joker_tag_text", "ASSISTANT", size=0.03,
   extrude=0.0, loc=<world point of native (0, -0.5, 1.66) projected: the tag centre moved 0.004 m toward +Y>,
   rot=(90, 0, 180), mat=toon2("tag_ink", "#111318"))` — rot (90, 0, 180) makes the text face +Y (the
   character's front) and read left-to-right for a camera in front. Then scale it uniformly so its
   `dimensions.x` (after `view_layer.update()`) is 0.9 × the tag's world width; `attach_part(…, "Torso", "tag_text")`.
4. `smooth(qc)`, then outline (0.010) on the body only.

### 7.3 `tools/turnaround.py` — stills for review (task E4)
`blender -b --factory-startup --python tools/turnaround.py -- --cast batman,joker --out output/tests/E4`
For each name: `C.reset_scene()`; `qc = CAST[name]()`; `store_night(target=(0, 0, 0.9))`; `floor()`;
`set_action(qc, "Idle", 1)`; render at 540x960 `quality="final"`:
| view | camera position → look-at | lens |
|---|---|---|
| `front` | (0, 4.6, 1.05) → (0, 0, 0.9) | 50 |
| `threeq` | (2.64, 3.77, 1.05) → (0, 0, 0.9) | 50 |
| `side` | (4.6, 0, 1.05) → (0, 0, 0.9) | 50 |
| `back` | (0, −4.6, 1.05) → (0, 0, 0.9) | 50 |
| `face` | (0, 1.40, 1.48) → (0, 0, 1.42) | 50 |
| `sil` | as `front`, with `view_layer.material_override` = black emission, world `#ffffff`, resolution 25 % | 50 |
Files: `<out>/<name>_<view>.png`. Then `--lineup`: one scene with both characters (Batman root at
(−0.55, 0, 0) rot_z −12°, Joker at (0.55, 0, 0) rot_z 12°), camera (0.6, 4.2, 1.2) → (0, 0, 0.95),
lens 40, 1080x1350 → `<out>/lineup.png`.

### Test `tools/tests/t_cast.py` (E4)
For each builder (with `C.reset_scene()` between): Batman height 1.80 ± 0.02, Joker 1.80–1.95 (hair) (`height_now`); Batman has parts
`belt, ear.L, ear.R, cape, emblem, bat` (+ face parts); Joker has `tag`, `tag_text`; the outline material is
the LAST slot of every outlined object; both ears are above the head top (world z > 1.70) and on opposite
sides (x signs differ); the cape's world mean y < −0.05 (behind the character). Print `[test] PASS`.

---

## 8. After checkpoint 1 (outline — detailed later, after the owner's review)
- Spring cape: bone chains in the cape + damped-spring secondary motion baked to keys.
- Set "Gotham Mart 3 A.M.": Kenney Mini Market props (`assets/library/kenney/kenney_mini-market`), a
  self-checkout built in code (screen with text), one flickering tube light, mist, grade.
- Motion: NLA helper for Quaternius actions + FK pose keys (slam, batarang throw, screen grab, smoke bomb,
  walk-in), contact checks.
- Shot library v1 (auto-framed from bounding boxes), captions, hook check, dead-time check, `social.md`.
- Audio: casting sheets (Batman cloned + modified per the voice policy, Joker, flat machine voice),
  Rhubarb mouth keys, real SFX (Kenney interface sounds for beeps), music (Mystery Sax / Hidden Agenda).

---

## 9. Tasks (checkpoint 1)

| task | files you may edit | check (the supervisor runs it) |
|---|---|---|
| **E1** qchar | `kit/qchar.py`, `tools/tests/t_qchar.py` | `t_qchar.py` prints `[test] PASS` |
| **E2** look | `kit/look.py`, `tools/tests/t_look.py` | `t_look.py` prints `[test] PASS`; senior reviews `look.png` |
| **E3** face | `kit/face.py`, `tools/tests/t_face.py` | `t_face.py` prints `[test] PASS`; senior reviews the stills |
| **E4** cast | `kit/cast.py`, `tools/turnaround.py`, `tools/tests/t_cast.py` | `t_cast.py` PASS, then turnaround stills |

Check command pattern: `/f/blender/blender.exe -b --factory-startup --python-exit-code 1 --python tools/tests/t_<x>.py`

## 10. Review (senior)
After each task: `ACCEPT E<n>` or a numbered fix list. Checkpoint 1 is shown to the owner as one sheet:
look-dev grid, Batman and Joker turnarounds, face close-ups, silhouettes, the line-up still.
Time and findings go into `docs/EP02_LOG.md`.
