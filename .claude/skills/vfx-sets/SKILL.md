---
name: vfx-sets
description: Rules for visual effects and sets/backgrounds in blender-video (plan factors 8 and 10) — stylised event-tied FX, layered big moments, CC0 set kits, contrast with the characters, and set coverage for every camera. Use when adding FX (kit/fx.py, props like smoke/batarang/portal) or building/dressing a set (kit/sets.py).
---

# VFX & sets

## VFX
- Stylised to match the toon look, short and punchy; made from geometry and animated shaders, not heavy simulation.
- Each FX is tied to an event (contact, release, landing) and lives only as long as it reads.
- Big moments are layered on one frame: flash + shape (shockwave or smear) + debris/smoke + camera shake + sound.
- Never over a face on a punchline; it must stay readable (EP02: the smoke-bomb ending had to be made readable).
- The source's canonical look wins: when a character's effect is famous, match its screenshot (Jhin's W = a thin
  white line with a blue-violet halo; a portal = a green swirl with a bright rim).
- EEVEE volume mist renders as noise: grade atmosphere in post (`grade` in cues.json).
- Library today: spark, smear, dust, shake, helmet split, smoke puff, batarang. Next (plan phase 6): impact star,
  shockwave ring, speed lines, debris (rigid bodies, baked), toon fire, explosion preset, glass/screen crack.

## Sets
- "Where are we" in one glance; lower contrast and saturation than the characters; foreground/mid/background depth.
- Built from CC0 kits (Kenney, Quaternius, Poly Haven), each with a look preset (lights, grade).
- Props the story uses are bigger and clearer than the dressing; nothing the camera must see through sits between
  camera and faces (skill `shot-design`).
- Coverage: the set extends past the widest camera in every direction (no void or grey edges).
- Night grades via ffmpeg (EP02); keep faces lit (rim/key) even in dark sets.
