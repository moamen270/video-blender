"""Star Wars parody cast and props: Vader, Luke, the lightsaber (vader-vs-luke-duel, 2026-09-26).

Vader = BaseCharacter (like Batman: the approved cape) in black with a helmet sized from the measured head, a face
mask (lenses, cheek plates, grille), chest box with lights, shoulder plates and a belt. No face decals (he has a mask:
no lip sync; his lines play over the breathing). Luke = Kimono_Male (the wrap front reads as the black Jedi tunic),
sleeves kept, black boots, one black glove (right hand), sandy hair from Casual_Male.
Characters face world +y at rest (root rotation 0); parts are placed in world space at rest and bone-parented.
"""
from __future__ import annotations

import math

import bpy
from mathutils import Vector

import kit.cape
from kit import face as F
from kit import fight as FT
from kit import look as L
from kit import qchar as Q
from studio import core as C


def _head_bounds(qc: Q.QChar) -> tuple[Vector, Vector]:
    """World bbox of the body's head verts (above the Head bone's root) at rest."""
    neck = qc.arm.matrix_world @ qc.arm.data.bones["Head"].head_local
    pts = [qc.body.matrix_world @ v.co for v in qc.body.data.vertices]
    hv = [p for p in pts if p.z > neck.z + 0.04]
    lo = Vector((min(p.x for p in hv), min(p.y for p in hv), min(p.z for p in hv)))
    hi = Vector((max(p.x for p in hv), max(p.y for p in hv), max(p.z for p in hv)))
    return lo, hi


def _attach(qc, objs, bone, tag):
    for i, o in enumerate(objs):
        Q.attach_part(qc, o, bone, f"{tag}{i}")


def _lathe(name, rows, n, keep, mat, col, centre, sx, sy, sz):
    """Revolve profile rows [(r, z) or callable(phi) -> (r, z)] around Z; phi = 90 deg is the front (+y).
    keep(i, phi) decides which quads exist (open the face). Returns the object."""
    import bmesh
    verts, faces = [], []
    phis = [2 * math.pi * j / n for j in range(n)]
    for i, row in enumerate(rows):
        for phi in phis:
            r, z = row(phi) if callable(row) else row
            verts.append(Vector((centre.x + r * sx * math.cos(phi), centre.y + r * sy * math.sin(phi), centre.z + z * sz)))
    for i in range(len(rows) - 1):
        for j in range(n):
            if keep(i, phis[j]) and keep(i, phis[(j + 1) % n]):
                a, b = i * n + j, i * n + (j + 1) % n
                faces.append((a, b, b + n, a + n))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    C.link(o, col)
    m = o.modifiers.new("solid", "SOLIDIFY"); m.thickness = 0.012; m.offset = 1.0
    return o


