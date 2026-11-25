"""Procedural commuter EMU for the Marmaray Roblox project (original design, real-world dimensions).
Run inside Blender:  exec(open(r"...\\blender\\build_train.py", encoding="utf-8").read())
Units: metres. Blender axes: +X = forward, +Y = left, +Z = up. Rail top = z 0.
Dimensions: car 22.5 m (coupler-coupler), body 3.01 m wide, 3.85 m high, floor 1.05 m, 5 double doors per side.
"""
import bpy, bmesh, math
from mathutils import Vector

# ---------------------------------------------------------------- scene reset
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
for blk in (bpy.data.meshes, bpy.data.materials):
    for d in list(blk): blk.remove(d)

# ---------------------------------------------------------------- materials (original livery)
PAL = {  # base rgb, metallic, roughness
    "BODY": ((0.78, 0.79, 0.80), 0.75, 0.35), "ROOF": ((0.62, 0.63, 0.64), 0.3, 0.5),
    "SKIRT": ((0.16, 0.17, 0.18), 0.2, 0.6), "BAND": ((0.06, 0.07, 0.08), 0.1, 0.35),
    "GLASS": ((0.03, 0.06, 0.08), 0.0, 0.05), "STRIPE": ((0.0, 0.42, 0.46), 0.1, 0.4),
    "DOOR": ((0.0, 0.42, 0.46), 0.1, 0.4), "NOSE": ((0.0, 0.42, 0.46), 0.1, 0.35),
    "BOGIE": ((0.10, 0.10, 0.11), 0.6, 0.6), "WHEEL": ((0.35, 0.35, 0.36), 0.9, 0.4),
    "RUBBER": ((0.03, 0.03, 0.03), 0.0, 0.9), "EQUIP": ((0.13, 0.14, 0.15), 0.3, 0.6),
    "LIGHT": ((1.0, 0.97, 0.88), 0.0, 0.1), "TAIL": ((0.9, 0.05, 0.03), 0.0, 0.2),
    "SIGN": ((0.01, 0.01, 0.01), 0.0, 0.3), "FLOOR": ((0.35, 0.36, 0.37), 0.0, 0.8),
    "SEAT": ((0.05, 0.30, 0.34), 0.0, 0.7), "POLE": ((0.85, 0.85, 0.86), 1.0, 0.2),
    "INTERIOR": ((0.86, 0.87, 0.88), 0.0, 0.6),
}
MAT = {}
for k, (rgb, met, rough) in PAL.items():
    m = bpy.data.materials.new("M_" + k); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Metallic"].default_value = met
    b.inputs["Roughness"].default_value = rough
    if k in ("LIGHT", "TAIL"):
        b.inputs["Emission Color"].default_value = (*rgb, 1); b.inputs["Emission Strength"].default_value = 3.0
    m.diffuse_color = (*rgb, 1)
    MAT[k] = m

def mat_for(key):
    for p in ("DOORGLASS", "DOOR", "WINDSCREEN"):
        if key.startswith(p): return MAT["GLASS"] if "GLASS" in p or p == "WINDSCREEN" else MAT["DOOR"]
    return MAT.get(key, MAT["BODY"])

# ---------------------------------------------------------------- geometry constants
HALF_W = 1.505
ZS = [1.00, 1.40, 1.55, 1.90, 2.20, 2.60, 2.95, 3.00, 3.30]
_right = [(1.47, 0.90)] + [(HALF_W, z) for z in ZS]
for t in (18, 36, 54, 72):
    a = math.radians(t); _right.append((HALF_W * (math.cos(a) ** 0.45), 3.30 + 0.42 * math.sin(a)))
PROFILE = [(-y, z) for (y, z) in _right] + [(0.0, 3.72)] + [(y, z) for (y, z) in reversed(_right)]
DOORS = [-8.8, -4.4, 0.0, 4.4, 8.8]
DW, DG0, DG1 = 0.70, 0.12, 0.58
BOGIE_X = 7.85
BODY_X0, BODY_X1 = -11.0, 11.0
NOSE = [(11.00, 1.00, 1.00), (11.30, 0.99, 0.975), (11.58, 0.955, 0.84), (11.80, 0.89, 0.60), (11.92, 0.82, 0.47)]

def windows(cab):
    w = [(a + 1.0, b - 1.0) for a, b in zip(DOORS[:-1], DOORS[1:])] + [(-10.55, -9.80)]
    if not cab: w.append((9.80, 10.55))
    return w

