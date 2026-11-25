"""Rev 6 - cab geometry module.
Splits the old single shell into
  CC_Body_Main   : main body cage (rings X_REAR..X_NOSE0, door/window holes)  + live Subdivision / Solidify / Smooth
  CC_Cab_Body    : front cab cage (nose fillets + Coons face)                   + live Subdivision / Solidify / Boolean / normals
  CC_Ref_Exterior: hidden full cage without holes (+ Subdivision) used as projection / ray-cast target
and stores the cab surface as editable cross-section curves (CC_Cab_Sections collection).
After editing the curves run  rebuild_cab_from_curves().
Also builds the windscreen opening cutter, flush glass + seal, wipers, bumper (apron) and coupler group."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
from common import (G, pi, coll, remove, remove_prefix, mk, empty, activate, mat, mat_pbr, mod_subsurf, mod_solidify,
                    mod_boolean_collection, mod_smooth_by_angle, mod_weighted_normal, Caster, prop, flip_if)

NSEG = 8                       # fillet rows of geom.shell
X_SPLIT_UV = -0.50             # main-body UV strip split (a ring position)
STRIPS_MARGIN = 0.02

# ------------------------------------------------------------------ materials used by the shells
def shell_materials():
    return {
        "PAINT": mat("PBR_Livery_Procedural") or mat("PBR_Livery_Body") or mat_pbr("PBR_Livery_Procedural", (0.8, 0.8, 0.8)),
        "UNDER": mat("PBR_UnderframeBlack_RAL9005") or mat_pbr("PBR_UnderframeBlack_RAL9005", (0.0032, 0.0032, 0.004), 0.7),
        "INTERIOR": mat("PBR_InteriorPanel") or mat_pbr("PBR_InteriorPanel", (0.66, 0.67, 0.66), 0.45),
        "RIM": mat("PBR_Rubber") or mat_pbr("PBR_Rubber", (0.015, 0.015, 0.015), 0.85),
        "BLACK": mat("PBR_BlackPlastic") or mat_pbr("PBR_BlackPlastic", (0.012, 0.012, 0.013), 0.55),
    }

def profile_arclength():
    s = [0.0]
    for j in range(1, G.NP + 1):
        a, b = G.PROFILE[j - 1], G.PROFILE[j % G.NP]
        s.append(s[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return s                     # len NP+1, s[NP] = perimeter


# ------------------------------------------------------------------ split shell
def _shell():
    v, f, keys, rings = G.shell(NSEG, 0.0)
    NP = G.NP; nr = len(rings)
    return v, f, keys, rings, NP, nr

def build_shells():
    M = shell_materials()
    cx = coll("CabCar_Exterior"); cs = coll("CC_Cab_Sections"); cc = coll("CC_Cab_Cutters")
    cc.hide_render = True
    v, f, keys, rings, NP, nr = _shell()
    s = profile_arclength(); P = s[-1]
    base = (nr - 1) * NP                                        # first vertex of the seam ring
    nmain = (nr - 1) * NP                                       # ring faces
    # ---------------- main body cage
    mfaces, mmat, muv = [], [], []
    k = (1.0 - 3 * STRIPS_MARGIN) / (2 * P)
    for fi in range(nmain):
        if keys[fi] == "HOLE": continue
        q = f[fi]; mfaces.append(q); mmat.append(1 if keys[fi] == "UNDER" else 0)
        i0 = q[0] // NP; xm = 0.5 * (rings[i0][0] + rings[i0 + 1][0])
        strip = 0 if xm < X_SPLIT_UV else 1
        x0 = G.X_REAR if strip == 0 else X_SPLIT_UV
        v0 = STRIPS_MARGIN + strip * (P * k + STRIPS_MARGIN)
        js = [vid % NP for vid in q]; jmax = max(js)
        uv = []
        for vid in q:
            i, j = divmod(vid, NP)
            sj = s[NP] if (j == 0 and jmax == NP - 1) else s[j]
            uv.append((STRIPS_MARGIN + (rings[i][0] - x0) * k, v0 + sj * k))
        muv.append(uv)
    used = sorted({i for q in mfaces for i in q}); remap = {o: n for n, o in enumerate(used)}
    ob = mk("CC_Body_Main", [v[i] for i in used], [[remap[i] for i in q] for q in mfaces], [M["PAINT"], M["UNDER"], M["INTERIOR"], M["RIM"]], cx, face_mats=mmat)
    _set_uv(ob, muv, "UV_BodyAtlas")
    recalc_out(ob)
    mod_subsurf(ob, 1, 1); mod_solidify(ob, 0.045, inner=2, rim=3, use_rim=True); mod_smooth_by_angle(ob, 35)
    ob["uv_scale_per_m"] = k; ob["uv_strip_split_x"] = X_SPLIT_UV
    # ---------------- cab cage (sections + Coons face)
    cverts = v[base:]
    cfaces = [[i - base for i in q] for q in f[nmain:]]
    ckeys = keys[nmain:]
    S = NSEG + 2; nring = (S - 1) * NP
    kk = G.KCORNER; nu = 2 * kk; nv = NP // 2 - 2 * kk
    assert len(cverts) == S * NP + (nu - 1) * (nv - 1), (len(cverts), S, nu, nv)
    cab = mk("CC_Cab_Body", cverts, cfaces, [M["PAINT"], M["UNDER"], M["INTERIOR"], M["RIM"], M["BLACK"]], cx,
             face_mats=[1 if kk_ == "UNDER" else 0 for kk_ in ckeys])
    cab["sections"] = S; cab["np"] = NP; cab["face_cols"] = nu - 1; cab["face_rows"] = nv - 1
    _cab_uv(cab, nring, S, NP, s)
    recalc_out(cab)
    mod_subsurf(cab, 1, 1); mod_solidify(cab, 0.045, inner=2, rim=3, use_rim=False)
    mod_boolean_collection(cab, cc, "OpeningsAndLampPods")
    mod_smooth_by_angle(cab, 35); mod_weighted_normal(cab, 50)
    _pin_last(cab, "WeightedNormal")
    # ---------------- reference (full cage, no holes) for projection / ray casting
    ref = mk("CC_Ref_Exterior", v, f, [M["PAINT"]], coll("CC_Helpers"))
    recalc_out(ref); mod_subsurf(ref, 1, 1)
    ref.hide_render = True; ref.display_type = "WIRE"; ref.hide_set(True)
    coll("CC_Helpers").hide_render = True
    ref["cab_vertex_offset"] = base
    # ---------------- editable section curves
    write_section_curves(cab, cs)
    return ob, cab, ref

def _pin_last(ob, name):
    """Smooth-by-Angle pins itself last; unpin it and move the custom-normal modifier to the end."""
    for md in ob.modifiers:
        if md.type == "NODES":
            try: md.use_pin_to_last = False
            except Exception: pass
    activate(ob)
    try: bpy.ops.object.modifier_move_to_index(modifier=name, index=len(ob.modifiers) - 1)
    except Exception as e: print("modifier move", e)

def recalc_out(ob):
    """outward normals: make faces point away from the car centre line (x stays, y/z from the profile centre)."""
    c = Vector((0, 0, 2.2))
    def bad(fc):
        p = fc.calc_center_median(); d = Vector((0, p.y, p.z)) - c
        if p.x > G.X_NOSE0 - 0.01: d.x = (p.x - (G.X_NOSE0 - 0.6))
        return fc.normal.dot(d) < 0
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.normal_update()
    nbad = sum(1 for fc in bm.faces if bad(fc))
    if nbad > len(bm.faces) / 2:
        for fc in bm.faces: fc.normal_flip()
    bm.to_mesh(ob.data); bm.free()

def _set_uv(ob, face_uvs, name):
    me = ob.data
    uvl = me.uv_layers.get(name) or me.uv_layers.new(name=name)
    me.uv_layers.active = uvl
    for poly, uvs in zip(me.polygons, face_uvs):
        for li, uv in zip(poly.loop_indices, uvs): uvl.data[li].uv = uv

def _cab_uv(cab, nring, S, NP, s):
    """ring band: u = profile arc length, v = distance along the fillet; face: planar (y, z). Same scale for both."""
    P = s[-1]; kc = (1.0 - 2 * STRIPS_MARGIN) / P
    vv = [Vector(p.co) for p in cab.data.vertices]
    dist = [[0.0] * NP for _ in range(S)]
    for r in range(1, S):
        for j in range(NP): dist[r][j] = dist[r - 1][j] + (vv[r * NP + j] - vv[(r - 1) * NP + j]).length
    dmax = max(max(row) for row in dist)
    face_v0 = STRIPS_MARGIN * 2 + dmax * kc
    uvs = []
    for pi_, poly in enumerate(cab.data.polygons):
        ids = list(poly.vertices)
        if pi_ < nring:
            js = [i % NP for i in ids]; jmax = max(js); uv = []
            for i in ids:
                r, j = divmod(i, NP); sj = s[NP] if (j == 0 and jmax == NP - 1) else s[j]
                uv.append((STRIPS_MARGIN + sj * kc, STRIPS_MARGIN + dist[r][j] * kc))
        else:
            uv = [(STRIPS_MARGIN + (vv[i].y + 1.30) * kc, face_v0 + (vv[i].z - G.Z_BOT) * kc) for i in ids]
        uvs.append(uv)
    _set_uv(cab, uvs, "UV_CabAtlas")
    cab["uv_scale_per_m"] = kc


# ------------------------------------------------------------------ section curves (edit, then rebuild)
def _poly_curve(name, pts, cyclic, collection):
    remove(name)
    cd = bpy.data.curves.new(name, "CURVE"); cd.dimensions = "3D"
    sp = cd.splines.new("POLY"); sp.points.add(len(pts) - 1); sp.use_cyclic_u = cyclic
    for p, co in zip(sp.points, pts): p.co = (*co, 1.0)
    ob = bpy.data.objects.new(name, cd); collection.objects.link(ob); ob.hide_render = True
    return ob

def write_section_curves(cab, cs):
    S, NP, nc, nr = cab["sections"], cab["np"], cab["face_cols"], cab["face_rows"]
    vv = [tuple(p.co) for p in cab.data.vertices]
    remove_prefix("CC_CabSection_"); remove_prefix("CC_CabFaceColumn_")
    for r in range(S):
        _poly_curve(f"CC_CabSection_{r:02d}", vv[r * NP:(r + 1) * NP], True, cs)
    off = S * NP
    for c in range(nc):
        _poly_curve(f"CC_CabFaceColumn_{c + 1:02d}", vv[off + c * nr: off + (c + 1) * nr], False, cs)

def rebuild_cab_from_curves():
    """Read CC_CabSection_* and CC_CabFaceColumn_* (world space) back into CC_Cab_Body and CC_Ref_Exterior."""
    cab = bpy.data.objects["CC_Cab_Body"]; ref = bpy.data.objects["CC_Ref_Exterior"]
    S, NP, nc, nr = cab["sections"], cab["np"], cab["face_cols"], cab["face_rows"]
    pts = []
    for r in range(S):
        ob = bpy.data.objects[f"CC_CabSection_{r:02d}"]; mw = ob.matrix_world
        sp = ob.data.splines[0]; assert len(sp.points) == NP, f"section {r} must keep {NP} points"
        pts += [mw @ Vector(p.co[:3]) for p in sp.points]
    for c in range(nc):
        ob = bpy.data.objects[f"CC_CabFaceColumn_{c + 1:02d}"]; mw = ob.matrix_world
        sp = ob.data.splines[0]; assert len(sp.points) == nr
        pts += [mw @ Vector(p.co[:3]) for p in sp.points]
    for vtx, p in zip(cab.data.vertices, pts): vtx.co = p
    off = ref["cab_vertex_offset"]
    for i, p in enumerate(pts): ref.data.vertices[off + i].co = p
    cab.data.update(); ref.data.update()
    return len(pts)


# ------------------------------------------------------------------ windscreen opening, flush glass, seal, wipers
def _ring_on(caster, loop, off):
    return [caster.on_face(y, z, off) for (y, z) in loop]

def front_glazing():
    cf = coll("CabCar_Front"); cc = coll("CC_Cab_Cutters"); ref = bpy.data.objects["CC_Ref_Exterior"]
    for n in ("CC_Windscreen", "CC_WindscreenSeal", "CC_WindscreenFrit", "CC_FrontDestLED", "CC_FrontDestGlass", "CC_FrontDestSeal"): remove(n)
    remove_prefix("CC_Wiper")
    # opening cutter (prism along X), editable via geom WS_* constants
    loop = G.ws_loop(0.0, 120); n = len(loop)
    vv = [(10.05, y, z) for (y, z) in loop] + [(11.50, y, z) for (y, z) in loop]
    ff = [list(range(n))[::-1], [n + i for i in range(n)]] + [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    cut = mk("CC_Cutter_Windscreen", vv, ff, [mat("PBR_RubberSeal") or mat("PBR_Rubber")], cc, smooth=False)
    cut.display_type = "WIRE"; cut.hide_render = True
    caster = Caster(ref)
    e = 0.030                                                     # glass overlaps the opening by 30 mm (bonded flange)
    z0, z1 = G.WS_ZC - G.WS_B - e, G.WS_ZC + G.WS_B + e; rows, cols = 36, 40
    zs = [z0 + (z1 - z0) * (0.5 - 0.5 * math.cos(pi * k / rows)) for k in range(rows + 1)]
    verts = []
    for z in zs:
        w = max(G.ws_halfwidth(min(max(z, z0 + 1e-5), z1 - 1e-5), e), 1e-3)
        for i in range(cols + 1):
            u = -1 + 2 * i / cols; u = math.copysign(abs(u) ** 0.85, u)
            verts.append(caster.on_face(w * u, z, 0.0060))
    faces = [[k * (cols + 1) + i, k * (cols + 1) + i + 1, (k + 1) * (cols + 1) + i + 1, (k + 1) * (cols + 1) + i] for k in range(rows) for i in range(cols)]
    g = mk("CC_Windscreen_Glass", verts, faces, [mat("PBR_WindscreenGlass") or mat("PBR_TintedGlass")], cf)
    bm = bmesh.new(); bm.from_mesh(g.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(g.data); bm.free()
    flip_if(g, lambda fc: fc.normal.x < 0)
    li = _ring_on(caster, G.ws_loop(e - 0.002, 200), 0.0040); lo = _ring_on(caster, G.ws_loop(e + 0.006, 200), 0.0040); m = len(li)
    sl = mk("CC_Windscreen_Seal", li + lo, [[i, (i + 1) % m, m + (i + 1) % m, m + i] for i in range(m)], [mat("PBR_RubberSeal") or mat("PBR_Rubber")], cf)
    flip_if(sl, lambda fc: fc.normal.x < 0)
    # wipers parked on the lower glass edge
    for k_, yp in enumerate((-0.66, 0.14)):
        arm = [caster.on_face(yp + 0.07 * i, G.WS_Z0 + 0.09 + 0.004 * i, 0.03) for i in range(10)]
        _tube(f"CC_Wiper_Arm_{k_ + 1}", arm, 0.009, mat("PBR_BlackPlastic"), cf)
        blade = [caster.on_face(yp + 0.08 + 0.07 * i, G.WS_Z0 + 0.105 + 0.004 * i, 0.016) for i in range(9)]
        _tube(f"CC_Wiper_Blade_{k_ + 1}", blade, 0.007, mat("PBR_BlackPlastic"), cf)
    return g

def _tube(name, pts, r, m, c):
    remove(name)
    cd = bpy.data.curves.new(name, "CURVE"); cd.dimensions = "3D"; cd.bevel_depth = r; cd.bevel_resolution = 2; cd.use_fill_caps = True
    sp = cd.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, co in zip(sp.points, pts): p.co = (*co, 1.0)
    cd.materials.append(m); ob = bpy.data.objects.new(name, cd); c.objects.link(ob); return ob


# ------------------------------------------------------------------ bumper (apron) + coupler, parametric
BUMPER = {"x_start": 10.05, "z_top": 0.915, "z_bottom_front": 0.58, "z_bottom_side": 0.84, "coupler_half_width": 0.27,
          "tuck_front": 0.055, "thickness": 0.014}

def _lathe_x(name, prof, center, seg, m, c):
    verts = []
    for k in range(seg):
        th = 2 * pi * k / seg
        for (r, a) in prof: verts.append((center[0] + a, center[1] + r * math.cos(th), center[2] + r * math.sin(th)))
    n = len(prof); faces = [[k * n + j, k * n + (j + 1) % n, ((k + 1) % seg) * n + (j + 1) % n, ((k + 1) % seg) * n + j] for k in range(seg) for j in range(n)]
    ob = mk(name, verts, faces, [m], c); bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
    return ob

def _box(name, m, c, cx, cy, cz, sx, sy, sz, bevel=0.01):
    x0, x1, y0, y1, z0, z1 = cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = mk(name, v, f, [m], c, smooth=False)
    md = ob.modifiers.new("Bevel", "BEVEL"); md.width = bevel; md.segments = 3; md.limit_method = "ANGLE"
    return ob

def bumper_and_coupler():
    cf = coll("CabCar_Front"); ref = bpy.data.objects["CC_Ref_Exterior"]; caster = Caster(ref); B = BUMPER
    for n in ("CC_FrontApron", "CC_ApronLip_A", "CC_ApronLip_B", "CC_Coupler", "CC_CouplerPocket", "CC_CouplerHose_L", "CC_CouplerHose_R", "CC_ObstacleDeflector"): remove(n)
    remove_prefix("CC_Bumper"); remove_prefix("CC_Coupler_")
    apron_m = mat_pbr("PBR_BumperMetallicGrey", (0.40, 0.405, 0.41), rough=0.33, metal=0.90, coat=0.3)
    piv = Vector((10.0, 0.0, 0.0)); pts = []
    for i in range(49):
        ph = math.radians(-90 + 180 * i / 48); d = Vector((math.cos(ph), math.sin(ph), 0))
        o = piv + d * 4.0; o.z = 0.93
        l, n = caster.cast(o, -d); pts.append(Vector((l.x, l.y, 0)) if l is not None else Vector((piv.x, d.y * 1.5, 0)))
    pts = [p for p in pts if p.x >= B["x_start"]]
    CO = B["coupler_half_width"]; out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        for yc in (-CO, CO):
            if (a.y - yc) * (b.y - yc) < 0: out.append(a.lerp(b, (yc - a.y) / (b.y - a.y)))
        out.append(b)
    pts = out; ctr = Vector((10.0, 0, 0))
    def frontness(p):
        u = max(0.0, min(1.0, (p.x - B["x_start"]) / 0.65)); return u * u * (3 - 2 * u)
    fs = [0.0, 0.16, 0.36, 0.58, 0.80, 1.0]; verts = []
    for fr in fs:
        for p in pts:
            w = frontness(p); zb = B["z_bottom_side"] - (B["z_bottom_side"] - B["z_bottom_front"]) * w
            z = B["z_top"] - (B["z_top"] - zb) * fr
            inset = 0.014 + (0.004 + B["tuck_front"] * w) * fr ** 1.5
            dv = (p - ctr); dv.z = 0; dv.normalize(); q = p - dv * inset; verts.append((q.x, q.y, z))
    n = len(pts); faces = []
    for r in range(len(fs) - 1):
        for i in range(n - 1):
            a, b = pts[i], pts[i + 1]
            if r >= 1 and a.x > 10.5 and abs(a.y) <= CO + 1e-4 and abs(b.y) <= CO + 1e-4: continue
            faces.append([r * n + i, r * n + i + 1, (r + 1) * n + i + 1, (r + 1) * n + i])
    ap = mk("CC_Bumper", verts, faces, [apron_m], cf)
    flip_if(ap, lambda fc: fc.normal.dot(Vector((fc.calc_center_median().x - 10.0, fc.calc_center_median().y, 0))) < 0)
    md = ap.modifiers.new("Solidify", "SOLIDIFY"); md.thickness = B["thickness"]; md.offset = -1.0; md.use_even_offset = True
    mod_smooth_by_angle(ap, 40)
    lip = [verts[(len(fs) - 1) * n + i] for i in range(n)]
    for side, nm in ((-1, "CC_Bumper_Lip_R"), (1, "CC_Bumper_Lip_L")):
        _tube(nm, [p for p, q in zip(lip, pts) if not (q.x > 10.5 and abs(q.y) < CO - 0.01) and q.y * side > 0], 0.010, mat("PBR_RubberSeal") or mat("PBR_Rubber"), cf)
    # coupler group: pocket, shank, head with guide cone, electrical head, hoses
    root = empty("CC_Coupler", cf, (10.95, 0, 0.70), 0.25, "ARROWS")
    grey = mat("PBR_BogieFrameGrey") or mat_pbr("PBR_BogieFrameGrey", (0.11, 0.115, 0.12), 0.45)
    blk = mat("PBR_UnderframeBlack_RAL9005")
    parts = [_box("CC_Coupler_Pocket", blk, cf, 10.72, 0, 0.70, 0.34, CO * 2 + 0.06, 0.30, 0.02),
             _lathe_x("CC_Coupler_Shank", [(0.02, -0.42), (0.072, -0.42), (0.072, 0.40), (0.02, 0.40)], (10.93, 0, 0.70), 28, grey, cf),
             _box("CC_Coupler_Head", grey, cf, 11.30, 0, 0.70, 0.16, 0.34, 0.32, 0.03),
             _lathe_x("CC_Coupler_GuideCone", [(0.003, 0), (0.070, 0), (0.042, 0.085), (0.003, 0.105)], (11.38, 0.085, 0.72), 24, grey, cf),
             _lathe_x("CC_Coupler_GuideFunnel", [(0.075, 0), (0.090, 0), (0.090, 0.012), (0.075, 0.012)], (11.38, -0.085, 0.72), 24, blk, cf),
             _box("CC_Coupler_ElectricHead", blk, cf, 11.24, 0, 0.49, 0.18, 0.28, 0.11, 0.012)]
    for s in (1, -1):
        pp = [(11.02, s * 0.22, 0.64)] + [(11.02 + 0.09 * math.sin(a), s * (0.22 + 0.04 * math.sin(a)), 0.64 - 0.17 * (1 - math.cos(a))) for a in [k * pi / 10 for k in range(1, 11)]]
        parts.append(_tube(f"CC_Coupler_Hose_{'L' if s > 0 else 'R'}", pp, 0.021, mat("PBR_RubberSeal") or mat("PBR_Rubber"), cf))
    for p in parts:
        mw = p.matrix_world.copy(); p.parent = root; p.matrix_parent_inverse = root.matrix_world.inverted(); p.matrix_world = mw
    # obstacle deflector (plough) under the bumper
    dv_, sel = [], [q for q in pts if abs(q.y) < 0.95]
    for z, back in ((0.58, 0.10), (0.34, 0.14), (0.20, 0.16)):
        for p in sel:
            d = (p - ctr); d.z = 0; d.normalize(); q = p - d * back; dv_.append((q.x, q.y * 0.88, z))
    m_ = len(sel)
    de = mk("CC_ObstacleDeflector", dv_, [[r * m_ + i, r * m_ + i + 1, (r + 1) * m_ + i + 1, (r + 1) * m_ + i] for r in range(2) for i in range(m_ - 1)], [blk], cf)
    md = de.modifiers.new("Solidify", "SOLIDIFY"); md.thickness = 0.02
    return ap


# ------------------------------------------------------------------ clean-up of rev-5 front objects that rev 6 replaces
REV5_REPLACED = ["CC_BodyShell", "CC_Windscreen", "CC_WindscreenSeal", "CC_FrontDestLED", "CC_FrontApron", "CC_ApronLip_A", "CC_ApronLip_B",
                 "CC_Coupler", "CC_CouplerPocket", "CC_CouplerHose_L", "CC_CouplerHose_R", "CC_ObstacleDeflector", "_NoseRef"]
REV5_PREFIXES = ["CC_HeadLamp_", "CC_TailLamp_", "CC_LampPod", "CC_WiperArm_", "CC_WiperBlade_", "CC_WiperPivot_"]

def remove_rev5_front():
    for n in REV5_REPLACED: remove(n)
    for p in REV5_PREFIXES: remove_prefix(p)
