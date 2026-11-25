"""HQ commuter cab car - Blender builder. Run in Blender:
   exec(open(r"<folder>\\hq\\build_hq.py", encoding="utf-8").read())
Stages are controlled by STAGES set at bottom (shell, glazing, doors, scene, render).
"""
import bpy, bmesh, math, os, sys, importlib
from mathutils import Vector

HQ = os.path.join(os.path.expanduser("~"), "Downloads", "marmaray_roblox_paket", "blender", "hq")
if HQ not in sys.path: sys.path.insert(0, HQ)
import geom; importlib.reload(geom)
G = geom

# ================================================================== reset
def reset():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections): bpy.data.collections.remove(c)
    for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.curves, bpy.data.images, bpy.data.node_groups):
        for d in list(blk):
            try: blk.remove(d)
            except Exception: pass

# ================================================================== PBR materials
def _bsdf(m):
    m.use_nodes = True
    return m.node_tree.nodes.get("Principled BSDF"), m.node_tree
def _inp(b, *names):
    for n in names:
        if n in b.inputs: return b.inputs[n]
    return None
def mat_paint(name, rgb, rough=0.32, coat=1.0, metal=0.0):
    m = bpy.data.materials.new(name); b, _ = _bsdf(m)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    ci = _inp(b, "Coat Weight", "Clearcoat")
    if ci: ci.default_value = coat
    cr = _inp(b, "Coat Roughness", "Clearcoat Roughness")
    if cr: cr.default_value = 0.04
    m.diffuse_color = (*rgb, 1); return m
def mat_steel(name, rgb=(0.80, 0.81, 0.82), rough=0.30, scale=(1.0, 220.0, 1.0)):
    """Brushed stainless: anisotropic-looking roughness streaks via stretched noise along X."""
    m = bpy.data.materials.new(name); b, nt = _bsdf(m)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Metallic"].default_value = 1.0
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); nz = nt.nodes.new("ShaderNodeTexNoise")
    mp.inputs["Scale"].default_value = scale
    nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6.0
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = rough - 0.07; mr.inputs["To Max"].default_value = rough + 0.07
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    ai = _inp(b, "Anisotropic")
    if ai: ai.default_value = 0.6
    m.diffuse_color = (*rgb, 1); return m
def mat_glass(name, tint=(0.02, 0.028, 0.03), rough=0.03, alpha=0.42):
    """Thin tinted glazing: alpha-blended, reflective, no refraction (one-sided panes)."""
    m = bpy.data.materials.new(name); b, _ = _bsdf(m)
    b.inputs["Base Color"].default_value = (*tint, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = 0.0; b.inputs["IOR"].default_value = 1.52
    b.inputs["Alpha"].default_value = alpha
    for a, v in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND"), ("use_transparency_overlap", False), ("use_backface_culling", False)):
        try: setattr(m, a, v)
        except Exception: pass
    m.diffuse_color = (*tint, alpha); return m
def mat_plain(name, rgb, rough=0.6, metal=0.0, emit=0.0):
    m = bpy.data.materials.new(name); b, _ = _bsdf(m)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        _inp(b, "Emission Color", "Emission").default_value = (*rgb, 1); _inp(b, "Emission Strength").default_value = emit
    m.diffuse_color = (*rgb, 1); return m

M = {}
def build_materials():
    # palette: PMS 877 silver #A0A0A0, PMS 419 #212322, PMS 186 #C8102E, dark blue #142B70, white, RAL 9005 #0A0A0D
    M["STEEL"] = mat_paint("PBR_SilverMetallic_PMS877", (0.352, 0.352, 0.352), rough=0.34, coat=0.6, metal=0.65)
    M["ROOF"] = mat_paint("PBR_RoofSilverGrey", (0.30, 0.30, 0.31), rough=0.55, coat=0.15, metal=0.3)
    M["BAND"] = mat_paint("PBR_WindowBand_PMS419", (0.0152, 0.0168, 0.016), rough=0.18, coat=0.9)
    M["SKIRT"] = mat_paint("PBR_DarkBlue_142B70", (0.0070, 0.0242, 0.162), rough=0.30, coat=0.7)
    M["STRIPE"] = mat_paint("PBR_Red_PMS186", (0.578, 0.0052, 0.0273), rough=0.25, coat=0.8)
    M["DOOR"] = mat_paint("PBR_DoorSilver_PMS877", (0.352, 0.352, 0.352), rough=0.34, coat=0.6, metal=0.65)
    M["NOSE"] = mat_paint("PBR_CabWhite", (0.88, 0.885, 0.88), rough=0.22, coat=0.8)
    M["UNDER"] = mat_plain("PBR_UnderframeBlack_RAL9005", (0.0032, 0.0032, 0.004), rough=0.75)
    M["GLASS"] = mat_glass("PBR_TintedGlass")
    M["AMBER"] = mat_plain("PBR_DisplayAmber", (1.0, 0.45, 0.02), rough=0.3, emit=2.5)
    M["BLACK"] = mat_plain("PBR_BlackPlastic", (0.012, 0.012, 0.013), rough=0.45)
    M["INTERIOR"] = mat_plain("PBR_InteriorPanel", (0.66, 0.67, 0.66), rough=0.45)
    M["RIM"] = mat_plain("PBR_Rubber", (0.015, 0.015, 0.015), rough=0.85)
    M["FLOOR"] = mat_plain("PBR_FloorRubber", (0.22, 0.23, 0.24), rough=0.8)
    M["GROUND"] = mat_plain("PBR_Ballast", (0.11, 0.105, 0.10), rough=0.95)
    M["RAIL"] = mat_plain("PBR_RailSteel", (0.42, 0.40, 0.38), rough=0.45, metal=1.0)
    M["SLEEPER"] = mat_plain("PBR_Concrete", (0.45, 0.44, 0.42), rough=0.9)

# ================================================================== helpers
COLL = {}
def coll(name):
    if name not in COLL:
        c = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c); COLL[name] = c
    return COLL[name]