def xbreaks(cab):
    xs = {BODY_X0, BODY_X1}
    for c in DOORS: xs |= {c - DW, c - DG1, c - DG0, c, c + DG0, c + DG1, c + DW}
    for a, b in windows(cab): xs |= {a, b}
    return sorted(xs)

def classify(xc, yc, zc, cab, nose):
    side = "L" if yc > 0 else "R"
    if zc < 1.0: return "SKIRT"
    if nose:
        if 2.15 < zc < 3.55 and abs(yc) < 1.30: return "WINDSCREEN"
        return "ROOF" if zc > 3.55 else "NOSE"
    if zc > 3.30: return "ROOF"
    if abs(yc) > 1.4:
        for i, c in enumerate(DOORS):
            if abs(xc - c) < DW and zc < 3.0:
                leaf = "a" if xc < c else "b"
                if DG0 < abs(xc - c) < DG1 and 1.90 < zc < 2.75: return f"DOORGLASS_{side}{i + 1}{leaf}"
                return f"DOOR_{side}{i + 1}{leaf}"
        if 1.90 < zc < 2.95:
            return "GLASS" if any(a < xc < b for a, b in windows(cab)) else "BAND"
        if 1.40 < zc < 1.55: return "STRIPE"
    return "BODY"

# ---------------------------------------------------------------- helpers
def new_obj(name, verts, faces, key, coll, parent, solid=0.0):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    me.materials.append(mat_for(key))
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob); ob.parent = parent
    if solid:
        md = ob.modifiers.new("Solidify", "SOLIDIFY"); md.thickness = solid; md.offset = -1.0
    return ob

def faces_to_obj(name, flist, key, coll, parent, solid):
    vmap, verts, faces = {}, [], []
    for f in flist:
        idx = []
        for v in f:
            kk = (round(v[0], 5), round(v[1], 5), round(v[2], 5))
            if kk not in vmap: vmap[kk] = len(verts); verts.append(v)
            idx.append(vmap[kk])
        faces.append(idx)
    return new_obj(name, verts, faces, key, coll, parent, solid)

def orient(f, outward):
    a, b, c = Vector(f[0]), Vector(f[1]), Vector(f[2])
    n = (b - a).cross(c - a)
    return f if n.dot(outward) >= 0 else list(reversed(f))

def box(name, key, cx, cy, cz, sx, sy, sz, coll, parent):
    x0, x1, y0, y1, z0, z1 = cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return new_obj(name, v, f, key, coll, parent)

def cyl(name, key, center, radius, depth, axis, coll, parent, seg=16):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=radius, radius2=radius, depth=depth)
    rot = {"x": ((0, 1, 0), math.pi / 2), "y": ((1, 0, 0), math.pi / 2), "z": ((0, 0, 1), 0)}[axis]
    from mathutils import Matrix
    bmesh.ops.rotate(bm, verts=bm.verts, matrix=Matrix.Rotation(rot[1], 4, rot[0]))
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(center))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(MAT[key])
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob); ob.parent = parent
    return ob

def join(objs, name):
    if not objs: return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join(); objs[0].name = name; objs[0].data.name = name
    return objs[0]

