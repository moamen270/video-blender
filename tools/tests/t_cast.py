"""Test for recurring cast builders (Task E4)."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.isdir(os.path.join(ROOT, "studio")):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import bpy

from kit import cast, qchar
from studio import core as C


def main() -> None:
    # Check CAST dictionary
    assert "batman" in cast.CAST, "Missing 'batman' in cast.CAST"
    assert "joker" in cast.CAST, "Missing 'joker' in cast.CAST"
    assert cast.CAST["batman"] == cast.build_batman
    assert cast.CAST["joker"] == cast.build_joker

    # 1. Test Batman builder
    C.reset_scene()
    batman = cast.build_batman()

    # Batman height 1.80 +- 0.02
    h_bat = qchar.height_now(batman)
    assert abs(h_bat - 1.80) <= 0.02, f"Batman height expected 1.80 +- 0.02, got {h_bat:.4f}"

    # Batman parts: belt, ear.L, ear.R, cape, emblem, bat (+ face parts)
    for p in ["belt", "ear.L", "ear.R", "cape", "emblem", "bat"]:
        assert p in batman.parts, f"Missing batman part '{p}'"
    assert batman.face is not None, "Batman face is None"
    assert hasattr(batman.face, "eyes") and len(batman.face.eyes) == 2, "Batman face missing eyes"
    assert hasattr(batman.face, "brows") and len(batman.face.brows) == 2, "Batman face missing brows"
    assert hasattr(batman.face, "mouths") and len(batman.face.mouths) > 0, "Batman face missing mouths"

    # Both ears are above the head top (world z > 1.70) and on opposite sides (x signs differ)
    ear_l = batman.parts["ear.L"]
    ear_r = batman.parts["ear.R"]
    bpy.context.view_layer.update()
    pos_l = ear_l.matrix_world.translation
    pos_r = ear_r.matrix_world.translation
    assert pos_l.z > 1.70, f"ear.L world z = {pos_l.z:.4f}, expected > 1.70"
    assert pos_r.z > 1.70, f"ear.R world z = {pos_r.z:.4f}, expected > 1.70"
    assert (pos_l.x * pos_r.x) < 0.0, f"Ears not on opposite sides: pos_l.x={pos_l.x:.4f}, pos_r.x={pos_r.x:.4f}"

    # Cape world mean y < -0.05 (behind the character)
    cape = batman.parts["cape"]
    mw_cape = cape.matrix_world
    mean_cape_y = sum((mw_cape @ v.co).y for v in cape.data.vertices) / len(cape.data.vertices)
    assert mean_cape_y < -0.05, f"Cape mean world y = {mean_cape_y:.4f}, expected < -0.05"

    # Outline material is the LAST slot of every outlined object
    batman_outlined = [
        batman.body,
        batman.parts["belt"],
        batman.parts["ear.L"],
        batman.parts["ear.R"],
        batman.parts["cape"],
    ]
    for obj in batman_outlined:
        mats = obj.data.materials
        assert len(mats) > 0, f"{obj.name} has no materials"
        last_mat = mats[-1]
        assert last_mat.name.split(".")[0] == "outline", (
            f"{obj.name} last material is '{last_mat.name}', expected 'outline'"
        )
        assert "outline" in obj.modifiers, f"{obj.name} missing 'outline' modifier"

    # Non-outlined objects should not have outline modifier or outline material
    for p_name in ["emblem", "bat"]:
        obj = batman.parts[p_name]
        assert "outline" not in obj.modifiers, f"{obj.name} should not have outline modifier"

    # 2. Test Joker builder
    C.reset_scene()
    joker = cast.build_joker()

    # Joker height 1.80-1.95 (hair)
    h_jok = qchar.height_now(joker)
    assert 1.80 <= h_jok <= 1.95, f"Joker height expected 1.80-1.95, got {h_jok:.4f}"

    # Joker parts: tag, tag_text (+ face parts)
    assert "tag" in joker.parts, "Missing joker part 'tag'"
    assert "tag_text" in joker.parts, "Missing joker part 'tag_text'"
    assert joker.face is not None, "Joker face is None"
    assert hasattr(joker.face, "eyes") and len(joker.face.eyes) == 2, "Joker face missing eyes"
    assert hasattr(joker.face, "brows") and len(joker.face.brows) == 2, "Joker face missing brows"
    assert hasattr(joker.face, "mouths") and len(joker.face.mouths) > 0, "Joker face missing mouths"

    # Outline material is the LAST slot of every outlined object (body only)
    assert len(joker.body.data.materials) > 0, "joker.body has no materials"
    last_mat_jok = joker.body.data.materials[-1]
    assert last_mat_jok.name.split(".")[0] == "outline", (
        f"joker.body last material is '{last_mat_jok.name}', expected 'outline'"
    )
    assert "outline" in joker.body.modifiers, "joker.body missing 'outline' modifier"

    print("[test] PASS", flush=True)


if __name__ == "__main__":
    main()
