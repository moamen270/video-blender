# Production plan — animated Shorts that people watch to the end

Written 2026-09-24 by Claude (senior) after two discussion rounds with Gemini (worker).
Scope: any episode (Shapeshifter, Batman-style alley fight, samurai, anything), made in Blender
by agents. Constraints: free resources only, local GTX 1660 Super (6 GB), Windows, no account
logins, no manual GUI work, every render a new `output/vN`, no synthesized audio.

---

## 1. What "good" means to us — the viewer, measured

A Short wins when people **don't swipe in the first seconds, watch to the end, rewatch, and share**.
We measure that per video (YouTube Studio / TikTok analytics) into `analytics/videos.csv` at 24 h, 72 h and 7 d:

| metric | what it tells us |
|---|---|
| viewed vs swiped away (YouTube) / 3-s retention | did the first frame + hook stop the thumb |
| average % viewed (can exceed 100 % with loops) | did the story hold |
| likes, shares, comments per 1 000 views | did it land |
| followers per 1 000 views | does the series make people want more |

No borrowed "magic thresholds": we set our own baseline from the next 10 videos and judge every
change against it. One variable changes at a time when we test (hook text, CTA vs loop, length).

---

## 2. The order — what moves viewers most

Your nine factors plus four that were missing (hook, pacing, on-screen text, packaging), ranked by
effect on retention and likes. Gemini and I agree on this order after discussion.

| # | factor | why it is here |
|---|---|---|
| 1 | **Concept & hook** (premise, first frame, first 2 s, hook text) | decides whether anyone watches at all; our only data point says viewers left in the first 3 s |
| 2 | **Script & comedic timing** (+ captions/on-screen text) | holds seconds 3–25, delivers the payoff, makes people share; half the audience watches muted |
| 3 | **Characters & gear** | the first frame's stopping power: appeal + instant recognisability at phone size |
| 4 | **Sound effects & deliberate silence** | on a phone, weight and timing are heard more than seen; silence before the big moment is a tool |
| 5 | **Shot design & editing** (angles, framing, cuts, zoom, focus, blur, slow-mo) | pace and clarity; a new image every ~2 s keeps the thumb still |
| 6 | **Voices** | personality in one line; a wrong voice breaks the character instantly |
| 7 | **Motion, interaction, physics** | weight, contacts that land, things that fall and break |
| 8 | **Visual effects** (hits, fire, explosions, smoke, crashes) | punctuation for the big beats; cannot save a weak idea |
| 9 | **Music** | mood bed; must never fight the voice; its cut to silence is part of the drama |
| 10 | **Backgrounds & objects** | tells "where" in one glance; must not compete with the characters |
| × | **Packaging** (cover frame, title = hook, caption, hashtags, pinned comment) | decides the click on every surface that is not the swipe feed |
| × | **Series format & recurring cast** | makes people follow; lets us reuse everything daily |
| × | **Analytics loop** | turns every upload into a lesson |

**Format profiles** — the order shifts with the kind of video:
- **Action short** (Batman alley, duel): motion (7) and SFX (4) move up to #3–#4; VFX matters more.
- **Talk/comedy short** (Shapeshifter): voices (6) move up to #3; faces and expressions become part of #3.

---

## 3. Each factor — from abstract to practical

For each: **Standard** (what the viewer should get) · **Build** (what we make, once, reusable) ·
**Sources** (free, local, no login) · **Auto-check** (an agent verifies it) · **Now** (state today).

### 1. Concept & hook
- **Standard:** frame 1 already shows the conflict or the absurd image — mid-action, never an
  establishing shot or an introduction. A 3–6 word hook text from frame 1. A sound in the first 0.3 s.
  The viewer has a question they need answered.
- **Build:** an **idea bank** (`ideas/bank.md`): premises written as "serious character × trivial
  problem" (our tone), each scored by Claude + Gemini on: readable in 1 s, contrast, payoff strength.
  Every episode gets **3 hook variants**; the first 3 s of each are rendered at preview size (72 frames,
  ~20 s each) and the best is chosen. The episode spec has a `hook` block: first-frame action, hook text, hook sound.
- **Auto-check:** body motion in frames 1–12; an audio event before 0.3 s; hook text visible by frame 3;
  the frame-1 still passes a cover test (main character ≥ 30 % of frame height, contrast vs background).
- **Now:** hook text overlay exists; no idea bank, no variants, no checks. Our data says this is the weakness.

