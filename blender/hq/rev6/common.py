"""Rev 6 shared helpers (Blender 5.x). Imported by every rev6 module."""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HQ = os.path.join(os.path.expanduser("~"), "Downloads", "marmaray_roblox_paket", "blender", "hq")
if HQ not in sys.path: sys.path.insert(0, HQ)
import geom as G  # noqa: E402  (dimensions, profile, nose maths)

pi = math.pi
TEX_DIR = os.path.join(HQ, "textures")
EXPORT_DIR = os.path.join(HQ, "export_roblox")
S_Y = Matrix.Scale(-1.0, 4, (0.0, 1.0, 0.0))          # mirror across the XZ plane (left <-> right)


# ------------------------------------------------------------------ collections / objects
def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c

def remove(name):
    ob = bpy.data.objects.get(name)
    if ob is None: return
    data = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if data is not None and data.users == 0:
        for blk in (bpy.data.meshes, bpy.data.curves, bpy.data.lights):
            if data.name in blk and blk[data.name] == data:
                blk.remove(data); break

def remove_prefix(prefix):
    for ob in [o for o in bpy.data.objects if o.name.startswith(prefix)]: remove(ob.name)

def mk(name, verts, faces, mats, collection, smooth=True, face_mats=None):
    remove(name)
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.validate(); me.update()
    for m in mats: me.materials.append(m)
    if face_mats:
        for p, mi in zip(me.polygons, face_mats): p.material_index = mi
    if smooth:
        for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); collection.objects.link(ob)
    return ob

def empty(name, collection, loc=(0, 0, 0), size=0.1, kind="PLAIN_AXES"):
    remove(name)
    ob = bpy.data.objects.new(name, None); ob.empty_display_type = kind; ob.empty_display_size = size
    ob.location = loc; collection.objects.link(ob); return ob

def activate(ob):
    for o in bpy.context.selected_objects: o.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob

def recalc_normals(ob, outward_ref=None):
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()

def flip_if(ob, test):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.normal_update()
    for f in bm.faces:
        if test(f): f.normal_flip()
    bm.to_mesh(ob.data); bm.free()


# ------------------------------------------------------------------ materials
def _bsdf(m):
    m.use_nodes = True
    return m.node_tree.nodes.get("Principled BSDF")

def mat_pbr(name, rgb, rough=0.4, metal=0.0, coat=0.0, emit=0.0, alpha=None, spec=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    b = _bsdf(m)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if "Coat Weight" in b.inputs: b.inputs["Coat Weight"].default_value = coat
    if "Coat Roughness" in b.inputs: b.inputs["Coat Roughness"].default_value = 0.04
    if "Specular IOR Level" in b.inputs: b.inputs["Specular IOR Level"].default_value = spec
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1); b.inputs["Emission Strength"].default_value = emit
    if alpha is not None:
        b.inputs["Alpha"].default_value = alpha
        for a, v in (("surface_render_method", "BLENDED"), ("use_transparency_overlap", False), ("use_backface_culling", False)):
            try: setattr(m, a, v)
            except Exception: pass
    m.diffuse_color = (*rgb, 1 if alpha is None else alpha)
    return m

def mat(name):
    return bpy.data.materials.get(name)


# ------------------------------------------------------------------ modifiers (all non-destructive)
def mod_subsurf(ob, levels=1, render=1):
    md = ob.modifiers.new("Subdivision", "SUBSURF"); md.levels = levels; md.render_levels = render; md.quality = 3
    try: md.boundary_smooth = "PRESERVE_CORNERS"
    except Exception: pass
    return md

def mod_solidify(ob, t, inner=None, rim=None, use_rim=True):
    md = ob.modifiers.new("Solidify", "SOLIDIFY"); md.thickness = t; md.offset = -1.0; md.use_even_offset = True; md.use_rim = use_rim
    if inner is not None: md.material_offset = inner
    if rim is not None: md.material_offset_rim = rim
    return md

def mod_boolean_collection(ob, collection, name="Cutters"):
    md = ob.modifiers.new(name, "BOOLEAN"); md.operation = "DIFFERENCE"; md.operand_type = "COLLECTION"; md.collection = collection
    md.solver = "EXACT"
    try: md.material_mode = "TRANSFER"
    except Exception: pass
    return md

def mod_smooth_by_angle(ob, deg=35.0):
    """Blender 4.1+: 'Smooth by Angle' node-group modifier (non-destructive)."""
    activate(ob)
    try:
        bpy.ops.object.shade_auto_smooth(use_auto_smooth=True, angle=math.radians(deg))
    except TypeError:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(deg))
    except Exception:
        bpy.ops.object.shade_smooth()

