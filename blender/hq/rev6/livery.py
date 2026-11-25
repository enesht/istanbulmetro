"""Rev 6 - livery module (colour layout).
* PBR_Livery_Procedural : object-space procedural paint for body/doors/cab (source for the atlas bake)
* CC_DecalProject        : Geometry-Nodes group that turns a 2D Bezier curve (or a text object) into a paint decal
                           projected onto CC_Ref_Exterior along the curve object's local -Z (live, non-destructive)
* Paint objects (collection CC_Paint): CC_Paint_Mask, CC_Paint_MaskOutline, CC_Paint_Crown_L/_R (R = mirrored twin)
* Destination display: CC_Dest_Panel (dark LED field) + CC_Dest_Text (editable text, orange dot-matrix)
Edit the Bezier points of a paint curve in Edit Mode -> the decal updates immediately."""
import bpy, math
from mathutils import Vector, Matrix
from common import G, pi, coll, remove, mat, mat_pbr, prop, drive, mirror_parent, mirror_twin, frame_front, frame_side_left, set_gn_input

PAL = {"WHITE": (0.88, 0.885, 0.88), "RED": (0.578, 0.0052, 0.0273), "NAVY": (0.0070, 0.0242, 0.162),
       "DARK": (0.0152, 0.0168, 0.016), "ROOF": (0.30, 0.30, 0.31), "BLACK": (0.0032, 0.0032, 0.004)}
LIV = {"XC": 8.995, "XP": 9.40, "RAKE": 0.404, "NAVY": (1.20, 1.02, 42.0, 60.0), "RED_LOW": (1.68, 1.80, 56.0),
       "CANT": (3.20, 3.26, 10.12), "BAND": (1.86, 3.06, 66.0), "ROOF_Z": 3.30}


# ================================================================== procedural body paint
class _NB:
    def __init__(s, nt): s.nt = nt; s.x = 0
    def _n(s, typ):
        n = s.nt.nodes.new(typ); n.location = (s.x, 0); s.x += 20; return n
    def _set(s, sock, v):
        if isinstance(v, (int, float)): sock.default_value = v
        elif isinstance(v, tuple): sock.default_value = v if len(v) == 4 else (*v, 1.0)
        else: s.nt.links.new(v, sock)
    def m(s, op, a, b=None):
        n = s._n("ShaderNodeMath"); n.operation = op; s._set(n.inputs[0], a)
        if b is not None: s._set(n.inputs[1], b)
        return n.outputs[0]
    def ss(s, e0, e1, v):
        n = s._n("ShaderNodeMapRange"); n.interpolation_type = "SMOOTHSTEP"; n.clamp = True
        s._set(n.inputs[0], v); s._set(n.inputs[1], e0); s._set(n.inputs[2], e1); s._set(n.inputs[3], 0.0); s._set(n.inputs[4], 1.0)
        return n.outputs[0]
    def edge(s, v, eps=0.0015): return s.ss(-eps, eps, v)
    def lerp(s, a, b, f):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)): return s.m("ADD", a, s.m("MULTIPLY", b - a, f))
        return s.m("ADD", a, s.m("MULTIPLY", s.m("SUBTRACT", b, a), f))
    def cmix(s, a, b, f):
        n = s._n("ShaderNodeMix"); n.data_type = "RGBA"; n.blend_type = "MIX"; n.clamp_factor = True
        ins = {i.identifier: i for i in n.inputs}
        s._set(ins["Factor_Float"], f); s._set(ins["A_Color"], a); s._set(ins["B_Color"], b)
        return [o for o in n.outputs if o.identifier == "Result_Color"][0]

