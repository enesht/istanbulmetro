"""Rev 6 - UV atlases, 4096 bakes and SVG layouts.
Atlases (textures/):
  T_Body_BaseColor_4096.png / T_Body_Roughness_4096.png / T_Body_Metallic_4096.png   -> CC_Body_Main, door leaves, cab side doors (UV 'UV_BodyAtlas')
  T_Cab_BaseColor_4096.png  / T_Cab_Roughness_4096.png  / T_Cab_Metallic_4096.png    -> CC_Cab_Body (UV 'UV_CabAtlas')
  UV_Body_4096.svg, UV_Cab_4096.svg  : UV layouts to paint over
The PNGs are the live colour source of MAT_Body_Atlas / MAT_Cab_Atlas in the master file: repaint them, reload images.
rebake() recreates them from PBR_Livery_Procedural (overwrites the PNGs)."""
import bpy, os, math
from common import G, TEX_DIR, coll, activate, mat

SIZE = 4096
DOOR_REGION = (0.565, 0.02, 0.985, 0.98)          # u0, v0, u1, v1 of the body atlas used for the door leaves

def door_objects():
    return sorted([o for o in bpy.data.objects if o.type == "MESH" and (o.name.startswith("CC_Door_") or o.name.startswith("CC_CabSideDoor_"))], key=lambda o: o.name)

def door_uvs():
    body = bpy.data.objects["CC_Body_Main"]; k = body["uv_scale_per_m"]
    u0, v0, u1, v1 = DOOR_REGION; cols = int((u1 - u0) / (0.90 * k + 0.004)); x_cur, row = 0, 0
    placed = []
    for o in door_objects():
        me = o.data; ws = [o.matrix_world @ v.co for v in me.vertices]
        xmin, xmax = min(p.x for p in ws), max(p.x for p in ws); zmin, zmax = min(p.z for p in ws), max(p.z for p in ws)
        w, h = (xmax - xmin) * k, (zmax - zmin) * k
        if x_cur >= cols: x_cur, row = 0, row + 1
        ou = u0 + x_cur * ((u1 - u0) / cols); ov = v0 + row * (h + 0.012)
        uvl = me.uv_layers.get("UV_BodyAtlas") or me.uv_layers.new(name="UV_BodyAtlas"); me.uv_layers.active = uvl
        for poly in me.polygons:
            for li in poly.loop_indices:
                p = ws[me.loops[li].vertex_index]
                uvl.data[li].uv = (ou + (p.x - xmin) * k, ov + (p.z - zmin) * k) if poly.material_index == 0 else (0.997, 0.997)
        placed.append((o.name, round(ou, 3), round(ov, 3))); x_cur += 1
    return placed

def _image(name, colorspace):
    img = bpy.data.images.get(name)
    if img and (img.size[0] != SIZE): bpy.data.images.remove(img); img = None
    if img is None: img = bpy.data.images.new(name, SIZE, SIZE, alpha=False)
    img.colorspace_settings.name = colorspace
    img.filepath_raw = os.path.join(TEX_DIR, name + ".png"); img.file_format = "PNG"
    return img

class _BakeSetup:
    """temporarily: target image node in every material, atlas UV active, Solidify off (inner faces would overlap)."""
    def __init__(self, objs, uv_name, img): self.objs, self.uv, self.img = objs, uv_name, img
    def __enter__(self):
        self.mats = {m for o in self.objs for m in o.data.materials if m}
        self.saved_uv, self.saved_mods = {}, []
        for m in self.mats:
            nt = m.node_tree; node = nt.nodes.get("BAKE_TARGET") or nt.nodes.new("ShaderNodeTexImage")
            node.name = "BAKE_TARGET"; node.image = self.img
            for n_ in nt.nodes: n_.select = False
            node.select = True; nt.nodes.active = node
        for o in self.objs:
            uvs = o.data.uv_layers; self.saved_uv[o.name] = (uvs.active.name if uvs.active else None)
            uvs.active = uvs[self.uv]
            for l in uvs: l.active_render = (l.name == self.uv)
            for md in o.modifiers:
                if md.type == "SOLIDIFY" and md.show_render: md.show_render = False; md.show_viewport = False; self.saved_mods.append(md)
        for o in bpy.context.selected_objects: o.select_set(False)
        for o in self.objs: o.select_set(True)
        bpy.context.view_layer.objects.active = self.objs[0]
        return self
    def __exit__(self, *a):
        for m in self.mats:
            n = m.node_tree.nodes.get("BAKE_TARGET")
            if n: m.node_tree.nodes.remove(n)
        for md in self.saved_mods: md.show_render = True; md.show_viewport = True