def mk(name, verts, faces, mats, collection, face_mats=None, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.validate(); me.update()
    for m in mats: me.materials.append(m)
    if face_mats:
        for p, mi in zip(me.polygons, face_mats): p.material_index = mi
    if smooth:
        for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); collection.objects.link(ob); return ob
def activate(ob):
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); bpy.context.view_layer.objects.active = ob
def apply_mods(ob):
    activate(ob)
    for md in list(ob.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
def smooth_by_angle(ob, deg=32):
    activate(ob)
    try: bpy.ops.object.shade_smooth_by_angle(angle=math.radians(deg))
    except Exception:
        bpy.ops.object.shade_smooth()
        if hasattr(ob.data, "use_auto_smooth"): ob.data.use_auto_smooth = True; ob.data.auto_smooth_angle = math.radians(deg)
def orient_side(ob, side):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for fc in bm.faces:
        fc.normal_update()
        if fc.normal.y * side < 0: fc.normal_flip()
    bm.to_mesh(ob.data); bm.free()
def solidify(ob, t, inner_mat_offset=None, rim_offset=None):
    md = ob.modifiers.new("Solidify", "SOLIDIFY"); md.thickness = t; md.offset = -1.0; md.use_even_offset = True
    if inner_mat_offset is not None: md.material_offset = inner_mat_offset
    if rim_offset is not None: md.material_offset_rim = rim_offset
    return md

# ================================================================== stage: shell
SHELL_KEYS = ["STEEL", "ROOF", "BAND", "STRIPE", "NOSE", "UNDER", "SKIRT", "HOLE", "WINDSCREEN"]
def build_shell():
    c = coll("CabCar_Exterior")
    v, f, keys, rings = G.shell()
    idx = {k: i for i, k in enumerate(SHELL_KEYS)}
    mats = [M.get(k, M["STEEL"]) for k in SHELL_KEYS]
    ob = mk("CC_BodyShell", v, f, mats, c, [idx[k] for k in keys])
    # orient normals outward
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
    sd = ob.modifiers.new("Subdivision", "SUBSURF"); sd.levels = 1; sd.render_levels = 1; sd.quality = 3
    apply_mods(ob)
    # windscreen glass = copy of windscreen faces, then cut all openings
    bm = bmesh.new(); bm.from_mesh(ob.data)
    ws = [fc for fc in bm.faces if fc.material_index == idx["WINDSCREEN"]]
    ws_bm = bmesh.new(); vmap = {}
    for fc in ws:
        nv = []
        for vv in fc.verts:
            if vv.index not in vmap: vmap[vv.index] = ws_bm.verts.new(vv.co + vv.normal * 0.004)
            nv.append(vmap[vv.index])
        ws_bm.faces.new(nv)
    holes = [fc for fc in bm.faces if fc.material_index in (idx["HOLE"], idx["WINDSCREEN"])]
    bmesh.ops.delete(bm, geom=holes, context="FACES")
    bm.to_mesh(ob.data); bm.free()
    if ws:
        me = bpy.data.meshes.new("CC_Windscreen"); ws_bm.to_mesh(me)
        for p in me.polygons: p.use_smooth = True
        me.materials.append(M["GLASS"])
        wso = bpy.data.objects.new("CC_Windscreen", me); c.objects.link(wso)
        smooth_by_angle(wso, 40)
    ws_bm.free()
    # interior lining + rubber rims via solidify material offsets
    n = len(SHELL_KEYS)
    for _ in range(n): ob.data.materials.append(M["INTERIOR"])
    ob.data.materials.append(M["RIM"])
    solidify(ob, 0.045, inner_mat_offset=n, rim_offset=2 * n)
    apply_mods(ob); smooth_by_angle(ob, 35)
    # rear end wall with gangway opening
    ev, ef = G.end_wall(G.X_REAR + 0.025)
    ew = mk("CC_RearEndWall", ev, ef, [M["STEEL"], M["INTERIOR"], M["RIM"]], c, smooth=False)
    bm = bmesh.new(); bm.from_mesh(ew.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for fc in bm.faces:
        if fc.normal.x > 0: fc.normal_flip()
    bm.to_mesh(ew.data); bm.free()
    solidify(ew, 0.06, inner_mat_offset=1, rim_offset=2); apply_mods(ew)
    return ob

# ================================================================== stage: glazing (side windows)
def build_glazing():
    c = coll("CabCar_Exterior")
    for side in (1, -1):
        for k, (a, b) in enumerate(G.windows()):
            v, f = G.pane_grid(a - 0.025, b + 0.025, G.WIN_Z0 - 0.025, G.WIN_Z1 + 0.025, G.WIN_R + 0.02, side, 0.002)
            ob = mk(f"CC_Window_{'L' if side > 0 else 'R'}{k + 1}", v, f, [M["GLASS"]], c)
            orient_side(ob, side)
            for pl in ob.data.polygons: pl.use_smooth = True

# ================================================================== stage: door leaves (sliding plug, separate meshes)
def build_doors():
    c = coll("CabCar_Doors")
    for side in (1, -1):
        S = "L" if side > 0 else "R"
        for i, cx in enumerate(G.DOORS):
            for leafname, (x0, x1) in (("a", (cx - G.DOOR_HW + 0.006, cx - 0.008)), ("b", (cx + 0.008, cx + G.DOOR_HW - 0.006))):
                hx0, hx1 = x0 + 0.10, x1 - 0.10
                hole = (hx0, hx1, 1.80, 2.90)
                v, f = G.leaf(x0, x1, G.DOOR_Z0 + 0.006, G.DOOR_Z1 - 0.006, hole, side, 0.0)
                ob = mk(f"CC_Door_{S}{i + 1}{leafname}", v, f, [M["DOOR"], M["INTERIOR"], M["RIM"]], c)
                orient_side(ob, side)
                solidify(ob, 0.035, inner_mat_offset=1, rim_offset=2); apply_mods(ob); smooth_by_angle(ob, 35)
                gv, gf = G.pane_grid(hx0 - 0.015, hx1 + 0.015, 1.80 - 0.015, 2.90 + 0.015, 0.06, side, -0.004)
                g = mk(f"CC_DoorGlass_{S}{i + 1}{leafname}", gv, gf, [M["GLASS"]], c)
                orient_side(g, side)
                for pl in g.data.polygons: pl.use_smooth = True
                g.parent = ob
                ob["slide_dir"] = -1 if leafname == "a" else 1; ob["slide_m"] = G.DOOR_HW - 0.02
        # hinged cab side door with drop window
        x0, x1, z0, z1 = G.CAB_DOOR
        hole = (x0 + 0.09, x1 - 0.09, 2.05, 2.90)
        v, f = G.leaf(x0 + 0.006, x1 - 0.006, z0 + 0.006, z1 - 0.006, hole, side, 0.0)
        ob = mk(f"CC_CabSideDoor_{S}", v, f, [M["NOSE"], M["INTERIOR"], M["RIM"]], c)
        orient_side(ob, side); solidify(ob, 0.04, inner_mat_offset=1, rim_offset=2); apply_mods(ob); smooth_by_angle(ob, 35)
        gv, gf = G.pane_grid(hole[0] - 0.015, hole[1] + 0.015, hole[2] - 0.015, hole[3] + 0.015, 0.05, side, -0.004)
        g = mk(f"CC_CabSideWindow_{S}", gv, gf, [M["GLASS"]], c); orient_side(g, side); g.parent = ob
        ob["hinge_x"] = x0; ob["note"] = "hinged cab door, drop window"
        # side destination displays above the windows either side of the centre door
        for k, cx in enumerate((-1.97, 2.06)):
            for nm, w, h, off, mat in (("Housing", 1.00, 0.12, 0.004, M["BLACK"]), ("LED", 0.92, 0.07, 0.007, M.get("AMBER", M["BLACK"]))):
                dv, df = G.pane_grid(cx - w / 2, cx + w / 2, 3.12 - h / 2, 3.12 + h / 2, 0.02, side, off, rows=4)
                d = mk(f"CC_SideDest{nm}_{S}{k + 1}", dv, df, [mat], c); orient_side(d, side); solidify(d, 0.006); apply_mods(d)

# ================================================================== stage: minimal interior shell (floor, cab wall)
def build_floor():
    c = coll("CabCar_Interior")
    x0, x1, w, zt = G.X_REAR + 0.05, G.CAB_WALL_X, 1.455, G.FLOOR_Z
    v = [(x0, -w, zt - 0.045), (x1, -w, zt - 0.045), (x1, w, zt - 0.045), (x0, w, zt - 0.045), (x0, -w, zt), (x1, -w, zt), (x1, w, zt), (x0, w, zt)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mk("CC_Floor", v, f, [M["FLOOR"]], c, smooth=False)

# ================================================================== stage: scene (world, light, track, cameras)
def build_scene():
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try: sc.render.engine = eng; break
        except Exception: pass
    ee = sc.eevee
    for a, val in (("use_raytracing", True), ("taa_render_samples", 64), ("use_shadows", True)):
        if hasattr(ee, a):
            try: setattr(ee, a, val)
            except Exception: pass
    try: sc.view_settings.view_transform = "AgX"
    except Exception: pass
    w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
    nt = w.node_tree; nt.nodes.clear()
    bg = nt.nodes.new("ShaderNodeBackground"); out = nt.nodes.new("ShaderNodeOutputWorld")
    sky = nt.nodes.new("ShaderNodeTexSky")
    for st in ("NISHITA", "MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "HOSEK_WILKIE"):
        try: sky.sky_type = st; break
        except Exception: pass
    try: sky.sun_elevation = math.radians(28); sky.sun_rotation = math.radians(210)
    except Exception: pass
    nt.links.new(sky.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 0.22
    nt.links.new(bg.outputs[0], out.inputs[0])
    sun = bpy.data.lights.new("Sun", "SUN"); sun.energy = 2.3; sun.angle = math.radians(2.5)
    for a, v in (("look", "AgX - Medium High Contrast"), ("exposure", -0.25)):
        try: setattr(sc.view_settings, a, v)
        except Exception: pass
    so = bpy.data.objects.new("Sun", sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(55), 0, math.radians(-35))
    c = coll("Scene_Track")
    gv = [(-40, -12, -0.30), (40, -12, -0.30), (40, 12, -0.30), (-40, 12, -0.30)]
    mk("Ground", gv, [(0, 1, 2, 3)], [M["GROUND"]], c, smooth=False)
    # rails: simplified 60E1-like section swept along X
    prof = [(-0.075, -0.172), (0.075, -0.172), (0.075, -0.160), (0.012, -0.140), (0.009, -0.040), (0.036, -0.030),
            (0.036, -0.004), (0.026, 0.0), (-0.026, 0.0), (-0.036, -0.004), (-0.036, -0.030), (-0.009, -0.040), (-0.012, -0.140), (-0.075, -0.160)]
    for s in (-1, 1):
        cy = s * 0.7525
        v = [(x, cy + py, pz) for x in (-40, 40) for (py, pz) in prof]; n = len(prof)
        f = [[j, (j + 1) % n, n + (j + 1) % n, n + j] for j in range(n)] + [list(range(n))[::-1], [n + j for j in range(n)]]
        mk(f"Rail_{s}", v, f, [M["RAIL"]], c, smooth=False)
    sl = []
    for k in range(-66, 67):
        x = k * 0.6
        sl += [(x - 0.13, -1.3, -0.30), (x + 0.13, -1.3, -0.30), (x + 0.13, 1.3, -0.30), (x - 0.13, 1.3, -0.30),
               (x - 0.11, -1.3, -0.172), (x + 0.11, -1.3, -0.172), (x + 0.11, 1.3, -0.172), (x - 0.11, 1.3, -0.172)]
    sf = []
    for k in range(len(sl) // 8):
        o = 8 * k; sf += [(o + 0, o + 1, o + 5, o + 4), (o + 1, o + 2, o + 6, o + 5), (o + 2, o + 3, o + 7, o + 6), (o + 3, o, o + 4, o + 7), (o + 4, o + 5, o + 6, o + 7)]
    mk("Sleepers", sl, sf, [M["SLEEPER"]], c, smooth=False)
    # cameras
    def cam(name, loc, rot, ortho=None, lens=50):
        cd = bpy.data.cameras.new(name)
        if ortho: cd.type = "ORTHO"; cd.ortho_scale = ortho
        else: cd.lens = lens
        cd.clip_end = 500
        co = bpy.data.objects.new(name, cd); sc.collection.objects.link(co); co.location = loc; co.rotation_euler = rot
        return co
    cam("Cam_Side", (0.0, -40, 2.0), (math.radians(90), 0, 0), ortho=23.8)
    cam("Cam_Front", (40, 0, 2.15), (math.radians(90), 0, math.radians(90)), ortho=4.6)
    cam("Cam_Top", (0, 0, 40), (0, 0, 0), ortho=23.8)
    def look_at(co, target):
        d = Vector(target) - co.location; co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    p = cam("Cam_Persp34", (19.5, -10.5, 3.2), (0, 0, 0), lens=45); look_at(p, (8.6, 0, 1.9))
    p = cam("Cam_PerspNose", (15.2, -5.6, 2.45), (0, 0, 0), lens=40); look_at(p, (9.9, 0, 2.0))
    p = cam("Cam_PerspSide", (-2.0, -9.0, 1.9), (0, 0, 0), lens=35); look_at(p, (0.5, 0, 2.0))

def render(name, cam, res=(1600, 900), out=None):
    sc = bpy.context.scene; sc.camera = bpy.data.objects[cam]
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    out = out or os.path.join(HQ, "renders", name + ".png"); os.makedirs(os.path.dirname(out), exist_ok=True)
    sc.render.filepath = out; bpy.ops.render.render(write_still=True); return out

def stats():
    dg = bpy.context.evaluated_depsgraph_get(); tot = 0; per = {}
    for o in bpy.data.objects:
        if o.type != "MESH" or not o.name.startswith("CC_"): continue
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); n = len(me.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
        tot += n; per[o.name] = n
    top = sorted(per.items(), key=lambda kv: -kv[1])[:4]
    return tot, len(per), top

if "STAGES" not in globals(): STAGES = {"reset", "shell", "glazing", "doors", "floor", "scene"}
if "reset" in STAGES: reset(); COLL.clear(); build_materials()
if "shell" in STAGES: build_shell()
if "glazing" in STAGES: build_glazing()
if "doors" in STAGES: build_doors()
if "floor" in STAGES: build_floor()
if "scene" in STAGES: build_scene()
print("HQ build done:", stats())
