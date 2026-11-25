"""Revision 2 (presentation-grade): trims, seals, refined front, readable bogies, denser underframe,
detailed roof units, richer interior, controlled lighting. Runs after build_hq.py + details.py (same namespace)."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
pi = math.pi

def mats2():
    M["TRIM"] = mat_plain("PBR_PolishedTrim", (0.92, 0.92, 0.93), rough=0.10, metal=1.0)
    M["SEAL"] = mat_plain("PBR_RubberSeal", (0.008, 0.008, 0.009), rough=0.65)
    M["BOGIE2"] = mat_paint("PBR_BogieFrameSatin", (0.075, 0.08, 0.085), rough=0.42, coat=0.15)
    M["AXLEBOX"] = mat_paint("PBR_AxleBoxGrey", (0.30, 0.31, 0.32), rough=0.40, coat=0.2)
    M["BRAKE"] = mat_paint("PBR_BrakeRedOxide", (0.30, 0.045, 0.03), rough=0.45, coat=0.2)
    M["DAMPER"] = mat_paint("PBR_DamperOchre", (0.62, 0.42, 0.05), rough=0.35, coat=0.4)
    M["EQMID"] = mat_paint("PBR_EquipMidGrey", (0.17, 0.18, 0.19), rough=0.55, coat=0.1)
    M["TANK"] = mat_paint("PBR_TankGrey", (0.40, 0.41, 0.42), rough=0.45, coat=0.2)
    M["ALU"] = mat_plain("PBR_AluminiumFins", (0.55, 0.56, 0.57), rough=0.35, metal=1.0)
    M["FABRIC"] = mat_plain("PBR_SeatFabric", (0.035, 0.055, 0.085), rough=0.92)
    M["FROST"] = mat_plain("PBR_FrostedBand", (0.85, 0.87, 0.88), rough=0.55)
    M["RED"] = mat_paint("PBR_EmergencyRed", (0.55, 0.02, 0.02), rough=0.35)
    M["GREEN"] = mat_plain("PBR_ButtonGreen", (0.05, 0.6, 0.15), rough=0.3, emit=1.0)
    M["SCREEN"] = mat_paint("PBR_ScreenGloss", (0.005, 0.005, 0.006), rough=0.08, coat=1.0)
    M["FLOOR2"] = mat_plain("PBR_FloorSeatZone", (0.12, 0.13, 0.14), rough=0.85)
    M["INTTRIM"] = mat_plain("PBR_InteriorTrimGrey", (0.36, 0.37, 0.38), rough=0.5)
    # LED dot-matrix (side destination displays): emission masked by a fine checker
    m = bpy.data.materials.new("PBR_LEDMatrix"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1); b.inputs["Roughness"].default_value = 0.2
    ck = nt.nodes.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 130.0
    ck.inputs["Color1"].default_value = (1.0, 0.42, 0.02, 1); ck.inputs["Color2"].default_value = (0, 0, 0, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], ck.inputs["Vector"])
    nt.links.new(ck.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 2.2
    m.diffuse_color = (1.0, 0.45, 0.02, 1); M["LEDMATRIX"] = m
    M["LED"].node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"].default_value = 2.2
    def setc(m, rgb, rough=None):
        bs = m.node_tree.nodes.get("Principled BSDF"); bs.inputs["Base Color"].default_value = (*rgb, 1); m.diffuse_color = (*rgb, 1)
        if rough is not None: bs.inputs["Roughness"].default_value = rough
    setc(M["SEAT"], (0.03, 0.34, 0.50), 0.18)
    setc(M["INTERIOR"], (0.80, 0.81, 0.80), 0.35)
    setc(M["FLOOR"], (0.17, 0.22, 0.25), 0.7)
    M["SEATINSET"] = mat_paint("PBR_SeatInsetBlue", (0.01, 0.16, 0.30), rough=0.15, coat=0.8)
    M["HANDLE"] = mat_paint("PBR_HandleTeal", (0.03, 0.33, 0.46), rough=0.25, coat=0.5)
    M["STRAP"] = mat_plain("PBR_StrapGrey", (0.18, 0.19, 0.20), rough=0.7)
    M["CYAN"] = mat_plain("PBR_AccentCyanLED", (0.15, 0.85, 0.95), rough=0.3, emit=2.0)
    M["TVSCREEN"] = mat_plain("PBR_InfoScreenLit", (0.55, 0.65, 0.85), rough=0.2, emit=1.4)
    M["SPRING2"] = mat_paint("PBR_SpringSlateBlue", (0.06, 0.13, 0.24), rough=0.35, coat=0.3)
    M["SAFETYYEL"] = mat_paint("PBR_SafetyYellowGloss", (0.85, 0.75, 0.02), rough=0.3, coat=0.4)

def recolor(prefix, mat, exact=False):
    for ob in [o for o in bpy.data.objects if o.type == "MESH" and (o.name == prefix if exact else o.name.startswith(prefix))]:
        ob.data.materials.clear(); ob.data.materials.append(mat)
def kill(prefix):
    for ob in [o for o in bpy.data.objects if o.name.startswith(prefix)]: bpy.data.objects.remove(ob, do_unlink=True)
def conform(name, vf, mat, c, side, solid=0.0, parent=None, smooth=True):
    v, f = vf; ob = mk(name, v, f, [mat], c, smooth=smooth); orient_side(ob, side)
    if solid: solidify(ob, solid); apply_mods(ob)
    if parent: ob.parent = parent
    return ob

# ------------------------------------------------------------------ A/B: body trims, door/window frames, seals, sills
def body_trims():
    c = coll("CabCar_Trims")
    for side in (1, -1):
        S = "L" if side > 0 else "R"
        seams = []
        for i, cx in enumerate(G.DOORS):
            x0, x1 = cx - G.DOOR_HW, cx + G.DOOR_HW
            # polished door surround frame + rubber gasket inside it
            conform(f"CC_DoorFrame_{S}{i + 1}", G.frame_ring(x0 - 0.010, x1 + 0.010, G.DOOR_Z0 - 0.006, G.DOOR_Z1 + 0.010, 0.040, 0.03, side, 0.006), M["TRIM"], c, side, 0.006)
            conform(f"CC_DoorGasket_{S}{i + 1}", G.frame_ring(x0 + 0.002, x1 - 0.002, G.DOOR_Z0 + 0.004, G.DOOR_Z1 - 0.004, 0.012, 0.02, side, 0.0075), M["SEAL"], c, side, 0.004)
            # door-head drip moulding + door-open indicator lamp
            conform(f"CC_DoorDrip_{S}{i + 1}", G.strip(x0 - 0.12, x1 + 0.12, G.DOOR_Z1 + 0.055, G.DOOR_Z1 + 0.085, side, 0.018, 1), M["TRIM"], c, side, 0.012)
            lamp = lathe(f"CC_DoorLamp_{S}{i + 1}", [(0.003, 0), (0.028, 0), (0.028, 0.012), (0.018, 0.022), (0.003, 0.024)], "y", (0, 0, 0), 20, M["AMBER"], c)
            lamp.matrix_world = Matrix.Translation(Vector(G.side_point(cx, G.DOOR_Z1 + 0.15, side, 0.004))) @ Matrix.Rotation(0 if side > 0 else pi, 4, "Z")
            # exterior threshold / sill plate
            sill = []
            for k in range(6):
                zz = G.DOOR_Z0 - 0.012 - 0.004 * k
                sill.append(mk("sl", *G.strip(x0, x1, zz - 0.003, zz, side, 0.040 - 0.006 * k, 1), [M["TRIM"]], c))
            join(sill, f"CC_DoorSill_{S}{i + 1}")
            # leaf meeting seals + leaf glass frit borders (parented to the leaves so they move with them)
            for leaf, (lx0, lx1) in (("a", (x0 + 0.006, cx - 0.008)), ("b", (cx + 0.008, x1 - 0.006))):
                lo = bpy.data.objects.get(f"CC_Door_{S}{i + 1}{leaf}")
                ex = cx - 0.008 if leaf == "a" else cx + 0.008
                conform(f"CC_DoorSeal_{S}{i + 1}{leaf}", G.strip(ex - 0.014 if leaf == "a" else ex, ex if leaf == "a" else ex + 0.014, G.DOOR_Z0 + 0.02, G.DOOR_Z1 - 0.02, side, 0.008, 6), M["SEAL"], c, side, 0.006, lo)
                hx0, hx1 = lx0 + 0.10, lx1 - 0.10
                conform(f"CC_DoorFrit_{S}{i + 1}{leaf}", G.frame_ring(hx0 - 0.016, hx1 + 0.016, 1.80 - 0.016, 2.90 + 0.016, 0.022, 0.06, side, 0.0045), M["SEAL"], c, side, 0.002, lo)
            for xs in (x0 - 0.16, x1 + 0.16):   # vertical panel joints next to the door posts
                seams.append(mk("sm", *G.strip(xs - 0.003, xs + 0.003, G.SKIRT_Z1, G.BAND_Z0, side, 0.0015, 4), [M["SEAL"]], c))
        join(seams, f"CC_PanelSeams_{S}")
        # window rubber gaskets + polished outer trims
        for k, (a, b) in enumerate(G.windows()):
            conform(f"CC_WinGasket_{S}{k + 1}", G.frame_ring(a - 0.012, b + 0.012, G.WIN_Z0 - 0.012, G.WIN_Z1 + 0.012, 0.018, G.WIN_R - 0.01, side, 0.0075), M["SEAL"], c, side, 0.004)
            conform(f"CC_WinTrim_{S}{k + 1}", G.frame_ring(a - 0.030, b + 0.030, G.WIN_Z0 - 0.030, G.WIN_Z1 + 0.030, 0.012, G.WIN_R + 0.01, side, 0.006), M["TRIM"], c, side, 0.004)
            # inner window reveal frame (interior volume around the opening)
            conform(f"CC_WinReveal_{S}{k + 1}", G.frame_ring(a - 0.01, b + 0.01, G.WIN_Z0 - 0.01, G.WIN_Z1 + 0.01, 0.07, G.WIN_R, side, -0.075), M["INTTRIM"], c, side, 0.025)
        # cab door frame + grab handles + footstep + camera pod
        x0, x1, z0, z1 = G.CAB_DOOR
        conform(f"CC_CabDoorFrame_{S}", G.frame_ring(x0 - 0.008, x1 + 0.008, z0 - 0.006, z1 + 0.008, 0.030, 0.03, side, 0.006), M["SEAL"], c, side, 0.006)
        for xh in (x0 - 0.07, x1 + 0.07):
            p0 = G.side_point(xh, 1.35, side, 0.0); p1 = G.side_point(xh, 2.45, side, 0.0)
            tube(f"CC_CabGrab_{S}{'a' if xh < x0 else 'b'}", [p0, (p0[0], p0[1] + side * 0.055, p0[2] + 0.03), (p1[0], p1[1] + side * 0.055, p1[2] - 0.03), p1], 0.014, M["TRIM"], c)
        stp = [bbox_bevel("st", M["TRIM"], 0.5 * (x0 + x1), side * 1.56, 0.56, 0.56, 0.20, 0.03, c, bevel=0.006)]
        for xb in (x0 + 0.05, x1 - 0.05): stp.append(bbox_bevel("sb", M["SKIRT"], xb, side * 1.50, 0.72, 0.03, 0.10, 0.34, c, bevel=0.005))
        join(stp, f"CC_CabStep_{S}")
        bbox_bevel(f"CC_CabCameraPod_{S}", M["BLACK"], x1 + 0.10, side * 1.48, 3.28, 0.22, 0.12, 0.12, c, bevel=0.02)
        # horizontal skirt-top seam + band seams
        for zz in (G.SKIRT_Z1, G.BAND_Z1):
            conform(f"CC_LineSeam_{S}{int(zz * 100)}", G.strip(G.X_REAR + 0.05, G.CAB_WALL_X, zz - 0.002, zz + 0.002, side, 0.0012, 1), M["SEAL"], c, side)

def side_destinations():
    kill("CC_SideDest")
    c = coll("CabCar_Trims")
    for side in (1, -1):
        S = "L" if side > 0 else "R"
        for k, cx in enumerate((-1.97, 2.06)):
            w, h, zc = 1.00, 0.13, 3.13
            conform(f"CC_SideDestBezel_{S}{k + 1}", G.frame_ring(cx - w / 2, cx + w / 2, zc - h / 2, zc + h / 2, 0.018, 0.02, side, 0.006), M["TRIM"], c, side, 0.006)
            conform(f"CC_SideDestLED_{S}{k + 1}", G.pane_grid(cx - w / 2 + 0.03, cx + w / 2 - 0.03, zc - h / 2 + 0.025, zc + h / 2 - 0.025, 0.005, side, 0.003, rows=3), M["LEDMATRIX"], c, side)
            conform(f"CC_SideDestGlass_{S}{k + 1}", G.pane_grid(cx - w / 2, cx + w / 2, zc - h / 2, zc + h / 2, 0.015, side, 0.007, rows=3), M["GLASS"], c, side, 0.004)
            conform(f"CC_SideDestBack_{S}{k + 1}", G.pane_grid(cx - w / 2, cx + w / 2, zc - h / 2, zc + h / 2, 0.015, side, 0.002, rows=3), M["SCREEN"], c, side)

# ------------------------------------------------------------------ A: refined cab front
def front_refine():
    for p in ("CC_HeadlightBezel", "CC_Lamp", "CC_TailStrip", "CC_AntiClimber"): kill(p)
    c = coll("CabCar_Front")
    def surf_loop(cy, cz, loop, off):
        out = []
        for (u, v) in loop:
            l, n = hit(cy + u, cz + v); out.append(tuple(l + n * off))
        return out
    for s in (1, -1):
        S = "L" if s > 0 else "R"; cy, cz = s * 0.80, 1.43
        lp = rr(0.58, 0.21, 0.08, 6)
        loft(f"CC_HeadlightHousing_{S}", [surf_loop(cy, cz, lp, -0.002), surf_loop(cy, cz, lp, 0.016), surf_loop(cy, cz, rr(0.55, 0.18, 0.07, 6), 0.020)], M["BLACK"], c, caps=True, angle=40)
        bz = rr(0.60, 0.23, 0.09, 6)
        loft(f"CC_HeadlightBezel_{S}", [surf_loop(cy, cz, bz, 0.012), surf_loop(cy, cz, bz, 0.020), surf_loop(cy, cz, rr(0.57, 0.20, 0.08, 6), 0.022)], M["TRIM"], c, caps=False, angle=40)
        for k, (du, rad, emit) in enumerate(((s * 0.15, 0.062, M["HEADLAMP"]), (s * 0.015, 0.050, M["HEADLAMP"]), (-s * 0.135, 0.034, M["HEADLAMP"]))):
            l2, n2 = hit(cy + du, cz)
            T = Matrix.Translation(l2 + n2 * 0.020) @ n2.to_track_quat("Z", "Y").to_matrix().to_4x4()
            cup = lathe(f"CC_Reflector_{S}{k + 1}", [(rad * 0.30, -0.030), (rad * 0.95, -0.006), (rad, 0.0), (rad * 1.05, 0.0), (rad * 1.05, -0.010), (rad * 0.32, -0.036)], "z", (0, 0, 0), 28, M["CHROME"], c); cup.matrix_world = T
            led = lathe(f"CC_LED_{S}{k + 1}", [(0.002, -0.026), (rad * 0.28, -0.026), (rad * 0.28, -0.018), (0.002, -0.016)], "z", (0, 0, 0), 16, emit, c); led.matrix_world = T
            lens = lathe(f"CC_Lens_{S}{k + 1}", [(0.002, 0.0), (rad * 1.02, 0.0), (rad * 0.95, 0.008), (rad * 0.6, 0.014), (0.002, 0.016)], "z", (0, 0, 0), 28, M["LENS"], c); lens.matrix_world = T
        tl = rr(0.30, 0.036, 0.015, 3)
        loft(f"CC_TailLamp_{S}", [surf_loop(cy - s * 0.02, 1.265, tl, 0.000), surf_loop(cy - s * 0.02, 1.265, tl, 0.012)], M["TAIL"], c, caps=True)
        loft(f"CC_TailBezel_{S}", [surf_loop(cy - s * 0.02, 1.265, rr(0.33, 0.06, 0.025, 3), 0.004), surf_loop(cy - s * 0.02, 1.265, rr(0.33, 0.06, 0.025, 3), 0.010)], M["TRIM"], c, caps=False)
    # lower front grille in the bumper zone: dark frame + louvre blades
    fl = rr(1.50, 0.15, 0.03, 4)
    loft("CC_FrontGrilleFrame", [surf_loop(0, 1.085, fl, -0.002), surf_loop(0, 1.085, fl, 0.014)], M["BLACK"], c, caps=True, angle=40)
    bl = []
    for k in range(5):
        zz = 1.030 + k * 0.027; pts = []
        for kk in range(13):
            yy = -0.70 + 1.40 * kk / 12; l, n = hit(yy, zz); pts.append(tuple(l + n * 0.020))
        bl.append(tube("gb", pts, 0.006, M["TRIM"], c, res=1))
    join(bl, "CC_FrontGrilleBlades")
    # anti-climber ribs along the lower front edge
    rb = []
    for k in range(3):
        zz = 0.905 + 0.032 * k; pts = []
        for kk in range(15):
            yy = -1.02 + 2.04 * kk / 14; l, n = hit(yy, zz); pts.append(tuple(l + n * 0.022))
        rb.append(tube("ac", pts, 0.011, M["AXLEBOX"], c, res=2))
    join(rb, "CC_AntiClimber")
    # coupler pocket + air hoses
    bbox_bevel("CC_CouplerPocket", M["SEAL"], 10.93, 0, 0.74, 0.10, 0.62, 0.36, c, bevel=0.02)
    for s in (1, -1):
        pts = [(11.05, s * 0.22, 0.70)] + [(11.05 + 0.10 * math.sin(a), s * (0.22 + 0.05 * math.sin(a)), 0.70 - 0.20 * (1 - math.cos(a))) for a in [k * pi / 10 for k in range(1, 11)]]
        tube(f"CC_CouplerHose_{'L' if s > 0 else 'R'}", pts, 0.022, M["SEAL"], c, res=3)
    # windscreen wiper pivot caps
    for nm in ("CC_WiperPivot_L", "CC_WiperPivot_R"):
        ob = bpy.data.objects.get(nm)
        if ob: ob.data.materials.clear(); ob.data.materials.append(M["TRIM"])

# ------------------------------------------------------------------ C: bogie readability
def bogie_refine(tag, bx):
    c = coll("CabCar_Bogie_" + tag)
    for p, m in (("CC_SideFrame_" + tag, M["BOGIE2"]), ("CC_Transom_" + tag, M["BOGIE2"]), ("CC_AxleBox_" + tag, M["AXLEBOX"]),
                 ("CC_Calliper_" + tag, M["BRAKE"]), ("CC_VertDamper_" + tag, M["DAMPER"]), ("CC_YawDamper_" + tag, M["DAMPER"]),
                 ("CC_LatDamper_" + tag, M["DAMPER"]), ("CC_PrimarySpring_" + tag, M["SPRING2"])):
        recolor(p, m)
    for ia, ax in enumerate((-WB / 2, WB / 2)):
        for s in (1, -1):
            S = "L" if s > 0 else "R"
            for dx in (-0.13, 0.13):   # spring seats (lower + upper cups)
                for z0, up in ((0.588, 1), (0.716, -1)):
                    prof = [(0.03, 0.0), (0.095, 0.0), (0.095, up * 0.014), (0.07, up * 0.020), (0.03, up * 0.020)]
                    if up < 0: prof = prof[::-1]
                    lathe(f"CC_SpringSeat_{tag}{ia + 1}{S}", prof, "z", (bx + ax + dx, s * 1.0, z0), 20, M["AXLEBOX"], c)
            # speed sensor + cable from axle box to frame
            ex = s * 1.13
            lathe(f"CC_SpeedSensor_{tag}{ia + 1}{S}", [(0.003, 0), (0.035, 0), (0.035, 0.05), (0.003, 0.05)], "y", (bx + ax, ex - (0 if s > 0 else 0.05), WHEEL_R + 0.06), 16, M["BLACK"], c)
            tube(f"CC_SensorCable_{tag}{ia + 1}{S}", [(bx + ax, s * 1.16, WHEEL_R + 0.08), (bx + ax, s * 1.17, 0.60), (bx + ax * 0.82, s * 1.13, 0.66)], 0.010, M["SEAL"], c)
        # brake cylinders on the transom
        for s in (1, -1):
            lathe(f"CC_BrakeCylinder_{tag}{ia + 1}{'L' if s > 0 else 'R'}", [(0.03, -0.12), (0.075, -0.12), (0.08, -0.08), (0.08, 0.08), (0.075, 0.12), (0.03, 0.12)], "x",
                  (bx + ax * 0.55, s * 0.33, 0.58), 20, M["BRAKE"], c)
    # traction rods (bogie -> body) with rubber bushes
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        tube(f"CC_TractionRod_{tag}{S}", [(bx + 0.15, s * 0.42, 0.66), (bx + 0.95, s * 0.42, 0.80)], 0.028, M["AXLEBOX"], c)
        for p in ((bx + 0.15, s * 0.42, 0.66), (bx + 0.95, s * 0.42, 0.80)):
            lathe(f"CC_Bush_{tag}{S}", [(0.02, -0.04), (0.055, -0.04), (0.055, 0.04), (0.02, 0.04)], "y", p, 16, M["SEAL"], c)
        bbox_bevel(f"CC_BumpStop_{tag}{S}", M["SEAL"], bx, s * 0.20, 0.72, 0.10, 0.10, 0.06, c, bevel=0.015)
    # anti-roll bar with drop links
    tube(f"CC_AntiRollBar_{tag}", [(bx - 0.42, -1.02, 0.52), (bx - 0.42, 1.02, 0.52)], 0.030, M["BOGIE2"], c)
    for s in (1, -1):
        tube(f"CC_AntiRollLink_{tag}{'L' if s > 0 else 'R'}", [(bx - 0.42, s * 1.02, 0.52), (bx - 0.42, s * 1.06, 0.84)], 0.016, M["TRIM"], c)
    # lifeguards ahead of the leading wheels
    lead = bx + (WB / 2 + 0.55 if tag == "F" else -(WB / 2 + 0.55))
    for s in (1, -1):
        bbox_bevel(f"CC_Lifeguard_{tag}{'L' if s > 0 else 'R'}", M["SAFETYYEL"], lead, s * 0.7525, 0.20, 0.04, 0.16, 0.26, c, bevel=0.008)
    # flexible cable loops bogie -> body
    for s in (1, -1):
        pts = [(bx - 0.75, s * 0.85, 0.70)] + [(bx - 0.75 - 0.20 * math.sin(a), s * 0.85, 0.70 + 0.16 * (1 - math.cos(a))) for a in [k * pi / 8 for k in range(1, 9)]]
        tube(f"CC_BogieCable_{tag}{'L' if s > 0 else 'R'}", pts, 0.018, M["SEAL"], c, res=3)

# ------------------------------------------------------------------ C: underframe density / tonal separation
def underframe_refine():
    c = coll("CabCar_Underframe")
    for nm, m in (("CC_AuxConverter", M["EQMID"]), ("CC_BrakeControl", M["EQMID"]), ("CC_LowVoltage", M["EQMID"]), ("CC_SignallingCubicle", M["EQMID"])):
        recolor(nm, m, exact=True)
    boxes = {"CC_AuxConverter": (-5.2, -0.62, 1.8, 0.95, 0.50), "CC_BatteryBox": (-5.0, 0.70, 1.3, 0.80, 0.46), "CC_BrakeControl": (-2.4, -0.70, 1.2, 0.85, 0.44),
             "CC_Compressor": (-2.3, 0.65, 1.4, 0.95, 0.48), "CC_LowVoltage": (3.2, -0.66, 1.4, 0.80, 0.44), "CC_ToiletTank": (3.3, 0.70, 1.2, 0.82, 0.50)}
    hw = []
    for nm, (x, y, sx, sy, sz) in boxes.items():
        zc = 0.875 - sz / 2; face_y = y + (sy / 2 + 0.004) * (1 if y > 0 else -1)
        for dx in (-sx / 2 + 0.18, sx / 2 - 0.18):          # latches
            hw.append(bbox_bevel("lt", M["TRIM"], x + dx, face_y, zc + 0.05, 0.05, 0.012, 0.08, c, bevel=0.003))
        hw.append(bbox_bevel("hg", M["TRIM"], x, face_y, zc + sz / 2 - 0.05, sx - 0.30, 0.010, 0.015, c, bevel=0.002))   # hinge
        hw.append(bbox_bevel("pl", M["YELLOW"], x - sx / 2 + 0.12, face_y, zc - 0.08, 0.10, 0.006, 0.05, c, bevel=0.002))  # ID plate
    join(hw, "CC_EquipmentHardware")
    fins = [bbox_bevel("fn", M["ALU"], -5.2 - 0.75 + k * 0.10, -0.62, 0.36, 0.012, 0.80, 0.10, c, bevel=0.002) for k in range(16)]
    join(fins, "CC_HeatSinkFins")
    for k, (x0, x1, y) in enumerate(((-4.30, -2.95, 1.12), (0.9, 2.6, 1.12))):
        tp = [(0.04, x0), (0.12, x0), (0.19, x0 + 0.05), (0.21, x0 + 0.14), (0.21, x1 - 0.14), (0.19, x1 - 0.05), (0.12, x1), (0.04, x1)]
        lathe(f"CC_MainReservoir_{k + 1}", [(r, a) for (r, a) in tp], "x", (0, y, 0.62), 32, M["TANK"], c)
        for xs in (x0 + 0.30, x1 - 0.30):
            lathe(f"CC_TankStrap_{k + 1}", [(0.212, -0.02), (0.225, -0.02), (0.225, 0.02), (0.212, 0.02)], "x", (xs, y, 0.62), 32, M["BOGIE2"], c)
        tube(f"CC_TankPipe_{k + 1}", [(x1, y, 0.62), (x1 + 0.15, y, 0.62), (x1 + 0.15, y - 0.35, 0.80)], 0.014, M["TRIM"], c)
    bbox_bevel("CC_CableDuct", M["SEAL"], 0.0, 0.0, 0.84, 12.0, 0.30, 0.06, c, bevel=0.01)
    for k, x in enumerate((-3.6, 1.6, 4.6)):
        bbox_bevel(f"CC_JunctionBox_{k + 1}", M["EQMID"], x, 0.0, 0.76, 0.40, 0.30, 0.14, c, bevel=0.012, inset_sides=True)

# ------------------------------------------------------------------ D: roof units / antennas / seams
def roof_refine():
    c = coll("CabCar_Roof")
    for nm, x0, x1 in (("CC_SaloonHVAC_Rear", -10.80, -7.72), ("CC_SaloonHVAC_Front", 5.32, 8.02)):
        top = G.ZFLAT - 0.005 + 0.28
        for k, xf in enumerate((x0 + 0.75, x1 - 0.75)):
            ring = []
            for r0, r1 in ((0.27, 0.29), (0.20, 0.215), (0.13, 0.145), (0.06, 0.075)):
                ring.append(lathe("fr", [(r0, 0.0), (r1, 0.0), (r1, 0.010), (r0, 0.010)], "z", (xf, 0, top + 0.004), 40, M["BLACK"], c))
            for a in range(4):
                th = a * pi / 4
                ring.append(bbox_bevel("sp", M["BLACK"], xf, 0, top + 0.009, 0.56 * abs(math.cos(th)) + 0.012, 0.56 * abs(math.sin(th)) + 0.012, 0.006, c, bevel=0.002))
            ring.append(lathe("hub", [(0.003, 0), (0.05, 0), (0.05, 0.02), (0.003, 0.025)], "z", (xf, 0, top + 0.004), 24, M["AXLEBOX"], c))
            join(ring, f"{nm}_FanGrille{k + 1}")
        hatch = [bbox_bevel("ht", M["ROOF"], 0.5 * (x0 + x1), s * 0.62, top + 0.004, 0.70, 0.42, 0.008, c, bevel=0.003) for s in (1, -1)]
        join(hatch, f"{nm}_ServiceHatches")
    for k, x in enumerate((-6.2, -3.8, -1.4, 1.0, 3.4)):    # crown panel joints
        pts = [(x, y, G.roof_z(y) + 0.002) for y in [-1.15 + 2.3 * kk / 14 for kk in range(15)]]
        tube(f"CC_RoofSeam_{k + 1}", pts, 0.004, M["SEAL"], c, res=1)
    bbox_bevel("CC_GSMR_Antenna", M["BLACK"], -2.6, -0.35, G.roof_z(0.35) + 0.07, 0.22, 0.02, 0.14, c, bevel=0.008)
    lathe("CC_GPS_Antenna", [(0.003, 0), (0.07, 0), (0.07, 0.012), (0.05, 0.03), (0.003, 0.035)], "z", (-0.6, 0.30, G.roof_z(0.3)), 28, M["BLACK"], c)
    tube("CC_RoofConduit", [(-7.70, 0.75, G.ZFLAT + 0.02), (-7.30, 0.75, G.roof_z(0.75) + 0.02), (4.95, 0.75, G.roof_z(0.75) + 0.02), (5.35, 0.75, G.ZFLAT + 0.02)], 0.025, M["ROOF"], c, res=2)

# ------------------------------------------------------------------ E: interior enrichment
def interior_refine():
    c = coll("CabCar_Interior")
    wall_y = 1.455; RAIL_Y = wall_y - 0.52; fz = G.FLOOR_Z
    D = sorted(G.DOORS)
    for i, cx in enumerate(D):
        for s in (1, -1):
            S = "L" if s > 0 else "R"
            for e in (-1, 1):
                xs = cx + e * (G.DOOR_HW + 0.025)
                if not (G.X_REAR < xs < G.CAB_WALL_X - 0.05): continue
                tube(f"CC_DoorPole_{S}{i + 1}{'a' if e < 0 else 'b'}", [(xs, s * (wall_y - 0.50), fz), (xs, s * (wall_y - 0.50), G.CEIL_Z - 0.05)], 0.017, M["POLE"], c)
                fv = [(xs - 0.004 * e, s * wall_y, fz + 1.08), (xs - 0.004 * e, s * (wall_y - 0.49), fz + 1.08), (xs - 0.004 * e, s * (wall_y - 0.49), fz + 1.20), (xs - 0.004 * e, s * wall_y, fz + 1.20)]
                mk(f"CC_ScreenFrost_{S}{i + 1}{'a' if e < 0 else 'b'}", fv, [(0, 1, 2, 3)], [M["FROST"]], c, smooth=False)
                # door open/close button on the post + emergency handle
                bp = Vector(G.side_point(xs + e * 0.05, fz + 1.20, s, -0.06))
                lathe(f"CC_DoorButton_{S}{i + 1}{'a' if e < 0 else 'b'}", [(0.003, 0), (0.030, 0), (0.030, 0.012), (0.003, 0.016)], "y", tuple(bp), 20, M["GREEN"], c)
            ep = Vector(G.side_point(cx + G.DOOR_HW + 0.10, fz + 1.75, s, -0.06))
            bbox_bevel(f"CC_EmergencyHandle_{S}{i + 1}", M["RED"], ep.x, ep.y, ep.z, 0.10, 0.04, 0.16, c, bevel=0.01)
            # PID: glossy black screen with amber lines
            ob = bpy.data.objects.get(f"CC_PIDScreen_{S}{i + 1}")
            if ob: ob.data.materials.clear(); ob.data.materials.append(M["SCREEN"])
            for k, (w, dzl) in enumerate(((0.40, 0.025), (0.28, -0.012))):
                bbox_bevel(f"CC_PIDText_{S}{i + 1}{k}", M["AMBER"], cx - 0.04 + (w - 0.40) / 2, s * 1.169, G.CEIL_Z - 0.18 + dzl, w, 0.002, 0.012, c, bevel=0.0005)
    # seat cushions (fabric inserts) + armrests at bench ends
    seat_objs = [o for o in bpy.data.objects if o.name.startswith(("CC_Seat_", "CC_FlipSeat_"))]
    pads = {}
    for so in seat_objs:
        bb = [so.matrix_world @ Vector(v) for v in so.bound_box]
        xa, xb = min(v.x for v in bb), max(v.x for v in bb); s = 1 if sum(v.y for v in bb) > 0 else -1
        dz = G.FLOOR_Z - 1.05
        def pad(loop):
            return [[(xx, s * (wall_y - d), dz + z) for (d, z) in loop] for xx in (xa + 0.035, xa + 0.06, xb - 0.06, xb - 0.035)]
        pan = [(0.19, 1.546), (0.44, 1.524), (0.445, 1.548), (0.19, 1.572)]
        back = [(0.072, 1.97), (0.118, 1.66), (0.142, 1.668), (0.096, 1.98)]
        key = so.name.rsplit("_", 1)[0]
        pads.setdefault(key, [])
        pads[key].append(loft("pd", pad(pan), M["SEATINSET"], c, caps=True, subd=1, angle=50))
        pads[key].append(loft("pb", pad(back), M["SEATINSET"], c, caps=True, subd=1, angle=50))
    for key, objs in pads.items(): join(objs, key.replace("CC_Seat_", "CC_SeatPads_").replace("CC_FlipSeat_", "CC_FlipSeatPads_"))
    # floor: darker seat zones + aisle seam strips
    for s in (1, -1):
        bbox_bevel(f"CC_FloorSeatZone_{'L' if s > 0 else 'R'}", M["FLOOR2"], 0.5 * (G.X_REAR + G.CAB_WALL_X), s * 1.17, fz + 0.001, G.CAB_WALL_X - G.X_REAR - 0.2, 0.56, 0.002, c, bevel=0.0005)
    # CCTV domes + speakers in the ceiling, fire extinguisher at the rear end
    for k, x in enumerate((-9.6, -2.0, 6.0)):
        lathe(f"CC_CCTV_{k + 1}", [(0.003, 0.0), (0.07, 0.0), (0.065, -0.03), (0.04, -0.06), (0.003, -0.07)], "z", (x, 0.0, G.CEIL_Z - 0.012), 24, M["SCREEN"], c)
    for k, cx in enumerate(D):
        for x in (cx - 1.6, cx + 1.6):
            if G.X_REAR + 0.3 < x < G.CAB_WALL_X - 0.3:
                lathe(f"CC_Speaker_{k + 1}_{int(x * 10)}", [(0.003, 0.0), (0.075, 0.0), (0.075, -0.006), (0.003, -0.006)], "z", (x, 0.0, G.CEIL_Z - 0.01), 24, M["INTTRIM"], c)
    lathe("CC_FireExtinguisher", [(0.003, 0), (0.07, 0), (0.075, 0.05), (0.075, 0.42), (0.05, 0.48), (0.02, 0.52), (0.003, 0.52)], "z", (G.X_REAR + 0.20, -1.30, fz + 0.05), 24, M["RED"], c)
    recolor("CC_CeilingPanel", M["INTERIOR"], exact=True)
    RAIL_Z = fz + 1.85
    # triangular hand-straps (replace ring handholds)
    kill("CC_Handholds_")
    for s in (1, -1):
        S = "L" if s > 0 else "R"; parts = []
        xs_list = []
        for a_, b_ in zip(D[:-1], D[1:]):
            x0, x1 = a_ + G.DOOR_HW + 0.04, b_ - G.DOOR_HW - 0.04
            xs_list += [x0 + (k + 0.5) * (x1 - x0) / 5 for k in range(5)]
        for xh in xs_list:
            y = s * RAIL_Y; zt = RAIL_Z - 0.03
            parts.append(bbox_bevel("sp", M["STRAP"], xh, y, zt - 0.11, 0.035, 0.010, 0.20, c, bevel=0.003))
            parts.append(bbox_bevel("cl", M["HANDLE"], xh, y, zt - 0.005, 0.05, 0.05, 0.05, c, bevel=0.01))
            top, h, w = zt - 0.21, 0.14, 0.15
            tri = [(xh, y, top), (xh + w / 2, y, top - h), (xh - w / 2, y, top - h), (xh, y, top)]
            parts.append(tube("tr", tri, 0.012, M["HANDLE"], c, res=3))
        join(parts, f"CC_HandStraps_{S}")
        # rail hangers from the ceiling
        hg = [tube("hg", [(x, s * RAIL_Y, RAIL_Z), (x, s * RAIL_Y, G.CEIL_Z - 0.18)], 0.016, M["POLE"], c) for x in (-9.6, -6.0, -2.0, 2.0, 6.0)]
        join(hg, f"CC_RailHangers_{S}")
        # cyan accent light lines along the corner panels
        ring = [(G.X_REAR + 0.4, s * 1.24 + a_, G.CEIL_Z - 0.10 + b_) for (a_, b_) in rr(0.012, 0.012, 0.005, 2)]
        loft(f"CC_CyanAccent_{S}", [ring, [(G.CAB_WALL_X - 0.4, p[1], p[2]) for p in ring]], M["CYAN"], c, caps=True)
    # central split poles in each door zone (replace the trifurcate poles)
    kill("CC_TrifurcatePole_")
    for i, cx in enumerate(D):
        z0, z1 = fz + 0.90, fz + 2.05
        parts = [tube("c0", [(cx, 0, fz), (cx, 0, z0)], 0.019, M["POLE"], c), tube("c1", [(cx, 0, z1), (cx, 0, G.CEIL_Z)], 0.019, M["POLE"], c)]
        for e in (-1, 1):
            pts = [(cx, e * 0.11 * math.sin(pi * k / 12), z0 + (z1 - z0) * k / 12) for k in range(13)]
            parts.append(tube("cb", pts, 0.017, M["POLE"], c))
        parts.append(lathe("fl", [(0.003, 0), (0.06, 0), (0.05, 0.02), (0.02, 0.03), (0.003, 0.03)], "z", (cx, 0, fz), 20, M["POLE"], c))
        join(parts, f"CC_SplitPole_{i + 1}")
    # bowed door-side poles (replace the straight ones)
    kill("CC_DoorPole_")
    for i, cx in enumerate(D):
        for s in (1, -1):
            for e in (-1, 1):
                xs = cx + e * (G.DOOR_HW + 0.025)
                if not (G.X_REAR < xs < G.CAB_WALL_X - 0.05): continue
                y0 = s * (wall_y - 0.50)
                pts = [(xs, y0 - s * 0.07 * math.sin(pi * k / 14), fz + (G.CEIL_Z - 0.05 - fz) * k / 14) for k in range(15)]
                tube(f"CC_DoorPole_{'L' if s > 0 else 'R'}{i + 1}{'a' if e < 0 else 'b'}", pts, 0.017, M["POLE"], c)
    # interior door-leaf yellow edge warning strips + ribbed thresholds + intercom panels
    for i, cx in enumerate(D):
        for s in (1, -1):
            S = "L" if s > 0 else "R"
            for leaf, ex in (("a", cx - 0.008), ("b", cx + 0.008)):
                lo = bpy.data.objects.get(f"CC_Door_{S}{i + 1}{leaf}")
                xa, xb = (ex - 0.11, ex - 0.012) if leaf == "a" else (ex + 0.012, ex + 0.11)
                conform(f"CC_DoorYellow_{S}{i + 1}{leaf}", G.strip(xa, xb, fz + 0.10, fz + 1.95, s, -0.0335, 6), M["SAFETYYEL"], c, -s, 0.0, lo)
            th = [bbox_bevel("tb", M["TRIM"], cx, s * (wall_y - 0.06), fz + 0.004, 2 * G.DOOR_HW, 0.14, 0.008, c, bevel=0.002)]
            for k in range(4):
                th.append(bbox_bevel("tg", M["SEAL"], cx, s * (wall_y - 0.10 + 0.025 * k), fz + 0.0085, 2 * G.DOOR_HW - 0.04, 0.008, 0.002, c, bevel=0.0005))
            join(th, f"CC_InnerThreshold_{S}{i + 1}")
            ip = Vector(G.side_point(cx - G.DOOR_HW - 0.11, fz + 1.45, s, -0.06))
            panel = [bbox_bevel("ip", M["INTERIOR"], ip.x, ip.y, ip.z, 0.13, 0.03, 0.30, c, bevel=0.008),
                     bbox_bevel("il", M["HANDLE"], ip.x, ip.y - s * 0.016, ip.z + 0.07, 0.09, 0.004, 0.08, c, bevel=0.002),
                     lathe("ib", [(0.003, 0), (0.022, 0), (0.022, 0.01), (0.003, 0.012)], "y", (ip.x, ip.y - s * 0.016, ip.z - 0.06), 16, M["SCREEN"], c)]
            join(panel, f"CC_Intercom_{S}{i + 1}")
    # ceiling-hung double-sided information screens between doors
    for k, (a_, b_) in enumerate(zip(D[:-1], D[1:])):
        xm = 0.5 * (a_ + b_)
        parts = [bbox_bevel("tvh", M["INTTRIM"], xm, 0, G.CEIL_Z - 0.24, 0.06, 0.58, 0.34, c, bevel=0.012),
                 tube("tvm", [(xm, 0, G.CEIL_Z - 0.07), (xm, 0, G.CEIL_Z)], 0.02, M["POLE"], c)]
        for e in (-1, 1):
            parts.append(bbox_bevel("tvs", M["TVSCREEN"], xm + e * 0.032, 0, G.CEIL_Z - 0.24, 0.004, 0.50, 0.27, c, bevel=0.001))
        join(parts, f"CC_CeilingScreen_{k + 1}")

def run_details2():
    global SHELL
    SHELL = bpy.data.objects["CC_BodyShell"]
    mats2()
    if not globals().get("V3"): body_trims(); side_destinations()
    if not globals().get("V4"): front_refine()
    if not globals().get("V3"):
        for tag, bx in zip(("F", "R"), G.BOGIE_X): bogie_refine(tag, bx)
    underframe_refine(); roof_refine()
    if not globals().get("V3"): interior_refine()

run_details2()
print("details2 done:", stats())
