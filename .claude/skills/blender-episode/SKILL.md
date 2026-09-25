---
name: blender-episode
description: "How to produce an episode in blender-video with the kit (voice → build → render → mix → QA → sheet), the conventions and the traps learned on EP02. Use when planning, scripting (projects/<p>/script.py) or rendering any Blender video in this repo."
---

# Making an episode (blender-video)

Gate first: the premise/script is approved by the owner (skill `comedy-pitch`). Style direction: **3D**
(the 2D cut-out trial, v0.2.0, was rejected). Plan and status: `docs/PRODUCTION_PLAN.md`, `docs/PLAN_STATUS.md`.

## Skill map (load the one for the work at hand)
| work | skill |
|---|---|
| premise, pitches | `comedy-pitch` |
| hook, script, timing, captions, CTA | `hook-script` |
| characters, gear, faces, turnaround | `character-build` |
| voices (Chatterbox default), line direction | `voice-casting` |
| acting, contacts, walking, mocap | `motion-acting` |
| cameras, framing, cuts | `shot-design` |
| SFX, silence, music, mix, loudness | `sound-design` |
| effects, sets | `vfx-sets` |
| review of every render | `episode-review` |
| releases, upload text, analytics | `publish-release` |
| delegating to Gemini | `agy-delegation` (read-only jobs in a scratch cwd, never the repo being edited) |

## Pipeline (all automatic)
1. `projects/<p>/lines.json` — `{id, character, text, [speed, seed, emotion]}`; voices come from
   `assets/cast/voices.json` (skill `voice-casting`).
2. `uv run --project F:/PoCs/video-builder/py python tools/voice.py --project <p>` → cached WAVs, Rhubarb mouth
   cues and word timings in `projects/<p>/voice/manifest.json`. Keep ASR read-back ≥ 0.97.
3. `projects/<p>/script.py` `build()`: timeline constants computed from line lengths (`ceil(seconds·24)`),
   set → characters → motion → faces/lip sync/blinks → cameras → cape bake LAST → `cues.json`
   (lines with `wav`, sfx from the bank, captions via `kit.captions.groups`, overlays, music, beats, grade).
4. `sh tools/make.sh <p> preview|final` → new `projects/<p>/output/vN` (never overwrite): video, mix, final.mp4, `sheet_4hz.png`, `social.md` (from `projects/<p>/social.json`).
5. `uv run ... python tools/qa_episode.py --out projects/<p>/output/vN` (hook, dead time, 25–40 s). Then skill `episode-review`.

## Kit map
`qchar` (Quaternius loader, recolour, parts, native()), `face` (decal eyes/brows, mouths, expressions, lip sync,
blinks), `cast` (Batman, Joker), `cape` (spring bake), `motion` (NLA play, foot-locked `walk_to`, `turn_to`,
IK `reach`/`reach_path`, `hold`/`release`/`throw`, `foot_events`), `look` (toon2, toon_tex, store_night),
`sets` (Kenney import, gotham_mart, flicker), `checkout`, `props`, `shots` (auto-framed frame/push/whip/check),
`captions`. Worker skill `blender-kit` holds the coding rules; `.agy/BRIEF.md` the Blender 5.2 facts.

## Staging rules (each cost a review round on EP02)
- `shots.frame` yaw 0 = camera on world +Y. Put the camera on the side the character FACES; check nothing (bag rack,
  monitor, shelf) sits between camera and face, and the camera is not inside a prop.
- Two characters facing each other: cheat the one who must read toward camera, or use over-the-shoulder shots.
- Machine/object POV: camera behind the object with `clip_start` past it — but it slices hands that come close;
  keep hands out of the clip zone.
- Hold every shot ≥ 1 s; no cut right after a whip pan; entrances happen on screen (no teleports in view — move
  off-screen characters on a cut).
- Every SFX matches something visible (a batarang = air whoosh, never a blade swish); props big enough to read,
  shown in hand before a throw, insert shot on the impact.
- Contacts: hands must reach (chibi arm ≈ 0.55 m); props sit in the hand, not inside the fist; characters must
  not pass through each other or the counter (route walks around props).
- Performances: split lines where delivery changes; key expressions on the words.

## Known look limits
Low-poly chibi dummies, decal faces float off the silhouette at 3/4 angles, canned Quaternius actions (stiff),
EEVEE volume mist is noisy (use the ffmpeg `grade` in cues instead). See `docs/PHASE1_ASSESSMENT.md`.

## Project folders
- One folder per episode under `projects/`, named for the episode in kebab-case (`ryu-vs-ken-last-hadouken`,
  `batman-unexpected-item`), never a code like ep02/sf01.
- Screen tests, voice-take scratch and anything that is not an episode go in `projects/tests/<name>` (`--project tests/<name>`).
- Scripts find their own folder with `HERE = os.path.dirname(os.path.abspath(__file__))`; never hard-code the project name in a path.
