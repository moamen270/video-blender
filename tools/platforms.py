"""Shared platform API access (docs/PLATFORM_APIS.md): secrets, Meta Graph API, YouTube Data API.

Secrets live OUTSIDE the repo in %USERPROFILE%/.dummysticky/secrets.json (never commit, never print):
  youtube_api_key            public YouTube Data API reads (views, likes, comments)
  meta_access_token          system-user token (never expires) for the Dummy Sticky app
  meta_page_token            Page token derived from it (refresh: page_token(refresh=True))
  meta_page_id, meta_ig_user_id, meta_app_id
Missing keys simply disable that source; callers fall back to public pages.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

SECRETS = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), ".dummysticky", "secrets.json")
GRAPH = "https://graph.facebook.com/v23.0/"


def secrets() -> dict:
    return json.load(open(SECRETS, encoding="utf-8")) if os.path.exists(SECRETS) else {}


def _save(s: dict) -> None:
    os.makedirs(os.path.dirname(SECRETS), exist_ok=True)
    json.dump(s, open(SECRETS, "w", encoding="utf-8"), indent=1)


def http_json(url: str, params: dict | None = None, data: dict | None = None, timeout: int = 60) -> dict:
    """GET (or POST form `data`) returning JSON; API errors come back as {"error": message} (never the token)."""
    q = "?" + urllib.parse.urlencode(params) if params else ""
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    try:
        with urllib.request.urlopen(urllib.request.Request(url + q, data=body), timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read() or b"{}").get("error", {})
        except ValueError:
            err = {}
        return {"error": (err.get("message") if isinstance(err, dict) else str(err)) or f"HTTP {e.code}"}


# ---- Meta ------------------------------------------------------------------------------------------------------
def page_token(refresh: bool = False) -> str | None:
    s = secrets()
    if s.get("meta_page_token") and not refresh:
        return s["meta_page_token"]
    if not (s.get("meta_access_token") and s.get("meta_page_id")):
        return None
    r = http_json(GRAPH + s["meta_page_id"], {"fields": "access_token", "access_token": s["meta_access_token"]})
    if r.get("access_token"):
        s["meta_page_token"] = r["access_token"]; _save(s)
    return r.get("access_token")


def graph(path: str, *, page: bool = False, post: dict | None = None, **params) -> dict:
    tok = page_token() if page else secrets().get("meta_access_token")
    if not tok:
        return {"error": "no Meta token in secrets.json"}
    if post is not None:
        return http_json(GRAPH + path, data={**post, "access_token": tok})
    return http_json(GRAPH + path, {**params, "access_token": tok})


def meta_ready() -> bool:
    s = secrets()
    return bool(s.get("meta_access_token") and s.get("meta_page_id") and s.get("meta_ig_user_id"))


# ---- YouTube ---------------------------------------------------------------------------------------------------
def youtube_videos(ids: list[str]) -> dict:
    """id -> {views, likes, comments} via the Data API key (public statistics)."""
    key = secrets().get("youtube_api_key")
    if not key or not ids:
        return {}
    r = http_json("https://www.googleapis.com/youtube/v3/videos",
                  {"part": "statistics", "id": ",".join(ids), "key": key})
    out = {}
    for it in r.get("items", []):
        st = it.get("statistics", {})
        out[it["id"]] = {"views": int(st.get("viewCount", 0)), "likes": int(st.get("likeCount", 0)),
                         "comments": int(st.get("commentCount", 0)), "source": "youtube-data-api"}
    return out


# ---- YouTube OAuth (uploads + YouTube Analytics) -------------------------------------------------------------------
YT_SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly",
             "https://www.googleapis.com/auth/yt-analytics.readonly"]
YT_TOKEN = os.path.join(os.path.dirname(SECRETS), "youtube_token.json")


def youtube_login(port: int = 8765, timeout_s: int = 600) -> bool:
    """One-time desktop OAuth: opens the browser, the owner approves, the refresh token is saved to youtube_token.json."""
    import http.server, secrets as pysecrets, threading, webbrowser
    s = secrets()
    redirect = f"http://127.0.0.1:{port}/"
    state = pysecrets.token_urlsafe(16)
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": s["google_client_id"], "redirect_uri": redirect, "response_type": "code",
        "scope": " ".join(YT_SCOPES), "access_type": "offline", "prompt": "consent", "state": state})
    got = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state:
                got.update({k: v[0] for k, v in q.items()})
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
            ok = "code" in got
            self.wfile.write(("<h2>Dummy Sticky: YouTube access " + ("granted. You can close this tab." if ok else
                              "was not granted.") + "</h2>").encode())

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", port), H)
    srv.timeout = 5
    print("[youtube] opening the browser for approval (if it does not open, visit):\n" + url, flush=True)
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    import time as _t
    end = _t.time() + timeout_s
    while "code" not in got and "error" not in got and _t.time() < end:
        srv.handle_request()
    srv.server_close()
    if "code" not in got:
        print("[youtube] no approval:", got.get("error", "timeout"), flush=True)
        return False
    tok = http_json("https://oauth2.googleapis.com/token", data={
        "code": got["code"], "client_id": s["google_client_id"], "client_secret": s["google_client_secret"],
        "redirect_uri": redirect, "grant_type": "authorization_code"})
    if "refresh_token" not in tok:
        print("[youtube] token exchange failed:", tok.get("error") or sorted(tok), flush=True)
        return False
    json.dump({"refresh_token": tok["refresh_token"], "scope": tok.get("scope")}, open(YT_TOKEN, "w"), indent=1)
    print("[youtube] access granted; refresh token saved", flush=True)
    return True


def youtube_access_token() -> str | None:
    if not os.path.exists(YT_TOKEN):
        return None
    s, t = secrets(), json.load(open(YT_TOKEN))
    r = http_json("https://oauth2.googleapis.com/token", data={
        "client_id": s["google_client_id"], "client_secret": s["google_client_secret"],
        "refresh_token": t["refresh_token"], "grant_type": "refresh_token"})
    if not r.get("access_token"):
        # Google app still in "Testing": refresh tokens die after 7 days (docs/PLATFORM_APIS.md)
        print("[youtube] sign-in expired or revoked (%s): run  python tools/youtube_auth.py --relogin"
              % (r.get("error") or "no token"), flush=True)
    return r.get("access_token")


def youtube_get(url: str, params: dict) -> dict:
    tok = youtube_access_token()
    if not tok:
        return {"error": "no YouTube OAuth token (python tools/youtube_auth.py)"}
    req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params), headers={"Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read() or b"{}").get("error", {})
        except ValueError:
            err = {}
        return {"error": (err.get("message") if isinstance(err, dict) else str(err)) or f"HTTP {e.code}"}


YT_ANALYTICS = "https://youtubeanalytics.googleapis.com/v2/reports"


def youtube_analytics(ids: list[str], start: str = "2026-09-01", end: str | None = None) -> tuple[dict, dict]:
    """Per-video YouTube Analytics (OAuth): avg view duration/percentage, shares, subscribers gained, retention curve.
    Analytics lags 2-3 days, so new videos are missing at first. Returns (values by id, raw answers)."""
    import datetime as _dt
    end = end or _dt.date.today().isoformat()
    base = {"ids": "channel==MINE", "startDate": start, "endDate": end}
    r = youtube_get(YT_ANALYTICS, {**base, "dimensions": "video", "sort": "-views", "maxResults": 200,
                                   "metrics": "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,"
                                              "likes,shares,subscribersGained"})
    if "error" in r:
        return {}, {"error": r["error"]}
    cols = [h["name"] for h in r.get("columnHeaders", [])]
    out, raw = {}, {}
    lengths = {}
    key = secrets().get("youtube_api_key")
    if key and ids:
        d = http_json("https://www.googleapis.com/youtube/v3/videos", {"part": "contentDetails", "id": ",".join(ids), "key": key})
        import re as _re
        for it in d.get("items", []):
            m = _re.fullmatch(r"PT(?:(\d+)M)?(?:(\d+)S)?", it["contentDetails"]["duration"])
            lengths[it["id"]] = int(m.group(1) or 0) * 60 + int(m.group(2) or 0) if m else None
    for row in r.get("rows", []):
        v = dict(zip(cols, row))
        if v["video"] not in ids:
            continue
        curve = youtube_get(YT_ANALYTICS, {**base, "dimensions": "elapsedVideoTimeRatio", "metrics": "audienceWatchRatio",
                                           "filters": f"video=={v['video']}"}).get("rows", [])
        length = lengths.get(v["video"])
        at = lambda ratio: min(curve, key=lambda p: abs(p[0] - ratio))[1] if curve else None  # noqa: E731
        out[v["video"]] = {"avg_watch_s": v["averageViewDuration"], "avg_pct": round(v["averageViewPercentage"], 1),
                           "shares": v["shares"], "followers_gained": v["subscribersGained"],
                           "retention_3s_pct": round(100 * at(3 / length), 1) if curve and length else None,
                           "completion_pct": round(100 * at(1.0), 1) if curve else None}
        raw[v["video"]] = {"report": v, "length_s": length, "retention": curve}
    return out, raw


# ---- TikTok (Login Kit for Desktop + Display API video.list) --------------------------------------------------------
TT_TOKEN = os.path.join(os.path.dirname(SECRETS), "tiktok_token.json")
TT_REDIRECT = "http://127.0.0.1:8766/callback/"  # default; register EXACTLY the same string under Login Kit -> Desktop
#                                                  (override with secrets.json "tiktok_redirect_uri", localhost/127.0.0.1 + port)
TT_SCOPES = "user.info.basic,user.info.stats,video.list,video.upload"   # video.upload = drafts to the TikTok inbox


def _tt_keys() -> tuple[str | None, str | None]:
    """Sandbox credentials win while the app is unreviewed (sandbox keys differ from production)."""
    s = secrets()
    if s.get("tiktok_sandbox_client_key"):
        return s["tiktok_sandbox_client_key"], s.get("tiktok_sandbox_client_secret")
    return s.get("tiktok_client_key"), s.get("tiktok_client_secret")


def tiktok_login(timeout_s: int = 600) -> bool:
    """One-time desktop login (PKCE; TikTok desktop uses a HEX sha256 code_challenge). Saves tiktok_token.json."""
    import hashlib, http.server, secrets as pysecrets, threading, time as _t, webbrowser
    key, secret = _tt_keys()
    redirect = secrets().get("tiktok_redirect_uri") or TT_REDIRECT
    port = urllib.parse.urlparse(redirect).port or 80
    verifier = pysecrets.token_urlsafe(64)[:64]
    challenge = hashlib.sha256(verifier.encode()).hexdigest()
    state = pysecrets.token_urlsafe(16)
    url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
        "client_key": key, "scope": TT_SCOPES, "response_type": "code", "redirect_uri": redirect, "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256"})
    got = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state:
                got.update({k: v[0] for k, v in q.items()})
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
            self.wfile.write(("<h2>Dummy Sticky: TikTok access " + ("granted. You can close this tab." if "code" in got
                              else "was not granted.") + "</h2>").encode())

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", port), H); srv.timeout = 5
    print(f"[tiktok] redirect_uri = {redirect} (must match the portal exactly)", flush=True)
    print("[tiktok] opening the browser for approval (if it does not open, visit):\n" + url, flush=True)
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    end = _t.time() + timeout_s
    while "code" not in got and "error" not in got and _t.time() < end:
        srv.handle_request()
    srv.server_close()
    if "code" not in got:
        print("[tiktok] no approval:", got.get("error_description") or got.get("error", "timeout"), flush=True)
        return False
    tok = http_json("https://open.tiktokapis.com/v2/oauth/token/", data={
        "client_key": key, "client_secret": secret, "code": got["code"], "grant_type": "authorization_code",
        "redirect_uri": redirect, "code_verifier": verifier})
    if "refresh_token" not in tok:
        print("[tiktok] token exchange failed:", tok.get("error_description") or tok.get("error") or sorted(tok), flush=True)
        return False
    json.dump({"refresh_token": tok["refresh_token"], "open_id": tok.get("open_id"), "scope": tok.get("scope")},
              open(TT_TOKEN, "w"), indent=1)
    print("[tiktok] access granted; token saved (scopes: %s)" % tok.get("scope"), flush=True)
    return True


def tiktok_access_token() -> str | None:
    if not os.path.exists(TT_TOKEN):
        return None
    key, secret = _tt_keys(); t = json.load(open(TT_TOKEN))
    r = http_json("https://open.tiktokapis.com/v2/oauth/token/", data={
        "client_key": key, "client_secret": secret, "grant_type": "refresh_token", "refresh_token": t["refresh_token"]})
    if r.get("refresh_token") and r["refresh_token"] != t["refresh_token"]:
        t["refresh_token"] = r["refresh_token"]; json.dump(t, open(TT_TOKEN, "w"), indent=1)
    return r.get("access_token")


def tiktok_videos() -> dict:
    """video id -> {views, likes, comments, shares} for the signed-in account (Display API video.list)."""
    tok = tiktok_access_token()
    if not tok:
        return {}
    out, cursor = {}, None
    for _ in range(10):
        body = {"max_count": 20, **({"cursor": cursor} if cursor else {})}
        req = urllib.request.Request(
            "https://open.tiktokapis.com/v2/video/list/?fields=id,create_time,duration,view_count,like_count,comment_count,share_count",
            data=json.dumps(body).encode(), method="POST",
            headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.load(r).get("data", {})
        except urllib.error.HTTPError:
            break
        for v in d.get("videos", []):
            out[v["id"]] = {"views": v.get("view_count"), "likes": v.get("like_count"), "comments": v.get("comment_count"),
                            "shares": v.get("share_count"), "source": "tiktok-display-api"}
        if not d.get("has_more"):
            break
        cursor = d.get("cursor")
    return out


def tiktok_upload_draft(video: str) -> dict:
    """Content Posting API "Upload to TikTok": send the file to the signed-in account's inbox as a DRAFT.
    The owner gets a TikTok notification, edits the caption and posts it from the app (the owner chooses privacy)."""
    tok = tiktok_access_token()
    if not tok:
        return {"error": "no TikTok token: python tools/tiktok_auth.py"}
    size = os.path.getsize(video)
    chunk = size if size <= 64 * 1024 * 1024 else 10 * 1024 * 1024          # one chunk up to 64 MB
    n = max(1, size // chunk)
    init = urllib.request.Request(
        "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
        data=json.dumps({"source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": chunk,
                                         "total_chunk_count": n}}).encode(),
        method="POST", headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"})
    try:
        with urllib.request.urlopen(init, timeout=60) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode("utf-8", "ignore")[:300]}
    data = d.get("data", {})
    if not data.get("upload_url"):
        return {"error": d.get("error")}
    blob = open(video, "rb").read()
    for i in range(n):
        a = i * chunk
        b = size - 1 if i == n - 1 else a + chunk - 1
        put = urllib.request.Request(data["upload_url"], data=blob[a:b + 1], method="PUT",
                                     headers={"Content-Type": "video/mp4", "Content-Length": str(b - a + 1),
                                              "Content-Range": f"bytes {a}-{b}/{size}"})
        try:
            urllib.request.urlopen(put, timeout=600).read()
        except urllib.error.HTTPError as e:
            return {"error": f"chunk {i}: " + e.read().decode("utf-8", "ignore")[:200], "publish_id": data.get("publish_id")}
    return {"publish_id": data["publish_id"], "state": "draft sent to the TikTok inbox"}


def tiktok_publish_status(publish_id: str) -> dict:
    tok = tiktok_access_token()
    req = urllib.request.Request("https://open.tiktokapis.com/v2/post/publish/status/fetch/",
                                 data=json.dumps({"publish_id": publish_id}).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r).get("data", {})
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode("utf-8", "ignore")[:300]}
