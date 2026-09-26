# Video pipeline — how a Dummy Sticky video is made

Written 2026-09-26 with the owner. This is the process ("SDLC for videos"): phases with fixed inputs and outputs,
owner gates, a definition of done, and the files that carry the work from one phase ("team") to the next.
Rules for *how* to do each phase live in the skills; this file says *what* goes in and out, and *who* decides.

## 1. Principles
1. **The file is the contract — and the memory.** A phase reads only the previous phases' files, never the chat.
   Every owner decision or note is written to `projects/<slug>/state.json` the moment it is made. A new session,
   a compacted session or a weaker model (Gemini Flash) continues from files alone.
2. **Show early, fix early.** Each gate shows the owner the cheapest thing that can answer the question:
   a pitch PoC before a script, an animatic before animation. A note is sent back to the **earliest phase that
   caused it**; everything after that phase is redone from its files.
3. **Components before episodes.** Characters, poses, motions, props, FX, sets, sounds and music are built and
   approved as reusable library items first (Library lane), then assembled into the video. Every finished
   video is harvested back into the library.
4. **Engine-agnostic contracts.** Pitch, script, lines, shots and social files never depend on Blender,
   Remotion or any tool. Engines are plug-ins behind them; new technology is tried in small trials (tech radar).
5. **Every correction becomes a rule or a check.** If the owner has to repeat a note, the Learn phase failed.
6. **Light, not bureaucratic.** One owner, a few agents. Gates are short messages; phases are files.

## 2. Lanes (Kanban, not waterfall)
Work flows as cards on a board; several videos can be in flight (one renders while the next is pitched).
`python tools/board.py` prints the Episodes lane from every `state.json`.