def mod_weighted_normal(ob, weight=50):
    md = ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL"); md.weight = weight; md.keep_sharp = True; md.mode = "FACE_AREA"
    return md


# ------------------------------------------------------------------ ray casting against an evaluated object (world space)
class Caster:
    def __init__(self, ob):
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg); me = ev.to_mesh()
        bm = bmesh.new(); bm.from_mesh(me); bm.transform(ob.matrix_world); bm.normal_update()
        self.tree = BVHTree.FromBMesh(bm); bm.free(); ev.to_mesh_clear()
    def cast(self, o, d):
        d = Vector(d).normalized(); loc, nor, idx, dist = self.tree.ray_cast(Vector(o), d)
        if loc is None: return None, None
        if nor.dot(d) > 0: nor = -nor
        return loc, nor
    def on_face(self, y, z, off=0.0):
        l, n = self.cast((14.0, y, z), (-1, 0, 0))
        return tuple(l + n * off) if l is not None else (G.x_face(z), y, z)


# ------------------------------------------------------------------ custom properties + drivers
def prop(ob, key, val, mn=None, mx=None, desc="", subtype=None):
    ob[key] = val
    ui = ob.id_properties_ui(key)
    kw = {"description": desc}
    if mn is not None: kw["min"] = mn; kw["soft_min"] = mn
    if mx is not None: kw["max"] = mx; kw["soft_max"] = mx
    if subtype: kw["subtype"] = subtype
    try: ui.update(**kw)
    except Exception: pass

def drive(target, path, index, expr, variables):
    """variables: [(var_name, id, data_path)]"""
    fc = target.driver_add(path, index) if index is not None and index >= 0 else target.driver_add(path)
    d = fc.driver; d.type = "SCRIPTED"; d.expression = expr
    for v in list(d.variables): d.variables.remove(v)
    for vn, idb, dp in variables:
        var = d.variables.new(); var.name = vn; var.type = "SINGLE_PROP"
        var.targets[0].id_type = "OBJECT" if isinstance(idb, bpy.types.Object) else "MATERIAL" if isinstance(idb, bpy.types.Material) else var.targets[0].id_type
        var.targets[0].id = idb; var.targets[0].data_path = dp
    return fc

def mirror_parent(collection):
    """Empty with scale Y = -1. Children copy the transform of their left-hand twin through drivers -> exact symmetry."""
    ob = bpy.data.objects.get("CC_MirrorY")
    if ob is None:
        ob = bpy.data.objects.new("CC_MirrorY", None); ob.empty_display_size = 0.2; collection.objects.link(ob)
    ob.location = (0, 0, 0); ob.rotation_euler = (0, 0, 0); ob.scale = (1, -1, 1)
    return ob

def mirror_twin(left, right, mirror):
    """right becomes a child of the mirror empty and copies left's world transform (local == left world)."""
    right.parent = mirror; right.matrix_parent_inverse = Matrix.Identity(4)
    for i in range(3):
        drive(right, "location", i, "v", [("v", left, f"location[{i}]")])
        drive(right, "rotation_euler", i, "v", [("v", left, f"rotation_euler[{i}]")])
        drive(right, "scale", i, "v", [("v", left, f"scale[{i}]")])

def frame_front(origin_x=12.0):
    """object frame for front projection: local X = world +Y, local Y = world +Z, local Z = world +X (rays along local -Z)."""
    m = Matrix(((0, 0, 1, origin_x), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    return m

def frame_side_left(origin_y=2.6):
    """side projection for the left (+Y) side: local X = world -X, local Y = world +Z, local Z = world +Y."""
    return Matrix(((-1, 0, 0, 0), (0, 0, 1, origin_y), (0, 1, 0, 0), (0, 0, 0, 1)))

def tri_count(obs):
    dg = bpy.context.evaluated_depsgraph_get(); tot = 0
    for o in obs:
        if o.type not in ("MESH", "CURVE", "FONT"): continue
        ev = o.evaluated_get(dg)
        try: me = ev.to_mesh()
        except Exception: continue
        if me is None: continue
        me.calc_loop_triangles(); tot += len(me.loop_triangles); ev.to_mesh_clear()
    return tot


def set_gn_input(md, identifier, value):
    """Geometry-Nodes modifier input (Blender 5.x: md.properties.inputs.<id>.value, older: md[id])."""
    try:
        getattr(md.properties.inputs, identifier).value = value; return
    except AttributeError:
        pass
    md[identifier] = value

def get_gn_input(md, identifier):
    try: return getattr(md.properties.inputs, identifier).value
    except AttributeError: return md[identifier]
