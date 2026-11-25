"""Rev 6 - lamp system module (own pod design, parametric, exactly symmetric).
Parameters live as custom properties on the empty  CC_LampRig  (N-panel > Item > Properties, or Object Properties > Custom Properties).
After changing them run  rebuild_lamps().
Fine adjustment without rebuilding: move / rotate / scale the left empties CC_HeadLamp_L and CC_TailLamp_L -
the right side (CC_HeadLamp_R / CC_TailLamp_R, children of CC_MirrorY) follows through drivers.
Each optic is made of separate meshes: _Bezel, _Reflector, _Emitter, (_DRL), _Lens, plus a light and a Roblox anchor."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
from common import (G, pi, coll, remove, remove_prefix, mk, empty, mat_pbr, Caster, prop, mirror_parent, mirror_twin)

DEFAULTS = {   # name: (value, min, max, description)
    "pod_angle_deg":   (35.0, 0.0, 80.0, "projection direction of the pod, degrees from +X towards the side"),
    "pod_center_y":    (1.08, 0.5, 1.45, "pod centre, |y| on the front face (m)"),
    "pod_center_z":    (1.42, 1.0, 2.0, "pod centre height above rail (m)"),
    "pod_length":      (0.58, 0.2, 1.0, "pod length along the surface (m)"),
    "pod_height":      (0.22, 0.08, 0.5, "pod height (m)"),
    "pod_tilt_deg":    (20.0, -45.0, 45.0, "diagonal tilt (shear) of the pod; + rises towards the outer side"),
    "pod_corner_r":    (0.09, 0.0, 0.25, "corner radius of the pod outline (m)"),
    "pod_depth":       (0.040, 0.01, 0.044, "recess depth into the 45 mm shell (m)"),
    "head_u":          (-0.13, -0.5, 0.5, "head lamp position along the pod (m, + = outer)"),
    "head_w":          (-0.004, -0.2, 0.2, "head lamp offset across the pod (m, + = up)"),
    "head_radius":     (0.078, 0.02, 0.15, "head lamp reflector radius (m)"),
    "tail_u":          (0.175, -0.5, 0.5, "tail lamp position along the pod (m)"),
    "tail_w":          (0.014, -0.2, 0.2, "tail lamp offset across the pod (m)"),
    "tail_radius":     (0.048, 0.015, 0.12, "tail lamp reflector radius (m)"),
    "aim_forward":     (0.20, 0.0, 1.0, "0 = optics follow the surface normal, 1 = aimed straight ahead"),
    "head_light_w":    (180.0, 0.0, 5000.0, "spot light power for renders (W)"),
    "tail_light_w":    (6.0, 0.0, 500.0, "tail point light power (W)"),
}

def rig():
    c = coll("CC_Lamps")
    ob = bpy.data.objects.get("CC_LampRig")
    if ob is None:
        ob = empty("CC_LampRig", c, (11.2, 0, 1.42), 0.15, "CUBE")
    for k, (v, mn, mx, d) in DEFAULTS.items():
        if k not in ob.keys(): prop(ob, k, v, mn, mx, d)
    return ob

def P(r, k): return float(r[k])

# ------------------------------------------------------------------ geometry helpers
def rr(w, h, r, seg=14):
    r = max(1e-4, min(r, w / 2 - 1e-4, h / 2 - 1e-4)); pts = []
    for (cu, cv, a0) in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg); pts.append((cu + r * math.cos(a), cv + r * math.sin(a)))
    return pts

def resample(loop, step=0.008):
    out = []
    for a, b in zip(loop, loop[1:] + loop[:1]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        for k in range(n): out.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
    return out

class Pod:
    def __init__(self, r, caster):
        self.r = r; self.c = caster
        a = math.radians(P(r, "pod_angle_deg"))
        self.D = Vector((math.cos(a), math.sin(a), 0.0)); self.U = Vector((-math.sin(a), math.cos(a), 0.0)); self.W = Vector((0, 0, 1.0))
        self.C = Vector(caster.on_face(P(r, "pod_center_y"), P(r, "pod_center_z"), 0.0))
        self.shear = math.tan(math.radians(P(r, "pod_tilt_deg")))
    def outline(self, scale=1.0):
        loop = resample(rr(P(self.r, "pod_length"), P(self.r, "pod_height"), P(self.r, "pod_corner_r")))
        return [(u * scale, w * scale + u * scale * self.shear) for (u, w) in loop]
    def hit(self, u, w):
        o = self.C + self.U * u + self.W * w + self.D * 1.2
        l, n = self.c.cast(o, -self.D)
        return (l, n) if l is not None else (o - self.D * 1.2, self.D)

def pod_cutter_mesh(pod, scales=(1.0, 0.88, 0.74, 0.60, 0.46, 0.32, 0.18)):
    """curved slab following the surface on both caps (outer +50 mm, inner -depth)."""
    depth = P(pod.r, "pod_depth")
    rings = [[pod.hit(u, w) for (u, w) in pod.outline(k)] for k in scales]
    m = len(rings[0]); l0, n0 = pod.hit(0.0, 0.0); R = len(rings)
    outer = [tuple(l + n * 0.05) for ring in rings for l, n in ring] + [tuple(l0 + n0 * 0.05)]
    inner = [tuple(l - n * depth) for ring in rings for l, n in ring] + [tuple(l0 - n0 * depth)]
    N = len(outer); v = outer + inner; f = []
    for base, flip in ((0, False), (N, True)):
        for rr_ in range(R - 1):
            for i in range(m):
                q = [base + rr_ * m + i, base + rr_ * m + (i + 1) % m, base + (rr_ + 1) * m + (i + 1) % m, base + (rr_ + 1) * m + i]
                f.append(q[::-1] if flip else q)
        last = base + (R - 1) * m; ctr = base + N - 1
        for i in range(m):
            t = [last + i, last + (i + 1) % m, ctr]; f.append(t[::-1] if flip else t)
    f += [[i, N + i, N + (i + 1) % m, (i + 1) % m] for i in range(m)]
    return v, f

def lathe_local(name, prof, seg, m, c, closed=False):
    n = len(prof); verts = []
    for k in range(seg):
        th = 2 * pi * k / seg
        for (r, a) in prof: verts.append((r * math.cos(th), r * math.sin(th), a))
    faces = []
    for k in range(seg):
        k2 = (k + 1) % seg
        for j in range(n if closed else n - 1):
            j2 = (j + 1) % n; faces.append([k * n + j, k * n + j2, k2 * n + j2, k2 * n + j])
    ob = mk(name, verts, faces, [m], c)
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
    return ob

def frame_from_axis(p, z):
    z = Vector(z).normalized(); x = Vector((0, 0, 1)).cross(z)
    x = x.normalized() if x.length > 1e-6 else Vector((0, 1, 0)); y = z.cross(x).normalized()
    m = Matrix((x, y, z)).transposed().to_4x4(); m.translation = p
    return m

# ------------------------------------------------------------------ materials (separate per function -> separate control in Roblox)
def materials():
    return {
        "bezel": mat_pbr("LAMP_Bezel_Black", (0.012, 0.012, 0.013), rough=0.5),
        "refl": mat_pbr("LAMP_Reflector", (0.70, 0.71, 0.73), rough=0.14, metal=1.0),
        "head": mat_pbr("LAMP_Head_Emitter", (1.0, 0.96, 0.88), rough=0.1, emit=6.0),
        "drl": mat_pbr("LAMP_DRL_Emitter", (1.0, 0.97, 0.92), rough=0.2, emit=2.5),
        "tail": mat_pbr("LAMP_Tail_Emitter", (1.0, 0.03, 0.02), rough=0.2, emit=3.0),
        "lens": mat_pbr("LAMP_Lens_Clear", (0.85, 0.86, 0.88), rough=0.01, alpha=0.12),
        "lens_red": mat_pbr("LAMP_Lens_Red", (0.35, 0.004, 0.006), rough=0.02, alpha=0.55),
    }

def build_optic(kind, r, pod, M, c):
    u = P(r, f"{kind}_u"); w = P(r, f"{kind}_w"); rad = P(r, f"{kind}_radius")
    l, n = pod.hit(u, w + u * pod.shear)
    axis = (n * (1 - P(r, "aim_forward")) + Vector((1.0, 0.0, 0.0)) * P(r, "aim_forward")).normalized()
    nm = "CC_HeadLamp_L" if kind == "head" else "CC_TailLamp_L"
    root = empty(nm, c, (0, 0, 0), rad * 1.6, "CIRCLE"); root.matrix_world = frame_from_axis(l, axis)
    parts = [lathe_local(nm + "_Bezel", [(rad - 0.003, -0.010), (rad + 0.010, -0.010), (rad + 0.010, -0.017), (rad - 0.003, -0.017)], 48, M["bezel"], c, True),
             lathe_local(nm + "_Reflector", [(rad, -0.010), (0.93 * rad, -0.016), (0.78 * rad, -0.024), (0.55 * rad, -0.031), (0.28 * rad, -0.035), (0.10 * rad, -0.0365), (0.002, -0.037)], 48, M["refl"], c)]
    if kind == "head":
        parts.append(lathe_local(nm + "_Emitter", [(0.001, -0.024), (0.38 * rad, -0.024), (0.38 * rad, -0.031), (0.001, -0.031)], 32, M["head"], c, True))
        parts.append(lathe_local(nm + "_DRL", [(rad + 0.012, -0.011), (rad + 0.019, -0.011), (rad + 0.019, -0.016), (rad + 0.012, -0.016)], 64, M["drl"], c, True))
        parts.append(lathe_local(nm + "_Lens", [(0.001, -0.0045), (0.5 * rad, -0.0052), (0.85 * rad, -0.0068), (rad + 0.004, -0.0090)], 48, M["lens"], c))
    else:
        parts.append(lathe_local(nm + "_Emitter", [(0.001, -0.022), (0.55 * rad, -0.022), (0.55 * rad, -0.027), (0.001, -0.027)], 32, M["tail"], c, True))
        parts.append(lathe_local(nm + "_Lens", [(0.001, -0.0045), (0.5 * rad, -0.0052), (0.85 * rad, -0.0068), (rad + 0.004, -0.0090)], 48, M["lens_red"], c))
    anchor = mk(nm.replace("CC_", "CC_RobloxAnchor_"), [(0, 0, -0.02), (0.005, 0, -0.025), (0, 0.005, -0.025), (0, 0, -0.03)], [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2)], [M["bezel"]], c, smooth=False)
    anchor.hide_render = True; parts.append(anchor)
    ld = bpy.data.lights.get(nm + "_Light")
    if ld: bpy.data.lights.remove(ld)
    if kind == "head":
        ld = bpy.data.lights.new(nm + "_Light", "SPOT"); ld.energy = P(r, "head_light_w"); ld.color = (1.0, 0.95, 0.86); ld.spot_size = math.radians(55); ld.spot_blend = 0.6
    else:
        ld = bpy.data.lights.new(nm + "_Light", "POINT"); ld.energy = P(r, "tail_light_w"); ld.color = (1.0, 0.05, 0.03)
    ld.shadow_soft_size = rad * 0.4
    lo = bpy.data.objects.new(nm + "_Light", ld); c.objects.link(lo); parts.append(lo)
    for p in parts: p.parent = root; p.matrix_parent_inverse = Matrix.Identity(4)
    lo.location = (0, 0, -0.02); lo.rotation_euler = (pi, 0, 0)
    return root, parts

def mirror_optic(left_root, left_parts, mirror, c):
    rn = left_root.name.replace("_L", "_R")
    root = empty(rn, c, (0, 0, 0), left_root.empty_display_size, left_root.empty_display_type)
    mirror_twin(left_root, root, mirror)
    for p in left_parts:
        nn = p.name.replace("_L_", "_R_").replace("_L", "_R") if p.name.endswith("_L") else p.name.replace("_L_", "_R_")
        remove(nn)
        q = bpy.data.objects.new(nn, p.data); c.objects.link(q)
        q.parent = root; q.matrix_parent_inverse = Matrix.Identity(4); q.matrix_basis = p.matrix_basis.copy(); q.hide_render = p.hide_render
    return root

def rebuild_lamps():
    r = rig(); c = coll("CC_Lamps"); cc = coll("CC_Cab_Cutters")
    for pre in ("CC_HeadLamp_", "CC_TailLamp_", "CC_RobloxAnchor_HeadLamp_", "CC_RobloxAnchor_TailLamp_", "CC_Cutter_LampPod_"): remove_prefix(pre)
    caster = Caster(bpy.data.objects["CC_Ref_Exterior"])
    pod = Pod(r, caster)
    v, f = pod_cutter_mesh(pod)
    blk = bpy.data.materials.get("PBR_BlackPlastic") or mat_pbr("PBR_BlackPlastic", (0.012, 0.012, 0.013), 0.55)
    cl = mk("CC_Cutter_LampPod_L", v, f, [blk], cc, smooth=False)
    vr = [(x, -y, z) for (x, y, z) in v]; fr = [list(reversed(q)) for q in f]
    crr = mk("CC_Cutter_LampPod_R", vr, fr, [blk], cc, smooth=False)
    for o in (cl, crr): o.display_type = "WIRE"; o.hide_render = True
    M = materials(); mirror = mirror_parent(coll("CC_Paint"))
    for kind in ("head", "tail"):
        root, parts = build_optic(kind, r, pod, M, c)
        mirror_optic(root, parts, mirror, c)
    return cl, crr
