---
name: shot-design
description: Rules for cameras, framing and editing in blender-video (plan factor 5) — vertical composition, auto-framed named shots, visibility of faces, cut rhythm, camera moves and the POV/near-clip trap. Use when placing or animating cameras, choosing cuts, or reviewing framing in a render.
---

# Shot design & editing

Most of EP02's 8 review rounds were staging. Size and centring are automatic (`kit.shots`), but *visibility* is not.

## Composition (1080x1920)
- Subject large, eyes on the upper third, no dead floor or empty wall above the heads.
- Wide for geography, close for reaction; the camera is on whoever owns the beat.
- Characters face the camera enough to read their faces: put the camera on the side the character faces. Two
  characters facing each other → cheat the one who must read toward camera, or use over-the-shoulder shots.
- Nothing between the camera and a face (racks, monitors, shelves); the camera is never inside a prop.
- Wide or zoomed-out cameras must stay inside the set: no edge of the backdrop or void may show (check the widest frame).

## Named shots (no hand-typed coordinates)
`kit.shots.frame(target, shot)` with shot = wide / two_shot / ots / close / extreme_close / low_hero / insert;
moves: `push`, `whip`; `shots.check(cam, target, shot)` for coverage. Add new moves to the kit, not to a script.

## Editing
- A new image every ~2 s; no static shot > 3 s; hold every shot ≥ 1 s.
- Cut on action and within ±2 frames of the event; never cut right after a whip pan.
- An insert shot on the payoff object/impact if it is small.
- Captions stay fixed to the frame under any camera move.

## Traps
- Machine/object POV with `clip_start` past the object: the clip plane slices hands that come close. Keep hands
  out of the clip zone or cut away.
- Framing computed on the rest pose misses raised arms and props: frame on the region the action uses.

## Check every render
Dense strip (±6 frames) at every cut: readable new shot, no pop-in, the face visible and in the upper third.