def procedural_livery():
    """stripes, window band, roof, brushed stainless; the mask and the cab crown are separate paint objects now."""
    old = mat("PBR_Livery_Body")
    m = mat("PBR_Livery_Procedural")
    if m: bpy.data.materials.remove(m)
    m = bpy.data.materials.new("PBR_Livery_Procedural"); m.use_nodes = True; m.use_fake_user = True; nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF"); B = _NB(nt)
    tc = B._n("ShaderNodeTexCoord"); sp = B._n("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sp.inputs[0])
    x, y, z = sp.outputs[0], sp.outputs[1], sp.outputs[2]
    ay = B.m("ABSOLUTE", y)
    xr = B.m("ADD", x, B.m("MULTIPLY", LIV["RAKE"], B.m("MAXIMUM", B.m("SUBTRACT", z, 2.2), 0.0)))
    phi = B.m("MULTIPLY", B.m("ARCTAN2", ay, B.m("SUBTRACT", xr, LIV["XP"])), 57.29578)
    cab = B.edge(B.m("SUBTRACT", x, LIV["XC"]), 0.002)
    mp = B._n("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.8, 420.0, 420.0); nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = B._n("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 6.0
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"]); grain = nz.outputs["Fac"]
    scol = B.cmix((0.455, 0.46, 0.468), (0.56, 0.565, 0.572), B.ss(0.3, 0.7, grain))
    srgh = B.lerp(0.20, 0.38, B.ss(0.25, 0.75, grain))
    col = B.cmix(scol, PAL["WHITE"], cab); met = B.lerp(0.92, 0.0, cab); rgh = B.lerp(srgh, 0.20, cab); cot = B.lerp(0.0, 0.8, cab); spc = 0.5
    def layer(mask, c, mt, rg, ct, sp_=0.5):
        nonlocal col, met, rgh, cot, spc
        col = B.cmix(col, PAL[c], mask); met = B.lerp(met, mt, mask); rgh = B.lerp(rgh, rg, mask); cot = B.lerp(cot, ct, mask); spc = B.lerp(spc, sp_, mask)
    def zband(z0, z1): return B.m("MULTIPLY", B.edge(B.m("SUBTRACT", z, z0)), B.m("SUBTRACT", 1.0, B.edge(B.m("SUBTRACT", z, z1))))
    def phicut(p): return B.ss(p - 0.08, p + 0.08, phi)
    layer(B.m("MULTIPLY", B.edge(B.m("SUBTRACT", z, LIV["ROOF_Z"])), B.m("SUBTRACT", 1.0, cab)), "ROOF", 0.0, 0.50, 0.15, 0.45)
    ns, nf, p0, p1 = LIV["NAVY"]
    znt = B.m("SUBTRACT", ns, B.m("MULTIPLY", ns - nf, B.m("SUBTRACT", 1.0, B.ss(p0, p1, phi))))
    layer(B.m("SUBTRACT", 1.0, B.edge(B.m("SUBTRACT", z, znt))), "NAVY", 0.0, 0.34, 0.25, 0.32)
    r0, r1, rp = LIV["RED_LOW"]; c0, c1, ce = LIV["CANT"]
    xend = B.m("SUBTRACT", ce, B.m("MULTIPLY", LIV["RAKE"], B.m("SUBTRACT", z, 3.12)))
    cant = B.m("MULTIPLY", zband(c0, c1), B.m("SUBTRACT", 1.0, B.edge(B.m("SUBTRACT", x, xend), 0.002)))
    layer(B.m("MAXIMUM", B.m("MULTIPLY", zband(r0, r1), phicut(rp)), cant), "RED", 0.0, 0.30, 0.25, 0.32)
    b0, b1, bp = LIV["BAND"]
    layer(B.m("MULTIPLY", zband(b0, b1), phicut(bp)), "DARK", 0.0, 0.45, 0.10, 0.28)
    nt.links.new(col, bsdf.inputs["Base Color"]); nt.links.new(met, bsdf.inputs["Metallic"]); nt.links.new(rgh, bsdf.inputs["Roughness"])
    nt.links.new(cot, bsdf.inputs["Coat Weight"]); nt.links.new(spc, bsdf.inputs["Specular IOR Level"])
    bsdf.inputs["Coat Roughness"].default_value = 0.035
    m.diffuse_color = (0.6, 0.6, 0.6, 1)
    if old:
        old.user_remap(m); bpy.data.materials.remove(old)
    return m


# ================================================================== decal Geometry-Nodes group
def _sock(node, *names):
    for nm in names:
        if nm in node.inputs: return node.inputs[nm]
    raise KeyError(f"{node.bl_idname}: none of {names} in {[i.name for i in node.inputs]}")
def _out(node, *names):
    for nm in names:
        if nm in node.outputs: return node.outputs[nm]
    raise KeyError(f"{node.bl_idname}: none of {names} in {[o.name for o in node.outputs]}")

def decal_group(name="CC_DecalProject", outline=False, mesh_input=False):
    ng = bpy.data.node_groups.get(name)
    if ng: bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree"); ng.use_fake_user = True
    itf = ng.interface
    itf.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    s_t = itf.new_socket("Target", in_out="INPUT", socket_type="NodeSocketObject")
    s_o = itf.new_socket("Offset", in_out="INPUT", socket_type="NodeSocketFloat"); s_o.default_value = 0.0015
    s_l = itf.new_socket("Segment Length", in_out="INPUT", socket_type="NodeSocketFloat"); s_l.default_value = 0.012; s_l.min_value = 0.002
    s_s = itf.new_socket("Subdivisions", in_out="INPUT", socket_type="NodeSocketInt"); s_s.default_value = 3; s_s.min_value = 0; s_s.max_value = 6
    s_r = itf.new_socket("Ray Length", in_out="INPUT", socket_type="NodeSocketFloat"); s_r.default_value = 6.0
    if outline:
        s_w = itf.new_socket("Width", in_out="INPUT", socket_type="NodeSocketFloat"); s_w.default_value = 0.025
    itf.new_socket("Material", in_out="INPUT", socket_type="NodeSocketMaterial")
    itf.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    rs = N.new("GeometryNodeResampleCurve")
    try: rs.mode = "LENGTH"
    except Exception: pass
    if "Mode" in rs.inputs:
        try: rs.inputs["Mode"].default_value = "Length"
        except Exception: pass
    L.new(gi.outputs["Geometry"], _sock(rs, "Curve")); L.new(gi.outputs["Segment Length"], _sock(rs, "Length"))
    if mesh_input:
        mesh_out = gi.outputs["Geometry"]
    elif outline:
        line = N.new("GeometryNodeCurvePrimitiveLine")
        half = N.new("ShaderNodeMath"); half.operation = "MULTIPLY"; half.inputs[1].default_value = 0.5; L.new(gi.outputs["Width"], half.inputs[0])
        neg = N.new("ShaderNodeMath"); neg.operation = "MULTIPLY"; neg.inputs[1].default_value = -1.0; L.new(half.outputs[0], neg.inputs[0])
        a = N.new("ShaderNodeCombineXYZ"); L.new(neg.outputs[0], a.inputs[0]); b = N.new("ShaderNodeCombineXYZ"); L.new(half.outputs[0], b.inputs[0])
        L.new(a.outputs[0], _sock(line, "Start")); L.new(b.outputs[0], _sock(line, "End"))
        c2m = N.new("GeometryNodeCurveToMesh"); L.new(rs.outputs[0], _sock(c2m, "Curve")); L.new(line.outputs[0], _sock(c2m, "Profile Curve"))
        mesh_out = c2m.outputs[0]
    else:
        fill = N.new("GeometryNodeFillCurve")
        try: fill.mode = "TRIANGLES"
        except Exception: pass
        L.new(rs.outputs[0], _sock(fill, "Curve")); mesh_out = fill.outputs[0]
    sub = N.new("GeometryNodeSubdivideMesh"); L.new(mesh_out, _sock(sub, "Mesh")); L.new(gi.outputs["Subdivisions"], _sock(sub, "Level"))
    oi = N.new("GeometryNodeObjectInfo"); oi.transform_space = "RELATIVE"; L.new(gi.outputs["Target"], _sock(oi, "Object"))
    pos = N.new("GeometryNodeInputPosition")
    ray = N.new("GeometryNodeRaycast")
    L.new(_out(oi, "Geometry"), _sock(ray, "Target Geometry")); L.new(pos.outputs[0], _sock(ray, "Source Position"))
    _sock(ray, "Ray Direction").default_value = (0.0, 0.0, -1.0); L.new(gi.outputs["Ray Length"], _sock(ray, "Ray Length"))
    hitp, hitn, ishit = _out(ray, "Hit Position"), _out(ray, "Hit Normal"), _out(ray, "Is Hit")
    # orient the hit normal against the ray (robust to face winding)
    dot = N.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"; L.new(hitn, dot.inputs[0]); dot.inputs[1].default_value = (0, 0, -1)
    sgn = N.new("ShaderNodeMath"); sgn.operation = "SIGN"; L.new(_out(dot, "Value"), sgn.inputs[0])
    neg = N.new("ShaderNodeMath"); neg.operation = "MULTIPLY"; L.new(sgn.outputs[0], neg.inputs[0]); neg.inputs[1].default_value = -1.0
    k = N.new("ShaderNodeMath"); k.operation = "MULTIPLY"; L.new(neg.outputs[0], k.inputs[0]); L.new(gi.outputs["Offset"], k.inputs[1])
    sc = N.new("ShaderNodeVectorMath"); sc.operation = "SCALE"; L.new(hitn, sc.inputs[0]); L.new(k.outputs[0], _sock(sc, "Scale"))
    add = N.new("ShaderNodeVectorMath"); add.operation = "ADD"; L.new(hitp, add.inputs[0]); L.new(_out(sc, "Vector"), add.inputs[1])
    setp = N.new("GeometryNodeSetPosition"); L.new(sub.outputs[0], _sock(setp, "Geometry")); L.new(ishit, _sock(setp, "Selection")); L.new(_out(add, "Vector"), _sock(setp, "Position"))
    notn = N.new("FunctionNodeBooleanMath"); notn.operation = "NOT"; L.new(ishit, notn.inputs[0])
    dele = N.new("GeometryNodeDeleteGeometry"); dele.domain = "POINT"; L.new(setp.outputs[0], _sock(dele, "Geometry")); L.new(notn.outputs[0], _sock(dele, "Selection"))
    smo = N.new("GeometryNodeSetShadeSmooth"); L.new(dele.outputs[0], _sock(smo, "Geometry", "Mesh"))
    sm = N.new("GeometryNodeSetMaterial"); L.new(smo.outputs[0], _sock(sm, "Geometry")); L.new(gi.outputs["Material"], _sock(sm, "Material"))
    L.new(sm.outputs[0], go.inputs[0])
    return ng

def _apply_decal_mod(ob, ng, target, material, offset=0.0015, seg=0.012, subdiv=3, width=None):
    for md in list(ob.modifiers): ob.modifiers.remove(md)
    md = ob.modifiers.new("Decal", "NODES"); md.node_group = ng
    vals = {"Target": target, "Offset": offset, "Segment Length": seg, "Subdivisions": subdiv, "Material": material, "Width": width}
    for it in ng.interface.items_tree:
        if getattr(it, "in_out", "") != "INPUT" or vals.get(it.name) is None: continue
        set_gn_input(md, it.identifier, vals[it.name])
    return md


# ================================================================== paint curves
def _bezier_curve(name, pts2d, collection, matrix, cyclic=True, handle="AUTO"):
    remove(name)
    cd = bpy.data.curves.new(name, "CURVE"); cd.dimensions = "2D"; cd.fill_mode = "NONE"
    sp = cd.splines.new("BEZIER"); sp.bezier_points.add(len(pts2d) - 1); sp.use_cyclic_u = cyclic
    for bp, (u, v) in zip(sp.bezier_points, pts2d):
        bp.co = (u, v, 0.0); bp.handle_left_type = handle; bp.handle_right_type = handle
    ob = bpy.data.objects.new(name, cd); collection.objects.link(ob); ob.matrix_world = matrix
    return ob

def _set_vector_handles(ob, idx):
    sp = ob.data.splines[0]
    for i in idx:
        bp = sp.bezier_points[i]; bp.handle_left_type = "VECTOR"; bp.handle_right_type = "VECTOR"

def mask_outline_points(n=28):
    """the black mask outline (front view y, z) as Bezier anchors on geom's tapered superellipse."""
    return [(y, z) for (y, z) in G.mask_loop(0.0, n)]

def crown_points():
    """left-side cab crown (side view u = -x, z). Runs from the thin cant stripe up over the roof shoulder,
    front edge raked parallel to the windscreen."""
    pts = [(8.70, 3.200), (9.05, 3.175), (9.40, 3.120), (10.12, 3.120), (9.90, 3.700), (9.62, 3.700), (9.30, 3.560), (8.95, 3.360), (8.70, 3.260)]
    return [(-x, z) for (x, z) in pts]

# ---- paint panels: editable Bezier sources -> conforming decal meshes (constrained Delaunay + surface projection)
PAINT = {   # source curve: output, material, offset (m), interior point spacing (m), mirrored twin, outline width
    "CC_PaintSrc_Mask":  {"out": "CC_Paint_Mask", "mat": "PAINT_MaskBlack", "offset": 0.0012, "spacing": 0.022, "mirror": False, "outline": ("CC_Paint_MaskOutline", "PAINT_MaskOutlineWhite", 0.030, 0.0016)},
    "CC_PaintSrc_Crown": {"out": "CC_Paint_Crown", "mat": "PAINT_Red_PMS186", "offset": 0.0012, "spacing": 0.014, "mirror": True, "outline": None},
}

def _src_polygon(src, step):
    """evaluated outline of a cyclic Bezier source curve in its local XY plane, resampled to ~step."""
    dg = bpy.context.evaluated_depsgraph_get(); ev = src.evaluated_get(dg)
    cd = src.data; old = cd.resolution_u; cd.resolution_u = 24
    me = bpy.data.meshes.new_from_object(src.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    cd.resolution_u = old
    # walk the edge loop
    nb = {}
    for e in me.edges:
        a, b = e.vertices; nb.setdefault(a, []).append(b); nb.setdefault(b, []).append(a)
    start = 0; loop = [start]; prev = None; cur = start
    while True:
        nxt = [n for n in nb.get(cur, []) if n != prev]
        if not nxt: break
        prev, cur = cur, nxt[0]
        if cur == start: break
        loop.append(cur)
    pts = [Vector((me.vertices[i].co.x, me.vertices[i].co.y)) for i in loop]
    bpy.data.meshes.remove(me)
    out = []
    for p, q in zip(pts, pts[1:] + pts[:1]):
        n = max(1, int((q - p).length / step))
        for k in range(n): out.append(p.lerp(q, k / n))
    area = sum(p.x * q.y - q.x * p.y for p, q in zip(out, out[1:] + out[:1]))
    return out if area > 0 else out[::-1]

def _inside(pt, poly):
    x, y = pt; c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c

def _cdt(poly, spacing):
    from mathutils.geometry import delaunay_2d_cdt
    xs = [p.x for p in poly]; ys = [p.y for p in poly]; pts = [tuple(p) for p in poly]
    inner = []
    gx = int((max(xs) - min(xs)) / spacing) + 1; gy = int((max(ys) - min(ys)) / spacing) + 1
    for i in range(gx + 1):
        for j in range(gy + 1):
            q = (min(xs) + i * spacing + (0.5 * spacing if j % 2 else 0.0), min(ys) + j * spacing * 0.866)
            if not _inside(q, pts): continue
            if min((Vector(q) - p).length for p in poly[::max(1, len(poly) // 400)]) < spacing * 0.6: continue
            inner.append(q)
    verts = pts + inner; n = len(pts)
    res = delaunay_2d_cdt([Vector(v) for v in verts], [(i, (i + 1) % n) for i in range(n)], [list(range(n))], 2, 1e-7)
    return [tuple(v) for v in res[0]], [list(f) for f in res[2]]

def _project(src, uv, caster, offset):
    M = src.matrix_world; d = (M.to_3x3() @ Vector((0, 0, -1))).normalized(); out = []
    for (u, v) in uv:
        o = M @ Vector((u, v, 0.0)); l, n = caster.cast(o, d)
        out.append(tuple(l + n * offset) if l is not None else None)
    return out

def _mesh_from(name, verts, faces, m, c, mirror=False):
    keep = [i for i, v in enumerate(verts) if v is not None]; remap = {o: k for k, o in enumerate(keep)}
    vv = [verts[i] for i in keep]; ff = [[remap[i] for i in f] for f in faces if all(verts[i] is not None for i in f)]
    if mirror: vv = [(x, -y, z) for (x, y, z) in vv]; ff = [f[::-1] for f in ff]
    from common import mk
    ob = mk(name, vv, ff, [m], c)
    return ob

def _ribbon(poly, w):
    n = len(poly); inner, outer = [], []
    for i in range(n):
        t = (poly[(i + 1) % n] - poly[i - 1]).normalized(); nrm = Vector((t.y, -t.x))
        inner.append(tuple(poly[i] - nrm * w / 2)); outer.append(tuple(poly[i] + nrm * w / 2))
    return inner + outer, [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]

def paint_sources():
    cp = coll("CC_Paint_Sources")
    s1 = _bezier_curve("CC_PaintSrc_Mask", mask_outline_points(28), cp, frame_front(12.0))
    s2 = _bezier_curve("CC_PaintSrc_Crown", crown_points(), cp, frame_side_left(2.6)); _set_vector_handles(s2, [2, 3, 4, 5])
    for s in (s1, s2): s.hide_render = True; s["note"] = "edit the Bezier points, then run livery.update_paint()"
    return s1, s2

def update_paint(only=None):
    """(re)generate CC_Paint_* meshes from the CC_PaintSrc_* Bezier curves."""
    from common import Caster
    cp = coll("CC_Paint"); caster = Caster(bpy.data.objects["CC_Ref_Exterior"]); made = []
    mats = {"PAINT_MaskBlack": mat_pbr("PAINT_MaskBlack", PAL["BLACK"], rough=0.12, coat=0.8),
            "PAINT_MaskOutlineWhite": mat_pbr("PAINT_MaskOutlineWhite", (0.92, 0.925, 0.92), rough=0.15, coat=0.9),
            "PAINT_Red_PMS186": mat_pbr("PAINT_Red_PMS186", PAL["RED"], rough=0.30, coat=0.35, spec=0.32)}
    for sname, cfg in PAINT.items():
        if only and sname not in only: continue
        src = bpy.data.objects.get(sname)
        if src is None: continue
        poly = _src_polygon(src, cfg["spacing"] * 0.5)
        uv, faces = _cdt(poly, cfg["spacing"])
        verts = _project(src, uv, caster, cfg["offset"])
        if cfg["mirror"]:
            made.append(_mesh_from(cfg["out"] + "_L", verts, faces, mats[cfg["mat"]], cp))
            made.append(_mesh_from(cfg["out"] + "_R", verts, faces, mats[cfg["mat"]], cp, mirror=True))
        else:
            made.append(_mesh_from(cfg["out"], verts, faces, mats[cfg["mat"]], cp))
        if cfg["outline"]:
            oname, omat, w, off = cfg["outline"]
            rv, rf = _ribbon(poly, w)
            made.append(_mesh_from(oname, _project(src, [(p[0], p[1]) for p in rv], caster, off), rf, mats[omat], cp))
        for o in made[-3:]:
            o["paint_source"] = sname
    for o in made:
        if o.name.startswith("CC_Paint_"):
            flip_out(o)
    return [o.name for o in made]

def flip_out(o):
    import bmesh
    c = Vector((0, 0, 2.2))
    bm = bmesh.new(); bm.from_mesh(o.data); bm.normal_update()
    for f in bm.faces:
        p = f.calc_center_median(); d = Vector((max(p.x - 9.3, 0.0), p.y, p.z - c.z))
        if f.normal.dot(d) < 0: f.normal_flip()
    bm.to_mesh(o.data); bm.free()

def build_paint():
    for n in ("CC_Paint_Mask", "CC_Paint_MaskOutline", "CC_Paint_Crown_L", "CC_Paint_Crown_R"): remove(n)
    paint_sources()
    return update_paint()

def drive_copy(dst, src):
    for i in range(3):
        drive(dst, "location", i, "v", [("v", src, f"location[{i}]")])
        drive(dst, "rotation_euler", i, "v", [("v", src, f"rotation_euler[{i}]")])


# ================================================================== destination display (LED dot matrix, editable text)
def led_material(name, on_rgb=(1.0, 0.42, 0.02), strength=3.0, pitch=0.0055, dot=0.36, base_glow=0.0):
    m = bpy.data.materials.get(name)
    if m: bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1); b.inputs["Roughness"].default_value = 0.25
    tc = nt.nodes.new("ShaderNodeTexCoord"); sc = nt.nodes.new("ShaderNodeVectorMath"); sc.operation = "DIVIDE"
    nt.links.new(tc.outputs["Object"], sc.inputs[0]); sc.inputs[1].default_value = (pitch, pitch, pitch)
    fr = nt.nodes.new("ShaderNodeVectorMath"); fr.operation = "FRACTION"; nt.links.new(sc.outputs[0], fr.inputs[0])
    sub = nt.nodes.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; nt.links.new(fr.outputs[0], sub.inputs[0]); sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    # dots in the display plane (local Y/Z of the car front): ignore X
    mul = nt.nodes.new("ShaderNodeVectorMath"); mul.operation = "MULTIPLY"; nt.links.new(sub.outputs[0], mul.inputs[0]); mul.inputs[1].default_value = (0.0, 1.0, 1.0)
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; nt.links.new(mul.outputs[0], ln.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; nt.links.new(ln.outputs["Value"], lt.inputs[0]); lt.inputs[1].default_value = dot
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    ins = {i.identifier: i for i in mix.inputs}
    nt.links.new(lt.outputs[0], ins["Factor_Float"]); ins["A_Color"].default_value = (base_glow, base_glow * 0.4, 0.0, 1); ins["B_Color"].default_value = (*on_rgb, 1)
    nt.links.new([o for o in mix.outputs if o.identifier == "Result_Color"][0], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = (*on_rgb, 1); m["led_pitch_m"] = pitch
    return m

DEST = {"center_z": 3.315, "half_width": 0.60, "half_height": 0.072, "corner": 0.03, "text": "GEBZE", "text_size": 0.105}

def build_destination_display():
    cf = coll("CabCar_Front"); ref = bpy.data.objects["CC_Ref_Exterior"]; ng = bpy.data.node_groups["CC_DecalProject"]
    for n in ("CC_Dest_Panel", "CC_Dest_Text"): remove(n)
    hw, hh, r, zc = DEST["half_width"], DEST["half_height"], DEST["corner"], DEST["center_z"]
    pts = []
    for (cy, cz, a0) in ((hw - r, -hh + r, -90), (hw - r, hh - r, 0), (-hw + r, hh - r, 90), (-hw + r, -hh + r, 180)):
        for k in range(4):
            a = math.radians(a0 + 90 * k / 3); pts.append((cy + r * math.cos(a), zc + cz + r * math.sin(a)))
    panel = _bezier_curve("CC_Dest_Panel", pts, cf, frame_front(12.0), handle="VECTOR")
    m_off = led_material("LED_DotMatrix_Off", on_rgb=(0.035, 0.02, 0.01), strength=0.0, base_glow=0.0)
    _apply_decal_mod(panel, ng, ref, m_off, offset=0.0024, seg=0.01, subdiv=2)
    td = bpy.data.curves.new("CC_Dest_Text", "FONT"); td.body = DEST["text"]; td.align_x = "CENTER"; td.align_y = "CENTER"; td.size = DEST["text_size"]
    td.space_character = 1.15
    tx = bpy.data.objects.new("CC_Dest_Text", td); cf.objects.link(tx)
    tx.matrix_world = Matrix.Translation((12.0, 0, 0)) @ frame_front(0.0) @ Matrix.Translation((0, zc, 0))
    m_on = led_material("LED_DotMatrix_Orange", on_rgb=(1.0, 0.42, 0.02), strength=3.0)
    ngm = decal_group("CC_DecalProjectMesh", mesh_input=True)
    _apply_decal_mod(tx, ngm, ref, m_on, offset=0.0032, seg=0.004, subdiv=2)
    tx["note"] = "Tab into the text object to change the destination. Font: Object Data > Font."
    return panel, tx
