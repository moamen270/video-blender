---
name: voice-casting
description: "Cast and generate character voices for blender-video (parody clones per the owner's voice policy): find and get approval for reference clips, pick clean segments with Gemini, modify, clone with Chatterbox, choose takes, direct per sentence. Use when adding a character voice or re-voicing lines."
---

# Voice casting

Policy (owner, 2026-09-24): parody characters may clone a reference of the original performance, always
**modified** (pitch/formant), comedy framing, AI-label on upload. One casting-sheet entry per character.

**Engine: Chatterbox is the default** (owner approved 2026-09-24; `DEFAULT_ENGINE` in `tools/voice.py` and
`tools/audio.py`). Kokoro only for generic voices (machines, narrators) with `engine: "kokoro"` in the casting entry.

**Voices are part of the deliverable.** Every speaking character gets a real cast voice before a render is shown or
published. Never present a video with placeholder TTS as progress (the Rick and Morty test shipped with Kokoro
placeholders and the owner called it out). If casting is blocked (waiting for reference approval), say so
first, and render only as a clearly marked motion test.

## New character voice
1. **Find a clean source** (single speaker, no music/SFX/PA echo): game dialogue collections are best.
   Sites behind bot checks are off-limits (never bypass). Before downloading: ask the owner with filename,
   source URL, size; download only under `F:/PoCs`; partial downloads (`curl -r 0-5999999`) are enough.
   Record provenance in `assets/library/LICENSES.md`; references stay out of git (`assets/library/voices_ref/`).
2. **Segments:** split by silence (`silencedetect=noise=-40dB:d=0.35`), let Gemini Pro (`media`, skill
   `media-review`) pick 6–8 clean in-character lines; join to 10–14 s, mono 24 kHz, loudnorm −20 LUFS.
   **Game voice packs (The Sounds Resource):** first run `tools/clip_scan.py <folder> <name>` (wav2vec2 ASR →
   `clips_<name>.csv`: talking vs sound). Dash-named files (`LUK0028-4.wav`) are grunts/jumps/laughs — never
   use them (a Vader shout ref built from the loudest clips picked 3 grunts, 2026-09-26). Pick calm lines for
   `<char>_ref` and the loudest/emotional lines for `<char>_shout_ref`, then `tools/make_ref.py` (joins,
   loudnorm, modifies, keeps `_orig`). Listening check with Gemini when available.
3. **Modify:** `rubberband=pitch=0.93:formant=shifted` (deeper) / `pitch=1.04:formant=shifted` (lighter);
   keep the unmodified `*_ref_orig.wav` for comparison.
4. **Casting sheet** `assets/cast/voices.json`: engine (chatterbox by default), voiceRef, emotion (≤ 0.5 for deep
   voices), speed, seed, notes. Generic voices (machines, narrators): Kokoro (e.g. `bf_emma`, speed 1.12 for a crisp machine).
5. **Takes:** generate 2–3 seeds; keep ASR read-back ≥ 0.97 (Chatterbox prints "heard ..."); let Gemini pick the
   cleanest and confirm "different from the actor but evocative". Rewrite text that slurs ("nothing, in the
   bagging area"; ellipsis for pauses).

## Directing lines (every line, not only the big ones)
- Each line in `lines.json` carries its direction: `emotion` (Chatterbox exaggeration, 0.3 flat → 0.9 manic),
  `speed`, and pauses (ellipsis / `pauseAfter`). Write the intent next to it in the episode log.
- Split a line where the delivery changes ("I am vengeance. I am the night." → dramatic, higher emotion;
  "I am paying in exact change." → flat) and give each part its own emotion/speed; key matching expressions.
- `[laugh]`/`[cough]` tags need at least one spoken word in the line.
- `tools/voice.py` re-synthesises only lines whose settings changed; `tools/audio.py` normalises every line to
  −16 dB RMS.

## Shouts and made-up words (learned on sf01, Ryu/Ken, 2026-09-25)
- Chatterbox copies the reference's ENERGY: a calm dialogue reference gives flat "shouts". Build a second
  `<char>_shout_ref.wav` from the loudest combat/effort clips (same modification) and set `voiceRef` per shout line.
- Very short or invented words at high emotion hallucinate ("Hadouken!" -> "hart wokin"). What worked:
  respell ("Hadoken!"), double punctuation ("Hadouken!!"), or a carrier phrase ("Take this. Hadouken!") cut by word timing.
- Held vowels: write them ("Hadouuuuuuken!") with the shout reference; generate 4-5 seeds and pick by ear.
  Do NOT time-stretch speech (rubberband) - it sounds robotic. Splicing two takes is audible; reuse a clean take
  with a small pitch/gain change instead.
- ASR read-back scores are meaningless for held vowels and move names; Gemini listening scores drift between runs
  on identical audio - use Gemini to shortlist, the owner's ear to decide.
- A take much shorter than its text crashes the aligner ("targets length is too long for CTC") and kills the whole
  batch: drop that spelling.
- Voices must be clearly distinct: pitch the two references apart (Ryu 0.90, Ken 1.10) and check with a listener.
- Build a script-order preview with `tools/voice_preview.py` (shared shouts end-aligned) and send it to the owner.
