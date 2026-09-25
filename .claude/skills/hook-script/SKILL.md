---
name: hook-script
description: Rules for the hook, script structure, comedic timing, on-screen text and captions of a blender-video episode (plan factors 1–2). Use when writing or revising projects/<p>/lines.json, the beat timeline in script.py, hook text, captions or the ending/CTA — after the premise has passed the comedy-pitch gate.
---

# Hook & script

The premise itself is approved by the owner first (skill `comedy-pitch`). Model table-read scores are not a
signal (a Gemini read scored EP02 9/10, the owner 0/10). Only the owner judges the joke.

## Hook (first 3 s decide everything; our only analytics say viewers left in the first 3 s)
- Frame 1 is already mid-action or the absurd image: never an establishing shot, an introduction or a walk-in.
- Hook text (3–6 words) readable by frame 3, and it is the same sentence as the cover/title.
- A sound in the first 0.3 s. The character is alone and big in frame (≥ 30 % of frame height).
- Make 3 hook variants and render the first 72 frames of each at preview size; pick one with the owner.
- Auto-check: `tools/qa_episode.py` (motion in frames 2–12, audio > −40 dBFS, hook text).

## Structure
setup → 2–3 escalations → turn → payoff (a NEW surprise, not a repeat of the setup) → ending that loops to
frame 1 or lands exactly one CTA.
A loop is made of the action itself: the last beat sets up the first (same pose, camera, expression and props as
frame 1), with no transition effect. A white/black flash as the bridge was rejected by the owner (sf01). The CTA is spoken and in character. Nothing is drawn over the character in the CTA frame.
- 25–40 s. Every second advances the joke or the action. Lines ≤ ~8 words.
- At most 1–2 deliberate held beats (`beats` in cues.json, the deadpan pause); zero unintended dead time.
- The joke lives in the characters' choices, not in a repeated sound or line.
- The payoff must be unambiguous on a muted phone: if a viewer could ask "what just happened?", add an insert shot.

## Performance in the script
- Split a line wherever the delivery changes and direct each part (emotion, speed, pause), e.g.
  "I am vengeance. I am the night." (dramatic build) / "I am paying in exact change." (flat deadpan).
- Emotions ramp across beats (worried → fierce → angry); maximum intensity on the first beat leaves nowhere to go.
- Opening line slower than the body (speed ~0.8–0.9): it is a performance, not narration.
- A speech bubble is silent: if a line should be heard, it is a voiced line with the right speaker.

## Captions / on-screen text
- Built from exact word timings (`kit.captions.groups`, manifest `words`): 1–3 words at a time, keyword highlighted.
- Inside the safe area (not the bottom ~20 % / right-edge platform UI), never over a face on a punchline.
- Screen text (in-world displays) is centred inside its panel with margins; check it in a dense strip.