def _bake(objs, uv_name, img, kind, clear=True):
    """kind: color | rough | metal.  Bakes the current materials (PBR_Livery_Procedural on the paint slots) into img."""
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 4
    bk = sc.render.bake; bk.margin = 12; bk.use_clear = clear
    sock = {"color": "Base Color", "rough": "Roughness", "metal": "Metallic"}[kind]
    m = mat("PBR_Livery_Procedural"); nt = m.node_tree; b = nt.nodes.get("Principled BSDF")
    src = b.inputs[sock].links[0].from_socket if b.inputs[sock].is_linked else None
    es = b.inputs["Emission Strength"].default_value
    with _BakeSetup(objs, uv_name, img):
        # exact albedo / roughness / metalness via the emission channel (the diffuse pass would darken metals)
        if src: nt.links.new(src, b.inputs["Emission Color"])
        else:
            dv = b.inputs[sock].default_value
            b.inputs["Emission Color"].default_value = tuple(dv) if hasattr(dv, "__len__") else (dv, dv, dv, 1)
        b.inputs["Emission Strength"].default_value = 1.0
        try:
            bpy.ops.object.bake(type="EMIT", margin=12, use_clear=clear)
        finally:
            b.inputs["Emission Strength"].default_value = es
            for l in list(nt.links):
                if l.to_socket == b.inputs["Emission Color"]: nt.links.remove(l)
            b.inputs["Emission Color"].default_value = (0, 0, 0, 1)
    img.save()
    if img.packed_file: img.pack()   # .blend icindeki paketli kopyayi PNG ile esitle
    try: img.filepath_raw = bpy.path.relpath(img.filepath_raw)   # tasinabilir (//textures/...)
    except ValueError: pass
    return img.filepath_raw

def use_procedural(objs, atlas_mat):
    """paint slot (index 0) back to the procedural source for (re)baking."""
    proc = mat("PBR_Livery_Procedural")
    for o in objs:
        m = o.data.materials[0] if len(o.data.materials) else None
        if m is None or m.name.startswith("MAT_") or m.name.startswith("PBR_Livery"): o.data.materials[0] = proc

def atlas_material(name, prefix, uv_name):
    m = bpy.data.materials.get(name)
    if m: bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes.get("Principled BSDF")
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = uv_name
    for kind, sock, cs in (("BaseColor", "Base Color", "sRGB"), ("Roughness", "Roughness", "Non-Color"), ("Metallic", "Metallic", "Non-Color")):
        im = bpy.data.images.get(f"{prefix}_{kind}_{SIZE}")
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = im; n.name = kind; im.colorspace_settings.name = cs
        nt.links.new(uvn.outputs[0], n.inputs["Vector"]); nt.links.new(n.outputs["Color"], b.inputs[sock])
    b.inputs["Coat Weight"].default_value = 0.3; b.inputs["Coat Roughness"].default_value = 0.04
    return m

def assign_atlas(objs, m):
    for o in objs:
        if len(o.data.materials): o.data.materials[0] = m

def export_svg(objs, uv_name, path):
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in objs: o.select_set(True); o.data.uv_layers.active = o.data.uv_layers[uv_name]
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    try:
        bpy.ops.uv.export_layout(filepath=path, export_all=True, modified=False, mode="SVG", size=(SIZE, SIZE), opacity=0.0)
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
    return path

def body_objects(): return [bpy.data.objects["CC_Body_Main"]] + door_objects()
def cab_objects(): return [bpy.data.objects["CC_Cab_Body"]]

def bake_set(which):
    os.makedirs(TEX_DIR, exist_ok=True)
    if which == "body": objs, prefix, uv = body_objects(), "T_Body", "UV_BodyAtlas"
    else: objs, prefix, uv = cab_objects(), "T_Cab", "UV_CabAtlas"
    use_procedural(objs, None)
    out = []
    for kind, cs, tag in (("color", "sRGB", "BaseColor"), ("rough", "Non-Color", "Roughness"), ("metal", "Non-Color", "Metallic")):
        out.append(_bake(objs, uv, _image(f"{prefix}_{tag}_{SIZE}", cs), kind))
    return out

def finish():
    mb = atlas_material("MAT_Body_Atlas", "T_Body", "UV_BodyAtlas"); mc = atlas_material("MAT_Cab_Atlas", "T_Cab", "UV_CabAtlas")
    assign_atlas(body_objects(), mb); assign_atlas(cab_objects(), mc)
    sv = [export_svg(body_objects(), "UV_BodyAtlas", os.path.join(TEX_DIR, "UV_Body_4096.svg")),
          export_svg(cab_objects(), "UV_CabAtlas", os.path.join(TEX_DIR, "UV_Cab_4096.svg"))]
    m = mat("PBR_Livery_Procedural"); m.use_fake_user = True
    sc = bpy.context.scene; sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
    return sv

def run_all():
    door_uvs(); bake_set("body"); bake_set("cab"); return finish()

def bake_doors_only():
    """re-bake just the door leaves into the existing body atlas (no clear)."""
    objs = door_objects(); use_procedural(objs, None)
    for kind, tag in (("color", "BaseColor"), ("rough", "Roughness"), ("metal", "Metallic")):
        _bake(objs, "UV_BodyAtlas", bpy.data.images[f"T_Body_{tag}_{SIZE}"], kind, clear=False)
    assign_atlas(objs, bpy.data.materials["MAT_Body_Atlas"])

def rebake():
    """after editing the procedural paint: re-bake both atlases and re-assign."""
    return run_all()
