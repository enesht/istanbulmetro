"""Revision 5 (built on the approved rev-4 nose): one large flush glass over a black mask (clear driver opening + destination
display inside), compact diagonal lamp pods with round optics, panel-jointed apron, refined HVAC units, soft roof wells,
procedural livery (brushed stainless, red cant stripe/cab crown, dark window band, thin navy chin). Original design.
Runs after details3 with V3 = V4 = True."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
pi = math.pi

from mathutils.bvhtree import BVHTree
def nose_ref():
    bm = bmesh.new(); bm.from_mesh(bpy.data.objects["CC_BodyShell"].data); bm.normal_update()
    tree = BVHTree.FromBMesh(bm); bm.free(); return tree
REF = None
def cast(o, d):
    d = Vector(d).normalized(); loc, nor, idx, dist = REF.ray_cast(Vector(o), d)
    if loc is None: return (None, None)
    if nor.dot(d) > 0: nor = -nor
    return (loc, nor)
def on_face(y, z, off=0.0):
    l, n = cast((13.0, y, z), (-1, 0, 0))
    return tuple(l + n * off) if l is not None else (G.x_face(z), y, z)

def rrect_loop(hw, z0, z1, r, seg=8):
    return [(y, z) for (y, z) in [(p[0], p[1]) for p in G.rounded_rect(-hw, hw, z0, z1, r, seg)]]
def rrect_halfwidth(hw, z0, z1, r, z):
    dz = max(z0 + r - z, z - (z1 - r), 0.0)
    return hw - (r - math.sqrt(max(r * r - dz * dz, 0.0))) if dz > 0 else hw

def ws_cutter():
    loop = G.ws_loop(0.0, 96)
    v = [(10.10, y, z) for (y, z) in loop] + [(11.40, y, z) for (y, z) in loop]; n = len(loop)
    f = [list(range(n))[::-1], [n + i for i in range(n)]] + [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    return mk("_WSCutter", v, f, [M["SEAL"]], coll("CabCar_Exterior"), smooth=False)

def apply_cutters(cutters):
    sh = bpy.data.objects["CC_BodyShell"]
    for cut in cutters:
        bm = bmesh.new(); bm.from_mesh(cut.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(cut.data); bm.free()
    cut = join(cutters, "_Cutters")
    md = sh.modifiers.new("Cut", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = cut
    try: md.solver = "EXACT"
    except Exception: pass
    apply_mods(sh); bpy.data.objects.remove(cut, do_unlink=True)
    smooth_by_angle(sh, 35)

def _orient_out(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.normal_update()
    for fc in bm.faces:
        if fc.normal.x < 0: fc.normal_flip()
    bm.to_mesh(ob.data); bm.free()
def ws_panel(name, e, off, mat, c, rows=34, cols=30):
    z0, z1 = G.WS_ZC - G.WS_B - e, G.WS_ZC + G.WS_B + e
    zs = [z0 + (z1 - z0) * (0.5 - 0.5 * math.cos(pi * k / rows)) for k in range(rows + 1)]
    verts = []
    for z in zs:
        w = max(G.ws_halfwidth(min(max(z, z0 + 1e-5), z1 - 1e-5), e), 1e-3)
        for i in range(cols + 1): verts.append(on_face(-w + 2 * w * i / cols, z, off))
    faces = [[k * (cols + 1) + i, k * (cols + 1) + i + 1, (k + 1) * (cols + 1) + i + 1, (k + 1) * (cols + 1) + i] for k in range(rows) for i in range(cols)]
    ob = mk(name, verts, faces, [mat], c); _orient_out(ob)
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(ob.data); bm.free()
    return ob
def ws_ring(name, e_in, e_out, off, mat, c, n=160):
    li = [on_face(y, z, off) for (y, z) in G.ws_loop(e_in, n)]
    lo = [on_face(y, z, off) for (y, z) in G.ws_loop(e_out, n)]
    ob = mk(name, li + lo, [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)], [mat], c); _orient_out(ob)
    return ob

def resample(loop, step=0.015):
    out = []
    for a, b in zip(loop, loop[1:] + loop[:1]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        for k in range(n): out.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
    return out
DEST = (0.60, 3.245, 3.385, 0.035)     # half-width, z0, z1, corner radius
def rr_panel(name, hw, z0, z1, r, off, mat, c, rows=10, cols=40):
    verts = []
    for k in range(rows + 1):
        z = z0 + (z1 - z0) * k / rows; w = rrect_halfwidth(hw, z0, z1, r, z)
        for i in range(cols + 1): verts.append(on_face(-w + 2 * w * i / cols, z, off))
    faces = [[k * (cols + 1) + i, k * (cols + 1) + i + 1, (k + 1) * (cols + 1) + i + 1, (k + 1) * (cols + 1) + i] for k in range(rows) for i in range(cols)]
    ob = mk(name, verts, faces, [mat], c); _orient_out(ob)
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(ob.data); bm.free()
    return ob
def rr_ring(name, inner, outer, off, mat, c):
    li = resample(rrect_loop(*inner, 6)); n = len(li)
    lo = resample(rrect_loop(*outer, 6)); assert len(lo) >= 3
    # pair outer points to inner by angle around the centre
    zc = 0.5 * (inner[1] + inner[2])
    ang = lambda p: math.atan2(p[1] - zc, p[0])
    lo_m = [min(lo, key=lambda q: abs((ang(q) - ang(p) + pi) % (2 * pi) - pi)) for p in li]
    v = [on_face(y, z, off) for (y, z) in li] + [on_face(y, z, off) for (y, z) in lo_m]
    ob = mk(name, v, [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)], [mat], c); _orient_out(ob); return ob
def dest_display(c):
    hw, z0, z1, r = DEST
    rr_panel("CC_FrontDestLED", hw - 0.02, z0 + 0.02, z1 - 0.02, r - 0.01, 0.0015, M["LEDMATRIX"], c)
    rr_panel("CC_FrontDestGlass", hw + 0.006, z0 - 0.006, z1 + 0.006, r + 0.006, 0.0045, M["WSGLASS"], c)
    rr_ring("CC_FrontDestSeal", (hw + 0.006, z0 - 0.006, z1 + 0.006, r + 0.006), (hw + 0.013, z0 - 0.013, z1 + 0.013, r + 0.013), 0.0030, M["SEAL"], c)

def mask_panel(name, e, off, mat, c, rows=48, cols=44):
    z0, z1 = G.MK_ZC - G.MK_B - e, G.MK_ZC + G.MK_B + e
    zs = [z0 + (z1 - z0) * (0.5 - 0.5 * math.cos(pi * k / rows)) for k in range(rows + 1)]
    verts = []
    for z in zs:
        w = max(G.mask_halfwidth(min(max(z, z0 + 1e-5), z1 - 1e-5), e), 1e-3)
        for i in range(cols + 1):
            u = -1 + 2 * i / cols; u = math.copysign(abs(u) ** 0.85, u)          # denser towards the rim
            verts.append(on_face(w * u, z, off))
    faces = [[k * (cols + 1) + i, k * (cols + 1) + i + 1, (k + 1) * (cols + 1) + i + 1, (k + 1) * (cols + 1) + i] for k in range(rows) for i in range(cols)]
    ob = mk(name, verts, faces, [mat], c); _orient_out(ob)
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(ob.data); bm.free()
    return ob
def mask_ring(name, e_in, e_out, off, mat, c, n=240):
    li = [on_face(y, z, off) for (y, z) in G.mask_loop(e_in, n)]
    lo = [on_face(y, z, off) for (y, z) in G.mask_loop(e_out, n)]
    ob = mk(name, li + lo, [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)], [mat], c); _orient_out(ob)
    return ob

def glazing_front():
    """one flush-bonded glass over the whole black mask: clear driver opening, black frit/paint elsewhere, display inside"""
    c = coll("CabCar_Front")
    mask_panel("CC_Windscreen", 0.0, 0.0060, M["WSGLASS"], c)
    mask_ring("CC_WindscreenSeal", -0.0015, 0.0055, 0.0035, M["SEAL"], c)
    hw, z0, z1, r = DEST
    rr_panel("CC_FrontDestLED", hw - 0.02, z0 + 0.02, z1 - 0.02, r - 0.01, 0.0018, M["LEDMATRIX"], c)
    for k, yp in enumerate((-0.66, 0.14)):          # wipers parked on the glass along the lower opening edge
        arm = [on_face(yp + 0.07 * i, G.WS_Z0 + 0.09 + 0.004 * i, 0.03) for i in range(10)]
        tube(f"CC_WiperArm_{k + 1}", arm, 0.009, M["BLACK"], c, res=2)
        blade = [on_face(yp + 0.08 + 0.07 * i, G.WS_Z0 + 0.105 + 0.004 * i, 0.016) for i in range(9)]
        tube(f"CC_WiperBlade_{k + 1}", blade, 0.007, M["BLACK"], c, res=1)
        p = on_face(yp, G.WS_Z0 + 0.09, 0.0)
        lathe(f"CC_WiperPivot_{k + 1}", [(0.003, 0), (0.028, 0), (0.028, 0.03), (0.003, 0.035)], "x", (p[0], p[1], p[2]), 16, M["TRIM"], c)

# ================================================================== lamp pods: compact, diagonal, recessed, round optics (own shape)
POD = {"ang": 35.0, "yc": 1.08, "zc": 1.42, "L": 0.58, "H": 0.22, "shear": math.tan(math.radians(20.0)), "r": 0.09, "depth": 0.040}
_PF = {}
def pod_frame(s):
    if s not in _PF:
        a = math.radians(POD["ang"])
        D = Vector((math.cos(a), s * math.sin(a), 0.0)); U = Vector((-math.sin(a), s * math.cos(a), 0.0)); W = Vector((0, 0, 1.0))
        _PF[s] = (Vector(on_face(s * POD["yc"], POD["zc"], 0.0)), D, U, W)
    return _PF[s]
def pod_outline(scale=1.0, step=0.008):
    loop = resample(rr(POD["L"], POD["H"], POD["r"], 14), step)
    return [(u * scale, (w * scale) + u * scale * POD["shear"]) for (u, w) in loop]
def pod_hit(s, u, w):
    C, D, U, W = pod_frame(s)
    o = C + U * u + W * w + D * 1.2
    l, n = cast(o, -D)
    return (l, n) if l is not None else (o - D * 1.2, D)
def pod_cutter(s, scales=(1.0, 0.88, 0.74, 0.60, 0.46, 0.32, 0.18)):
    """curved slab cutter: both caps follow the body surface (a flat n-gon cap would pierce the thin pocket floor)"""
    rings = [[pod_hit(s, u, w) for (u, w) in pod_outline(k)] for k in scales]
    m = len(rings[0]); l0, n0 = pod_hit(s, 0.0, 0.0); R = len(rings)
    outer = [tuple(l + n * 0.05) for ring in rings for l, n in ring] + [tuple(l0 + n0 * 0.05)]
    inner = [tuple(l - n * POD["depth"]) for ring in rings for l, n in ring] + [tuple(l0 - n0 * POD["depth"])]
    N = len(outer); v = outer + inner; f = []
    for base, flip in ((0, False), (N, True)):
        for r in range(R - 1):
            for i in range(m):
                q = [base + r * m + i, base + r * m + (i + 1) % m, base + (r + 1) * m + (i + 1) % m, base + (r + 1) * m + i]
                f.append(q[::-1] if flip else q)
        last = base + (R - 1) * m; ctr = base + N - 1
        for i in range(m):
            t = [last + i, last + (i + 1) % m, ctr]; f.append(t[::-1] if flip else t)
    f += [[i, N + i, N + (i + 1) % m, (i + 1) % m] for i in range(m)]
    return mk(f"_PodCut{s}", v, f, [M["BLACK"]], coll("CabCar_Exterior"), smooth=False)
def pod_sheet(name, s, off, mat, c, scales=(1.0, 0.8, 0.6, 0.4, 0.2)):
    rings = [[pod_hit(s, u, w) for (u, w) in pod_outline(k)] for k in scales]
    m = len(rings[0]); l0, n0 = pod_hit(s, 0.0, 0.0)
    verts = [tuple(l + n * off) for ring in rings for l, n in ring] + [tuple(l0 + n0 * off)]
    faces = [[r * m + i, r * m + (i + 1) % m, (r + 1) * m + (i + 1) % m, (r + 1) * m + i] for r in range(len(rings) - 1) for i in range(m)]
    ctr = len(verts) - 1; last = (len(rings) - 1) * m
    faces += [[last + i, last + (i + 1) % m, ctr] for i in range(m)]
    ob = mk(name, verts, faces, [mat], c)
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.normal_update()
    for fc in bm.faces:
        if fc.normal.dot(n0) < 0: fc.normal_flip()
    bm.to_mesh(ob.data); bm.free(); return ob
def lathe_axis(name, prof, center, axis, seg, mat, c, closed=False):
    axis = Vector(axis).normalized(); t1 = axis.orthogonal().normalized(); t2 = axis.cross(t1)
    n = len(prof); verts = []
    for k in range(seg):
        th = 2 * pi * k / seg; rad = t1 * math.cos(th) + t2 * math.sin(th)
        for (r, a) in prof: verts.append(tuple(Vector(center) + rad * r + axis * a))
    faces = []
    for k in range(seg):
        k2 = (k + 1) % seg
        for j in range(n if closed else n - 1):
            j2 = (j + 1) % n; faces.append([k * n + j, k * n + j2, k2 * n + j2, k2 * n + j])
    ob = mk(name, verts, faces, [mat], c); _recalc(ob); return ob
def optic_round(name, s, u, w, r, kind, c):
    l, n = pod_hit(s, u, w + u * POD["shear"])
    axis = (n * 0.8 + Vector((1.0, 0.0, 0.0)) * 0.2).normalized()
    lathe_axis(name + "_Bezel", [(r - 0.003, -0.010), (r + 0.010, -0.010), (r + 0.010, -0.017), (r - 0.003, -0.017)], l, axis, 48, M["BLACK"], c, closed=True)
    lathe_axis(name + "_Reflector", [(r, -0.010), (0.93 * r, -0.016), (0.78 * r, -0.024), (0.55 * r, -0.031), (0.28 * r, -0.035), (0.10 * r, -0.0365), (0.002, -0.037)],
               l, axis, 48, M["REFLECTOR"], c)
    if kind == "head":
        lathe_axis(name + "_LED", [(0.001, -0.024), (0.38 * r, -0.024), (0.38 * r, -0.031), (0.001, -0.031)], l, axis, 32, M["HEADLAMP"], c, closed=True)
        lathe_axis(name + "_DRL", [(r + 0.012, -0.011), (r + 0.019, -0.011), (r + 0.019, -0.016), (r + 0.012, -0.016)], l, axis, 64, M["DRL"], c, closed=True)
        lens = M["GLASS"]
    else:
        lathe_axis(name + "_LED", [(0.001, -0.022), (0.55 * r, -0.022), (0.55 * r, -0.027), (0.001, -0.027)], l, axis, 32, M["TAIL"], c, closed=True)
        lens = M["TAILLENS"]
    lathe_axis(name + "_Lens", [(0.001, -0.0045), (0.5 * r, -0.0052), (0.85 * r, -0.0068), (r + 0.004, -0.0090)], l, axis, 48, lens, c)
def pod_parts():
    c = coll("CabCar_Front")
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        # open recessed pod (no flat cover sheet: it only added reflections; each optic has its own lens)
        optic_round(f"CC_HeadLamp_{S}", s, -0.13, -0.004, 0.078, "head", c)
        optic_round(f"CC_TailLamp_{S}", s, 0.175, 0.014, 0.048, "tail", c)

def apron_and_coupler():
    c = coll("CabCar_Front")
    piv = Vector((10.0, 0.0, 0.0))
    pts = []
    for i in range(41):
        ph = math.radians(-90 + 180 * i / 40); d = Vector((math.cos(ph), math.sin(ph), 0))
        o = piv + d * 4.0; o.z = 0.93
        l, n = cast(o, -d); pts.append(Vector((l.x, l.y, 0)) if l is not None else Vector((piv.x, d.y * 1.5, 0)))
    pts = [Vector((9.72, pts[0].y, 0))] + pts + [Vector((9.72, pts[-1].y, 0))]
    # insert exact columns at the coupler opening edges (|y| = CO)
    CO = 0.30
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        for yc in (-CO, CO):
            if (a.y - yc) * (b.y - yc) < 0:
                t = (yc - a.y) / (b.y - a.y); out.append(a.lerp(b, t))
        out.append(b)
    pts = out
    ctr = Vector((10.0, 0, 0))
    def fr(p):
        u = max(0.0, min(1.0, (p.x - 9.72) / 0.90)); return u * u * (3 - 2 * u)
    fs = [0.0, 0.16, 0.36, 0.58, 0.80, 1.0]
    verts = []
    for f in fs:
        for p in pts:
            w = fr(p); zb = 0.84 - 0.34 * w
            z = 0.915 - (0.915 - zb) * f
            inset = 0.014 + (0.004 + 0.060 * w) * f ** 1.5
            dirv = (p - ctr); dirv.z = 0; dirv.normalize()
            q = p - dirv * inset; verts.append((q.x, q.y, z))
    n = len(pts); faces = []
    for r in range(len(fs) - 1):
        for i in range(n - 1):
            a, b = pts[i], pts[i + 1]
            if r >= 1 and a.x > 10.5 and abs(a.y) <= CO + 1e-4 and abs(b.y) <= CO + 1e-4: continue   # coupler opening
            faces.append([r * n + i, r * n + i + 1, (r + 1) * n + i + 1, (r + 1) * n + i])
    ap = mk("CC_FrontApron", verts, faces, [M["APRON"]], c)
    lip = [verts[(len(fs) - 1) * n + i] for i in range(n)]
    tube("CC_ApronLip_A", [p for p, q in zip(lip, pts) if not (q.x > 10.5 and abs(q.y) < CO - 0.01) and q.y < 0], 0.011, M["SEAL"], c, res=2)
    tube("CC_ApronLip_B", [p for p, q in zip(lip, pts) if not (q.x > 10.5 and abs(q.y) < CO - 0.01) and q.y > 0], 0.011, M["SEAL"], c, res=2)
    bm = bmesh.new(); bm.from_mesh(ap.data); bm.normal_update()
    for fc in bm.faces:
        cc = fc.calc_center_median(); out_ = Vector((cc.x - ctr.x, cc.y, 0))
        if fc.normal.dot(out_) < 0: fc.normal_flip()
    bm.to_mesh(ap.data); bm.free()
    solidify(ap, 0.014); apply_mods(ap); smooth_by_angle(ap, 40)
    # coupler pocket + automatic coupler (generic)
    bbox_bevel("CC_CouplerPocket", M["UNDER"], 10.70, 0, 0.66, 0.36, 0.64, 0.36, c, bevel=0.02)
    parts = [bbox_bevel("dg", M["BOGIE3"], 10.42, 0, 0.70, 0.60, 0.40, 0.24, c, bevel=0.02, inset_sides=True),
             lathe("sh", [(0.02, -0.40), (0.075, -0.40), (0.075, 0.40), (0.02, 0.40)], "x", (10.95, 0, 0.70), 24, M["BOGIE3"], c),
             bbox_bevel("hd", M["BOGIE3"], 11.30, 0, 0.70, 0.16, 0.36, 0.34, c, bevel=0.03),
             lathe("cn", [(0.003, 0), (0.075, 0), (0.045, 0.09), (0.003, 0.11)], "x", (11.38, 0.09, 0.72), 20, M["BOGIE3"], c),
             bbox_bevel("eh", M["UNDER"], 11.24, 0, 0.47, 0.18, 0.30, 0.12, c, bevel=0.012)]
    join(parts, "CC_Coupler")
    for s in (1, -1):
        pts_ = [(11.00, s * 0.25, 0.64)] + [(11.00 + 0.10 * math.sin(a), s * (0.25 + 0.05 * math.sin(a)), 0.64 - 0.18 * (1 - math.cos(a))) for a in [k * pi / 10 for k in range(1, 11)]]
        tube(f"CC_CouplerHose_{'L' if s > 0 else 'R'}", pts_, 0.022, M["SEAL"], c, res=3)
    # obstacle deflector below the apron (follows the apron plan line)
    dv = []
    for z, back in ((0.52, 0.09), (0.30, 0.13), (0.20, 0.15)):
        for p in [q for q in pts[1:-1] if abs(q.y) < 1.0]:
            dirv = (p - ctr); dirv.z = 0; dirv.normalize(); q = p - dirv * back
            dv.append((q.x, q.y * 0.86, z))
    m = len([q for q in pts[1:-1] if abs(q.y) < 1.0])
    df = [[r * m + i, r * m + i + 1, (r + 1) * m + i + 1, (r + 1) * m + i] for r in range(2) for i in range(m - 1)]
    de = mk("CC_ObstacleDeflector", dv, df, [M["UNDER"]], c); solidify(de, 0.02); apply_mods(de); smooth_by_angle(de, 40)

# ================================================================== roof: HVAC units refined (fans, guards, condenser louvres)
def _box(cx, cy, cz, sx, sy, sz, rot_x=0.0):
    hx, hy, hz = sx / 2, sy / 2, sz / 2; cr, sr = math.cos(rot_x), math.sin(rot_x); out = []
    for (a, b, d) in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
        y, z = b * hy, d * hz
        out.append((cx + a * hx, cy + y * cr - z * sr, cz + y * sr + z * cr))
    return out
_BOXF = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
def boxes(name, specs, mat, c):
    v, f = [], []
    for sp in specs:
        o = len(v); v += _box(*sp); f += [[o + i for i in fc] for fc in _BOXF]
    return mk(name, v, f, [mat], c, smooth=False)
def fan(name, xf, top, R, c):
    parts = [lathe("d", [(0.002, 0.0), (R, 0.0), (R, 0.002), (0.002, 0.002)], "z", (xf, 0, top + 0.0005), 48, M["UNDER"], c),
             lathe("lip", [(R, 0.0), (R + 0.022, 0.0), (R + 0.022, 0.012), (R + 0.006, 0.016), (R, 0.010)], "z", (xf, 0, top), 48, M["ROOF"], c),
             lathe("hub", [(0.002, 0.0), (0.06, 0.0), (0.06, 0.020), (0.03, 0.028), (0.002, 0.029)], "z", (xf, 0, top + 0.002), 32, M["BLACK"], c)]
    join(parts, name + "_Shroud")
    v, f = [], []
    for b in range(7):                                    # swept rotor blades seen through the guard
        th0 = 2 * pi * b / 7; rows = []
        for i in range(6):
            r = 0.065 + (R - 0.085) * i / 5; sweep = 0.25 * (i / 5) ** 1.5; half = 0.20 - 0.06 * i / 5
            for e in (-1, 1):
                th = th0 + sweep + e * half; rows.append((xf + r * math.cos(th), r * math.sin(th), top + 0.010 + 0.007 * e))
        o = len(v); v += rows
        f += [[o + 2 * i, o + 2 * i + 1, o + 2 * i + 3, o + 2 * i + 2] for i in range(5)]
    bl = mk(name + "_Rotor", v, f, [M["BOGIE3"]], c); solidify(bl, 0.003); apply_mods(bl)
    rings = [lathe("g", [(rr_ - 0.0025, 0.0), (rr_ + 0.0025, 0.0), (rr_ + 0.0025, 0.004), (rr_ - 0.0025, 0.004)], "z", (xf, 0, top + 0.026), 64, M["BLACK"], c, smooth=False)
             for rr_ in [0.07 + k * (R - 0.07) / 5 for k in range(6)]]
    sv, sf = [], []
    for k in range(10):
        a = 2 * pi * k / 10; ca, sa = math.cos(a), math.sin(a)
        for r0, r1 in ((0.05, R + 0.012),):
            o = len(sv)
            for (rx, ry) in ((r0, -0.002), (r1, -0.002), (r1, 0.002), (r0, 0.002)):
                sv.append((xf + rx * ca - ry * sa, rx * sa + ry * ca, top + 0.030))
            for (rx, ry) in ((r0, -0.002), (r1, -0.002), (r1, 0.002), (r0, 0.002)):
                sv.append((xf + rx * ca - ry * sa, rx * sa + ry * ca, top + 0.034))
            sf += [[o + i for i in fc] for fc in _BOXF]
    rings.append(mk("spk", sv, sf, [M["BLACK"]], c, smooth=False))
    join(rings, name + "_Guard")
def condenser_louvres(name, x0, x1, top, w, c):
    specs, plates = [], []
    for s in (1, -1):
        y0, y1 = 0.60, w / 2 - 0.10
        plates.append((0.5 * (x0 + x1), s * 0.5 * (y0 + y1), top + 0.0015, x1 - x0, y1 - y0, 0.003))
        nx = int((x1 - x0) / 0.032)
        for k in range(nx + 1):
            xx = x0 + (x1 - x0) * k / nx
            specs.append((xx, s * 0.5 * (y0 + y1), top + 0.010, 0.012, y1 - y0 - 0.01, 0.004, math.radians(0)))
        specs.append((0.5 * (x0 + x1), s * y0, top + 0.009, x1 - x0, 0.010, 0.016)); specs.append((0.5 * (x0 + x1), s * y1, top + 0.009, x1 - x0, 0.010, 0.016))
    boxes(name + "_CoilBase", plates, M["UNDER"], c)
    boxes(name + "_CoilSlats", [sp[:6] for sp in specs], M["ROOF"], c)
def side_louvres(name, x0, x1, base, h, w, c):
    specs, plates = [], []
    for s in (1, -1):
        yy = s * (w / 2 + 0.002)
        plates.append((0.5 * (x0 + x1), yy, base + 0.5 * h, x1 - x0, 0.004, h * 0.62))
        for k in range(5):
            zs = base + h * 0.26 + k * h * 0.12
            specs.append((0.5 * (x0 + x1), s * (w / 2 + 0.012), zs, x1 - x0 - 0.02, 0.026, 0.004, -s * math.radians(35)))
    boxes(name + "_SideGrillBack", plates, M["UNDER"], c); boxes(name + "_SideLouvres", specs, M["ROOF"], c)
def cab_unit(c):
    x0, x1, w, h = 8.10, 8.84, 1.60, 0.26; zb = G.ZFLAT - 0.005; secs = []
    for x, ww, hh in ((x0, w * 0.92, h * 0.55), (x0 + 0.06, w, h), (x1 - 0.20, w, h), (x1 - 0.08, w * 0.97, h * 0.72), (x1, w * 0.92, h * 0.32)):
        secs.append([(x, a, zb + hh / 2 + bb) for (a, bb) in rr(ww, hh, min(0.07, hh / 2.2), 4)])
    loft("CC_CabHVAC", secs, M["ROOF"], c, caps=True, subd=1, angle=35)
    fan("CC_CabHVAC_Fan", 8.40, zb + h, 0.20, c)
    side_louvres("CC_CabHVAC", x0 + 0.12, x1 - 0.26, zb, h, w, c)
def roof4():
    c = coll("CabCar_Roof")
    killmany(["CC_SaloonHVAC_Rear_Grilles", "CC_SaloonHVAC_Front_Grilles", "CC_SaloonHVAC_Rear_FanGrille", "CC_SaloonHVAC_Front_FanGrille",
              "CC_SaloonHVAC_Rear_ServiceHatches", "CC_SaloonHVAC_Front_ServiceHatches", "CC_CabHVAC"])
    top = G.ZFLAT - 0.005 + 0.28; zb = G.ZFLAT - 0.005
    for nm, x0, x1 in (("CC_SaloonHVAC_Rear", -10.80, -7.72), ("CC_SaloonHVAC_Front", 5.32, 8.02)):
        for k, xf in enumerate((x0 + 0.75, x1 - 0.75)): fan(f"{nm}_Fan{k + 1}", xf, top, 0.28, c)
        condenser_louvres(nm, x0 + 0.22, x1 - 0.22, top, 2.30, c)
        side_louvres(nm, x0 + 0.30, x1 - 0.30, zb, 0.28, 2.30, c)
        xm = 0.5 * (x0 + x1)
        boxes(f"{nm}_ServiceHatch", [(xm, 0, top + 0.004, 0.46, 0.74, 0.008)], M["ROOF"], c)
        boxes(f"{nm}_HatchLatches", [(xm + dx, dy, top + 0.010, 0.04, 0.03, 0.008) for dx in (-0.20, 0.20) for dy in (-0.30, 0.30)], M["BLACK"], c)
    cab_unit(c)

# ================================================================== side: thin flush window borders, flush door seals
def side4():
    c = coll("CabCar_Trims")
    for side in (1, -1):
        S = "L" if side > 0 else "R"
        for k, (a, b) in enumerate(G.windows()):
            kill(f"CC_WinFrit_{S}{k + 1}")
            conform(f"CC_WinFrit_{S}{k + 1}", G.frame_ring(a + 0.085, b - 0.085, G.WIN_Z0 + 0.085, G.WIN_Z1 - 0.085, 0.110, G.WIN_R - 0.06, side, 0.0026), M["FRIT"], c, side)
            o = bpy.data.objects.get(f"CC_WinReveal_{S}{k + 1}")
            if o:
                for i in range(len(o.data.materials)): o.data.materials[i] = M["BLACK"]
        for i, cx in enumerate(G.DOORS):
            x0, x1 = cx - G.DOOR_HW, cx + G.DOOR_HW
            kill(f"CC_DoorDrip_{S}{i + 1}")
            conform(f"CC_DoorDrip_{S}{i + 1}", G.strip(x0 - 0.06, x1 + 0.06, G.DOOR_Z1 + 0.05, G.DOOR_Z1 + 0.066, side, 0.004, 1), M["TRIM"], c, side, 0.004)
            for leaf in ("a", "b"):
                kill(f"CC_DoorSeal_{S}{i + 1}{leaf}")
                lo = bpy.data.objects.get(f"CC_Door_{S}{i + 1}{leaf}")
                ex = cx - 0.008 if leaf == "a" else cx + 0.008
                xa, xb = (ex - 0.010, ex) if leaf == "a" else (ex, ex + 0.010)
                conform(f"CC_DoorSeal_{S}{i + 1}{leaf}", G.strip(xa, xb, G.DOOR_Z0 + 0.02, G.DOOR_Z1 - 0.02, side, 0.0006, 6), M["SEAL"], c, side, 0.0012, lo)

# ================================================================== materials: roughness per family
def _set(m, **kw):
    b = m.node_tree.nodes.get("Principled BSDF")
    for k, v in kw.items():
        key = {"rough": "Roughness", "metal": "Metallic", "coat": "Coat Weight", "spec": "Specular IOR Level", "color": "Base Color"}[k]
        if key in b.inputs and not b.inputs[key].is_linked:
            b.inputs[key].default_value = (*v, 1) if key == "Base Color" else v
    if "color" in kw: m.diffuse_color = (*kw["color"], 1)
def material_pass():
    _set(M["STEEL"], color=(0.50, 0.505, 0.51), metal=0.92, rough=0.30, coat=0.0)     # brushed stainless trims/end wall
    _set(M["ROOF"], color=(0.30, 0.30, 0.31), metal=0.0, rough=0.50, coat=0.15)      # painted roof equipment
    _set(M["BLACK"], rough=0.55, spec=0.4)                                              # moulded black plastic
    _set(M["SEAL"], rough=0.80, spec=0.3)                                               # EPDM / PU seals
    _set(M["RIM"], rough=0.85, spec=0.3)                                                # rubber
    _set(M["TRIM"], color=(0.72, 0.73, 0.74), metal=1.0, rough=0.22)                   # satin stainless trims (not chrome)
    _set(M["UNDER"], rough=0.70, spec=0.35)                                             # underframe black
    _set(M["FRIT"], rough=0.25)
    _set(M["GLASS"], rough=0.015); _set(M["WSGLASS"], rough=0.010)
    _set(M["REFLECTOR"], rough=0.14)

# ================================================================== livery (procedural, object space; continuous over doors)
PAL = {"WHITE": (0.88, 0.885, 0.88), "RED": (0.578, 0.0052, 0.0273), "NAVY": (0.0070, 0.0242, 0.162),
       "DARK": (0.0152, 0.0168, 0.016), "ROOF": (0.30, 0.30, 0.31)}
LIV = {"XC": 8.995, "XP": 9.40, "RAKE": 0.404,
       "NAVY": (1.20, 1.02, 42.0, 60.0),                 # side top, front top, phi blend
       "RED_LOW": (1.68, 1.80, 56.0),                    # lower red stripe + front end (phi)
       "CANT": (3.20, 3.26),                             # thin red cant-rail stripe under the roof line
       "CROWN": (8.80, 9.35, 9.40, 3.12, 3.74, 10.12),   # cab crown: x start, x full(bottom), x full(top), z bottom, z top, front end x @z=3.12
       "BAND": (1.86, 3.06, 66.0), "ROOF_Z": 3.30}
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
    def edge(s, v, eps=0.0015): return s.ss(-eps, eps, v)                     # 0 below 0, 1 above (anti-aliased)
    def lerp(s, a, b, f): return s.m("ADD", a, s.m("MULTIPLY", s.m("SUBTRACT", b, a), f)) if not isinstance(a, (int, float)) or not isinstance(b, (int, float)) else s.m("ADD", a, s.m("MULTIPLY", b - a, f))
    def cmix(s, a, b, f):
        n = s._n("ShaderNodeMix"); n.data_type = "RGBA"; n.blend_type = "MIX"; n.clamp_factor = True
        ins = {i.identifier: i for i in n.inputs}
        s._set(ins["Factor_Float"], f); s._set(ins["A_Color"], a); s._set(ins["B_Color"], b)
        return [o for o in n.outputs if o.identifier == "Result_Color"][0]
def livery_material():
    m = bpy.data.materials.get("PBR_Livery_Body")
    if m: bpy.data.materials.remove(m)
    m = bpy.data.materials.new("PBR_Livery_Body"); m.use_nodes = True; nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF"); B = _NB(nt)
    tc = B._n("ShaderNodeTexCoord"); sp = B._n("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sp.inputs[0])
    x, y, z = sp.outputs[0], sp.outputs[1], sp.outputs[2]
    ay = B.m("ABSOLUTE", y)
    xr = B.m("ADD", x, B.m("MULTIPLY", LIV["RAKE"], B.m("MAXIMUM", B.m("SUBTRACT", z, 2.2), 0.0)))
    phi = B.m("MULTIPLY", B.m("ARCTAN2", ay, B.m("SUBTRACT", xr, LIV["XP"])), 57.29578)
    cab = B.edge(B.m("SUBTRACT", x, LIV["XC"]), 0.002)
    # brushed stainless: noise stretched along X -> horizontal grain in colour and roughness
    mp = B._n("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.8, 420.0, 420.0); nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = B._n("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 6.0
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"]); grain = nz.outputs["Fac"]
    scol = B.cmix((0.455, 0.46, 0.468), (0.56, 0.565, 0.572), B.ss(0.3, 0.7, grain))
    srgh = B.lerp(0.20, 0.38, B.ss(0.25, 0.75, grain))
    col = B.cmix(scol, PAL["WHITE"], cab)
    met = B.lerp(0.92, 0.0, cab); rgh = B.lerp(srgh, 0.20, cab); cot = B.lerp(0.0, 0.8, cab); spc = 0.5
    def layer(mask, c, mt, rg, ct, sp=0.5):
        nonlocal col, met, rgh, cot, spc
        col = B.cmix(col, PAL[c], mask); met = B.lerp(met, mt, mask); rgh = B.lerp(rgh, rg, mask); cot = B.lerp(cot, ct, mask)
        spc = B.lerp(spc, sp, mask)
    def zband(z0, z1): return B.m("MULTIPLY", B.edge(B.m("SUBTRACT", z, z0)), B.m("SUBTRACT", 1.0, B.edge(B.m("SUBTRACT", z, z1))))
    def phicut(p): return B.ss(p - 0.08, p + 0.08, phi)
    layer(B.m("MULTIPLY", B.edge(B.m("SUBTRACT", z, LIV["ROOF_Z"])), B.m("SUBTRACT", 1.0, cab)), "ROOF", 0.0, 0.50, 0.15, 0.45)
    ns, nf, p0, p1 = LIV["NAVY"]
    znt = B.m("SUBTRACT", ns, B.m("MULTIPLY", ns - nf, B.m("SUBTRACT", 1.0, B.ss(p0, p1, phi))))
    layer(B.m("SUBTRACT", 1.0, B.edge(B.m("SUBTRACT", z, znt))), "NAVY", 0.0, 0.34, 0.25, 0.32)
    r0, r1, rp = LIV["RED_LOW"]
    low = B.m("MULTIPLY", zband(r0, r1), phicut(rp))
    xs, xfb, xft, cz0, cz1, xe = LIV["CROWN"]; c0, c1 = LIV["CANT"]
    xend = B.m("SUBTRACT", xe, B.m("MULTIPLY", LIV["RAKE"], B.m("SUBTRACT", z, cz0)))
    front_ok = B.m("SUBTRACT", 1.0, B.edge(B.m("SUBTRACT", x, xend), 0.002))
    cant = zband(c0, c1)
    # cab crown: red over the upper cab side and both roof shoulders, bounded on the roof by straight lines |y| = y_in(x)
    zlo = B.m("SUBTRACT", c0, B.m("MULTIPLY", c0 - cz0, B.ss(xs, xfb, x)))
    y_in = B.m("SUBTRACT", 1.56, B.m("MULTIPLY", 1.56 - 0.80, B.ss(xs, xft, x)))
    crown = B.m("MULTIPLY", B.edge(B.m("SUBTRACT", z, zlo)), B.edge(B.m("SUBTRACT", ay, y_in), 0.002))
    crown = B.m("MULTIPLY", B.m("MAXIMUM", cant, crown), front_ok)
    layer(B.m("MAXIMUM", low, crown), "RED", 0.0, 0.30, 0.25, 0.32)
    b0, b1, bp = LIV["BAND"]
    layer(B.m("MULTIPLY", zband(b0, b1), phicut(bp)), "DARK", 0.0, 0.45, 0.10, 0.28)
    # black mask under the front glass: same tapered superellipse as geom.mask_loop (nose only)
    zz = B.m("SUBTRACT", z, G.MK_ZC)
    aa = B.m("ADD", G.MK_A, B.m("MULTIPLY", G.MK_TAPER, zz))
    q = B.m("ADD", B.m("POWER", B.m("DIVIDE", ay, aa), G.MK_N), B.m("POWER", B.m("DIVIDE", B.m("ABSOLUTE", zz), G.MK_B), G.MK_N))
    inside = B.m("MULTIPLY", B.m("SUBTRACT", 1.0, B.edge(B.m("SUBTRACT", q, 1.0), 0.004)), B.edge(B.m("SUBTRACT", x, 9.95), 0.01))
    layer(inside, "DARK", 0.0, 0.10, 0.6, 0.5)
    nt.links.new(col, bsdf.inputs["Base Color"]); nt.links.new(met, bsdf.inputs["Metallic"]); nt.links.new(rgh, bsdf.inputs["Roughness"])
    ci = bsdf.inputs.get("Coat Weight")
    if ci: nt.links.new(cot, ci)
    si = bsdf.inputs.get("Specular IOR Level")
    if si: nt.links.new(spc, si)
    cr = bsdf.inputs.get("Coat Roughness")
    if cr: cr.default_value = 0.035
    m.diffuse_color = (0.6, 0.6, 0.6, 1)
    return m
def apply_livery():
    L = livery_material(); M["LIVERY"] = L
    names = {M[k].name for k in ("STEEL", "ROOF", "BAND", "STRIPE", "NOSE", "SKIRT")}
    sh = bpy.data.objects["CC_BodyShell"]
    for i, mt in enumerate(sh.data.materials):
        if mt and mt.name in names: sh.data.materials[i] = L
    for o in bpy.data.objects:
        if o.name.startswith("CC_RainGutter_") or o.name.startswith("CC_DoorDrip_"):
            for i in range(len(o.data.materials)): o.data.materials[i] = L
    n = 0
    for o in bpy.data.objects:
        if o.type == "MESH" and (o.name.startswith("CC_Door_") or o.name.startswith("CC_CabSideDoor_")):
            for i, mt in enumerate(o.data.materials):
                if mt and mt.name in (M["DOOR"].name, M["NOSE"].name): o.data.materials[i] = L; n += 1
    return n

def uv_pass():
    import time
    t0 = time.time(); done = []
    objs = [o for o in bpy.data.objects if o.type == "MESH" and (o.name == "CC_BodyShell" or o.name.startswith("CC_Door_") or o.name.startswith("CC_CabSideDoor_") or o.name in ("CC_FrontApron", "CC_Windscreen"))]
    for o in objs:
        activate(o)
        try:
            bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.002)
            done.append(o.name)
        except Exception as e:
            print("uv fail", o.name, e)
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")
    print("uv:", len(done), "objects in", round(time.time() - t0, 1), "s")

def color_cameras():
    clay_cameras(); sc = bpy.context.scene
    ob = bpy.data.objects.get("Cam_LampDetail")
    if ob: bpy.data.objects.remove(ob, do_unlink=True)
    cd = bpy.data.cameras.new("Cam_LampDetail"); cd.lens = 58; co = bpy.data.objects.new("Cam_LampDetail", cd); sc.collection.objects.link(co)
    co.location = (12.05, -2.30, 1.58); co.rotation_euler = (Vector((10.82, -1.08, 1.42)) - co.location).to_track_quat("-Z", "Y").to_euler()
def color_renders(prefix="rev5_", jobs=None):
    color_cameras()
    vs = bpy.context.scene.view_settings
    try: vs.look = "AgX - Punchy"
    except Exception: pass
    vs.exposure = -0.30
    jobs = jobs or [("on_orto", "Clay_Front", (1200, 1200)), ("yan_tam", "Cam_Side", (2400, 700)), ("yan_kabin", "Clay_Side", (1600, 900)),
                    ("ust_kabin", "Clay_Top", (1600, 900)), ("34_on", "Clay_34", (1600, 900)), ("34_alcak", "Clay_34Low", (1600, 900)),
                    ("34_yuksek", "Clay_34High", (1600, 900)), ("far_detay", "Cam_LampDetail", (1600, 900))]
    return [render(prefix + n, cam, res) for n, cam, res in jobs]

def clay_mats():
    out = {}
    for nm, col, rough in (("CLAY", (0.60, 0.60, 0.60), 0.55), ("CLAY_GLASS", (0.035, 0.037, 0.04), 0.08)):
        m = bpy.data.materials.get(nm) or bpy.data.materials.new(nm); m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (*col, 1); bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = 0.0; out[nm] = m
    return out
def clay_cameras():
    sc = bpy.context.scene
    def cam(name, loc, rot=(0, 0, 0), ortho=None, lens=50, target=None):
        ob = bpy.data.objects.get(name)
        if ob: bpy.data.objects.remove(ob, do_unlink=True)
        cd = bpy.data.cameras.new(name)
        if ortho: cd.type = "ORTHO"; cd.ortho_scale = ortho
        else: cd.lens = lens
        cd.clip_end = 500; co = bpy.data.objects.new(name, cd); sc.collection.objects.link(co); co.location = loc; co.rotation_euler = rot
        if target: co.rotation_euler = (Vector(target) - co.location).to_track_quat("-Z", "Y").to_euler()
        return co
    cam("Clay_Front", (40, 0, 2.05), (math.radians(90), 0, math.radians(90)), ortho=4.4)
    cam("Clay_Side", (7.9, -40, 2.05), (math.radians(90), 0, 0), ortho=7.2)
    cam("Clay_Top", (7.9, 0, 40), (0, 0, 0), ortho=7.2)
    cam("Clay_34", (15.6, -6.2, 2.7), lens=40, target=(9.9, 0, 1.95))
    cam("Clay_34Low", (14.2, -4.9, 0.75), lens=32, target=(10.2, 0, 1.75))
    cam("Clay_34High", (14.8, 5.8, 5.6), lens=40, target=(9.6, 0, 2.3))
def clay_renders(names=("Clay_Front", "Clay_Side", "Clay_Top", "Clay_34", "Clay_34Low", "Clay_34High"), prefix="v4_clay_"):
    cm = clay_mats(); clay_cameras(); saved = {}
    glass = {"GLASS"}
    gnames = {M[k].name for k in ("GLASS",) if k in M} | {m.name for m in bpy.data.materials if "Glass" in m.name and "Frit" not in m.name}
    for o in bpy.data.objects:
        if o.type not in ("MESH", "CURVE") or not o.name.startswith("CC_"): continue
        mats = o.data.materials; saved[o.name] = [m for m in mats]
        for i, m in enumerate(mats):
            mats[i] = cm["CLAY_GLASS"] if (m and m.name in gnames) else cm["CLAY"]
    outs = []
    try:
        for nm in names:
            res = (1600, 900) if nm != "Clay_Front" else (1200, 1200)
            if nm == "Clay_Front": bpy.data.objects[nm].data.ortho_scale = 4.4
            outs.append(render(prefix + nm[5:].lower(), nm, res))
    finally:
        for on, ml in saved.items():
            o = bpy.data.objects[on]
            for i, m in enumerate(ml): o.data.materials[i] = m
    return outs

def mats4():
    M["APRON"] = mat_paint("PBR_ApronMetallicGrey", (0.21, 0.215, 0.22), rough=0.32, coat=0.5, metal=0.85)
    M["REFLECTOR"] = mat_plain("PBR_LampReflector", (0.70, 0.71, 0.73), rough=0.14, metal=1.0)
    M["WSGLASS"] = mat_glass("PBR_WindscreenGlass", tint=(0.010, 0.013, 0.016), rough=0.01, alpha=0.66)
    M["COVERGLASS"] = mat_glass("PBR_LampCoverClear", tint=(0.85, 0.86, 0.88), rough=0.0, alpha=0.10)
    M["TAILLENS"] = mat_glass("PBR_TailLens", tint=(0.35, 0.004, 0.006), rough=0.02, alpha=0.55)
    M["DRL"] = mat_plain("PBR_DRL_LED", (1.0, 0.97, 0.92), rough=0.2, emit=2.5)

def run_details4():
    global REF
    mats4(); material_pass()
    REF = nose_ref(); _PF.clear()
    apply_cutters([ws_cutter(), pod_cutter(1), pod_cutter(-1)])
    glazing_front(); pod_parts(); apron_and_coupler()
    roof4(); side4()
    print("livery slots on doors:", apply_livery())
    if globals().get("DO_UV", True): uv_pass()

if not globals().get("CLAY_ONLY"):
    run_details4()
    print("details4 done:", stats())
