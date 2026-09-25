"""Create a new episode folder from templates/episode (phase 0 -> 1 of docs/PIPELINE.md).

    python tools/new_episode.py <episode-slug> "Episode title" [--why-now "..."] [--deadline YYYY-MM-DD]

The slug is descriptive kebab-case (ryu-vs-ken-last-hadouken), never a code like ep03. Creates
projects/<slug>/ with state.json, pitch.md, script.md, design.md, lines.json and social.json, and prints
the branch to work on (ep/<slug>). Never overwrites an existing folder.
"""
import argparse, datetime as dt, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "templates", "episode")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug"); ap.add_argument("title")
    ap.add_argument("--why-now", default=""); ap.add_argument("--deadline", default="")
    a = ap.parse_args()
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)+", a.slug):
        sys.exit("slug must be descriptive kebab-case with at least two words, e.g. bison-dmv-tuesday")
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
    st["why_now"], st["deadline"] = a.why_now, a.deadline
    json.dump(st, open(st_path, "w", encoding="utf-8", newline="\n"), indent=2, ensure_ascii=False)
    print(f"[new] projects/{a.slug}/ created ({', '.join(sorted(os.listdir(dest)))})")
    print(f"[new] next: git checkout -b ep/{a.slug}; write pitch.md; set status 'pitch' in state.json")


if __name__ == "__main__":
    main()
