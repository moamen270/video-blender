"""Low-level Blender helpers: scene reset, materials, primitives, keyframes, cameras, render.

Everything here is plain `bpy` so it runs identically in a headless `blender -b` build
and inside a live Blender session driven over MCP. No hard-coded node names or enum ids.
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence

import bpy
from mathutils import Matrix, Vector

FPS = 24

Vec3 = Sequence[float]


# --------------------------------------------------------------------------- scene


def reset_scene() -> bpy.types.Scene:
    """Remove every object/datablock so a build is reproducible from an empty state."""
    scene = bpy.context.scene
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.lights,
                 bpy.data.cameras, bpy.data.actions, bpy.data.fonts, bpy.data.images):
        for block in list(coll):
            if block.users == 0 or coll is bpy.data.actions:
                try:
                    coll.remove(block)
                except Exception:
                    pass
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    scene.timeline_markers.clear()
    scene.frame_start = 1
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    return scene


def collection(name: str, parent: bpy.types.Collection | None = None) -> bpy.types.Collection:
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def link(obj: bpy.types.Object, col: bpy.types.Collection | None) -> bpy.types.Object:
    target = col or bpy.context.scene.collection
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    target.objects.link(obj)
    return obj


# --------------------------------------------------------------------------- materials


def material(name: str, color: Vec3, *, rough: float = 0.55, metal: float = 0.0,
             emit: float = 0.0, emit_color: Vec3 | None = None) -> bpy.types.Material:
    """Flat Principled material. Looked up by node *type* so it works on localized UIs."""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*(emit_color or color), 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = (*color, 1.0)
    return m


def hex_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    # sRGB -> linear so what we type is what we see
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b))


# --------------------------------------------------------------------------- objects


def empty(name: str, *, parent: bpy.types.Object | None = None, loc: Vec3 = (0, 0, 0),
          rot: Vec3 = (0, 0, 0), col: bpy.types.Collection | None = None,
          size: float = 0.15) -> bpy.types.Object:
    o = bpy.data.objects.new(name, None)
    o.empty_display_type = "PLAIN_AXES"
    o.empty_display_size = size
    link(o, col)
    _place(o, parent, loc, rot, (1, 1, 1))
    return o


def _finish_primitive(name: str, *, parent, loc, rot, scale, mat, col, smooth) -> bpy.types.Object:
    o = bpy.context.active_object
    o.name = name
    o.data.name = name
    if mat is not None:
        o.data.materials.append(mat)
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = True
    link(o, col)
    _place(o, parent, loc, rot, scale)
    return o


def _place(o, parent, loc, rot, scale):
    # Assigning .parent directly keeps matrix_parent_inverse = identity, so
    # loc/rot/scale below are expressed in the parent's local space (what we want for rigs).
    o.parent = parent
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    o.scale = scale


def sphere(name, *, r=0.5, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1),
           mat=None, col=None, segments=24, rings=16, smooth=True):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=segments, ring_count=rings)
    return _finish_primitive(name, parent=parent, loc=loc, rot=rot, scale=scale, mat=mat, col=col, smooth=smooth)


def icosphere(name, *, r=0.5, subdiv=1, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1),
              mat=None, col=None, smooth=False):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=r, subdivisions=subdiv)
    return _finish_primitive(name, parent=parent, loc=loc, rot=rot, scale=scale, mat=mat, col=col, smooth=smooth)


def cylinder(name, *, r=0.5, depth=1.0, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1),
             mat=None, col=None, verts=24, smooth=True, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts)
    o = _finish_primitive(name, parent=parent, loc=loc, rot=rot, scale=scale, mat=mat, col=col, smooth=smooth)
    if bevel:
        add_bevel(o, bevel)
    return o


def cone(name, *, r1=0.5, r2=0.0, depth=1.0, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1),
         mat=None, col=None, verts=24, smooth=True):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth, vertices=verts)
    return _finish_primitive(name, parent=parent, loc=loc, rot=rot, scale=scale, mat=mat, col=col, smooth=smooth)


def cube(name, *, size=1.0, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1),
         mat=None, col=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=size)
    o = _finish_primitive(name, parent=parent, loc=loc, rot=rot, scale=scale, mat=mat, col=col, smooth=False)
    if bevel:
        add_bevel(o, bevel)
    return o


def plane(name, *, size=1.0, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), mat=None, col=None):
    bpy.ops.mesh.primitive_plane_add(size=size)
    return _finish_primitive(name, parent=parent, loc=loc, rot=rot, scale=scale, mat=mat, col=col, smooth=False)


def torus(name, *, major=1.0, minor=0.25, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1),
          mat=None, col=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=32, minor_segments=12)
    return _finish_primitive(name, parent=parent, loc=loc, rot=rot, scale=scale, mat=mat, col=col, smooth=True)


def add_bevel(o: bpy.types.Object, width: float, segments: int = 4) -> None:
    m = o.modifiers.new("Bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    for p in o.data.polygons:
        p.use_smooth = True


def curve_arc(name: str, points: list[Vec3], *, bevel: float = 0.03, parent=None, loc=(0, 0, 0),
              rot=(0, 0, 0), mat=None, col=None, bezier: bool = True) -> bpy.types.Object:
    """A tube along a smooth (bezier) or straight (poly) path — used for bows and strings."""
    c = bpy.data.curves.new(name, "CURVE")
    c.dimensions = "3D"
    c.bevel_depth = bevel
    c.bevel_resolution = 4
    c.use_fill_caps = True
    if bezier:
        sp = c.splines.new("BEZIER")
        sp.bezier_points.add(len(points) - 1)
        for bp, p in zip(sp.bezier_points, points):
            bp.co = p
            bp.handle_left_type = bp.handle_right_type = "AUTO"
    else:
        sp = c.splines.new("POLY")
        sp.points.add(len(points) - 1)
        for pt, p in zip(sp.points, points):
            pt.co = (*p, 1.0)
    o = bpy.data.objects.new(name, c)
    if mat is not None:
        c.materials.append(mat)
    link(o, col)
    _place(o, parent, loc, rot, (1, 1, 1))
    return o


def text(name: str, body: str, *, size=1.0, extrude=0.05, parent=None, loc=(0, 0, 0), rot=(0, 0, 0),
         mat=None, col=None, align="CENTER") -> bpy.types.Object:
    c = bpy.data.curves.new(name, "FONT")
    c.body = body
    c.size = size
    c.extrude = extrude
    c.align_x = align
    c.align_y = "CENTER"
    o = bpy.data.objects.new(name, c)
    if mat is not None:
        c.materials.append(mat)
    link(o, col)
    _place(o, parent, loc, rot, (1, 1, 1))
    return o


# --------------------------------------------------------------------------- animation


def rad(rot: Vec3) -> list[float]:
    return [math.radians(a) for a in rot]


def key(obj: bpy.types.Object, frame: int, *, loc: Vec3 | None = None, rot: Vec3 | None = None,
        scale: Vec3 | None = None, interp: str | None = None) -> None:
    """Insert location/rotation(deg)/scale keys at `frame`. `interp` overrides the
    interpolation of just these keys (e.g. 'LINEAR', 'CONSTANT', 'BEZIER')."""
    if loc is not None:
        obj.location = loc
        obj.keyframe_insert("location", frame=frame)
    if rot is not None:
        obj.rotation_euler = rad(rot)
        obj.keyframe_insert("rotation_euler", frame=frame)
    if scale is not None:
        obj.scale = scale
        obj.keyframe_insert("scale", frame=frame)
    if interp:
        set_interp_at(obj, frame, interp)


def fcurves(obj: bpy.types.Object) -> Iterable[bpy.types.FCurve]:
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    # Blender >= 4.4 slotted actions; fall back to the legacy accessor.
    try:
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    yield from bag.fcurves
        return
    except AttributeError:
        pass
    yield from act.fcurves


def set_interp_at(obj, frame: int, interp: str) -> None:
    for fc in fcurves(obj):
        for kp in fc.keyframe_points:
            if abs(kp.co.x - frame) < 0.5:
                kp.interpolation = interp


def set_interp_all(obj, interp: str, data_path: str | None = None) -> None:
    for fc in fcurves(obj):
        if data_path and fc.data_path != data_path:
            continue
        for kp in fc.keyframe_points:
            kp.interpolation = interp


def set_extrapolation(obj, mode: str = "LINEAR") -> None:
    for fc in fcurves(obj):
        fc.extrapolation = mode


def add_cycles(obj, data_path: str | None = None) -> None:
    """Loop the keys (walk cycles, wing flaps) with a Cycles modifier."""
    for fc in fcurves(obj):
        if data_path and fc.data_path != data_path:
            continue
        if not any(m.type == "CYCLES" for m in fc.modifiers):
            fc.modifiers.new("CYCLES")


def visible(obj: bpy.types.Object, frame: int, on: bool) -> None:
    """Keyframe render+viewport visibility of `obj` and all its descendants
    (Blender does not propagate hide flags down a parent chain)."""
    for o in [obj, *obj.children_recursive]:
        o.hide_render = not on
        o.hide_viewport = not on
        o.keyframe_insert("hide_render", frame=frame)
        o.keyframe_insert("hide_viewport", frame=frame)


def world_pos(obj: bpy.types.Object, frame: int | None = None) -> Vector:
    """Evaluated world-space position of an (animated, parented) object at `frame`."""
    if frame is not None:
        bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    return obj.matrix_world.translation.copy()


def aim_rot(direction: Vector, up: str = "Z", track: str = "Y") -> list[float]:
    """Euler (radians) that points an object's local `track` axis along `direction`."""
    return list(direction.normalized().to_track_quat(track, up).to_euler())


