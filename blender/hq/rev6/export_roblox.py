"""Rev 6 - Roblox export (FBX + GLB). The master scene is not modified: evaluated copies are built in a temporary
collection, consolidated to one material per mesh (Roblox: one material / SurfaceAppearance per MeshPart),
decimated / split to stay under 20,000 triangles per mesh, exported, then deleted.
Units: metres. In Roblox Importer set 'Scale Unit' = Meter (25:7 studs per metre -> 1 stud = 0.28 m)."""
import bpy, bmesh, os, math, re
from mathutils import Vector, Matrix
from common import EXPORT_DIR, TEX_DIR

TRI_LIMIT = 19500
TEX_EXPORT = 1024

# ------------------------------------------------------------------ which objects, grouped how
SKIP = re.compile(r"^(CC_Ref_|CC_Cutter_|CC_CabSection_|CC_CabFaceColumn_|CC_PaintSrc_|CC_MirrorY|CC_Controls|CC_LampRig|_)")
def part_of(o):
    n = o.name; cols = [c.name for c in o.users_collection]
    if SKIP.match(n) or not n.startswith("CC_") or o.type not in ("MESH", "CURVE", "FONT"): return None
    if n.startswith("CC_Body_Main"): return "Body_Main"
    if n.startswith("CC_Cab_Body"): return "Cab_Body"
    m = re.match(r"CC_Door_([LR]\d[ab])$", n)
    if m: return f"Door_{m.group(1)}"
    if n.startswith("CC_DoorGlass_") or n.startswith("CC_DoorSeal_") or n.startswith("CC_DoorFrit_"):
        par = o.parent.name if o.parent else ""
        m = re.match(r"CC_Door_([LR]\d[ab])$", par)
        if m: return f"Door_{m.group(1)}"
    if n.startswith("CC_CabSideDoor_") or n.startswith("CC_CabSideWindow_") or n.startswith("CC_CabWinFrit_"):
        return "CabDoor_" + ("L" if n.endswith("_L") else "R")
    m = re.match(r"CC_(Head|Tail)Lamp_([LR])_(\w+)$", n)
    if m: return f"Lamp_{m.group(1)}_{m.group(2)}_{m.group(3)}"
    m = re.match(r"CC_RobloxAnchor_(Head|Tail)Lamp_([LR])$", n)
    if m: return f"LightAnchor_{m.group(1)}_{m.group(2)}"
    if n.startswith("CC_Dest_Text"): return "Dest_Text"
    if n.startswith("CC_Dest_Panel"): return "Dest_Panel"
    if n.startswith("CC_Paint_"): return n.replace("CC_", "")
    if n.startswith("CC_Windscreen"): return "Windscreen"
    if n.startswith("CC_Bumper") or n.startswith("CC_Coupler") or n.startswith("CC_ObstacleDeflector"): return "Front_Bumper_Coupler"
    m = re.match(r"CC_B([FR])_Wheelset(\d)", n)
    if m: return f"Wheelset_{m.group(1)}{m.group(2)}"
    if "CabCar_Bogie_F" in cols: return "Bogie_F"
    if "CabCar_Bogie_R" in cols: return "Bogie_R"
    if "CabCar_Interior" in cols: return "Interior"
    if "CabCar_Roof" in cols: return "Roof"
    if "CabCar_Underframe" in cols: return "Underframe"
    if "CabCar_Gangway" in cols: return "Gangway"
    if "CabCar_Front" in cols: return "Front_Details"
    return "Exterior_Details"

DECIMATE = {"Interior": 0.35, "Roof": 0.45, "Underframe": 0.45, "Gangway": 0.5, "Bogie_F": 0.4, "Bogie_R": 0.4,
            "Front_Bumper_Coupler": 0.6, "Exterior_Details": 0.6, "Front_Details": 0.6}
WHEEL_RATIO = 0.5

