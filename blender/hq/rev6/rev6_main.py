"""Rev 6 driver. Run inside Blender with cab_car_master.blend open:
    import sys, importlib, os, bpy
    p = os.path.join(os.path.dirname(bpy.data.filepath), "rev6")   # master .blend'in yanindaki rev6 klasoru
    sys.path.insert(0, p); import rev6_main; importlib.reload(rev6_main); rev6_main.run(["geometry", "lamps", "paint"])
Steps: geometry, lamps, paint, atlas, controls, export (see README_REV6.md)."""
import importlib, time
import common, cab_geometry, livery, lamps
for _m in (common, cab_geometry, livery, lamps): importlib.reload(_m)

def step_geometry():
    cab_geometry.remove_rev5_front()
    livery.procedural_livery()
    cab_geometry.build_shells()
    cab_geometry.front_glazing()
    cab_geometry.bumper_and_coupler()

def step_lamps():
    lamps.rebuild_lamps()

def step_paint():
    livery.build_paint()
    livery.build_destination_display()

def step_atlas():
    import atlas; importlib.reload(atlas); atlas.run_all()

def step_controls():
    import controls; importlib.reload(controls); controls.build_controls()

def step_export():
    import export_roblox; importlib.reload(export_roblox); return export_roblox.export_all()

STEPS = {"geometry": step_geometry, "lamps": step_lamps, "paint": step_paint, "atlas": step_atlas, "controls": step_controls, "export": step_export}

def run(steps):
    out = {}
    for s in steps:
        t0 = time.time(); r = STEPS[s](); out[s] = (round(time.time() - t0, 1), r)
        print("rev6 step", s, out[s][0], "s")
    return out
