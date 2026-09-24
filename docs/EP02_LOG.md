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
