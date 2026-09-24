---
name: episode-review
description: Review checklist for every rendered version in blender-video before showing it to the owner — 4 Hz sheet, dense strips around cuts/contacts/SFX, measured audio, the known failure classes, and how to log owner notes. Use after every make.sh render.
---

# Reviewing a render (blender-video)

The owner watches on a phone in one pass; anything that reads as a glitch is a bug.

## 1. Automatic
- `tools/qa_episode.py --out output/vN` must PASS (hook motion + sound + text by frame 3, no dead time, length).
- `output/vN/sheet_4hz.png` exists (owner rule) — open it first: story readable muted? rows of identical tiles =
  dead time; cut rhythm; captions never over a face at a punchline.

## 2. Dense strips (ffmpeg select+tile) around every
- **cut** (±6 frames): is the new shot readable ≥ 1 s? no whip+cut, no pop-in of characters.
- **contact / hand action**: fist in the prop? hand reaching the target? arm through another character?
- **SFX cue**: the sound's source is visible on that frame.
- **POV / close shots**: clip plane slicing hands, decals (eyes/brows) outside the head silhouette.
- **Screens/text**: centred inside their panel, readable.

## 3. Audio — measure, don't guess
- Per cue: RMS 0.15 s after vs before in `mix.wav` (should rise); voices at matched loudness; music ≥ 10 dB under
  voices; beats really silent. Cut-off lines end at a word boundary (use the manifest word timings).
- Gemini (Pro, `media` + skill `media-review`) is good for hearing (slurred words, clean takes);
  do not trust it for lip sync or anything under ~1 s.

## 4. Showing the owner
Send `final.mp4` **and** `sheet_4hz.png`. Log every owner note in the episode log (score, note, cause, fix) and
turn repeated notes into a rule (memory / this skill / worker skill `blender-kit`).

## EP02 failure classes (check them every time)
back-facing shots · camera inside props · occluding props · whip+cut too fast · teleport in view · sound with no
visible source · invisible prop · fist inside prop · character through character/counter · clip plane slicing
hands · decals off the silhouette · off-centre screen text · unclear payoff (e.g. unexplained theft).