# ------------------------------------------------------------------ material consolidation
CLASSES = {   # export material: (base colour, metallic, roughness, alpha, emission)
    "Black": ((0.012, 0.012, 0.013), 0.0, 0.6, 1, 0), "GlossBlack": ((0.004, 0.004, 0.005), 0.0, 0.15, 1, 0),
    "Steel": ((0.62, 0.63, 0.64), 1.0, 0.28, 1, 0), "Grey": ((0.30, 0.30, 0.31), 0.0, 0.5, 1, 0),
    "Bogie": ((0.11, 0.115, 0.12), 0.3, 0.45, 1, 0), "Roof": ((0.30, 0.30, 0.31), 0.0, 0.5, 1, 0),
    "Bumper": ((0.40, 0.405, 0.41), 0.9, 0.33, 1, 0), "Red": ((0.578, 0.0052, 0.0273), 0.0, 0.3, 1, 0),
    "White": ((0.92, 0.925, 0.92), 0.0, 0.15, 1, 0), "Interior": ((0.66, 0.67, 0.66), 0.0, 0.45, 1, 0),
    "Seat": ((0.006, 0.20, 0.46), 0.0, 0.4, 1, 0), "Floor": ((0.22, 0.23, 0.24), 0.0, 0.8, 1, 0),
    "Yellow": ((0.95, 0.70, 0.02), 0.0, 0.4, 1, 0), "Glass": ((0.02, 0.028, 0.03), 0.0, 0.03, 0.4, 0),
    "GlassRed": ((0.35, 0.004, 0.006), 0.0, 0.03, 0.55, 0), "NeonWhite": ((1.0, 0.96, 0.88), 0.0, 0.2, 1, 5),
    "NeonRed": ((1.0, 0.03, 0.02), 0.0, 0.2, 1, 3), "NeonOrange": ((1.0, 0.42, 0.02), 0.0, 0.3, 1, 3),
}
def classify(m):
    if m is None: return "Grey"
    n = m.name
    if n == "MAT_Body_Atlas": return "Atlas_Body"
    if n == "MAT_Cab_Atlas": return "Atlas_Cab"
    b = m.node_tree.nodes.get("Principled BSDF") if m.use_nodes else None
    col = tuple(b.inputs["Base Color"].default_value)[:3] if b else tuple(m.diffuse_color)[:3]
    alpha = b.inputs["Alpha"].default_value if b else 1.0
    emit = b.inputs["Emission Strength"].default_value if b else 0.0
    metal = b.inputs["Metallic"].default_value if b else 0.0
    lum = 0.2126 * col[0] + 0.7152 * col[1] + 0.0722 * col[2]
    if "LED_DotMatrix_Orange" in n or "LEDMatrix" in n or "Amber" in n: return "NeonOrange"
    if "Tail_Emitter" in n or "TailLED" in n: return "NeonRed"
    if "Emitter" in n or "Headlamp" in n or "DRL" in n: return "NeonWhite"
    if "Lens_Red" in n or "TailLens" in n: return "GlassRed"
    if alpha < 0.9 or "Glass" in n or "Lens" in n: return "Glass"
    if "MaskBlack" in n: return "GlossBlack"
    if "MaskOutline" in n: return "White"
    if "PAINT_Red" in n or "Red_PMS186" in n: return "Red"
    if "Bumper" in n or "Apron" in n: return "Bumper"
    if "Seat" in n: return "Seat"
    if "Floor" in n: return "Floor"
    if "Yellow" in n or "Safety" in n: return "Yellow"
    if "Roof" in n: return "Roof"
    if "Bogie" in n or "Brake" in n or "Axle" in n: return "Bogie"
    if "Interior" in n or "Wall" in n or "Ceil" in n or "Diffuser" in n or "Panel" in n: return "Interior"
    if lum < 0.035 or emit > 0 and lum < 0.05: return "Black"
    if metal > 0.5: return "Steel"
    return "Grey"

