"""Look-dev: toon v2 material, store_night light rig, and floor."""
from __future__ import annotations

import math
from typing import Sequence

import bpy
from mathutils import Matrix, Vector

from studio import core as C
from kit import toon

_CACHE: dict[str, bpy.types.Material] = {}


def _lerp(a: Sequence[float], b: Sequence[float], t: float) -> tuple[float, float, float]:
    """Linearly interpolate two 3-channel colour vectors per channel."""
    return (
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    )


def toon2(
    name: str,
    base_hex: str,
    *,
    shadow_hex: str | None = None,
    hi_hex: str | None = None,
    rim_hex: str = "#8ab4ff",
    rim: float = 0.8,
    rim_width: float = 0.70,
    emission: float = 0.0,
) -> bpy.types.Material:
    """Create or return a cached toon v2 material with warm/cool ramp and rim lighting."""
    if emission > 0:
        return toon.toon(name, base_hex, emission=emission)

    if name in _CACHE:
        try:
            _CACHE[name].name
            return _CACHE[name]
        except ReferenceError:
            del _CACHE[name]

    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    links = mat.node_tree.links

    base = C.hex_rgb(base_hex)
    mat.diffuse_color = (*base, 1.0)

    if shadow_hex is not None:
        shadow = C.hex_rgb(shadow_hex)
    else:
        base_half = (base[0] * 0.5, base[1] * 0.5, base[2] * 0.5)
        shadow = _lerp(base_half, C.hex_rgb("#1b2440"), 0.35)

    if hi_hex is not None:
        highlight = C.hex_rgb(hi_hex)
    else:
        # Scaled by brightness: a subtle sheen on near-black (cowl, dummy skin), a warm glint on colours.
        highlight = _lerp(base, C.hex_rgb("#fff1d6"), 0.06 + 0.16 * max(base))

    rim_color = C.hex_rgb(rim_hex)

    node_out = nodes.new("ShaderNodeOutputMaterial")
    node_emit = nodes.new("ShaderNodeEmission")
    node_emit.inputs["Strength"].default_value = 1.0
    links.new(node_emit.outputs["Emission"], node_out.inputs["Surface"])

    node_mix = nodes.new("ShaderNodeMix")
    node_mix.data_type = "RGBA"
    node_mix.blend_type = "MIX"

    in_fac = next(s for s in node_mix.inputs if s.identifier == "Factor_Float")
    in_a = next(s for s in node_mix.inputs if s.identifier == "A_Color")
    in_b = next(s for s in node_mix.inputs if s.identifier == "B_Color")
    out_res = next(s for s in node_mix.outputs if s.identifier == "Result_Color")

    in_b.default_value = (*rim_color, 1.0)
    links.new(out_res, node_emit.inputs["Color"])

    node_diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    node_diffuse.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)

    node_s2rgb = nodes.new("ShaderNodeShaderToRGB")
    links.new(node_diffuse.outputs["BSDF"], node_s2rgb.inputs["Shader"])

    node_rgb2bw = nodes.new("ShaderNodeRGBToBW")
    links.new(node_s2rgb.outputs["Color"], node_rgb2bw.inputs["Color"])

    node_ramp = nodes.new("ShaderNodeValToRGB")
    node_ramp.name = "ramp"
    links.new(node_rgb2bw.outputs["Val"], node_ramp.inputs["Fac"])

    ramp = node_ramp.color_ramp
    ramp.interpolation = "CONSTANT"
    ramp.elements[0].position = 0.00
    ramp.elements[0].color = (*shadow, 1.0)
    ramp.elements[1].position = 0.30
    ramp.elements[1].color = (*base, 1.0)
    elem2 = ramp.elements.new(0.85)
    elem2.color = (*highlight, 1.0)

    links.new(node_ramp.outputs["Color"], in_a)

    node_lw = nodes.new("ShaderNodeLayerWeight")
    node_lw.inputs["Blend"].default_value = 0.5

    node_gt_a = nodes.new("ShaderNodeMath")
    node_gt_a.operation = "GREATER_THAN"
    links.new(node_lw.outputs["Facing"], node_gt_a.inputs[0])
    node_gt_a.inputs[1].default_value = rim_width

    node_gt_b = nodes.new("ShaderNodeMath")
    node_gt_b.operation = "GREATER_THAN"
    links.new(node_rgb2bw.outputs["Val"], node_gt_b.inputs[0])
    node_gt_b.inputs[1].default_value = 0.30

    node_mul_ab = nodes.new("ShaderNodeMath")
    node_mul_ab.operation = "MULTIPLY"
    links.new(node_gt_a.outputs[0], node_mul_ab.inputs[0])
    links.new(node_gt_b.outputs[0], node_mul_ab.inputs[1])

    node_mul_rim = nodes.new("ShaderNodeMath")
    node_mul_rim.operation = "MULTIPLY"
    links.new(node_mul_ab.outputs[0], node_mul_rim.inputs[0])
    node_mul_rim.inputs[1].default_value = rim

    links.new(node_mul_rim.outputs[0], in_fac)

    _CACHE[name] = mat
    return mat


