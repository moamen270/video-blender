"""Snapshot the numbers of every published video and append them to analytics/videos.csv.

    python tools/stats.py            # snapshot all videos in analytics/posts.json
    python tools/stats.py --dry      # print, don't write

Sources (best available per platform; tools/platforms.py, keys in %USERPROFILE%/.dummysticky/secrets.json):
- Facebook: Graph API reel insights — plays, reach, avg watch, retention curve (per second, capped at 40 s),
  reactions, followers gained. Fallback: public Reels page (views only, rounded).
- Instagram: Graph API media insights — views, reach, likes, comments, shares, saves, avg watch time.
  Fallback: public Reels page (views, likes, comments).
- YouTube: Data API key — exact, fresh views/likes/comments; YouTube Analytics (OAuth, tools/youtube_auth.py) —
  avg view duration, % watched, retention curve (3 s + completion), shares, subscribers gained (lags 2-3 days).
  YouTube retention is audienceWatchRatio: it can exceed 100 % (rewatches of the opening).
  Fallback: yt-dlp.
- TikTok: public profile via yt-dlp (needs `pip install curl_cffi`); no API access yet.
Raw API answers (incl. the full Facebook retention curve) go to analytics/raw/<date>.json.
Profile listings also report posts that are not in posts.json yet.
"""
import argparse, csv, datetime as dt, json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import platforms as PF  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
COLS = ["date", "slug", "version", "platform", "checkpoint", "views", "retention_3s_pct", "avg_watch_s",
        "completion_pct", "likes", "comments", "shares", "saves", "followers_gained", "hook_text", "notes"]


# ---- public fallbacks -------------------------------------------------------------------------------------------
def ytdlp(*args):
    r = subprocess.run(["yt-dlp", "-J", *args], capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout) if r.stdout.strip() else None


def chrome_dom(url):
    prof = os.path.join(os.environ.get("TEMP", "."), "dummysticky_stats_profile")
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", f"--user-data-dir={prof}", "--lang=en-US",
                        "--virtual-time-budget=15000", "--dump-dom", url],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=180)
    return r.stdout


def num(s):
    if s is None: return None
    s = s.replace(",", ""); m = {"K": 1e3, "M": 1e6}.get(s[-1:], 1)
    return int(float(s.rstrip("KM")) * m)


def youtube_public(vid):
    d = ytdlp("--skip-download", f"https://www.youtube.com/shorts/{vid}") or {}
    return dict(views=d.get("view_count"), likes=d.get("like_count"), comments=d.get("comment_count"), source="yt-dlp")


def tiktok_all(handle):
    d = ytdlp("--flat-playlist", "--impersonate", "chrome", f"https://www.tiktok.com/@{handle}") or {}
    return {e["id"]: dict(views=e.get("view_count"), likes=e.get("like_count"), comments=e.get("comment_count"),
                          shares=e.get("repost_count"), source="yt-dlp") for e in d.get("entries", [])}


def instagram_public(handle):
    html = chrome_dom(f"https://www.instagram.com/{handle}/reels/")
    ms = list(re.finditer(rf'href="/{handle}/reel/([^/"]+)/?"', html)); out = {}
    for i, m in enumerate(ms):
        seg = html[m.end(): ms[i + 1].start() if i + 1 < len(ms) else m.end() + 20000]
        n = re.findall(r'>(\d[\d,.]*[KM]?)</span>', seg)
        if len(n) >= 3: out[m.group(1)] = dict(likes=num(n[0]), comments=num(n[1]), views=num(n[2]), source="public page")
    return out


def facebook_public(page):
    html = chrome_dom(f"https://www.facebook.com/{page}/reels/"); out = {}
    for rid in dict.fromkeys(re.findall(r'/reel/(\d+)', html)):
        seg = html[html.find("/reel/" + rid):][:8000]
        n = re.search(r'>(\d[\d,.]*[KM]?)</span>', seg)
        out[rid] = dict(views=num(n.group(1)) if n else None, source="public page (rounded)" if n and n.group(1)[-1:] in "KM" else "public page")
    return out


# ---- APIs -------------------------------------------------------------------------------------------------------
IG_METRICS = ["views", "reach", "likes", "comments", "shares", "saved", "ig_reels_avg_watch_time"]


def instagram_api() -> tuple[dict, dict]:
    """shortcode -> row values, plus raw answers."""
    s = PF.secrets(); out, raw = {}, {}
    media = PF.graph(f"{s['meta_ig_user_id']}/media", fields="id,shortcode,timestamp,like_count,comments_count", limit=50)
    for m in media.get("data", []):
        vals = {}
        for met in IG_METRICS:   # one call per metric: an unsupported metric must not sink the others
            r = PF.graph(f"{m['id']}/insights", metric=met)
            if "data" in r and r["data"]:
                vals[met] = r["data"][0]["values"][0]["value"]
        raw[m["shortcode"]] = {"media": m, "insights": vals}
        avg = vals.get("ig_reels_avg_watch_time")
        out[m["shortcode"]] = dict(views=vals.get("views"), likes=vals.get("likes", m.get("like_count")),
                                   comments=vals.get("comments", m.get("comments_count")), shares=vals.get("shares"),
                                   saves=vals.get("saved"), avg_watch_s=round(avg / 1000, 1) if avg else None,
                                   reach=vals.get("reach"), source="instagram-graph-api")
    return out, raw


