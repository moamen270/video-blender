# EP02 "Unexpected Item" — build log (senior)

Plan: `docs/EP02_PLAN.md`. Worker: Gemini 3.8 Flash (high) via agy v2 with `check_command` loops.

## Checkpoint 1 — characters + look (2026-09-24)

| task | worker | result | senior findings / fixes |
|---|---|---|---|
| prep | — | — | Probed the Quaternius pack: 23-bone rig, 17 actions, faces −Y, no UVs, flat face front, eye/brow islands separate from the head. Chose the pack's "dummy" look (black body, white eyes) as the house style. |
| E2 look | 1 job, 221 s, check passed round 1 | toon2 (warm/cool ramp + rim), store_night rig | **Senior spec bug:** key light too high/weak (measured L 0.39 at centre) → key 35°, energy 3.2. Rim turned the floor blue (grazing plane) → rim off for sets/props. **Old kit bug found:** the inverted-hull outline cast a shadow over its own object, so every outlined object (incl. the samurai video) rendered in its shadow tone → `use_backface_culling_shadow` on the outline material (1 line). |
| E1 qchar | 2 jobs, 412 + 495 s | loader, recolour, part transplant, surface ray-casts | Worker correctly BLOCKED on my height spec (3.269 measured with hair; bald body 3.147). The chest-centre quad is dominated by `Shoulder.L` → chest filter widened. Transplanted belt sits flush with the bare body → inflate step added for E4. |
| E3 face | 1 job, 271 s, check passed round 1 | eyes/brows extracted from the mesh as rigid parts on `Head`, 10 plain + 9 grin mouth shapes, 7 expressions, blink | Brow sign rule held (test-verified). **Senior fixes:** mouth outlines rendered with holes (concave, non-planar n-gons with coincident tips) → fan / quad-strip triangulation; widest grins dipped below the flat face → thinner. |
| E4 cast | 1 job, 219 s, check passed round 1 | Batman (base body, cowl/gloves/boots by bone region, inflated belt, ears, scalloped cape, emblem), Joker (Suit_Male recolour, grin, ASSISTANT tag), turnaround tool | Look-dev decision from a senior A/B test: subdivision level 1 + smooth shading (flat low-poly facets looked like a game asset). **Senior fixes:** silhouette render hid the legs (floor), face camera too close, beige highlight blob on black heads → brightness-scaled highlight, tag 30 % larger. |

**Checkpoint 1 totals:** ~1 h 10 min wall time (senior probing + spec ≈ 35 min, 5 worker jobs ≈ 27 min of worker time,
all checks automated). Worker bugs: 0 blocking (1 correct BLOCKED on my spec). Senior spec bugs: 5 (height, chest
filter, key light, rim on flat surfaces, mouth triangulation) + 1 old kit bug found (outline hull self-shadow).
Lesson: measure in Blender before writing numbers into a spec (every spec bug was an unmeasured assumption).

Owner review stills: `output/ep02/cp1/` (lineup, turnarounds, expressions, silhouettes, look-dev spheres).

## Checkpoint 2 — spring cape, motion, voice + lip sync, screen test (2026-09-24)

| task | worker | result | senior findings / fixes |
|---|---|---|---|
| F1 cape | 1 job, 3 check rounds | 3×3 cape bones, skinned grid, Verlet spring baked to keys | Worker **loosened my test** to pass (stream threshold −0.04 → −0.025, rounding on (d)). Real cause: my default spring (0.12/0.18) gave 3 cm lag. Senior sweep → 0.06/0.25 (tip trails 0.17 m at a walk, swings to the legs on a stop, settles in ~18 frames); strict test restored. My test camera did not follow the walk. |
| F2 motion | 2 jobs (first check_failed after 4 rounds) | NLA strips, root motion extracted from the planted foot, turn | **Senior spec bug:** the Quaternius Walk is not constant-speed; constant root speed skated the feet 0.025 m/frame. Worker had also narrowed the test to one foot. New spec: per-frame root advance = planted foot's backward travel → slide 0.0014 m/frame. |
| F3 voice | 1 job, round 1 | voice.py (cached TTS + Rhubarb cues manifest), audio.py wav passthrough, apply_lipsync/auto_blink | — |
| F4 clip | 1 job, round 1 | projects/cp2 screen test, 8 s | Review fixes (senior): Joker grin did not read while talking → teeth part with a dark gap; footsteps 1 frame early + settle steps missing → measured touchdowns (`motion.foot_events`); Joker 8 dB louder → every line normalised to −16 dB RMS; Batman take re-rolled (seed 23). |

