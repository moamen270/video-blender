"""Write projects/<p>/output/v<N>/social.md: ready-to-paste upload text for every platform we publish on.

    python tools/social.py sf01                # latest version
    python tools/social.py sf01 --version 40

Source: projects/<p>/social.json (one title/description/tag set, written per episode) + brand.json
(channel name, handle, links, default hashtags). Same layout as video-builder's `vb social`
(engine/src/social.ts): YouTube Shorts, TikTok, Instagram Reels, Facebook Reels, pinned comment, cover text,
plus the upload checklist (AI label, parody framing, credits). Only the copy file is written; renders are
never touched. make.sh runs this after every render.

social.json fields: title, hook, description, tags[], hashtags[], pinnedComment, coverText,
disclaimer, credits[], checklist[], published{"<N>": url}.
"""
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

YT_TITLE_MAX = 100
YT_TAGS_MAX = 500
IG_CAPTION_MAX = 2200
TT_CAPTION_MAX = 2200


def uniq(xs):
    out = []
    for x in xs:
        x = x.strip()
        if x and x.lower() not in [o.lower() for o in out]:
            out.append(x)
    return out


def clamp(s, n):
    return s if len(s) <= n else s[: n - 1] + "…"


def trim_tags(tags, n):
    out = []
    for t in tags:
        if len(", ".join(out + [t])) > n:
            break
        out.append(t)
    return ", ".join(out)


def seconds_of(mp4):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                           capture_output=True, text=True, check=True)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def markdown(s, brand, version, seconds, url=None):
    hook = s.get("hook") or s["description"].strip().splitlines()[0]
    hashtags = uniq(s.get("hashtags", []) + brand.get("defaultHashtags", []))
    links = brand.get("links", {})
    handle = "\n".join([f'{brand["name"]} {brand["handle"]}'] + [f"{k[0].upper()}{k[1:]}: {u}" for k, u in links.items()])
    body = s["description"].strip()
    extra = [x for x in [s.get("disclaimer", "").strip(), "\n".join(s.get("credits", []))] if x]
    full = "\n\n".join([body] + extra)

    yt_title = clamp(s["title"], YT_TITLE_MAX)
    yt_desc = "\n\n".join([full, handle, " ".join(hashtags)])
    yt_tags = trim_tags(uniq(s.get("tags", [])), YT_TAGS_MAX)
    # TikTok has no #shorts convention; #fyp is the feed tag there.
    tt_tags = uniq(["#fyp"] + [h for h in hashtags if h.lower() != "#shorts"])[:6]
    tt = clamp(f'{hook} {" ".join(tt_tags)}' + (f'\n\n{s["disclaimer"].strip()}' if s.get("disclaimer") else ""),
               TT_CAPTION_MAX)
    ig = clamp("\n\n".join([hook, full, " ".join(hashtags)]), IG_CAPTION_MAX)
    fb = "\n\n".join([hook] + ([s["disclaimer"].strip()] if s.get("disclaimer") else []) + [" ".join(hashtags[:8])])

    md = [f'# {s.get("name", s["title"])} — v{version} ({seconds:.1f} s)', ""]
    if url:
        md += [f"Master: {url}", ""]
    md += ["## YouTube Shorts", "", f"**Title** ({len(yt_title)}/{YT_TITLE_MAX})", "", yt_title, "",
           "**Description**", "", yt_desc, "",
           f"**Tags** ({len(yt_tags)}/{YT_TAGS_MAX} chars, comma-separated)", "", yt_tags, "",
           "## TikTok", "", tt, "",
           "## Instagram Reels", "", ig, "",
           "## Facebook Reels", "", fb, ""]
    if s.get("pinnedComment"):
        md += ["## Pinned comment (all platforms)", "", s["pinnedComment"], ""]
    md += ["## Thumbnail / cover text", "", s.get("coverText") or hook, ""]
    if s.get("checklist"):
        md += ["## Before upload", ""] + [f"- [ ] {c}" for c in s["checklist"]] + [""]
    return "\n".join(md)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--version", type=int)
    a = ap.parse_args()
    pdir = os.path.join(ROOT, "projects", a.project)
    src = os.path.join(pdir, "social.json")
    if not os.path.exists(src):
        print(f"[social] no {src}; add one (title, hook, description, tags, hashtags) and rerun")
        return 1
    s = json.load(open(src, encoding="utf-8"))
    brand = json.load(open(os.path.join(ROOT, "brand.json"), encoding="utf-8"))
    outs = os.path.join(pdir, "output")
    versions = sorted(int(m.group(1)) for d in (os.listdir(outs) if os.path.isdir(outs) else [])
                      if (m := re.fullmatch(r"v(\d+)", d)))
    n = a.version or (versions[-1] if versions else None)
    vdir = os.path.join(outs, f"v{n}")
    mp4 = os.path.join(vdir, "final.mp4")
    if n is None or not os.path.exists(mp4):
        print(f"[social] no rendered version of {a.project} ({vdir})")
        return 1
    url = s.get("published", {}).get(str(n))
    text = markdown(s, brand, n, seconds_of(mp4), url)
    with open(os.path.join(vdir, "social.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"[social] wrote {os.path.relpath(os.path.join(vdir, 'social.md'), ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
