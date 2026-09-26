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
