---
name: character-build
description: Rules for building or changing a 3D character in blender-video (plan factor 3) — parody recognisability, gear, faces/expressions, casting-sheet entry, turnaround + silhouette checks and the owner approval gate. Use before and while writing kit/cast.py builders, recolouring/adding parts to Quaternius rigs, or changing faces.
---

# Character build (3D)

Direction (owner, 2026-09-24): 3D. The 2D cut-out trial (release v0.2.0) was rejected as "very poor", so don't
propose it again as the main style. EP02 scores: building Batman/Joker 7/10, the character style 4/10 ("could use enhancements").

## Standard
- Recognisable at phone size in one glance: silhouette first (hair, ears, cape, coat), then 2–3 signature colours.
  Parody villains: Joker = white face, slicked green hair, dark eye sockets, red grin; Penguin = top hat + monocle.
- The gear that defines the character must read: a cowl with ears plus a cape; a kabuto as a bowl + neck guard + crest;
  a katana is a *curved* blade with a guard and wrapped grip (a straight line in a hand is a stick).
  Costume videos live or die on the gear.
- Same look every episode: one builder per character in `kit/cast.py`, colours and parts as data.
- Smaller casts read better in action; set relative scale deliberately (hero > villain > sidekick).

## Faces
- Decal eyes/brows sit on the head surface: at 3/4 angles they must stay inside the head silhouette
  (EP02 flaw). Project or offset them along the surface normal; check at yaw 0/35/60 in the turnaround.
- Expression set per character (neutral, stern/angry, worried, smug, surprised, deadpan), brows + eye scale + mouth set.
  Blinks automatic; eye direction keyed to whoever the character looks at.
- Mouth shapes = the 9 Rhubarb shapes; readable at MCU size.

## Gate & checks (before any animation)
1. `tools/turnaround.py` sheet: front, 3/4, side, back, close-up. Look for floating decals, gaps between parts,
   parts through the body, and outline artefacts.
2. Silhouette render (black on white) at 25 % size: still recognisable?
3. Contrast against the set it will stand in.
4. Show the owner the turnaround and get approval. Only then write motion.
5. Casting entry in `assets/cast/voices.json` (skill `voice-casting`); notes on personality and do/don't.

## Build rules
- Quaternius rig + `kit.qchar` (recolour, parts, native()); parts parented to bones must not intersect in the
  full motion range. Check at the extreme poses the episode uses, not only at rest.
- Props attach to the hand with a grip offset and a grip pose (the fist must wrap the handle, never sink into the prop).
- Toon look via `kit.look.toon2` (rim, warm/cool shadow); outlines must not shadow their own object.
