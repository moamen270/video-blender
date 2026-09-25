"""The component library: search it, check it, find what is not catalogued yet, and build the gallery.

    python tools/catalog.py search [text] [--kind set] [--tag night] [--status approved]
    python tools/catalog.py show set/gotham-mart
    python tools/catalog.py check        # every source exists, ids unique, kinds valid, previews present (exit 1 on errors)
    python tools/catalog.py harvest      # kit functions / poses / cast / sfx / music / voices / rigs not in the catalog yet
    python tools/catalog.py gallery      # waveforms for audio items + library/CATALOG.md (thumbnails, grouped by kind)

The catalog is library/catalog.json (docs/PIPELINE.md, Library lane): before building anything for an episode,
search here and REUSE; build only what is missing, as a reusable kit function, then add its entry here.
Blender previews: blender -b --python tools/catalog_preview.py -- [--ids a,b] [--force].
"""
import argparse, ast, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "library", "catalog.json")
PREV = os.path.join(ROOT, "library", "previews")


def load():
    return json.load(open(CATALOG, encoding="utf-8"))


def save(cat):
    json.dump(cat, open(CATALOG, "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)


def kit_names(module: str) -> tuple[set, set]:
    """Top-level public defs/classes/assignments of kit/<module>.py, and the keys of its CAST dict."""
    path = os.path.join(ROOT, *module.split(".")) + ".py"
    tree = ast.parse(open(path, encoding="utf-8").read())
    names, cast_keys = set(), set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                if isinstance(t, ast.Name):
                    names.add(t.id)
                    if isinstance(n.value, ast.Dict):
                        keys = {k.value for k in n.value.keys if isinstance(k, ast.Constant)}
                        if t.id == "CAST": cast_keys |= keys
                        names |= {f"{t.id}['{k}']" for k in keys}
    return names, cast_keys


def source_errors(item: dict) -> list[str]:
    errs, src = [], item.get("source", {})
    ref = src.get("kit")
    if ref:
        if ref.endswith(".py"):
            if not os.path.exists(os.path.join(ROOT, ref)): errs.append(f"missing file {ref}")
        else:
            mod, _, name = ref.partition(":")
            try:
                names, _ = kit_names(mod)
                if name not in names: errs.append(f"{mod} has no {name}")
            except FileNotFoundError:
                errs.append(f"no module {mod}")
    f = src.get("file")
    if f and not os.path.exists(os.path.join(ROOT, f)) and "voices_ref" not in f:
        errs.append(f"missing file {f}")
    if "sfx" in src:
        bank = json.load(open(os.path.join(ROOT, "assets", "sfx_bank.json"), encoding="utf-8"))["sounds"]
        if src["sfx"] not in bank: errs.append(f"sfx id {src['sfx']} not in sfx_bank.json")
    if "voices" in src:
        v = json.load(open(os.path.join(ROOT, "assets", "cast", "voices.json"), encoding="utf-8"))["characters"]
        if src["voices"] not in v: errs.append(f"voice {src['voices']} not in voices.json")
    return errs


def cmd_search(cat, a):
    q = (a.text or "").lower()
    n = 0
    for it in cat["items"]:
        if a.kind and it["kind"] != a.kind: continue
        if a.tag and a.tag not in it.get("tags", []): continue
        if a.status and it.get("status") != a.status: continue
        hay = " ".join([it["id"], it["name"], it.get("description", ""), " ".join(it.get("tags", []))]).lower()
        if q and not re.search(r"(?<![a-z0-9])" + re.escape(q), hay): continue   # word start: "night" != "knight"
        src = it["source"].get("kit") or it["source"].get("sfx") or it["source"].get("file") or it["source"].get("voices")
        print(f"{it['id']:40s} {it.get('status', ''):10s} {src}")
        n += 1
    print(f"[catalog] {n} match(es)")


def cmd_show(cat, a):
    it = next((i for i in cat["items"] if i["id"] == a.text), None)
    if not it: sys.exit(f"no item {a.text}")
    print(json.dumps(it, indent=1, ensure_ascii=False))


def cmd_check(cat, a):
    errors, ids = [], set()
    kinds = set(cat.get("kinds", []))
    for it in cat["items"]:
        if it["id"] in ids: errors.append(f"{it['id']}: duplicate id")
        ids.add(it["id"])
        if it["kind"] not in kinds: errors.append(f"{it['id']}: unknown kind {it['kind']}")
        if it.get("status") not in cat.get("statuses", {}): errors.append(f"{it['id']}: unknown status {it.get('status')}")
        for k in ("name", "description", "source", "licence"):
            if not it.get(k): errors.append(f"{it['id']}: missing {k}")
        errors += [f"{it['id']}: {e}" for e in source_errors(it)]
        img = (it.get("preview") or {}).get("image")
        if (it.get("preview") or {}).get("recipe") and not (img and os.path.exists(os.path.join(ROOT, img))):
            errors.append(f"{it['id']}: preview not rendered (tools/catalog_preview.py or catalog.py gallery)")
    for e in errors: print("[check]", e)
    print(f"[check] {len(cat['items'])} items, {len(errors)} problem(s)")
    sys.exit(1 if errors else 0)


def cmd_harvest(cat, a):
    """List reusable things that exist in kit/ or assets/ but have no catalog entry (the harvest step)."""
    refs = {it["source"].get("kit") for it in cat["items"]}
    sfx = {it["source"].get("sfx") for it in cat["items"]}
    files = {it["source"].get("file") for it in cat["items"]}
    voices = {it["source"].get("voices") for it in cat["items"]}
    skip = {"kit.qchar", "kit.rig", "kit.toon", "kit.captions"}   # low-level helpers, catalogued via their users
    refs |= set(cat.get("internal", []))                           # helpers reviewed and deliberately not catalogued
    out = []
    for fn in sorted(os.listdir(os.path.join(ROOT, "kit"))):
        if not fn.endswith(".py") or fn.startswith("_"): continue
        mod = "kit." + fn[:-3]
        if mod in skip: continue
        names, cast_keys = kit_names(mod)
        for n in sorted(names):
            if n.startswith("_") or "[" in n or n.isupper() and n not in ("STANCE", "STANCE_LOW", "CHARGE", "CHARGE_HIP",
                                                                            "CHARGE_OUT", "THRUST", "TIRED", "CHARGE_FAR"):
                continue
            if f"{mod}:{n}" not in refs: out.append(f"kit    {mod}:{n}")
        for k in sorted(cast_keys):
            if not any(it["source"].get("cast") == k for it in cat["items"]): out.append(f"cast   {k}")
    bank = json.load(open(os.path.join(ROOT, "assets", "sfx_bank.json"), encoding="utf-8"))["sounds"]
    out += [f"sfx    {s}" for s in bank if s not in sfx]
    mdir = os.path.join(ROOT, "assets", "library", "music")
    out += [f"music  assets/library/music/{f}" for f in sorted(os.listdir(mdir))
            if f.endswith(".mp3") and f"assets/library/music/{f}" not in files]
    v = json.load(open(os.path.join(ROOT, "assets", "cast", "voices.json"), encoding="utf-8"))["characters"]
    out += [f"voice  {c}" for c in v if c not in voices]
    qdir = os.path.join(ROOT, "assets", "library", "quaternius", "ultimate_animated_character")
    out += [f"rig    {f}" for f in sorted(os.listdir(qdir)) if f.endswith(".blend")
            and f"assets/library/quaternius/ultimate_animated_character/{f}" not in files]
    for line in out: print("[harvest]", line)
    print(f"[harvest] {len(out)} uncatalogued (helpers/internals can stay out; reusable components need an entry)")


def waveform(item) -> str | None:
    """Audio preview: a waveform PNG (ffmpeg showwavespic)."""
    src = item["source"].get("file")
    if not src or not os.path.exists(os.path.join(ROOT, src)): return None
    out = os.path.join(PREV, item["id"].replace("/", "__") + ".png")
    if not os.path.exists(out):
        dur = ["-t", "20"] if item["kind"] == "music" else []
        subprocess.run(["ffmpeg", "-v", "error", "-y", *dur, "-i", os.path.join(ROOT, src), "-filter_complex",
                        "aformat=channel_layouts=mono,showwavespic=s=360x90:colors=#4aa8ff", "-frames:v", "1", out], check=False)
    return os.path.relpath(out, ROOT).replace("\\", "/") if os.path.exists(out) else None


def cmd_gallery(cat, a):
    os.makedirs(PREV, exist_ok=True)
    for it in cat["items"]:
        p = it.get("preview") or {}
        if p.get("recipe") == "audio":
            img = waveform(it)
            if img: p["image"] = img
    save(cat)
    order = cat["kinds"]
    titles = {"character": "Characters", "character-part": "Character parts", "rig": "Base rigs (Quaternius, CC0)",
              "pose": "Poses", "motion": "Motions", "prop": "Props", "fx": "Effects", "set": "Sets / environments",
              "set-part": "Set parts", "camera": "Cameras", "sfx": "Sound effects", "music": "Music", "voice": "Voices"}
    by = {k: [i for i in cat["items"] if i["kind"] == k] for k in order}
    lines = ["# Component library", "",
             "Generated by `python tools/catalog.py gallery` from `library/catalog.json` — do not edit by hand.",
             "Search: `python tools/catalog.py search <text> [--kind K] [--tag T]`. Status: approved · draft · ~~deprecated~~.", "",
             "| kind | items |", "|---|---|"]
    lines += [f"| [{titles.get(k, k)}](#{titles.get(k, k).lower().replace(' ', '-').replace('/', '').replace('(', '').replace(')', '').replace(',', '')}) | {len(by[k])} |"
              for k in order if by[k]]
    for k in order:
        items = by[k]
        if not items: continue
        lines += ["", f"## {titles.get(k, k)}", ""]
        thumbs = [i for i in items if (i.get("preview") or {}).get("image") and i["kind"] not in ("sfx", "music")]
        if thumbs:   # image grid, 6 per row
            for r in range(0, len(thumbs), 6):
                row = thumbs[r:r + 6]
                lines.append("| " + " | ".join(f"<img src=\"{os.path.relpath(os.path.join(ROOT, i['preview']['image']), os.path.join(ROOT, 'library')).replace(os.sep, '/')}\" width=\"120\">" for i in row) + " |")
                lines.append("|" + "---|" * len(row))
                lines.append("| " + " | ".join(_label(i) for i in row) + " |")
                lines.append("")
        rest = [i for i in items if i not in thumbs]
        if rest:
            lines += ["| id | name | status | what | source | preview |", "|---|---|---|---|---|---|"]
            for i in rest:
                img = (i.get("preview") or {}).get("image")
                pv = f"<img src=\"{os.path.relpath(os.path.join(ROOT, img), os.path.join(ROOT, 'library')).replace(os.sep, '/')}\" width=\"180\">" if img else ""
                src = i["source"].get("kit") or i["source"].get("sfx") or i["source"].get("file") or i["source"].get("voices")
                name = f"~~{i['name']}~~" if i.get("status") == "deprecated" else i["name"]
                what = i.get("description", "").replace("|", "/")[:140]
                lines.append(f"| `{i['id']}` | {name} | {i.get('status')} | {what} | `{src}` | {pv} |")
    open(os.path.join(ROOT, "library", "CATALOG.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print(f"[gallery] library/CATALOG.md ({len(cat['items'])} items)")


def _label(i) -> str:
    name = f"~~{i['name']}~~" if i.get("status") == "deprecated" else i["name"]
    return f"**{name}**<br>`{i['id']}`<br>{i.get('status')}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["search", "show", "check", "harvest", "gallery"])
    ap.add_argument("text", nargs="?")
    ap.add_argument("--kind"); ap.add_argument("--tag"); ap.add_argument("--status")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    cat = load()
    {"search": cmd_search, "show": cmd_show, "check": cmd_check, "harvest": cmd_harvest, "gallery": cmd_gallery}[a.cmd](cat, a)


if __name__ == "__main__":
    main()