### 2. Script & comedic timing (+ on-screen text)
- **Standard:** one premise; setup → 2–3 escalations → turn → payoff the hook promised → ending that
  either loops into frame 1 or lands a short in-character CTA. Lines short (≈ ≤ 8 words). Every second
  either advances the joke or the action. At most 1–2 **deliberate** held beats (the deadpan pause is
  the joke); zero unintended dead time. Captions: 1–3 words at a time, keyword highlighted, inside the safe area.
- **Build:** a **script template** in the episode spec (beats with roles), a "table read" step
  (Gemini and Claude each critique the script before anything is built), kinetic captions driven by our
  exact word timings (Kokoro timestamps / Chatterbox forced alignment — no Whisper), a `beat:` marker
  for intended pauses.
- **Auto-check:** 25–40 s total; dead-time detector (no motion and no audio for > 0.5 s outside marked
  beats); captions within safe area and never over a face at a punchline.
- **Now:** timings exact; captions are simple overlays; no template, no dead-time check.
- **Test on the channel:** CTA-at-end vs pure loop (same video, two uploads over time).

### 3. Characters & gear
- **Standard:** readable in silhouette at thumbnail size; appealing stylised proportions; the gear that
  defines the character reads instantly (cowl ears + cape, curved katana, mask); expressive faces;
  identical every episode.
- **Build:** a **character kit**: one deforming base body with one rig for everyone + a **gear/costume
  parts library** + **2D decal faces** (eye/brow/mouth textures swapped by cue — cheap, anime-like,
  agent-friendly; mouth decals can be driven by lip sync later) + look-dev materials (toon with rim light,
  warm/cool shadows, outline, bevelled edges). Each recurring character has a **character sheet**
  (`characters/<name>.json`: parts, colours, face set, voice, personality, do/don't).
- **Sources:** Quaternius "Ultimate Animated Character" / "Universal Base Characters" (CC0, public Google
  Drive), Kenney characters (CC0), Blender's bundled Rigify; gear from Quaternius weapon/prop packs (CC0) or built in code.
- **Auto-check:** turnaround sheet rendered for every new/changed character (front, ¾, side, close-up)
  and reviewed; silhouette render (black on white) still recognisable at 25 % size; character/background contrast.
- **Now:** primitives rigidly glued to bones — the biggest visual gap.

### 4. Sound effects & deliberate silence
- **Standard:** every hit, step, swing, fall and object has a real recorded sound on the exact frame; variety
  (no identical repeats); silence before and after the key moment; impacts have body on phone speakers.
- **Build:** the **SFX bank** (done: `assets/sfx_bank.json`, real CC0 only, round-robin, loudness
  normalised) + **automatic SFX from events**: contacts → clash/impact by material, foot plants → steps
  by surface, fast limbs → whoosh, landings/falls → thud, cloth on big moves; layered hits (transient +
  low-end from real recordings); `silence:` markers.
- **Sources:** Kenney Impact/RPG (CC0), OpenGameArt CC0 packs; bigger CC0 packs on demand.
- **Auto-check:** every contact/fall event has a sound within ±1 frame; bank-only (synthesis disabled in
  code); no SFX louder than the voice while a word is spoken.
- **Now:** bank done; events wired per project, not yet generic.

### 5. Shot design & editing
- **Standard:** vertical composition — subject large, eyes on the upper third, no dead floor; wide for
  geography, close for reaction; cut on action; a new image every ~2 s; camera shake on impacts; depth of
  field to isolate the subject; slow-motion or a speed ramp on the one big moment; whip pans for energy.
- **Build:** a **shot library**: named shots (`wide`, `two_shot`, `ots`, `close`, `extreme_close`,
  `low_hero`, `insert`) **auto-framed from the characters' bounding boxes** (no hand-typed camera
  coordinates — that cost the samurai video four review rounds), named moves (push, pull, orbit, whip pan,
  handheld, rack focus, shake), editing rules (auto-cut at contact frames, max shot length), slow-mo by retiming the key range.
- **Auto-check:** per shot, subject covers the planned share of the frame and stays out of platform UI
  zones; no static shot > 3 s; cuts land within ±2 frames of their events.
- **Now:** cameras placed by hand per video.

### 6. Voices
- **Standard:** each character has a distinct voice that fits the personality (pitch, pace, timbre,
  attitude); controlled acting, not monotone; the same voice every episode.
- **Build:** a **voice casting sheet** per character (engine, reference clip, emotion range, speed, FX);
  Chatterbox with ASR read-back and retakes (exists in video-builder).
