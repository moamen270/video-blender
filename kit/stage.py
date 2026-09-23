"""Moonlit bamboo stage, lights, moon, and falling petals (Task T5)."""
from __future__ import annotations

import math
import random

import bpy

from kit import toon
from studio import core as C


def build_stage(seed: int = 7) -> None:
    """Build the moonlit bamboo stage environment per SAMURAI_PLAN §4.9."""
    rng = random.Random(seed)
    col = C.collection("stage")

    # World sky
    C.sky(C.hex_rgb("#0b1026"), 1.0)

    # Ground plane: size 60 at z 0, toon #1e2433, no outline
    mat_ground = toon.toon("stage_ground", "#1e2433")
    C.plane("stage_ground", size=60.0, loc=(0.0, 0.0, 0.0), mat=mat_ground, col=col)

    # Moon: cylinder r 2.6 depth 0.05 at (1.0, 30, 11) rot (90, 0, 0), emission 2.0, no outline
    mat_moon = toon.toon("stage_moon", "#f3ecd2", emission=2.0)
    C.cylinder(
        "stage_moon",
        r=2.6,
        depth=0.05,
        loc=(1.0, 30.0, 11.0),
        rot=(90.0, 0.0, 0.0),
        mat=mat_moon,
        col=col,
    )

    # Distant hills: 6 spheres r 6-10 scaled (1, 0.5, 0.35), y 25-40, z 0, toon #11172b, no outline
    mat_hill = toon.toon("stage_hill", "#11172b")
    for i in range(6):
        r_hill = rng.uniform(6.0, 10.0)
        y_hill = rng.uniform(25.0, 40.0)
        x_hill = -25.0 + i * 10.0 + rng.uniform(-2.0, 2.0)
        C.sphere(
            f"stage_hill_{i}",
            r=r_hill,
            loc=(x_hill, y_hill, 0.0),
            scale=(1.0, 0.5, 0.35),
            mat=mat_hill,
            col=col,
        )

    # Bamboo: 36 stalks behind (y in [6, 18]) + 12 stalks in front (y in [-14, -9])
    mat_bamboo = toon.toon("stage_bamboo", "#2f5d3a")
    mat_ring = toon.toon("stage_ring", "#22452b")

    stalk_coords: list[tuple[float, float]] = []
    for _ in range(36):
        stalk_coords.append((rng.uniform(-9.0, 9.0), rng.uniform(6.0, 18.0)))
    for _ in range(12):
        stalk_coords.append((rng.uniform(-9.0, 9.0), rng.uniform(-14.0, -9.0)))

    stalk_idx = 0
    for x, y in stalk_coords:
        if math.hypot(x, y) < 3.0:
            continue
        r = rng.uniform(0.05, 0.08)
        h = rng.uniform(6.0, 9.0)
        stalk = C.cylinder(
            f"stage_bamboo_{stalk_idx}",
            r=r,
            depth=h,
            loc=(x, y, h / 2.0),
            mat=mat_bamboo,
            col=col,
        )
        toon.add_outline(stalk, 0.012)

        for k in range(5):
            z_ring = (k + 1) * 1.2
            C.torus(
                f"stage_ring_{stalk_idx}_{k}",
                major=r + 0.01,
                minor=0.012,
                loc=(x, y, z_ring),
                mat=mat_ring,
                col=col,
            )
        stalk_idx += 1

    # Lights: key and rim sun lights
    key = C.sun("stage_key", energy=2.5, rot=(55, 0, 160), col=col)
    rim = C.sun("stage_rim", energy=1.5, rot=(60, 0, -20), col=col)
    key.data.color = (0.75, 0.82, 1.0)
    rim.data.color = (0.75, 0.82, 1.0)


def petals(
    count: int = 50,
    f0: int = 1,
    f1: int = 672,
    seed: int = 11,
) -> list[bpy.types.Object]:
    """Create falling cherry blossom petals per SAMURAI_PLAN §4.9."""
    rng = random.Random(seed)
    col = C.collection("stage")
    mat_petal = toon.toon("petal", "#f4b6c8", emission=0.4)
    petal_objs: list[bpy.types.Object] = []

    for i in range(count):
        s = rng.randint(f0 - 100, f1)
        d = rng.randint(120, 200)
        x0 = rng.uniform(-4.0, 4.0)
        y0 = rng.uniform(-2.0, 4.0)
        phase = rng.uniform(0.0, 2.0 * math.pi)
        spin_x = rng.uniform(-1.0, 1.0)
        spin_y = rng.uniform(-1.0, 1.0)

        petal = C.plane(
            f"fx_petal_{i}",
            size=1.0,
            scale=(0.04, 0.03, 1.0),
            mat=mat_petal,
            col=col,
        )

        for k in range(0, d + 1, 12):
            frame = s + k
            if frame < 1:
                continue
            t = k / d
            z = 4.5 * (1.0 - t)
            x = x0 + 0.4 * math.sin(2.0 * math.pi * 2.0 * t + phase)
            rot = (t * 720.0 * spin_x, t * 540.0 * spin_y, 0.0)
            C.key(petal, frame, loc=(x, y0, z), rot=rot, interp="BEZIER")

        C.visible(petal, 1, True)
        C.visible(petal, s + d + 1, False)

        petal_objs.append(petal)

    return petal_objs