def unparent_keep(obj: bpy.types.Object) -> None:
    mw = obj.matrix_world.copy()
    obj.parent = None
    obj.matrix_world = mw


# --------------------------------------------------------------------------- camera / cuts


def camera(name: str, loc: Vec3, look_at: Vec3, *, lens: float = 40.0, col=None) -> bpy.types.Object:
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = lens
    cam_data.sensor_fit = "VERTICAL"
    cam_data.sensor_height = 36.0
    cam = bpy.data.objects.new(name, cam_data)
    link(cam, col)
    cam.location = loc
    point_at(cam, look_at)
    return cam


def point_at(obj: bpy.types.Object, target: Vec3) -> None:
    d = Vector(target) - Vector(obj.location)
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def cut(frame: int, cam: bpy.types.Object) -> None:
    """Bind `cam` from `frame` on — the same timeline-marker mechanism a human editor uses."""
    scene = bpy.context.scene
    m = scene.timeline_markers.new(f"cut_{cam.name}_{frame}", frame=frame)
    m.camera = cam
    if scene.camera is None:
        scene.camera = cam


# --------------------------------------------------------------------------- world / render


def sun(name="Sun", *, energy=3.0, rot=(50, 10, 30), angle_deg=3.0, col=None) -> bpy.types.Object:
    data = bpy.data.lights.new(name, "SUN")
    data.energy = energy
    data.angle = math.radians(angle_deg)
    o = bpy.data.objects.new(name, data)
    link(o, col)
    o.rotation_euler = rad(rot)
    return o


