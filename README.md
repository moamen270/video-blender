# blender-video

Code-first 3D shorts in Blender, built so humans and AI agents can work on the same assets
with the same tools. Every character, prop, camera cut and keyframe is Python; every render
is a new `projects/<name>/output/vN/` that is never overwritten, with a `social.md` ready to paste on every platform.

```
studio/          reusable library (the "asset pack")
  core.py        scene reset, materials, primitives, keyframes, cameras, cuts, render settings
  characters.py  build_character() rig + poses/cycles (walk, bounce, squash, eyes, mouth…)
  props.py       bow/arrow/shield/helmet/wings/halo/heart/star, trees/rocks/clouds/text
projects/<name>/   one folder per episode, named for the episode (kebab-case: ryu-vs-ken-last-hadouken)
  script.py      the story: a timeline of frame constants + calls into studio
  cues.json      audio cue sheet emitted by the build (frames → sfx / narration lines)
  social.json    upload text: title, hook, description, tags, hashtags, pinned comment, cover, checklist
  output/vN      scene.blend, video.mp4, mix.wav, final.mp4, sheet_4hz.png, social.md, render.log  (never overwritten)
projects/tests/  screen tests, voice-take scratch and other non-episodes (same layout; --project tests/<name>)
brand.json       channel identity (name, handle, links, default hashtags) used in every social.md
tools/
  build.py       blender -b … : build scene, save scene.blend, render video.mp4
  audio.py       narration (Kokoro via video-builder/py) + SFX + music → mix.wav → final.mp4
  live.py        helpers for the live Blender MCP session: load(), look(), contact()
  sheet.sh       tile review frames into a contact sheet
  make.sh        one-shot: next version dir → build+render → audio → final.mp4 → social.md
  social.py      projects/<p>/social.json + brand.json → output/vN/social.md (YouTube, TikTok, Instagram, Facebook)
assets/sfx       wav library (some synthesized on first use by audio.py)
output/review    low-res contact sheets used while iterating
```

## Make a video

```sh
sh tools/make.sh cupid-had-one-job preview     # ~3 min on a GTX 1660 S: projects/cupid-had-one-job/output/v<next>/final.mp4
sh tools/make.sh cupid-had-one-job final       # 1080x1920, 64 samples
```

## Iterate with an agent (Blender MCP)

Blender open → sidebar "MCP for Blender" → Connect. Then from Claude Code / any MCP client:

```python
exec(open('F:/PoCs/blender-video/tools/live.py').read())
load('projects/cupid-had-one-job/script.py')         # rebuilds the whole scene from code in the live session
look(frame=300)                          # camera view, material shading, jump to a frame
contact([30, 125, 300], 'output/review/x')   # render stills through the cut cameras
```

Edit `script.py` / `studio/*`, re-run `load()`, screenshot, repeat. A human can open
`projects/<name>/output/vN/scene.blend` and pose/tweak anything in the UI — the rig is plain parented objects
with Empties as joints, camera cuts are timeline markers, the bow string is an animated curve point.

## Conventions

- 24 fps, 1080x1920 (Shorts). Frame numbers in `script.py` are the single source of truth;
  `cues.json` is generated from them so audio can never drift from animation.
- Characters face local -Y; `root` rotates around Z to turn. Joint X rotation swings limbs.
- `C.visible(obj, frame, on)` keys visibility for the object *and its children*; always give an
  initial key at frame 1.
- Never hard-code enum ids (`_set_enum` tries candidates) — Blender 5.x renamed several.
