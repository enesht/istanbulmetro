"""Rev 6 - control rig. One empty, CC_Controls, carries every animatable switch as a custom property;
drivers connect them to the doors, cab doors, bogies, wheelsets and all light sources.
Hierarchy:  CC_Bogie_F_Pivot / CC_Bogie_R_Pivot  ->  CC_Wheelset_<F|R><1|2>_Pivot  ->  CC_B<F|R>_Wheelset<n> (spins)"""
import bpy, math
from mathutils import Vector, Matrix
from common import G, coll, empty, prop, drive, mat

PROPS = {
    "doors_left_open":      (0.0, 0.0, 1.0, "saloon doors, left side (+Y): 0 closed .. 1 open"),
    "doors_right_open":     (0.0, 0.0, 1.0, "saloon doors, right side (-Y)"),
    "cab_door_left_open":   (0.0, 0.0, 1.0, "hinged cab door, left"),
    "cab_door_right_open":  (0.0, 0.0, 1.0, "hinged cab door, right"),
    "cab_door_max_deg":     (95.0, 0.0, 120.0, "cab door opening angle at 1.0"),
    "wheel_rotation_deg":   (0.0, -1e6, 1e6, "wheel spin angle (animate this)"),
    "bogie_front_yaw_deg":  (0.0, -15.0, 15.0, "front bogie yaw"),
    "bogie_rear_yaw_deg":   (0.0, -15.0, 15.0, "rear bogie yaw"),
    "headlights":           (1.0, 0.0, 1.0, "white head lamps"),
    "drl":                  (1.0, 0.0, 1.0, "daytime running light rings"),
    "taillights":           (0.0, 0.0, 1.0, "red tail lamps"),
    "saloon_lights":        (1.0, 0.0, 1.0, "interior lighting"),
    "destination_display":  (1.0, 0.0, 1.0, "front and side LED displays"),
}

def _ctrl():
    c = coll("CC_Controls")
    ob = bpy.data.objects.get("CC_Controls") or empty("CC_Controls", c, (0, 0, 4.6), 0.4, "SPHERE")
    for k, (v, mn, mx, d) in PROPS.items():
        if k not in ob.keys(): prop(ob, k, v, mn, mx, d)
    return ob

def _reparent_keep(child, parent):
    bpy.context.view_layer.update()            # parent.matrix_world must be current (fresh empties are identity until updated)
    mw = child.matrix_world.copy(); child.parent = parent; child.matrix_parent_inverse = parent.matrix_world.inverted(); child.matrix_basis = Matrix.Identity(4)
    child.matrix_world = mw

def repair_parent_inverses(parents=("CC_Coupler", "CC_Bogie_F_Pivot", "CC_Bogie_R_Pivot")):
    """one-off fix for rigs parented before the depsgraph update: assumes matrix_basis holds the intended world matrix."""
    fixed = 0
    def walk(p):
        nonlocal fixed
        bpy.context.view_layer.update()
        for ch in p.children:
            ch.matrix_parent_inverse = p.matrix_world.inverted(); fixed += 1
        bpy.context.view_layer.update()
        for ch in p.children:
            if ch.type == "EMPTY": walk(ch)
    for n in parents:
        o = bpy.data.objects.get(n)
        if o: walk(o)
    return fixed

def _move_origin(ob, new_origin):
    """move the object origin (mesh data shifted) without moving geometry or children."""
    old = ob.matrix_world.copy(); d = Vector(new_origin) - old.translation
    ob.data.transform(Matrix.Translation(-d)); ob.location = ob.location + d
    for ch in ob.children: ch.matrix_parent_inverse = Matrix.Translation(-d) @ ch.matrix_parent_inverse

def doors(ctrl):
    n = 0
    for o in bpy.data.objects:
        if not o.name.startswith("CC_Door_") or o.type != "MESH" or "slide_dir" not in o.keys(): continue
        side = "left" if "_L" in o.name[7:9] else "right"
        o.delta_location = (0, 0, 0)
        drive(o, "delta_location", 0, "d * m * k", [("k", ctrl, f'["doors_{side}_open"]'), ("d", o, '["slide_dir"]'), ("m", o, '["slide_m"]')]); n += 1
    for S, sgn in (("L", 1), ("R", -1)):
        o = bpy.data.objects.get(f"CC_CabSideDoor_{S}")
        if o is None: continue
        x0 = G.CAB_DOOR[0]; hinge = (x0 + 0.01, sgn * 1.50, 0.5 * (G.CAB_DOOR[2] + G.CAB_DOOR[3]))
        if (o.matrix_world.translation - Vector(hinge)).length > 1e-3: _move_origin(o, hinge)
        side = "left" if S == "L" else "right"
        drive(o, "rotation_euler", 2, f"{sgn} * k * radians(a)", [("k", ctrl, f'["cab_door_{side}_open"]'), ("a", ctrl, '["cab_door_max_deg"]')])
        n += 1
    return n

