---
name: sound-design
description: Rules for sound effects, silence, music and the final mix in blender-video (plan factors 4 and 9) — real CC0 recordings only, event-timed SFX, visible sources, music under voices, loudness, licences and credits. Use when adding sfx/music/beats to cues.json, extending assets/sfx_bank.json, or reviewing a mix.
---

# Sound design & music

## Hard rules (owner)
- **No synthesized audio**, ever: every SFX is a real recording from `assets/sfx_bank.json` (CC0 packs:
  Kenney impact/rpg/interface/sci-fi, OpenGameArt). Music: Kevin MacLeod (CC BY 4.0, credit required).
- No white-noise textures ("100 % noise, trash"); sustained noisy SFX under dialogue sound like a broken radio.
  Use short hits.
- New packs: download under `F:/PoCs`, licence line in `assets/library/LICENSES.md` before use.

## Placement
- Every hit, step, swing, fall, prop and effect has a sound on its exact frame (±1). Derive the frames from events
  (contacts, `motion.foot_events`, the prop release frame), never by guessing.
- The sound's source is visible on that frame, and matches it (a batarang = an air whoosh, not a blade swish).
- Variety: round-robin bank files; no identical repeat within a few seconds.
- Silence is a tool: a beat of silence before the big moment, music cut on the punchline; footsteps never under
  the punchline.
- Picking sounds: Gemini Pro listening (`media` + skill `media-review`) labels candidates well; its quality scores
  are uniform, so verify the choice with measurements.

## Mix
- Voices normalised per line (`VOICE_RMS_DB`), music ≥ 10 dB under speech with ducking; no SFX louder than a
  word being spoken.
- Final: loudnorm to −14 LUFS integrated / −1 dBTP (both mux branches of `tools/audio.py`; the no-overlay branch
  skipped it until 2026-09-24). Measure: `ffmpeg -af ebur128` on final.mp4 (expect about −14 to −17).
- Measure every cue: RMS 0.15 s after vs before in `mix.wav` should rise.

## Music
- Pick by mood and energy; choose the excerpt by energy analysis; a cut to silence is part of the drama.
- The credit line goes into the upload text (skill `publish-release`).
