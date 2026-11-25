"""Marmaray Rev7 experimental front correction for the supplied Rev6 project.
Run with Blender 5.2, not system Python. Preview does not overwrite the Rev6 blend or PNGs.
"""
import os, sys, math, shutil, argparse, importlib
from pathlib import Path
import bpy

p=argparse.ArgumentParser()
p.add_argument('--bake-export', action='store_true', help='Bake cab atlas and export new FBX/GLB in rev7_output')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
source=Path(bpy.data.filepath).resolve()
HQ=source.parent
if not (HQ/'rev6'/'livery.py').is_file():
    HQ=HQ.parent
if not (HQ/'rev6'/'livery.py').is_file():
    raise RuntimeError('Open blender/hq/cab_car_master.blend first')
sys.path.insert(0,str(HQ/'rev6')); sys.path.insert(0,str(HQ))
import common, livery, lamps, controls, atlas, export_roblox
for mod in (livery, lamps, controls, atlas, export_roblox): importlib.reload(mod)

# These are visually estimated art parameters, NOT verified manufacturer dimensions.
MASK_CENTER=2.86
MASK_HALF_HEIGHT=0.96
MASK_HALF_WIDTH=1.20
MASK_EXP=2.8
RED_Z_LOW=1.20
RED_Z_HIGH=3.77
LAMP_PARAMS=dict(pod_angle_deg=22.0,pod_center_y=1.06,pod_center_z=1.48,
                 pod_length=0.67,pod_height=0.31,pod_tilt_deg=36.0,pod_corner_r=0.045,
                 head_u=0.15,head_w=0.0,tail_u=-0.17,tail_w=0.0,
                 head_radius=0.078,tail_radius=0.048,pod_depth=0.040)

required=['CC_Cab_Body','CC_Ref_Exterior','CC_LampRig','CC_Windscreen_Glass','CC_Controls']
for name in required:
    if bpy.data.objects.get(name) is None: raise RuntimeError('Missing Rev6 object: '+name)
if bpy.context.object and bpy.context.object.mode!='OBJECT': bpy.ops.object.mode_set(mode='OBJECT')

# Disable the old projected paint surfaces, including their crown artifacts. The
# replacement is a shader mask on the actual cab surface, not floating triangles.
for o in list(bpy.data.objects):
    if o.name.startswith(('CC_Paint_Crown','CC_Paint_Mask')):
        common.remove(o.name)

# Retain existing body atlas. Rebuild only the procedural source and add
# continuous cab masks in world metres, so the color follows curved surfaces.
m=livery.procedural_livery(); nt=m.node_tree; B=livery._NB(nt)
b=nt.nodes.get('Principled BSDF')
geo=B._n('ShaderNodeNewGeometry'); sep=B._n('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Position'],sep.inputs[0])
x,y,z=sep.outputs[:3]; ay=B.m('ABSOLUTE',y)
def add(a,c): return B.m('ADD',a,c)
def sub(a,c): return B.m('SUBTRACT',a,c)
def mul(a,c): return B.m('MULTIPLY',a,c)
def mx(a,c): return B.m('MAXIMUM',a,c)
def mn(a,c): return B.m('MINIMUM',a,c)
def one(a): return sub(1.0,a)
def edge(a): return B.edge(a,0.003)
def band(a,lo,hi): return mul(edge(sub(a,lo)),edge(sub(hi,a)))
def pow_(a,c): return B.m('POWER',a,c)
def abs_(a): return B.m('ABSOLUTE',a)
# Smooth front envelope: follows the rake instead of painting the entire roof.
front_min=sub(10.29,mul(0.40,mx(sub(z,2.20),0.0)))
front=edge(sub(x,front_min))
# Reset inherited horizontal bands on the front, keep them at the side seam.
front_reset=edge(sub(x,sub(10.42,mul(0.40,mx(sub(z,2.20),0.0)))))
# Black oval with lower sweep and broad upper area. Width is tapered toward bottom.
q=abs_(mul(sub(z,MASK_CENTER),1.0/MASK_HALF_HEIGHT))
width=add(MASK_HALF_WIDTH,mul(0.085,sub(z,MASK_CENTER)))
q2=pow_(q,MASK_EXP)
rad=pow_(mx(sub(1.0,q2),0.0),1.0/MASK_EXP)
half=mul(width,rad)
black=mul(front,mul(edge(sub(half,ay)),edge(sub(1.0,q))))
# Vertical red wings wrap the shoulder and sweep inward towards the low lamps.
# Lower and upper boundaries are independent from the old horizontal body stripe.
inner=B.lerp(0.70,1.11,B.ss(1.35,2.15,z))
inner=mx(inner,mul(add(half,0.055),B.ss(1.92,2.20,z)))
outer=B.lerp(1.21,1.46,B.ss(1.20,2.02,z))
outer=B.lerp(outer,1.26,B.ss(3.45,3.77,z))
wing_x=sub(10.20,mul(0.25,mx(sub(z,2.1),0.0)))
wing=mul(band(z,RED_Z_LOW,RED_Z_HIGH),mul(band(ay,inner,outer),edge(sub(x,wing_x))))
# Two narrow curved accents under the black mask, split left and right.
arc_z=add(1.89,mul(0.24,pow_(mul(ay,1.0/1.18),2.0)))
arc=mul(front,mul(edge(sub(0.94,ay)),edge(sub(0.026,abs_(sub(z,arc_z))))))
side=edge(y)
# Preserve existing PBR shader channels and layer the new paint on top.
channels={}
for name in ('Base Color','Metallic','Roughness','Coat Weight','Specular IOR Level'):
    s=b.inputs[name]; channels[name]=s.links[0].from_socket if s.is_linked else (tuple(s.default_value) if name=='Base Color' else s.default_value)
