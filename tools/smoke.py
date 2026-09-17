"""blender -b --python tools/smoke.py — build one of everything and report errors early."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bpy
from studio import core as C, characters as CH, props as P

C.reset_scene()
col = C.collection("Smoke")
pip = CH.build_character("Pip", loc=(-1, 0, 0), face_deg=90, leg=0.45, body_h=0.55, body_r=0.28, head_r=0.3, arm=0.4, col=col)
bru = CH.build_character("Bruno", loc=(1, 0, 0), face_deg=-90, leg=0.75, body_h=0.95, body_r=0.45, head_r=0.38, arm=0.55,
                         colors={"body": "#3b4a6b", "limb": "#5b6b8c"}, col=col)
b = P.bow("Pip.bow", parent=pip["hand_l"], col=col)
P.draw_bow(b, 1, 0.0); P.draw_bow(b, 20, 1.0)
a = P.arrow("Arrow1", col=col)
P.shield("Bruno.shield", parent=bru["hand_l"], col=col)
P.helmet("Bruno.helmet", parent=bru["head"], loc=(0, 0, 0.12), col=col)
w = P.wings("Pip.wings", parent=bru["body"], col=col); P.flap_wings(w, 1, 40)
P.halo("Pip.halo", parent=pip["head"], loc=(0, 0, 0.5), col=col)
P.quiver("Pip.quiver", parent=pip["body"], loc=(0.1, 0.3, 0.1), rot=(20, 0, 0), col=col)
P.heart("H1", loc=(0, 0, 3), col=col); P.star("S1", loc=(0, 0, 3.5), col=col)
P.ground(col=col); P.hill("Hill", loc=(0, 20, -3), col=col); P.tree("Tree", loc=(4, 5, 0), col=col)
P.rock("Rock", loc=(2, 2, 0), col=col); P.cloud("Cloud", loc=(0, 20, 10), col=col); P.sign("Sign", "HELLO", loc=(0, 5, 2), col=col)
CH.rest_pose(pip, 1); CH.walk(pip, 1, 60, (-4, 0), (-1, 0)); CH.bounce(bru, 1, 40); CH.squash(bru, 50)
CH.eyes(bru, 1, scale=1.5, look=(1, 0)); CH.mouth(bru, 1, shape="o"); CH.head_turn(bru, 1, yaw=20)
C.visible(a, 1, False); C.visible(a, 10, True)
cam = C.camera("Cam", (0, -10, 2), (0, 0, 1)); C.cut(1, cam)
C.sun(); C.sky((0.55, 0.75, 0.95))
C.render_settings(frame_end=60, quality="draft", filepath="F:/PoCs/blender-video/output/smoke_")
print("fcurves on hips:", len(list(C.fcurves(bru["hips"]))))
print("world_pos hand_l @30:", tuple(round(v, 2) for v in C.world_pos(pip["hand_l"], 30)))
print("engine:", bpy.context.scene.render.engine, "view:", bpy.context.scene.view_settings.view_transform)
print("objects:", len(bpy.data.objects))
print("SMOKE OK")
