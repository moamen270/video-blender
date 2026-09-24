---
name: voice-casting
description: Cast and generate character voices for blender-video (parody clones per the owner's voice policy): find and get approval for reference clips, pick clean segments with Gemini, modify, clone with Chatterbox, choose takes, direct per sentence. Use when adding a character voice or re-voicing lines.
---

# Voice casting

Policy (owner, 2026-09-24): parody characters may clone a reference of the original performance, always
**modified** (pitch/formant), comedy framing, AI-label on upload. One casting-sheet entry per character.

## New character voice
1. **Find a clean source** (single speaker, no music/SFX/PA echo): game dialogue collections are best.
   Sites behind bot checks are off-limits (never bypass). Before downloading: ask the owner with filename,
   source URL, size; download only under `F:/PoCs`; partial downloads (`curl -r 0-5999999`) are enough.
   Record provenance in `assets/library/LICENSES.md`; references stay out of git (`assets/library/voices_ref/`).
2. **Segments:** split by silence (`silencedetect=noise=-40dB:d=0.35`), let Gemini Pro (`media`, skill
   `media-review`) pick 6–8 clean in-character lines; join to 10–14 s, mono 24 kHz, loudnorm −20 LUFS.
3. **Modify:** `rubberband=pitch=0.93:formant=shifted` (deeper) / `pitch=1.04:formant=shifted` (lighter);
   keep the unmodified `*_ref_orig.wav` for comparison.
4. **Casting sheet** `assets/cast/voices.json`: engine, voiceRef, emotion (≤ 0.5 for deep voices), speed, seed,
   notes. Generic voices (machines, narrators): Kokoro (e.g. `bf_emma`, speed 1.12 for a crisp machine).
5. **Takes:** generate 2–3 seeds; keep ASR read-back ≥ 0.97 (Chatterbox prints "heard ..."); let Gemini pick the
   cleanest and confirm "different from the actor but evocative". Rewrite text that slurs ("nothing, in the
   bagging area"; ellipsis for pauses).

## Directing lines
- Split a line where the delivery changes ("I am vengeance. I am the night." → dramatic, higher emotion;
  "I am paying in exact change." → flat) and give each part its own emotion/speed; key matching expressions.
- `[laugh]`/`[cough]` tags need at least one spoken word in the line.
- `tools/voice.py` re-synthesises only lines whose settings changed; `tools/audio.py` normalises every line to
  −16 dB RMS.