def sky(color: Vec3, strength: float = 1.0) -> None:
    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (*color, 1.0)
    bg.inputs["Strength"].default_value = strength


def _set_enum(owner, prop: str, wanted: list[str]) -> str:
    """Assign the first identifier in `wanted` the running Blender accepts."""
    for ident in wanted:
        try:
            setattr(owner, prop, ident)
            return ident
        except TypeError:
            continue
    return getattr(owner, prop)


def render_settings(*, width=1080, height=1920, frame_end=240, quality="preview",
                    filepath: str | None = None, video: bool = True) -> None:
    scene = bpy.context.scene
    r = scene.render
    scale = {"draft": 25, "preview": 50, "final": 100}[quality]
    samples = {"draft": 8, "preview": 16, "final": 32}[quality]
    r.resolution_x, r.resolution_y = width, height
    r.resolution_percentage = scale
    r.fps = FPS
    scene.frame_start = 1
    scene.frame_end = frame_end
    _set_enum(r, "engine", ["BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"])
    scene.eevee.taa_render_samples = samples
    r.film_transparent = False
    # Punchy cartoon colours: skip AgX's filmic desaturation if the build supports it.
    _set_enum(scene.view_settings, "view_transform", ["Standard"])
    if video:
        # Blender >= 5.0 gates video formats behind media_type
        if hasattr(r.image_settings, "media_type"):
            r.image_settings.media_type = "VIDEO"
        r.image_settings.file_format = "FFMPEG"
        r.ffmpeg.format = "MPEG4"
        r.ffmpeg.codec = "H264"
        _set_enum(r.ffmpeg, "constant_rate_factor", ["HIGH", "MEDIUM"])
        r.ffmpeg.audio_codec = "NONE"
    else:
        if hasattr(r.image_settings, "media_type"):
            r.image_settings.media_type = "IMAGE"
        r.image_settings.file_format = "PNG"
    if filepath:
        r.filepath = filepath