def paint(mask, rgb, rough, metallic=0.0, coat=.35):
    channels['Base Color']=B.cmix(channels['Base Color'],rgb,mask)
    for name,value in [('Metallic',metallic),('Roughness',rough),('Coat Weight',coat),('Specular IOR Level',.40)]:
        channels[name]=B.lerp(channels[name],value,mask)
paint(front_reset,livery.PAL['WHITE'],.27)
paint(wing,livery.PAL['RED'],.30)
paint(black,livery.PAL['BLACK'],.18,0,.65)
paint(mul(arc,side),livery.PAL['RED'],.30)
paint(mul(arc,one(side)),livery.PAL['NAVY'],.30)
for name,value in channels.items(): nt.links.new(value,b.inputs[name])
# The existing body and doors retain their baked materials. Only cab slot 0 changes.
cab=bpy.data.objects['CC_Cab_Body']; cab.data.materials[0]=m

# Rounded tapered pod: larger outer end for white headlamp, smaller inner end
# for red marker. Keep identical point count at every cutter ring.
def tapered_outline(self,scale=1.0):
    L=lamps.P(self.r,'pod_length'); h=lamps.P(self.r,'pod_height')
    corners=[(-L/2,-h*.26),(L/2,-h*.48),(L/2,h*.50),(-L/2,h*.20)]
    points=[]
    for i,c in enumerate(corners):
        prev=corners[i-1]; nxt=corners[(i+1)%4]
        # quadratic rounded corner, followed by straight edge
        a=tuple(c[j]+.15*(prev[j]-c[j]) for j in (0,1)); d=tuple(c[j]+.15*(nxt[j]-c[j]) for j in (0,1))
        for k in range(9):
            t=k/8; points.append(tuple((1-t)**2*a[j]+2*t*(1-t)*c[j]+t*t*d[j] for j in (0,1)))
    return [(u*scale,(w+u*self.shear)*scale) for u,w in lamps.resample(points)]
lamps.Pod.outline=tapered_outline
rig=lamps.rig()
for k,v in LAMP_PARAMS.items(): rig[k]=v
lamps.rebuild_lamps()
controls.lights(bpy.data.objects['CC_Controls'])
bpy.context.view_layer.update()

# Save new file only. Original Rev6 blend, body texture and exports stay untouched.
preview=HQ/'cab_car_rev7_preview.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(preview))
print('REV7 PREVIEW SAVED:',preview)

if args.bake_export:
    out=HQ/'rev7_output'; tex=out/'textures'; exp=out/'export_roblox'
    tex.mkdir(parents=True,exist_ok=True); exp.mkdir(parents=True,exist_ok=True)
    for f in (HQ/'textures').glob('*'):
        if f.is_file(): shutil.copy2(f,tex/f.name)
    # Switch the save base BEFORE baking, so relative PNG paths are correct.
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'cab_car_rev7.blend'))
    atlas.TEX_DIR=str(tex); export_roblox.TEX_DIR=str(tex); export_roblox.EXPORT_DIR=str(exp)
    # Do not call run_all/rebake: that would regenerate the unchanged body atlas.
    atlas.bake_set('cab')
    mc=atlas.atlas_material('MAT_Cab_Atlas','T_Cab','UV_CabAtlas')
    atlas.assign_atlas(atlas.cab_objects(),mc)
    # Point both body and cab images at the copied output resources.
    for im in bpy.data.images:
        if im.name.startswith(('T_Body_','T_Cab_')):
            f=tex/(im.name+'.png')
            if f.is_file():
                im.filepath_raw=bpy.path.relpath(str(f))
                if im.packed_file: im.unpack(method='REMOVE')
                im.reload(); im.pack()
    sc=bpy.context.scene
    try: sc.render.engine='BLENDER_EEVEE'
    except Exception: pass
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'cab_car_rev7.blend'))
    print('REV7 EXPORT:',export_roblox.export_all('Marmaray_CabCar_Rev7'))