def _gloss(name: str, hex_: str, rough: float, metal: float = 0.0, coat: float = 0.0) -> bpy.types.Material:
    """Principled material (glossy plastic / metal) — the helmet look the owner liked in the live session."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*C.hex_rgb(hex_), 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat
    m.diffuse_color = (*C.hex_rgb(hex_), 1.0)
    return m


def vader_helmet(centre, R: float, col=None) -> list:
    """Darth Vader's helmet (the dome piece only; the faceplate is vader_mask) from the owner's live session
    (2026-09-26): a motorcycle helmet with the face cut out, shaped to the owner's reference photos: dome with a
    raised centre ridge, V brow, bell-flared skirt (widest at the sides, near-vertical at the back), open front.
    R = shell radius (head half-size x 1.22). Front = +y. Returns the objects."""
    c0 = Vector(centre)
    paint = _gloss("vh_paint", "#121317", 0.12, coat=1.0)
    lensm = _gloss("vh_lens", "#050608", 0.03, metal=0.7, coat=1.0)
    silver = _gloss("vh_silver", "#b9bec7", 0.25, metal=1.0)
    dgrey = _gloss("vh_dgrey", "#2c2f36", 0.3, metal=0.4)
    FRONT = math.radians(41)                                # half-width of the face opening = the mask's (asin 0.64 = 40 deg)

    def d(phi):                                             # angular distance from the front (+y)
        return abs((phi - math.pi / 2 + math.pi) % (2 * math.pi) - math.pi)

    def skirt_row(t):                                       # t 0..1 down the skirt
        def row(phi):
            side = abs(math.cos(phi))
            flare = 0.10 + 0.34 * side                      # bell: widest at the sides
            z_end = -1.02 + 0.10 * side                     # back lowest
            return (1.03 + flare * t ** 1.6, 0.10 + (z_end - 0.10) * t)
        return row

    def brow(phi):                                          # the dome's front edge dips into a V at the middle
        k = max(0.0, 1.0 - d(phi) / FRONT)
        return (1.03 + 0.05 * k, 0.10 - 0.16 * k)

    dome = [(0.0, 1.00), (0.36, 0.97), (0.64, 0.89), (0.84, 0.74), (0.96, 0.55), (1.02, 0.34), brow]
    rows = dome + [skirt_row(t) for t in (0.25, 0.5, 0.75, 1.0)]
    n_dome = len(dome)

    def keep(i, phi):
        return i < n_dome - 1 or d(phi) > FRONT             # open front below the brow

    shell = _lathe("vh_shell", rows, 72, keep, paint, col, c0, R, R * 1.1, R)
    shell.modifiers["solid"].thickness = 0.018
    parts = [shell]
    # the raised centre ridge over the dome, brow to back
    ridge_pts = []
    for a in range(0, 181, 12):
        t = math.radians(a)
        ridge_pts.append(c0 + Vector((0, math.cos(t) * R * 1.12, 0.1 * R + math.sin(t) * R * 0.92)))
    parts.append(C.curve_arc("vh_ridge", ridge_pts[1:-2], bevel=R * 0.07, mat=paint, col=col))
    return parts


def vader_mask(centre, R: float, col=None) -> list:
    """The faceplate on its own (owner: 'it's just a helmet and a mask, do each separately, then merge them').
    One curved plate cut to the mask outline (brow edge on top, straight sides, jaw corners, chin), wrapped on a
    cylinder of radius R and pushed forward toward the mouth (the reference profile), then the details on it:
    big angled eyes, ribbed nose bridge, slanted cheek lines, triangular grille with slots, two silver chin tubes.
    Units: R = the helmet's shell radius, so the mask fits the opening. centre = where the helmet's centre would be."""
    import bmesh
    c0 = Vector(centre)
    paint = _gloss("vh_paint", "#121317", 0.12, coat=1.0)
    lensm = _gloss("vh_lens", "#050608", 0.03, metal=0.7, coat=1.0)
    silver = _gloss("vh_silver", "#b9bec7", 0.25, metal=1.0)
    dgrey = _gloss("vh_dgrey", "#2c2f36", 0.3, metal=0.4)
    outline = [(-0.64, 0.06), (0.0, -0.08), (0.64, 0.06), (0.64, -0.55), (0.46, -0.95), (0.18, -1.10),
               (-0.18, -1.10), (-0.46, -0.95), (-0.64, -0.55)]           # (x, z) in R, clockwise from top-left

    def inside(x, z):
        n, ins = len(outline), False
        for i in range(n):
            (x1, z1), (x2, z2) = outline[i], outline[(i + 1) % n]
            if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1):
                ins = not ins
        return ins

    def surf(x, z):                                          # the mask surface: cylinder + forward jut at the mouth
        y = math.sqrt(max(0.0, 1.0 - x * x)) * 1.02
        jut = 0.18 * max(0.0, min(1.0, (-z - 0.35) / 0.55))
        return c0 + Vector((x * R, (y + jut) * R, z * R))

    N = 48
    xs = [-0.66 + 1.32 * i / N for i in range(N + 1)]
    zs = [0.08 - 1.20 * j / N for j in range(N + 1)]
    bm = bmesh.new()
    grid = {}
    for i, x in enumerate(xs):
        for j, z in enumerate(zs):
            if inside(x, z):
                grid[i, j] = bm.verts.new(surf(x, z))
    for i in range(N):
        for j in range(N):
            q = [grid.get(k) for k in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
            if all(q):
                bm.faces.new(q)
    def snap(px, pz):                                        # nearest point on the outline (smooth edge, no staircase)
        best = None
        pts = [(c0.x + x * R, c0.z + z * R) for x, z in outline]
        for i in range(len(pts)):
            (ax, az), (bx, bz) = pts[i], pts[(i + 1) % len(pts)]
            dx, dz = bx - ax, bz - az
            t = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / (dx * dx + dz * dz)))
            q = (ax + t * dx, az + t * dz)
            dd = math.hypot(px - q[0], pz - q[1])
            if best is None or dd < best[0]:
                best = (dd, q)
        return best[1]

    for v in bm.verts:
        if v.is_boundary:
            x, z = snap(v.co.x, v.co.z)
            v.co = surf((x - c0.x) / R, (z - c0.z) / R)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0015)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("vm_mask")
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(paint)
    mask = bpy.data.objects.new("vm_mask", me)
    C.link(mask, col)
    s = mask.modifiers.new("solid", "SOLIDIFY"); s.thickness = 0.02; s.offset = -1.0
    parts = [mask]

    def on(x, z, out=0.0):                                   # a point on the mask surface, `out` metres in front
        p = surf(x, z)
        return p + Vector((0, out, 0))

    for sgn in (-1, 1):                                      # eyes: big angled lenses, outer corners dropping
        e = C.sphere(f"vm_eye{sgn}", r=1.0, loc=on(sgn * 0.33, -0.18, 0.002), scale=(R * 0.27, 0.006, R * 0.15),
                     mat=lensm, col=col)                     # flat glass on the plate (owner review: no bug-eye domes)
        e.rotation_euler = (0, math.radians(sgn * 18), math.radians(sgn * -16))
        parts.append(e)
    nd = R * 0.10                                            # nose depth: its back sits 4 mm inside the plate
    parts.append(C.cube("vm_nose", size=1.0, loc=on(0, -0.30, nd / 2 - 0.004), scale=(R * 0.14, nd, R * 0.36),
                        mat=paint, col=col))
    for k in range(4):
        parts.append(C.cube(f"vm_rib{k}", size=1.0, loc=on(0, -0.30, nd - 0.004 + R * 0.01) + Vector((0, 0, (0.14 - 0.07 * k) * R)),
                            scale=(R * 0.16, R * 0.02, R * 0.022), mat=dgrey, col=col))
    # (no painted cheek lines: the owner removed them, 2026-09-26)
    grille = C.cylinder("vm_grille", r=R * 0.26, depth=R * 0.05, loc=on(0, -0.80, R * 0.02), rot=(-90, 0, 0),
                        mat=dgrey, col=col, verts=3)
    grille.location = c0 + Vector((-0.0006, 1.1671 * R, -0.8156 * R))   # the owner's hand edit: placed, bigger, angled
    grille.rotation_euler = (-4.67, 0.0, 0.04)
    grille.scale = (1.227, 1.227, 1.227)
    parts.append(grille)
    for k in range(-3, 4):
        parts.append(C.cube(f"vm_slot{k}", size=1.0, loc=on(k * 0.05, -0.74, R * 0.05),
                            scale=(R * 0.016, R * 0.01, R * 0.15 - abs(k) * R * 0.03), mat=lensm, col=col))
    for sgn in (-1, 1):
        parts.append(C.cylinder(f"vm_tube{sgn}", r=R * 0.024, depth=R * 0.20, loc=on(sgn * 0.22, -1.02, R * 0.06),
                                rot=(90, 0, 0), mat=silver, col=col))
    # the owner's hand edits in Blender (2026-09-26): slots and chin tubes moved/resized. Offsets in units of R from
    # the centre; slot scales stored for R = 0.347 and scaled with R. Backup: assets/models/vader_mask_owner_edit_*.blend
    OWNER = {
        "vm_slot-3": ((-0.1372, 1.1986, -0.7925), (0.0051, 0.0032, 0.0190)),
        "vm_slot-2": ((-0.0915, 1.2045, -0.7925), (0.0051, 0.0032, 0.0286)),
        "vm_slot-1": ((-0.0457, 1.2080, -0.7925), (0.0051, 0.0032, 0.0381)),
        "vm_slot0": ((0.0, 1.2091, -0.7925), (0.0051, 0.0032, 0.0476)),
        "vm_slot1": ((0.0457, 1.2080, -0.7925), (0.0051, 0.0032, 0.0381)),
        "vm_slot2": ((0.0914, 1.2045, -0.7925), (0.0051, 0.0032, 0.0286)),
        "vm_slot3": ((0.1372, 1.1986, -0.7925), (0.0051, 0.0032, 0.0190)),
        "vm_tube-1": ((-0.2682, 1.2427, -0.9783), None),
        "vm_tube1": ((0.2649, 1.2342, -0.9685), None),
    }
    for o in parts:
        if o.name in OWNER:
            d, s = OWNER[o.name]
            o.location = c0 + Vector(d) * R
            if s:
                o.scale = tuple(v * R / 0.347 for v in s)
    return parts


def vader_suit(qc: Q.QChar, col=None) -> dict:
    """Vader's costume on a plain Quaternius body (owner live session 2026-09-26): black leather bodysuit (the skin),
    glossy gloves/gauntlets and boots, shoulder armour collar, chest box with lights, belt with buckle and boxes, cape.
    Positions come from the body at rest (bones + a ray to the chest surface); front = world +y."""
    from mathutils.bvhtree import BVHTree
    leather = _gloss("vs_leather", "#131418", 0.45)
    gloss = _gloss("vs_gloss", "#0f1013", 0.12, coat=1.0)
    dgrey = _gloss("vh_dgrey", "#2c2f36", 0.3, metal=0.4)
    silver = _gloss("vh_silver", "#b9bec7", 0.25, metal=1.0)
    cloth = _gloss("vs_cape", "#0b0c0f", 0.75)
    cloth.use_backface_culling = False
    out = {}
    # 1) suit: the skin becomes black leather
    for s in qc.body.material_slots:
        if s.material and Q.strip(s.material.name) in ("Skin",):
            s.material = leather
    # 2) gloves + gauntlets, boots (native-space ranges as used for Batman)
    Q.assign(qc, gloss, bones=["Fist.L", "Fist.R"])
    Q.assign(qc, gloss, bones=["LowerArm.L", "LowerArm.R"], absx_min=1.06)
    Q.assign(qc, gloss, bones=["Foot.L", "Foot.R"])
    Q.assign(qc, gloss, bones=["LowerLeg.L", "LowerLeg.R"], z_range=(-1.0, 0.45))
    bpy.context.view_layer.update()
    mw, arm = qc.arm.matrix_world, qc.arm.data.bones
    neck = mw @ arm["Neck"].head_local if "Neck" in arm else mw @ arm["Head"].head_local
    sh_l, sh_r = mw @ arm["UpperArm.L"].head_local, mw @ arm["UpperArm.R"].head_local
    hip = mw @ arm["Abdomen"].head_local if "Abdomen" in arm else mw @ arm["Hips"].head_local
    pts = [qc.body.matrix_world @ v.co for v in qc.body.data.vertices]
    tree = BVHTree.FromPolygons(pts, [p.vertices[:] for p in qc.body.data.polygons])

    def front_at(z, x=0.0):                                   # the body's front surface at height z
        hit = tree.ray_cast(Vector((x, 2.0, z)), Vector((0, -1, 0)))
        return hit[0].y if hit[0] is not None else 0.1

    def ring(z, band=0.03):                                   # half-width / half-depth of the body at height z
        sl = [p for p in pts if abs(p.z - z) < band and abs(p.x) < abs(sh_l.x) * 0.9]
        return (max(abs(p.x) for p in sl), max(abs(p.y) for p in sl)) if sl else (0.15, 0.1)

    # 3) shoulder armour: a glossy collar plate over the shoulders, dipping at the front
    half_w = abs(sh_l.x - sh_r.x) / 2 * 1.35
    cw, cd = ring(neck.z - 0.08)
    def mantle_row(t):
        def row(phi):
            dip = 0.05 * max(0.0, math.sin(phi))              # lower at the chest
            return (0.35 + 0.65 * t, -0.13 * t - dip * t)
        return row
    out["mantle"] = _lathe("vs_mantle", [mantle_row(t) for t in (0.0, 0.35, 0.7, 1.0)], 64, lambda i, phi: True, gloss, col,
                           Vector((0, (sh_l.y + sh_r.y) / 2, neck.z + 0.01)), half_w, max(cd * 1.35, 0.12), 1.0)
    # 4) chest box on the chest surface, with coloured lights and switches
    cz = neck.z - 0.24
    fy = front_at(cz)
    box = C.cube("vs_chestbox", size=1.0, loc=(0, fy + 0.012, cz), scale=(0.15, 0.03, 0.10), mat=dgrey, col=col)
    parts = [box]
    for i, (hx, x, z) in enumerate((("#ff3a30", -0.045, 0.022), ("#36ff6a", 0.0, 0.022), ("#3a8cff", 0.045, 0.022),
                                    ("#ff3a30", -0.03, -0.02), ("#d8dde6", 0.0, -0.02), ("#d8dde6", 0.03, -0.02))):
        parts.append(C.cube(f"vs_light{i}", size=1.0, loc=(x, fy + 0.03, cz + z), scale=(0.022, 0.01, 0.016),
                            mat=FT.emit_mat(f"vs_l{i}", hx, 4.0) if i < 4 else silver, col=col))
    out["chest"] = parts
    # 5) belt: glossy band at the waist, silver buckle with slots, two boxes each side
    bz = hip.z + 0.05
    bw, bd = ring(bz)
    belt = _lathe("vs_belt", [(1.0, 0.03), (1.0, -0.03)], 48, lambda i, phi: True, gloss, col, Vector((0, 0, bz)),
                  bw * 1.08, bd * 1.12, 1.0)
    bfy = front_at(bz)
    parts = [belt, C.cube("vs_buckle", size=1.0, loc=(0, bfy + 0.02, bz), scale=(0.10, 0.012, 0.06), mat=silver, col=col)]
    for k in (-1, 0, 1):
        parts.append(C.cube(f"vs_bslot{k}", size=1.0, loc=(k * 0.025, bfy + 0.027, bz), scale=(0.012, 0.004, 0.035),
                            mat=gloss, col=col))
    for s in (-1, 1):
        for j in (1, 2):
            ang = math.radians(90 - s * (28 + 18 * j))
            px, py = bw * 1.12 * math.cos(ang), bd * 1.15 * math.sin(ang)
            b = C.cube(f"vs_bbox{s}{j}", size=1.0, loc=(px, py, bz - 0.005), scale=(0.045, 0.03, 0.05), mat=dgrey, col=col)
            b.rotation_euler = (0, 0, ang - math.pi / 2)
            parts.append(b)
    out["belt"] = parts
    for grp in ("chest", "belt"):
        for o in out[grp]:
            Q.attach_part(qc, o, "Torso" if grp == "chest" else ("Abdomen" if "Abdomen" in arm else "Hips"), o.name)
    Q.attach_part(qc, out["mantle"], "Torso", "mantle")
    # 6) cape: the approved skinned cape, in black fabric
    out["cape"] = kit.cape.build_cape(qc, cloth)
    return out


def _vader_helmet(c: Vector, h: Vector, *, gloss, grey, lens, dark, col) -> list:
    """The helmet as sculpted surfaces sized to the head bounds (c = centre, h = half size):
    dome + brow line + a flared skirt that sweeps lower at the back, open in front for the face mask;
    the mask = a plate that narrows to the chin, slanted triangular lenses, cheek plates, nose ridge, grille."""
    rx, ry, rz = h.x * 1.08, h.y * 1.1, h.z
    cc = c + Vector((0, -0.01, 0.02))
    FRONT = math.radians(40)                       # half-width of the face opening around phi = 90 deg

    def bottom(phi):                                # the skirt's lower edge: deepest at the back, higher at the front
        s = math.sin(phi)
        return (1.58, -1.08 - 0.30 * max(0.0, -s) + 0.10 * max(0.0, s))

    dome = [(0.0, 1.10), (0.36, 1.07), (0.63, 0.99), (0.83, 0.85), (0.96, 0.65), (1.03, 0.44), (1.06, 0.26)]
    skirt = [(1.10, 0.06), (1.18, -0.22), (1.32, -0.55), (1.46, -0.85), bottom]
    rows = dome + skirt
    n_dome = len(dome)

    def keep(i, phi):                               # below the brow, leave the front open
        d = abs((phi - math.pi / 2 + math.pi) % (2 * math.pi) - math.pi)
        return i < n_dome - 1 or d > FRONT

    helmet = _lathe("vader_helmet", rows, 64, keep, gloss, col, cc, rx, ry, rz)
    parts = [helmet]
    # brow ridge: a thick lip along the front edge of the dome (the "eyebrow" of the helmet)
    brow = _lathe("vader_brow", [(1.06, 0.30), (1.12, 0.24), (1.06, 0.16)], 64,
                  lambda i, phi: abs((phi - math.pi / 2 + math.pi) % (2 * math.pi) - math.pi) < FRONT + 0.25,
                  gloss, col, cc, rx, ry, rz)
    parts.append(brow)
    # face plate: from the brow down to the chin, narrowing (cheeks slope in), dark metal
    plate_rows = [(1.03, 0.20), (1.03, 0.00), (1.01, -0.30), (0.95, -0.62), (0.80, -0.92), (0.55, -1.08)]
    plate = _lathe("vader_face", plate_rows, 64,
                   lambda i, phi: abs((phi - math.pi / 2 + math.pi) % (2 * math.pi) - math.pi) <= FRONT + 0.05,
                   gloss, col, cc, rx, ry, rz)
    parts.append(plate)
    fy = cc.y + ry * 1.03                           # the plate's front, for the details
    # slanted triangular lenses (a 3-sided prism, point toward the nose and down)
    glass = L.toon2("vader_lensglass", "#050608", hi_hex="#5f7896", rim_hex="#7d9cc4", rim=1.0)
    for s in (-1, 1):
        e = C.cylinder(f"vader_eye{s}", r=h.x * 0.34, depth=0.03, loc=Vector((cc.x + s * rx * 0.33, fy + 0.02, cc.z + rz * 0.02)),
                       rot=(-90, 0, s * 20), scale=(1.35, 1.0, 0.80), mat=glass, col=col, verts=3)
        parts.append(e)
        parts.append(C.sphere(f"vader_glint{s}", r=1.0, loc=Vector((cc.x + s * rx * 0.25, fy + 0.04, cc.z + rz * 0.12)),
                              scale=(h.x * 0.05, 0.006, rz * 0.035), mat=FT.emit_mat("vader_glint", "#9fb8d8", 1.5), col=col))
    # nose ridge + cheek plates (grey) + the triangular grille with slits
    parts.append(C.cube("vader_nose", size=1.0, loc=Vector((cc.x, fy + 0.012, cc.z - rz * 0.22)),
                        scale=(h.x * 0.13, 0.035, rz * 0.40), mat=dark, col=col))
    for s in (-1, 1):
        parts.append(C.cube(f"vader_cheek{s}", size=1.0, loc=Vector((cc.x + s * rx * 0.44, fy - 0.03, cc.z - rz * 0.48)),
                            rot=(0, 0, s * -28), scale=(h.x * 0.26, 0.03, rz * 0.34), mat=grey, col=col))
    grille = C.cylinder("vader_grille", r=h.x * 0.30, depth=0.03, loc=Vector((cc.x, fy - 0.01, cc.z - rz * 0.72)),
                        rot=(-90, 0, 0), scale=(1.0, 1.0, 1.0), mat=grey, col=col, verts=3)
    parts.append(grille)
    for k in (-1, 0, 1):
        parts.append(C.cube(f"vader_slit{k}", size=1.0, loc=Vector((cc.x + k * h.x * 0.09, fy + 0.008, cc.z - rz * 0.68)),
                            scale=(0.009, 0.01, rz * 0.16), mat=lens, col=col))
    return parts


def build_vader(col: bpy.types.Collection | None = None) -> Q.QChar:
    """Darth Vader parody."""
    qc = Q.load_character("BaseCharacter.blend", "vader", col=col)
    tc = col or (qc.body.users_collection[0] if qc.body.users_collection else None)
    black = L.toon2("vader_black", "#16171c")
    gloss = L.toon2("vader_gloss", "#2a2d35")
    grey = L.toon2("vader_grey", "#7b808a")
    dark_grey = L.toon2("vader_dgrey", "#3a3d45")
    lens = L.toon2("vader_lens", "#0b0c10")
    for s in qc.body.material_slots:
        if s.material:
            s.material = black

    lo, hi = _head_bounds(qc)
    c, h = (lo + hi) / 2, (hi - lo) / 2
    front = hi.y
    parts = _vader_helmet(c, h, gloss=gloss, grey=grey, lens=lens, dark=dark_grey, col=tc)
    _attach(qc, parts, "Head", "helmet")
    qc.arm.pose.bones["Head"].scale = (0.72, 0.72, 0.72)   # smaller head (the helmet follows): less chibi, more menace

    # chest box with lights, found on the chest surface (Batman's emblem position)
    chest = Q.native(qc, Q.surface_points(qc, [(0.0, 1.62)], bones=["Torso", "Abdomen"], offset=0.01)[0])
    box = C.cube("vader_chestbox", size=1.0, loc=chest + Vector((0, 0.02, 0.0)), scale=(0.17, 0.035, 0.12),
                 mat=dark_grey, col=tc)
    lights = [C.cube(f"vader_light{i}", size=1.0, loc=chest + Vector((-0.05 + 0.05 * i, 0.042, 0.02 - 0.03 * (i == 1))),
                     scale=(0.028, 0.012, 0.022), mat=FT.emit_mat(f"vader_l{i}", ["#ff3a30", "#36ff6a", "#3a8cff"][i], 7.0),
                     col=tc) for i in range(3)]
    _attach(qc, [box, *lights], "Torso", "chest")
    # shoulder plates
    for side, k in (("L", 1), ("R", -1)):
        b = qc.arm.data.bones[f"UpperArm.{side}"]
        p = qc.arm.matrix_world @ b.head_local
        sp = C.sphere(f"vader_shoulder.{side}", r=1.0, loc=p + Vector((0, 0.0, 0.05)), scale=(0.13, 0.13, 0.06),
                      mat=gloss, col=tc)
        Q.attach_part(qc, sp, "Torso", f"shoulder.{side}")
    # belt with two silver boxes
    hip = qc.arm.matrix_world @ qc.arm.data.bones["Abdomen"].head_local
    belt = C.cylinder("vader_belt", r=1.0, depth=0.07, loc=hip + Vector((0, 0, 0.02)), scale=(0.2, 0.15, 1.0),
                      mat=dark_grey, col=tc)
    buckles = [C.cube(f"vader_buckle{s}", size=1.0, loc=hip + Vector((s * 0.08, 0.15, 0.02)), scale=(0.06, 0.02, 0.06),
                      mat=grey, col=tc) for s in (-1, 1)]
    _attach(qc, [belt, *buckles], "Abdomen", "belt")

    cape = kit.cape.build_cape(qc, black)
    black.use_backface_culling = False
    Q.smooth(qc)
    Q.smooth(qc, obj=cape)
    Q.outline(qc.body, 0.010)
    Q.outline(cape, 0.010)
    for n in ("vader_helmet", "vader_brow"):
        Q.outline(bpy.data.objects[n], 0.008)
    return qc


def luke_hair(qc: Q.QChar, mat, col=None) -> bpy.types.Object:
    """Luke's hair (owner refs 2026-09-26: LEGO Luke, ROTJ art): a rounded light-brown cap over the head that covers
    the ears, a fringe swept to his right from a part on his left, down to the nape at the back. Built at rest from the
    head bounds and parented to the Head bone."""
    lo, hi = _head_bounds(qc)
    c, h = (lo + hi) / 2, (hi - lo) / 2

    def d(phi):
        return abs((phi - math.pi / 2 + math.pi) % (2 * math.pi) - math.pi)

    def edge(phi):                                             # the hair's lower edge height, in head half-sizes
        a = d(phi)
        front = 0.26 + 0.22 * math.cos(phi)                     # diagonal swept fringe: low on his right (world -x), high at the part
        if a < math.radians(62):
            return front
        if a < math.radians(105):                               # temples -> over the ears
            t = (a - math.radians(62)) / math.radians(43)
            return front + (-0.38 - front) * t
        t = (a - math.radians(105)) / math.radians(75)          # ears -> nape
        return -0.38 + (-0.72 + 0.38) * t

    def radius(z):                                             # follow the round head, with volume on top
        if z >= 0:
            return 1.17 * math.sqrt(max(0.0, 1.0 - (z / 1.30) ** 2))
        return 1.10 * math.sqrt(max(0.25, 1.0 - (z / 1.10) ** 2))

    LOCKS, TWIST = 11, 0.55                                    # hair locks around the head; how much they sweep sideways

    def lock(phi, u):                                          # 1 on a lock's ridge, 0 in the groove between locks
        return (0.5 + 0.5 * math.cos(LOCKS * (phi + TWIST * u))) ** 2

    def row(u, z_of):                                          # u: 0 at the crown -> 1 at the tips
        def f(phi):
            z = z_of(phi)
            if u >= 0.99:                                      # the tips: each lock ends in a point, lower than the grooves
                z -= 0.12 * lock(phi, u)
            tuck = 0.05 * max(0.0, (u - 0.45) / 0.55) * max(0.0, 1.0 - d(phi) / math.radians(62))
            bump = 0.07 * (u ** 0.8) * lock(phi, u)             # locks stand out more toward the tips
            return (radius(z) * (1.0 + bump) - tuck, z)
        return f

    rows = [row(0.0, lambda phi: 1.30)]
    for u, z in ((0.06, 1.26), (0.16, 1.15), (0.28, 0.98), (0.40, 0.76)):
        rows.append(row(u, lambda phi, z=z: z))
    for tt in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        rows.append(row(0.45 + 0.55 * tt, lambda phi, tt=tt: 0.55 + (edge(phi) - 0.55) * tt))
    o = _lathe("luke_hair", rows, 176, lambda i, phi: True, mat, col, c + Vector((0, -0.01, 0.0)), h.x, h.y, h.z)
    o.modifiers["solid"].thickness = 0.03
    Q.attach_part(qc, o, "Head", "hair")
    return o


def build_luke(col: bpy.types.Collection | None = None) -> Q.QChar:
    """Luke Skywalker parody (Return of the Jedi black tunic)."""
    from kit import cast
    qc = Q.load_character("Kimono_Male.blend", "luke", col=col)
    tc = col or (qc.body.users_collection[0] if qc.body.users_collection else None)
    F.build_face(qc, rest="frown", paint_hex="#241812")
    F.set_expression(qc.face, "stern")
    skin = L.toon2("luke_skin", cast.SKIN["ken"])
    tunic = L.toon2("luke_tunic", "#1c1d22")
    Q.assign(qc, skin, materials=["Skin"])
    Q.assign(qc, tunic, materials=["Clothes"])
    Q.assign(qc, L.toon2("luke_belt", "#3a3b42"), materials=["Band"], z_range=(-1.0, 2.0))
    hair = L.toon2("luke_hair", "#a07c55")                    # light brown (owner refs)
    band = L.toon2("luke_band", cast.SKIN["ken"])              # the pack's headband in skin colour (the hair covers it)
    Q.assign(qc, band, materials=["Band"], z_range=(2.0, 9.0))
    # the pack's headband tails stand straight up (they read as horns): remove them (as cast._fighter does)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(qc.body.data)
    hi_ = list(qc.body.data.materials).index(band)
    tails = [f for f in bm.faces if f.material_index == hi_ and f.calc_center_median().z > 2.98]
    bmesh.ops.delete(bm, geom=tails, context="FACES")
    bm.to_mesh(qc.body.data); bm.free(); qc.body.data.update()
    cast.shape_arms(qc)
    cast.add_thumbs(qc, skin, tc)
    Q.assign(qc, L.toon2("luke_glove", "#121216"), bones=["Fist.R"])     # the black glove (his robot hand)
    boots = L.toon2("luke_boots", "#141418")
    Q.assign(qc, boots, bones=["Foot.L", "Foot.R"])
    Q.assign(qc, boots, bones=["LowerLeg.L", "LowerLeg.R"], z_range=(-1.0, 0.45))
    part = luke_hair(qc, hair, tc)
    Q.smooth(qc)
    Q.outline(qc.body, 0.010)
    Q.outline(part, 0.010)
    return qc


class Lightsaber:
    """A lightsaber in a character's hand: hilt + white core + coloured glow; key(frame, on=0..1) ignites/retracts.

    Built along +Z of an empty `root` that is bone-parented to the fist (grip), so it follows the hand; aim it by
    rotating root. on = blade length fraction (ignite = 0 -> 1 over ~5 frames)."""

    def __init__(self, name: str, colour: str, qc: Q.QChar | None = None, side: str = "R", length: float = 0.95):
        self.length = length
        self.root = C.empty(f"{name}_root")
        hilt_m = L.toon2(f"{name}_hilt", "#9aa0aa")
        grip_m = L.toon2(f"{name}_grip", "#1b1c20")
        self.hilt = C.cylinder(f"{name}_hilt", r=0.022, depth=0.26, loc=(0, 0, 0.0), mat=hilt_m, parent=self.root)
        C.cylinder(f"{name}_griprings", r=0.024, depth=0.1, loc=(0, 0, -0.04), mat=grip_m, parent=self.root)
        C.cylinder(f"{name}_emitter", r=0.028, depth=0.04, loc=(0, 0, 0.13), mat=hilt_m, parent=self.root)
        # blade objects have their origin at the emitter so scaling Z grows them out of the hilt
        self.blade = C.empty(f"{name}_blade", parent=self.root, loc=(0, 0, 0.15))
        C.cylinder(f"{name}_core", r=0.014, depth=1.0, loc=(0, 0, 0.5), mat=FT.emit_mat(f"{name}_core", "#ffffff", 9.0),
                   parent=self.blade)
        C.sphere(f"{name}_tip", r=0.014, loc=(0, 0, 1.0), mat=FT.emit_mat(f"{name}_core", "#ffffff", 9.0), parent=self.blade)
        C.cylinder(f"{name}_glow", r=0.034, depth=1.02, loc=(0, 0, 0.5),
                   mat=FT.emit_mat(f"{name}_glow", colour, strength=6.0, alpha=0.5), parent=self.blade)
        self.blade.scale = (1, 1, length)
        if qc is not None:
            bpy.context.view_layer.update()
            fist = qc.arm.pose.bones[f"Fist.{side}"]
            p = qc.arm.matrix_world @ fist.tail
            self.root.location = p
            from kit import rig
            rig.attach(self.root, qc.arm, f"Fist.{side}")

    def key(self, frame: int, on: float) -> None:
        """Low-level blade length key. Scenes use ignite()/retract() (docs/PROPS.md: a state change needs its action)."""
        self.blade.scale = (1, 1, max(on, 0.001) * self.length)
        self.blade.hide_render = on <= 0.001
        self.blade.keyframe_insert("scale", frame=frame)
        for o in self.blade.children:
            o.hide_render = on <= 0.001
            o.keyframe_insert("hide_render", frame=frame)

    # --- actions (docs/PROPS.md) ---------------------------------------------------------------------
    holder = None
    side = "R"

    def hold(self, qc: Q.QChar, side: str = "R") -> None:
        """Put the hilt in the fist (bone-parented at the grip point)."""
        from kit import rig
        bpy.context.view_layer.update()
        self.root.location = qc.arm.matrix_world @ qc.arm.pose.bones[f"Fist.{side}"].tail
        rig.attach(self.root, qc.arm, f"Fist.{side}")
        self.holder, self.side = qc, side

    def _thumb(self, frame: int) -> None:
        """The thumb press: a 2-frame wrist tick on the holder's fist."""
        if self.holder is None:
            raise RuntimeError("a saber is switched by its holder: call hold() first (docs/PROPS.md)")
        pb = self.holder.arm.pose.bones[f"Fist.{self.side}"]
        pb.rotation_mode = "XYZ"
        for f, a in ((frame - 3, 0.0), (frame - 1, 9.0), (frame + 1, 0.0)):
            pb.rotation_euler = (math.radians(a), 0, 0)
            pb.keyframe_insert("rotation_euler", frame=f)

    def ignite(self, frame: int, frames: int = 5) -> dict:
        """The holder's thumb press, then the blade grows over `frames`. Returns the sound cue (on `frame`)."""
        self._thumb(frame)
        self.key(frame - 1, 0.0)
        for i in range(1, frames + 1):
            self.key(frame + i - 1, i / frames)
        self.events = getattr(self, "events", []) + [("ignite", frame)]
        return {"frame": frame, "sfx": "saber_ignite"}

    def retract(self, frame: int, frames: int = 4) -> dict:
        self._thumb(frame)
        self.key(frame - 1, 1.0)
        for i in range(1, frames + 1):
            self.key(frame + i - 1, 1.0 - i / frames)
        self.events = getattr(self, "events", []) + [("retract", frame)]
        return {"frame": frame, "sfx": "saber_retract"}

    def core_points(self, n: int = 12) -> list:
        """World points along the lit blade core at the current frame ([] when off)."""
        if self.blade.scale.z <= 0.002 or self.blade.hide_render:
            return []
        m = self.blade.matrix_world
        return [m @ Vector((0, 0, (i + 0.5) / n)) for i in range(n)]


# ------------------------------------------------------------------ set: a Death Star-style corridor
def death_star_corridor(col: bpy.types.Collection | None = None, *, width: float = 4.4, height: float = 3.3,
                        depth: float = 14.0) -> dict:
    """Grey panelled corridor along +y (camera at -y looks in): floor grating, wall panels, light strips, a ceiling,
    an octagonal doorway at the end. Never a black void (border check). Returns the lights (see corridor_lights)."""
    col = col or C.collection("corridor")
    wall = L.toon2("ds_wall", "#8a93a3", rim=0.0)
    panel = L.toon2("ds_panel", "#6e7788", rim=0.0)
    floor_m = L.toon2("ds_floor", "#3c424f", rim=0.0)
    ceil = L.toon2("ds_ceiling", "#5b6272", rim=0.0)
    strip = FT.emit_mat("ds_strip", "#e8f4ff", 4.0)
    y0 = -4.0
    C.cube("ds_floor", size=1, loc=(0, y0 + depth / 2, -0.05), scale=(width + 2, depth + 4, 0.1), mat=floor_m, col=col)
    for k in range(int(depth / 0.9)):                                   # floor grating lines
        C.cube(f"ds_grate{k}", size=1, loc=(0, y0 + 0.45 + k * 0.9, 0.003), scale=(width, 0.03, 0.006),
               mat=L.toon2("ds_grate", "#2a2f39", rim=0.0), col=col)
    C.cube("ds_ceiling", size=1, loc=(0, y0 + depth / 2, height + 0.05), scale=(width + 2, depth + 4, 0.1), mat=ceil, col=col)
    for s in (-1, 1):
        x = s * width / 2
        C.cube(f"ds_wall{s}", size=1, loc=(x + s * 0.1, y0 + depth / 2, height / 2), scale=(0.2, depth + 4, height + 0.2),
               mat=wall, col=col)
        for k in range(int(depth / 1.6)):
            y = y0 + 0.8 + k * 1.6
            C.cube(f"ds_panel{s}_{k}", size=1, loc=(x - s * 0.02, y, 1.35), scale=(0.04, 1.3, 1.6), mat=panel, col=col)
            C.cube(f"ds_strip{s}_{k}", size=1, loc=(x - s * 0.04, y, 2.55), scale=(0.03, 1.1, 0.08), mat=strip, col=col)
        C.cube(f"ds_base{s}", size=1, loc=(x - s * 0.06, y0 + depth / 2, 0.12), scale=(0.12, depth + 4, 0.24),
               mat=L.toon2("ds_base", "#4a5160", rim=0.0), col=col)
    for k in range(int(depth / 1.6)):                                     # ceiling light panels
        C.cube(f"ds_ceilight{k}", size=1, loc=(0, y0 + 0.8 + k * 1.6, height - 0.01), scale=(1.2, 0.35, 0.02), mat=strip, col=col)
    end = y0 + depth
    C.cube("ds_endwall", size=1, loc=(0, end, height / 2), scale=(width + 0.4, 0.2, height + 0.2), mat=wall, col=col)
    door = C.cylinder("ds_door", r=1.15, depth=0.05, loc=(0, end - 0.12, 1.25), rot=(90, 0, 22.5),
                      mat=L.toon2("ds_door", "#454c5a", rim=0.0), col=col)
    door.data.update()
    C.torus("ds_doorframe", major=1.2, minor=0.05, loc=(0, end - 0.15, 1.25), rot=(90, 0, 0),
            mat=L.toon2("ds_doorframe", "#9aa3b3", rim=0.0), col=col)
    return corridor_lights(col)


def corridor_lights(col=None) -> dict:
    """Cool overhead key + blue fill + world. key_mood(frame, 'lit'|'dark') switches them (keyed)."""
    key = C.sun("ds_key", energy=2.6, rot=(35, 0, 15), angle_deg=6.0, col=col)
    key.data.color = C.hex_rgb("#eef4ff")
    fill = C.sun("ds_fill", energy=0.9, rot=(70, 0, 200), angle_deg=10.0, col=col)
    fill.data.color = C.hex_rgb("#8fb0ff")
    C.sky(C.hex_rgb("#4d5566"), 1.0)
    return {"key": key, "fill": fill}


MOODS = {  # key, fill, world strength, strip emission, exposure (toon shading keeps a floor: exposure does the dark)
    "lit": (2.6, 0.9, 1.0, 4.0, 0.0),
    "dark": (0.0, 0.5, 0.3, 0.6, -2.4),   # dim blue emergency level: dark but never flat black (border check)
    "lamp": (0.0, 0.35, 0.3, 0.4, -1.4),  # warm point light from the bulb does the rest
}


def key_mood(lights: dict, frame: int, mood: str) -> None:
    k, f, w, s, ev = MOODS[mood]
    vs = bpy.context.scene.view_settings
    vs.exposure = ev; vs.keyframe_insert("exposure", frame=frame)
    lights["key"].data.energy = k; lights["key"].data.keyframe_insert("energy", frame=frame)
    lights["fill"].data.energy = f; lights["fill"].data.keyframe_insert("energy", frame=frame)
    bg = next(n for n in bpy.context.scene.world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Strength"].default_value = w; bg.inputs["Strength"].keyframe_insert("default_value", frame=frame)
    m = bpy.data.materials.get("ds_strip")
    if m:
        em = next(n for n in m.node_tree.nodes if n.type == "EMISSION")
        em.inputs["Strength"].default_value = s; em.inputs["Strength"].keyframe_insert("default_value", frame=frame)
    for d in (lights["key"].data, lights["fill"].data, bpy.context.scene):   # moods switch, they don't fade
        for fc in C.fcurves(d):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


# ------------------------------------------------------------------ prop: a bare bulb on a pull cord
class PullLamp:
    """A bare bulb hanging from the ceiling on a flex, with a pull cord and bead. key_on(frame, on) switches the bulb
    glow + a warm point light; swing(frame, amp_deg, frames) keys a damped swing (the pull)."""

    def __init__(self, loc=(0.0, 0.6, 3.3), drop: float = 1.05, col=None):
        self.pivot = C.empty("lamp_pivot", loc=loc, col=col)
        self.pivot.rotation_mode = "XYZ"
        flex_m = L.toon2("lamp_flex", "#1b1c20", rim=0.0)
        C.cylinder("lamp_flex", r=0.008, depth=drop, loc=(0, 0, -drop / 2), mat=flex_m, parent=self.pivot, col=col)
        C.cylinder("lamp_socket", r=0.035, depth=0.09, loc=(0, 0, -drop - 0.02), mat=L.toon2("lamp_socket", "#2a2b30"),
                   parent=self.pivot, col=col)
        self.glass = FT.emit_mat("lamp_bulb", "#fff1c8", 0.4)
        self.bulb = C.sphere("lamp_bulb", r=0.07, loc=(0, 0, -drop - 0.12), scale=(1, 1, 1.2), mat=self.glass,
                             parent=self.pivot, col=col)
        C.cylinder("lamp_cord", r=0.004, depth=0.55, loc=(0.03, 0, -drop - 0.33), mat=L.toon2("lamp_cord", "#d9d2c0", rim=0.0),
                   parent=self.pivot, col=col)
        self.bead = C.sphere("lamp_bead", r=0.018, loc=(0.03, 0, -drop - 0.62), mat=L.toon2("lamp_bead", "#c9a54a"),
                             parent=self.pivot, col=col)
        ld = bpy.data.lights.new("lamp_light", "POINT")
        ld.energy, ld.color, ld.shadow_soft_size = 0.0, C.hex_rgb("#ffcf8a"), 0.05
        self.light = bpy.data.objects.new("lamp_light", ld)
        C.link(self.light, col)
        self.light.parent = self.pivot
        self.light.location = (0, 0, -drop - 0.12)

    def key_on(self, frame: int, on: bool, energy: float = 900.0) -> None:
        em = next(n for n in self.glass.node_tree.nodes if n.type == "EMISSION")
        em.inputs["Strength"].default_value = 12.0 if on else 0.4
        em.inputs["Strength"].keyframe_insert("default_value", frame=frame)
        self.light.data.energy = energy if on else 0.0
        self.light.data.keyframe_insert("energy", frame=frame)

    def pull(self, qc: Q.QChar, frame: int, side: str = "R") -> dict:
        """The only way to switch the lamp (docs/PROPS.md): the fist is on the bead 3 frames before `frame`, pulls it
        down 8 cm by `frame` (state toggles + click there) and lets go; then the lamp swings. Keys the hand's IK target
        (kit.fight.prepare must have run; key the reach before this). Returns the sound cue."""
        bpy.context.scene.frame_set(frame - 3)
        bpy.context.view_layer.update()
        bead0 = self.bead.matrix_world.translation.copy()
        emp = qc.parts[f"ik.{side}"]
        con = next(c for c in qc.arm.pose.bones[f"LowerArm.{side}"].constraints if c.type == "IK")
        emp.location = bead0; emp.keyframe_insert("location", frame=frame - 3)
        con.influence = 1.0; con.keyframe_insert("influence", frame=frame - 3)
        emp.location = bead0 - Vector((0, 0, 0.08)); emp.keyframe_insert("location", frame=frame)
        bl = self.bead.location.copy()                     # the bead follows the hand down, then springs back
        self.bead.keyframe_insert("location", frame=frame - 3)
        self.bead.location = bl - Vector((0, 0, 0.08)); self.bead.keyframe_insert("location", frame=frame)
        self.bead.location = bl; self.bead.keyframe_insert("location", frame=frame + 3)
        self.state = not getattr(self, "state", False)
        self.key_on(frame - 1, not self.state)
        self.key_on(frame, self.state)
        for fc in C.fcurves(self.light.data):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
        self.swing(frame)
        self.events = getattr(self, "events", []) + [("pull", frame, qc.name, side)]
        return {"frame": frame, "sfx": "pull_cord_click"}

    def swing(self, frame: int, amp_deg: float = 14.0, frames: int = 60, period: int = 22) -> None:
        for i in range(0, frames + 1, 2):
            a = amp_deg * math.exp(-3.0 * i / frames) * math.sin(2 * math.pi * i / period)
            self.pivot.rotation_euler = (math.radians(a), math.radians(a * 0.3), 0)
            self.pivot.keyframe_insert("rotation_euler", frame=frame + i)


# ------------------------------------------------------------------ poses (kit.fight.Pose, native space: front = -y, up = +z,
# ~3.15 units tall; x+ = the character's left; head/torso X: + = tip FORWARD (look down), - = look up/back).
# Named for the script beats of vader-vs-luke-duel.
from kit.fight import Pose  # noqa: E402

_FEET_GUARD = dict(foot_l=(0.36, -0.30, 0.02), foot_r=(-0.30, 0.30, 0.02))
_FEET_STAND = dict(foot_l=(0.26, 0.02, 0.02), foot_r=(-0.26, 0.02, 0.02))
POSES = {
    # blades crossed, both hands on the hilt at chest height (the frame-1 / loop pose)
    "saber_guard": Pose(**_FEET_GUARD, hips=(0, 0, -0.18), hand_l=(0.06, -0.62, 1.62), hand_r=(-0.04, -0.58, 1.55),
                        torso=(6, 0, -8)),
    # leaning into the bind (the clash / "I AM YOUR—")
    "saber_press": Pose(foot_l=(0.40, -0.45, 0.02), foot_r=(-0.34, 0.42, 0.02), hips=(0, -0.08, -0.24),
                        hand_l=(0.06, -0.86, 1.72), hand_r=(-0.04, -0.82, 1.66), torso=(16, 0, -8)),
    # one hand raised: "hold on a second" (before both switch off)
    "hand_up": Pose(**_FEET_STAND, hand_r=(-0.40, -0.45, 2.55), hand_l=(0.36, -0.05, 1.05), torso=(0, 0, 0)),
    # Luke: hand cupped to the ear ("YOU'RE MY WHAT?!")
    "ear_cup": Pose(**_FEET_STAND, hand_l=(0.66, -0.12, 2.45), hand_r=(-0.34, -0.40, 1.45), torso=(8, 10, 0)),
    # Luke in the dark: arms out, feeling for the way
    "lost": Pose(**_FEET_STAND, hand_l=(0.40, -0.88, 1.75), hand_r=(-0.40, -0.88, 1.75), torso=(6, 0, 0), head=(0, 0, 20)),
    # Vader looks around in the dark
    "look_around": Pose(**_FEET_STAND, hand_l=(0.34, -0.10, 1.10), hand_r=(-0.34, -0.10, 1.10), head=(0, 30, 0)),
    # Vader reaches up for the pull cord
    "pull_cord": Pose(**_FEET_STAND, hand_r=(-0.72, -0.25, 3.20), hand_l=(0.34, -0.05, 1.05), torso=(-6, 0, 0),
                      head=(-25, 0, 0)),
    # Vader straightens up, formal, hands at the belt ("Luke. I am your father.")
    "formal": Pose(**_FEET_STAND, hand_l=(0.26, -0.30, 1.28), hand_r=(-0.26, -0.30, 1.28), torso=(-5, 0, 0)),
    # Luke: "NOOOO!" head back, fists down
    "no_scream": Pose(foot_l=(0.30, 0.0, 0.02), foot_r=(-0.30, 0.0, 0.02), hips=(0, 0, -0.10),
                      hand_l=(0.55, -0.05, 1.40), hand_r=(-0.55, -0.05, 1.40), torso=(-20, 0, 0), head=(-40, 0, 0)),
    # Vader leans in over the hum ("...WHAT?") with a hand to the side of his helmet
    "lean_in": Pose(**_FEET_STAND, hand_l=(0.55, -0.25, 2.50), hand_r=(-0.30, -0.60, 1.55), torso=(18, 0, -10)),
}

# which character uses which pose (G3 pose sheets show only these)
POSE_CAST = {
    "vader": ["saber_guard", "saber_press", "hand_up", "look_around", "pull_cord", "formal", "lean_in"],
    "luke": ["saber_guard", "saber_press", "ear_cup", "lost", "no_scream"],
}

# face per pose (kit.face EXPRESSIONS; Vader has no face)
POSE_FACE = {"ear_cup": "suspicious", "lost": "surprised", "no_scream": "surprised", "saber_press": "angry"}
