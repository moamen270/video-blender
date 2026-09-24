# Phase one — Blender + agent kit: honest assessment (2026-09-24)

Test episode: EP02 "Unexpected Item" (Batman vs the self-checkout), final `output/v21` (39.9 s, 1080x1920).
Owner verdict: **does not like the result**; accepted as a phase-one test of Blender and the library.

## What it cost
| item | amount |
|---|---|
| wall time, zero kit → final (one working day, incl. review rounds and one usage-limit pause) | ≈ 1 day |
| Gemini worker jobs (17 Flash, 8 Pro listening/review) | 25+ jobs, ≈ 13 M tokens, ≈ 2.3 h of worker time |
| my review rounds on the full episode | v10 → v20 (8 previews) + 3 owner-note rounds |
| render | preview ≈ 6 min, final (full size) ≈ 30–50 min on the GTX 1660 Super |
| code | `kit/` + `tools/` ≈ 6 600 lines, all tested headless (12 test scripts) |

A second episode with the same cast/set would reuse almost everything: estimated ½ day of agent time + review.

## What works (keep it, whatever the style)
- **The pipeline is fully automatic and reproducible**: script → voice lines (cached) → lip sync (Rhubarb) →
  build → render → mix (real CC0 SFX, CC BY music, ducking, loudness) → captions from word timings → grade →
  QA (hook, dead time, length) → 4 Hz sheet. No manual step.
- **Voices**: casting sheet with modified parody clones; ASR read-back; Gemini picks clean takes.
- **Reusable library**: characters (any of 52 Quaternius rigs + recolour/parts/face), NLA motion with foot-locked
  walking, IK reach / hold / throw, spring cape, auto-framed shots, captions, SFX from measured contacts.
- **Agent division of labour**: Gemini Flash writes code from literal specs with a test loop; I spec, measure, review.

## What does not work (why the result disappoints)
1. **Animation is stiff.** Quaternius ships 17 generic game actions; everything else (slam, grab, throw, scan) is
   IK reaching on top of Idle. There is no acting: no anticipation, no weight, no gestures, no head/eye direction.
   For comedy this is the biggest loss — the jokes need timing *in the bodies*.
2. **Characters look generic.** Low-poly chibi "dummies" with white decal eyes read as a mobile game, not a show;
   the faces cannot really act (brows/eye scale/2D mouths only).
3. **Staging costs a lot of review.** Occlusion (bag rack, monitor, shelves), characters facing away, cameras inside
   props — the auto-framer fixes size and centring but not visibility; most of my 8 review rounds were staging.
4. **Set and FX are placeholders.** Kenney props are clean but bland; smoke/batarang are simple geometry; mist in
   EEVEE came out as noise.
5. **Slow iteration.** Every change = a 6-minute preview render before anyone can judge it.

Quality ceiling of this approach as it stands: a tidy mobile-game cutscene. Getting to "a show people follow" in 3D
would need real character art + real motion (mocap or hand-keyed), i.e. much more than kit tweaks.

## Phase-two options (senior view)
| option | idea | pros | cons / risk |
|---|---|---|---|
| **A. Limited 2D ("cut-out") comedy style** in Blender Grease Pencil or 2D planes | flat, bold characters with swappable poses/faces (South-Park-like limited animation); keep the whole pipeline | fits deadpan comedy; poses + expressions matter more than motion; staging problems mostly disappear (flat, frontal); fast renders | needs a consistent 2D character-art source (hand-made in code, or generated art + cleanup) |
| **B. Better 3D characters + real motion** | stylised characters with facial blendshapes (e.g. free VRM/VRoid-style models with permissive licences) + mocap libraries | richer acting and faces; reuses the 3D kit | free commercial mocap is limited (CMU BVH is free; others are non-commercial); licences per model; still heavy review |
| **C. Local AI video on top of Blender layouts** | Blender for layout/timing/camera → AI video-to-video stylisation | can look far better per frame | 6 GB GPU is very tight; temporal consistency and character identity are hard; slow |
| **D. Stay in this style, polish** | more custom actions, better set dressing, FX | lowest risk | owner already dislikes the look; ceiling stays low |

**My recommendation:** before choosing, a **cheap bake-off**: the same 5-second beat ("WHERE. IS. THE ITEM.")
made in A and B (C only as a research spike), compared side by side. First I need the owner's answer to one
question: **what bothers you most — the look of the characters, the animation, the humour, or the pacing?**
