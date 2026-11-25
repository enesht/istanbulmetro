"""Detail stages for the HQ cab car (run after build_hq.py in the same namespace).
Front equipment, bogies, underframe, roof HVAC, interior. All parts are independent meshes."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
pi = math.pi

# ------------------------------------------------------------------ extra PBR materials
def extra_materials():
    M["CHROME"] = mat_plain("PBR_Chrome", (0.90, 0.90, 0.92), rough=0.06, metal=1.0)
    M["BOGIE"] = mat_paint("PBR_BogieGrey", (0.055, 0.058, 0.062), rough=0.55, coat=0.0)
    M["WHEEL"] = mat_plain("PBR_WheelSteel", (0.55, 0.54, 0.52), rough=0.32, metal=1.0)
    M["RUST"] = mat_plain("PBR_WheelWeb", (0.18, 0.14, 0.12), rough=0.75, metal=0.3)
    M["SPRING"] = mat_paint("PBR_SpringPaint", (0.03, 0.03, 0.035), rough=0.45, coat=0.0)
    M["HEADLAMP"] = mat_plain("PBR_HeadlampLED", (1.0, 0.96, 0.86), rough=0.1, emit=6.0)
    M["TAIL"] = mat_plain("PBR_TailLED", (1.0, 0.03, 0.02), rough=0.2, emit=3.0)
    M["LENS"] = mat_glass("PBR_LensGlass", tint=(0.95, 0.95, 0.95), rough=0.01)
    M["LED"] = mat_plain("PBR_CeilingLED", (1.0, 0.98, 0.94), rough=0.3, emit=4.0)
    M["SEAT"] = mat_paint("PBR_SeatShell", (0.02, 0.17, 0.20), rough=0.38, coat=0.3)
    M["POLE"] = mat_plain("PBR_PolishedStainless", (0.86, 0.86, 0.87), rough=0.12, metal=1.0)
    M["YELLOW"] = mat_paint("PBR_SafetyYellow", (0.95, 0.70, 0.02), rough=0.4, coat=0.0)
    M["CABLE"] = mat_plain("PBR_Cable", (0.02, 0.02, 0.02), rough=0.6)
    M["DIFFUSER"] = mat_plain("PBR_DiffuserGrey", (0.55, 0.56, 0.57), rough=0.5, metal=0.2)

# ------------------------------------------------------------------ generic mesh builders
def _recalc(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
def lathe(name, prof, axis, center, seg, mat, c, smooth=True, angle_deg=None, seg_mat=None):
    n = len(prof); verts = []
    for k in range(seg):
        th = 2 * pi * k / seg; cs, sn = math.cos(th), math.sin(th)
        for (r, a) in prof:
            if axis == "y": verts.append((center[0] + r * cs, center[1] + a, center[2] + r * sn))
            elif axis == "z": verts.append((center[0] + r * cs, center[1] + r * sn, center[2] + a))
            else: verts.append((center[0] + a, center[1] + r * cs, center[2] + r * sn))
    faces = []
    for k in range(seg):
        k2 = (k + 1) % seg
        for j in range(n):
            j2 = (j + 1) % n; faces.append([k * n + j, k * n + j2, k2 * n + j2, k2 * n + j])
    mats = mat if isinstance(mat, list) else [mat]
    fm = None
    if seg_mat: fm = [seg_mat(prof[j], prof[(j + 1) % n]) for k in range(seg) for j in range(n)]
    ob = mk(name, verts, faces, mats, c, face_mats=fm, smooth=smooth); _recalc(ob)
    if angle_deg: smooth_by_angle(ob, angle_deg)
    return ob
def loft(name, sections, mat, c, caps=True, smooth=True, subd=0, angle=None):
    n = len(sections[0]); verts = [p for s in sections for p in s]; faces = []
    for i in range(len(sections) - 1):
        for j in range(n):
            j2 = (j + 1) % n; faces.append([i * n + j, (i + 1) * n + j, (i + 1) * n + j2, i * n + j2])
    if caps:
        faces.append(list(range(n))[::-1]); faces.append([(len(sections) - 1) * n + j for j in range(n)])
    ob = mk(name, verts, faces, [mat] if not isinstance(mat, list) else mat, c, smooth=smooth); _recalc(ob)
    if subd:
        md = ob.modifiers.new("Subdivision", "SUBSURF"); md.levels = subd; md.render_levels = subd; apply_mods(ob)
    if angle: smooth_by_angle(ob, angle)
    return ob
def rr(w, h, r, seg=4):
    """rounded rectangle loop in (u,v), centred, CCW"""
    r = min(r, w / 2 - 1e-4, h / 2 - 1e-4); pts = []
    for (cu, cv, a0) in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg); pts.append((cu + r * math.cos(a), cv + r * math.sin(a)))
    return pts
def bbox_bevel(name, mat, cx, cy, cz, sx, sy, sz, c, bevel=0.012, inset_sides=False, louvres=0):
    x0, x1, y0, y1, z0, z1 = cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = mk(name, v, f, [mat], c, smooth=False)
    if inset_sides:
        bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
        side = [fc for fc in bm.faces if abs(fc.normal.z) < 0.5]
        bmesh.ops.inset_individual(bm, faces=side, thickness=min(0.035, sz * 0.15), depth=-0.008)
        bm.to_mesh(ob.data); bm.free()
    md = ob.modifiers.new("Bevel", "BEVEL"); md.width = bevel; md.segments = 3; md.limit_method = "ANGLE"
    apply_mods(ob); smooth_by_angle(ob, 40)
    if louvres:
        lv = []
        for k in range(louvres):
            x = x0 + 0.08 + k * (sx - 0.16) / max(louvres - 1, 1)
            for s in (-1, 1):
                yy = cy + s * (sy / 2 + 0.006)
                lv.append(bbox_bevel(name + "_lv", M["BLACK"], x, yy, cz, 0.018, 0.012, sz * 0.6, c, bevel=0.003))
        join(lv, name + "_Louvres")
    return ob
def join(objs, name):
    objs = [o for o in objs if o]
    if not objs: return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    objs[0].name = name; objs[0].data.name = name; return objs[0]
def tube(name, pts, radius, mat, c, res=3, cyclic=False):
    cd = bpy.data.curves.new(name, "CURVE"); cd.dimensions = "3D"; cd.bevel_depth = radius; cd.bevel_resolution = res
    cd.use_fill_caps = True; cd.resolution_u = 6
    sp = cd.splines.new("POLY"); sp.points.add(len(pts) - 1); sp.use_cyclic_u = cyclic
    for p, co in zip(sp.points, pts): p.co = (*co, 1.0)
    cd.materials.append(mat)
    ob = bpy.data.objects.new(name, cd); c.objects.link(ob); activate(ob)
    bpy.ops.object.convert(target="MESH"); ob = bpy.context.view_layer.objects.active; ob.name = name
    for p in ob.data.polygons: p.use_smooth = True
    return ob
def arc(p0, p1, ctr, n=8):
    """points on circular arc from p0 to p1 around ctr (all 3D, same plane)"""
    a, b, cc = Vector(p0), Vector(p1), Vector(ctr); va, vb = a - cc, b - cc; r = va.length
    out = []
    for k in range(n + 1):
        v = va.slerp(vb, k / n) if hasattr(va, "slerp") else va.lerp(vb, k / n)
        out.append(tuple(cc + v.normalized() * r))
    return out
SHELL = None
def hit(y, z, x0=13.0, d=(-1, 0, 0), target=None):
    ob = target or SHELL
    ok, loc, nor, _ = ob.ray_cast(Vector((x0, y, z)), Vector(d))
    if ok: return loc, nor
    return Vector((11.08, y, z)), Vector((1, 0, 0))
def hitw(y, z): return hit(y, z, target=bpy.data.objects["CC_Windscreen"])

# ------------------------------------------------------------------ front equipment
def build_front():
    c = coll("CabCar_Front")
    # headlight clusters: bezel conforming to the front panel + LED lenses + tail strip
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        loop = rr(0.50, 0.17, 0.06, 5); secs = []
        for off in (0.0, 0.012):
            ring = []
            for (u, v) in loop:
                loc, nor = hit(s * 0.80 + u, 1.42 + v)
                ring.append(tuple(loc + nor * off))
            secs.append(ring)
        bz = loft(f"CC_HeadlightBezel_{S}", secs, M["BLACK"], c, caps=True, angle=40)
        loc, nor = hit(s * 0.80, 1.42); q = nor.to_track_quat("Z", "Y")
        for k, (du, rad, mat) in enumerate(((s * 0.12, 0.055, M["HEADLAMP"]), (-s * 0.04, 0.040, M["HEADLAMP"]), (-s * 0.155, 0.030, M["TAIL"]))):
            l2, n2 = hit(s * 0.80 + du, 1.42)
            prof = [(0.002, 0.000), (rad, 0.000), (rad, 0.010), (rad * 0.8, 0.022), (0.002, 0.026)]
            lens = lathe(f"CC_Lamp_{S}{k + 1}", prof, "z", (0, 0, 0), 24, mat, c)
            lens.matrix_world = Matrix.Translation(l2 + n2 * 0.010) @ n2.to_track_quat("Z", "Y").to_matrix().to_4x4()
            ring = lathe(f"CC_LampRing_{S}{k + 1}", [(rad + 0.004, 0.0), (rad + 0.012, 0.0), (rad + 0.012, 0.014), (rad + 0.004, 0.016)], "z", (0, 0, 0), 24, M["CHROME"], c)
            ring.matrix_world = lens.matrix_world.copy()
        # red tail/marker LED strip under the bezel
        loop2 = rr(0.34, 0.028, 0.012, 3); secs = []
        for off in (0.0, 0.008):
            secs.append([tuple(hit(s * 0.80 + u, 1.27 + v)[0] + hit(s * 0.80 + u, 1.27 + v)[1] * off) for (u, v) in loop2])
        loft(f"CC_TailStrip_{S}", secs, M["TAIL"], c, caps=True)
    # LED destination display behind the windscreen (upper band)
    for dz, mat, nm in ((0.0, M["BLACK"], "CC_DestinationHousing"), (0.012, M["AMBER"], "CC_DestinationLED")):
        w, h = (1.50, 0.20) if dz == 0 else (1.38, 0.12)
        ring = []
        for (u, v) in rr(w, h, 0.02, 2):
            loc, nor = hitw(u, 3.42 + v)
            ring.append(tuple(loc - nor * (0.10 - dz)))
        loft(nm, [ring, [tuple(Vector(p) - hitw(0, 3.42)[1] * 0.02) for p in ring]], mat, c, caps=True)
    # windscreen wipers (parked along the lower edge)
    for s in (1, -1):
        yp = -0.55 if s > 0 else 0.20      # both wipers park parallel, sweeping toward +Y
        l0, n0 = hitw(yp, 2.52)
        pts = []
        for k in range(9):
            yy = yp + 0.085 * k; zz = 2.52 + 0.010 * k
            l, nn = hitw(yy, zz); pts.append(tuple(l + nn * 0.025))
        tube(f"CC_WiperArm_{'L' if s > 0 else 'R'}", pts, 0.008, M["BLACK"], c, res=2)
        bl = [tuple(hitw(yp + 0.06 + 0.085 * k, 2.555 + 0.010 * k)[0] + hitw(yp + 0.06 + 0.085 * k, 2.555 + 0.010 * k)[1] * 0.012) for k in range(9)]
        tube(f"CC_WiperBlade_{'L' if s > 0 else 'R'}", bl, 0.006, M["BLACK"], c, res=1)
        lathe(f"CC_WiperPivot_{'L' if s > 0 else 'R'}", [(0.003, 0), (0.03, 0), (0.03, 0.02), (0.003, 0.025)], "x", (l0.x - 0.02, l0.y, l0.z), 16, M["BLACK"], c)
    # automatic coupler (generic): draft gear box, shank, head with guide cone, electrical head
    parts = [bbox_bevel("cpl1", M["BOGIE"], 10.40, 0, 0.74, 0.9, 0.42, 0.26, c, bevel=0.02, inset_sides=True),
             bbox_bevel("cpl2", M["BOGIE"], 11.02, 0, 0.74, 0.6, 0.16, 0.16, c, bevel=0.02),
             bbox_bevel("cpl3", M["BOGIE"], 11.33, 0, 0.74, 0.14, 0.38, 0.34, c, bevel=0.035)]
    parts.append(lathe("cpl4", [(0.003, 0), (0.08, 0), (0.05, 0.09), (0.003, 0.11)], "x", (11.40, 0.09, 0.76), 20, M["BOGIE"], c))
    parts.append(bbox_bevel("cpl5", M["BLACK"], 11.29, 0, 0.52, 0.16, 0.30, 0.12, c, bevel=0.015))
    join(parts, "CC_Coupler")
    # obstacle deflector (pilot): curved plate in plan, two ribs
    secs = []
    for z in (0.16, 0.30, 0.45, 0.60, 0.72):
        sec = []
        for k in range(15):
            u = -1 + 2 * k / 14
            y = u * 1.20; x = 11.10 - 0.38 * u * u - 0.06 * (0.72 - z)
            sec.append((x, y, z))
        back = [(p[0] - 0.035, p[1], p[2]) for p in reversed(sec)]
        secs.append(sec + back)
    loft("CC_Pilot", secs, M["BOGIE"], c, caps=True, angle=35)
    for s in (1, -1):
        bbox_bevel(f"CC_PilotBracket_{'L' if s > 0 else 'R'}", M["BOGIE"], 10.62, s * 0.75, 0.74, 0.5, 0.06, 0.28, c, bevel=0.01)
    # anti-climber ribs across the lower front edge
    rb = []
    for k in range(4):
        z = 1.00 + k * 0.05; ring = []
        for kk in range(13):
            y = -0.9 + 1.8 * kk / 12
            l, nn = hit(y, z); ring.append(tuple(l + nn * 0.018))
        rb.append(tube(f"ac{k}", ring, 0.010, M["BLACK"], c, res=2))
    join(rb, "CC_AntiClimber")

# ------------------------------------------------------------------ bogie (original trailer bogie design)
WHEEL_R, BACK2BACK, WB = 0.43, 1.36, 2.50
def build_bogie(tag, bx, motor=False):
    c = coll("CabCar_Bogie_" + tag)
    wheel_prof = [(0.095, -0.07), (0.17, -0.07), (0.18, -0.02), (0.36, 0.010), (0.40, 0.000), (0.458, 0.000), (0.461, 0.012),
                  (0.452, 0.026), (WHEEL_R, 0.032), (WHEEL_R - 0.007, 0.165), (0.41, 0.168), (0.385, 0.150), (0.36, 0.125),
                  (0.19, 0.095), (0.18, 0.125), (0.095, 0.125)]
    for ia, ax in enumerate((-WB / 2, WB / 2)):
        parts = []
        for s in (1, -1):
            pr = [(r, s * (BACK2BACK / 2 + a)) if s > 0 else (r, -(BACK2BACK / 2 + a)) for (r, a) in wheel_prof]
            if s < 0: pr = pr[::-1]
            parts.append(lathe("w", pr, "y", (bx + ax, 0, WHEEL_R), 48, [M["WHEEL"], M["RUST"]], c,
                               seg_mat=lambda p, q: 0 if min(p[0], q[0]) >= 0.42 else 1))
            # axle-mounted brake disc (ventilated look) + calliper
            dprof = [(0.12, -0.055), (0.32, -0.055), (0.32, -0.008), (0.30, -0.008), (0.30, 0.008), (0.32, 0.008), (0.32, 0.055), (0.12, 0.055)]
            parts.append(lathe("d", dprof, "y", (bx + ax, s * 0.33, WHEEL_R), 40, M["RUST"], c))
        parts.append(lathe("ax", [(0.075, -1.06), (0.088, -1.06), (0.088, 1.06), (0.075, 1.06)], "y", (bx + ax, 0, WHEEL_R), 24, M["WHEEL"], c))
        join(parts, f"CC_Wheelset_{tag}{ia + 1}")
        for s in (1, -1):
            S = "L" if s > 0 else "R"
            bbox_bevel(f"CC_Calliper_{tag}{ia + 1}{S}", M["BOGIE"], bx + ax - 0.29 * (1 if ax > 0 else -1), s * 0.33, WHEEL_R, 0.16, 0.17, 0.24, c, bevel=0.015)
            # axle box: housing around journal + saddle
            hb = [lathe("ab", [(0.06, -0.11), (0.13, -0.11), (0.14, -0.06), (0.14, 0.06), (0.13, 0.11), (0.06, 0.11)], "y", (bx + ax, s * 1.00, WHEEL_R), 28, M["BOGIE"], c)]
            hb.append(bbox_bevel("ab2", M["BOGIE"], bx + ax, s * 1.00, 0.585, 0.46, 0.24, 0.03, c, bevel=0.008))
            hb.append(lathe("ab3", [(0.003, 0.0), (0.08, 0.0), (0.08, 0.03), (0.003, 0.035)], "y", (bx + ax, s * 1.105 - (0 if s > 0 else 0), WHEEL_R), 20, M["BOGIE"], c) if s > 0 else
                      lathe("ab3", [(0.003, -0.035), (0.08, -0.03), (0.08, 0.0), (0.003, 0.0)], "y", (bx + ax, -1.105, WHEEL_R), 20, M["BOGIE"], c))
            join(hb, f"CC_AxleBox_{tag}{ia + 1}{S}")
            # primary suspension: twin coil springs per axle box
            for dx in (-0.13, 0.13):
                pts = []; turns, h, r = 3.5, 0.11, 0.065; z0 = 0.60
                for k in range(int(turns * 24) + 1):
                    th = 2 * pi * k / 24; pts.append((bx + ax + dx + r * math.cos(th), s * 1.00 + r * math.sin(th), z0 + h * k / (turns * 24)))
                tube(f"CC_PrimarySpring_{tag}{ia + 1}{S}{'a' if dx < 0 else 'b'}", pts, 0.015, M["SPRING"], c, res=2)
    # side frames: lofted box-section beams with a lowered (fish-belly) centre
    for s in (1, -1):
        S = "L" if s > 0 else "R"; secs = []
        for x in (-1.62, -1.50, -1.25, -0.95, -0.55, 0.0, 0.55, 0.95, 1.25, 1.50, 1.62):
            u = min(abs(x) / 1.25, 1.0); zc = 0.58 + (0.78 - 0.58) * (u ** 2); hh = 0.30 - 0.16 * (u ** 2)
            if abs(x) > 1.5: hh *= 0.8
            secs.append([(bx + x, s * 1.00 + a, zc + b) for (a, b) in rr(0.20, hh, 0.035, 3)])
        loft(f"CC_SideFrame_{tag}{S}", secs, M["BOGIE"], c, caps=True, angle=35)
        # secondary suspension: air spring bellows on the side frame
        ap = [(0.08, 0.0), (0.24, 0.0), (0.27, 0.02), (0.31, 0.055), (0.315, 0.08), (0.30, 0.11), (0.26, 0.135), (0.24, 0.15), (0.08, 0.15)]
        lathe(f"CC_AirSpring_{tag}{S}", ap, "z", (bx, s * 1.00, 0.725), 40, M["BLACK"], c)
        # vertical + yaw dampers
        tube(f"CC_VertDamper_{tag}{S}", [(bx + 0.45, s * 1.14, 0.60), (bx + 0.45, s * 1.14, 0.82)], 0.038, M["BOGIE"], c)
        tube(f"CC_VertDamperRod_{tag}{S}", [(bx + 0.45, s * 1.14, 0.80), (bx + 0.45, s * 1.14, 0.87)], 0.016, M["CHROME"], c)
        tube(f"CC_YawDamper_{tag}{S}", [(bx - 0.95, s * 1.22, 0.80), (bx - 0.05, s * 1.22, 0.80)], 0.04, M["BOGIE"], c)
    # transom + lateral damper + brake cylinder housings
    loft(f"CC_Transom_{tag}", [[(bx + a, y, 0.58 + b) for (a, b) in rr(0.34, 0.22, 0.04, 3)] for y in (-1.0, 1.0)], M["BOGIE"], c, caps=True, angle=35)
    tube(f"CC_LatDamper_{tag}", [(bx + 0.20, -0.45, 0.76), (bx + 0.20, 0.45, 0.76)], 0.035, M["BOGIE"], c)
    if motor:
        lathe(f"CC_TractionMotor_{tag}", [(0.05, -0.30), (0.24, -0.30), (0.26, -0.25), (0.26, 0.25), (0.24, 0.30), (0.05, 0.30)], "y", (bx + 0.55, 0, 0.47), 32, M["BOGIE"], c)
    # balise/ATP antenna on the leading bogie
    if tag == "F":
        bbox_bevel("CC_ATPAntenna", M["YELLOW"], bx + 1.95, 0, 0.17, 0.30, 0.40, 0.06, c, bevel=0.01)

# ------------------------------------------------------------------ underframe equipment (between bogies)
def build_underframe():
    c = coll("CabCar_Underframe")
    boxes = [("CC_AuxConverter", -5.2, -0.62, 1.8, 0.95, 0.50, True, 9), ("CC_BatteryBox", -5.0, 0.70, 1.3, 0.80, 0.46, True, 0),
             ("CC_BrakeControl", -2.4, -0.70, 1.2, 0.85, 0.44, True, 0), ("CC_Compressor", -2.3, 0.65, 1.4, 0.95, 0.48, True, 7),
             ("CC_HVBox", 0.4, 0.0, 2.2, 1.6, 0.40, True, 0), ("CC_LowVoltage", 3.2, -0.66, 1.4, 0.80, 0.44, True, 0),
             ("CC_ToiletTank", 3.3, 0.70, 1.2, 0.82, 0.50, True, 0), ("CC_SignallingCubicle", 5.2, 0.0, 0.9, 1.6, 0.38, True, 0)]
    for (nm, x, y, sx, sy, sz, ins, lv) in boxes:
        bbox_bevel(nm, M["UNDER"], x, y, 0.875 - sz / 2, sx, sy, sz, c, bevel=0.018, inset_sides=ins, louvres=lv)
    for k, x in enumerate((-0.9, 1.9)):
        tp = [(0.04, -0.80), (0.16, -0.80), (0.21, -0.74), (0.23, -0.65), (0.23, 0.65), (0.21, 0.74), (0.16, 0.80), (0.04, 0.80)]
        lathe(f"CC_AirReservoir_{k + 1}", tp, "x", (x, -1.12, 0.66), 28, M["UNDER"], c)
    # sole-bar cable conduits along both sides
    for s in (1, -1):
        tube(f"CC_Conduit_{'L' if s > 0 else 'R'}", [(-6.2, s * 1.30, 0.85), (6.2, s * 1.30, 0.85)], 0.025, M["CABLE"], c)

# ------------------------------------------------------------------ roof HVAC unit with fairings + grilles
def build_roof():
    c = coll("CabCar_Roof")
    zr = G.Z_ROOF - 0.005
    def housing(name, x0, x1, w, h):
        secs = []
        for x, ww, hh in ((x0, w * 0.78, 0.02), (x0 + 0.20, w * 0.95, h * 0.75), (x0 + 0.50, w, h), (x1 - 0.50, w, h), (x1 - 0.20, w * 0.95, h * 0.75), (x1, w * 0.78, 0.02)):
            secs.append([(x, a, zr + hh / 2 + b) for (a, b) in rr(ww, hh, min(0.06, hh / 2.2), 4)])
        return loft(name, secs, M["ROOF"], c, caps=True, subd=1, angle=35)
    # HVAC units seated in the lowered roof wells at both car ends (2 saloon units + 1 cab unit)
    zb = G.ZFLAT - 0.005
    def unit(name, x0, x1, w, h):
        secs = []
        for x, ww, hh in ((x0, w * 0.92, h * 0.55), (x0 + 0.06, w, h), (x1 - 0.06, w, h), (x1, w * 0.92, h * 0.55)):
            secs.append([(x, a, zb + hh / 2 + bb) for (a, bb) in rr(ww, hh, min(0.07, hh / 2.2), 4)])
        ob = loft(name, secs, M["ROOF"], c, caps=True, subd=1, angle=35)
        gr = [bbox_bevel("g", M["BLACK"], x0 + 0.25 + k * 0.18, 0, zb + h + 0.002, 0.06, w * 0.62, 0.006, c, bevel=0.002)
              for k in range(int((x1 - x0 - 0.5) / 0.18) + 1)]
        for s in (1, -1):
            gr += [bbox_bevel("l", M["BLACK"], x0 + 0.3 + k * 0.12, s * (w / 2 + 0.003), zb + h * 0.5, 0.05, 0.006, h * 0.5, c, bevel=0.002)
                   for k in range(int((x1 - x0 - 0.6) / 0.12) + 1)]
        join(gr, name + "_Grilles")
        return ob
    unit("CC_SaloonHVAC_Rear", -10.80, -7.72, 2.30, 0.28)
    unit("CC_SaloonHVAC_Front", 5.32, 8.02, 2.30, 0.28)
    unit("CC_CabHVAC", 8.12, 8.78, 1.60, 0.22)
    for s in (1, -1):   # rain gutters along both sides
        tube(f"CC_RainGutter_{'L' if s > 0 else 'R'}", [(G.X_REAR + 0.05, s * 1.415, 3.43), (G.X_NOSE0 - 0.05, s * 1.415, 3.43)], 0.010, M["STEEL"], c, res=1)
    lathe("CC_RadioAntenna", [(0.003, 0.0), (0.05, 0.0), (0.05, 0.03), (0.012, 0.05), (0.008, 0.30), (0.003, 0.31)], "z", (2.0, 0.4, G.Z_ROOF - 0.01), 16, M["BLACK"], c)

# ------------------------------------------------------------------ interior
def seat_profile():
    # side section of one GRP seat shell (d = distance from wall, z) for floor at 1.05; shifted to FLOOR_Z below
    return [(0.05, 2.02), (0.09, 1.86), (0.11, 1.70), (0.13, 1.60), (0.17, 1.54), (0.46, 1.515), (0.50, 1.50), (0.505, 1.475),
            (0.47, 1.46), (0.20, 1.47), (0.14, 1.50), (0.10, 1.58), (0.07, 1.70), (0.045, 1.86), (0.02, 2.01)]
def seat(name, xa, xb, s, c, wall_y=1.455, dz=0.0):
    sp = seat_profile(); secs = []
    for xx, sc in ((xa, 0.92), (xa + 0.02, 0.985), (xa + 0.05, 1.0), (xb - 0.05, 1.0), (xb - 0.02, 0.985), (xb, 0.92)):
        cz = 1.72
        secs.append([(xx, s * (wall_y - d * sc), dz + cz + (z - cz) * sc) for (d, z) in sp])
    return loft(name, secs, M["SEAT"], c, caps=True, subd=1, angle=50)
def build_interior():
    c = coll("CabCar_Interior")
    wall_y = 1.455; dz = G.FLOOR_Z - 1.05; RAIL_Z = G.FLOOR_Z + 1.85; RAIL_Y = wall_y - 0.52
    D = sorted(G.DOORS)
    bays = [(a + G.DOOR_HW + 0.04, b - G.DOOR_HW - 0.04) for a, b in zip(D[:-1], D[1:])]
    for bi, (x0, x1) in enumerate(bays):                       # 5-seater benches (8 per car)
        n = 5; w = (x1 - x0) / n
        for s in (1, -1):
            S = "L" if s > 0 else "R"
            for k in range(n):
                seat(f"CC_Seat_{S}{bi + 1}_{k + 1}", x0 + k * w + 0.002, x0 + (k + 1) * w - 0.002, s, c, wall_y, dz)
            bbox_bevel(f"CC_SeatFrame_{S}{bi + 1}", M["POLE"], 0.5 * (x0 + x1), s * (wall_y - 0.24), G.FLOOR_Z + 0.37, (x1 - x0) - 0.05, 0.36, 0.04, c, bevel=0.01)
            for xe in (x0, x1):                                  # bench-end vertical poles up to the longitudinal rail
                tube(f"CC_BenchPole_{S}{bi + 1}{'a' if xe == x0 else 'b'}", [(xe, s * RAIL_Y, G.FLOOR_Z + 0.47), (xe, s * RAIL_Y, RAIL_Z)], 0.017, M["POLE"], c)
    # rear end bay: fixed 3-seater on the right, flip-down 3-seater + wheelchair space on the left
    x0, x1 = G.X_REAR + 0.14, D[0] - G.DOOR_HW - 0.04; w = 0.45
    for k in range(3):
        seat(f"CC_Seat_R0_{k + 1}", x0 + k * w + 0.01, x0 + (k + 1) * w - 0.01, -1, c, wall_y, dz)
        seat(f"CC_FlipSeat_L0_{k + 1}", x0 + k * w + 0.01, x0 + (k + 1) * w - 0.01, 1, c, wall_y, dz)
    for s in (1, -1):
        bbox_bevel(f"CC_SeatFrame_{'L' if s > 0 else 'R'}0", M["POLE"], x0 + 0.675, s * (wall_y - 0.24), G.FLOOR_Z + 0.37, 1.30, 0.36, 0.04, c, bevel=0.01)
    bbox_bevel("CC_WheelchairPlate", M["STRIPE"], x0 + 1.35 + 0.5 * (x1 - x0 - 1.35), 1.25, G.FLOOR_Z + 0.002, x1 - x0 - 1.40, 0.40, 0.004, c, bevel=0.001)
    tube("CC_WheelchairRail", [(x0 + 1.40, 1.40, G.FLOOR_Z + 0.85), (x1 - 0.05, 1.40, G.FLOOR_Z + 0.85)], 0.017, M["POLE"], c)
    # longitudinal handrails on both sides of the aisle + hanging handholds
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        tube(f"CC_Handrail_{S}", [(G.X_REAR + 0.3, s * RAIL_Y, RAIL_Z), (D[-1] + G.DOOR_HW, s * RAIL_Y, RAIL_Z)], 0.017, M["POLE"], c)
        hh = []
        for (bx0, bx1) in bays:
            for k in range(5):
                xh = bx0 + (k + 0.5) * (bx1 - bx0) / 5
                hh.append(lathe("h", [(0.050, -0.012), (0.062, -0.012), (0.062, 0.012), (0.050, 0.012)], "x", (xh, s * RAIL_Y, RAIL_Z - 0.30), 16, M["BLACK"], c))
                hh.append(bbox_bevel("hs", M["BLACK"], xh, s * RAIL_Y, RAIL_Z - 0.13, 0.03, 0.012, 0.26, c, bevel=0.003))
        join(hh, f"CC_Handholds_{S}")
    # draft screens at the doorway edges + trifurcate poles at each doorway centre
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        for i, cx in enumerate(D):
            for e in (-1, 1):
                if i == 0 and e < 0: pass
                xs = cx + e * (G.DOOR_HW + 0.025)
                if not (G.X_REAR < xs < G.CAB_WALL_X - 0.05): continue
                v = [(xs, s * wall_y, G.FLOOR_Z + 0.52), (xs, s * (wall_y - 0.50), G.FLOOR_Z + 0.52), (xs, s * (wall_y - 0.50), G.FLOOR_Z + 1.32), (xs, s * wall_y, G.FLOOR_Z + 1.32)]
                g = mk(f"CC_DraftScreen_{S}{i + 1}{'a' if e < 0 else 'b'}", v, [(0, 1, 2, 3)], [M["GLASS"]], c, smooth=False)
                solidify(g, 0.012); apply_mods(g)
                tube(f"CC_ScreenFrame_{S}{i + 1}{'a' if e < 0 else 'b'}", [(xs, s * wall_y, G.FLOOR_Z + 0.52), (xs, s * (wall_y - 0.50), G.FLOOR_Z + 0.52),
                     (xs, s * (wall_y - 0.50), G.FLOOR_Z + 1.32), (xs, s * wall_y, G.FLOOR_Z + 1.55)], 0.016, M["POLE"], c, res=2)
            y = s * 0.72; zt = G.FLOOR_Z + 1.20; ztop = G.CEIL_Z - 0.06
            trunk = [(cx, y, G.FLOOR_Z), (cx, y, zt)]
            br = [tube("t0", trunk + [(cx, y, ztop)], 0.017, M["POLE"], c)]
            for e in (-1, 1):
                pts = [(cx, y, zt)] + [(cx + e * 0.42 * (1 - math.cos(a)), y, zt + (ztop - zt) * math.sin(a)) for a in [k * (pi / 2) / 8 for k in range(1, 9)]]
                br.append(tube("tb", pts, 0.017, M["POLE"], c))
            join(br, f"CC_TrifurcatePole_{S}{i + 1}")
            # passenger information display in the corner panel above each doorway
            bbox_bevel(f"CC_PIDHousing_{S}{i + 1}", M["BLACK"], cx, s * 1.20, G.CEIL_Z - 0.18, 0.62, 0.05, 0.14, c, bevel=0.008)
            bbox_bevel(f"CC_PIDScreen_{S}{i + 1}", M["AMBER"], cx, s * 1.172, G.CEIL_Z - 0.18, 0.56, 0.004, 0.09, c, bevel=0.001)
    # ceiling: aluminium honeycomb panel arc (centre 2 258 mm above floor) + corner panels + LED lines + diffuser
    secs = []
    for x in (G.X_REAR + 0.06, G.CAB_WALL_X - 0.02):
        ring = [(x, -1.30 + 2.6 * k / 16, (G.CEIL_Z - 0.26) + 0.26 * (1 - (-1 + 2 * k / 16) ** 2)) for k in range(17)]
        ring += [(x, p[1], p[2] + 0.03) for p in reversed(ring)]
        secs.append(ring)
    loft("CC_CeilingPanel", secs, M["INTERIOR"], c, caps=True, angle=35)
    for s in (1, -1):
        zz = (G.CEIL_Z - 0.26) + 0.26 * (1 - 0.42 ** 2) - 0.012
        ring = [(G.X_REAR + 0.4, s * 0.55 + a, zz + b) for (a, b) in rr(0.16, 0.012, 0.005, 2)]
        loft(f"CC_LEDStrip_{'L' if s > 0 else 'R'}", [ring, [(G.CAB_WALL_X - 0.4, p[1], p[2]) for p in ring]], M["LED"], c, caps=True)
    ring = [(G.X_REAR + 0.4, a, G.CEIL_Z - 0.012 + b) for (a, b) in rr(0.36, 0.02, 0.008, 2)]
    loft("CC_AirDiffuser", [ring, [(G.CAB_WALL_X - 0.4, p[1], p[2]) for p in ring]], M["DIFFUSER"], c, caps=True)
    for i, cx in enumerate(D):
        for s in (1, -1):
            bbox_bevel(f"CC_DoorStrip_{'L' if s > 0 else 'R'}{i + 1}", M["YELLOW"], cx, s * 1.36, G.FLOOR_Z + 0.002, 2 * G.DOOR_HW, 0.10, 0.004, c, bevel=0.001)
    # cab partition wall with hinged door
    xw = G.CAB_WALL_X; fz = G.FLOOR_Z
    v = [(xw, -1.42, fz), (xw, -0.38, fz), (xw, -0.38, fz + 1.95), (xw, 0.38, fz + 1.95), (xw, 0.38, fz), (xw, 1.42, fz), (xw, 1.42, 3.30), (xw, -1.42, 3.30)]
    wall = mk("CC_CabWall", v, [(0, 1, 2, 3, 4, 5, 6, 7)], [M["INTERIOR"]], c, smooth=False)
    bm = bmesh.new(); bm.from_mesh(wall.data); bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(wall.data); bm.free()
    solidify(wall, 0.05); apply_mods(wall)
    cd = mk("CC_CabPartitionDoor", [(xw - 0.01, -0.37, fz + 0.01), (xw - 0.01, 0.37, fz + 0.01), (xw - 0.01, 0.37, fz + 1.94), (xw - 0.01, -0.37, fz + 1.94)], [(0, 1, 2, 3)], [M["DOOR"]], c, smooth=False)
    solidify(cd, 0.04); apply_mods(cd)
    mk("CC_CabDoorWindow", [(xw - 0.055, -0.22, fz + 1.10), (xw - 0.055, 0.22, fz + 1.10), (xw - 0.055, 0.22, fz + 1.75), (xw - 0.055, -0.22, fz + 1.75)], [(0, 1, 2, 3)], [M["GLASS"]], c, smooth=False)
    # driver desk + driver seat (compact 2 m cab)
    secs = []
    for y in (-1.15, -0.85, 0.85, 1.15):
        sc = 0.85 if abs(y) > 1.0 else 1.0
        secs.append([(9.62 + a * sc, y, fz + b * sc) for (a, b) in ((0, 0), (0.80, 0), (0.92, 0.60), (0.78, 0.74), (0.30, 0.88), (0.0, 0.88))])
    loft("CC_DriverDesk", secs, M["BLACK"], c, caps=True, subd=1, angle=40)
    ds = []
    for xx, sc in ((-0.23, 0.92), (-0.21, 1.0), (0.21, 1.0), (0.23, 0.92)):
        ds.append([(9.10 + (d - 0.02) * sc, xx, dz + 1.72 + (z - 1.72) * sc) for (d, z) in seat_profile()])
    loft("CC_DriverSeat", ds, M["BLACK"], c, caps=True, subd=1, angle=50)
    # wide walk-through gangway: inner portal frame, corrugated outer bellows, face frame, bridge plate
    X0 = G.X_REAR; W, H = G.GANGWAY_W, G.GANGWAY_H
    def ring(x, w, h, r, zc):
        return [(x, a, zc + bb) for (a, bb) in rr(w, h, r, 5)]
    zc = fz + H / 2
    loft("CC_GangwayPortal", [ring(X0 + 0.07, W + 0.24, H + 0.20, 0.22, zc + 0.03), ring(X0 + 0.07, W, H, 0.12, zc),
                              ring(X0 - 0.01, W, H, 0.12, zc), ring(X0 - 0.01, W + 0.24, H + 0.20, 0.22, zc + 0.03)], M["BLACK"], c, caps=False, angle=40)
    outer = []
    for k in range(13):
        g = 0.05 if k % 2 else 0.0
        outer.append(ring(X0 - 0.02 - k * 0.020, W + 0.50 + g, H + 0.42 + g, 0.30, zc + 0.10))
    loft("CC_GangwayBellows", outer, M["BLACK"], c, caps=False, angle=60)
    loft("CC_GangwayInner", [ring(X0 - 0.02, W + 0.02, H + 0.02, 0.13, zc), ring(X0 - 0.26, W + 0.02, H + 0.02, 0.13, zc)], M["RIM"], c, caps=False, angle=60)
    loft("CC_GangwayFaceFrame", [ring(X0 - 0.26, W + 0.02, H + 0.02, 0.13, zc), ring(X0 - 0.26, W + 0.56, H + 0.48, 0.31, zc + 0.10),
                                 ring(X0 - 0.30, W + 0.56, H + 0.48, 0.31, zc + 0.10), ring(X0 - 0.30, W + 0.02, H + 0.02, 0.13, zc)], M["BOGIE"], c, caps=False, angle=40)
    bp = [bbox_bevel("bp", M["BOGIE"], X0 - 0.14, 0, fz - 0.004, 0.30, W - 0.10, 0.012, c, bevel=0.003)]
    for k in range(9):
        bp.append(bbox_bevel("br", M["RIM"], X0 - 0.14, -W / 2 + 0.15 + k * (W - 0.30) / 8, fz + 0.003, 0.28, 0.012, 0.004, c, bevel=0.001))
    join(bp, "CC_GangwayBridgePlate")

def run_details():
    global SHELL
    SHELL = bpy.data.objects["CC_BodyShell"]
    extra_materials()
    if not globals().get("V4"): build_front()
    if not globals().get("V3"): build_bogie("F", G.BOGIE_X[0], motor=False); build_bogie("R", G.BOGIE_X[1], motor=False)
    build_underframe(); build_roof(); build_interior()

run_details()
print("details done:", stats())
