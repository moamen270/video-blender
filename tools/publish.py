"""Publish an episode's final video to Facebook, Instagram (Meta APIs) and YouTube (Data API) — docs/PLATFORM_APIS.md.

    python tools/publish.py <episode> --platform facebook,instagram            # DRY RUN: show what would be posted
    python tools/publish.py <episode> --platform instagram --container-only    # upload + process on Instagram, do NOT publish
    python tools/publish.py <episode> --platform facebook,instagram --go       # publish now
    python tools/publish.py <episode> --platform facebook --go --at 2026-09-27T18:00   # Facebook: scheduled (local time)

Video: projects/<episode>/output/v<final>/final.mp4 (state.json final.version, or --version N).
Texts: social.json via tools/social.py captions() (Facebook = facebook text, Instagram = instagram caption);
the pinned-comment question is posted as the first comment (pinning is done in the app).
After publishing: post ids go to analytics/posts.json and the episode's state.json (definition of done 1).
Only the owner decides WHEN something is published: never run with --go unless the owner asked for it.
YouTube (--platform youtube): uploaded with the OAuth token (tools/youtube_auth.py) as PRIVATE — Google keeps uploads
from unaudited API projects private; the owner switches it to Public in YouTube Studio. The AI disclosure is set by the
API (status.containsSyntheticMedia). The pinned comment is not posted on YouTube (needs another scope): add it in Studio.
TikTok (--platform tiktok): the video goes to the @dummysticky INBOX AS A DRAFT (Content Posting API "Upload"); the
owner opens the TikTok notification, pastes the caption printed here, sets privacy and posts. Direct posting needs
TikTok's production review. The post id is registered later (tools/stats.py reports new TikTok posts).
Facebook/Instagram do not expose the AI / altered-content label: turn it on in the app after posting.
"""
from __future__ import annotations

import argparse, datetime as dt, json, os, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import platforms as PF  # noqa: E402
import social as SO  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def upload_bytes(url: str, token: str, path: str) -> dict:
    """Resumable upload of a whole file to rupload.facebook.com (Facebook Reels / Instagram)."""
    size = os.path.getsize(path)
    req = urllib.request.Request(url, data=open(path, "rb").read(), method="POST",
                                 headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size),
                                          "Content-Type": "application/octet-stream"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode("utf-8", "ignore")[:300]}


def instagram(video: str, caption: str, comment: str, *, go: bool, container_only: bool) -> dict:
    s = PF.secrets(); ig = s["meta_ig_user_id"]
    c = PF.graph(f"{ig}/media", post={"media_type": "REELS", "upload_type": "resumable", "caption": caption,
                                      "share_to_feed": "true"})
    if "id" not in c:
        return {"error": f"container: {c.get('error')}"}
    up = upload_bytes(c["uri"], s["meta_access_token"], video)
    if not up.get("success"):
        return {"error": f"upload: {up}"}
    for _ in range(60):                                   # processing usually takes 10-60 s
        st = PF.graph(c["id"], fields="status_code,status")
        if st.get("status_code") in ("FINISHED", "ERROR", "EXPIRED"):
            break
        time.sleep(5)
    if st.get("status_code") != "FINISHED":
        return {"error": f"processing: {st}", "container": c["id"]}
    if container_only or not go:
        return {"container": c["id"], "status": "FINISHED (not published; the container expires in 24 h)"}
    pub = PF.graph(f"{ig}/media_publish", post={"creation_id": c["id"]})
    if "id" not in pub:
        return {"error": f"publish: {pub.get('error')}", "container": c["id"]}
    info = PF.graph(pub["id"], fields="shortcode,permalink")
    if comment:
        PF.graph(f"{pub['id']}/comments", post={"message": comment})
    return {"media_id": pub["id"], "post_id": info.get("shortcode"), "url": info.get("permalink")}


def facebook(video: str, text: str, comment: str, *, go: bool, at: str | None) -> dict:
    s = PF.secrets(); page = s["meta_page_id"]; tok = PF.page_token()
    start = PF.graph(f"{page}/video_reels", page=True, post={"upload_phase": "start"})
    if "video_id" not in start:
        return {"error": f"start: {start.get('error')}"}
    vid = start["video_id"]
    up = upload_bytes(start.get("upload_url") or f"https://rupload.facebook.com/video-upload/v23.0/{vid}", tok, video)
    if not up.get("success"):
        return {"error": f"upload: {up}"}
    fin = {"upload_phase": "finish", "video_id": vid, "description": text,
           "video_state": "SCHEDULED" if at else "PUBLISHED"}
    if at:
        fin["scheduled_publish_time"] = str(int(dt.datetime.fromisoformat(at).timestamp()))
    r = PF.graph(f"{page}/video_reels", page=True, post=fin)
    if not r.get("success"):
        return {"error": f"finish: {r.get('error') or r}", "video_id": vid}
    if comment and not at:
        PF.graph(f"{vid}/comments", page=True, post={"message": comment})
    return {"post_id": vid, "url": f"https://www.facebook.com/reel/{vid}", "state": fin["video_state"],
            **({"scheduled": at} if at else {})}


