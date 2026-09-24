---
name: publish-release
description: How to publish a blender-video milestone — push the branch, GitHub release on moamen270/video-blender with video + scene + sheets, upload text (title = hook, parody framing, AI/altered label, credits) and analytics logging. Use whenever a render is a milestone (new episode/test, owner-approved version) or when preparing an upload.
---

# Publishing

## GitHub release (every milestone, without being asked)
1. Commit, then `git push -u origin <branch>`.
2. `gh release create vX.Y.Z -R moamen270/video-blender --target <branch> --title "vX.Y.Z — <name>" --notes-file notes.md`
   with the assets: `<slug>-v<N>.mp4` (final.mp4), `<slug>-v<N>-scene.blend`, `sheet-4hz.png`, plus any character/turnaround sheet.
3. Notes follow the v0.1.0 layout: one-line summary, length/resolution/render time, beats, what's new in the
   pipeline, what is placeholder/not final (say it plainly), assets list, a reproduce command, and the
   Claude Code footer.
4. Verify: `gh release view vX.Y.Z --json assets` shows every asset `uploaded`. Give the owner the URL.

## Upload text (`output/vN/social.md`)
- Title = the hook sentence = the cover text. `#shorts` first on YouTube, `#fyp` on TikTok.
- Parody framing in every description for famous characters; turn on the platform's AI/altered-content label
  when voices are cloned (voice policy).
- Credits: music (Kevin MacLeod, CC BY 4.0 line), any CC BY asset.
- One pinned-comment question.

## After upload
- Log into analytics at 24 h / 72 h / 7 d: views, 3-s retention, average watch, completion, likes, shares,
  followers (video-builder's `analytics/videos.csv` format). Every upload is a lesson: write the lesson down.