def export_material(cls, tex):
    name = f"EXP_{cls}"; m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes.get("Principled BSDF")
    if cls.startswith("Atlas_"):
        pre = "T_Body" if cls == "Atlas_Body" else "T_Cab"
        for kind, sock, cs in (("BaseColor", "Base Color", "sRGB"), ("Roughness", "Roughness", "Non-Color"), ("Metallic", "Metallic", "Non-Color")):
            n = nt.nodes.new("ShaderNodeTexImage"); n.image = tex[f"{pre}_{kind}"]; n.image.colorspace_settings.name = cs
            nt.links.new(n.outputs["Color"], b.inputs[sock])
        return m
    col, metal, rough, alpha, emit = CLASSES[cls]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Metallic"].default_value = metal; b.inputs["Roughness"].default_value = rough
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        try: m.surface_render_method = "BLENDED"
        except Exception: pass
    if emit: b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def export_textures():
    os.makedirs(os.path.join(EXPORT_DIR, "textures"), exist_ok=True); out = {}
    for pre in ("T_Body", "T_Cab"):
        for kind in ("BaseColor", "Roughness", "Metallic"):
            src = bpy.data.images.get(f"{pre}_{kind}_4096")
            if src is None:
                p = os.path.join(TEX_DIR, f"{pre}_{kind}_4096.png"); src = bpy.data.images.load(p, check_existing=True)
            im = src.copy(); im.name = f"{pre}_{kind}_{TEX_EXPORT}"; im.scale(TEX_EXPORT, TEX_EXPORT)
            im.filepath_raw = os.path.join(EXPORT_DIR, "textures", im.name + ".png"); im.file_format = "PNG"; im.save()
            out[f"{pre}_{kind}"] = im
    return out

# ------------------------------------------------------------------ realise, consolidate, limit
def realise(o, dg):
    ev = o.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    mw = o.matrix_world.copy(); me.transform(mw)
    if mw.determinant() < 0: me.flip_normals()
    return me

def build_parts(tex, tmp):
    dg = bpy.context.evaluated_depsgraph_get()
    saved = []
    body = bpy.data.objects.get("CC_Body_Main")
    if body:                                     # export the body cage without subdivision (smooth shading keeps it round)
        for md in body.modifiers:
            if md.type == "SUBSURF": saved.append((md, "levels", md.levels)); md.levels = 0
            if md.type == "SOLIDIFY": saved.append((md, "use_even_offset", md.use_even_offset)); md.use_even_offset = False
        dg.update()
    groups = {}
    for o in bpy.context.scene.objects:
        g = part_of(o)
        if g is None or (o.hide_render and not g.startswith("LightAnchor")): continue
        groups.setdefault(g, []).append(o)
    parts = []
    for g, obs in sorted(groups.items()):
        per_cls = {}
        for o in obs:
            me = realise(o, dg)
            if len(me.polygons) == 0: bpy.data.meshes.remove(me); continue
            per_cls_local = {}
            for i, m in enumerate(me.materials):
                per_cls_local[i] = classify(m)
            bm = bmesh.new(); bm.from_mesh(me); bpy.data.meshes.remove(me)
            uv = None
            for l in bm.loops.layers.uv.values():
                if l.name in ("UV_BodyAtlas", "UV_CabAtlas"): uv = l
            for cls in set(per_cls_local.values()):
                sub = bm.copy()
                bmesh.ops.delete(sub, geom=[f for f in sub.faces if per_cls_local.get(f.material_index, "Grey") != cls], context="FACES")
                if len(sub.faces) == 0: sub.free(); continue
                per_cls.setdefault(cls, []).append(sub)
            bm.free()
        for cls, bms in per_cls.items():
            me = bpy.data.meshes.new(f"{g}_{cls}"); acc = bmesh.new()
            for b_ in bms:
                tmpm = bpy.data.meshes.new("t"); b_.to_mesh(tmpm); acc.from_mesh(tmpm); bpy.data.meshes.remove(tmpm); b_.free()
            acc.to_mesh(me); acc.free()
            keep = "UV_BodyAtlas" if cls == "Atlas_Body" else "UV_CabAtlas" if cls == "Atlas_Cab" else None
            for l in list(me.uv_layers):
                if l.name != keep: me.uv_layers.remove(l)
            if keep and me.uv_layers: me.uv_layers[0].name = "UVMap"
            me.materials.clear(); me.materials.append(export_material(cls, tex))
            for p in me.polygons: p.material_index = 0; p.use_smooth = True
            name = g if len(per_cls) == 1 else f"{g}_{cls.replace('Atlas_', '')}"
            ob = bpy.data.objects.new(name, me); tmp.objects.link(ob); parts.append((g, ob))
    for md, attr, val in saved: setattr(md, attr, val)
    return parts

