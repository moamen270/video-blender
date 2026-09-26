# Platform APIs — publishing and analytics (plan, 2026-09-26)

Goal (owner): Claude publishes videos and pulls numbers/analytics on YouTube, TikTok, Instagram and Facebook through
official APIs, instead of the owner uploading by hand and `tools/stats.py` reading public pages.
Status (2026-09-26): **Meta is live** (Facebook + Instagram: publish + insights, system-user token that does not
expire); **YouTube live** (API key for fresh public numbers + OAuth to the Dummy Sticky channel: YouTube Analytics and private uploads; `tools/youtube_auth.py`); **TikTok: numbers live** via the sandbox
(Login Kit Desktop + Display API, signed in as Dummy Sticky on 2026-09-26; publishing: drafts to the @dummysticky inbox work now via Content Posting API "Upload" (`video.upload`, 2026-09-26) —
the owner posts from the app — confirmed 2026-09-26: the draft arrives as a notification in the TikTok PHONE app
(Inbox → system notifications), not on the web profile; direct posting still needs the production review). Tools: `tools/platforms.py` (secrets + API helpers), `tools/stats.py` (API-first numbers),
`tools/publish.py` (Facebook/Instagram publishing, dry run by default). Tested: stats for all 6 videos; an Instagram
upload processed to FINISHED without publishing. Facebook publishing is written but has not posted yet.

Earlier plan text: Each platform needs a developer app and an owner login first; the owner
does those steps (accounts, verification, consent screens), then Claude builds `tools/publish.py` and upgrades
`tools/stats.py`. Facts below were checked on 2026-09-26 (sources at the end); re-check them during setup.

## Summary
| platform | publish | analytics | hard part | recommendation |
|---|---|---|---|---|
| **Facebook Page** | Reels API `/{page-id}/video_reels` | Page/video insights | none for our own Page: an app in **development mode** can use the admin's own Page with Standard Access (no app review) | **start here** |
| **Instagram** (Business/Creator linked to the Page) | Graph API media container → publish (Reels) | media insights (plays, likes, saves, shares) | same app as Facebook, own account in dev mode; account must be Business/Creator linked to the FB Page; some sources say Reel insights need ≥ 1,000 followers (we have 6) — verify | with Facebook (one Meta app) |
| **YouTube** | Data API v3 `videos.insert` (1 unit/call, 100 uploads/day since 2026-06-01) | YouTube Analytics API (views, watch time, retention, subscribers) for our own channel via OAuth | uploads from an **unaudited** project are forced to **private**; the audit (privacy policy, ToS, use case) takes weeks–months | analytics now; upload as private + owner flips to public (or Claude via API after audit); apply for the audit |
| **TikTok** | Content Posting API (Direct Post) | Display API video list (views/likes/comments/shares) — limited, no retention | **unaudited apps post only as SELF_ONLY and the whole account must be private** while posting → unusable for a public channel until TikTok audits the app | apply for the audit; until then upload by hand (or a paid, already-audited posting service) |