# ---------------------------------------------------------------- car builder
def build_car(kind):
    """kind: 'CAB' (driving trailer w/ cab at +X), 'MID' (intermediate), 'MIDP' (intermediate with pantograph)."""
    cab = kind == "CAB"
    coll = bpy.data.collections.new("Car_" + kind); bpy.context.scene.collection.children.link(coll)
    root = bpy.data.objects.new(kind, None); coll.objects.link(root); root.empty_display_size = 2
    P = f"{kind}_"
    # --- body shell: sections x profile
    secs = [(x, 1.0, 1.0, False) for x in xbreaks(cab)]
    if cab: secs += [(x, sy, sz, True) for (x, sy, sz) in NOSE[1:]]
    pts = [[(x, y * sy, 0.9 + (z - 0.9) * sz) for (y, z) in PROFILE] for (x, sy, sz, _) in secs]
    groups = {}
    for i in range(len(secs) - 1):
        nose = secs[i + 1][3]
        for j in range(len(PROFILE) - 1):
            f = [pts[i][j], pts[i + 1][j], pts[i + 1][j + 1], pts[i][j + 1]]
            c = Vector([sum(v[k] for v in f) / 4 for k in range(3)])
            f = orient(f, Vector((0 if not nose else 0.6, c.y, c.z - 2.3)))
            key = classify(c.x, c.y, c.z, cab, nose)
            if key.startswith("DOOR"):  # 16 mm seam between the two leaves
                dc = DOORS[int(key[-2]) - 1]
                f = [(dc + math.copysign(max(abs(v[0] - dc), 0.008), v[0] - dc if abs(v[0] - dc) > 1e-6 else c.x - dc), v[1], v[2]) for v in f]
            groups.setdefault(key, []).append(f)
    # end caps
    rear = pts[0]; groups.setdefault("BODY", []).append(orient(list(rear), Vector((-1, 0, 0))))
    front = pts[-1]; groups.setdefault("NOSE" if cab else "BODY", []).append(orient(list(front), Vector((1, 0, 0))))
    parts = {}
    for key, fl in groups.items():
        solid = 0.04 if key.startswith("DOOR") and "GLASS" not in key else (0.012 if "GLASS" in key or key == "WINDSCREEN" else 0.05)
        parts[key] = faces_to_obj(P + key, fl, key, coll, root, solid)
    # --- underframe, floor, couplers, gangways
    box(P + "Underplate", "SKIRT", 0, 0, 0.905, 22.0, 2.94, 0.01, coll, root)
    box(P + "Floor", "FLOOR", 0, 0, 1.025, 21.9, 2.92, 0.05, coll, root)
    eq = []
    for x0, x1, w in ((-5.9, -3.2, 2.2), (-2.9, -0.6, 2.4), (-0.3, 2.6, 2.2), (2.9, 5.9, 2.4)):
        eq.append(box(P + "eq", "EQUIP", (x0 + x1) / 2, 0, 0.62, x1 - x0, w, 0.52, coll, root))
    join(eq, P + "Equipment")
    rear_x = BODY_X0
    box(P + "Coupler_R", "BOGIE", rear_x - 0.12, 0, 0.92, 0.26, 0.3, 0.25, coll, root)
    box(P + "Gangway_R", "RUBBER", rear_x - 0.06, 0, 2.05, 0.12, 1.3, 2.1, coll, root)
    if cab:
        box(P + "Coupler_F", "BOGIE", 12.04, 0, 0.92, 0.26, 0.3, 0.25, coll, root)
        pv = [(11.55, -1.35, 0.90), (11.55, 1.35, 0.90), (11.80, 1.30, 0.90), (11.80, -1.30, 0.90),
              (11.62, -1.10, 0.22), (11.62, 1.10, 0.22), (12.02, 0.95, 0.22), (12.02, -0.95, 0.22)]
        new_obj(P + "Plough", pv, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], "SKIRT", coll, root)
        for s in (-1, 1):
            box(P + f"Headlight_{'L' if s > 0 else 'R'}", "LIGHT", 11.925, s * 0.92, 1.42, 0.02, 0.38, 0.14, coll, root)
            box(P + f"Taillight_{'L' if s > 0 else 'R'}", "TAIL", 11.925, s * 0.92, 1.25, 0.02, 0.38, 0.08, coll, root)
        box(P + "DestinationSign", "SIGN", 11.28, 0, 3.45, 0.04, 1.7, 0.22, coll, root)
    else:
        box(P + "Coupler_F", "BOGIE", BODY_X1 + 0.12, 0, 0.92, 0.26, 0.3, 0.25, coll, root)
        box(P + "Gangway_F", "RUBBER", BODY_X1 + 0.06, 0, 2.05, 0.12, 1.3, 2.1, coll, root)
    # --- roof equipment (height limit 3.85 m)
    box(P + "RoofAC", "ROOF", -3.0 if cab else 5.0, 0, 3.775, 3.6, 1.9, 0.13, coll, root)
    if kind == "MIDP":
        box(P + "Panto_Base", "EQUIP", -6.6, 0, 3.78, 1.6, 1.4, 0.12, coll, root)
        lower = box(P + "Panto_Lower", "POLE", -6.0, 0, 3.90, 1.6, 0.08, 0.05, coll, root)   # hinge at x=-6.8
        upper = box(P + "Panto_Upper", "POLE", -6.0, 0, 3.97, 1.5, 0.06, 0.04, coll, root)   # hinge at x=-5.2
        head = box(P + "Panto_Head", "EQUIP", -6.75, 0, 4.03, 0.25, 1.8, 0.05, coll, root)
        for o in (lower, upper, head): o["hinge_note"] = "animate in Roblox: lower pivots at x=-6.8, upper at x=-5.2"
    # --- bogies with primary/secondary suspension
    for tag, bx in (("F", BOGIE_X), ("R", -BOGIE_X)):
        fr = []
        for s in (-1, 1):
            fr.append(box(P + "bf", "BOGIE", bx, s * 1.0, 0.56, 2.9, 0.22, 0.32, coll, root))       # side frame
            for ax in (-1.25, 1.25):
                fr.append(box(P + "bf", "BOGIE", bx + ax, s * 1.0, 0.43, 0.38, 0.26, 0.26, coll, root))  # axle box
                fr.append(cyl(P + "bf", "EQUIP", (bx + ax, s * 1.0, 0.66), 0.09, 0.22, "z", coll, root, 10))  # primary spring
        fr.append(box(P + "bf", "BOGIE", bx, 0, 0.58, 0.55, 2.0, 0.26, coll, root))                   # transom
        if kind != "CAB":
            fr.append(box(P + "bf", "EQUIP", bx + 0.62, 0, 0.45, 0.55, 1.2, 0.36, coll, root))        # traction motor
        join(fr, P + f"Bogie_{tag}")
        air = [cyl(P + "as", "RUBBER", (bx, s * 1.0, 0.81), 0.27, 0.17, "z", coll, root, 16) for s in (-1, 1)]
        join(air, P + f"AirSpring_{tag}")
        for k, ax in enumerate((-1.25, 1.25)):
            ws = [cyl(P + "w", "WHEEL", (bx + ax, s * 0.7525, 0.43), 0.43, 0.135, "y", coll, root, 24) for s in (-1, 1)]
            ws.append(cyl(P + "w", "WHEEL", (bx + ax, 0, 0.43), 0.085, 1.62, "y", coll, root, 10))
            join(ws, P + f"Wheelset_{tag}{k + 1}")
    # --- interior: longitudinal benches between doors, grab poles, ceiling
    seats, poles = [], []
    for a, b in windows(cab):
        for s in (-1, 1):
            seats.append(box(P + "s", "SEAT", (a + b) / 2, s * 1.25, 1.50, b - a - 0.1, 0.45, 0.10, coll, root))
            seats.append(box(P + "s", "SEAT", (a + b) / 2, s * 1.43, 1.80, b - a - 0.1, 0.08, 0.55, coll, root))
    for c in DOORS:
        for s in (-1, 1):
            poles.append(cyl(P + "p", "POLE", (c, s * 0.75, 2.05), 0.02, 2.0, "z", coll, root, 8))
    join(seats, P + "Seats"); join(poles, P + "Poles")
    box(P + "Ceiling", "INTERIOR", 0, 0, 3.12, 21.9, 2.8, 0.03, coll, root)
    if cab:
        box(P + "CabWall", "INTERIOR", 10.15, 0, 2.05, 0.06, 2.9, 2.0, coll, root)
        box(P + "CabDesk", "EQUIP", 10.95, 0, 1.75, 0.55, 2.2, 0.35, coll, root)
    root["car_kind"] = kind; root["length_m"] = 22.5
    return root