- **Voice policy (owner decision 2026-09-24):** cloning is allowed when a character needs it. For a parody
  of a movie/game character we may clone a reference that fits the character (the original performance or
  a different voice with the right personality), always **modified** so it is not the exact voice (pitch,
  timbre, FX), and always in an obviously comedic cartoon context — making fun of the character, never
  presenting the actor as saying or endorsing anything. Original cast members get custom voices built the
  same way (pick a reference that matches the personality, clone, modify).
- **Upload hygiene for cloned voices:** the description frames it as parody / voice impression; turn on the
  platform's AI/altered-content label where it applies; keep the voice swappable per character so a
  complaint costs one re-voice, not a remake.
- **Auto-check:** ASR read-back equals the text; measured pitch inside the character's range; loudness.
- **Now:** Chatterbox is the default engine (owner approved 2026-09-24, D13 closed); Kokoro only for generic voices (machines, narrators) when the casting sheet says so.

### 7. Motion, interaction, physics
- **Standard:** anticipation → action → follow-through; contacts that really land; planted feet; loose
  parts that swing; objects that fall, bounce and break believably.
- **Build:** an **action library** of named, parameterised moves (`walk_to`, `run`, `jump`, `punch`,
  `kick`, `slash`, `throw`, `catch`, `fall`, `get_up`, `sit`, `point`, `shrug`, `react_hit`…) — body motion
  from CMU motion capture where possible (BVH, free incl. commercial), contacts solved by the generalised
  `sword_through` idea ("this effector reaches that target on that frame"), spring **secondary motion**
  (capes, hair, sashes), baked **rigid-body physics** for props and debris (deterministic).
- **Auto-check:** the samurai QA generalised: contact distance, grip, foot slide, pass-through, dead time.
- **Now:** IK rig, pose library, contact solver, auto steps, QA — samurai-specific, to be generalised.

### 8. Visual effects
- **Standard:** stylised to match the toon look, short and punchy; big moments layered (flash + shockwave
  + debris + smoke + shake + sound on the same frame).
- **Build:** an **FX library** built from stylised geometry and animated shaders, not heavy simulation:
  spark, smear, impact star, shockwave ring, speed lines, dust, smoke puff, debris (rigid bodies), fire
  (noise-shader toon flames), explosion (layered preset), glass/screen crack, magic/transform.
  Optional billboard sprites from Kenney's CC0 particle pack.
- **Auto-check:** each FX tied to an event; lifetime limits; never covers a face on a punchline.
- **Now:** spark, smear, dust, shake, helmet split.

### 9. Music
- **Standard:** fits the mood; always under the voice; drops to silence on the big moment; cuts and hits
  can sit on the beat.
- **Build:** a **music library** with tags (mood, tempo, energy, licence, credit line); excerpt chosen by
  energy analysis (as done for "Asian Drums"); beat detection to snap cuts/hits within ±2 frames; ducking
  (done); the credit line written automatically into the upload text.
- **Sources:** Kevin MacLeod / incompetech (CC BY 4.0, credit required), other CC0 music to be verified.
- **Auto-check:** music ≥ 10 dB under the voice while speaking; muted where the spec says silence; credit present in `social.md`.

### 10. Backgrounds & objects
- **Standard:** "where are we" in one glance; lower contrast and saturation than the characters;
  foreground/mid/background depth; props the story actually uses.
- **Build:** a **set library** (alley, office, stage/audition room, street, dojo, forest…) assembled from
  CC0 kits + a look preset per set (lighting, fog/mist, colour grade).
- **Sources:** Quaternius kits (modular streets, medieval village, cyberpunk, restaurant…), Kenney kits,
  Poly Haven (textures, skies) — all CC0.
- **Auto-check:** character vs background contrast; background detail density below the character's.

### Cross-cutting
- **Packaging:** frame 1 doubles as the cover; title = hook; description with credits; pinned-comment
  question; hashtags — generated per render into `output/vN/social.md` (port from video-builder).
- **Series & cast:** recurring characters in fixed formats (e.g. *serious warrior vs trivial chore*;
  *villains at a mundane job*; *a tense standoff interrupted by petty etiquette*; the *Shapeshifter
  audition*). Same cast, sets and voices → faster episodes and followers who come back.
- **Famous characters (policy):** we make comedy parodies of movie and game characters; the views upside is
  real, and so are manual IP claims and monetisation limits, so the comedy/parody framing is kept clear in
  every video and description. Voices follow the voice policy in §3.6. Grow our own recurring cast alongside.