def bogies(ctrl):
    out = []
    for tag, cname, bx, key in (("F", "CabCar_Bogie_F", G.BOGIE_X[0], "bogie_front_yaw_deg"), ("R", "CabCar_Bogie_R", G.BOGIE_X[1], "bogie_rear_yaw_deg")):
        c = bpy.data.collections.get(cname)
        if c is None: continue
        piv = bpy.data.objects.get(f"CC_Bogie_{tag}_Pivot") or empty(f"CC_Bogie_{tag}_Pivot", c, (bx, 0, 0.75), 0.6, "SINGLE_ARROW")
        drive(piv, "rotation_euler", 2, "radians(a)", [("a", ctrl, f'["{key}"]')])
        wsets = sorted([o for o in c.objects if o.name.startswith(f"CC_B{tag}_Wheelset")], key=lambda o: o.name)
        for k, ws in enumerate(wsets):
            ws_ = [ws.matrix_world @ v.co for v in ws.data.vertices]
            ctr = Vector((sum(p.x for p in ws_) / len(ws_), 0.0, 0.5 * (min(p.z for p in ws_) + max(p.z for p in ws_))))
            wp = bpy.data.objects.get(f"CC_Wheelset_{tag}{k + 1}_Pivot") or empty(f"CC_Wheelset_{tag}{k + 1}_Pivot", c, ctr, 0.5, "PLAIN_AXES")
            wp.rotation_euler = (0, 0, 0); wp.location = ctr
            if wp.parent != piv: _reparent_keep(wp, piv)
            if (ws.matrix_world.translation - ctr).length > 1e-3: _move_origin(ws, ctr)
            if ws.parent != wp: _reparent_keep(ws, wp)
            drive(ws, "rotation_euler", 1, "radians(a)", [("a", ctrl, '["wheel_rotation_deg"]')])
            for o in c.objects:          # axle boxes / gearboxes ride with the wheelset but do not spin
                if o.parent is None and (o.name.startswith(f"CC_B{tag}_AxleBox{k + 1}") or o.name.startswith(f"CC_B{tag}_Gearbox{k + 1}")): _reparent_keep(o, wp)
        for o in list(c.objects):
            if o.parent is None and o != piv: _reparent_keep(o, piv)
        out.append((piv.name, len(c.objects)))
    return out

def _emit_driver(mname, base, key, ctrl):
    m = mat(mname)
    if m is None: return 0
    b = m.node_tree.nodes.get("Principled BSDF")
    if b is None: return 0
    sock = b.inputs["Emission Strength"]
    try: sock.driver_remove("default_value")
    except Exception: pass
    drive(sock, "default_value", None, f"{base} * k", [("k", ctrl, f'["{key}"]')]); m["emission_base"] = base
    return 1

def lights(ctrl):
    n = 0
    for mname, base, key in (("LAMP_Head_Emitter", 6.0, "headlights"), ("LAMP_DRL_Emitter", 2.5, "drl"), ("LAMP_Tail_Emitter", 3.0, "taillights"),
                             ("LED_DotMatrix_Orange", 3.0, "destination_display"), ("PBR_LEDMatrix", 2.2, "destination_display")):
        n += _emit_driver(mname, base, key, ctrl)
    rig = bpy.data.objects.get("CC_LampRig")
    for lname, key, pkey in (("CC_HeadLamp_L_Light", "headlights", "head_light_w"), ("CC_TailLamp_L_Light", "taillights", "tail_light_w")):
        ld = bpy.data.lights.get(lname)
        if ld and rig:
            drive(ld, "energy", None, "w * k", [("k", ctrl, f'["{key}"]'), ("w", rig, f'["{pkey}"]')]); n += 1
    for lname in ("SaloonLight_L", "SaloonLight_R", "CeilingBounce_L", "CeilingBounce_R"):
        lo = bpy.data.objects.get(lname)
        if lo:
            lo.data["energy_base"] = lo.data.get("energy_base", lo.data.energy)
            drive(lo.data, "energy", None, "e * k", [("k", ctrl, '["saloon_lights"]'), ("e", lo, 'data["energy_base"]')]); n += 1
    return n

def build_controls():
    ctrl = _ctrl()
    return {"doors": doors(ctrl), "bogies": bogies(ctrl), "lights": lights(ctrl)}