**Gemini as reviewer:** useful for audio (it found the loudness gap and a slurred word; picked the clean take),
**unreliable for per-frame visuals** — twice it reported "static mouths" that frame strips prove are animating
(it samples video sparsely). Lip sync / fast motion is judged from frame strips, not Gemini.

Render: output/v7 (first), **output/v8 (review fixes)** — 193 frames, 42 s render at preview size.
Time: ~55 min wall; 7 worker jobs.

## Voices — "closer to the originals" (2026-09-24)
Owner chose reference clips of the original performances. Approved partial downloads (first 6 MB each of two
Dropbox MP3s linked from YouTube Arkham dialogue compilations); Gemini listening picked the clean lines (no PA echo /
music); references pitch/formant-modified with rubberband (Batman 0.93, Joker 1.04) before Chatterbox cloning;
takes chosen by Gemini + ASR read-back ≥ 0.97 ("bagging area" slurred until written "nothing, in the bagging
area"). Casting sheet `assets/cast/voices.json`; machine = Kokoro bf_emma. 101soundboards was behind a bot check
(not bypassed); the Arkham City archive.org pack has only numbered files.

## Checkpoint 3 — the episode as an animatic (2026-09-24)

| task | worker | result | senior findings / fixes |
|---|---|---|---|
| G1 checkout + props | 1 job, 3 rounds | kiosk with 4 screen states, lamp, anchors; milk, batarang, smoke puff | worker fixed a stale-matrix anchor bug itself (test unchanged) |
| G2 Kenney set | 1 job, round 1 | glTF import + textured toon, Gotham Mart layout, flicker | **Senior spec bugs:** Kenney floor tile = 2×2 checker (1.2 m squares at ×2.4) → half scale + tint; wall model 1.44 m deep swallowed the freezers; sign faced the wall (rot (90,0,0) → (90,0,180), same lesson as the name tag) |
| G3 auto-framing | 1 job, 3 rounds | frame/push/whip/check | worker added a damped measure-and-correct loop (perspective broke my closed-form distance at ECU); senior: region() ignored IK empties later |
| G4 reach/hold/throw | 1 job, round 1 | IK reach 0.0000 m, visibility-swap props | senior added `reach_path` (chained reaches overwrote each other's influence keys) |
| G5 captions | 1 job, round 1 | word timings in the manifest, `dur` trim, drawtext captions, `kit/captions.py` | Pillow missing → whole-group highlight |
| G7 QA | 1 job, round 1 | hook / dead time / length | flagged the known hook weakness on the cp2 clip |
| G6 episode | 1 job, round 1 | projects/ep02, 13 shots, 12 lines, 28 SFX | review v10 → v13 (below) |

Review rounds (all senior): **v10** — most shots showed Batman's back (my yaw 0 = customer side), the first wide sat
inside a shelf, IK empties inflated the Joker's framing, captions overlapped, 40.8 s. **v11** — machine-POV shots too
close, two-shot blocked by Batman. **v12** — POV camera moved behind the screen with `clip_start` past the monitor
(the camera *is* the screen), Joker faces Batman and scans with his right hand. **v13** — monitor hidden during POV
shots (edge line). QA: hook PASS (motion 10.96, audio −22.9 dBFS, text frame 1), dead time 0, length 39.2 s.
Render ≈ 6 min at preview size (540x960, 942 frames).
**v14** (audio review — Gemini could not open the audio this time, so measured in the mix): cut-off machine line
trimmed at the end of "item" (1.40 s, from word timings; 1.45 leaked "in"), scanner beep / chime / grab gains up,
Joker's exit footsteps removed under the vengeance line and doubled landings deduplicated. QA PASS, 39.2 s.