def store_night(
    target: Sequence[float] = (0.0, 0.0, 1.0),
    facing_deg: float = 0.0,
    *,
    col: bpy.types.Collection | None = None,
) -> dict[str, bpy.types.Object]:
    """'Gotham Mart, 3 A.M.' light rig."""
    C.sky(C.hex_rgb("#0b0f18"), 1.0)

    rot_m = Matrix.Rotation(math.radians(facing_deg), 3, "Z")
    t = Vector(target)

    key_offset = rot_m @ Vector((1.86, 3.65, 2.87))
    key = C.sun("key", energy=3.2, angle_deg=5.0, col=col)
    key.location = t + key_offset
    key.data.color = C.hex_rgb("#e4f0ff")
    C.point_at(key, target)

    rim_offset = rot_m @ Vector((-2.0, -3.5, 2.0))
    rim = C.sun("rim", energy=3.5, angle_deg=2.0, col=col)
    rim.location = t + rim_offset
    rim.data.color = C.hex_rgb("#8ab4ff")
    C.point_at(rim, target)

    scene = bpy.context.scene
    C._set_enum(scene.view_settings, "view_transform", ["Standard"])
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    return {"key": key, "rim": rim}


def floor(
    size: float = 8.0,
    hex_: str = "#2b3040",
    col: bpy.types.Collection | None = None,
) -> bpy.types.Object:
    """Ground plane with toon2 material."""
    return C.plane("floor", size=size, mat=toon2("floor", hex_, rim=0.0), col=col)


