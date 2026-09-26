# blender-video — start here

Code-first 3D comedy Shorts for the **Dummy Sticky** channel (owner: Moamen). Every character, set, camera and
keyframe is Python run headless in Blender 5.2; every render is a new immutable version.
Read this file first, then the skill for the work at hand. Nothing below depends on chat memory.

## Start of every session (and after every compaction)
1. Read this file. 2. Run `python tools/board.py` — the Kanban board of all episodes: status, the gate waiting on
the owner, the `next` action, open owner notes, definition-of-done gaps. 3. Open the active episode's
`projects/<slug>/state.json` and continue from its `next`. The chat is not the memory; the files are.

## How we work — the pipeline (`docs/PIPELINE.md`)
Phases (the `status` in `state.json`), each with fixed input/output files and an owner gate:
`idea` → `pitch` (**G1** premise + pitch PoC) → `script` (**G2**) → `design` (**G3** look, new items only) → `voice`
(timing locked) → `animatic` (**G4** staging) → `animation` → `sound` → `qa` (**G5** final) → `package` →
`awaiting-upload` → `published` → `learn` → `done` (also `dropped`, `archived`).
- **Write it down immediately:** every owner decision, approval or note goes into `state.json` (`gates`,
  `owner_notes` with the phase that must fix it, `decisions`, `next`, `history`, `updated`) *before* acting on it.
  Update `status`/`next` on every phase change. This is what survives compaction and lets a weaker model continue.
- **Send a note back to the earliest phase that caused it** (staging → `animatic`, joke → `pitch`) and redo from there.
- **Components before episodes — search the library first:** `python tools/catalog.py search <text> [--kind K]`
  (gallery with previews: `library/CATALOG.md`). Reuse what exists; build only what is missing, as a reusable kit
  function, then add its entry to `library/catalog.json`, render its preview and rebuild the gallery. Harvest after
  every video: `python tools/catalog.py harvest` must list 0 uncatalogued components (`state.harvested`).
- New episode = **phase 0 first** (`docs/PIPELINE.md` "Phase 0 steps"): exclude the cast/topic of every open episode
  (`tools/board.py`), check events (one event-tied episode at a time, only when the event is close), rank the idea bank
  with the analytics, write the **idea card** in `content/IDEAS.md` §6. Only then
  `python tools/new_episode.py <card-slug> "Title"` (it refuses without a card or on a cast clash)
  (templates in `templates/episode/`: state.json, pitch.md, script.md, design.md, lines.json, social.json),
  then `git checkout -b ep/<slug>`.
- Lanes besides episodes: Research (events, trends, tech radar), Library (components), Platform (tools/checks).
  Weekly: research + pick ideas, `python tools/stats.py`, retro (notes → checks/skill rules, harvest).

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
  logged + reusable parts harvested. Full definition: `docs/PIPELINE.md` §5; branch rules: skill `publish-release`.
- Branches: `main` = finished work; work on `ep/<episode-slug>` or `kit/<topic>`, merge when done.
- Record every owner correction as a skill rule (and in `docs/` logs) so it is never repeated.

## Important files
| file | what it is |
|---|---|
| `tools/platforms.py`, `tools/publish.py`, `tools/youtube_auth.py` | API keys/helpers (secrets outside the repo); publish to Facebook/Instagram/YouTube (dry run unless `--go`; only when the owner asks); one-time YouTube sign-in |
| `site/` | public pages (home, privacy, terms, app icon) at https://moamen270.github.io/video-blender/ — required by the Google and TikTok app reviews |
| `docs/PLATFORM_APIS.md` | plan for publishing + analytics APIs on YouTube, TikTok, Instagram, Facebook: owner setup steps, limits (audits), where secrets live (outside the repo) |
| `docs/PIPELINE.md` | **the process**: phases, inputs/outputs, gates, lanes, definition of done, `state.json` schema, teams, what exists vs planned |
| `projects/<slug>/state.json` | per-episode handoff + memory: status, gates, owner notes, decisions, known issues, next action |
| `library/catalog.json`, `library/CATALOG.md`, `library/previews/` | **component library**: every character, rig, pose, motion, prop, FX, set, camera move, sound, music track and voice, with source, licence, status and preview |
| `tools/catalog.py`, `tools/catalog_preview.py` | library search / check / harvest / gallery; Blender preview renderer |
| `tools/storyboard.py` | pitch PoC (G1): renders `projects/<p>/poc/storyboard.json` panels (library characters or PoC stand-ins, sabers, sets, text overlays) → `poc/board.jpg` |
| `tools/board.py`, `tools/new_episode.py`, `templates/episode/` | Kanban board of episodes; new-episode scaffold; phase templates |
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
| `tools/clip_scan.py`, `tools/make_ref.py` | voice packs: label every game clip talking vs sound (ASR) → pick clips → build the modified Chatterbox reference |
| `tools/voice.py`, `tools/audio.py`, `tools/social.py`, `tools/qa_episode.py` | voices (+ lip sync, word timings), mix/loudness/overlays, upload text, QA |
| `.agy/BRIEF.md`, `.agy/skills/` | standing rules for the Gemini (agy) worker |

