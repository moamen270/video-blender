---
name: blender-kit
description: blender-video kit conventions learned in EP02 (native coords, build order, facing, yaw, NLA vs active action, props, staging)
always: false
---
- Quaternius characters: native space faces −Y, character's left = +X, bald body height 3.147; the armature sits
  under `<name>_root` rotated 180° and scaled height/3.147. Convert native → world only with `kit.qchar.native()`.
- Build order per character: load at the origin in rest pose → build_face → recolour/parts → smooth → outline
  LAST (outline material must be the last slot). Attach rigid parts only at rest pose (`qchar.attach_part`).
- Body animation lives in NLA strips (`kit.motion.play`, `walk_to`); the ACTIVE action holds only IK influence and
  cape keys. Never call `qchar.set_action` in an episode. `cape.bake_cape` is the LAST animation call.
- Several hand targets in a row: use `motion.reach_path`, never back-to-back `reach` (influence keys overwrite).
- Chibi arm reach ≈ 0.55 m from the shoulder: keep targets inside it or the hand stops short.
- Props held in a hand: `motion.hold` / `release` (visibility swap). Hidden objects (`C.visible`) are not
  evaluated — compute anything from their pose before hiding them.
- Shots: `kit.shots.frame` yaw 0 = camera on the world +Y side. A character facing −Y is seen from BEHIND at
  yaw 0; for faces put the camera on the side the character faces. The framer ignores occlusion: keep cameras
  out of props/shelves and check that nothing sits between camera and face.
- Text objects facing +Y need rot (90, 0, 180); (90, 0, 0) reads mirrored.
- Keep every shot ≥ 1 s; no cut right after a whip pan; every SFX must match something visible.
- Kenney props: ×2.4 (floor ×1.2), imported models face −Y at rot_z 0.