def tris(ob):
    ob.data.calc_loop_triangles(); return len(ob.data.loop_triangles)

def limit(parts, tmp):
    out = []
    for g, ob in parts:
        ratio = DECIMATE.get(g, WHEEL_RATIO if g.startswith("Wheelset") else 1.0)
        if ratio < 1.0 and tris(ob) > 3000:
            md = ob.modifiers.new("Dec", "DECIMATE"); md.ratio = ratio
            bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier=md.name)
        if tris(ob) <= TRI_LIMIT: out.append(ob); continue
        if g.startswith("Body") or g.startswith("Cab_Body") or g == "Interior":
            out += split_x(ob, tmp)
        else:
            md = ob.modifiers.new("Dec", "DECIMATE"); md.ratio = TRI_LIMIT / tris(ob) * 0.97
            bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier=md.name); out.append(ob)
    return out

def split_x(ob, tmp):
    n = math.ceil(tris(ob) / TRI_LIMIT) + (1 if tris(ob) > TRI_LIMIT * 1.6 else 0)
    xs = sorted(sum((ob.data.vertices[v].co.x for v in p.vertices)) / len(p.vertices) for p in ob.data.polygons)
    cuts = [xs[int(len(xs) * k / n)] for k in range(1, n)]
    res = []
    for k in range(n):
        lo = cuts[k - 1] if k > 0 else -1e9; hi = cuts[k] if k < n - 1 else 1e9
        me = ob.data.copy(); bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if not (lo <= f.calc_center_median().x < hi)], context="FACES")
        bm.to_mesh(me); bm.free()
        o2 = bpy.data.objects.new(f"{ob.name}_{chr(65 + k)}", me); tmp.objects.link(o2)
        if tris(o2) > TRI_LIMIT:
            md = o2.modifiers.new("Dec", "DECIMATE"); md.ratio = TRI_LIMIT / tris(o2) * 0.97
            bpy.context.view_layer.objects.active = o2; bpy.ops.object.modifier_apply(modifier=md.name)
        res.append(o2)
    bpy.data.objects.remove(ob, do_unlink=True)
    return res

def export_all(basename="Marmaray_CabCar_Rev6"):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    tmp = bpy.data.collections.new("EXPORT_TMP"); bpy.context.scene.collection.children.link(tmp)
    tex = export_textures()
    try:
        parts = limit(build_parts(tex, tmp), tmp)
        root = bpy.data.objects.new(basename, None); tmp.objects.link(root)
        for o in parts: o.parent = root
        for o in bpy.context.selected_objects: o.select_set(False)
        for o in parts + [root]: o.select_set(True)
        bpy.context.view_layer.objects.active = root
        fbx = os.path.join(EXPORT_DIR, basename + ".fbx"); glb = os.path.join(EXPORT_DIR, basename + ".glb")
        bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={"MESH", "EMPTY"}, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
                                 axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", use_mesh_modifiers=True, path_mode="COPY", embed_textures=True, add_leaf_bones=False)
        bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
        stats = sorted(((o.name, tris(o)) for o in parts), key=lambda t: -t[1])
        report = {"parts": len(parts), "total_tris": sum(t for _, t in stats), "max_part": stats[0], "fbx": fbx, "glb": glb}
        with open(os.path.join(EXPORT_DIR, basename + "_parts.txt"), "w", encoding="utf-8") as fh:
            fh.write(f"parts {len(parts)}  total triangles {report['total_tris']}\n")
            for n, t in stats: fh.write(f"{t:7d}  {n}\n")
        return report
    finally:
        for o in list(tmp.objects):
            me = o.data; bpy.data.objects.remove(o, do_unlink=True)
            if me is not None and me.users == 0: bpy.data.meshes.remove(me)
        bpy.data.collections.remove(tmp)
        for m in [m for m in bpy.data.materials if m.name.startswith("EXP_")]: bpy.data.materials.remove(m)
        for im in list(tex.values()): bpy.data.images.remove(im)