## Projects
`projects/<episode-slug>/`: `state.json`, `pitch.md`, `script.md`, `design.md`, `script.py` (timeline + build), `lines.json`, `social.json`, `output/vN/` (git-ignored),
`voice/` (git-ignored). Non-episodes live in `projects/tests/<name>`.
Live status is in each `state.json` (`python tools/board.py`); summary:
| project | status |
|---|---|
| `vader-vs-luke-duel` | `pitch` — 3 pitches + storyboard PoC waiting for G1 |
| `samurai-standoff` | `dropped` at phase 0 (owner: famous characters for now) |
| `ryu-vs-ken-last-hadouken` | `awaiting-upload` — Street Fighter loop, 18 s, final v40 = release v0.3.4. Owner: "not bad, I like it" |
| `batman-unexpected-item` | `published` 2026-09-24 — final v21; owner story 0/10, humour 0/10, style 4/10; Facebook flagged a border |
| `cupid-had-one-job` | `archived` — first pipeline test, v0.1.0 |
| `samurai-duel` | `archived` — early 3D test |
| `tests/rick-and-morty-screen-test` | 2D cut-out trial, v0.2.0, **rejected** (direction: 3D) |

## Commands
```sh
uv run --project F:/PoCs/video-builder/py python tools/voice.py --project <p>   # voices (cached)
sh tools/make.sh <p> preview|final        # -> projects/<p>/output/v<next>/
python tools/social.py <p> [--version N]  # regenerate social.md from social.json
python tools/stats.py                     # snapshot numbers (APIs: FB/IG insights, YouTube key; TikTok public)
python tools/publish.py <p> --platform facebook,instagram [--go] [--at ISO]   # dry run without --go
python tools/board.py                     # episode board: status, next action, DoD gaps
python tools/storyboard.py <p> [--only A1]   # pitch PoC stills -> projects/<p>/poc/board.jpg
python tools/new_episode.py <slug> "Title" # scaffold a new episode from templates/episode
python tools/catalog.py search <text> [--kind K] [--tag T]   # find reusable components (check|harvest|gallery|show)
/f/blender/blender.exe -b --python tools/catalog_preview.py -- --ids <id,...>   # render a component preview
uv run --project F:/PoCs/video-builder/py python tools/qa_episode.py --out projects/<p>/output/vN   # QA incl. border
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
- 2026-09-26: Facebook flagged Batman EP02 "video has a border" (open set top = black band) → `qa_episode.py`
  border check (FAIL on black/white edge band ≥ 5 %). Owner chose only the check; no set rule or checklist change.
- 2026-09-26: the pipeline is in place (`docs/PIPELINE.md`, `state.json` per episode, board, scaffold, templates).
  2026-09-26: library catalog v1 (182 components, 93 rendered previews, audio waveforms, `library/CATALOG.md`).
  Planned next (owner's list): research lane (events calendar, tech radar,
  asset scouting), pitch PoC tooling, animatic spec + compiler + staging checks, per-team subagents, creator analytics.
- 2026-09-26: releases v0.4.0 (Batman v21, published) and v0.4.1 (Samurai v6, archived) created; every episode
  final now has a release.
- **Ryu vs Ken v40: the owner uploads it on 2026-09-27** (their date, not earlier); then register the post ids.
- **Gemini (agy) is unavailable until 2026-09-28** (weekly limit used). Until then do listening/research work
  without it (measure audio yourself, WebSearch for research); do not start agy jobs.
- 2026-09-26: **Meta API live** (FB + IG publish and insights: avg watch, retention curve, reach, followers);
  **YouTube** (API key + OAuth to the Dummy Sticky channel: Analytics — avg view duration, % watched, retention —
  uploads are NOT used: unaudited API uploads are locked private — YouTube is uploaded by hand; audit on hold); **TikTok** numbers via the sandbox app (Display API: views,
  likes, comments, shares; no retention) and **drafts to the TikTok inbox** (`publish.py --platform tiktok`; the owner
  posts from the app); direct TikTok posting needs the production review (`docs/PLATFORM_APIS.md`).
  Keys in `%USERPROFILE%\.dummysticky\secrets.json` — never commit, print or store them in memory.
  Google app published by the owner 2026-09-26 (branding done); if YouTube calls ever fail with an expired token:
  `python tools/youtube_auth.py --relogin`. TikTok production app **in review since 2026-09-26** (direct posting later).
  Publishing with `--go` only when the owner says so (Ryu vs Ken: the owner uploads on 2026-09-27).
- Other repos: `video-builder` has 12 uncommitted changes and 3 unpushed commits and `taxi-trial1` has no GitHub
  remote; this workspace's GitHub access covers only `moamen270/video-blender`, so the owner pushes those.
