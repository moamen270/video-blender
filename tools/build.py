"""Headless build + render.

    blender -b --python tools/build.py -- --project cupid --out output/v3 --quality preview

Writes into --out:
    scene.blend        the built scene (open it in Blender to tweak by hand)
    video.mp4          silent render
"""
import argparse
import os
import runpy
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import bpy  # noqa: E402

from studio import core as C  # noqa: E402


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--quality", default="preview", choices=["draft", "preview", "final"])
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--frames", default=None, help="optional 'start-end' override for partial renders")
    args = ap.parse_args(argv)

    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    ns = runpy.run_path(os.path.join(ROOT, "projects", args.project, "script.py"), run_name="build")
    ns["build"]()

    scene = bpy.context.scene
    C.render_settings(frame_end=scene.frame_end, quality=args.quality,
                      filepath=os.path.join(out, "video.mp4"))
    if args.frames:
        a, b = (int(x) for x in args.frames.split("-"))
        scene.frame_start, scene.frame_end = a, b
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "scene.blend"))
    print(f"[build] saved {out}/scene.blend  ({scene.frame_end} frames @ {args.quality})", flush=True)
    if args.no_render:
        return
    t0 = time.time()
    bpy.ops.render.render(animation=True)
    print(f"[build] rendered in {time.time() - t0:.0f}s -> {out}/video.mp4", flush=True)


main()
