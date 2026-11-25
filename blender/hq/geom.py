"""Pure-python geometry for the HQ commuter cab car (no bpy). Units m. +X forward (cab end), +Y left, +Z up, rail top z=0.
Engineering reference: TCDD E32000/E64000 mechanical training notes (body length Mc 21 900 mm, width 3 010, height 3 800,
underframe top 1 015 + 45 mm floor, side wall 2 440, bogie centres 16 000; door pitch / window sizes measured from Fig. 2-1-15).
Cab front shape and livery are an original design.
"""
import math

# ------------------------------------------------------------------ cross-section (from Fig. 2-1-14 dimensions)
Z_BOT, Z_ROOF, HALF_W = 0.88, 3.80, 1.505
FLOOR_Z = 1.06                      # 1.015 underframe top + 0.045 floating floor
EAVE_Z = 3.455                      # 1.015 + 2.440 side wall
CEIL_Z = FLOOR_Z + 2.258            # interior ceiling at centre
def side_y(z):
    """Side wall half-width: vertical lower wall, ~85 mm tumblehome towards the eave."""
    if z <= 2.0: return HALF_W
    u = min((z - 2.0) / 1.40, 1.0)
    return HALF_W - 0.085 * u ** 1.7
_R_ROOF = 3.82
def roof_z(y): return Z_ROOF - _R_ROOF + math.sqrt(_R_ROOF ** 2 - y * y)

_HALF = [(0.0, Z_BOT), (0.55, Z_BOT), (1.05, Z_BOT), (1.30, 0.884), (1.42, 0.895), (1.48, 0.915), (1.50, 0.95),
         (HALF_W, 1.00), (HALF_W, 1.03), (HALF_W, 1.05), (HALF_W, 1.20), (HALF_W, 1.30), (HALF_W, 1.55), (HALF_W, 1.70), (HALF_W, 1.78),
         (HALF_W, 1.86), (HALF_W, 1.92), (HALF_W, 1.94), (HALF_W, 1.96)]
