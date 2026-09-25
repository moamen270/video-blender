# Plan status — checklist of docs/PRODUCTION_PLAN.md

Last checked against the code: 2026-09-25. ✅ done · 🟡 partial · ❌ not started. Update this file when an item changes.
Each factor has a skill with its rules (see the skill map in `.claude/skills/blender-episode/SKILL.md`).

| # | factor (skill) | item | status |
|---|---|---|---|
| 1 | Concept & hook (`comedy-pitch`, `hook-script`) | idea bank (`content/IDEAS.md`) | ✅ |
| | | 3 hook variants per episode, previewed | ❌ |
| | | hook auto-check (`tools/qa_episode.py`) | ✅ |
| | | frame 1 = cover test | ❌ |
| 2 | Script & timing (`hook-script`) | script template | 🟡 scripts in `content/scripts/`, no fixed template |
| | | table read | ✅ replaced by owner pitch approval (model scores proved useless) |
| | | captions from word timings (`kit/captions.py`) | ✅ |
| | | dead-time check, `beats` markers | ✅ |
| 3 | Characters (`character-build`) | Quaternius rigs, gear parts, decal faces, lip sync, cast builders, toon look | ✅ |
| | | turnaround tool (`tools/turnaround.py`) | ✅ |
| | | silhouette check | ❌ |
| | | character quality (owner: style 4/10) | 🟡 |
| 4 | SFX & silence (`sound-design`) | real CC0 bank (incl. sci-fi pack) | ✅ |
| | | footsteps from measured foot contacts | ✅ |
| | | generic event-driven SFX | 🟡 per project |
| | | `silence:` markers | ❌ |
| 5 | Shots & editing (`shot-design`) | auto-framed named shots, push, whip, coverage check | ✅ |
| | | orbit, rack focus, slow-mo, cut-on-action rule | ❌ |
| | | face-visibility / occlusion check | ❌ |
| 6 | Voices (`voice-casting`) | casting sheet, parody clones, ASR read-back | ✅ |
| | | Chatterbox as default engine | ✅ 2026-09-24 |
| | | per-sentence direction | 🟡 rule written, not yet applied to an episode |
| | | Rick and Morty voices | ❌ owed |
| 7 | Motion (`motion-acting`) | foot-locked walk, IK reach/hold/throw, spring cape | ✅ |
| | | CMU mocap retarget, gesture/acting library | ❌ (main cause of stiffness) |
| | | rigid-body props/debris | ❌ |
| 8 | VFX (`vfx-sets`) | spark, smear, dust, shake, helmet split, smoke, batarang | ✅ |
| | | fire, explosion, shockwave, debris, speed lines | ❌ |
| 9 | Music (`sound-design`) | CC BY library, ducking, loudnorm −14 (both mux branches) | ✅ |
| | | mood/tempo tags, beat snap, auto credit line | ❌ |
| 10 | Sets (`vfx-sets`) | Gotham Mart (Kenney) | ✅ |
| | | set library with look presets | ❌ |
| × | Packaging (`publish-release`) | GitHub releases | ✅ v0.1.0, v0.2.0 |
| | | auto `social.md` (all 4 platforms, `tools/social.py`) | ✅ 2026-09-25 |
| | | definition of done = published + merged + analytics (skill `publish-release`) | ✅ rule written 2026-09-25 |
| × | Analytics | public numbers for all 4 platforms (`tools/stats.py`, `analytics/posts.json`) | ✅ 2026-09-25 (6 videos backfilled) |
| | | retention / avg watch / completion (creator APIs) | ❌ |
| × | Episode compiler | spec → episode | ❌ |

## Process (docs/PIPELINE.md)
| item | status |
|---|---|
| phases, gates, DoD, `state.json` per episode, board, new-episode scaffold, templates | ✅ 2026-09-26 |
| library catalog + harvest, research lane (events, tech radar, scouting), pitch PoC, animatic compiler, subagents | ❌ planned |

## EP02 owner-flagged defects → automatic checks
| defect | check | status |
|---|---|---|
| fist sinking into the milk | prop-in-hand intersection | ❌ |
| Joker's arm through Batman | character/character intersection | ❌ |
| eyes/brows off the head at 3/4 | decal-outside-silhouette at the shot camera | ❌ |
| clip plane slicing fists | near-clip cutting a character | ❌ |
| PLEASE WAIT text off-centre | text centred in its panel | ❌ |

## Roadmap phases
| phase | status |
|---|---|
| 1 Hook & script machine | 🟡 ~60 % |
| 2 Character kit + look-dev | 🟡 ~70 % (quality below the bar) |
| 3 Sound & voice | 🟡 ~50 % (voices owed) |
| 4 Shot library & editing | 🟡 ~60 % |
| 5 Action library & physics | 🟡 ~30 % |
| 6 FX & sets | 🟡 ~30 % |
| 7 Episode compiler | ❌ |

## Tried and dropped
- 2D cut-out style (Rick and Morty parody, release v0.2.0, branch `rm01-cutout`): rejected by the owner
  ("very poor"). Kept from it: the voice.py word-timing fix, the loudnorm fix, the Kenney sci-fi SFX.
