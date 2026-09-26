"""Build-time rule checks (docs/PROPS.md). Call after the timeline is keyed; returns the violations and writes them to
<out>/checks.json when `out` is given. A violation is a bug to fix before review, not a style note.

    from kit import checks
    bad = checks.prop_rules(chars=[vader, luke], sabers=[vs, ls], lamps=[lamp], f0=1, f1=END, out=HERE)
"""
from __future__ import annotations

import json
import os

import bpy
from mathutils.bvhtree import BVHTree

BLADE_CLEARANCE = 0.04      # m: nobody touches a lit blade (owner 2026-09-26)
BEAD_REACH = 0.04           # m: the fist is on the lamp's bead when it switches


def _bvh(obj, dg) -> BVHTree:
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    mw = obj.matrix_world
    tree = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons])
    ev.to_mesh_clear()
    return tree


def prop_rules(chars, sabers=(), lamps=(), f0: int = 1, f1: int = 1, step: int = 1, out: str | None = None) -> list:
    sc = bpy.context.scene
    bad = []
    if sabers:
        for f in range(f0, f1 + 1, step):
            sc.frame_set(f)
            dg = bpy.context.evaluated_depsgraph_get()
            trees = {qc.name: _bvh(qc.body, dg) for qc in chars}
            for s in sabers:
                pts = s.core_points()
                for name, tree in trees.items():
                    ds = [hit[3] for hit in (tree.find_nearest(p) for p in pts) if hit[0] is not None]
                    if ds and min(ds) < BLADE_CLEARANCE:
                        bad.append({"frame": f, "rule": "lit blade touches a body", "saber": s.root.name,
                                    "body": name, "distance_m": round(min(ds), 3)})
    for lamp in lamps:
        for _, frame, who, side in getattr(lamp, "events", []):
            sc.frame_set(frame)
            qc = next(c for c in chars if c.name == who)
            fist = qc.arm.matrix_world @ qc.arm.pose.bones[f"Fist.{side}"].tail
            d = (fist - lamp.bead.matrix_world.translation).length
            if d > BEAD_REACH:
                bad.append({"frame": frame, "rule": "lamp switched without the fist on the bead", "distance_m": round(d, 3)})
    if out:
        json.dump({"prop_rules": bad, "frames": [f0, f1]}, open(os.path.join(out, "checks.json"), "w"), indent=1)
    print(f"[checks] prop rules: {len(bad)} violation(s) in frames {f0}-{f1}", flush=True)
    return bad
