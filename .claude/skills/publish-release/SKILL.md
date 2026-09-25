---
name: publish-release
description: How to publish a blender-video milestone — push the branch, GitHub release on moamen270/video-blender with video + scene + sheets, upload text (title = hook, parody framing, AI/altered label, credits) and analytics logging. Use whenever a render is a milestone (new episode/test, owner-approved version) or when preparing an upload.
---

# Publishing

## Definition of done (an episode is DONE only when all of these are true)
1. **Published on every platform** (YouTube Shorts, TikTok, Instagram Reels, Facebook Reels) with the owner-approved
   final, and each post URL recorded in `projects/<p>/social.json` → `"posts": {"youtube": url, ...}`.
2. **GitHub release** of that final exists (below), with `social.md` attached.
3. **Branch merged to `main`** (fast-forward or merge commit) and pushed; the episode branch is then deleted.
4. **Analytics row** for each platform in `analytics/videos.csv` at upload, then 24 h / 72 h / 7 d.
5. **Harvest:** new characters, poses, sets, props, FX, sounds from the episode are reusable from `kit/` / asset
   banks (not only inside `script.py`), and every owner correction from the episode is a skill rule or a check.
A GitHub release alone is a milestone, not done. Until the owner has uploaded, the episode stays "awaiting upload".

## Branches
- `main` = everything finished. One branch per episode or kit change: `ep/<episode-slug>`, `kit/<topic>`.
- Releases may target the branch while in progress; merge to `main` when the episode is done (DoD 3), and
  merge kit work as soon as it is tested so the next episode starts from it.

## GitHub release (every milestone, without being asked)
1. Commit, then `git push -u origin <branch>`.
2. `gh release create vX.Y.Z -R moamen270/video-blender --target <branch> --title "vX.Y.Z — <name>" --notes-file notes.md`
   with the assets: `<slug>-v<N>.mp4` (final.mp4), `<slug>-v<N>-scene.blend`, `sheet-4hz.png`, plus any character/turnaround sheet.
3. Notes follow the v0.1.0 layout: one-line summary, length/resolution/render time, beats, what's new in the
   pipeline, what is placeholder/not final (say it plainly), assets list, a reproduce command, and the
   Claude Code footer.
4. Verify: `gh release view vX.Y.Z --json assets` shows every asset `uploaded`. Give the owner the URL.

## Upload text (`projects/<p>/output/vN/social.md`, every platform)
- Written once per episode in `projects/<p>/social.json` (title, hook, description, disclaimer, credits, tags,
  hashtags, pinnedComment, coverText, checklist, published{N: release mp4 URL}); `make.sh` renders it into each
  version's `social.md` with `brand.json` (handle, links, default hashtags). After editing social.json or
  publishing, rerun `python tools/social.py <p> [--version N]` and attach `social.md` to the release.
- Sections: YouTube Shorts (title ≤100, description, tags ≤500 chars), TikTok, Instagram Reels, Facebook Reels,
  pinned comment, cover text, before-upload checklist. Same layout as video-builder's `vb social`.
- Title = the hook sentence = the cover text. `#shorts` first on YouTube, `#fyp` on TikTok.
- Parody framing in every description for famous characters; turn on the platform's AI/altered-content label
  when voices are cloned (voice policy).
- Credits: music (Kevin MacLeod, CC BY 4.0 line), any CC BY asset.
- One pinned-comment question.

## After upload
- Log into `analytics/videos.csv` (same columns as video-builder's) at upload, 24 h / 72 h / 7 d: views,
  3-s retention, average watch, completion, likes, comments, shares, saves, followers. Every upload is a lesson:
  write the lesson down (skill rule / `docs/` log).