CARS = {k: build_car(k) for k in ("CAB", "MID", "MIDP")}
# preview 5-car formation: CAB(rev) - MID - MIDP - MID - CAB
spacing = 22.5
CARS["CAB"].location = (2 * spacing, 0, 0)
CARS["MID"].location = (spacing, 0, 0)
CARS["MIDP"].location = (0, 0, 0)
inst = []
for name, x, rot in (("MID", -spacing, 0), ("CAB", -2 * spacing, math.pi)):
    e = bpy.data.objects.new(f"Preview_{name}_{len(inst)}", None)
    e.instance_type = "COLLECTION"; e.instance_collection = bpy.data.collections["Car_" + name]
    e.location = (x - CARS[name].location.x, 0, 0) if False else (x, 0, 0); e.rotation_euler = (0, 0, rot)
    bpy.context.scene.collection.objects.link(e); inst.append(e)
# instance offset: collection instance uses collection origin (0,0,0) -> shift by root location
for e in inst:
    src = CARS[e.name.split("_")[1]]
    e.location.x -= src.location.x * (1 if e.rotation_euler.z == 0 else -1)
# ground rails for reference
rc = bpy.data.collections.new("Reference"); bpy.context.scene.collection.children.link(rc)
for s in (-1, 1): box(f"Rail_{s}", "WHEEL", 0, s * 0.7525, 0.0 - 0.085, 130, 0.07, 0.17, rc, None)
tris = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == "MESH")
print("built", {k: len([o for o in bpy.data.collections['Car_' + k].objects]) for k in CARS}, "faces", tris)
