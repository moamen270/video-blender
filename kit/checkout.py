"""Self-checkout kiosk prop module (Task G1)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import bmesh
import bpy
from mathutils import Vector

from kit import look as L
from kit import toon
from studio import core as C


@dataclass
class Checkout:
    root: bpy.types.Object
    parts: dict[str, bpy.types.Object]
    screens: dict[str, list[bpy.types.Object]]
    lamps: dict[str, bpy.types.Object]
    anchors: dict[str, Vector]


def _cylinder_between(
    name: str,
    p1: Sequence[float],
    p2: Sequence[float],
    r: float,
    mat: bpy.types.Material,
    parent: bpy.types.Object | None = None,
    col: bpy.types.Collection | None = None,
) -> bpy.types.Object:
    """Create a cylinder between two points oriented along the direction vector."""
    p1_v = Vector(p1)
    p2_v = Vector(p2)
    d = p2_v - p1_v
    center = (p1_v + p2_v) / 2.0
    cyl = C.cylinder(name, r=r, depth=d.length, parent=parent, loc=center, mat=mat, col=col)
    cyl.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return cyl


def build_checkout(
    loc: Sequence[float] = (0.0, 0.0, 0.0),
    heading: float = 0.0,
    col: bpy.types.Collection | None = None,
) -> Checkout:
    """Build the self-checkout kiosk with screen states, status lamp, and anchors."""
    root = C.empty("checkout_root", loc=loc, rot=(0.0, 0.0, heading), col=col)

    mat_body = L.toon2("ck_body", "#3a3f4a", rim=0.0)
    mat_stripe = L.toon2("ck_stripe", "#c8102e", rim=0.0)
    mat_scanner = L.toon2("ck_scanner", "#10131a", rim=0.0)
    mat_laser = L.toon2("ck_laser", "#ff2a2a", emission=3.0)
    mat_post = L.toon2("ck_post", "#2a2e36", rim=0.0)
    mat_bag_plate = L.toon2("ck_bag_plate", "#c9ced6", rim=0.0)
    mat_bag_poles = L.toon2("ck_bag_poles", "#8a8f99", rim=0.0)
    mat_bag = L.toon2("ck_bag", "#eeeeee", rim=0.0)

    parts: dict[str, bpy.types.Object] = {}

    # 1. Boxes
    parts["ck_body"] = C.cube(
        "ck_body",
        parent=root,
        loc=(0.0, 0.0, 0.40),
        scale=(0.70, 0.55, 0.80),
        mat=mat_body,
        col=col,
    )
    parts["ck_stripe"] = C.cube(
        "ck_stripe",
        parent=root,
        loc=(0.0, 0.28, 0.62),
        scale=(0.72, 0.01, 0.10),
        mat=mat_stripe,
        col=col,
    )
    parts["ck_scanner"] = C.cube(
        "ck_scanner",
        parent=root,
        loc=(0.0, 0.0, 0.82),
        scale=(0.60, 0.45, 0.04),
        mat=mat_scanner,
        col=col,
    )
    parts["ck_laser"] = C.cube(
        "ck_laser",
        parent=root,
        loc=(0.0, 0.0, 0.842),
        scale=(0.40, 0.012, 0.004),
        mat=mat_laser,
        col=col,
    )
    parts["ck_monitor"] = C.cube(
        "ck_monitor",
        parent=root,
        loc=(0.0, -0.15, 1.30),
        rot=(-15.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0),
        mat=mat_post,
        col=col,
    )
    for v in parts["ck_monitor"].data.vertices:
        v.co.x *= 0.46
        v.co.y *= 0.05
        v.co.z *= 0.34
    parts["ck_monitor"].data.update()
    parts["ck_bag_base"] = C.cube(
        "ck_bag_base",
        parent=root,
        loc=(-0.72, 0.0, 0.39),
        scale=(0.60, 0.55, 0.78),
        mat=mat_body,
        col=col,
    )
    parts["ck_bag_plate"] = C.cube(
        "ck_bag_plate",
        parent=root,
        loc=(-0.72, 0.0, 0.795),
        scale=(0.58, 0.50, 0.03),
        mat=mat_bag_plate,
        col=col,
    )
    parts["ck_bag"] = C.cube(
        "ck_bag",
        parent=root,
        loc=(-0.72, -0.18, 1.08),
        scale=(0.34, 0.20, 0.30),
        mat=mat_bag,
        col=col,
    )

    # 2. Cylinders
    parts["ck_post"] = _cylinder_between(
        "ck_post",
        (0.0, -0.18, 0.84),
        (0.0, -0.18, 1.16),
        0.03,
        mat=mat_post,
        parent=root,
        col=col,
    )
    parts["ck_lamp_pole"] = _cylinder_between(
        "ck_lamp_pole",
        (0.20, -0.17, 1.47),
        (0.20, -0.17, 1.62),
        0.012,
        mat=mat_post,
        parent=root,
        col=col,
    )

    # 3. Bag poles (two vertical poles + one horizontal bar merged into one object)
    temp_pole_l = _cylinder_between(
        "temp_pole_l",
        (-0.95, -0.22, 0.81),
        (-0.95, -0.22, 1.25),
        0.012,
        mat=mat_bag_poles,
        col=col,
    )
    temp_pole_r = _cylinder_between(
        "temp_pole_r",
        (-0.49, -0.22, 0.81),
        (-0.49, -0.22, 1.25),
        0.012,
        mat=mat_bag_poles,
        col=col,
    )
    temp_pole_bar = _cylinder_between(
        "temp_pole_bar",
        (-0.95, -0.22, 1.25),
        (-0.49, -0.22, 1.25),
        0.012,
        mat=mat_bag_poles,
        col=col,
    )

    bm_poles = bmesh.new()
    for c in (temp_pole_l, temp_pole_r, temp_pole_bar):
        bm_temp = bmesh.new()
        bm_temp.from_mesh(c.data)
        bm_temp.transform(c.matrix_basis)
        v_start = len(bm_poles.verts)
        for v in bm_temp.verts:
            bm_poles.verts.new(v.co)
        bm_poles.verts.ensure_lookup_table()
        for f in bm_temp.faces:
            bm_poles.faces.new([bm_poles.verts[v.index + v_start] for v in f.verts])
        bm_temp.free()

    mesh_poles = bpy.data.meshes.new("ck_bag_poles")
    bm_poles.to_mesh(mesh_poles)
    bm_poles.free()
    mesh_poles.materials.append(mat_bag_poles)
    for p in mesh_poles.polygons:
        p.use_smooth = True

    obj_poles = bpy.data.objects.new("ck_bag_poles", mesh_poles)
    C.link(obj_poles, col)
    obj_poles.parent = root
    parts["ck_bag_poles"] = obj_poles

    for c in (temp_pole_l, temp_pole_r, temp_pole_bar):
        m_data = c.data
        bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.meshes.remove(m_data)

    # 4. Screens (parented to ck_monitor, in monitor local space)
    ck_monitor = parts["ck_monitor"]
    screens: dict[str, list[bpy.types.Object]] = {}

    screen_specs = [
        ("scan", "#1e5bd8", "PLEASE\nSCAN ITEM"),
        ("error", "#d0202a", "UNEXPECTED ITEM\nIN BAGGING AREA"),
        ("wait", "#e0a020", "PLEASE WAIT\nASSISTANT COMING"),
        ("thanks", "#1f9d55", "THANK YOU FOR\nSHOPPING AT\nGOTHAM MART"),
    ]
    mat_screen_text = L.toon2("ck_screen_text", "#ffffff", emission=2.0)

    for state, bg_hex, text_body in screen_specs:
        mat_bg = L.toon2(f"ck_screen_{state}", bg_hex, emission=1.2)

        # 0.42 x 0.30 plane with normal pointing +Y (monitor front)
        bm_plane = bmesh.new()
        v1 = bm_plane.verts.new(Vector((-0.21, 0.0, -0.15)))
        v2 = bm_plane.verts.new(Vector((-0.21, 0.0, 0.15)))
        v3 = bm_plane.verts.new(Vector((0.21, 0.0, 0.15)))
        v4 = bm_plane.verts.new(Vector((0.21, 0.0, -0.15)))
        bm_plane.faces.new([v1, v2, v3, v4])
        mesh_plane = bpy.data.meshes.new(f"ck_screen_{state}")
        bm_plane.to_mesh(mesh_plane)
        bm_plane.free()
        mesh_plane.materials.append(mat_bg)

        plane_obj = bpy.data.objects.new(f"ck_screen_{state}", mesh_plane)
        plane_obj.location = (0.0, 0.027, 0.0)
        plane_obj.parent = ck_monitor
        C.link(plane_obj, col)

        # White emission text 0.002 in front of the screen plane (y = 0.029)
        txt_obj = C.text(
            f"ck_text_{state}",
            body=text_body,
            size=0.1,
            extrude=0.0,
            parent=ck_monitor,
            loc=(0.0, 0.029, 0.0),
            rot=(90.0, 0.0, 180.0),
            mat=mat_screen_text,
            col=col,
            align="CENTER",
        )
        bpy.context.view_layer.update()

        # Scale uniformly so text block is <= 0.36 wide and <= 0.22 tall
        xs = [b[0] for b in txt_obj.bound_box]
        ys = [b[1] for b in txt_obj.bound_box]
        w = max(xs) - min(xs)
        h = max(ys) - min(ys)
        if w > 0.0 and h > 0.0:
            s = min(0.36 / w, 0.22 / h)
            txt_obj.scale = (s, s, s)

        screens[state] = [plane_obj, txt_obj]

    # 5. Status Lamps
    mat_lamp_off = L.toon2("ck_lamp_off", "#40444c", rim=0.0)
    mat_lamp_red = L.toon2("ck_lamp_red", "#ff2a2a", emission=3.0)
    mat_lamp_green = L.toon2("ck_lamp_green", "#2aff6a", emission=3.0)

    lamp_off = C.sphere("ck_lamp_off", r=0.05, parent=root, loc=(0.20, -0.17, 1.66), mat=mat_lamp_off, col=col, smooth=True)
    lamp_red = C.sphere("ck_lamp_red", r=0.05, parent=root, loc=(0.20, -0.17, 1.66), mat=mat_lamp_red, col=col, smooth=True)
    lamp_green = C.sphere("ck_lamp_green", r=0.05, parent=root, loc=(0.20, -0.17, 1.66), mat=mat_lamp_green, col=col, smooth=True)

    lamps = {"off": lamp_off, "red": lamp_red, "green": lamp_green}

    # 6. Outlines on body, stripe, bag base, plate, monitor, bag (thickness 0.006)
    bpy.context.view_layer.update()
    for p_name in ["ck_body", "ck_stripe", "ck_bag_base", "ck_bag_plate", "ck_monitor", "ck_bag"]:
        p_obj = parts[p_name]
        scale_x = p_obj.matrix_world.to_scale()[0]
        thickness = 0.006 / scale_x if scale_x != 0 else 0.006
        toon.add_outline(p_obj, thickness=thickness)

    # 7. World Anchors
    bpy.context.view_layer.update()
    anchors = {
        "scanner": root.matrix_world @ Vector((0.0, 0.0, 0.84)),
        "bagging": root.matrix_world @ Vector((-0.72, 0.0, 0.81)),
        "screen": ck_monitor.matrix_world @ Vector((0.0, 0.027, 0.0)),
        "screen_L": ck_monitor.matrix_world @ Vector((0.23, 0.027, 0.0)),
        "screen_R": ck_monitor.matrix_world @ Vector((-0.23, 0.027, 0.0)),
        "customer": root.matrix_world @ Vector((0.0, 0.62, 0.0)),
        "lamp": root.matrix_world @ Vector((0.20, -0.17, 1.66)),
    }

    ck = Checkout(
        root=root,
        parts=parts,
        screens=screens,
        lamps=lamps,
        anchors=anchors,
    )
    screen_state(ck, 1, "scan")
    lamp(ck, 1, "off")
    return ck


def screen_state(ck: Checkout, frame: int, state: str) -> None:
    """Key visibility of screen states at frame."""
    for s_name, objs in ck.screens.items():
        is_active = (s_name == state)
        for obj in objs:
            C.visible(obj, frame, is_active)
            C.set_interp_all(obj, "CONSTANT", "hide_render")
            C.set_interp_all(obj, "CONSTANT", "hide_viewport")


def lamp(ck: Checkout, frame: int, state: str) -> None:
    """Key visibility of status lamp states ('off', 'red', 'green') at frame."""
    for l_name, obj in ck.lamps.items():
        C.visible(obj, frame, l_name == state)
        C.set_interp_all(obj, "CONSTANT", "hide_render")
        C.set_interp_all(obj, "CONSTANT", "hide_viewport")