def toon_tex(mat: bpy.types.Material, tint: float = 1.0) -> bpy.types.Material:
    """Convert an imported glTF material in place to a toon texture material.

    `tint` multiplies the texture colour (sets are darkened so the characters pop at night).
    """
    if "glass" in mat.name.lower():
        return toon2(mat.name, "#9fb4c8", rim=0.0)

    image = None
    flat_color = (0.8, 0.8, 0.8, 1.0)

    if mat.use_nodes and mat.node_tree:
        for n in mat.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image:
                image = n.image
                break
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                if "Base Color" in n.inputs:
                    flat_color = tuple(n.inputs["Base Color"].default_value)
                break

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    links = mat.node_tree.links

    mat.diffuse_color = (*flat_color[:3], 1.0)

    # Image Texture (same image, interpolation = "Closest") -> colour C
    if image is not None:
        node_tex = nodes.new("ShaderNodeTexImage")
        node_tex.image = image
        node_tex.interpolation = "Closest"
        color_c = node_tex.outputs["Color"]
    else:
        node_rgb = nodes.new("ShaderNodeRGB")
        node_rgb.outputs["Color"].default_value = (*flat_color[:3], 1.0)
        color_c = node_rgb.outputs["Color"]

    if abs(tint - 1.0) > 1e-6:
        node_tint = nodes.new("ShaderNodeMix")
        node_tint.data_type = "RGBA"
        node_tint.blend_type = "MULTIPLY"
        next(i for i in node_tint.inputs if i.identifier == "Factor_Float").default_value = 1.0
        links.new(color_c, next(i for i in node_tint.inputs if i.identifier == "A_Color"))
        next(i for i in node_tint.inputs if i.identifier == "B_Color").default_value = (tint, tint, tint, 1.0)
        color_c = next(o for o in node_tint.outputs if o.identifier == "Result_Color")

    # Diffuse (white) -> ShaderToRGB -> RGBToBW = L
    node_diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    node_diffuse.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)

    node_s2rgb = nodes.new("ShaderNodeShaderToRGB")
    links.new(node_diffuse.outputs["BSDF"], node_s2rgb.inputs["Shader"])

    node_rgb2bw = nodes.new("ShaderNodeRGBToBW")
    links.new(node_s2rgb.outputs["Color"], node_rgb2bw.inputs["Color"])
    light_l = node_rgb2bw.outputs["Val"]

    # lit = L > 0.30 (Math GREATER_THAN), hi = L > 0.85
    node_lit = nodes.new("ShaderNodeMath")
    node_lit.operation = "GREATER_THAN"
    links.new(light_l, node_lit.inputs[0])
    node_lit.inputs[1].default_value = 0.30

    node_hi = nodes.new("ShaderNodeMath")
    node_hi.operation = "GREATER_THAN"
    links.new(light_l, node_hi.inputs[0])
    node_hi.inputs[1].default_value = 0.85

    def _new_mix(blend_type: str = "MIX"):
        n = nodes.new("ShaderNodeMix")
        n.data_type = "RGBA"
        n.blend_type = blend_type
        in_fac = next(s for s in n.inputs if s.identifier == "Factor_Float")
        in_a = next(s for s in n.inputs if s.identifier == "A_Color")
        in_b = next(s for s in n.inputs if s.identifier == "B_Color")
        out_res = next(s for s in n.outputs if s.identifier == "Result_Color")
        return n, in_fac, in_a, in_b, out_res

    # shadow colour = C * 0.5 mixed 35 % toward #1b2440
    _, fac_half, in_a_half, in_b_half, out_half = _new_mix("MULTIPLY")
    fac_half.default_value = 1.0
    links.new(color_c, in_a_half)
    in_b_half.default_value = (0.5, 0.5, 0.5, 1.0)

    _, fac_shadow, in_a_shadow, in_b_shadow, out_shadow = _new_mix("MIX")
    fac_shadow.default_value = 0.35
    links.new(out_half, in_a_shadow)
    in_b_shadow.default_value = (*C.hex_rgb("#1b2440"), 1.0)

    # highlight = C mixed 18 % toward #fff1d6
    _, fac_hi, in_a_hi, in_b_hi, out_hi = _new_mix("MIX")
    fac_hi.default_value = 0.18
    links.new(color_c, in_a_hi)
    in_b_hi.default_value = (*C.hex_rgb("#fff1d6"), 1.0)

    # col = mix(shadow, C, lit)
    _, fac_lit, in_a_lit, in_b_lit, out_lit = _new_mix("MIX")
    links.new(node_lit.outputs[0], fac_lit)
    links.new(out_shadow, in_a_lit)
    links.new(color_c, in_b_lit)

    # col = mix(col, highlight, hi)
    _, fac_final, in_a_final, in_b_final, out_final = _new_mix("MIX")
    links.new(node_hi.outputs[0], fac_final)
    links.new(out_lit, in_a_final)
    links.new(out_hi, in_b_final)

    # Emission (1.0) -> output
    node_emit = nodes.new("ShaderNodeEmission")
    node_emit.inputs["Strength"].default_value = 1.0
    links.new(out_final, node_emit.inputs["Color"])

    node_out = nodes.new("ShaderNodeOutputMaterial")
    links.new(node_emit.outputs["Emission"], node_out.inputs["Surface"])

    return mat

