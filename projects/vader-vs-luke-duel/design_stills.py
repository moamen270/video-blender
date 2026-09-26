"""G3 look stills: the real Vader + Luke in the corridor, blades crossed, the pull-cord lamp, in the 3 moods.

    F:/blender/blender.exe -b --python projects/vader-vs-luke-duel/design_stills.py
-> projects/vader-vs-luke-duel/design/{lit,dark,lamp}.jpg (+ design/look.jpg via ffmpeg hstack)
"""
import math, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

import bpy
from mathutils import Vector

from kit import fight as FT, post, starwars as SW
from studio import core as C

VADER_AT, LUKE_AT = Vector((-0.72, 0.9, 0)), Vector((0.72, 0.9, 0))
OUT = os.path.join(HERE, "design")


def face(qc, at, target):
    d = target - at
    qc.root.location = at
    qc.root.rotation_euler = (0, 0, math.radians(math.degrees(math.atan2(d.y, d.x)) - 90))


def saber(name, colour, qc, direction):
    s = SW.Lightsaber(name, colour)
    bpy.context.view_layer.update()
    p = qc.arm.matrix_world @ qc.arm.pose.bones["Fist.R"].tail
    s.root.location = p
    s.root.rotation_euler = Vector(direction).normalized().to_track_quat("Z", "Y").to_euler()
    return s


def main():
    os.makedirs(OUT, exist_ok=True)
    for mood in ("lit", "dark", "lamp"):
        C.reset_scene()
        lights = SW.death_star_corridor()
        lamp = SW.PullLamp(loc=(0.0, 0.9, 3.3))
        vader, luke = SW.build_vader(), SW.build_luke()
        face(vader, VADER_AT, LUKE_AT); face(luke, LUKE_AT, VADER_AT)
        bpy.context.view_layer.update()
        for q in (vader, luke):
            FT.prepare(q)
            FT.key_pose(q, 1, FT.STANCE)
        bpy.context.scene.frame_set(1)
        if mood == "lit":
            saber("vsab", "#ff2a2a", vader, (0.75, -0.15, 0.65))
            saber("lsab", "#39ff5a", luke, (-0.75, -0.15, 0.65))
        SW.key_mood(lights, 1, mood)
        lamp.key_on(1, mood == "lamp")
        cam = C.camera("cam", (0.0, -2.6, 1.5), (0.0, 0.9, 1.3), lens=28)
        sc = bpy.context.scene
        sc.camera = cam
        post.setup(threshold=0.9, strength=0.6, size=0.4)
        path = os.path.join(OUT, f"{mood}.jpg")
        C.render_settings(width=540, height=960, quality="final", video=False, frame_end=1, filepath=path)
        sc.render.resolution_percentage = 100
        sc.render.image_settings.file_format = "JPEG"
        sc.frame_set(1)
        bpy.ops.render.render(write_still=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/lit.jpg", "-i", f"{OUT}/dark.jpg", "-i", f"{OUT}/lamp.jpg",
                    "-filter_complex", "hstack=3", f"{OUT}/look.jpg"], check=True)


main()
