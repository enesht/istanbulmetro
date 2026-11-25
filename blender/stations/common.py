"""Marmaray istasyon modelleme - ortak altyapi.

Birim: 1 Blender birimi = 1 metre (sahne metrik, scale_length = 1.0).
Koordinat kurgusu (istasyon yerel):
    +X  = Yol 1 ekseninden SOLA (MarmarayLayout'un + yonu ile ayni)
    +Y  = seyir yonu (Halkali -> Gebze), peron uzun ekseni
    +Z  = yukari; Z = 0 -> RAY USTU (top of rail). Peron ustu Z = +1.10

OLCU GUVENI
    Her olcu sabiti ya PV (photo-verified: fotograftan turetildi) ya da
    AS (assumed: fotografta yok, makul varsayim) olarak isaretlenir.
    AS olanlari kesin bilgi gibi kullanma; referans gelince duzelt.
"""

import bpy
import bmesh
from mathutils import Vector

# --------------------------------------------------------------------------- sabitler
RAIL_TOP = 0.0          # Z datum
PLATFORM_TOP = 1.10     # PV: peron ustu ray ustunden 1.10 m (MarmarayLayout)
GAUGE = 1.435           # PV: standart aciklik


def mark(kind, note):
    """Olcu guven etiketini konsola yaz (PV = fotograf, AS = varsayim)."""
    assert kind in ("PV", "AS")
    return note


# --------------------------------------------------------------------------- sahne
def reset_scene(unit_metric=True):
    """Sahneyi tamamen bosalt. SADECE yeni/bos dosyada cagir."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.curves,
                  bpy.data.images, bpy.data.node_groups):
        for item in list(block):
            if item.users == 0:
                block.remove(item)
    if unit_metric:
        us = bpy.context.scene.unit_settings
        us.system = "METRIC"
        us.scale_length = 1.0
        us.length_unit = "METERS"


def set_engine(preferred=("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES")):
    """Motoru ayarla. Enum kimlikleri surumden surume degisir: okuyarak dene."""
    scn = bpy.context.scene
    current = scn.render.engine
    for name in preferred:
        if name == current:
            return current
        try:
            scn.render.engine = name
            return name
        except TypeError:
            continue
    return current


def collection(name, parent=None):
    """Isimli koleksiyon dondur, yoksa olustur."""
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
    target = parent if parent is not None else bpy.context.scene.collection
    if col.name not in target.children:
        target.children.link(col)
    return col


def put(obj, col):
    """Nesneyi yalnizca verilen koleksiyonda birak."""
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    return obj


# --------------------------------------------------------------------------- malzeme
def _principled(mat):
    """Principled BSDF dugumunu TIPINDEN bul (isimler yerellestirilmis olabilir)."""
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def _set(node, names, value):
    """Girdiyi birden fazla olasi isimden ilk tutana yaz (surum farki)."""
    for n in names:
        sock = node.inputs.get(n)
        if sock is not None:
            sock.default_value = value
            return True
    return False


def material(name, base, roughness=0.6, metallic=0.0, specular=None,
             emission=None, emission_strength=0.0, alpha=1.0, ior=None):
    """PBR malzeme olustur/guncelle. base = (r,g,b) lineer 0-1."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = _principled(mat)
    _set(bsdf, ["Base Color"], (*base, 1.0))
    _set(bsdf, ["Roughness"], roughness)
    _set(bsdf, ["Metallic"], metallic)
    if specular is not None:
        _set(bsdf, ["Specular IOR Level", "Specular"], specular)
    if ior is not None:
        _set(bsdf, ["IOR"], ior)
    if alpha < 1.0:
        _set(bsdf, ["Alpha"], alpha)
        mat.blend_method = "BLEND" if hasattr(mat, "blend_method") else mat.blend_method
    if emission is not None:
        _set(bsdf, ["Emission Color", "Emission"], (*emission, 1.0))
        _set(bsdf, ["Emission Strength"], emission_strength)
    return mat


def assign(obj, *mats):
    """Malzemeleri nesneye sirayla ata (slot 0,1,2...)."""
    obj.data.materials.clear()
    for m in mats:
        obj.data.materials.append(m)
    return obj


# --------------------------------------------------------------------------- geometri
def box(name, size, center=(0, 0, 0), col=None, mat=None):
    """Eksen hizali kutu. size/center metre."""
    sx, sy, sz = size
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((sx, sy, sz)), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    obj.location = center
    (col or bpy.context.scene.collection).objects.link(obj)
    if mat:
        assign(obj, mat)
    return obj


def slab(name, x0, x1, y0, y1, z0, z1, col=None, mat=None):
    """Iki kose noktasindan kutu - istasyon isinde kenar vermek daha okunur."""
    return box(name,
               (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)),
               ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
               col, mat)


def cylinder(name, radius, depth, center=(0, 0, 0), verts=32, col=None, mat=None,
             axis="Z"):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts,
                          radius1=radius, radius2=radius, depth=depth)
    if axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts,
                         matrix=__import__("mathutils").Matrix.Rotation(1.5707963, 3, "X"))
    elif axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts,
                         matrix=__import__("mathutils").Matrix.Rotation(1.5707963, 3, "Y"))
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    obj.location = center
    (col or bpy.context.scene.collection).objects.link(obj)
    if mat:
        assign(obj, mat)
    return obj


def bevel(obj, width=0.004, segments=2, angle_deg=40.0, harden=True):
    """Kalite icin kenar kirma. Gercek geometri degil modifier - export'ta uygulanir.

    harden_normals yalnizca mesh duz-olmayan golgelemedeyken anlamli. Blender 4.1
    use_auto_smooth'u kaldirdi; varsa yaz, yoksa aciya gore smooth operatorunu dene.
    """
    m = obj.modifiers.new("Bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = angle_deg * 3.14159265 / 180.0
    if harden and segments > 1:
        if hasattr(obj.data, "use_auto_smooth"):      # 4.0 ve oncesi
            obj.data.use_auto_smooth = True
            m.harden_normals = True
        else:                                          # 4.1+
            smooth_by_angle(obj, angle_deg)
            # harden_normals 4.1+'ta ozel veri gerektirir; sessizce atla
    return m


def smooth_by_angle(obj, angle_deg=40.0):
    """Blender 4.1+ : aciya gore golgeleme. Operator yoksa duz birak."""
    op = getattr(bpy.ops.object, "shade_smooth_by_angle", None)
    if op is None:
        return False
    prev_active = bpy.context.view_layer.objects.active
    prev_sel = [o for o in bpy.context.selected_objects]
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        op(angle=angle_deg * 3.14159265 / 180.0)
        ok = True
    except (RuntimeError, TypeError):
        ok = False
    bpy.ops.object.select_all(action="DESELECT")
    for o in prev_sel:
        try:
            o.select_set(True)
        except ReferenceError:
            pass
    bpy.context.view_layer.objects.active = prev_active
    return ok


def array_y(obj, count, pitch):
    """Y ekseninde pitch araliklariyla cogalt."""
    m = obj.modifiers.new("ArrayY", "ARRAY")
    m.count = count
    m.use_relative_offset = False
    m.use_constant_offset = True
    m.constant_offset_displace = (0.0, pitch, 0.0)
    return m


def join(objs, name):
    """Nesneleri tek mesh'te birlestir; ilki hedef olur."""
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    objs[0].name = name
    return objs[0]


def stats():
    """Poli sayimi - kalite/butce takibi icin."""
    tris = 0
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
    return {"objects": len(bpy.context.scene.objects), "tris": tris}