_HALF += [(side_y(z), z) for z in (2.20, 2.45, 2.70, 2.96, 2.98, 3.00, 3.06, 3.15, 3.17, 3.19, 3.30, 3.40)]
_HALF += [(1.40, 3.455), (1.36, 3.52), (1.30, 3.565), (1.22, 3.60)]
_HALF += [(y, roof_z(y)) for y in (1.0, 0.75, 0.5, 0.25)] + [(0.0, Z_ROOF)]
PROFILE = _HALF + [(-y, z) for (y, z) in reversed(_HALF[1:-1])]
NP = len(PROFILE)
KCORNER = min(range(NP // 4), key=lambda i: (PROFILE[i][0] - HALF_W) ** 2 + (PROFILE[i][1] - 1.03) ** 2)

# ------------------------------------------------------------------ Mc car layout (x = 0 at body centre, cab at +X)
X_TIP = 10.95                        # body length 21.9 m
X_REAR = -10.95
NOSE_L = 1.25
X_NOSE0 = X_TIP - NOSE_L
DOORS = [-8.03, -4.00, 0.05, 4.08, 8.13]       # door centre lines (pitch ~4.03 m)
DOOR_HW, DOOR_Z0, DOOR_Z1 = 0.86, 1.03, 3.17     # plug door leaf outline 1.72 x 2.14 m
WIN_Z0, WIN_Z1, WIN_R = 1.94, 2.98, 0.14
BAND_Z0, BAND_Z1 = 1.86, 3.06
STRIPE_Z0, STRIPE_Z1 = 1.70, 1.78
SKIRT_Z1 = 1.20                     # dark lower skirt band (body side + cab front bumper zone)
CAB_DOOR = (9.03, 9.66, 1.05, 3.15)   # hinged cab side door (x0, x1, z0, z1)
CAB_WALL_X = 8.98
BOGIE_X = (7.95, -8.05)               # 16.0 m bogie centres
# roof: full-height curved centre block (Fig. 2-1-15 crown line X -7.52..5.15); lowered flat end wells for HVAC units
ZFLAT = 3.50
WELLS = [(-10.95, -7.67), (5.30, 8.86)]   # lowered roof zones; full-height crown exactly between X -7.52 and 5.15
BLEND = 0.15
WELL_RAMP_FRONT = 0.76          # long S-ramp from the front roof well up to the full cab crown (no step)
def _smoother(u): u = max(0.0, min(1.0, u)); return u * u * u * (u * (u * 6 - 15) + 10)
ZKNEE = 3.40                    # soft knee: roof shoulder rolls smoothly into the lowered well floor (no clipped crease)
def soft_roof(z):
    if z <= ZKNEE: return z
    k = ZFLAT - ZKNEE
    return ZKNEE + k * (1.0 - math.exp(-(z - ZKNEE) / k))
def crown_z(z, f): s = soft_roof(z); return s + (z - s) * f
def _smooth(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
def crown_factor(x):
    f = 1.0
    for a, b in WELLS:
        front = b > 0; bb = WELL_RAMP_FRONT if front else BLEND
        if a - (BLEND if a > X_REAR else 0) <= x <= b + bb:
            if x < a: f = min(f, _smooth((a - x) / BLEND))
            elif x > b: f = min(f, _smoother((x - b) / bb) if front else _smooth((x - b) / bb))
            else: f = 0.0
    return f
def windows():
    w = [(c - 0.685, c + 0.685) for c in (-6.01, -1.97, 2.06, 6.11)]   # 4 large windows per side (1.37 m)
    w.append((-9.70 - 0.325, -9.70 + 0.325))                           # small end window (0.65 m)
    return w

# cab nose (original shape) : short raked front within the 2 m cab
NOSE_T = [0.0, 0.05, 0.10, 0.16, 0.24, 0.32, 0.40, 0.48, 0.56, 0.64, 0.72, 0.80, 0.87, 0.93, 0.97, 1.0]
_TOP = [(0.0, Z_ROOF), (0.10, 3.785), (0.20, 3.69), (0.34, 3.43), (0.50, 2.98), (0.62, 2.55), (0.78, 2.16), (1.0, 1.92)]
_SY = [(0.0, 1.0), (0.30, 0.997), (0.50, 0.990), (0.70, 0.975), (0.85, 0.955), (0.95, 0.925), (1.0, 0.885)]
def _catmull(pts, t):
    xs = [p[0] for p in pts]
    i = max(0, min(len(pts) - 2, max(k for k in range(len(pts) - 1) if xs[k] <= t)))
    p0 = pts[max(i - 1, 0)][1]; p1 = pts[i][1]; p2 = pts[i + 1][1]; p3 = pts[min(i + 2, len(pts) - 1)][1]
    u = (t - xs[i]) / (xs[i + 1] - xs[i])
    return 0.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)
def nose_top(t): return _catmull(_TOP, t)
def nose_sy(t): return _catmull(_SY, t)

# ---------------------------------------------------------------- cab front v4 (original design, near-vertical compact face)
R_SIDE, R_TOP, R_BOT = 0.32, 0.40, 0.05          # plan corner radius, roof-to-windscreen fillet, bottom edge fillet
CROWN = 0.15                                      # plan crown of the face: centre ahead of the face edges (oval plan)
FACE_SY = (HALF_W - R_SIDE) / HALF_W              # face outline = affine-scaled body section (no folds)
FACE_Z0 = Z_BOT + R_BOT
FACE_SZ = (Z_ROOF - Z_BOT - R_TOP - R_BOT) / (Z_ROOF - Z_BOT)
RAKE = math.tan(math.radians(22.0))               # windscreen rake from vertical
def _ramp(x, w=0.30):
    if x <= 0: return 0.0
    if x < w: return x * x / (2 * w)
    return x - w / 2
def face_setback(z):
    s = max(0.0, min(1.0, (z - 1.20) / 1.0)); lean = 0.025 * s * s * (3 - 2 * s)
    return lean + RAKE * _ramp(z - 2.08)
def x_face(z): return X_TIP - face_setback(z)
def dxdz_face(z, h=1e-4): return (x_face(z + h) - x_face(z - h)) / (2 * h)
def face_x(y, z):
    """front face surface x(y, z): raked profile + parabolic plan crown (centre at X_TIP)"""
    return x_face(z) - CROWN * (y / FACE_YMAX) ** 2
def dxdy_face(y): return -2 * CROWN * y / FACE_YMAX ** 2
FACE_YMAX = HALF_W * FACE_SY
def face_point(j):
    y, z = PROFILE[j]
    return (y * FACE_SY, FACE_Z0 + (z - Z_BOT) * FACE_SZ)
def nose_fillets(nseg=8):
    """Per profile point: fillet from the straight body side (direction +x) into the front face, as a quadratic
    Bezier tangent to both surfaces (accounts for the windscreen rake)."""
    out = []
    for j, (y, z) in enumerate(PROFILE):
        fy, fz = face_point(j)
        dy, dz = fy - y, fz - z; R = math.hypot(dy, dz)
        if R < 1e-6: out.append(None); continue
        uy, uz = dy / R, dz / R
        tx = dxdz_face(fz) * uz + dxdy_face(fy) * uy   # x change per unit of inward travel on the face
        xb = face_x(fy, fz); cx = xb - R * tx; ax = cx - R
        out.append((ax, cx, xb, R, uy, uz))
    return out
FILLETS = nose_fillets()
X_NOSE0 = min(f[0] for f in FILLETS if f) - 0.05
NOSE_L = X_TIP - X_NOSE0

def ring_list():
    xs = {X_REAR, X_REAR + 0.03, X_NOSE0, CAB_WALL_X}
    for c in DOORS: xs |= {c - DOOR_HW - 0.02, c - DOOR_HW, c - DOOR_HW + 0.02, c, c + DOOR_HW - 0.02, c + DOOR_HW, c + DOOR_HW + 0.02}
    for a, b in windows() + [CAB_DOOR[:2]]: xs |= {a - 0.02, a, a + 0.02, b - 0.02, b, b + 0.02}
    for k in range(-11, 10): xs.add(k + 0.5)
    for a, b in WELLS:
        for x in (a - BLEND, a - BLEND / 2, a, b, b + BLEND / 2, b + BLEND): xs.add(round(x, 4))
        if b > 0:
            for k in range(1, 17): xs.add(round(b + WELL_RAMP_FRONT * k / 16, 4))
    rings = [(x, -1.0) for x in sorted(x for x in xs if X_REAR <= x < X_NOSE0)] + [(X_NOSE0, -1.0)]
    return rings

def classify(x, t, zo, yo):
    if zo <= Z_BOT + 0.006: return "UNDER"
    side = abs(yo) >= 1.40 and 0.95 < zo < 3.30
    if t < 0:
        if side:
            if DOOR_Z0 < zo < DOOR_Z1 and any(abs(x - c) < DOOR_HW for c in DOORS): return "HOLE"
            if CAB_DOOR[0] < x < CAB_DOOR[1] and CAB_DOOR[2] < zo < CAB_DOOR[3]: return "HOLE"
            if WIN_Z0 < zo < WIN_Z1 and any(a < x < b for a, b in windows()): return "HOLE"
            if BAND_Z0 < zo < BAND_Z1: return "BAND"
            if STRIPE_Z0 < zo < STRIPE_Z1: return "STRIPE"
            if zo < SKIRT_Z1: return "SKIRT"
            return "NOSE" if x > CAB_WALL_X else "STEEL"     # cab section painted like the nose
        if zo < SKIRT_Z1: return "SKIRT"
        return "ROOF" if zo > 3.30 else ("NOSE" if x > CAB_WALL_X else "STEEL")
    if 0.20 < t < 0.64 and zo > 3.0: return "WINDSCREEN"
    if 0.12 < t < 0.72 and zo > 2.60: return "BAND"
    if t <= 0.12 and BAND_Z0 < zo < BAND_Z1: return "BAND"
    if STRIPE_Z0 < zo < STRIPE_Z1: return "STRIPE"
    if zo < SKIRT_Z1: return "SKIRT"
    if t <= 0.10 and zo > 3.30: return "ROOF"
    return "NOSE"

def shell(nseg=8, bulge=0.0):
    rings = ring_list(); verts = []; faces = []; keys = []
    for x, t in rings:
        f = crown_factor(x)
        for (y, z) in PROFILE: verts.append((x, y, crown_z(z, f)))
    for i in range(len(rings) - 1):
        for j in range(NP):
            j2 = (j + 1) % NP
            faces.append([i * NP + j, (i + 1) * NP + j, (i + 1) * NP + j2, i * NP + j2])
            x = 0.5 * (rings[i][0] + rings[i + 1][0])
            zo = 0.5 * (PROFILE[j][1] + PROFILE[j2][1]); yo = 0.5 * (PROFILE[j][0] + PROFILE[j2][0])
            keys.append(classify(x, -1, zo, yo))
    # fillet grid: k = 0 last body ring (X_NOSE0), k = 1 straight end (ax), k = 2..nseg+1 Bezier samples to the face
    base = (len(rings) - 1) * NP
    cols = [base + j for j in range(NP)]
    grid = [cols]
    for k in range(1, nseg + 2):
        row = []
        for j, (y, z) in enumerate(PROFILE):
            ax, cx, xb, R, uy, uz = FILLETS[j]
            if k == 1: p = (ax, y, z)
            else:
                t = (k - 1) / nseg
                bx_ = (1 - t) ** 2 * ax + 2 * (1 - t) * t * cx + t * t * xb
                s_ = t * t * R                     # inward travel: Bezier from (ax,0) via (cx,0) to (xb,R)
                p = (bx_, y + uy * s_, z + uz * s_)
            verts.append(p); row.append(len(verts) - 1)
        grid.append(row)
    for k in range(len(grid) - 1):
        for j in range(NP):
            j2 = (j + 1) % NP
            q = [grid[k][j], grid[k + 1][j], grid[k + 1][j2], grid[k][j2]]
            faces.append(q)
            zc = sum(verts[v][2] for v in q) / 4
            bottom = PROFILE[j][1] <= Z_BOT + 0.006 and PROFILE[j2][1] <= Z_BOT + 0.006
            keys.append("UNDER" if bottom and k < len(grid) - 3 else ("SKIRT" if zc < SKIRT_Z1 else "NOSE"))
    # front face: Coons patch over the face loop (follows the raked side profile exactly), slight plan bulge
    loop = grid[-1]
    k = KCORNER; idx = lambda i: loop[i % NP]
    bottom = [idx(i) for i in range(-k, k + 1)]
    top = [idx(i) for i in range(NP // 2 + k, NP // 2 - k - 1, -1)]
    left = [idx(i) for i in range(-k, -k - (NP // 2 - 2 * k) - 1, -1)]
    right = [idx(i) for i in range(k, NP // 2 - k + 1)]
    nu, nv = len(bottom) - 1, len(right) - 1
    P = lambda vid: verts[vid]; gd = {}
    for iu in range(nu + 1):
        for iv in range(nv + 1):
            if iv == 0: gd[iu, iv] = bottom[iu]; continue
            if iv == nv: gd[iu, iv] = top[iu]; continue
            if iu == 0: gd[iu, iv] = left[iv]; continue
            if iu == nu: gd[iu, iv] = right[iv]; continue
            u, v = iu / nu, iv / nv; c = [0, 0, 0]
            for d in range(3):
                c[d] = ((1 - v) * P(bottom[iu])[d] + v * P(top[iu])[d] + (1 - u) * P(left[iv])[d] + u * P(right[iv])[d]
                        - ((1 - u) * (1 - v) * P(bottom[0])[d] + u * (1 - v) * P(bottom[nu])[d] + (1 - u) * v * P(top[0])[d] + u * v * P(top[nu])[d]))
            c[0] = face_x(c[1], c[2]) + bulge * math.sin(math.pi * u) * math.sin(math.pi * v) ** 0.5
            verts.append(tuple(c)); gd[iu, iv] = len(verts) - 1
    for iu in range(nu):
        for iv in range(nv):
            q = [gd[iu, iv], gd[iu, iv + 1], gd[iu + 1, iv + 1], gd[iu + 1, iv]]
            faces.append(q); keys.append("SKIRT" if sum(verts[vv][2] for vv in q) / 4 < SKIRT_Z1 - 0.03 else "NOSE")
    return verts, faces, keys, rings

# windscreen opening on the face (y half-width, z range, corner radius) and lamp band height
WS_HW, WS_Z0, WS_Z1, WS_R = 0.98, 2.05, 3.17, 0.20
WS_ZC, WS_B, WS_A, WS_TAPER, WS_N = 2.61, 0.56, 0.985, -0.11, 4.6
MK_ZC, MK_B, MK_A, MK_TAPER, MK_N = 2.785, 0.835, 1.11, -0.15, 3.2
def mask_halfwidth(z, e=0.0):
    b = MK_B + e; zz = z - MK_ZC
    if abs(zz) >= b: return 0.0
    a = MK_A + e + MK_TAPER * zz
    return a * (1 - abs(zz / b) ** MK_N) ** (1 / MK_N)
def mask_loop(e=0.0, n=200):
    out = []
    for k in range(n):
        th = 2 * math.pi * k / n; c, s = math.cos(th), math.sin(th)
        zz = (MK_B + e) * math.copysign(abs(s) ** (2 / MK_N), s)
        a = MK_A + e + MK_TAPER * zz
        out.append((a * math.copysign(abs(c) ** (2 / MK_N), c), MK_ZC + zz))
    return out
def ws_halfwidth(z, e=0.0):
    """half-width of the windscreen outline (tapered superellipse) at height z, grown by e"""
    b = WS_B + e; zz = z - WS_ZC
    if abs(zz) >= b: return 0.0
    a = WS_A + e + WS_TAPER * zz
    return a * (1 - abs(zz / b) ** WS_N) ** (1 / WS_N)
def ws_loop(e=0.0, n=160):
    out = []
    for k in range(n):
        th = 2 * math.pi * k / n; c, s = math.cos(th), math.sin(th)
        zz = (WS_B + e) * math.copysign(abs(s) ** (2 / WS_N), s)
        a = WS_A + e + WS_TAPER * zz
        out.append((a * math.copysign(abs(c) ** (2 / WS_N), c), WS_ZC + zz))
    return out
LAMP_Z = 1.42

GANGWAY_W, GANGWAY_H = 2.18, 2.05     # structural end opening (Fig. 2-1-12); clear passage inside bellows ~1.5 m
GANGWAY_LEN = 0.70                     # gangway length between adjacent car ends (doc: 700 mm), 0.35 m per car

def end_wall(x, open_w=GANGWAY_W, open_z0=FLOOR_Z, open_z1=FLOOR_Z + GANGWAY_H, inset=0.012):
    """Rear end wall with the wide gangway opening; sits just inside the shell ring."""
    f = crown_factor(x)
    prof = [(y, crown_z(z, f)) for (y, z) in PROFILE]       # follow the lowered roof well
    outer = [(x, y * (1 - inset / HALF_W), Z_BOT + inset + (z - Z_BOT) * (1 - 2 * inset / (Z_ROOF - Z_BOT))) for (y, z) in prof]
    cy, cz = 0.0, 0.5 * (open_z0 + open_z1); hw, hh = open_w / 2, (open_z1 - open_z0) / 2
    inner = []
    for (y, z) in PROFILE:
        a = math.atan2(z - cz, y - cy); dy, dz = math.cos(a), math.sin(a)
        s = min(hw / abs(dy) if abs(dy) > 1e-9 else 1e9, hh / abs(dz) if abs(dz) > 1e-9 else 1e9)
        inner.append((x, cy + dy * s, cz + dz * s))
    return outer + inner, [[j, (j + 1) % NP, NP + (j + 1) % NP, NP + j] for j in range(NP)]

def side_point(x, z, side, offset): return (x, side * (side_y(z) + offset), z)

def rounded_rect(x0, x1, z0, z1, r, seg=5):
    r = min(r, (x1 - x0) / 2 - 1e-4, (z1 - z0) / 2 - 1e-4); pts = []
    for (cx, cz, a0) in ((x1 - r, z0 + r, -90), (x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg); pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts

def frame_ring(x0, x1, z0, z1, w, r, side, offset, seg=5):
    """Rounded-rectangle frame (trim / gasket) of width w around an opening, conforming to the body side."""
    inner = rounded_rect(x0, x1, z0, z1, r, seg); outer = rounded_rect(x0 - w, x1 + w, z0 - w, z1 + w, r + w, seg)
    verts = [side_point(x, z, side, offset) for (x, z) in inner] + [side_point(x, z, side, offset) for (x, z) in outer]
    n = len(inner)
    return verts, [[j, (j + 1) % n, n + (j + 1) % n, n + j] for j in range(n)]

def strip(x0, x1, z0, z1, side, offset, nz=3):
    """Flat trim strip conforming to the side (seams, seals, drip mouldings)."""
    zs = [z0 + (z1 - z0) * k / nz for k in range(nz + 1)]
    verts = [side_point(x, z, side, offset) for z in zs for x in (x0, x1)]
    return verts, [[2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2] for i in range(nz)]

def pane_grid(x0, x1, z0, z1, r, side, offset, rows=18):
    zs = sorted({z0, z1} | {z0 + r * (1 - math.cos(math.radians(90 * k / 6))) for k in range(1, 6)}
                | {z1 - r * (1 - math.cos(math.radians(90 * k / 6))) for k in range(1, 6)}
                | {z0 + (z1 - z0) * k / rows for k in range(1, rows)})
    verts = []
    for z in zs:
        dz = max(z0 + r - z, z - (z1 - r), 0.0)
        ins = r - math.sqrt(max(r * r - dz * dz, 0.0)) if dz > 0 else 0.0
        xl, xr = x0 + ins, x1 - ins
        for x in (xl, 0.5 * (xl + xr), xr): verts.append(side_point(x, z, side, offset))
    faces = [[3 * i, 3 * i + 1, 3 * (i + 1) + 1, 3 * (i + 1)] for i in range(len(zs) - 1)]
    faces += [[3 * i + 1, 3 * i + 2, 3 * (i + 1) + 2, 3 * (i + 1) + 1] for i in range(len(zs) - 1)]
    return verts, faces

def leaf(x0, x1, z0, z1, hole, side, offset, nz=12):
    hx0, hx1, hz0, hz1 = hole
    xs = sorted({x0, hx0, hx1, x1})
    zs = sorted({z0, hz0, hz1, z1} | {z0 + (z1 - z0) * k / nz for k in range(1, nz)})
    verts = [side_point(x, z, side, offset) for z in zs for x in xs]
    nx = len(xs); faces = []
    for iz in range(len(zs) - 1):
        for ix in range(nx - 1):
            xm, zm = 0.5 * (xs[ix] + xs[ix + 1]), 0.5 * (zs[iz] + zs[iz + 1])
            if hx0 < xm < hx1 and hz0 < zm < hz1: continue
            f = [iz * nx + ix, iz * nx + ix + 1, (iz + 1) * nx + ix + 1, (iz + 1) * nx + ix]
            faces.append(f if side < 0 else list(reversed(f)))
    return verts, faces

# reference values measured from the training-notes side elevation (metres from the cab tip) for verification
REF = {"door_centres_from_tip": [2.82, 6.87, 10.90, 14.95, 18.98], "large_window_centres_from_tip": [4.84, 8.89, 12.92, 16.96],
       "end_window_from_tip": 20.65, "bogie_centres_from_tip": [3.00, 19.00], "body_length": 21.90}

assert CAB_DOOR[1] + 0.03 < X_NOSE0, (CAB_DOOR, X_NOSE0)
assert WELLS[1][1] + WELL_RAMP_FRONT < X_NOSE0 - 0.04

if __name__ == "__main__":
    v, f, k, r = shell()
    from collections import Counter
    print("profile", NP, "rings", len(r), "verts", len(v), "faces", len(f), Counter(k))
    print("model door centres from tip", [round(X_TIP - c, 2) for c in sorted(DOORS, reverse=True)], "ref", REF["door_centres_from_tip"])
    print("model windows from tip", [round(X_TIP - 0.5 * (a + b), 2) for a, b in windows()])
    print("bogies from tip", [round(X_TIP - b, 2) for b in BOGIE_X], "roof", Z_ROOF, "eave", EAVE_Z, "ceiling", round(CEIL_Z, 3))
