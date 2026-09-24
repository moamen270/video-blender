"""Test for props and self-checkout kiosk (Task G1)."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isdir(os.path.join(ROOT, "studio")):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy
from mathutils import Vector

from kit import checkout, look as L, props
from studio import core as C


def main() -> None:
    # 1. Reset scene, setup environment
    C.reset_scene()
    L.store_night(target=(0.0, 0.0, 1.0))
    L.floor()

    # 2. Build checkout at the origin
    ck = checkout.build_checkout(loc=(0.0, 0.0, 0.0), heading=0.0)

    # 3. Milk on the scanner anchor
    milk_obj = props.milk("milk", loc=ck.anchors["scanner"])

    # 4. Batarang lying on the bagging plate
    batarang_obj = props.batarang("batarang", loc=ck.anchors["bagging"])

    # 5. Smoke puff at (1.5, 0.5, 0) frame 10
    puff_objs = props.smoke_puff("smoke", center=(1.5, 0.5, 0.0), frame=10)

    # 6. Assert every part exists
    expected_parts = [
        "ck_body",
        "ck_stripe",
        "ck_scanner",
        "ck_laser",
        "ck_post",
        "ck_monitor",
        "ck_bag_base",
        "ck_bag_plate",
        "ck_bag_poles",
        "ck_bag",
        "ck_lamp_pole",
    ]
    for p in expected_parts:
        assert p in ck.parts, f"Missing part '{p}' in ck.parts"
        assert ck.parts[p] is not None, f"Part '{p}' is None"

    expected_screens = ["scan", "error", "wait", "thanks"]
    for s in expected_screens:
        assert s in ck.screens, f"Missing screen state '{s}' in ck.screens"
        assert len(ck.screens[s]) == 2, f"Screen state '{s}' expected 2 objects (plane + text), got {len(ck.screens[s])}"

    expected_lamps = ["off", "red", "green"]
    for l in expected_lamps:
        assert l in ck.lamps, f"Missing lamp '{l}' in ck.lamps"
        assert ck.lamps[l] is not None, f"Lamp '{l}' is None"

    assert milk_obj is not None, "Milk object is None"
    assert batarang_obj is not None, "Batarang object is None"
    assert len(puff_objs) == 9, f"Smoke puff expected 9 objects, got {len(puff_objs)}"

    # 7. Assert anchors match the table (+-0.005)
    # scanner: (0, 0, 0.84)
    assert (ck.anchors["scanner"] - Vector((0.0, 0.0, 0.84))).length <= 0.005, (
        f"Scanner anchor {ck.anchors['scanner']} differs from (0, 0, 0.84)"
    )

    # bagging: (-0.72, 0, 0.81)
    assert (ck.anchors["bagging"] - Vector((-0.72, 0.0, 0.81))).length <= 0.005, (
        f"Bagging anchor {ck.anchors['bagging']} differs from (-0.72, 0, 0.81)"
    )

    # customer: (0, 0.62, 0)
    assert (ck.anchors["customer"] - Vector((0.0, 0.62, 0.0))).length <= 0.005, (
        f"Customer anchor {ck.anchors['customer']} differs from (0, 0.62, 0)"
    )

    # lamp: (0.20, -0.17, 1.66)
    assert (ck.anchors["lamp"] - Vector((0.20, -0.17, 1.66))).length <= 0.005, (
        f"Lamp anchor {ck.anchors['lamp']} differs from (0.20, -0.17, 1.66)"
    )

    # screen_L: kiosk x = +0.23
    assert abs(ck.anchors["screen_L"].x - 0.23) <= 0.005, (
        f"screen_L anchor x {ck.anchors['screen_L'].x} differs from 0.23"
    )

    # screen_R: kiosk x = -0.23
    assert abs(ck.anchors["screen_R"].x - (-0.23)) <= 0.005, (
        f"screen_R anchor x {ck.anchors['screen_R'].x} differs from -0.23"
    )

    # screen: screen centre
    assert abs(ck.anchors["screen"].x) <= 0.005, (
        f"screen anchor x {ck.anchors['screen'].x} differs from 0.0"
    )
    screen_mid = (ck.anchors["screen_L"] + ck.anchors["screen_R"]) / 2.0
    assert (ck.anchors["screen"] - screen_mid).length <= 0.005, (
        f"screen anchor {ck.anchors['screen']} differs from screen edge midpoint {screen_mid}"
    )

    # 8. Assert screen states (frame 1 initially scan, frame 20 error)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    for o in ck.screens["scan"]:
        assert o.hide_render is False, f"Expected {o.name} to be render-visible at frame 1"
    for s in ["error", "wait", "thanks"]:
        for o in ck.screens[s]:
            assert o.hide_render is True, f"Expected {o.name} to be hidden at frame 1"

    checkout.screen_state(ck, 20, "error")
    bpy.context.scene.frame_set(20)
    bpy.context.view_layer.update()
    for o in ck.screens["error"]:
        assert o.hide_render is False, f"Expected {o.name} to be render-visible at frame 20"
    for s in ["scan", "wait", "thanks"]:
        for o in ck.screens[s]:
            assert o.hide_render is True, f"Expected {o.name} to be hidden at frame 20"

    # 9. Render stills
    out_dir = os.path.join(ROOT, "output", "tests", "G1")
    os.makedirs(out_dir, exist_ok=True)

    cam = C.camera("cam_checkout", loc=(1.2, 2.2, 1.4), look_at=(-0.2, 0.0, 0.95), lens=40.0)
    bpy.context.scene.camera = cam

    # Frame 1 still
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    still_1 = os.path.join(out_dir, "frame_0001.png")
    C.render_settings(width=540, height=960, quality="final", video=False, frame_end=1, filepath=still_1)
    bpy.context.scene.render.filepath = still_1
    bpy.ops.render.render(write_still=True)
    assert os.path.isfile(still_1) and os.path.getsize(still_1) > 0, f"Missing still {still_1}"

    # Frame 20 still
    bpy.context.scene.frame_set(20)
    bpy.context.view_layer.update()
    still_20 = os.path.join(out_dir, "frame_0020.png")
    C.render_settings(width=540, height=960, quality="final", video=False, frame_end=20, filepath=still_20)
    bpy.context.scene.render.filepath = still_20
    bpy.ops.render.render(write_still=True)
    assert os.path.isfile(still_20) and os.path.getsize(still_20) > 0, f"Missing still {still_20}"

    # Frame 14 still (main view)
    bpy.context.scene.frame_set(14)
    bpy.context.view_layer.update()
    still_14 = os.path.join(out_dir, "frame_0014.png")
    C.render_settings(width=540, height=960, quality="final", video=False, frame_end=14, filepath=still_14)
    bpy.context.scene.render.filepath = still_14
    bpy.ops.render.render(write_still=True)
    assert os.path.isfile(still_14) and os.path.getsize(still_14) > 0, f"Missing still {still_14}"

    # Frame 14 still (focused on puff)
    cam_puff = C.camera("cam_puff", loc=(1.5, 3.2, 1.2), look_at=(1.5, 0.5, 0.6), lens=40.0)
    bpy.context.scene.camera = cam_puff
    still_puff = os.path.join(out_dir, "puff_0014.png")
    C.render_settings(width=540, height=960, quality="final", video=False, frame_end=14, filepath=still_puff)
    bpy.context.scene.render.filepath = still_puff
    bpy.ops.render.render(write_still=True)
    assert os.path.isfile(still_puff) and os.path.getsize(still_puff) > 0, f"Missing still {still_puff}"

    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
