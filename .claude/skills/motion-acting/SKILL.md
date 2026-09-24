---
name: motion-acting
description: Rules for body motion, acting, contacts and interaction in blender-video (plan factor 7) — anticipation/follow-through, gestures on words, IK reach/hold/throw, collisions, walking, secondary motion and the mocap plan. Use when animating characters in projects/<p>/script.py or extending kit/motion.py.
---

# Motion & acting

EP02's biggest loss was stiff bodies: everything was IK reaching on top of Idle, with no acting. Comedy needs the
timing *in the bodies*.

## Acting
- Anticipation → action → follow-through → settle, for every gesture (a small counter-move 3–5 frames before,
  an overshoot, then the settle). Snap only the impact frame; ease the approach and the recovery.
- Key gestures, head accents and expressions on the *words* (manifest word timings), not on line starts.
- Every line has a body idea: point, shrug, lean in, recoil, fold arms, hand to face. The listener reacts too
  (eye direction, brows, a small head turn); nobody stands frozen while someone else talks.
- Faces carry the joke: set the expression before the line, change it on the turn word.

## Contacts & interaction (the EP02 failure classes)
- Hands really reach (chibi arm ≈ 0.55 m); use `motion.reach`/`reach_path`; check the distance at the contact frame.
- Props sit in the hand with a grip offset; the fist never sinks into the prop.
- No character passes through another character or through set pieces: route walks around props; check
  character-to-character distance on every frame of a reach or pass.
- Target → impact → effect, in that order; the target is still there when the hit arrives.
- A miss must miss by a visible margin (the dodge starts BEFORE the arrival); one law of motion per projectile
  (a single gravity parabola, no mid-air equation switch); a touch must be visible (a bounce or a reaction).
- Bodies never teleport in view; move off-screen characters on a cut.

## Locomotion
- `motion.walk_to` (root motion from the planted foot); footsteps SFX from `motion.foot_events`, never timed by hand.
- Fights need footwork: close the distance, plant, recover. Arms-only motion reads as standing still.

## Secondary motion
- Spring-baked capes/coats/hair (`kit.cape`); bake LAST, after all motion.

## Next capability (plan phase 5)
- CMU motion capture (BVH, free incl. commercial) retargeted to the Quaternius rig: gestures, reactions, falls.
  This replaces canned Quaternius actions for acting beats.
- Generic contact QA: grip distance, foot slide, character/character and character/prop intersection per frame.
