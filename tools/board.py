"""Print the Episodes board (Kanban) from every projects/<slug>/state.json, plus definition-of-done gaps.

    python tools/board.py          # board + next action per episode
    python tools/board.py --json   # machine-readable

Start every session with this after reading CLAUDE.md: it says which episodes are in flight, which gate
waits on the owner, and what to do next (docs/PIPELINE.md).
"""
import argparse, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = ["idea", "pitch", "script", "design", "voice", "animatic", "animation", "sound", "qa", "package",
         "awaiting-upload", "published", "learn", "done", "dropped", "archived"]


def dod_gaps(st, posts):
    """Definition-of-done items still missing for a published episode."""
    gaps, slug = [], st["slug"]
    reg = next((v for v in posts.get("videos", []) if v["slug"] == slug), None)
    if not reg:
        return ["post ids not in analytics/posts.json"]
    missing = [p for p in ("youtube", "tiktok", "instagram", "facebook") if not reg.get(p)]
    if missing: gaps.append("not posted on " + ", ".join(missing))
    if not (st.get("final") or {}).get("release"): gaps.append("no GitHub release recorded")
    if st.get("branch") not in (None, "", "main"): gaps.append(f"branch {st['branch']} not merged")
    csv_path = os.path.join(ROOT, "analytics", "videos.csv")
    rows = open(csv_path, encoding="utf-8").read() if os.path.exists(csv_path) else ""
    import datetime as dt
    age = (dt.date.today() - dt.date.fromisoformat(reg["uploaded"])).days
    if age >= 7 and f",{slug}," in rows and not any(f"day {d}" in line for line in rows.splitlines()
                                                     if f",{slug}," in line for d in range(7, 60)):
        gaps.append("7-day stats missing (python tools/stats.py)")
    if not st.get("harvested"): gaps.append("harvest to library not recorded (state.harvested)")
    return gaps


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", action="store_true"); a = ap.parse_args()
    posts_path = os.path.join(ROOT, "analytics", "posts.json")
    posts = json.load(open(posts_path, encoding="utf-8")) if os.path.exists(posts_path) else {}
    cards = []
    for path in glob.glob(os.path.join(ROOT, "projects", "**", "state.json"), recursive=True):
        st = json.load(open(path, encoding="utf-8"))
        st["_dir"] = os.path.relpath(os.path.dirname(path), ROOT).replace("\\", "/")
        pending = [g for g, v in (st.get("gates") or {}).items() if v.get("status") == "pending"]
        st["_waiting_gate"] = pending[0] if pending else None
        st["_open_notes"] = sum(1 for n in st.get("owner_notes", []) if n.get("status") == "open")
        st["_dod_gaps"] = dod_gaps(st, posts) if st.get("status") in ("published", "learn") else []
        cards.append(st)
    cards.sort(key=lambda s: (ORDER.index(s["status"]) if s["status"] in ORDER else 99, s["slug"]))
    if a.json:
        json.dump(cards, sys.stdout, indent=2, ensure_ascii=False); return
    sys.stdout.reconfigure(encoding="utf-8")
    for s in cards:
        if s["status"] in ("done", "dropped", "archived"):
            print(f"  [{s['status']}] {s['slug']}"); continue
        print(f"* [{s['status']}] {s['slug']} — {s.get('title', '')}  (updated {s.get('updated', '?')})")
        print(f"    next: {s.get('next', '')}")
        if s["_open_notes"]: print(f"    open owner notes: {s['_open_notes']}")
        if s.get("deadline"): print(f"    deadline: {s['deadline']}")
        for g in s["_dod_gaps"]: print(f"    DoD gap: {g}")
    if not cards: print("no episodes with state.json yet")


if __name__ == "__main__":
    main()
