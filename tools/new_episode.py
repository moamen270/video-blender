"""Create a new episode folder from templates/episode (phase 0 -> 1 of docs/PIPELINE.md).

    python tools/new_episode.py <card-slug> ["Episode title"] [--override "reason"]

Phase 0 must be done first: the slug needs an idea card ("### card: <slug>") in content/IDEAS.md §6 with every field
filled. Refuses when the card's cast overlaps an open episode (status not done/archived/dropped) or when the card is
event-tied while another open episode is event-tied. --override "reason" bypasses the clash checks and records why.
Title, why now, deadline, cast and event come from the card. The slug is descriptive kebab-case, never ep03. Creates
projects/<slug>/ with state.json, pitch.md, script.md, design.md, lines.json and social.json, and prints
the branch to work on (ep/<slug>). Never overwrites an existing folder.
"""
import argparse, datetime as dt, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "templates", "episode")
IDEAS = os.path.join(ROOT, "content", "IDEAS.md")
FIELDS = ["Title", "Premise", "Cast", "Why now", "Event", "Deadline", "Excluded (open episodes)", "Library", "Numbers"]
CLOSED = {"done", "archived", "dropped"}


def read_card(slug: str) -> dict:
    """Fields of the idea card '### card: <slug>' in content/IDEAS.md ({} if missing)."""
    text = open(IDEAS, encoding="utf-8").read()
    m = re.search(rf"^### card: {re.escape(slug)}\s*$(.*?)(?=^#{{2,3}} |\Z)", text, re.M | re.S)
    if not m:
        return {}
    return {k.strip(): v.strip() for k, v in re.findall(r"^- \*\*(.+?):\*\*\s*(.*)$", m.group(1), re.M)}


def open_episodes() -> list[dict]:
    out = []
    for name in sorted(os.listdir(os.path.join(ROOT, "projects"))):
        f = os.path.join(ROOT, "projects", name, "state.json")
        if os.path.exists(f):
            s = json.load(open(f, encoding="utf-8"))
            if s.get("status") not in CLOSED:
                out.append(s)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug"); ap.add_argument("title", nargs="?")
    ap.add_argument("--override", default="", help="reason to bypass the cast/event clash checks (recorded)")
    a = ap.parse_args()
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)+", a.slug):
        sys.exit("slug must be descriptive kebab-case with at least two words, e.g. bison-dmv-tuesday")
    card = read_card(a.slug)
    if not card:
        sys.exit(f"no idea card '### card: {a.slug}' in content/IDEAS.md section 6 - do phase 0 first (docs/PIPELINE.md)")
    empty = [k for k in FIELDS if not card.get(k) or card[k] in ("...", "…")]
    if empty:
        sys.exit(f"idea card {a.slug}: fill in {', '.join(empty)}")
    cast = [c.strip().lower() for c in card["Cast"].split(",") if c.strip()]
    event = "" if card["Event"].lower().startswith("evergreen") else card["Event"]
    problems = []
    for s in open_episodes():
        clash = set(cast) & {c.lower() for c in s.get("cast", [])}
        if clash:
            problems.append(f"cast {', '.join(sorted(clash))} is in open episode {s['slug']} ({s['status']})")
        if event and s.get("event"):
            problems.append(f"open episode {s['slug']} is already event-tied ({s['event']}): one event video at a time")
    if problems and not a.override:
        sys.exit("refused:\n  " + "\n  ".join(problems) +
                 "\n(fix the card, or --override \"reason\" if the owner asked)")
    a.title = a.title or card["Title"]
    a.why_now = card["Why now"]
    a.deadline = "" if card["Deadline"].lower() == "none" else card["Deadline"]
    dest = os.path.join(ROOT, "projects", a.slug)
    if os.path.exists(dest):
        sys.exit(f"{dest} already exists; not overwriting")
    today = dt.date.today().isoformat()
    os.makedirs(dest)
    for name in os.listdir(TEMPLATE):
        text = open(os.path.join(TEMPLATE, name), encoding="utf-8").read()
        text = text.replace("__SLUG__", a.slug).replace("__TITLE__", a.title).replace("__DATE__", today)
        with open(os.path.join(dest, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    st_path = os.path.join(dest, "state.json")
    st = json.load(open(st_path, encoding="utf-8"))
    st["why_now"], st["deadline"], st["cast"], st["event"] = a.why_now, a.deadline, cast, event
    st["idea_card"] = f"content/IDEAS.md#card-{a.slug}"
    if problems:
        st["decisions"].append({"date": today, "decision": "created despite: " + "; ".join(problems),
                                "why": a.override})
    json.dump(st, open(st_path, "w", encoding="utf-8", newline="\n"), indent=2, ensure_ascii=False)
    print(f"[new] projects/{a.slug}/ created ({', '.join(sorted(os.listdir(dest)))})")
    print(f"[new] next: git checkout -b ep/{a.slug}; write pitch.md; set status 'pitch' in state.json")


if __name__ == "__main__":
    main()