## Public site (live 2026-09-26, GitHub Pages from `site/`)
- Home: https://moamen270.github.io/video-blender/
- Privacy policy: https://moamen270.github.io/video-blender/privacy.html
- Terms of service: https://moamen270.github.io/video-blender/terms.html
- App icon: https://moamen270.github.io/video-blender/app-icon-1024.png
Any change under `site/` on `main` redeploys (`.github/workflows/pages.yml`).
- `site/tiktokZpwkIG5QACwbe3eBUPNFoBtyCz2Wvoxz.txt`: TikTok URL-prefix verification for `https://moamen270.github.io/video-blender/` —
  **never delete** (TikTok re-checks it; deleting it un-verifies the app's URLs).
- `site/google4e892d0c6a0100ee.html`: Google Search Console ownership of the site (Google OAuth branding) — **never delete**.
- Root site `https://moamen270.github.io/` = repo `moamen270/moamen270.github.io` (owner-managed; outside this workspace's
  GitHub access): `index.html` forwards to /video-blender/, plus the same Google verification file — **never delete**.
  Google branding home page = `https://moamen270.github.io/`.

## Status log
- 2026-09-26: TikTok production app **submitted for review** (Login Kit Desktop, Display API video.list, Content Posting API
  Upload/drafts; user.info.basic, user.info.stats, video.list, video.upload). Demo video built with `tools/tiktok_demo.py`
  + the owner's phone clip. Waiting on TikTok ("high volume of requests").
- 2026-09-26: Google Auth Platform branding completed (site links, no logo) and the app published by the owner; YouTube
  re-signed in afterwards (Dummy Sticky channel, 2026-09-26) so the token no longer has the Testing 7-day expiry.
  Data Access lists no sensitive scopes → no data-access verification; scopes are requested only at sign-in (do NOT add
  them to the Data Access page, that triggers Google's review). Branding stays unverified → consent screen warning only.

## Google app: Testing → Production
- While the Google Auth Platform app is in **Testing**, refresh tokens expire after **7 days** → the YouTube sign-in of
  2026-09-26 stops working ~2026-10-03; renew with `python tools/youtube_auth.py --relogin` (owner approves).
- To end that: Branding → Application home page / privacy policy / terms = the GitHub Pages site (`site/`), Authorized
  domain `moamen270.github.io` (may need Search Console verification) → Audience → **Publish app** (In production).
  Do **not** upload a logo (that triggers Google's verification review). Unverified production apps show a warning
  screen at sign-in but tokens no longer expire weekly.

## Still needed from the owner
- ~~YouTube OAuth client~~ done 2026-09-26 (signed in as the Dummy Sticky channel `UCPWwluuNVAtYi42L5ilN85Q`; the token is
  rejected if it belongs to another channel). Kept for reference: an **OAuth client** (Desktop app) — Google Cloud console →
  the same project → APIs: YouTube Data API v3 + YouTube Analytics API → OAuth consent screen (owner as test user) →
  Credentials → OAuth client ID → Desktop → download `client_secret.json` into `%USERPROFILE%\.dummysticky\`.
  (The API key alone can only read public numbers.)
- **TikTok** (app "dummy-sticky" exists; production client key/secret saved 2026-09-26). Two tracks:
  1. **Numbers now — Sandbox (no review):** in the developer portal switch to **Sandbox** → create a sandbox →
     Products: **Login Kit** (platform **Desktop**, Redirect URI exactly `http://127.0.0.1:8766/callback/`) and **Display API**;
     Scopes: `user.info.basic`, `user.info.stats`, `video.list` → **Target users → Add account → log in as @dummysticky**
     → send Claude the **sandbox** client key + secret (they differ from production) → Claude runs
     `python tools/tiktok_auth.py` and the owner approves in the browser. Remove *Data Portability API* (not needed;
     it needs its own application).
  2. **Production + publishing (review):** fill the production form: icon `site/app-icon-1024.png`; Terms / Privacy /
     website URLs = the GitHub Pages site (`site/`, workflow `.github/workflows/pages.yml`, live after the owner OKs
     enabling Pages: https://moamen270.github.io/video-blender/terms.html, /privacy.html, /); description and the
     review explanation below; add **Content Posting API** (`video.upload`, `video.publish`) when we want to post;
     a demo video recorded in the sandbox showing the sign-in and the stats/posting flow.
  - Review explanation draft (≤ 1000 chars): "dummy-sticky is a private desktop tool used only by the owner of the
    Dummy Sticky TikTok account (@dummysticky), an animated comedy channel. Login Kit (Desktop): the owner signs in once
    with the channel's own account. user.info.basic / user.info.stats: show the channel's own follower and video counts
    in the owner's production dashboard. video.list: read the view, like, comment and share counts of the channel's
    own videos so the owner can see which videos work and plan the next one. (With Content Posting API:
    video.upload / video.publish: publish the channel's own finished videos with their captions instead of uploading
    them by hand.) The app has no other users, never accesses other accounts, and stores tokens only on the owner's
    computer."
- ~~TikTok: developer app + Direct Post audit (below).~~
- In the apps: turn on the AI/altered-content label after each API post (not exposed by the APIs).

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