- **Variation (anti "template fatigue"):** the risk of reusable blocks is that every episode looks the
  same. Every block takes variation parameters (timing offsets, lens choice, move variants, colour grade),
  and each series rotates sets and shot patterns.

---

## 4. How an episode gets made (agent workflow, daily)

1. **Idea** — pick a premise from the idea bank; write 3 hooks. *(Claude + Gemini, 5 min)*
2. **Script** — fill the template; table read by both models; fix. *(10 min)*
3. **Episode spec** — beats → shots → actions → lines → sounds, in one file that compiles to Blender:
   ```yaml
   episode: alley-stakeout
   series: vigilante-chores
   cast: [bat_vigilante, clown_villain]
   set: alley_night
   hook: {text: "He trained 10 years for this.", first_action: bat_vigilante.land_from_roof, sound: impact_heavy}
   beats:
     - shot: low_hero(bat_vigilante)
       say: {bat_vigilante: "Nobody leaves this alley."}
     - shot: two_shot
       act: [clown_villain.throw(pie, at: bat_vigilante.face), bat_vigilante.dodge(side)]
     - beat: 0.6            # deliberate deadpan pause
     - shot: close(bat_vigilante)
       face: {bat_vigilante: unimpressed}
   ending: {cta: in_character, loop_to_frame_1: true}
   ```
4. **Preview** — hook variants + full preview at half size; QA runs automatically. *(≈ 5 min render)*
5. **Review** — QA report + Gemini watch/listen + Claude contact sheets; fixes as a new version.
6. **Final** — full render + mix + overlays + `social.md`. *(≈ 10 min render)*
7. **Owner** — watch, approve or note (≈ 10 min). Upload.
8. **Measure** — fill analytics at 24 h / 72 h / 7 d; weekly lesson review → rules in the skills.

Target once the blocks exist: **≤ 1 hour of agent time and ≤ 10 minutes of yours per episode.**

---

## 5. Roadmap — impact first, each phase proven by a real episode

| phase | builds | proven by |
|---|---|---|
| **1. Hook & script machine** (days) | idea bank, script template + table read, 3-hook preview, kinetic captions, dead-time + hook checks, `social.md` + credits, analytics sheet | one episode made with the current kit, uploaded, measured |
| **2. Character kit + look-dev** (≈ 1–2 weeks) | base deforming body + rig, gear library, 2D decal faces, character sheets, toon look-dev (rim, warm/cool shadows, bevels), turnaround QA | two recurring characters that pass the turnaround + silhouette review |
| **3. Sound & voice** (days) | generic event-driven SFX, silence markers, music library + beat snap, voice casting sheets, Chatterbox decision | an episode where no sound is placed by hand |
| **4. Shot library & editing** (≈ 1 week) | auto-framed named shots and moves, cut-on-action, slow-mo, framing QA | an episode with zero hand-typed camera coordinates |
| **5. Action library & physics** (≈ 2 weeks) | CMU mocap retarget, generalised contact solver, secondary motion, rigid-body props/debris | an action episode built only from named moves |
| **6. FX & sets** (≈ 1–2 weeks) | FX library (incl. fire/explosion/smoke/debris presets), set library from CC0 kits | a Batman-style alley episode with an explosion |
| **7. Episode compiler & daily cadence** | the spec above compiles end to end, variation parameters, scheduled drafting | 7 episodes in 7 days |

The compiler grows from phase 1 on: each phase adds its block to the spec, so we never build blocks
nothing uses. Phases 1 and 3 are cheap and hit the top of the ranking; phase 2 is the biggest visual jump.

---

## 6. Rules that never change
- Free, local, no logins; every asset has a licence entry (`assets/library/LICENSES.md`).
- No synthesized audio. Cloned voices only per the voice policy (§3.6): modified, parody context, labelled.
  Credits go into every upload that needs them.
- Every render is a new `output/vN`; nothing is overwritten.
- A contact, a camera framing or a sound is only "done" when an automatic check has verified it.
- Gemini writes the code from literal specs; Claude plans, runs, reviews; the owner approves.

## 7. Decisions for the owner
1. Next episode after the plan: which premise/series to use as the phase-1 proof?
2. Famous characters vs parody archetypes vs an original cast — which mix?
3. CTA at the end vs pure loop — agree to A/B test?
4. Cadence while building: keep 2 uploads/week until phase 4, then daily?
