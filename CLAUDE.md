# blender-video — start here

Code-first 3D comedy Shorts for the **Dummy Sticky** channel (owner: Moamen). Every character, set, camera and
keyframe is Python run headless in Blender 5.2; every render is a new immutable version.
Read this file first, then the skill for the work at hand. Nothing below depends on chat memory.

## Owner rules (always)
- **A question gets an answer, not an action.** Explain/propose, then wait for the go-ahead.
- No permission prompts for work the owner asked for: decide, do, report. Creative choices (premise, look) go to the owner.
- **The owner judges the joke.** Model/Gemini comedy scores are worthless (EP02: Gemini 9/10, owner 0/10). Pitch first
  (skill `comedy-pitch`, in `~/.claude/skills/`), build only an approved premise.
- **Never overwrite or delete a render.** Every render is a new `projects/<p>/output/vN`.
- **No synthesized audio.** Sounds only from `assets/sfx_bank.json` (real CC0 recordings), music only from licensed files.
- Voices: modified parody clones (Chatterbox), AI/altered label on upload, parody line in every description.
  **Never commit voice references (`assets/library/voices_ref/`) or API keys** (git-ignored; keep it that way).
- Loops continue through the action (last frame = setup of frame 1); never a white/black flash.
- Every milestone render → GitHub release on `moamen270/video-blender` (skill `publish-release`).
- **Done = published on all 4 platforms** (post URLs recorded) + GitHub release + **merged to `main`** + analytics
  logged + reusable parts harvested. Full definition and branch rules: skill `publish-release`.
- Branches: `main` = finished work; work on `ep/<episode-slug>` or `kit/<topic>`, merge when done.
- Record every owner correction as a skill rule (and in `docs/` logs) so it is never repeated.

## Important files
| file | what it is |
|---|---|
| `README.md` | layout, `make.sh`, live Blender-MCP loop |
| `.claude/skills/blender-episode/SKILL.md` | **how to make an episode** + skill map (hook-script, character-build, voice-casting, motion-acting, shot-design, sound-design, vfx-sets, episode-review, publish-release) |
| `docs/PLAN_STATUS.md` | checklist of the production plan: what is done / partial / missing |
| `docs/PRODUCTION_PLAN.md` | the 10 quality factors + roadmap phases |
| `docs/PHASE1_ASSESSMENT.md` | honest assessment of the 3D approach (cost, what works, what doesn't) |
| `docs/EP02_LOG.md`, `docs/SAMURAI_LOG.md` | owner scores and notes per version (evidence) |
| `content/IDEAS.md`, `content/scripts/` | idea bank and written scripts |
| `brand.json` | channel name, handle, platform links, default hashtags |
| `assets/cast/voices.json` | voice casting (engine, reference wav, pitch) per character |
| `analytics/posts.json`, `analytics/videos.csv` | every published video's post ids (all channel videos, both repos) and the numbers log |
| `tools/stats.py` | pulls public views/likes from YouTube, TikTok, Instagram, Facebook (no login) → appends to `videos.csv` |
| `assets/sfx_bank.json`, `assets/library/LICENSES.md` | sound bank (ids → CC0 files) and every asset licence |
| `kit/` | the library: `qchar` (Quaternius rigs), `cast` (character builders: Batman, Joker, Ryu, Ken…), `fight` (poses, fireballs, rooftop, leaves), `shots` (auto-framed cameras), `face`, `motion` (IK), `captions`, `post` (bloom), `sets`, `fx` |
| `tools/make.sh` | one command: build → render → mix → `final.mp4` → 4 Hz sheet → `social.md` |
| `tools/voice.py`, `tools/audio.py`, `tools/social.py`, `tools/qa_episode.py` | voices (+ lip sync, word timings), mix/loudness/overlays, upload text, QA |
| `.agy/BRIEF.md`, `.agy/skills/` | standing rules for the Gemini (agy) worker |

## Projects
`projects/<episode-slug>/`: `script.py` (timeline + build), `lines.json`, `social.json`, `output/vN/` (git-ignored),
`voice/` (git-ignored). Non-episodes live in `projects/tests/<name>`.
| project | status |
|---|---|
| `ryu-vs-ken-last-hadouken` | latest (Street Fighter loop, 18 s). Final v40 = release v0.3.4. Owner: "not bad, I like it" |
| `batman-unexpected-item` | EP02, final v21; owner story 0/10, humour 0/10, style 4/10 |
| `cupid-had-one-job` | first pipeline test, v0.1.0 |
| `samurai-duel` | early 3D test |
| `tests/rick-and-morty-screen-test` | 2D cut-out trial, v0.2.0, **rejected** (direction: 3D) |

## Commands
```sh
uv run --project F:/PoCs/video-builder/py python tools/voice.py --project <p>   # voices (cached)
sh tools/make.sh <p> preview|final        # -> projects/<p>/output/v<next>/
python tools/social.py <p> [--version N]  # regenerate social.md from social.json
python tools/stats.py                     # snapshot numbers for every video in analytics/posts.json
gh release create vX.Y.Z -R moamen270/video-blender --target <branch> ...
```
Blender: `F:/blender/blender.exe` (5.2). A final render ≈ 6 min (GTX 1660 Super).

## Related repos (F:/PoCs)
- `video-builder` — the earlier stickman engine (Remotion + Kokoro/Chatterbox, JSON manifest, MCP tools).
  Its `docs/LESSONS.md` is the owner's correction log from that period; its Python env (`py/`) runs our voice tools;
  `analytics/videos.csv` is the (incomplete) upload log.
- `audios` — voice research (why Chatterbox). `agy_scratch/` — scratch cwd for read-only Gemini jobs.

## Current state (update when it changes)
- 2026-09-25: all work merged to `main` (housekeeping). Old branches removed.
- 2026-09-25: numbers backfilled (`python tools/stats.py`, day 1–8): Batman EP02 (3D) 5,947 views in 1 day on
  4 platforms vs 554–1,438 for each stickman video in 4–8 days. TikTok gave Wolverine/Jhin/Dodgeball 1–2 views
  (likely restricted — owner to check TikTok Studio). Retention/avg watch need creator dashboards/APIs (not public).
  `analytics/` is the canonical log for the whole channel (video-builder's sheet is superseded).
- Open proposals awaiting the owner: a phased production process (research → pitch PoC → script → design →
  voice → animatic → animation → sound → QA → publish → learn), a reusable component/asset/set library,
  per-episode `state.json`, analytics pulled from the platforms.
- Ryu vs Ken v40 is ready but not uploaded yet (as far as the repo knows).
