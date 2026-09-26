"""One-time TikTok sign-in (owner approves in the browser): python tools/tiktok_auth.py

Needs in the TikTok developer portal: Login Kit (Desktop) with the redirect URI http://127.0.0.1:8766/callback/ and the scopes
user.info.basic, user.info.stats, video.list (Display API); while unreviewed use the SANDBOX (its own client key/secret →
secrets.json tiktok_sandbox_client_key/_secret) with @dummysticky added as a target user.
Saves %USERPROFILE%/.dummysticky/tiktok_token.json, then lists the account's videos as a check.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import platforms as PF  # noqa: E402

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if not os.path.exists(PF.TT_TOKEN) and not PF.tiktok_login():
        sys.exit(1)
    vids = PF.tiktok_videos()
    print(f"[tiktok] {len(vids)} videos readable")
    for vid, v in list(vids.items())[:10]:
        print(f"  {vid}: {v}")