def facebook_api() -> tuple[dict, dict]:
    """reel id -> row values, plus raw answers (incl. the retention curve)."""
    s = PF.secrets(); out, raw = {}, {}
    reels = PF.graph(f"{s['meta_page_id']}/video_reels", page=True, fields="id,created_time,length", limit=50)
    for rl in reels.get("data", []):
        r = PF.graph(f"{rl['id']}/video_insights", page=True)
        vals = {d["name"]: d["values"][0]["value"] for d in r.get("data", [])}
        raw[rl["id"]] = {"reel": rl, "insights": vals}
        curve = vals.get("post_video_retention_graph") or {}
        length = rl.get("length") or 0
        end_key = str(min(int(length), 40)) if length else None
        likes = vals.get("post_video_likes_by_reaction_type") or {}
        out[rl["id"]] = dict(
            views=vals.get("fb_reels_total_plays", vals.get("blue_reels_play_count")),
            reach=vals.get("post_impressions_unique"),
            avg_watch_s=round(vals["post_video_avg_time_watched"] / 1000, 1) if vals.get("post_video_avg_time_watched") else None,
            retention_3s_pct=round(100 * curve["3"], 1) if "3" in curve else None,
            completion_pct=round(100 * curve[end_key], 1) if end_key in curve and length <= 40 else None,
            likes=sum(likes.values()) if isinstance(likes, dict) else None,
            followers_gained=vals.get("post_video_followers"),
            replays=vals.get("fb_reels_replay_count"), source="facebook-graph-api")
    return out, raw


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    posts = json.load(open(os.path.join(ROOT, "analytics", "posts.json"), encoding="utf-8"))
    today = dt.date.today()
    raw = {"date": today.isoformat()}
    if PF.meta_ready():
        ig, raw["instagram"] = instagram_api()
        fb, raw["facebook"] = facebook_api()
    else:
        ig, fb = instagram_public("dummysticky"), facebook_public("DummySticky")
    yt_ids = [v["youtube"] for v in posts["videos"] if v.get("youtube")]
    yt = PF.youtube_videos(yt_ids)
    yta, raw["youtube_analytics"] = PF.youtube_analytics(yt_ids)
    for vid, extra in yta.items():
        if vid in yt:
            yt[vid].update({k: v for k, v in extra.items() if v is not None})
            yt[vid]["source"] = "youtube-data-api + youtube-analytics"
            yt[vid]["avg_pct"] = extra.get("avg_pct")
    tt = tiktok_all("dummysticky")
    rows = []
    for v in posts["videos"]:
        age = (today - dt.date.fromisoformat(v["uploaded"])).days
        got = {"youtube": yt.get(v["youtube"]) or youtube_public(v["youtube"]), "tiktok": tt.get(v["tiktok"], {}),
               "instagram": ig.get(v["instagram"], {}), "facebook": fb.get(v["facebook"], {})}
        for plat, s in got.items():
            extra = "; ".join(f"{k} {s[k]}" for k in ("reach", "replays", "avg_pct") if s.get(k) is not None)
            note = f"uploaded {v['uploaded']}; {s.get('source', 'no data')}" + (f"; {extra}" if extra else "")
            rows.append({"date": today.isoformat(), "slug": v["slug"], "version": v["version"], "platform": plat,
                         "checkpoint": f"day {age}", "hook_text": v["hook"], "notes": note,
                         **{c: s.get(c) for c in ("views", "retention_3s_pct", "avg_watch_s", "completion_pct", "likes",
                                                  "comments", "shares", "saves", "followers_gained")}})
    known = {p: {v[p] for v in posts["videos"]} for p in ("tiktok", "instagram", "facebook")}
    for p, found in (("tiktok", tt), ("instagram", ig), ("facebook", fb)):
        for k in sorted(set(found) - known[p]): print(f"[stats] NEW {p} post not in posts.json: {k}")
    w = csv.DictWriter(sys.stdout, COLS); w.writeheader(); w.writerows(rows)
    if not a.dry:
        path = os.path.join(ROOT, "analytics", "videos.csv")
        new = {(r["date"], r["slug"], r["platform"]) for r in rows}   # a re-run on the same day replaces that day's rows
        old = [r for r in csv.DictReader(open(path, encoding="utf-8")) if (r["date"], r["slug"], r["platform"]) not in new]
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(old + rows)
        os.makedirs(os.path.join(ROOT, "analytics", "raw"), exist_ok=True)
        json.dump(raw, open(os.path.join(ROOT, "analytics", "raw", f"{today.isoformat()}.json"), "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
        print(f"[stats] appended {len(rows)} rows to analytics/videos.csv; raw API answers in analytics/raw/{today}.json")


if __name__ == "__main__":
    main()