def youtube(video: str, texts: dict) -> dict:
    """Resumable upload to YouTube (private until the project passes Google's audit)."""
    tok = PF.youtube_access_token()
    if not tok:
        return {"error": "no YouTube token: python tools/youtube_auth.py"}
    meta = {"snippet": {"title": texts["yt_title"], "description": texts["yt_desc"], "categoryId": "23",
                        "tags": [t.strip() for t in texts["yt_tags"].split(",") if t.strip()]},
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}}
    size = os.path.getsize(video)
    init = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode(), method="POST",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)})
    try:
        with urllib.request.urlopen(init, timeout=60) as r:
            loc = r.headers["Location"]
        put = urllib.request.Request(loc, data=open(video, "rb").read(), method="PUT",
                                     headers={"Authorization": f"Bearer {tok}", "Content-Type": "video/mp4"})
        with urllib.request.urlopen(put, timeout=900) as r:
            v = json.load(r)
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode("utf-8", "ignore")[:300]}
    return {"post_id": v["id"], "url": f"https://www.youtube.com/shorts/{v['id']}",
            "state": v.get("status", {}).get("privacyStatus"), "note": "private: switch to Public in YouTube Studio"}


def record(ep: str, st: dict, version: int, results: dict, day: str) -> None:
    """Register the posts in analytics/posts.json and the episode's state.json."""
    pp = os.path.join(ROOT, "analytics", "posts.json"); posts = json.load(open(pp, encoding="utf-8"))
    social = json.load(open(os.path.join(ROOT, "projects", ep, "social.json"), encoding="utf-8"))
    row = next((v for v in posts["videos"] if v["slug"] == ep), None)
    if row is None:
        row = {"slug": ep, "repo": "blender-video", "version": version, "uploaded": day,
               "hook": social.get("hook", ""), "youtube": "", "tiktok": "", "instagram": "", "facebook": ""}
        posts["videos"].append(row)
    for plat, r in results.items():
        if r.get("post_id"):
            row[plat] = r["post_id"]
    json.dump(posts, open(pp, "w", encoding="utf-8", newline="\n"), indent=2, ensure_ascii=False)
    st.setdefault("posts", {}).update({p: r.get("url") for p, r in results.items() if r.get("post_id")})
    st.setdefault("history", []).append({"date": day, "status": st.get("status"),
                                         "note": "published via API: " + ", ".join(p for p, r in results.items() if r.get("post_id"))})
    st["updated"] = day
    json.dump(st, open(os.path.join(ROOT, "projects", ep, "state.json"), "w", encoding="utf-8", newline="\n"),
              indent=2, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode"); ap.add_argument("--platform", default="facebook,instagram")
    ap.add_argument("--version", type=int); ap.add_argument("--go", action="store_true")
    ap.add_argument("--container-only", action="store_true"); ap.add_argument("--at", help="Facebook schedule, local ISO time")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    pdir = os.path.join(ROOT, "projects", a.episode)
    st = json.load(open(os.path.join(pdir, "state.json"), encoding="utf-8"))
    version = a.version or (st.get("final") or {}).get("version")
    video = os.path.join(pdir, "output", f"v{version}", "final.mp4")
    if not os.path.exists(video):
        sys.exit(f"no final video at {video}")
    texts = SO.captions(json.load(open(os.path.join(pdir, "social.json"), encoding="utf-8")),
                        json.load(open(os.path.join(ROOT, "brand.json"), encoding="utf-8")))
    plats = [p.strip() for p in a.platform.split(",") if p.strip()]
    if {"facebook", "instagram"} & set(plats) and not PF.meta_ready():
        sys.exit("Meta keys missing in %USERPROFILE%/.dummysticky/secrets.json")
    print(f"[publish] {a.episode} v{version}: {os.path.getsize(video) / 1e6:.1f} MB -> {', '.join(plats)}"
          f"{'' if a.go else ' (DRY RUN: nothing is published without --go)'}")
    for p in plats:
        body = (f"TITLE: {texts['yt_title']}\n{texts['yt_desc']}\nTAGS: {texts['yt_tags']}\n(private upload, AI disclosure on)"
                if p == "youtube" else texts.get(p, "(not supported)"))
        print(f"--- {p} text ---\n{body}\n--- first comment: {texts['pinned']}")
    if not a.go and not a.container_only:
        return
    results = {}
    for p in plats:
        if p == "instagram":
            results[p] = instagram(video, texts["instagram"], texts["pinned"], go=a.go, container_only=a.container_only)
        elif p == "facebook" and a.go:
            results[p] = facebook(video, texts["facebook"], texts["pinned"], go=True, at=a.at)
        elif p == "youtube" and a.go:
            results[p] = youtube(video, texts)
        elif p == "tiktok" and a.go:
            results[p] = PF.tiktok_upload_draft(video)
            if results[p].get("publish_id"):
                time.sleep(10)
                results[p]["status"] = PF.tiktok_publish_status(results[p]["publish_id"]).get("status")
                print(f"[publish] TikTok caption to paste in the app:\n{texts['tiktok']}")
        else:
            results[p] = {"error": f"{p}: not supported yet (YouTube needs OAuth, TikTok needs an audit)"}
        print(f"[publish] {p}: {results[p]}")
    if a.go and any(r.get("post_id") for r in results.values()):
        record(a.episode, st, version, results, dt.date.today().isoformat())
        print("[publish] recorded in analytics/posts.json and state.json; turn on the AI/altered label in each app")


if __name__ == "__main__":
    main()
