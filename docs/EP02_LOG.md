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
