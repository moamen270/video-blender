"""Toon material and outline module."""
from __future__ import annotations

import bpy

from studio.core import hex_rgb

_CACHE: dict[str, bpy.types.Material] = {}


def toon(
    name: str,
    base_hex: str,
    shadow_hex: str | None = None,
    emission: float = 0.0,
) -> bpy.types.Material:
    """Create or return a cached toon material."""
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

    base_rgb = hex_rgb(base_hex)
    mat.diffuse_color = (*base_rgb, 1.0)

    if emission > 0:
        node_out = nodes.new("ShaderNodeOutputMaterial")
        node_emit = nodes.new("ShaderNodeEmission")
        node_emit.inputs["Color"].default_value = (*base_rgb, 1.0)
        node_emit.inputs["Strength"].default_value = float(emission)
        links.new(node_emit.outputs["Emission"], node_out.inputs["Surface"])
    else:
        if shadow_hex is not None:
            shadow_rgb = hex_rgb(shadow_hex)
        else:
            shadow_rgb = (base_rgb[0] * 0.45, base_rgb[1] * 0.45, base_rgb[2] * 0.45)

        node_out = nodes.new("ShaderNodeOutputMaterial")
        node_diffuse = nodes.new("ShaderNodeBsdfDiffuse")
        node_s2rgb = nodes.new("ShaderNodeShaderToRGB")
        node_ramp = nodes.new("ShaderNodeValToRGB")
        node_emit = nodes.new("ShaderNodeEmission")
        node_emit.inputs["Strength"].default_value = 1.0

        links.new(node_diffuse.outputs["BSDF"], node_s2rgb.inputs["Shader"])
        links.new(node_s2rgb.outputs["Color"], node_ramp.inputs["Fac"])
        links.new(node_ramp.outputs["Color"], node_emit.inputs["Color"])
        links.new(node_emit.outputs["Emission"], node_out.inputs["Surface"])

        ramp = node_ramp.color_ramp
        ramp.interpolation = "CONSTANT"
        ramp.elements[0].position = 0.0
        ramp.elements[0].color = (*shadow_rgb, 1.0)
        if len(ramp.elements) < 2:
            elem1 = ramp.elements.new(0.35)
        else:
            elem1 = ramp.elements[1]
            elem1.position = 0.35
        elem1.color = (*base_rgb, 1.0)

    _CACHE[name] = mat
    return mat


def outline_material() -> bpy.types.Material:
    """Return the cached black inverted-hull outline material."""
    if "outline" in _CACHE:
        try:
            _CACHE["outline"].name
            return _CACHE["outline"]
        except ReferenceError:
            del _CACHE["outline"]

    mat = bpy.data.materials.get("outline")
    if mat is None:
        mat = bpy.data.materials.new("outline")

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    links = mat.node_tree.links

    node_out = nodes.new("ShaderNodeOutputMaterial")
    node_emit = nodes.new("ShaderNodeEmission")
    node_emit.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    node_emit.inputs["Strength"].default_value = 1.0
    links.new(node_emit.outputs["Emission"], node_out.inputs["Surface"])

    mat.use_backface_culling = True
    # The hull encloses the object; without this it shadows the whole object (flipped normals -> culled).
    mat.use_backface_culling_shadow = True
    mat.diffuse_color = (0.0, 0.0, 0.0, 1.0)

    _CACHE["outline"] = mat
    return mat


def add_outline(obj: bpy.types.Object, thickness: float = 0.012) -> None:
    """Append the outline material and add a Solidify modifier for inverted-hull outline."""
    if obj.name.startswith("fx_"):
        return
    if not hasattr(obj, "data") or obj.data is None or not hasattr(obj.data, "materials"):
        return

    mat = outline_material()
    obj.data.materials.append(mat)
    slot_idx = len(obj.data.materials) - 1

    mod = obj.modifiers.get("outline")
    if mod is None:
        mod = obj.modifiers.new("outline", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.material_offset = slot_idx
    mod.use_rim = False
