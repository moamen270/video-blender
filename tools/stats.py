"""Pull public numbers for every published video and append them to analytics/videos.csv.

    python tools/stats.py            # snapshot all videos in analytics/posts.json
    python tools/stats.py --dry      # print, don't write

No logins: YouTube and TikTok via yt-dlp (TikTok needs `pip install curl_cffi` for --impersonate),
Instagram and Facebook from the public profile Reels pages rendered by headless Chrome (views; Instagram also
likes/comments). Retention, average watch and completion are NOT public — they need the platforms' creator
APIs/dashboards (left empty). Profile listings also report posts that are not in posts.json yet.
"""
import argparse, csv, datetime as dt, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
COLS = ["date", "slug", "version", "platform", "checkpoint", "views", "retention_3s_pct", "avg_watch_s",
        "completion_pct", "likes", "comments", "shares", "saves", "followers_gained", "hook_text", "notes"]


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


def youtube(v):
    d = ytdlp("--skip-download", f"https://www.youtube.com/shorts/{v['youtube']}") or {}
    return dict(views=d.get("view_count"), likes=d.get("like_count"), comments=d.get("comment_count"))


def tiktok_all(handle):
    d = ytdlp("--flat-playlist", "--impersonate", "chrome", f"https://www.tiktok.com/@{handle}") or {}
    return {e["id"]: dict(views=e.get("view_count"), likes=e.get("like_count"), comments=e.get("comment_count"),
                          shares=e.get("repost_count")) for e in d.get("entries", [])}


def instagram_all(handle):
    html = chrome_dom(f"https://www.instagram.com/{handle}/reels/")
    ms = list(re.finditer(rf'href="/{handle}/reel/([^/"]+)/?"', html)); out = {}
    for i, m in enumerate(ms):
        seg = html[m.end(): ms[i + 1].start() if i + 1 < len(ms) else m.end() + 20000]
        n = re.findall(r'>(\d[\d,.]*[KM]?)</span>', seg)
        if len(n) >= 3: out[m.group(1)] = dict(likes=num(n[0]), comments=num(n[1]), views=num(n[2]))
    return out


def facebook_all(page):
    html = chrome_dom(f"https://www.facebook.com/{page}/reels/"); out = {}
    for rid in dict.fromkeys(re.findall(r'/reel/(\d+)', html)):
        seg = html[html.find("/reel/" + rid):][:8000]
        n = re.search(r'>(\d[\d,.]*[KM]?)</span>', seg)
        out[rid] = dict(views=num(n.group(1)) if n else None, rounded=bool(n and n.group(1)[-1:] in "KM"))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    posts = json.load(open(os.path.join(ROOT, "analytics", "posts.json"), encoding="utf-8"))
    today = dt.date.today()
    tt, ig, fb = tiktok_all("dummysticky"), instagram_all("dummysticky"), facebook_all("DummySticky")
    rows = []
    for v in posts["videos"]:
        age = (today - dt.date.fromisoformat(v["uploaded"])).days
        got = {"youtube": youtube(v), "tiktok": tt.get(v["tiktok"], {}), "instagram": ig.get(v["instagram"], {}),
               "facebook": fb.get(v["facebook"], {})}
        for plat, s in got.items():
            note = f"uploaded {v['uploaded']}; public snapshot" + ("; views rounded by Facebook" if s.get("rounded") else "")
            rows.append({"date": today.isoformat(), "slug": v["slug"], "version": v["version"], "platform": plat,
                         "checkpoint": f"day {age}", "views": s.get("views"), "likes": s.get("likes"),
                         "comments": s.get("comments"), "shares": s.get("shares"), "hook_text": v["hook"], "notes": note})
    known = {p: {v[p] for v in posts["videos"]} for p in ("tiktok", "instagram", "facebook")}
    for p, found in (("tiktok", tt), ("instagram", ig), ("facebook", fb)):
        for k in set(found) - known[p]: print(f"[stats] NEW {p} post not in posts.json: {k}")
    w = csv.DictWriter(sys.stdout, COLS); w.writeheader(); w.writerows(rows)
    if not a.dry:
        path = os.path.join(ROOT, "analytics", "videos.csv")
        with open(path, "a", newline="", encoding="utf-8") as f: csv.DictWriter(f, COLS).writerows(rows)
        print(f"[stats] appended {len(rows)} rows to analytics/videos.csv")


if __name__ == "__main__":
    main()
