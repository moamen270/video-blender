"""Helpers for driving the *live* Blender session over MCP.

Usage from execute_blender_code:
    exec(open('F:/PoCs/blender-video/tools/live.py').read())
    load('tools/smoke.py')          # or 'projects/cupid/script.py'
    look(frame=30)                  # camera view + material shading, jump to frame
"""
import importlib
import os
import runpy
import sys

ROOT = "F:/PoCs/blender-video"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def load(rel_path: str, **argv):
    """Re-import the studio package (so edits are picked up) and run a build script."""
    for name in list(sys.modules):
        if name == "studio" or name.startswith("studio."):
            del sys.modules[name]
    import studio  # noqa: F401
    return runpy.run_path(os.path.join(ROOT, rel_path), run_name="__main__")


def look(frame: int | None = None, shading: str = "MATERIAL", camera: bool = True):
    import bpy
    if frame is not None:
        bpy.context.scene.frame_set(frame)
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            space = area.spaces.active
            space.shading.type = shading
            space.overlay.show_overlays = False
            if camera:
                space.region_3d.view_perspective = "PERSP"
                space.region_3d.view_perspective = "CAMERA"
            area.tag_redraw()
    return f"frame {bpy.context.scene.frame_current}"


def contact(frames, out_dir: str, pct: int = 25):
    """Render the given frames (through the marker-bound camera) to out_dir/f_<n>.png."""
    import bpy
    scene = bpy.context.scene
    r = scene.render
    keep = (r.resolution_percentage, r.filepath, r.image_settings.file_format,
            getattr(r.image_settings, "media_type", None), scene.eevee.taa_render_samples)
    os.makedirs(out_dir, exist_ok=True)
    if hasattr(r.image_settings, "media_type"):
        r.image_settings.media_type = "IMAGE"
    r.image_settings.file_format = "PNG"
    r.resolution_percentage = pct
    scene.eevee.taa_render_samples = 8
    for f in frames:
        scene.frame_set(f)
        r.filepath = os.path.join(out_dir, f"f_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
    r.resolution_percentage, r.filepath, fmt, media, scene.eevee.taa_render_samples = keep
    if media is not None:
        r.image_settings.media_type = media
    r.image_settings.file_format = fmt
    return [f"f_{f:04d}.png" for f in frames]
