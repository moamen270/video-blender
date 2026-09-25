"""Compositor post: glow on bright emission (bloom) and a keyable white flash (loop bridge, impacts).

Blender 5.x: the scene compositor is a node group (scene.compositing_node_group) with a group output.
"""
from __future__ import annotations

import bpy


def setup(*, glow: bool = True, threshold: float = 0.8, strength: float = 1.0, size: float = 0.6):
    """Build RLayers -> Glare -> Mix(white) -> output. Returns the flash mix node (key flash())."""
    sc = bpy.context.scene
    ng = bpy.data.node_groups.new("post", "CompositorNodeTree")
    sc.compositing_node_group = ng
    sc.render.use_compositing = True
    if not any(i.in_out == "OUTPUT" for i in ng.interface.items_tree):
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = ng.nodes.new("CompositorNodeRLayers")
    out = ng.nodes.new("NodeGroupOutput")
    src = rl.outputs["Image"]
    if glow:
        g = ng.nodes.new("CompositorNodeGlare")
        for want in ("Bloom", "BLOOM", "Fog Glow", "FOG_GLOW"):
            try:
                g.inputs["Type"].default_value = want
                break
            except (TypeError, ValueError):
                continue
        g.inputs["Threshold"].default_value = threshold
        g.inputs["Strength"].default_value = strength
        g.inputs["Size"].default_value = size
        ng.links.new(src, g.inputs["Image"])
        src = g.outputs["Image"]
    mix = ng.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[0].default_value = 0.0
    a = next(i for i in mix.inputs if i.name == "A" and i.type == "RGBA")
    b = next(i for i in mix.inputs if i.name == "B" and i.type == "RGBA")
    b.default_value = (1.0, 1.0, 1.0, 1.0)
    ng.links.new(src, a)
    res = next(o for o in mix.outputs if o.type == "RGBA")
    ng.links.new(res, out.inputs[0])
    return mix


def flash(mix, frame: int, value: float) -> None:
    """Key the white-flash amount (0 = picture, 1 = white) at `frame`."""
    mix.inputs[0].default_value = value
    mix.inputs[0].keyframe_insert("default_value", frame=frame)
