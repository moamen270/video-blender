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
| 2 | screen test clip: Batman walks in (spring cape), both characters speak with lip sync, blinks | F1–F4 (§11) |
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
     hex_rgb("#fff1d6"), 0.06 + 0.16 * max(base))` (warm; only a subtle sheen on near-black). `lerp(a, b, t) = a + (b - a) * t` per channel.
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
3. Name tag across the chest: rounded rectangle superellipse(0.22, 0.07, 6, k=32) centred at
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
| `face` | (0, 2.10, 1.50) → (0, 0, 1.38) | 50 |
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


---

## 11. Checkpoint 2 — spring cape, motion, voice + lip sync, screen test (tasks F1–F4)

Owner decisions after checkpoint 1 (2026-09-24): keep the "dummy" house style, the chibi proportions, and the
Joker's name tag (no apron).

### 11.1 `kit/cape.py` — skinned cape with baked spring motion (task F1)

Replaces the rigid cape of §7.1 step 6. Everything in NATIVE coordinates unless stated.

**Grid** (unchanged shape): `P(u, v)` with `z = lerp(2.02, zb(u), v)`, `x = u·lerp(0.36, 0.62, v)`,
`y = lerp(0.20, 0.55, v) − lerp(0.04, 0.12, v)·u²`, `zb(u) = 0.30 + 0.12·|sin(2πu)|`; 17 columns
`u = −1 … 1`, 10 rows `v = 0 … 1`.

**Bones** — `add_cape_bones(qc) -> dict[str, list[str]]`: enter EDIT mode on `qc.arm`
(`view_layer.objects.active = qc.arm`; `bpy.ops.object.mode_set(mode="EDIT")`), create 3 chains × 3 bones:
chain `"R"` at u = −1, `"C"` at u = 0, `"L"` at u = +1 (native +X = character's left). Bone
`f"cape.{c}.{j}"` (j = 0, 1, 2): head = `P(u_c, j/3)`, tail = `P(u_c, (j+1)/3)` (armature data coordinates
= native), `use_deform = True`, `roll = 0`. Parent of `cape.{c}.0` = `Torso` (`use_connect = False`);
parent of `cape.{c}.j` = `cape.{c}.{j-1}` (`use_connect = True`). Back to OBJECT mode. Return
`{"R": [...3 names], "C": [...], "L": [...]}`.

**Mesh + weights** — `build_cape(qc, mat) -> Object`: call `add_cape_bones`; build the grid mesh in NATIVE
coordinates (object `f"{qc.name}_cape"`, `parent = qc.arm`, `matrix_parent_inverse = identity`, identity
local transform, linked to the body's collection), quads between neighbours, material `mat`.
Vertex groups: the 9 cape bone names and `"Torso"`. For a vertex at `(u, v)`:
- chain weights: `u ≤ 0`: `wR = −u`, `wC = 1 + u`; `u > 0`: `wC = 1 − u`, `wL = u`;
- segment weights with `s = 3v`: `w_j = max(0, 1 − |s − (j + 0.5)|)` for j = 0, 1, 2, then divide by their sum;
- torso weight `wT = max(0, 1 − v / 0.15)` (pins the top edge to the shoulders);
- final: `Torso = wT`, `cape.{c}.{j} = (1 − wT) · w_c · w_j`; skip weights < 0.001.
Modifiers in this order: `ARMATURE` (object `qc.arm`), `SOLIDIFY` `"thick"` (thickness `0.012 / qc.scale`,
offset 0 — local units are native), then the caller adds `smooth` and the outline.
`qc.parts["cape"] = cape`. Return it.

**Spring bake** — `bake_cape(qc, start, end, *, stiffness=0.12, drag=0.18, max_forward=0.02) -> None`.
Must be called LAST in a project build (after all root keys and NLA strips exist). It uses no depsgraph
update except one `scene.frame_set(f)` per frame. Let `A = qc.arm`, `Rest(b) = A.data.bones[b].matrix_local`
(armature space). For each frame `f = start … end`:
1. `scene.frame_set(f)`; `Mw = A.matrix_world` (read after `frame_set`; it changes with the root);
   `Mt = A.pose.bones["Torso"].matrix` (armature space);
   `rigid(b) = Mt @ Rest("Torso").inverted() @ Rest(b)` — where cape bone `b` would be if the cape were rigid.
2. For each chain `c`: armature-space points `h0 = rigid(cape.c.0).translation` and the rigid tails
   `t_j = rigid(cape.c.j) @ Vector((0, len_j, 0))` for j = 0, 1, 2 with `len_j = A.data.bones[cape.c.j].length`.
   World: root `X_0 = Mw @ h0` (fixed), targets `T_k = Mw @ t_{k−1}` for k = 1, 2, 3.
3. Particles `X_k`, `Xprev_k` (world, per chain, k = 1..3). At `f == start`: `X = Xprev = T`.
   Otherwise: `vel = (X − Xprev)·(1 − drag)`; `Xnew = X + vel + stiffness·(T − X)`; `Xprev = X`; `X = Xnew`.
4. Body collision: `fwd = (qc.root.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()`; for each k:
   `e = (X_k − T_k)·fwd`; if `e > max_forward`: `X_k −= (e − max_forward)·fwd`.
5. Lengths (root to tip, k = 1..3): `X_k = X_{k−1} + (X_k − X_{k−1}).normalized() · len_{k−1} · sw` with
   `sw = Mw.to_scale()[0]`.
6. Bone rotations, chain root to tip, in ARMATURE space. `Minv3 = Mw.inverted().to_3x3()`. For j = 0, 1, 2 with
   bone `b = cape.c.j`, parent `p` (`Torso` for j = 0, else `cape.c.{j−1}`), `M_parent = Mt` for j = 0 else the
   `M_{j−1}` computed here:
   `M0 = M_parent @ Rest(p).inverted() @ Rest(b)`; `R0 = M0.to_quaternion()`;
   `y0 = (M0.to_3x3() @ Vector((0, 1, 0))).normalized()`; `d = (Minv3 @ (X_{j+1} − X_j)).normalized()`;
   `q = y0.rotation_difference(d)`; `basis = R0.inverted() @ q @ R0`;
   `pb.rotation_mode = "QUATERNION"`; `pb.rotation_quaternion = basis`;
   `pb.keyframe_insert("rotation_quaternion", frame=f)`;
   `M_j = Matrix.Translation(M0.translation) @ (q @ R0).to_matrix().to_4x4()`.
7. Keep `X`, `Xprev` in Python for the next frame (do not store them in Blender).
The keys go into the armature's ACTIVE action (created by `keyframe_insert`); body motion lives in NLA strips
(§11.2), so the two never overwrite each other. After the bake do not call `qchar.set_action`.

### 11.2 `kit/motion.py` — NLA actions, walking, turning (task F2)

All body animation goes into NLA strips (never `animation_data.action`, which is reserved for the cape bake).
1. `play(qc, action, start, frames, *, blend_in=0) -> NlaStrip` — creates a NEW NLA track on top
   (`qc.arm.animation_data_create()`; `qc.arm.animation_data.nla_tracks.new()`, name `f"{action}@{start}"`),
   a strip `track.strips.new(f"{action}@{start}", start, qc.actions[action])`, sets
   `strip.repeat = frames / action_length` (`action_length = act.frame_range[1] − act.frame_range[0]`),
   `strip.blend_in = blend_in`, `strip.extrapolation = "HOLD_FORWARD"`, `strip.blend_type = "REPLACE"`.
   Each new strip is on a higher track, so a new action cross-fades over the one below (only `blend_in`,
   never `blend_out`). (Measured: `strips.new` assigns the action slot automatically in Blender 5.2.)
2. `ground_speed(qc, action) -> float` — world metres per frame of a looping locomotion action. Mute every NLA
   track, set the action as the active action (with its slot), for every integer frame in the action's range read
   the ARMATURE-space heads of pose bones `Foot.L` and `Foot.R` (after `scene.frame_set`); a foot is planted on
   frames where its z ≤ (its minimum z over the cycle) + 0.03; speed = mean of |Δy| between consecutive planted
   frames of the same foot; unmute, set the active action back to its previous value. Return
   `speed_native · qc.scale`. Cache per `(qc.name, action)` in a module dict. (Senior measurement for Walk:
   ≈ 0.10 native ≈ 0.058 world m/frame, cycle 30 frames, in place.)
3. `key_root(qc, frame, *, loc=None, heading=None)` — keys `qc.root` location and/or rotation z (heading in
   degrees, 0 = facing world +Y, 90 = facing world −X; `rotation_euler.z = radians(heading)`), LINEAR
   interpolation on the keys it inserts (`C.set_interp_at`).
4. `foot_track(qc, action) -> dict` — cached per `(qc.name, action)`: sample the action exactly like
   `ground_speed` (mute NLA, active action, restore) and return `{"len": L, "L": [(y, z) for p in 0..L],
   "R": [...]}` — native armature-space heads of `Foot.L` / `Foot.R` for every phase p = 0 … L (inclusive).
   `ground_speed` may reuse it.
   **Why (senior measurement 2026-09-24):** the Quaternius Walk is NOT a constant-speed cycle — the planted
   foot slows down inside every step, so a constant root speed makes the feet skate up to 0.025 m/frame.
   `walk_to` therefore extracts the root motion from the animation (the planted foot stays locked).
5. `walk_to(qc, start, to_xy, *, action="Walk", turn_frames=6, blend=6) -> tuple[int, list[int]]`
   - `had_tracks = len(qc.arm.animation_data.nla_tracks) > 0` (create animation data first).
   - `p0` = root location at `start` (`scene.frame_set(start)`); `d = Vector(to_xy) − p0.xy`; `dist = d.length`;
     `u = d.normalized()`; `heading = degrees(atan2(−d.x, d.y))`; current heading = `degrees(root.rotation_euler.z)`;
     `key_root(start, heading=current)`, `key_root(start + turn_frames, heading=heading)`; `key_root(start, loc=p0)`.
   - Root motion loop: `tr = foot_track(qc, action)`, `L = tr["len"]`, `cum = 0`, `f = start`, `prev_sup = None`,
     `steps = []`. Repeat: `p = (f − start) % L`; `sup = "L" if tr["L"][p][1] <= tr["R"][p][1] else "R"`;
     if `prev_sup` is not None and `sup != prev_sup`: `steps.append(f)`; `prev_sup = sup`;
     `delta = max(0.0, tr[sup][p + 1][0] − tr[sup][p][0]) · qc.scale` (the planted foot moves toward native +Y =
     backward, so the root advances by that amount); if `had_tracks` and `f − start < blend`:
     `delta *= (f − start + 1) / blend` (ease in while the walk fades in); `cum += delta`; `f += 1`;
     if `cum >= dist`: `key_root(f, loc=(to_xy[0], to_xy[1], p0.z))` and stop; else
     `key_root(f, loc=p0 + u·cum)` (z = p0.z). Raise `RuntimeError` if `f − start > 20·L`.
   - `n = f − start`; `play(qc, action, start, n + blend, blend_in=blend if had_tracks else 0)`;
     `play(qc, "Idle", start + n, 240, blend_in=blend)`. Return `(start + n, steps)`.
6. `turn_to(qc, frame, heading, frames=8)` — keys the current heading at `frame` and `heading` at `frame + frames`.

### 11.3 Voice, lip sync, blinks (task F3)

1. `projects/<p>/lines.json` (written by the senior): list of `{id, character, text, engine, voice | voiceRef,
   emotion, speed, seed}`.
2. `tools/voice.py` (system Python: `uv run --project F:/PoCs/video-builder/py python tools/voice.py --project <p>`):
   - imports `narrate`, `chatterbox` from `tools/audio.py` (put the tools folder on `sys.path`, `import audio`);
   - out dir `projects/<p>/voice/`; manifest `projects/<p>/voice/manifest.json`;
   - `hash` = sha1 of `json.dumps({text, engine, voice, voiceRef, emotion, speed, seed}, sort_keys=True)`;
     a line is re-synthesised only if its wav is missing or its hash changed (group the changed lines by engine
     as `audio.main` does: Kokoro by voice, Chatterbox together). `narrate`/`chatterbox` write `<id>.wav` into
     the dir you give them — give them `projects/<p>/voice/`;
   - for every line run Rhubarb: `F:/PoCs/tools/Rhubarb-Lip-Sync-1.14.0-Windows/rhubarb.exe -q -f json
     -o <dir>/<id>.rhubarb.json --dialogFile <dir>/<id>.txt <dir>/<id>.wav` (write the text file first);
     output format (measured): `{"metadata": {...}, "mouthCues": [{"start": 0.0, "end": 0.08, "value": "X"}, ...]}`;
   - manifest: `{"lines": {id: {"wav": <absolute path>, "seconds": <float>, "hash": ..., "text": ...,
     "character": ..., "cues": <the mouthCues list>}}}`; print `[voice] <id> <seconds>s <n> cues`.
3. `tools/audio.py`: a cue line that has a `"wav"` key is loaded with `load_wav(line["wav"])` and never
   synthesised (only lines without `"wav"` go to `narrate` / `chatterbox`). Nothing else changes.
4. `kit/face.py` additions (do not change existing functions):
   - `apply_lipsync(face, cues, start_frame, fps=24) -> int` — for each cue: `f = start_frame +
     round(cue["start"] * fps)`; shape = `face.rest_shape` if the value is `"X"` else the value; `key_mouth(face,
     f, shape)`. After the last cue key the rest shape at `start_frame + round(last["end"] * fps)`. Return that frame.
   - `change_expression(face, frame, from_name, to_name, frames=4)` — `set_expression(face, from_name, frame)`
     then `set_expression(face, to_name, frame + frames)`.
   - `auto_blink(face, start, end, schedule, *, seed=0, gap=(48, 110)) -> list[int]` — `schedule` = sorted list
     of `(frame, expression)`; `rng = random.Random(seed)`; candidate blink frames start at `start + 12` and
     advance by `rng.randint(*gap)` while `< end − 4`; skip a candidate within 6 frames of a schedule entry; call
     `blink(face, f, expression_active_at_f)`. Return the blink frames.

### 11.4 `projects/cp2/script.py` — the screen test (task F4)

A ~9 s test clip for the owner: Batman walks in (spring cape), turns to camera, says his line with lip sync;
the Joker answers. Structure like `projects/samurai/script.py`: constants at the top, `build()` at the bottom.
Voice lines come from `projects/cp2/voice/manifest.json` (already generated by `tools/voice.py`); the build
reads it and never synthesises anything.

**Constants** (world metres, frames at 24 fps):
`BAT_START = (-2.5, 0.2)`, `BAT_STOP = (-0.40, 0.2)`, `JOK_AT = (0.45, 0.0)`.
(Camera looks from +Y toward −Y, so world −X is on the RIGHT of the image: Batman enters from the right.)

**build()** — in this order:
1. `C.reset_scene()`; `look.store_night(target=(0.0, 0.0, 1.0))`; `look.floor(size=14.0)`;
   back wall: `C.plane("wall", size=14.0, loc=(0, -3.0, 7.0), rot=(90, 0, 0), mat=look.toon2("wall",
   "#161b27", rim=0.0))`.
2. `bat = cast.build_batman()`, `jok = cast.build_joker()` (both built at the origin — required); then
   `bat.root.location = (*BAT_START, 0)`, `jok.root.location = (*JOK_AT, 0)`;
   `motion.key_root(bat, 1, loc=(*BAT_START, 0), heading=-90.0)` (faces world +X, the walking direction);
   `motion.key_root(jok, 1, loc=(*JOK_AT, 0), heading=0.0)`.
3. `man = json.load(projects/cp2/voice/manifest.json)["lines"]`; `L1 = ceil(man["bat1"]["seconds"] * 24)`,
   `L2 = ceil(man["jok1"]["seconds"] * 24)`.
4. Motion: `walk_end, steps = motion.walk_to(bat, 1, BAT_STOP)`; `motion.turn_to(bat, walk_end + 2, 0.0,
   frames=8)`; `motion.play(jok, "Idle", 1, 400)`.
5. Timeline: `LINE1 = walk_end + 18`; `ANGRY = LINE1 + L1 - 10`; `LINE2 = LINE1 + L1 + 14`;
   `END = LINE2 + L2 + 30`. `scene.frame_end = END`.
6. Faces: `face.set_expression(bat.face, "stern", 1)`; `face.change_expression(bat.face, ANGRY, "stern",
   "angry")`; `face.apply_lipsync(bat.face, man["bat1"]["cues"], LINE1)`;
   `face.set_expression(jok.face, "smug", 1)`; `face.apply_lipsync(jok.face, man["jok1"]["cues"], LINE2)`;
   `face.auto_blink(bat.face, 1, END, [(1, "stern"), (ANGRY, "angry")], seed=1)`;
   `face.auto_blink(jok.face, 1, END, [(1, "smug")], seed=2)`.
7. Cameras (`C.camera`, then `C.cut(frame, cam)`):
   | name | from frame | position → look-at | lens |
   |---|---|---|---|
   | `cam_wide` | 1 | (0.0, 5.6, 1.15) → (−0.2, 0.0, 0.9) | 35 |
   | `cam_bat` | LINE1 − 8 | (−0.15, 2.3, 1.40) → (−0.40, 0.2, 1.22) | 50 |
   | `cam_jok` | LINE2 − 6 | (0.20, 2.3, 1.40) → (0.45, 0.0, 1.22) | 50 |
   | `cam_two` | LINE2 + L2 + 8 | (0.0, 3.6, 1.30) → (0.0, 0.0, 1.0) | 40 |
8. `cape.bake_cape(bat, 1, END)` — LAST, after everything that moves Batman.
9. `cues.json` (write `projects/cp2/cues.json`, same format as `projects/samurai/cues.json`):
   `{"fps": 24, "frames": END, "music": {"file": "F:/PoCs/blender-video/assets/library/music/Hidden Agenda.mp3",
   "start_s": 0, "gain": 0.30}, "lines": [{"id": "bat1", "frame": LINE1, "text": ..., "wav": man["bat1"]["wav"]},
   {"id": "jok1", "frame": LINE2, "text": ..., "wav": man["jok1"]["wav"]}], "sfx": [{"frame": f, "sfx":
   "step_hard", "gain": 0.35} for f in steps], "overlays": []}`.
10. Print `[cp2] walk_end=… LINE1=… LINE2=… END=…`.

Check (supervisor): `blender -b --python tools/build.py -- --project cp2 --out output/tests/F4 --quality draft
--no-render` exits 0 and prints the `[cp2]` line; then the senior runs `sh tools/make.sh cp2 preview`.


### 11.5 Tasks (checkpoint 2)

| task | files you may edit | check |
|---|---|---|
| **F1** cape | `kit/cape.py`, `kit/cast.py` (use `build_cape` instead of the rigid cape), `tools/tests/t_cape.py` | `t_cape.py` PASS and `t_cast.py` still PASS |
| **F2** motion | `kit/motion.py`, `tools/tests/t_motion.py` | `t_motion.py` PASS |
| **F4** screen test | `projects/cp2/script.py` | `tools/build.py --project cp2 --no-render` exits 0 with the `[cp2]` line |
| **F3** voice | `tools/voice.py`, `tools/audio.py`, `kit/face.py` (additions only), `tools/tests/t_lipsync.py` | `voice.py --project cp2`, then `t_lipsync.py` PASS |

**t_cape.py (F1):** build Batman (`kit.cast.build_batman`); root keyed (LINEAR): frames 1 and 24 at (0, 0, 0);
(0, 2.8, 0) at frame 72; held (same key) at frame 132. `bake_cape(qc, 1, 132)`. Helper `targets(f)` recomputes
the rigid tail targets exactly as bake steps 1–2 (world). Measure the baked result as the WORLD tail of the pose
bone: `A.matrix_world @ A.pose.bones[b].tail` after `scene.frame_set(f)`. Assert:
(a) frame 20: the tail of `cape.C.2` is within 0.01 m of its target;
(b) frame 60 (moving forward at 0.058 m/frame): `(tail − target)·fwd < −0.04` (the cape streams behind);
(c) frame 132 (60 frames after the stop): within 0.02 m of the target again;
(d) every frame 1–132, every chain's last tail: `(tail − target)·fwd ≤ 0.021`;
(e) skinning: at frame 60, the evaluated cape mesh vertex nearest (in rest) to native `P(0, 1)` is within 0.04 m of
the world tail of `cape.C.2` (evaluate with `evaluated_depsgraph_get`, `obj.evaluated_get(dg).to_mesh()`, compare
in world space; the solidify doubles vertices — use the vertex nearest to the tail).
`t_cast.py` must still pass (Batman keeps a part named `cape`). Render side-view stills (camera
(4.5, 1.4, 1.0) → (0, 1.4, 0.9), lens 40, 540x960, `store_night`, `floor`) at frames 20, 48, 60, 72, 84, 100
to `output/tests/F1/cape_<f>.png`.

**t_motion.py (F2):** `qc = load_character("Suit_Male.blend", "walker")` (not `kit.cast`);
`play(qc, "Idle", 1, 30)`; `end, steps = walk_to(qc, 10, (0, 3.0))`. Assert:
(a) at frame `end` the root world position is within 0.001 m of (0, 3.0); `30 < end − 10 < 80`;
(b) foot lock — for every f in `17 … end − 2`: `lo` = the foot (`Foot.L` / `Foot.R`) with the lower WORLD z at
f; if the same foot is also the lower one at f + 1, its horizontal world displacement between f and f + 1 is
< 0.006 m (print the largest value);
(c) `len(steps) >= 3`, strictly increasing, consecutive gaps between 10 and 20 frames;
(d) the top NLA track's strip action is the walker's Idle action;
(e) `turn_to(qc, end + 12, 90)`; at `end + 20` the root heading is 90° ± 0.5.
Render frames 12, 24, 36, end, end + 20 (camera (4.0, 1.5, 1.1) → (0, 1.5, 0.9), lens 35, 540x960,
`store_night`, `floor`) to `output/tests/F2/`.

**t_lipsync.py (F3):** reads `projects/cp2/voice/manifest.json` (asserts lines `bat1` and `jok1` exist, seconds >
0.5, ≥ 5 cues each, wav files exist); `qc = load_character("BaseCharacter.blend", "hero")`,
`face = build_face(qc, rest="frown")` (not `kit.cast` — F1 edits it in parallel), `apply_lipsync(face, cues_bat1, 10)`; for every cue whose
frame differs from the next cue's frame, at that frame exactly one mouth object has `hide_render == False` and it
is the cue's shape (rest shape for `"X"`); `auto_blink(face, 1, 240, [(1, "stern")])` returns ≥ 2 blinks, no two
closer than 48 frames; render 4 face stills at the frames of cues 1, 3, 5, 7 (camera (0, 2.1, 1.5) →
(0, 0, 1.38), lens 50, 540x960, `store_night`) to `output/tests/F3/`.


---

## 12. Checkpoint 3 — the whole episode as an animatic (tasks G1–G7)

Owner (2026-09-24): voices approved (casting sheet `assets/cast/voices.json`). Goal of checkpoint 3: the full
episode with its final timing, shots, voices, lip sync, captions, set, props and rough actions. Polish (mist,
grade, FX detail, secondary motion) is checkpoint 4. Voices are generated: `projects/ep02/voice/manifest.json`.

World conventions for this episode: the self-checkout stands at the world origin and FACES +Y (its screen faces
+Y); the customer stands in front of it at +Y and faces −Y. Kenney props are scaled ×2.4 (measured: Kenney walls
are 1.0 tall, shelves 0.85–1.05, floor tiles 1×1).

### 12.1 `kit/props.py` + `kit/checkout.py` (task G1)
Rules: materials `kit.look.toon2(..., rim=0.0)` unless stated; outlines with `kit.qchar.outline(obj, t)`-style
world thickness (use `kit.toon.add_outline(obj, thickness=t / obj.matrix_world.to_scale()[0])`); every prop is ONE
mesh object (build with bmesh; text is converted with `bpy.data.meshes.new_from_object(text_obj)` and merged into the
prop's bmesh, then the text object is deleted) so that `obj.copy()` duplicates it completely. Origins as stated.

`kit/props.py`:
1. `milk(name="milk", loc=(0, 0, 0), col=None) -> Object` — carton 0.12 × 0.12 × 0.24 (x, y, z) white `#f2f2ee`,
   gable top: a triangular prism 0.12 wide (x), 0.12 deep, 0.05 high on top (ridge along x), a blue band
   `#2e6fd8` 0.06 high around the carton at z 0.09–0.15 (4 thin quads 2 mm outside the faces), the word "MILK"
   (white `#f2f2ee`, text size 0.045, extrude 0) on the +Y face of the band (convert with
   `bpy.data.meshes.new_from_object(text_obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))`). Origin at the bottom centre.
   Outline 0.004.
2. `batarang(name="batarang", loc=(0, 0, 0), col=None) -> Object` — the bat outline of §7.1 step 7 (mirrored,
   32 points) scaled so its width is 0.30, as a flat polygon in the XY plane (x = width, y = the outline's z),
   extruded 0.012 (bmesh extrude + translate), material `#1a1d26`, origin at the centre. Outline 0.003.
3. `smoke_puff(name, center, frame, *, count=9, radius=0.9, seed=0, col=None) -> list[Object]` — `count` icospheres
   (subdiv 2, smooth) of radius `rand(0.25, 0.45)` placed at `center + (rand(−r, r), rand(−r·0.6, r·0.6),
   rand(0.1, 1.3))` (`random.Random(seed)`), material `toon2("smoke", "#9aa0ab", rim=0.0)`, outline 0.008. Scale keys:
   0 at `frame − 1`, 1.15 at `frame + 3`, 1.0 at `frame + 6`, hold until `frame + 30 + i`, 0 at `frame + 42 + i`
   (i = index); z location +0.25 between `frame` and `frame + 42`. Return the list.

`kit/checkout.py` — `build_checkout(loc=(0, 0, 0), heading=0.0, col=None) -> Checkout`. Kiosk-local coordinates
(+Y = the customer side). Everything is parented (plain object parenting) to an empty `checkout_root` at `loc`,
rotation z = `heading` degrees. Parts (sizes x × y × z, positions = box centres):
| part | geometry | material |
|---|---|---|
| `ck_body` | box 0.70 × 0.55 × 0.80 at (0, 0, 0.40) | `#3a3f4a` |
| `ck_stripe` | box 0.72 × 0.01 × 0.10 at (0, 0.28, 0.62) | `#c8102e` |
| `ck_scanner` | box 0.60 × 0.45 × 0.04 at (0, 0, 0.82) | `#10131a` |
| `ck_laser` | box 0.40 × 0.012 × 0.004 at (0, 0, 0.842) | emission `#ff2a2a` strength 3 (`toon2(..., emission=3.0)`) |
| `ck_post` | cylinder r 0.03, from (0, −0.18, 0.84) to (0, −0.18, 1.16) | `#2a2e36` |
| `ck_monitor` | box 0.46 × 0.05 × 0.34 at (0, −0.15, 1.30), rotation x = −15° | `#2a2e36` |
| `ck_bag_base` | box 0.60 × 0.55 × 0.78 at (−0.72, 0, 0.39) | `#3a3f4a` |
| `ck_bag_plate` | box 0.58 × 0.50 × 0.03 at (−0.72, 0, 0.795) | `#c9ced6` |
| `ck_bag_poles` | two cylinders r 0.012 from (−0.95/−0.49, −0.22, 0.81) to z 1.25 + a bar between their tops | `#8a8f99` |
| `ck_bag` | box 0.34 × 0.20 × 0.30 at (−0.72, −0.18, 1.08) | `#eeeeee` |
| `ck_lamp_pole` | cylinder r 0.012 from (0.20, −0.17, 1.47) to (0.20, −0.17, 1.62) | `#2a2e36` |
Screen: four state planes 0.42 × 0.30, parented to `ck_monitor`, placed 0.027 in front of its +Y face (local to the
monitor), each with an emission background (strength 1.2) and a white emission text (`C.text`, `\n` for line breaks,
scaled uniformly so the text block is 0.36 wide or 0.22 tall, whichever is smaller), text 0.002 in front:
| state | background | text |
|---|---|---|
| `scan` | `#1e5bd8` | `PLEASE\nSCAN ITEM` |
| `error` | `#d0202a` | `UNEXPECTED ITEM\nIN BAGGING AREA` |
| `wait` | `#e0a020` | `PLEASE WAIT\nASSISTANT COMING` |
| `thanks` | `#1f9d55` | `THANK YOU FOR\nSHOPPING AT\nGOTHAM MART` |
Status lamp: three spheres r 0.05 at (0.20, −0.17, 1.66): off `#40444c` (toon2), red `#ff2a2a` and green `#2aff6a`
(emission 3).
`screen_state(ck, frame, state)` and `lamp(ck, frame, "off"|"red"|"green")` key visibility with `C.visible` (only
the chosen one visible from that frame). The initial call `screen_state(ck, 1, "scan")`, `lamp(ck, 1, "off")` is
made by `build_checkout`.
Outlines 0.006 on body, stripe, bag base, plate, monitor, bag. No outline on the laser, screens, texts, lamps.
`@dataclass Checkout: root, parts: dict[str, Object], screens: dict[str, list[Object]], lamps: dict[str, Object],
anchors: dict[str, Vector]` with WORLD anchors (after `view_layer.update()`):
`scanner` = top centre of `ck_scanner` (0, 0, 0.84); `bagging` = top centre of the plate (−0.72, 0, 0.81);
`screen` = screen centre; `screen_L` / `screen_R` = the midpoints of the monitor's left/right edges as seen by the
customer (customer faces −Y, so the customer's LEFT is kiosk +X): `screen_L` at kiosk x = +0.23, `screen_R` at
x = −0.23; `customer` = floor point (0, 0.62, 0); `lamp` = lamp centre.

Test `tools/tests/t_props.py`: build the checkout at the origin, a milk on the scanner anchor, a batarang lying on
the bagging plate, one smoke puff at (1.5, 0.5, 0) frame 10; assert every part exists, the anchors match the table
(±0.005), `screen_state(ck, 20, "error")` makes only the error plane + text render-visible at frame 20; render
540x960 stills (`store_night`, `floor`) from (1.2, 2.2, 1.4) → (−0.2, 0, 0.95) lens 40 at frames 1 and 20, plus the
puff at frame 14 → `output/tests/G1/`.

### 12.2 `kit/sets.py` + `look.toon_tex()` (task G2)
1. `kit/look.py` — ADD `toon_tex(mat) -> Material`: converts an imported glTF material IN PLACE. Find its
   `TEX_IMAGE` node image (if none, use the Principled Base Color value as a flat colour). New tree: Image Texture
   (same image, `interpolation = "Closest"`) → colour C; `Diffuse (white) → ShaderToRGB → RGBToBW` = L;
   `lit = L > 0.30` (Math GREATER_THAN), `hi = L > 0.85`; shadow colour = `C × 0.5` mixed 35 % toward `#1b2440`
   (MixRGB/`ShaderNodeMix` RGBA with a constant colour), highlight = `C` mixed 18 % toward `#fff1d6`;
   `col = mix(shadow, C, lit)`, `col = mix(col, highlight, hi)` → Emission (1.0) → output. No rim. Keep glass
   materials (name contains "glass") as `toon2(name, "#9fb4c8", rim=0.0)`. Returns the material.
2. `kit/sets.py`:
   - `PACK = ROOT + "/assets/library/kenney/kenney_mini-market/Models/GLB format"`, `K = 2.4`.
   - `prop(model, *, loc=(0, 0, 0), rot_z=0.0, scale=K, col=None) -> Object` — imports `<model>.glb` with
     `bpy.ops.import_scene.gltf(filepath=...)` (this task may use that operator), parents every imported top-level
     object to a new empty `f"set_{model}_{n}"` at `loc` / `rot_z` degrees / uniform `scale`, converts every new
     material with `look.toon_tex` (once per material), adds an outline 0.006 (world) to every mesh, links to `col`.
   - `gotham_mart(col=None) -> Mart` — layout (world, metres; the checkout itself is NOT built here):
     Facing (measured 2026-09-24): an imported Kenney model faces −Y at rot_z 0 (glTF +Z forward → Blender −Y);
     `freezers-standing` spans y 0…0.5 behind its origin; shelves are double-sided (goods on both sides).
     floor: `floor` tiles covering x −6…6, y −3…9 (5 × 5 tiles of 2.4, tile origin = its corner or centre — measure
     the bbox and place so they cover the range without gaps); back wall: `wall` ×5 along y = −3.0,
     x = −4.8 … 4.8, rot_z 0; along the back wall `freezers-standing` at x = −4.8, −2.4, 2.4, 4.8, y = −2.9,
     rot_z 180 (front faces +Y into the store); left aisle: `shelf-boxes` at x = −3.6, y = 1.2, 3.1, 5.0, rot_z 90;
     right aisle: `shelf-bags` at x = +3.6, same y, rot_z 90; a sign "GOTHAM MART" (C.text, extrude 0.02, emission
     `#ff3344` strength 2) centred at (0, −2.85, 2.15), scaled so it is 2.4 wide, facing +Y (rot (90, 0, 0));
     tube light: box 1.2 × 0.08 × 0.05 at (0, 0.35, 2.6), emission `#e6f4ff` strength 4, plus an AREA light
     (shape RECTANGLE, size 1.2 × 0.12, energy 80, colour `#dff2ff`) at (0, 0.35, 2.55) pointing down.
   - `flicker(mart, frames: list[tuple[int, int]])` — for each `(a, b)`: the tube emission strength and the area
     light energy are keyed ON at `a − 1`, OFF (strength 0.1 / energy 0) at `a`, ON at `b` (CONSTANT interpolation).
   - `@dataclass Mart: root, tube, tube_light, anchors` with `anchors = {"checkout": (0, 0, 0),
     "aisle_entry": (−2.4, 3.2, 0), "aisle_mid": (−2.4, 1.6, 0)}`.
   Test `tools/tests/t_sets.py`: build the mart + `store_night(target=(0, 0, 1))`; assert ≥ 20 imported meshes, every
   imported material has an Emission node and no Principled node, the shelves' heights are 1.9–2.6 m; render
   540x960 from (3.0, 4.2, 1.7) → (−0.3, 0, 1.0) lens 28 and from (0, 5.5, 1.5) → (0, 0, 1.2) lens 24 to
   `output/tests/G2/`.

### 12.3 `kit/shots.py` — auto-framed shots (task G3)
Vertical FOV: cameras use `sensor_fit = "VERTICAL"`, `sensor_height = 36` (`C.camera` does it), aspect 9:16.
1. `region(target, part="full") -> tuple[Vector, Vector]` — world bbox (min, max) of a target at the current frame.
   `target` is a `QChar` (evaluated body bbox, plus its parts), an Object (evaluated bbox incl. children), a Vector
   (a 0.1 m cube around it) or a list of these (union). For a QChar, `part` = `"full"` (whole bbox), `"medium"`
   (z from top − 0.62·h to top), `"close"` (top − 0.38·h to top), `"face"` (top − 0.30·h to top − 0.02·h),
   h = bbox height.
2. `frame(name, target, *, shot, yaw, pitch=0.0, at=None, lens=None, headroom=None, side_offset=0.0) -> Object`
   - `shot` presets (fraction of frame HEIGHT the region fills, default lens, default headroom, QChar part):
     `wide` (0.45, 28, 0.20, full), `full` (0.75, 35, 0.08, full), `medium` (0.80, 40, 0.06, medium),
     `close` (0.62, 50, 0.07, close), `ecu` (0.95, 60, 0.02, face), `insert` (0.60, 50, 0.20, full),
     `two_shot` (0.70, 35, 0.08, medium of each QChar, union).
   - `at` (frame) → `scene.frame_set(at)` first. `yaw`: direction FROM the region centre TO the camera, degrees,
     0 = camera on the +Y side, 90 = on the −X side (counter-clockwise seen from above); `pitch`: camera elevation,
     positive = above looking down.
   - Region height `rh`, `H = rh / fraction`, `d = H / (2·tan(vfov/2))`, `vfov = 2·atan(18/lens)`. Aim point =
     region centre − up·(0.5·H − headroom·H − 0.5·rh) + right·side_offset·H (right = camera right). Camera
     location = aim + d·(cos(pitch)·(−sin(yaw), cos(yaw), 0) + (0, 0, sin(pitch))); `C.point_at`. Also consider the
     region's depth: add half of the region's horizontal extent along the view direction to `d`.
   - Returns the camera (created with `C.camera(name, …, lens=lens)`).
3. `push(cam, start, end, amount=0.12)` — keys the camera location at `start` and moved `amount × distance` toward
   its aim point at `end` (store the aim point on the camera as custom props `aim_x/aim_y/aim_z` in `frame`).
4. `whip(cam, frame, to_target, frames=4)` — keys the camera rotation at `frame` (current) and pointing at
   `to_target` at `frame + frames` (location unchanged); sets `scene.render.use_motion_blur = True`.
5. `check(cam, target, shot) -> dict` — projects the region corners with
   `bpy_extras.object_utils.world_to_camera_view` → returns `{"top": ..., "bottom": ..., "cx": ..., "fill": ...}`
   (normalised 0..1, y up).
Test `tools/tests/t_shots.py`: load BaseCharacter as "a" at (0, 0, 0) and Suit_Male as "b" at (1.0, 0, 0)
(`kit.qchar`); for every shot type (two_shot with [a, b]) at yaw 30, pitch 5: `check()` gives `fill` within ±0.06
of the preset fraction, `top` within ±0.04 of `1 − headroom`, `cx` within 0.06 of 0.5; `push` moves the camera
closer by 12 % ± 1 %; render one 270x480 still per shot to `output/tests/G3/`.

### 12.4 `kit/motion.py` additions — hand reach and props in hand (task G4)
1. `setup_ik(qc) -> dict[str, Object]` — for side in L, R: an empty `f"{qc.name}_ik.{side}"` (world, at the
   current world position of the `Fist.{side}` head) and an `IK` constraint on pose bone `LowerArm.{side}`:
   `target = empty`, `chain_count = 2`, `use_tail = True`, `influence = 0` (keyed 0 at frame 1). Returns the empties.
2. `reach(qc, side, target, start, end, *, blend=5)` — `target` world Vector (the hand goes there). Keys the empty
   location = target at `start − blend` and at `end` (CONSTANT interpolation between separate reaches: set the
   interpolation of the key at `start − blend` to CONSTANT for the previous segment), and the constraint influence:
   0 at `start − blend`, 1 at `start`, 1 at `end`, 0 at `end + blend`. (The constraint fcurves live in the armature's
   active action together with the cape keys — that is fine.)
3. `hold(qc, prop, side, frame) -> Object` — `scene.frame_set(frame)`; `held = prop.copy()` (same data) linked to
   the prop's collections, `held.parent = qc.arm`, `parent_type = "BONE"`, `parent_bone = f"Fist.{side}"`,
   `view_layer.update()`, `held.matrix_world = prop.matrix_world.copy()` (the prop stays where it was at that frame
   and moves with the hand afterwards); visibility: `C.visible(held, 1, False)`, `C.visible(held, frame, True)`,
   `C.visible(prop, frame, False)`. Returns `held`.
4. `release(held, frame, *, place=None) -> Object` — `scene.frame_set(frame)`; `obj = held.copy()`, no parent,
   `obj.matrix_world` = `held.matrix_world` (or a translation to `place` keeping the rotation); visibility swap at
   `frame` (`obj` hidden before). Returns `obj`.
5. `throw(obj, start, end, p0, p1, *, arc=0.25, spin=720.0)` — keys `obj` location along a parabola from `p0` at
   `start` to `p1` at `end` (one key per frame, the apex `arc` metres above the chord) and rotation z from 0 to
   `spin` degrees (LINEAR).
Test `tools/tests/t_reach.py`: `load_character("BaseCharacter.blend", "hero")`, `motion.play(qc, "Idle", 1, 100)`,
`setup_ik`; `reach(qc, "R", Vector((0.35, 0.45, 1.0)), 20, 40)`; at frame 30 the world head of `Fist.R` is within
0.03 m of the target; at frame 1 and 50 the constraint influence is 0; a box prop at (0.35, 0.45, 1.0):
`held = hold(qc, box, "R", 30)`; at frame 45 `held` moved with the hand (its distance to the Fist.R head is the
same as at frame 30 ± 0.01) and `box` is hidden; `release(held, 45)` leaves a visible copy where the hand was;
`throw(box2, 50, 60, …)` passes through the apex. Render frames 1, 30, 45 to `output/tests/G4/`.

### 12.5 Word timings, captions, trimmed lines (task G5)
1. `tools/voice.py`: store per-line word timings in the manifest: `"words": [{"w": text, "start": s, "end": e}]`
   from `align.json` (Kokoro) or `chatterbox.json` (Chatterbox) — both have `scenes[].sceneId` and
   `scenes[].tokens[] {text, start, end}`. Keep the previous `words` for unchanged lines.
2. `tools/audio.py`: a cue line may have `"dur"` (seconds): the clip is cut at `dur` with a 20 ms fade-out.
   Cue `"captions": [{"start_frame", "end_frame", "text", "hi": bool}]` are drawn as ffmpeg drawtext overlays in the
   same filter script as the existing overlays: font `C\:/Windows/Fonts/ariblk.ttf` (Arial Black, as the existing
   overlays), size 72 at 1080 wide (scale with the actual video width), white (`#ffd400` yellow when `hi` is true),
   black border 5 px (scaled), centred horizontally (`x=(w-text_w)/2`), `y=0.70*h-text_h/2`, enabled
   `between(t, start, end)` with start/end = frames / fps. (Pillow is not installed: whole-group highlight only.)
3. `kit/captions.py` (runs inside Blender scripts, standard library only):
   `groups(words, start_frame, fps=24, *, max_words=3, max_chars=16, keywords=()) -> list[dict]` — splits the word
   list into groups (a group ends at max_words, when adding the next word would exceed max_chars, or after a word
   ending in `.`, `?`, `!`, `,`); each group: `start_frame = start + round(first.start·fps)`,
   `end_frame = start + round(last.end·fps) + 3` (but never past the next group's start), `text` = words joined by
   spaces UPPERCASE without trailing commas, `hi` = True if any word's lower-cased, punctuation-stripped form is in `keywords`.
Test `tools/tests/t_captions.py` (system Python via `uv run --project F:/PoCs/video-builder/py python`): the manifest
of `projects/ep02` has `words` for every line; `groups()` on `b_vengeance` gives groups of ≤ 3 words that together
contain all words in order; a synthetic cues file with one line `dur` 1.0 and two captions runs through the
audio.py caption/overlay builder and produces the expected number of drawtext filters (unit-test the function that
builds the filter script; do not render video).

### 12.6 `tools/qa_episode.py` (task G7)
System Python (uv, numpy). `python tools/qa_episode.py --out output/vN` reads `final.mp4`, `mix.wav`, `cues.json`:
- frames: decode with ffmpeg to 90×160 gray raw; motion(f) = mean |frame f − frame f−1| (0–255).
- audio: RMS per video frame (1/24 s) in dBFS from `mix.wav`.
- `hook`: max motion over frames 2–12 > 1.0; audio RMS over the first 0.3 s > −40 dBFS; an overlay or caption
  starts at frame ≤ 3.
- `dead_time`: windows of ≥ 12 consecutive frames with motion < 0.4 AND RMS < −45 dBFS, excluding frames inside
  `cues["beats"]` ranges `[a, b]` → list them.
- `length`: 25–40 s.
Writes `qa.json` `{hook: {...pass}, dead_time: [...], length: ..., pass: bool}` and prints `[qa] ...` lines.
Arguments: `--out output/vN` (input folder) and `--report <path>` (default `<out>/qa.json`).
Test: `--out output/v9 --report output/tests/G7/qa.json` (never write into an existing output/vN during tests).
The check passes when the script exits 0 and the report exists.
