"""Demo of the dummy-sticky TikTok integration for TikTok's app review (records the screen while it runs).

    python tools/tiktok_demo.py [--video projects/samurai-duel/output/v6/final.mp4] [--out <demo.mp4>] [--no-record]

Flow shown: Login Kit (Desktop) sign-in in the browser -> user.info.basic + user.info.stats (account check) ->
video.list (the channel's own video numbers) -> video.upload (a draft sent to the @dummysticky inbox) + status.
Runs against the sandbox keys (secrets.json tiktok_sandbox_*). The recording is written with ffmpeg gdigrab.
"""
import argparse, json, os, subprocess, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import platforms as PF  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def say(text: str, pause: float = 2.0) -> None:
    print(text, flush=True)
    time.sleep(pause)


def to_front() -> None:
    """Bring this console window back in front of the browser (and maximise it) so the recording shows the steps."""
    try:
        import ctypes
        k32, u32 = ctypes.windll.kernel32, ctypes.windll.user32
        h = k32.GetConsoleWindow()
        if h:
            u32.keybd_event(0x12, 0, 0, 0); u32.keybd_event(0x12, 0, 2, 0)   # ALT tap: lets SetForegroundWindow work
            u32.ShowWindow(h, 3)                                             # SW_MAXIMIZE
            u32.SetForegroundWindow(h)
    except Exception:
        pass


def user_info(tok: str) -> dict:
    req = urllib.request.Request("https://open.tiktokapis.com/v2/user/info/?fields=display_name,follower_count,likes_count,video_count",
                                 headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["data"]["user"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default=os.path.join(ROOT, "projects", "samurai-duel", "output", "v6", "final.mp4"))
    ap.add_argument("--out", default="F:/PoCs/agy_scratch/tiktok_demo/demo_raw.mp4")
    ap.add_argument("--no-record", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    rec = None
    to_front()
    if not a.no_record:
        rec = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "gdigrab", "-framerate", "15", "-i", "desktop",
                                "-vf", "scale=1280:-2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
                                "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
        time.sleep(2)
    try:
        say("=" * 70, 0)
        say("  dummy-sticky  —  Dummy Sticky's private publishing + stats tool", 0)
        say("  TikTok integration demo (sandbox): Login Kit, Display API, Content Posting API", 0)
        say("=" * 70, 3)

        say("\n[1/4] Login Kit (Desktop): sign in with the channel's own TikTok account.", 1)
        say("      The browser opens TikTok's consent page; the owner approves.", 2)
        if os.path.exists(PF.TT_TOKEN):
            os.remove(PF.TT_TOKEN)                      # show the full consent flow
        if not PF.tiktok_login():
            say("      Sign-in was not completed.", 1)
            return
        time.sleep(3)                                   # keep the "access granted" page in the recording
        to_front()
        tok = PF.tiktok_access_token()
        say("      Signed in. The token is stored only on this computer.", 3)

        say("\n[2/4] user.info.basic + user.info.stats: check the signed-in account.", 1)
        u = user_info(tok)
        say(f"      Account: {u.get('display_name')}   followers {u.get('follower_count')}   "
            f"likes {u.get('likes_count')}   videos {u.get('video_count')}", 4)

        say("\n[3/4] video.list (Display API): numbers of the channel's own videos.", 1)
        vids = PF.tiktok_videos()
        say(f"      {'video id':<22}{'views':>8}{'likes':>8}{'comments':>10}{'shares':>8}", 0)
        for vid, v in vids.items():
            say(f"      {vid:<22}{v['views']:>8}{v['likes']:>8}{v['comments']:>10}{v['shares']:>8}", 0.4)
        say("      -> used by the owner to see which videos work and plan the next one.", 4)

        say(f"\n[4/4] video.upload (Content Posting API): send a finished video to the owner's inbox as a DRAFT.", 1)
        say(f"      File: {os.path.relpath(a.video, ROOT)} ({os.path.getsize(a.video) / 1e6:.1f} MB)", 2)
        r = PF.tiktok_upload_draft(a.video)
        if "publish_id" not in r:
            say(f"      Upload failed: {r}", 3)
            return
        say(f"      Uploaded. publish_id = {r['publish_id']}", 1)
        status = None
        for _ in range(24):
            st = PF.tiktok_publish_status(r["publish_id"])
            status = st.get("status")
            say(f"      status: {status}", 2.5)
            if status in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE", "FAILED"):
                break
        say("\n      The draft is now in the @dummysticky TikTok inbox: the owner opens the notification,", 0)
        say("      edits the caption, chooses privacy and posts it from the TikTok app.", 4)
        say("\nDemo complete.", 2)
    finally:
        if rec:
            rec.communicate(b"q")
            print(f"[demo] recording saved: {a.out}", flush=True)


if __name__ == "__main__":
    main()