| lane | what moves in it | where it lives |
|---|---|---|
| **Research** (continuous) | events calendar (releases, holidays, viral moments, last month's trends), idea cards, tech radar, asset scouting | `content/` (IDEAS.md; EVENTS.md and TECH_RADAR.md planned) |
| **Library** (continuous) | reusable components: characters, poses, motions, props, FX, sets/environments, sounds, music, voices | `library/catalog.json` + `library/CATALOG.md` (previews) → code in `kit/`, files in `assets/`; `tools/catalog.py` |
| **Episodes** | one card per video, phases 1–11 below | `projects/<slug>/` + `state.json` |
| **Platform** | tools, checks, compiler, MCP servers | `tools/`, `kit/`, skills |

**Weekly cadence (the sprint):** research events and pick ideas → run `python tools/stats.py` → retro: owner
notes become checks/skill rules, new components go to the library → plan next week's videos.

## 3. Episode phases (inputs → outputs → done when)
Status values in `state.json` are the phase ids in the first column.

| # | phase (`status`) | team / player | input | output (files in `projects/<slug>/`) | done when / gate |
|---|---|---|---|---|---|
| 0 | `idea` | Research — Gemini (web) + Claude | events calendar, analytics, idea bank, **every open episode's `state.json`** | idea card in `content/IDEAS.md` §6 (premise, cast, why now, event, deadline) → `tools/new_episode.py` creates the folder (refuses without a card) | card passes the phase-0 steps below |
| 1 | `pitch` | Writers — Claude (skill `comedy-pitch`) | idea card, owner taste | `pitch.md` (3 pitches: logline, why funny, punchline written out, first frame, risk) + **pitch PoC** (storyboard stills or a stickman clip with the key line) | **G1 — owner approves one premise** |
| 2 | `script` | Writers — Claude (skill `hook-script`) | approved pitch | `script.md` (beats with target seconds, hook text, loop/CTA plan, performance direction), `lines.json`, `social.json` draft | **G2 — owner approves the script** |
| 3 | `design` | Art — Claude / platform | script, library (`tools/catalog.py search`) | `design.md`: cast, set, props, FX, poses/motions needed — each marked *reuse* (catalog id) or *build* (Library lane first, then a catalog entry); turnaround/set stills for new items | all components exist; **G3 — owner approves the look of new characters/sets** (skipped if all reused) |
| 4 | `voice` | Voice — scripts + Gemini Pro listening (skill `voice-casting`) | `lines.json`, `assets/cast/voices.json` | `voice/manifest.json` (takes, timings, lip-sync, words), voice preview mp3 | ASR read-back ≥ 0.97, clean takes; **timing locked** |
| 5 | `animatic` | Layout — Claude now; compiler later | script, locked voice, components | `script.py` blocking pass: positions, facing, cameras per beat; draft render (`make.sh <p> draft`) + 4 Hz sheet | staging checks pass; **G4 — owner approves staging & timing** |
| 6 | `animation` | Animation — Claude (skill `motion-acting`, `shot-design`) | approved animatic | full `script.py`: motion, acting, lip sync, FX; preview render | motion/contact review passes (skill `episode-review`) |
| 7 | `sound` | Sound & finishing — scripts (skill `sound-design`) | preview, events, `cues.json` | SFX/music/overlays/captions in the build, `mix.wav`, `final.mp4` (`make.sh <p> final`) | −14 LUFS, sync and caption checks |
| 8 | `qa` | QA — `tools/qa_episode.py` + Gemini Pro (audio) + review (skill `episode-review`) | `final.mp4` | `qa.json`, review notes in `state.json` | QA PASS (hook, dead time, length, **border**); **G5 — owner final review** |
| 9 | `package` | Publishing — scripts (skill `publish-release`) | approved final | `social.json` → `social.md` (4 platforms), GitHub release, cover frame | release assets verified |
| 10 | `awaiting-upload` → `published` | **Owner uploads**; Claude registers | release, `social.md` | post ids in `analytics/posts.json` | posted on YouTube, TikTok, Instagram, Facebook |
| 11 | `learn` → `done` | Analytics + retro — Claude | platform numbers, owner notes | `tools/stats.py` rows at 24 h / 72 h / 7 d; lessons → skills/checks; components harvested to the library; branch merged | **Definition of done** (§5) |

### Phase 0 steps (the idea card) — do all of them, in order
1. `python tools/board.py`: list every episode that is not `done`, `archived` or `dropped`. Its **cast and topic are
   excluded** (never pitch a cast/topic that was just made or is waiting for upload; each `state.json` has `cast`).
2. **Events:** check the events calendar (releases, holidays, trends). An event-tied video is wanted when the event is
   **close** (we can make it and post it in the event's window) and **no other event-tied episode is pending**
   (`state.json` `event`). Otherwise pick an evergreen idea. Never start an event too early (Halloween in September).
3. **Cast: famous (parody) characters for now** (owner, 2026-09-26), not our own original characters — they bring
   the reach (Batman 3D 5,947 views day 1). Revisit only when the owner says.
4. **Idea bank + analytics:** rank candidates in `content/IDEAS.md` by what the numbers say
   (`analytics/videos.csv`: views, avg watch, % watched), the owner's taste (rejected patterns stay rejected) and
   the library (`tools/catalog.py search`: what exists vs must be built).
5. Write the **idea card** in `content/IDEAS.md` §6 (format there): premise, cast, why now, event (or "evergreen"),
   deadline, excluded casts, library reuse/build, numbers behind the choice.
6. `python tools/new_episode.py <card-slug> "Title"` (reads the card; refuses without one or on a cast clash),
   `git checkout -b ep/<slug>`, then phase 1.

Side exits: `dropped` (premise rejected or abandoned — keep the reason), `archived` (old tests).

## 4. Owner gates (what the owner sees, and how long it takes)
| gate | shown | question | ~time |
|---|---|---|---|
| G1 premise | 3 pitches + a pitch PoC | "Is this funny?" | 2 min |
| G2 script | `script.md` + voice preview when ready | "Is this the joke, well told?" | 3 min |
| G3 look | turnaround / set stills (new items only) | "Is this the character/place?" | 1 min |
| G4 animatic | draft render + 4 Hz sheet | "Staging, framing, timing right?" | 2 min |
| G5 final | `final.mp4` | "Ship it?" — taste only; checks caught the mechanics | 1 min |

## 5. Definition of done (an episode is `done` only when all are true)
1. Published on YouTube, TikTok, Instagram and Facebook; post ids in `analytics/posts.json`.
2. GitHub release of the final with `social.md` attached.
3. Branch merged to `main` (branch per episode `ep/<slug>`, per tool change `kit/<topic>`).
4. `analytics/videos.csv` has the 24 h, 72 h and 7 d snapshots (`python tools/stats.py`).
5. Harvest: new components reusable from `kit/`/`assets/` and in `library/catalog.json` with a preview (`tools/catalog.py harvest` = 0); every owner correction is a skill rule or a check.

## 6. `state.json` (one per episode; the handoff and the memory)
```json
{
  "slug": "ryu-vs-ken-last-hadouken",
  "title": "Ryu vs Ken — Who Gets the Last Hadouken",
  "status": "awaiting-upload",
  "branch": "main",
  "updated": "2026-09-26",
  "next": "One sentence: exactly what the next agent/owner does next.",
  "gates": {"G1": {"status": "approved", "date": "2026-09-25", "note": "..."}, "G2": {}, "G3": {}, "G4": {}, "G5": {}},
  "files": {"pitch": "pitch.md", "script": "script.md", "lines": "lines.json", "build": "script.py", "social": "social.json"},
  "final": {"version": 40, "release": "v0.3.4"},
  "owner_notes": [{"date": "", "version": 0, "note": "", "phase": "animation", "status": "open|fixed|wontfix", "fixed_in": 0}],
  "decisions": [{"date": "", "decision": "", "why": ""}],
  "known_issues": ["..."],
  "lessons": ["..."],
  "history": [{"date": "", "status": "", "note": ""}]
}
```
Gate status: `pending` · `approved` · `rejected` · `skipped` (with the reason). Update `status`, `next`,
`updated` and `history` on every phase change; add owner notes with the phase that must fix them.

## 7. Teams = skills + tools (+ subagents later)
One repo. A "team" is a skill (its rules), its tools, and its files. Claude plays most teams; Gemini (agy) is the
cheap worker for literal, checkable tasks; the owner holds the gates. Subagents per team (own context, keeps the
main context small) come when a phase has a contract and a checker a weaker model can pass.

| team | skill(s) | tools | Flash-ready? |
|---|---|---|---|
| Research | `comedy-pitch` (ideas part) | Gemini web search, `content/` | yes, with literal specs |
| Writers | `comedy-pitch`, `hook-script` | templates | no (taste) — formatting only |
| Art / Library | `character-build`, `vfx-sets` | `kit/cast.py`, `tools/turnaround.py` | picking from a catalog: planned |
| Voice | `voice-casting` | `tools/voice.py`, `voice_preview.py`, `shout.py` | yes |
| Layout / Animation | `shot-design`, `motion-acting` | `kit/shots.py`, `kit/fight.py`, `make.sh` | after the spec + compiler |
| Sound | `sound-design` | `tools/audio.py`, `assets/sfx_bank.json` | yes |
| QA | `episode-review` | `tools/qa_episode.py`, sheets | automatic part yes |
| Publishing / Analytics | `publish-release` | `tools/social.py`, `tools/stats.py`, `gh` | yes |

## 8. What exists vs planned (update as it lands)
| item | status |
|---|---|
| phases, gates, DoD, `state.json`, board, new-episode scaffold | ✅ 2026-09-26 |
| QA: hook, dead time, length, border | ✅ |
| upload text for 4 platforms, releases, public stats | ✅ |
| events calendar, tech radar, asset scouting routine | ❌ planned (Research lane) |
| library catalog with previews + search/check/harvest/gallery (`tools/catalog.py`, `tools/catalog_preview.py`) | ✅ 2026-09-26 (182 items) |
| asset scouting into the library (Poly Haven, Kenney, Quaternius, CMU mocap…), motion clips, more sets | ❌ planned |
| pitch PoC tooling (storyboard stills / stickman clip via video-builder) | ❌ planned |
| animatic spec (`shots.json`) + compiler + staging checks (facing, distance, FX over bodies, frame edges) | ❌ planned — biggest win |
| per-team subagents, blender-video MCP tools | ❌ planned |
| publishing + creator analytics via platform APIs (`docs/PLATFORM_APIS.md`) | 🟡 Meta live (FB/IG publish + insights); YouTube live (Analytics + private uploads); TikTok numbers live + drafts to the inbox (sandbox); direct posting pending (review) |
