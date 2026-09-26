# Platform APIs — publishing and analytics (plan, 2026-09-26)

Goal (owner): Claude publishes videos and pulls numbers/analytics on YouTube, TikTok, Instagram and Facebook through
official APIs, instead of the owner uploading by hand and `tools/stats.py` reading public pages.
Status: **plan — nothing is set up yet.** Each platform needs a developer app and an owner login first; the owner
does those steps (accounts, verification, consent screens), then Claude builds `tools/publish.py` and upgrades
`tools/stats.py`. Facts below were checked on 2026-09-26 (sources at the end); re-check them during setup.

## Summary
| platform | publish | analytics | hard part | recommendation |
|---|---|---|---|---|
| **Facebook Page** | Reels API `/{page-id}/video_reels` | Page/video insights | none for our own Page: an app in **development mode** can use the admin's own Page with Standard Access (no app review) | **start here** |
| **Instagram** (Business/Creator linked to the Page) | Graph API media container → publish (Reels) | media insights (plays, likes, saves, shares) | same app as Facebook, own account in dev mode; account must be Business/Creator linked to the FB Page; some sources say Reel insights need ≥ 1,000 followers (we have 6) — verify | with Facebook (one Meta app) |
| **YouTube** | Data API v3 `videos.insert` (1 unit/call, 100 uploads/day since 2026-06-01) | YouTube Analytics API (views, watch time, retention, subscribers) for our own channel via OAuth | uploads from an **unaudited** project are forced to **private**; the audit (privacy policy, ToS, use case) takes weeks–months | analytics now; upload as private + owner flips to public (or Claude via API after audit); apply for the audit |
| **TikTok** | Content Posting API (Direct Post) | Display API video list (views/likes/comments/shares) — limited, no retention | **unaudited apps post only as SELF_ONLY and the whole account must be private** while posting → unusable for a public channel until TikTok audits the app | apply for the audit; until then upload by hand (or a paid, already-audited posting service) |

## What the owner does (once)
1. **Meta (Facebook + Instagram)**
   - Instagram: switch @dummysticky to a **Professional (Creator or Business)** account and **link it to the Dummy Sticky Facebook Page**.
   - https://developers.facebook.com → create an app (type *Business*), owner as Administrator; add the products
     *Facebook Login for Business*, *Instagram Graph API* (Instagram API with Facebook Login) and *Video API*.
   - Keep the app in **development mode** (no app review needed for our own Page/account).
   - Graph API Explorer → generate a **long-lived Page access token** with `pages_show_list`, `pages_read_engagement`,
     `pages_manage_posts`, `read_insights`, `instagram_basic`, `instagram_content_publish`, `instagram_manage_insights`,
     `business_management`. Give Claude: app id, app secret, Page id, IG user id, the long-lived token.
2. **Google (YouTube)**
   - https://console.cloud.google.com → new project "dummysticky-publisher" → enable **YouTube Data API v3** and
     **YouTube Analytics API** → OAuth consent screen (External, the owner's Google account as test user) →
     OAuth client of type **Desktop app** → download `client_secret.json`.
   - Claude runs the one-time OAuth login; the owner approves in the browser → refresh token stored locally.
   - Optional (for public uploads by API): the **YouTube API Services Audit** form (needs a public privacy policy and
     terms page, e.g. on GitHub Pages, and a use-case description).
3. **TikTok**
   - https://developers.tiktok.com → create an app, add **Login Kit** + **Content Posting API** (Direct Post) +
     scopes `user.info.basic`, `video.list`, `video.publish`, `video.upload`; a privacy policy/ToS URL is required.
   - Submit the **Direct Post audit** (usage estimate: 1 creator, ~1 post/day). Until approved: manual uploads.

## Secrets (never in git, never in memory)
Local file **outside the repo**: `%USERPROFILE%\.dummysticky\secrets.json` (Meta tokens/ids, TikTok client key/secret)
and `%USERPROFILE%\.dummysticky\youtube_token.json` (OAuth refresh token); `client_secret.json` next to them.
Tools read them from there; nothing is printed or committed. Tokens are revoked from each platform's settings if lost.

## What Claude builds after the keys exist
- `tools/publish.py <episode> --platform youtube|facebook|instagram|tiktok [--at 2026-09-27T18:00]`: uploads
  `output/vN/final.mp4` with the texts from `social.json` (title, description, hashtags, pinned comment where the API
  allows), sets the AI/altered-content disclosure where the API exposes it, records the post id in
  `analytics/posts.json` and the episode's `state.json` (DoD 1).
- `tools/stats.py`: use the APIs where available (exact views, watch time, retention, followers gained), fall back to
  the public pages otherwise; same `analytics/videos.csv` rows.
- A check after posting: read each post's processing/visibility status back (e.g. YouTube `status.privacyStatus`,
  Meta publishing status) and report problems.
- Later: an MCP server wrapping publish/stats so any agent can call them.

## Order
1. Meta app (Facebook + Instagram): same day, no review → publish + insights for 2 of 4 platforms.
2. YouTube: OAuth project → analytics immediately; uploads private until the audit (owner flips to public).
3. TikTok: audit application now; manual uploads meanwhile.

## Sources (2026-09-26)
- YouTube quota & audits: https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits ·
  https://www.outstand.so/blog/youtube-api-pricing-quota · https://postproxy.dev/blog/youtube-upload-api-guide/
- TikTok Direct Post rules: https://developers.tiktok.com/docs/en/content-sharing-guidelines ·
  https://developers.tiktok.com/docs/en/content-posting-api-get-started · https://vorplabs.com/agent-tools/tiktok-content-posting-api
- Instagram Reels API: https://postproxy.dev/blog/instagram-reels-api-publishing-guide/ ·
  https://www.getphyllo.com/post/a-complete-guide-to-the-instagram-reels-api
- Facebook Reels API: https://developers.facebook.com/docs/video-api/guides/reels-publishing/ ·
  https://developers.facebook.com/docs/graph-api/reference/page/video_reels/
- Meta dev mode / app roles: https://developers.facebook.com/docs/development/build-and-test/app-roles/ ·
  https://singhamandeep.com/what-is-meta-advanced-access/
