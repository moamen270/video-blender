"""YouTube sign-in (owner approves in the browser): python tools/youtube_auth.py [--relogin]

Uses google_client_id/secret from %USERPROFILE%/.dummysticky/secrets.json; saves the refresh token to
%USERPROFILE%/.dummysticky/youtube_token.json (never in the repo). Scopes: upload, read, YouTube Analytics.
Then checks the channel and one analytics query.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import platforms as PF  # noqa: E402

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--relogin" in sys.argv and os.path.exists(PF.YT_TOKEN):
        os.remove(PF.YT_TOKEN)          # weekly while the Google app is in "Testing" (tokens expire after 7 days)
    if not os.path.exists(PF.YT_TOKEN) and not PF.youtube_login():
        sys.exit(1)
    ch = PF.youtube_get("https://www.googleapis.com/youtube/v3/channels", {"part": "snippet,statistics", "mine": "true"})
    want = PF.secrets().get("youtube_channel_id")
    for c in ch.get("items", []):
        print(f"[youtube] channel {c['snippet']['title']} ({c['id']}): {c['statistics']}")
        if want and c["id"] != want:   # signed in as the wrong channel (e.g. the personal one): throw the token away
            os.remove(PF.YT_TOKEN)
            sys.exit(f"[youtube] WRONG CHANNEL: expected {want} (Dummy Sticky). Token deleted; run again and pick "
                     "the Dummy Sticky channel in Google's account/channel chooser.")
    if "error" in ch:
        print("[youtube] channel check:", ch["error"])
