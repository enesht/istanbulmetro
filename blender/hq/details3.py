"""Revision 3: production-quality pass on the cab car master.
Flush plug doors + thin glazing frits, livery from the doc colour palette (own arrangement), moulded GRP benches
on wall cantilevers (Fig. 1-2-4), handrail system per Fig. 1-2-5 (horizontal pole 220 mm under the ceiling, 825/1175 mm
fixing pitch, trifurcate pole at each doorway), corner-panel displays, detailed ceiling, wide gangway per end structure
(Fig. 2-1-12, 700 mm gangway length) and a fully rebuilt mechanical bogie.
Runs after build_hq.py + details.py + details2.py with V3 = True (same namespace)."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
pi = math.pi
FZ = G.FLOOR_Z
WALL_Y = 1.455

def mats3():
    M["SILVER"] = M["STEEL"]
    M["NAVY"] = M["SKIRT"]
    M["FRIT"] = mat_paint("PBR_GlassFrit_RAL9005", (0.0032, 0.0032, 0.004), rough=0.25, coat=0.8)
    M["SCREENGLASS"] = mat_glass("PBR_DraftScreenGlass", tint=(0.55, 0.62, 0.62), rough=0.02, alpha=0.14)
    M["SEAT3"] = mat_paint("PBR_SeatGRP_Blue", (0.006, 0.20, 0.46), rough=0.14, coat=1.0)
    M["WALL3"] = mat_paint("PBR_InteriorGRP_White", (0.80, 0.80, 0.77), rough=0.30, coat=0.5)
    M["CEIL3"] = mat_plain("PBR_CeilingAluWhite", (0.78, 0.79, 0.79), rough=0.35, metal=0.15)
    M["PLEAT"] = mat_plain("PBR_BellowsGrey", (0.085, 0.09, 0.095), rough=0.8)
    M["BELLOWS"] = mat_plain("PBR_OuterBellowsRubber", (0.035, 0.036, 0.038), rough=0.7)
    M["FLOOR3"] = mat_plain("PBR_FloorGreyBlue", (0.10, 0.155, 0.17), rough=0.55)
    M["GRILLE"] = mat_plain("PBR_GrilleDark", (0.02, 0.02, 0.022), rough=0.6)
    M["BLUESIGN"] = mat_plain("PBR_SignBlue", (0.01, 0.10, 0.45), rough=0.4)
    M["ADPANEL"] = mat_plain("PBR_AdPanel", (0.55, 0.60, 0.62), rough=0.4)
    M["BOGIE3"] = mat_paint("PBR_BogieFrameGrey", (0.11, 0.115, 0.12), rough=0.45, coat=0.15)
    M["BOGIELT"] = mat_paint("PBR_BogieLightGrey", (0.32, 0.33, 0.34), rough=0.40, coat=0.2)
    M["DAMP3"] = mat_paint("PBR_DamperGrey", (0.22, 0.23, 0.24), rough=0.35, coat=0.3)
    M["LABELRED"] = mat_paint("PBR_LabelRed", (0.578, 0.0052, 0.0273), rough=0.35)
    M["LABELYEL"] = mat_paint("PBR_LabelYellow", (0.85, 0.65, 0.02), rough=0.35)
    M["DISC"] = mat_plain("PBR_BrakeDisc", (0.30, 0.29, 0.28), rough=0.35, metal=1.0)
    for k, rgb in (("INTERIOR", (0.80, 0.80, 0.77)), ("FLOOR", (0.10, 0.155, 0.17))):
        bs = M[k].node_tree.nodes.get("Principled BSDF"); bs.inputs["Base Color"].default_value = (*rgb, 1); M[k].diffuse_color = (*rgb, 1)

def killmany(prefixes):
    for ob in [o for o in bpy.data.objects if o.name.startswith(tuple(prefixes))]:
        bpy.data.objects.remove(ob, do_unlink=True)

def place(ob, p, d, up=(0, 0, 1)):
    """orient object built along local +Z so that local Z -> direction d, at point p"""
    q = Vector(d).normalized().to_track_quat("Z", "Y")
    ob.matrix_world = Matrix.Translation(Vector(p)) @ q.to_matrix().to_4x4()
    return ob

# =====================================================================================  exterior
def exterior3():
    c = coll("CabCar_Trims")
    for side in (1, -1):
        S = "L" if side > 0 else "R"
        for i, cx in enumerate(G.DOORS):
            x0, x1 = cx - G.DOOR_HW, cx + G.DOOR_HW
            # leaf meeting seals (flush) + door-glass frits (move with the leaves)
            for leaf, (lx0, lx1) in (("a", (x0 + 0.006, cx - 0.008)), ("b", (cx + 0.008, x1 - 0.006))):
                lo = bpy.data.objects.get(f"CC_Door_{S}{i + 1}{leaf}")
                ex = cx - 0.008 if leaf == "a" else cx + 0.008
                xa, xb = (ex - 0.012, ex) if leaf == "a" else (ex, ex + 0.012)
                conform(f"CC_DoorSeal_{S}{i + 1}{leaf}", G.strip(xa, xb, G.DOOR_Z0 + 0.02, G.DOOR_Z1 - 0.02, side, 0.0015, 6), M["SEAL"], c, side, 0.003, lo)
                hx0, hx1 = lx0 + 0.10, lx1 - 0.10
                conform(f"CC_DoorFrit_{S}{i + 1}{leaf}", G.frame_ring(hx0 - 0.012, hx1 + 0.012, 1.80 - 0.012, 2.90 + 0.012, 0.016, 0.06, side, -0.0035), M["FRIT"], c, side, 0.0, lo)
            # door head drip moulding, door-status lamp, threshold step plate
            conform(f"CC_DoorDrip_{S}{i + 1}", G.strip(x0 - 0.10, x1 + 0.10, G.DOOR_Z1 + 0.05, G.DOOR_Z1 + 0.072, side, 0.010, 1), M["SILVER"], c, side, 0.008)
            lamp = lathe(f"CC_DoorLamp_{S}{i + 1}", [(0.003, 0), (0.022, 0), (0.022, 0.008), (0.014, 0.016), (0.003, 0.018)], "y", (0, 0, 0), 20, M["AMBER"], c)
            lamp.matrix_world = Matrix.Translation(Vector(G.side_point(cx, G.DOOR_Z1 + 0.14, side, 0.0))) @ Matrix.Rotation(0 if side > 0 else pi, 4, "Z")
            st = [mk("sl", *G.strip(x0, x1, 0.996, 1.026, side, 0.014, 1), [M["TRIM"]], c), mk("sl2", *G.strip(x0, x1, 0.990, 0.996, side, 0.010, 1), [M["SEAL"]], c)]
            for o in st: orient_side(o, side); solidify(o, 0.012); apply_mods(o)
            join(st, f"CC_DoorSill_{S}{i + 1}")
        # bonded flush windows: black frit border + 4 mm edge seal
        for k, (a, b) in enumerate(G.windows()):
            conform(f"CC_WinFrit_{S}{k + 1}", G.frame_ring(a + 0.015, b - 0.015, G.WIN_Z0 + 0.015, G.WIN_Z1 - 0.015, 0.040, G.WIN_R - 0.01, side, 0.0026), M["FRIT"], c, side)
            conform(f"CC_WinSeal_{S}{k + 1}", G.frame_ring(a - 0.025, b + 0.025, G.WIN_Z0 - 0.025, G.WIN_Z1 + 0.025, 0.004, G.WIN_R + 0.02, side, 0.0005), M["SEAL"], c, side, 0.003)
            conform(f"CC_WinReveal_{S}{k + 1}", G.frame_ring(a, b, G.WIN_Z0, G.WIN_Z1, 0.055, G.WIN_R, side, -0.050), M["WALL3"], c, side, 0.020)
        # cab door: thin seal, grab handles, step, camera pod
        x0, x1, z0, z1 = G.CAB_DOOR
        cdo = bpy.data.objects.get(f"CC_CabSideDoor_{S}")
        conform(f"CC_CabWinFrit_{S}", G.frame_ring(x0 + 0.09 + 0.01, x1 - 0.09 - 0.01, 2.05 + 0.01, 2.90 - 0.01, 0.022, 0.05, side, -0.0035), M["FRIT"], c, side, 0.0, cdo)
        for xh in (x0 - 0.06, x1 + 0.06):
            p0 = G.side_point(xh, 1.35, side, 0.0); p1 = G.side_point(xh, 2.40, side, 0.0)
            tube(f"CC_CabGrab_{S}{'a' if xh < x0 else 'b'}", [p0, (p0[0], p0[1] + side * 0.05, p0[2] + 0.03), (p1[0], p1[1] + side * 0.05, p1[2] - 0.03), p1], 0.013, M["TRIM"], c)
        stp = [bbox_bevel("st", M["TRIM"], 0.5 * (x0 + x1), side * 1.56, 0.56, 0.52, 0.20, 0.03, c, bevel=0.006)]
        for xb in (x0 + 0.06, x1 - 0.06): stp.append(bbox_bevel("sb", M["UNDER"], xb, side * 1.50, 0.72, 0.03, 0.10, 0.34, c, bevel=0.005))
        join(stp, f"CC_CabStep_{S}")
        bbox_bevel(f"CC_CabCameraPod_{S}", M["FRIT"], x1 + 0.12, side * 1.47, 3.26, 0.20, 0.10, 0.11, c, bevel=0.02)
        # panel joints (hairlines) next to the door posts and at colour breaks
        seams = []
        for cx in G.DOORS:
            for xs in (cx - G.DOOR_HW - 0.16, cx + G.DOOR_HW + 0.16):
                seams.append(mk("sm", *G.strip(xs - 0.0025, xs + 0.0025, G.SKIRT_Z1, G.BAND_Z0, side, 0.0012, 4), [M["SEAL"]], c))
        for zz in (G.SKIRT_Z1, G.BAND_Z1 + 0.002):
            seams.append(mk("ls", *G.strip(G.X_REAR + 0.05, G.CAB_WALL_X, zz - 0.0018, zz + 0.0018, side, 0.0012, 1), [M["SEAL"]], c))
        for o in seams: orient_side(o, side)
        join(seams, f"CC_PanelSeams_{S}")
        # side destination displays: flush-bonded glass over a dot-matrix LED field
        for k, cx in enumerate((-1.97, 2.06)):
            w, h, zc = 1.00, 0.13, 3.13
            conform(f"CC_SideDestFrame_{S}{k + 1}", G.frame_ring(cx - w / 2, cx + w / 2, zc - h / 2, zc + h / 2, 0.010, 0.02, side, 0.0008), M["FRIT"], c, side, 0.002)
            conform(f"CC_SideDestLED_{S}{k + 1}", G.pane_grid(cx - w / 2 + 0.03, cx + w / 2 - 0.03, zc - h / 2 + 0.025, zc + h / 2 - 0.025, 0.005, side, 0.0012, rows=3), M["LEDMATRIX"], c, side)
            conform(f"CC_SideDestBack_{S}{k + 1}", G.pane_grid(cx - w / 2, cx + w / 2, zc - h / 2, zc + h / 2, 0.015, side, 0.0006, rows=3), M["SCREEN"], c, side)
            conform(f"CC_SideDestGlass_{S}{k + 1}", G.pane_grid(cx - w / 2, cx + w / 2, zc - h / 2, zc + h / 2, 0.015, side, 0.0022, rows=3), M["GLASS"], c, side)
    # front destination display (dot-matrix) behind the windscreen top
    killmany(["CC_DestinationHousing", "CC_DestinationLED"])
    cf = coll("CabCar_Front")
    lc, ln = (None, None) if globals().get("V4") else hitw(0.0, 3.30)
    if lc is not None:
        for nm, w, h, back, mat in (("CC_FrontDestHousing", 1.36, 0.24, 0.075, M["FRIT"]), ("CC_FrontDestLED", 1.24, 0.15, 0.060, M["LEDMATRIX"])):
            ring = []
            for (u, v) in rr(w, h, 0.02, 2):
                l, n = hitw(u, 3.30 + v)
                ring.append(tuple(l - n * back))
            loft(nm, [ring, [tuple(Vector(p) - ln * 0.02) for p in ring]], mat, cf, caps=True)

# =====================================================================================  interior
def seat_section():
    # moulded GRP shell section (d from wall, z) for floor at 1.05 (Fig. 1-2-4 side view)
    return [(0.055, 2.055), (0.072, 1.97), (0.090, 1.85), (0.108, 1.72), (0.125, 1.63), (0.145, 1.575), (0.168, 1.548), (0.20, 1.533),
            (0.26, 1.522), (0.34, 1.515), (0.42, 1.510), (0.470, 1.507), (0.495, 1.500), (0.503, 1.485), (0.497, 1.458)]
def bench(name, x0, x1, n, s, c, fold=False):
    sec = seat_section(); m = len(sec); per = 11; dz = FZ - 1.05
    xs = [x0 + (x1 - x0) * k / (n * per) for k in range(n * per + 1)]
    verts, faces = [], []
    for k, x in enumerate(xs):
        u = (k % per) / per if k < n * per else 1.0
        bump = math.sin(pi * u) ** 0.7
        endroll = min(1.0, min(x - x0, x1 - x) / 0.035) ** 0.5
        for j, (d, z) in enumerate(sec):
            dd, zz = d, z
            if j == 0: zz += 0.050 * bump - 0.012                       # scalloped back top per seat
            if 1 <= j <= 5: dd += 0.030 * bump * (1 - j / 7)           # sculpted back recess per seat
            if 7 <= j <= 11: zz -= 0.028 * bump * math.sin(pi * (j - 6) / 6)  # deep pan dimple
            if j == 12: zz -= 0.006 * bump
            dd = 0.02 + (dd - 0.02) * (0.92 + 0.08 * endroll)
            verts.append((x, s * (WALL_Y - dd), dz + zz))
    for k in range(len(xs) - 1):
        for j in range(m - 1):
            f = [k * m + j, (k + 1) * m + j, (k + 1) * m + j + 1, k * m + j + 1]
            faces.append(f if s > 0 else f[::-1])
    ob = mk(name, verts, faces, [M["SEAT3"]], c)
    sd = ob.modifiers.new("Subdivision", "SUBSURF"); sd.levels = 1; sd.render_levels = 1
    solidify(ob, 0.010); apply_mods(ob); smooth_by_angle(ob, 55)
    return ob
def bench_mount(name, x0, x1, n, s, c):
    dz = FZ - 1.05; parts = []
    for zz in (1.30, 1.72):     # wall-mounted frame channels behind the shell
        parts.append(bbox_bevel("ch", M["POLE"], 0.5 * (x0 + x1), s * (WALL_Y - 0.035), dz + zz, x1 - x0 - 0.06, 0.04, 0.05, c, bevel=0.006))
    for k in range(n + 1):      # cantilever brackets at the seat joints (no floor legs)
        x = x0 + (x1 - x0) * k / n; x = min(max(x, x0 + 0.04), x1 - 0.04)
        v = [(x - 0.006, s * (WALL_Y - 0.03), dz + 1.24), (x - 0.006, s * (WALL_Y - 0.03), dz + 1.49), (x - 0.006, s * (WALL_Y - 0.43), dz + 1.49), (x - 0.006, s * (WALL_Y - 0.43), dz + 1.46)]
        b = mk("br", v, [(0, 1, 2, 3)], [M["POLE"]], c, smooth=False); solidify(b, 0.012); apply_mods(b); parts.append(b)
    join(parts, name)
def interior3():
    killmany(["CC_Seat_", "CC_SeatFrame_", "CC_BenchPole_", "CC_FlipSeat_", "CC_WheelchairRail", "CC_Handrail_", "CC_Handholds_",
              "CC_DraftScreen_", "CC_ScreenFrame_", "CC_TrifurcatePole_", "CC_PIDHousing_", "CC_PIDScreen_", "CC_CeilingPanel", "CC_LEDStrip_",
              "CC_AirDiffuser", "CC_DoorStrip_", "CC_Gangway", "CC_WheelchairPlate"])
    c = coll("CabCar_Interior")
    D = sorted(G.DOORS); HW = G.DOOR_HW
    recolor("CC_Floor", M["FLOOR3"], exact=True)
    # ---- moulded 5-seat benches between the doors, 3-seat + flip-down at the rear end
    bays = [(a + HW + 0.09, b - HW - 0.09) for a, b in zip(D[:-1], D[1:])]
    for bi, (x0, x1) in enumerate(bays):
        for s in (1, -1):
            S = "L" if s > 0 else "R"
            bench(f"CC_Bench5_{S}{bi + 1}", x0, x1, 5, s, c); bench_mount(f"CC_BenchMount_{S}{bi + 1}", x0, x1, 5, s, c)
            grl = [bbox_bevel("hg", M["GRILLE"], 0.5 * (x0 + x1), s * (WALL_Y - 0.004), FZ + 0.17, x1 - x0 - 0.10, 0.008, 0.16, c, bevel=0.002)]
            for k in range(int((x1 - x0 - 0.12) / 0.03)):
                grl.append(bbox_bevel("gs", M["WALL3"], x0 + 0.08 + k * 0.03, s * (WALL_Y - 0.009), FZ + 0.17, 0.012, 0.004, 0.15, c, bevel=0.001))
            join(grl, f"CC_HeaterGrille_{S}{bi + 1}")
    xe0 = G.X_REAR + 0.47; xe1 = D[0] - HW - 0.09
    bench("CC_Bench3_R0", xe1 - 1.33, xe1, 3, -1, c); bench_mount("CC_BenchMount_R0", xe1 - 1.33, xe1, 3, -1, c)
    for k in range(3):   # flip-down seats beside the wheelchair space (separate, they fold)
        xa = xe1 - 1.33 + k * 0.443
        bench(f"CC_FlipSeat_L0_{k + 1}", xa + 0.004, xa + 0.439, 1, 1, c)
    bench_mount("CC_FlipSeatMount_L0", xe1 - 1.33, xe1, 3, 1, c)
    wc = []
    for (cx_, cy_, sx_, sy_) in ((xe0 + 0.40, 0.72, 0.74, 0.02), (xe0 + 0.40, 1.38, 0.74, 0.02), (xe0 + 0.04, 1.05, 0.02, 0.68), (xe0 + 0.76, 1.05, 0.02, 0.68)):
        wc.append(bbox_bevel("wc", M["LABELYEL"], cx_, cy_, FZ + 0.001, sx_, sy_, 0.002, c, bevel=0.0005))
    wc.append(lathe("wcs", [(0.10, 0.0), (0.12, 0.0), (0.12, 0.002), (0.10, 0.002)], "z", (xe0 + 0.40, 1.05, FZ), 24, M["LABELYEL"], c))
    join(wc, "CC_WheelchairMarking")
    tube("CC_WheelchairRail", [(xe0 + 0.05, 1.40, FZ + 0.85), (xe1 - 1.40, 1.40, FZ + 0.85)], 0.017, M["POLE"], c)
    # ---- handrail system (Fig. 1-2-5): horizontal poles 220 mm under the ceiling, top fixing brackets 825/1175 mm
    RZ = G.CEIL_Z - 0.22 - 0.06; RY = WALL_Y - 0.52
    def pole_run(nm, xa, xb, s):
        y = s * RY
        pts = [(xa, y, RZ + 0.20)] + [(xa + 0.10 * (1 - math.cos(a)), y, RZ + 0.20 * (1 - math.sin(a))) for a in [k * pi / 16 for k in range(1, 9)]]
        pts += [(xb - 0.10 * (1 - math.cos(a)), y, RZ + 0.20 * (1 - math.sin(a))) for a in [k * pi / 16 for k in range(8, 0, -1)]] + [(xb, y, RZ + 0.20)]
        parts = [tube("hp", pts, 0.017, M["POLE"], c, res=3)]
        xb_ = xa + 0.825
        while xb_ < xb - 0.3:
            parts.append(tube("tf", [(xb_, y, RZ), (xb_, y, RZ + 0.20)], 0.017, M["POLE"], c))
            parts.append(lathe("tfb", [(0.003, 0), (0.035, 0), (0.03, 0.03), (0.003, 0.03)], "z", (xb_, y, RZ + 0.17), 16, M["POLE"], c))
            xb_ += 1.175
        n = 8; hh = []
        for k in range(n):
            xh = xa + 0.25 + (xb - xa - 0.50) * (k + 0.5) / n
            hh.append(bbox_bevel("sp", M["STRAP"], xh, y, RZ - 0.10, 0.032, 0.010, 0.17, c, bevel=0.003))
            hh.append(bbox_bevel("cl", M["HANDLE"], xh, y, RZ - 0.01, 0.05, 0.046, 0.045, c, bevel=0.01))
            top, h, w = RZ - 0.18, 0.15, 0.16
            hh.append(tube("tr", [(xh, y, top), (xh + w / 2, y, top - h), (xh - w / 2, y, top - h), (xh, y, top)], 0.013, M["HANDLE"], c, res=2))
        join(parts, nm); join(hh, nm.replace("HorizPole", "Handholds"))
    for bi, (x0, x1) in enumerate(bays):
        for s in (1, -1): pole_run(f"CC_HorizPole_{'L' if s > 0 else 'R'}{bi + 1}", x0 - 0.03, x1 + 0.03, s)
    for s in (1, -1): pole_run(f"CC_HorizPole_{'L' if s > 0 else 'R'}0", xe0 + 0.05, xe1 + 0.03, s)
    # ---- draft screens: frameless glass + bowed stainless pole as free edge
    for i, cx in enumerate(D):
        for s in (1, -1):
            S = "L" if s > 0 else "R"
            for e in (-1, 1):
                xs = cx + e * (HW + 0.065)
                if not (G.X_REAR + 0.5 < xs < G.CAB_WALL_X - 0.05): continue
                y0, y1 = s * (WALL_Y - 0.01), s * (WALL_Y - 0.48)
                ring = [(xs, y0, FZ + 0.56), (xs, y1, FZ + 0.56), (xs, y1, FZ + 1.58), (xs, y0 + (y1 - y0) * 0.35, FZ + 1.70), (xs, y0, FZ + 1.70)]
                g = mk(f"CC_DraftScreen_{S}{i + 1}{'a' if e < 0 else 'b'}", ring, [list(range(5))], [M["SCREENGLASS"]], c, smooth=False)
                pts = [(xs, s * (WALL_Y - 0.50) - s * 0.06 * math.sin(pi * k / 16), FZ + (RZ + 0.20 - FZ) * k / 16) for k in range(17)]
                tube(f"CC_ScreenPole_{S}{i + 1}{'a' if e < 0 else 'b'}", pts, 0.017, M["POLE"], c, res=3)
                cl = [bbox_bevel("cl", M["POLE"], xs, y1, FZ + zz, 0.03, 0.04, 0.05, c, bevel=0.005) for zz in (0.62, 1.50)]
                join(cl, f"CC_ScreenClamps_{S}{i + 1}{'a' if e < 0 else 'b'}")
            # wall grab handle on each door post + intercom / sign panel
            for e in (-1, 1):
                xp = cx + e * (HW + 0.028)
                if not (G.X_REAR + 0.5 < xp < G.CAB_WALL_X - 0.05): continue
                y = s * (WALL_Y - 0.06)
                tube(f"CC_PostHandle_{S}{i + 1}{'a' if e < 0 else 'b'}", [(xp, s * (WALL_Y - 0.01), FZ + 0.92), (xp, y, FZ + 0.95), (xp, y, FZ + 1.58), (xp, s * (WALL_Y - 0.01), FZ + 1.61)], 0.014, M["POLE"], c, res=3)
            xp = cx - (HW + 0.040); y = s * (WALL_Y - 0.012)
            pnl = [bbox_bevel("sg", M["BLUESIGN"], xp, y, FZ + 1.78, 0.045, 0.006, 0.10, c, bevel=0.002),
                   lathe("ib", [(0.003, 0), (0.016, 0), (0.016, 0.010), (0.003, 0.012)], "y", (xp, y - s * 0.004, FZ + 1.68), 16, M["SCREEN"], c),
                   bbox_bevel("lb", M["LABELRED"], xp, y, FZ + 1.62, 0.045, 0.006, 0.025, c, bevel=0.001)]
            join(pnl, f"CC_IntercomPanel_{S}{i + 1}")
            # inner door: yellow edge bands on both leaves (meeting edges)
            for leaf, ex in (("a", cx - 0.008), ("b", cx + 0.008)):
                lo = bpy.data.objects.get(f"CC_Door_{S}{i + 1}{leaf}")
                xa, xb = (ex - 0.105, ex - 0.005) if leaf == "a" else (ex + 0.005, ex + 0.105)
                o = mk(f"CC_DoorYellow_{S}{i + 1}{leaf}", *G.strip(xa, xb, FZ + 0.12, FZ + 1.95, s, -0.0365, 8), [M["SAFETYYEL"]], c)
                orient_side(o, -s); o.parent = lo
            th = [bbox_bevel("tb", M["TRIM"], cx, s * (WALL_Y - 0.09), FZ + 0.003, 2 * HW, 0.18, 0.006, c, bevel=0.002)]
            for k in range(5): th.append(bbox_bevel("tg", M["GRILLE"], cx, s * (WALL_Y - 0.16 + 0.03 * k), FZ + 0.0065, 2 * HW - 0.04, 0.010, 0.0015, c, bevel=0.0004))
            join(th, f"CC_DoorThreshold_{S}{i + 1}")
        # ---- trifurcate pole at the doorway centre (single -> 3 bowed branches -> single)
        z0, z1 = FZ + 0.80, FZ + 1.95
        parts = [tube("c0", [(cx, 0, FZ), (cx, 0, z0)], 0.019, M["POLE"], c), tube("c1", [(cx, 0, z1), (cx, 0, G.CEIL_Z)], 0.019, M["POLE"], c)]
        for a0 in (pi / 2, pi / 2 + 2 * pi / 3, pi / 2 + 4 * pi / 3):
            pts = [(cx + 0.10 * math.sin(pi * k / 14) * math.cos(a0), 0.10 * math.sin(pi * k / 14) * math.sin(a0), z0 + (z1 - z0) * k / 14) for k in range(15)]
            parts.append(tube("cb", pts, 0.016, M["POLE"], c, res=3))
        for zz in (FZ, G.CEIL_Z - 0.03):
            parts.append(lathe("fl", [(0.003, 0), (0.055, 0), (0.045, 0.02), (0.02, 0.03), (0.003, 0.03)] if zz == FZ else [(0.003, 0), (0.02, 0), (0.045, 0.01), (0.055, 0.03), (0.003, 0.03)], "z", (cx, 0, zz), 20, M["POLE"], c))
        join(parts, f"CC_TrifurcatePole_{i + 1}")
    # ---- ceiling: centre panel, light troughs, corner panels with displays / ads, diffusers, speakers, CCTV
    xa, xb = G.X_REAR + 0.47, G.CAB_WALL_X - 0.02
    def strip_x(nm, pts_yz, mat, thick=0.0):
        ring = [(xa, y, z) for (y, z) in pts_yz]
        return loft(nm, [ring, [(xb, p[1], p[2]) for p in ring]], mat, c, caps=True, angle=35)
    cz = G.CEIL_Z; wz = FZ + 1.98
    strip_x("CC_CeilingCentre", [(-0.78, cz - 0.02), (-0.4, cz), (0.4, cz), (0.78, cz - 0.02), (0.78, cz + 0.02), (-0.78, cz + 0.02)], M["CEIL3"])
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        strip_x(f"CC_CornerPanel_{S}", [(s * 1.43, wz - 0.01), (s * 0.95, cz - 0.07), (s * 0.95, cz - 0.04), (s * 1.43, wz + 0.02)], M["WALL3"])
        strip_x(f"CC_LightTrough_{S}", [(s * 0.95, cz - 0.07), (s * 0.78, cz - 0.03), (s * 0.78, cz - 0.01), (s * 0.95, cz - 0.05)], M["CEIL3"])
        strip_x(f"CC_LightDiffuser_{S}", [(s * 0.935, cz - 0.075), (s * 0.80, cz - 0.040), (s * 0.80, cz - 0.034), (s * 0.935, cz - 0.069)], M["LED"])
        sl = []
        x_ = xa + 0.4
        while x_ + 0.9 < xb:
            sl.append(bbox_bevel("ra", M["GRILLE"], x_ + 0.45, s * 0.42, cz - 0.004, 0.90, 0.028, 0.008, c, bevel=0.002))
            sl.append(bbox_bevel("rf", M["TRIM"], x_ + 0.45, s * 0.42, cz - 0.003, 0.93, 0.046, 0.006, c, bevel=0.002))
            x_ += 1.25
        join(sl, f"CC_ReturnAirGrilles_{S}")
        # corner-panel passenger displays above every doorway and route-map / ad frames between doors
        P0, P1 = Vector((0, s * 1.43, wz)), Vector((0, s * 0.95, cz - 0.07))
        tvec = (P1 - P0).normalized(); nvec = Vector((1, 0, 0)).cross(tvec).normalized()
        if nvec.z > 0: nvec = -nvec
        def panel_item(nm, x, w, hfrac, h, off, mat):
            ctr = P0.lerp(P1, hfrac); ctr.x = x
            q = [ctr + Vector((-w / 2, 0, 0)) - tvec * h / 2 + nvec * off, ctr + Vector((w / 2, 0, 0)) - tvec * h / 2 + nvec * off,
                 ctr + Vector((w / 2, 0, 0)) + tvec * h / 2 + nvec * off, ctr + Vector((-w / 2, 0, 0)) + tvec * h / 2 + nvec * off]
            return mk(nm, [tuple(p) for p in q], [(0, 1, 2, 3)], [mat], c, smooth=False)
        for i, cx in enumerate(D):
            h = panel_item(f"CC_PIDHousing_{S}{i + 1}", cx, 0.72, 0.45, 0.17, 0.006, M["FRIT"]); solidify(h, 0.012); apply_mods(h)
            panel_item(f"CC_PIDScreen_{S}{i + 1}", cx, 0.64, 0.45, 0.11, 0.0075, M["LEDMATRIX"])
        for bi, (x0, x1) in enumerate(bays):
            for k in range(2):
                xm = x0 + (x1 - x0) * (0.27 + 0.46 * k)
                f = panel_item(f"CC_AdFrame_{S}{bi + 1}{k}", xm, 0.72, 0.50, 0.30, 0.004, M["INTTRIM"]); solidify(f, 0.006); apply_mods(f)
                panel_item(f"CC_AdPanel_{S}{bi + 1}{k}", xm, 0.66, 0.50, 0.24, 0.0065, M["ADPANEL"])
    for k, x in enumerate((-9.9, -6.0, -2.0, 2.0, 6.0)):
        lathe(f"CC_CCTV_{k + 1}", [(0.003, 0.0), (0.075, 0.0), (0.07, -0.03), (0.045, -0.065), (0.003, -0.075)], "z", (x, 0.0, cz - 0.004), 24, M["SCREEN"], c)
    for k, (x0, x1) in enumerate(bays + [(xe0, xe1)]):
        for x in (x0 + 0.5, x1 - 0.5):
            sp = [lathe("sk", [(0.003, 0.0), (0.085, 0.0), (0.085, -0.006), (0.003, -0.006)], "z", (x, 0.0, cz - 0.001), 24, M["INTTRIM"], c)]
            for r in (0.025, 0.045, 0.065):
                sp.append(lathe("sr", [(r, -0.006), (r + 0.006, -0.006), (r + 0.006, -0.008), (r, -0.008)], "z", (x, 0.0, cz), 24, M["GRILLE"], c))
            join(sp, f"CC_Speaker_{k}_{int(x * 10)}")
    # door operator covers over each doorway (corner panel bulge) + door indicator
    for i, cx in enumerate(D):
        for s in (1, -1):
            bbox_bevel(f"CC_DoorOperatorCover_{'L' if s > 0 else 'R'}{i + 1}", M["WALL3"], cx, s * (WALL_Y - 0.10), wz + 0.03, 2 * HW + 0.10, 0.20, 0.10, c, bevel=0.02)
    # ---- rear end: cabinets narrowing the body to the gangway opening, header, extinguisher
    X0 = G.X_REAR + 0.025; ow = 0.78
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        y_in, y_out = s * ow, s * (WALL_Y - 0.005)
        cab = bbox_bevel(f"CC_EndCabinet_{S}", M["WALL3"], X0 + 0.22, 0.5 * (y_in + y_out), FZ + 0.99, 0.44, abs(y_out - y_in), 1.98, c, bevel=0.015)
        hw_ = [bbox_bevel("hdl", M["TRIM"], X0 + 0.442, 0.5 * (y_in + y_out), FZ + 1.10, 0.01, 0.025, 0.08, c, bevel=0.003)]
        for zz in (FZ + 0.25, FZ + 1.80): hw_.append(lathe("lk", [(0.003, 0), (0.012, 0), (0.012, 0.004), (0.003, 0.004)], "x", (X0 + 0.44, 0.5 * (y_in + y_out), zz), 12, M["TRIM"], c))
        join(hw_, f"CC_EndCabinetHW_{S}")
        bbox_bevel(f"CC_EndCabinetPlinth_{S}", M["TRIM"], X0 + 0.22, 0.5 * (y_in + y_out), FZ + 0.04, 0.445, abs(y_out - y_in) + 0.005, 0.08, c, bevel=0.004)
    bbox_bevel("CC_GangwayHeader", M["WALL3"], X0 + 0.20, 0, FZ + 2.12, 0.40, 2 * ow + 0.04, 0.26, c, bevel=0.03)
    for s in (1, -1):
        bbox_bevel(f"CC_GangwayJamb_{'L' if s > 0 else 'R'}", M["WALL3"], X0 + 0.02, s * (ow + 0.015), FZ + 1.0, 0.05, 0.04, 2.0, c, bevel=0.012)
    kill("CC_FireExtinguisher")

def gangway3():
    """Gangway: inner pleated bellows (clear passage ~1.45 m), bridge plate, outer full-section bellows; 0.35 m per car."""
    c = coll("CabCar_Gangway")
    X0 = G.X_REAR; L = G.GANGWAY_LEN / 2; ow = G.GANGWAY_W / 2; H = G.GANGWAY_H
    clear = 0.70; top = FZ + 2.00
    pleats = []
    for k in range(12):
        x = X0 - 0.02 - k * (L - 0.04) / 11
        yo = clear + 0.05 + (0.045 if k % 2 else 0.0)
        r_c = 0.18
        pts = [(x, -yo, FZ + 0.03)]
        pts += [(x, -yo, top - r_c)] + [(x, -yo + r_c * (1 - math.cos(a)), top - r_c + r_c * math.sin(a)) for a in [j * (pi / 2) / 6 for j in range(1, 7)]]
        pts += [(x, yo - r_c * (1 - math.cos(a)), top - r_c + r_c * math.sin(a)) for a in [j * (pi / 2) / 6 for j in range(6, 0, -1)]] + [(x, yo, top - r_c), (x, yo, FZ + 0.03)]
        pleats.append(tube("pl", pts, 0.042, M["PLEAT"], c, res=4))
        for s in (1, -1):     # flared pleat feet
            pleats.append(lathe("pf", [(0.003, 0.0), (0.056, 0.0), (0.044, 0.12), (0.003, 0.12)], "z", (x, s * yo, FZ), 14, M["PLEAT"], c))
    join(pleats, "CC_GangwayPleats")
    # pleat backing wall (closes the gap between pleats and the structural opening)
    for s in (1, -1):
        v = [(X0, s * (clear + 0.13), FZ), (X0 - L, s * (clear + 0.13), FZ), (X0 - L, s * (clear + 0.13), top + 0.04), (X0, s * (clear + 0.13), top + 0.04)]
        mk(f"CC_GangwayBacking_{'L' if s > 0 else 'R'}", v, [(0, 1, 2, 3) if s > 0 else (3, 2, 1, 0)], [M["PLEAT"]], c, smooth=False)
    v = [(X0, -clear - 0.13, top + 0.04), (X0 - L, -clear - 0.13, top + 0.04), (X0 - L, clear + 0.13, top + 0.04), (X0, clear + 0.13, top + 0.04)]
    mk("CC_GangwayBackingTop", v, [(3, 2, 1, 0)], [M["PLEAT"]], c, smooth=False)
    bp = [bbox_bevel("bp", M["BOGIELT"], X0 - L / 2, 0, FZ - 0.006, L, 2 * clear + 0.10, 0.012, c, bevel=0.003)]
    for k in range(10): bp.append(bbox_bevel("bg", M["GRILLE"], X0 - L / 2, -clear + 0.05 + k * (2 * clear - 0.10) / 9, FZ + 0.001, L - 0.04, 0.010, 0.002, c, bevel=0.0005))
    join(bp, "CC_GangwayBridgePlate")
    # outer bellows: corrugated black rubber over the full end section + end face frame
    def ring(x, w, h, r, zc): return [(x, a, zc + b) for (a, b) in rr(w, h, r, 5)]
    zc = 2.32; outer = []
    for k in range(15):
        g = 0.05 if k % 2 else 0.0
        outer.append(ring(X0 - 0.01 - k * (L - 0.04) / 14, 2.70 + g, 2.60 + g, 0.40, zc))
    loft("CC_GangwayOuterBellows", outer, M["BELLOWS"], c, caps=False, angle=60)
    xf = X0 - L + 0.02; bw = 2 * (clear + 0.13); zi = FZ + (top + 0.04 - FZ) / 2; hi = top + 0.04 - FZ
    loft("CC_GangwayFaceFrame", [ring(xf, bw, hi, 0.18, zi), ring(xf, 2.78, 2.68, 0.42, zc), ring(xf - 0.03, 2.78, 2.68, 0.42, zc), ring(xf - 0.03, bw, hi, 0.18, zi)],
         M["BELLOWS"], c, caps=False, angle=40)
    loft("CC_GangwayFaceTrim", [ring(xf - 0.031, 2.74, 2.64, 0.41, zc), ring(xf - 0.031, 2.62, 2.52, 0.38, zc)], M["BOGIELT"], c, caps=False, angle=40)

# =====================================================================================  bogie
WR = 0.43; WB2 = 1.25; BTB = 1.36
def damper3(name, p0, p1, r, c):
    p0, p1 = Vector(p0), Vector(p1); L = (p1 - p0).length; e = 0.035
    prof = [(0.003, e), (0.36 * r, e), (0.36 * r, 0.30 * L), (0.95 * r, 0.30 * L), (0.95 * r, 0.40 * L), (r, 0.42 * L), (r, L - e - 0.02), (0.6 * r, L - e), (0.003, L - e)]
    parts = [lathe("db", prof, "z", (0, 0, 0), 20, M["DAMP3"], c)]
    for a in (0.0, L):
        parts.append(lathe("de", [(0.003, -0.032), (0.034, -0.032), (0.034, 0.032), (0.003, 0.032)], "x", (0, 0, a), 16, M["DAMP3"], c))
        parts.append(lathe("dr", [(0.003, -0.036), (0.016, -0.036), (0.016, 0.036), (0.003, 0.036)], "x", (0, 0, a), 12, M["SEAL"], c))
    parts.append(lathe("lb", [(r * 1.01, 0.55 * L), (r * 1.02, 0.55 * L), (r * 1.02, 0.66 * L), (r * 1.01, 0.66 * L)], "z", (0, 0, 0), 20, M["LABELYEL"], c))
    ob = join(parts, name); place(ob, p0, p1 - p0); return ob
def coil(name, center, r, wire, h, turns, mat, c):
    pts = []
    for k in range(int(turns * 20) + 1):
        th = 2 * pi * k / 20; pts.append((center[0] + r * math.cos(th), center[1] + r * math.sin(th), center[2] + h * k / (turns * 20)))
    return tube(name, pts, wire, mat, c, res=2)
def bolts(name, center, axis, rad, n, c, size=0.012):
    parts = []
    for k in range(n):
        a = 2 * pi * k / n
        if axis == "y": p = (center[0] + rad * math.cos(a), center[1], center[2] + rad * math.sin(a))
        else: p = (center[0], center[1] + rad * math.cos(a), center[2] + rad * math.sin(a))
        parts.append(lathe("bt", [(0.003, 0), (size, 0), (size, size * 0.9), (0.003, size)], axis, p, 6, M["TRIM"], c))
    return join(parts, name)
def bogie3(tag, bx, lead):
    c = coll("CabCar_Bogie_" + tag)
    T = f"CC_B{tag}_"
    wheel = [(0.095, -0.07), (0.17, -0.07), (0.18, -0.02), (0.36, 0.010), (0.40, 0.000), (0.458, 0.000), (0.461, 0.012),
             (0.452, 0.026), (WR, 0.032), (WR - 0.007, 0.165), (0.41, 0.168), (0.385, 0.150), (0.36, 0.125), (0.19, 0.095), (0.18, 0.125), (0.095, 0.125)]
    for ia, ax in enumerate((-WB2, WB2)):
        xa = bx + ax; parts = []
        for s in (1, -1):
            pr = [(r, s * (BTB / 2 + a)) for (r, a) in wheel]
            if s < 0: pr = pr[::-1]
            parts.append(lathe("w", pr, "y", (xa, 0, WR), 48, [M["WHEEL"], M["RUST"]], c, seg_mat=lambda p, q: 0 if min(p[0], q[0]) >= 0.42 else 1))
        parts.append(lathe("ax", [(0.075, -1.10), (0.09, -1.10), (0.09, 1.10), (0.075, 1.10)], "y", (xa, 0, WR), 24, M["WHEEL"], c))
        # axle-mounted ventilated brake disc (doc p.57) on one side, gearbox on the other
        dprof = [(0.13, -0.055), (0.31, -0.055), (0.31, -0.012), (0.295, -0.012), (0.295, 0.012), (0.31, 0.012), (0.31, 0.055), (0.13, 0.055)]
        parts.append(lathe("d", dprof, "y", (xa, -0.36, WR), 48, M["DISC"], c))
        parts.append(lathe("dh", [(0.09, -0.07), (0.14, -0.07), (0.14, 0.07), (0.09, 0.07)], "y", (xa, -0.36, WR), 24, M["BOGIELT"], c))
        ob = join(parts, f"{T}Wheelset{ia + 1}")
        sgn = -1 if ax > 0 else 1      # toward bogie centre
        gb = [bbox_bevel("gb", M["BOGIE3"], xa + sgn * 0.12, 0.36, WR + 0.02, 0.52, 0.20, 0.46, c, bevel=0.06),
              lathe("gbc", [(0.09, -0.11), (0.20, -0.11), (0.20, 0.11), (0.09, 0.11)], "y", (xa, 0.36, WR), 32, M["BOGIE3"], c)]
        join(gb, f"{T}Gearbox{ia + 1}")
        lathe(f"{T}TractionMotor{ia + 1}", [(0.05, -0.30), (0.22, -0.30), (0.245, -0.27), (0.245, 0.24), (0.22, 0.28), (0.12, 0.30), (0.05, 0.30)], "y", (xa + sgn * 0.62, 0.02, 0.50), 36, M["BOGIE3"], c)
        fins = [bbox_bevel("mf", M["BOGIE3"], xa + sgn * 0.62, -0.20 + k * 0.08, 0.50 + 0.245, 0.30, 0.012, 0.03, c, bevel=0.003) for k in range(6)]
        join(fins, f"{T}MotorFins{ia + 1}")
        lathe(f"{T}Coupling{ia + 1}", [(0.03, -0.06), (0.10, -0.06), (0.10, 0.06), (0.03, 0.06)], "y", (xa + sgn * 0.35, 0.30, 0.48), 20, M["SEAL"], c)
        # brake calliper (single-pin suspension) on the disc + actuator + hose
        cp = [bbox_bevel("cb", M["BOGIELT"], xa + sgn * 0.27, -0.36, WR + 0.02, 0.16, 0.16, 0.24, c, bevel=0.02),
              lathe("cy", [(0.02, -0.10), (0.065, -0.10), (0.07, -0.06), (0.07, 0.06), (0.065, 0.10), (0.02, 0.10)], "x", (xa + sgn * 0.42, -0.36, WR + 0.08), 20, M["BOGIELT"], c),
              lathe("pin", [(0.003, -0.05), (0.02, -0.05), (0.02, 0.05), (0.003, 0.05)], "y", (xa + sgn * 0.42, -0.36, WR + 0.19), 12, M["TRIM"], c)]
        join(cp, f"{T}Calliper{ia + 1}")
        tube(f"{T}BrakeHose{ia + 1}", [(xa + sgn * 0.48, -0.36, WR + 0.08), (xa + sgn * 0.55, -0.45, 0.62), (bx + sgn * 0.0, -0.55, 0.62)], 0.012, M["SEAL"], c)
        bbox_bevel(f"{T}CalliperLabel{ia + 1}", M["LABELRED"], xa + sgn * 0.42, -0.36 - 0.072, WR + 0.08, 0.06, 0.004, 0.025, c, bevel=0.001)
        for s in (1, -1):
            S = "L" if s > 0 else "R"; ya = s * 1.00
            # axle box: housing, bolted front cover, earthing / sensor cap, box arm to frame pivot
            ab = [lathe("ah", [(0.06, -0.12), (0.13, -0.12), (0.145, -0.08), (0.145, 0.08), (0.13, 0.12), (0.06, 0.12)], "y", (xa, ya, WR), 32, M["BOGIELT"], c)]
            cov_y = ya + s * 0.125
            ab.append(lathe("ac", [(0.003, 0.0), (0.115, 0.0), (0.115, 0.018), (0.08, 0.026), (0.003, 0.03)] if s > 0 else [(0.003, -0.03), (0.08, -0.026), (0.115, -0.018), (0.115, 0.0), (0.003, 0.0)], "y", (xa, cov_y, WR), 32, M["BOGIELT"], c))
            ab.append(bolts("bl", (xa, cov_y + s * 0.018, WR), "y", 0.095, 8, c, 0.011))
            arm = loft("arm", [[(xa + sgn * t_, ya + a, WR + 0.02 + b) for (a, b) in rr(0.12, 0.10 - 0.02 * t_, 0.025, 2)] for t_ in (0.10, 0.48)], M["BOGIELT"], c, caps=True, angle=40)
            ab.append(arm)
            ab.append(lathe("ap", [(0.02, -0.08), (0.065, -0.08), (0.065, 0.08), (0.02, 0.08)], "y", (xa + sgn * 0.52, ya, WR + 0.03), 24, M["SEAL"], c))
            ab.append(bbox_bevel("sp", M["BOGIELT"], xa, ya, 0.585, 0.30, 0.24, 0.025, c, bevel=0.006))
            join(ab, f"{T}AxleBox{ia + 1}{S}")
            if s > 0 and ia == 0:
                lathe(f"{T}EarthBrush", [(0.003, 0), (0.06, 0), (0.06, 0.07), (0.04, 0.09), (0.003, 0.09)], "y", (xa, cov_y + 0.03, WR), 24, M["BOGIE3"], c)
                tube(f"{T}EarthCable", [(xa, cov_y + 0.12, WR + 0.03), (xa + 0.15, cov_y + 0.14, WR + 0.25), (xa + 0.45, 1.15, 0.70)], 0.012, M["SEAL"], c)
            # primary suspension: nested coil springs on the axle box + vertical damper
            coil(f"{T}PrimaryOuter{ia + 1}{S}", (xa, ya, 0.598), 0.085, 0.017, 0.12, 4.0, M["SPRING2"], c)
            coil(f"{T}PrimaryInner{ia + 1}{S}", (xa, ya, 0.598), 0.050, 0.011, 0.12, 5.0, M["SPRING2"], c)
            lathe(f"{T}SpringCap{ia + 1}{S}", [(0.03, 0.0), (0.105, 0.0), (0.105, 0.018), (0.03, 0.018)], "z", (xa, ya, 0.716), 28, M["BOGIELT"], c)
            damper3(f"{T}PrimaryDamper{ia + 1}{S}", (xa - sgn * 0.20, s * 1.15, 0.46), (xa - sgn * 0.20, s * 1.15, 0.80), 0.032, c)
    # H-frame: box-section side frames with top/bottom flanges, two tubular cross beams, brackets
    for s in (1, -1):
        S = "L" if s > 0 else "R"; secs = []; fl = []
        xs = (-1.66, -1.55, -1.40, -1.10, -0.80, -0.50, 0.0, 0.50, 0.80, 1.10, 1.40, 1.55, 1.66)
        prof = []
        for x in xs:
            u = min(abs(x) / 1.10, 1.0); zc = 0.56 + (0.775 - 0.56) * (u ** 2.2); hh = 0.26 - 0.13 * (u ** 2.2)
            if abs(x) > 1.5: hh *= 0.75
            prof.append((x, zc, hh))
            secs.append([(bx + x, s * 1.00 + a, zc + b) for (a, b) in rr(0.20, hh, 0.02, 2)])
        loft(f"{T}SideFrame{S}", secs, M["BOGIE3"], c, caps=True, angle=30)
        for sgnz in (1, -1):
            fsecs = [[(bx + x, s * 1.00 + a, zc + sgnz * (hh / 2 + 0.008) + b) for (a, b) in rr(0.26, 0.016, 0.006, 1)] for (x, zc, hh) in prof]
            loft(f"{T}Flange{S}{'T' if sgnz > 0 else 'B'}", fsecs, M["BOGIE3"], c, caps=True, angle=30)
        rib = []
        for x in (-0.80, -0.40, 0.40, 0.80):
            u = min(abs(x) / 1.10, 1.0); zc = 0.56 + (0.775 - 0.56) * (u ** 2.2); hh = 0.26 - 0.13 * (u ** 2.2)
            rib.append(bbox_bevel("rb", M["BOGIE3"], bx + x, s * (1.00 + 0.11), zc, 0.014, 0.025, hh, c, bevel=0.002))
        join(rib, f"{T}Stiffeners{S}")
        # secondary suspension: air spring with top plate, bellows and emergency rubber spring
        ap = [(0.08, 0.0), (0.24, 0.0), (0.275, 0.018), (0.315, 0.05), (0.322, 0.075), (0.31, 0.105), (0.27, 0.13), (0.24, 0.145), (0.08, 0.145)]
        lathe(f"{T}AirSpring{S}", ap, "z", (bx, s * 1.00, 0.70), 40, M["SEAL"], c)
        lathe(f"{T}AirSpringPlate{S}", [(0.003, 0), (0.30, 0), (0.30, 0.018), (0.003, 0.018)], "z", (bx, s * 1.00, 0.845), 36, M["BOGIELT"], c)
        lathe(f"{T}EmergencySpring{S}", [(0.05, 0.0), (0.17, 0.0), (0.17, 0.02), (0.15, 0.03), (0.17, 0.04), (0.17, 0.06), (0.05, 0.06)], "z", (bx, s * 1.00, 0.64), 28, M["SEAL"], c)
        # yaw damper: frame bracket -> body bracket, outside the side frame
        bbox_bevel(f"{T}YawBracket{S}", M["BOGIE3"], bx - 0.30, s * 1.17, 0.70, 0.12, 0.10, 0.14, c, bevel=0.01)
        damper3(f"{T}YawDamper{S}", (bx - 0.30, s * 1.24, 0.72), (bx - 1.20, s * 1.24, 0.82), 0.045, c)
        bbox_bevel(f"{T}YawBodyBracket{S}", M["UNDER"], bx - 1.20, s * 1.24, 0.86, 0.12, 0.12, 0.06, c, bevel=0.008)
        # levelling valve + lever
        bbox_bevel(f"{T}LevelValve{S}", M["BOGIELT"], bx + 0.40, s * 0.82, 0.84, 0.10, 0.08, 0.06, c, bevel=0.01)
        tube(f"{T}LevelRod{S}", [(bx + 0.40, s * 0.82, 0.82), (bx + 0.60, s * 0.86, 0.80), (bx + 0.60, s * 0.92, 0.62)], 0.008, M["TRIM"], c)
    for k, dx in enumerate((-0.30, 0.30)):
        cb = [lathe("cb", [(0.06, -1.02), (0.085, -1.02), (0.085, 1.02), (0.06, 1.02)], "y", (bx + dx, 0, 0.55), 24, M["BOGIE3"], c)]
        for s in (1, -1): cb.append(bbox_bevel("gs", M["BOGIE3"], bx + dx, s * 0.86, 0.55, 0.22, 0.12, 0.20, c, bevel=0.01))
        join(cb, f"{T}CrossBeam{k + 1}")
    # traction centre: pivot block, Z-arranged traction rods, lateral damper + bump stops, anti-roll bar
    bbox_bevel(f"{T}TractionCentre", M["BOGIELT"], bx, 0, 0.74, 0.30, 0.34, 0.22, c, bevel=0.03)
    for s in (1, -1):
        p0, p1 = (bx, s * 0.22, 0.68), (bx + s * 0.55, s * 0.22, 0.60)
        tube(f"{T}TractionRod{'L' if s > 0 else 'R'}", [p0, p1], 0.028, M["BOGIELT"], c)
        for p in (p0, p1): lathe(f"{T}TractionBush{'L' if s > 0 else 'R'}", [(0.02, -0.045), (0.055, -0.045), (0.055, 0.045), (0.02, 0.045)], "y", p, 16, M["SEAL"], c)
        bbox_bevel(f"{T}LatStop{'L' if s > 0 else 'R'}", M["SEAL"], bx, s * 0.22, 0.79, 0.10, 0.06, 0.08, c, bevel=0.015)
    damper3(f"{T}LateralDamper", (bx - 0.10, -0.55, 0.66), (bx - 0.10, 0.10, 0.78), 0.035, c)
    arb = [lathe("ar", [(0.003, -1.16), (0.028, -1.16), (0.028, 1.16), (0.003, 1.16)], "y", (bx + 0.12, 0, 0.47), 16, M["BOGIE3"], c)]
    for s in (1, -1):
        arb.append(tube("aa", [(bx + 0.12, s * 1.16, 0.47), (bx - 0.18, s * 1.16, 0.47)], 0.024, M["BOGIE3"], c))
        arb.append(tube("al", [(bx - 0.18, s * 1.18, 0.47), (bx - 0.18, s * 1.20, 0.86)], 0.014, M["TRIM"], c))
    join(arb, f"{T}AntiRollBar")
    # lifeguards, ATP antenna, cable loops
    for s in (1, -1):
        xl = bx + (WB2 + 0.55) * (1 if lead else -1)
        lg = [bbox_bevel("lg", M["LABELYEL"], xl, s * 0.7525, 0.22, 0.035, 0.16, 0.28, c, bevel=0.008), bbox_bevel("lgb", M["BOGIE3"], xl - 0.06 * (1 if lead else -1), s * 0.85, 0.46, 0.14, 0.06, 0.20, c, bevel=0.01)]
        join(lg, f"{T}Lifeguard{'L' if s > 0 else 'R'}")
        pts = [(bx - 0.80, s * 0.86, 0.70)] + [(bx - 0.80 - 0.20 * math.sin(a), s * 0.86, 0.70 + 0.16 * (1 - math.cos(a))) for a in [k * pi / 8 for k in range(1, 9)]]
        tube(f"{T}CableLoop{'L' if s > 0 else 'R'}", pts, 0.018, M["SEAL"], c, res=3)
    if lead:
        bbox_bevel(f"{T}ATPAntenna", M["LABELYEL"], bx + WB2 + 0.75, 0, 0.17, 0.30, 0.40, 0.06, c, bevel=0.01)

def lights3():
    """Interior LED light lines as real area lights (controlled saloon lighting)."""
    for s in (1, -1):
        ld = bpy.data.lights.new(f"SaloonLight_{'L' if s > 0 else 'R'}", "AREA"); ld.shape = "RECTANGLE"
        ld.size = 19.4; ld.size_y = 0.10; ld.energy = 420; ld.color = (1.0, 0.97, 0.92)
        lo = bpy.data.objects.new(ld.name, ld); bpy.context.scene.collection.objects.link(lo)
        lo.location = (0.5 * (G.X_REAR + 0.47 + G.CAB_WALL_X), s * 0.87, G.CEIL_Z - 0.09)
        lo.rotation_euler = (s * math.radians(25), 0, 0)
    for s in (1, -1):   # up-light from the light troughs onto the ceiling panels
        ul = bpy.data.lights.new(f"CeilingBounce_{'L' if s > 0 else 'R'}", "AREA"); ul.shape = "RECTANGLE"; ul.size = 19.0; ul.size_y = 0.08; ul.energy = 160
        uo = bpy.data.objects.new(ul.name, ul); bpy.context.scene.collection.objects.link(uo)
        uo.location = (0.5 * (G.X_REAR + 0.47 + G.CAB_WALL_X), s * 0.80, G.CEIL_Z - 0.10); uo.rotation_euler = (math.radians(180) - s * math.radians(35), 0, 0)

def run_details3():
    global SHELL
    SHELL = bpy.data.objects["CC_BodyShell"]
    mats3(); exterior3(); interior3(); gangway3(); lights3()
    killmany(["CC_Wheelset_", "CC_Calliper_", "CC_AxleBox_", "CC_PrimarySpring_", "CC_SideFrame_", "CC_AirSpring_", "CC_VertDamper", "CC_YawDamper_",
              "CC_Transom_", "CC_LatDamper_", "CC_ATPAntenna", "CC_SpringSeat_", "CC_SpeedSensor_", "CC_SensorCable_", "CC_BrakeCylinder_",
              "CC_TractionRod_", "CC_Bush_", "CC_BumpStop_", "CC_AntiRollBar_", "CC_AntiRollLink_", "CC_Lifeguard_", "CC_BogieCable_"])
    bogie3("F", G.BOGIE_X[0], True); bogie3("R", G.BOGIE_X[1], False)

run_details3()
print("details3 done:", stats())
