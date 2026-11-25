"""Marmaray istasyon modelleme - ortak (yeniden kullanilabilir) assetler.

refs/ASSET_LIST.md'deki "ortak assetler" bolumunun karsiligi. Her uretici
fonksiyon tek bir koleksiyon dondurur ve istasyon modullerinden cagrilir.

Olcu etiketleri:
    PV = fotograftan turetildi (refs/ARCHITECTURAL_ANALYSIS.md)
    AS = fotografta yok, varsayim - referans gelince duzeltilmeli
"""

import bpy
from common import (box, slab, cylinder, bevel, array_y, collection, put,
                   material, assign, PLATFORM_TOP, GAUGE)

# --------------------------------------------------------------------------- malzemeler
def materials():
    """Hat genelinde paylasilan malzeme seti."""
    M = {}
    # Not: degerler LINEER (sRGB degil). Fotograftaki "acik gri granit" sRGB ~0.72
    # demek lineer ~0.48; dolayisiyla 0.34 fazla koyuydu.
    # PV: cilali acik gri benekli granit - tavan isiklari zeminde yansiyor
    M["floor_granite"] = material("MAT_Floor_GraniteGrey", (0.50, 0.50, 0.51),
                                  roughness=0.16, specular=0.65)
    # PV: sicak bej / sutlu kahve buyuk format mat seramik
    M["tile_beige"] = material("MAT_Tile_WarmBeige", (0.62, 0.53, 0.41),
                               roughness=0.42)
    # PV: ray tarafi ham puskurtme beton, koyu gri-siyah
    M["concrete_raw"] = material("MAT_Concrete_RawDark", (0.045, 0.045, 0.048),
                                 roughness=0.93)
    M["concrete_pale"] = material("MAT_Concrete_Pale", (0.38, 0.375, 0.365),
                                  roughness=0.85)
    # REFERANS: ray tarafi alinlik bandi - acik gri-bej duz panel
    M["fascia_grey"] = material("MAT_Fascia_PaleGrey", (0.47, 0.465, 0.45),
                                roughness=0.48)
    # REFERANS: mural BAKIR/TERRAKOTA tonlu seramik rolyef (turkuaz DEGIL -
    # turkuaz olan yalnizca peron kenarindaki grafik bant)
    M["mural_copper"] = material("MAT_Mural_Copper", (0.34, 0.145, 0.055),
                                 roughness=0.52, metallic=0.15)
    M["mural_copper_dk"] = material("MAT_Mural_CopperDeep", (0.19, 0.075, 0.028),
                                    roughness=0.60, metallic=0.10)
    M["mural_frame"] = material("MAT_Mural_Frame", (0.035, 0.032, 0.030),
                                roughness=0.55)
    # PV: peron kenari bantlari
    M["band_white"] = material("MAT_Band_EdgeWhite", (0.84, 0.84, 0.82), roughness=0.32)
    M["band_tactile"] = material("MAT_Band_TactileYellow", (0.80, 0.56, 0.03), roughness=0.55)
    M["band_turquoise"] = material("MAT_Band_IznikTurquoise", (0.05, 0.38, 0.40), roughness=0.28)
    M["band_orange"] = material("MAT_Band_WarnOrange", (0.85, 0.28, 0.02), roughness=0.45)
    # metaller
    # REFERANS: lameller MAT gri-antrasit bicaklar; ayna gibi metalik degil.
    M["metal_baffle"] = material("MAT_Metal_BaffleGrey", (0.115, 0.118, 0.122),
                                 roughness=0.62, metallic=0.25)
    M["metal_galv"] = material("MAT_Metal_Galvanised", (0.42, 0.43, 0.44),
                               roughness=0.38, metallic=0.9)
    M["steel_rail"] = material("MAT_Steel_RailHead", (0.26, 0.25, 0.24),
                               roughness=0.28, metallic=1.0)
    M["steel_dark"] = material("MAT_Steel_Dark", (0.08, 0.08, 0.085),
                               roughness=0.5, metallic=0.9)
    # isik yuzeyleri
    M["light_panel"] = material("MAT_Light_Panel", (1.0, 0.97, 0.92), roughness=0.1,
                                emission=(1.0, 0.96, 0.90), emission_strength=7.0)
    M["light_strip"] = material("MAT_Light_Strip", (1.0, 0.96, 0.90), roughness=0.1,
                                emission=(1.0, 0.95, 0.88), emission_strength=11.0)
    # donati
    M["sign_white"] = material("MAT_Sign_White", (0.80, 0.80, 0.79), roughness=0.3)
    M["sign_dark"] = material("MAT_Sign_DarkBand", (0.045, 0.045, 0.05), roughness=0.4)
    M["emergency_red"] = material("MAT_Emergency_Red", (0.52, 0.02, 0.02), roughness=0.4)
    M["emergency_yellow"] = material("MAT_Emergency_Yellow", (0.70, 0.50, 0.02), roughness=0.45)
    M["ballast"] = material("MAT_Ballast_Grey", (0.11, 0.108, 0.105), roughness=0.95)
    M["sleeper"] = material("MAT_Sleeper_Concrete", (0.20, 0.195, 0.185), roughness=0.88)
    M["screen_black"] = material("MAT_Screen_Black", (0.012, 0.012, 0.014),
                                 roughness=0.22)
    # REFERANS: zemin ve duvar gercekte BELIRGIN DERZ izgarali. Duz renk
    # yerine prosedurel derz: binlerce karoyu geometri olarak gecirmeden
    # hem renk hem kabartma farki verir.
    M["floor_tiled"] = tile_material("MAT_Floor_GraniteTiled",
                                     (0.52, 0.52, 0.53),
                                     grout=(0.26, 0.26, 0.265),
                                     tile=(0.60, 0.60), roughness=0.26,
                                     mortar=0.010, bump=0.0018)
    M["wall_tiled"] = tile_material("MAT_Wall_BeigeTiled",
                                    (0.66, 0.57, 0.45),
                                    grout=(0.085, 0.072, 0.058),
                                    tile=(0.60, 0.90), roughness=0.38,
                                    mortar=0.014, bump=0.0028)
    return M


# --------------------------------------------------------------------------- peron kenari
#: PV - rayin kenarindan iceri dogru bant sirasi ve genislikleri (m).
#: Zemin karosu ~0.60 m (yetiskin ayakkabisinin 2-2.5 kati) ve taktil bant
#: "yaklasik 1 karo", turkuaz bant "taktil ile esit" olarak olculdu.
EDGE_BANDS = [
    ("EdgeWhite",      0.15, "band_white"),
    ("Tactile",        0.60, "band_tactile"),
    ("GraphicTurkuaz", 0.60, "band_turquoise"),
    ("WarnOrange",     0.10, "band_orange"),
]
EDGE_BAND_TOTAL = sum(w for _, w, _ in EDGE_BANDS)   # 1.45 m


def platform_edge_bands(col, M, x_edge, y0, y1, inward=+1, z_top=PLATFORM_TOP,
                        prefix="Edge"):
    """Peron kenarinin katmanli bant kompozisyonu.

    x_edge : peron kenarinin X'i (ray tarafi)
    inward : +1 ise bantlar +X yonune dogru dizilir
    Bantlar zemin karosunun 2 mm ustune oturur (kabartma taktil okunsun diye).
    """
    out = []
    x = x_edge
    for name, w, matkey in EDGE_BANDS:
        x2 = x + inward * w
        # taktil bant hafifce kabarik (PV: "kabartma noktali")
        lift = 0.006 if matkey == "band_tactile" else 0.002
        o = slab(f"{prefix}_{name}", min(x, x2), max(x, x2), y0, y1,
                 z_top, z_top + lift, col, M[matkey])
        out.append(o)
        x = x2
    return out


# --------------------------------------------------------------------------- tavan
def tile_material(name, base, grout=(0.055, 0.05, 0.045), tile=(0.60, 0.60),
                  roughness=0.40, mortar=0.012, bump=0.0022):
    """Derzli buyuk format karo - prosedurel.

    Zemin/duvar gibi binlerce karo iceren yuzeylerde her karoyu ayri gecirmek
    yuz binlerce poligon demek; derz Brick Texture ile hem renge hem bump'a
    baglanir. Kameraya yakin ogelerde (kolon) ayrica GERCEK geometri derzi
    kullanilir - bkz. tiled_box().
    """
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")

    tex = nt.nodes.new("ShaderNodeTexBrick")
    tex.location = (-620, 0)
    tex.offset = 0.0              # kaydirmasiz duz izgara (PV: duz dizilim)
    tex.offset_frequency = 2
    tex.squash = 1.0
    tex.inputs["Color1"].default_value = (*base, 1.0)
    tex.inputs["Color2"].default_value = (*[c * 0.94 for c in base], 1.0)
    tex.inputs["Mortar"].default_value = (*grout, 1.0)
    tex.inputs["Scale"].default_value = 1.0
    tex.inputs["Mortar Size"].default_value = mortar
    tex.inputs["Mortar Smooth"].default_value = 0.08
    tex.inputs["Bias"].default_value = 0.0
    tex.inputs["Brick Width"].default_value = tile[0]
    tex.inputs["Row Height"].default_value = tile[1]

    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (-980, 0)
    nt.links.new(tex.inputs["Vector"], coord.outputs["Object"])
    nt.links.new(bsdf.inputs["Base Color"], tex.outputs["Color"])

    # derz cukurlugu: Fac -> Bump
    bmp = nt.nodes.new("ShaderNodeBump")
    bmp.location = (-300, -220)
    bmp.inputs["Strength"].default_value = 1.0
    bmp.inputs["Distance"].default_value = bump
    nt.links.new(bmp.inputs["Height"], tex.outputs["Fac"])
    nt.links.new(bsdf.inputs["Normal"], bmp.outputs["Normal"])

    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = roughness
    return mat


def tiled_box(name, x0, x1, y0, y1, z0, z1, col, mat_tile, mat_grout,
              tile=(0.60, 0.90), reveal=0.006, prefix=None):
    """Kameraya yakin yuzeyler icin GERCEK geometri derzi olan karo kaplama.

    Koyu bir govde (derz rengi) + govdeden `reveal` kadar disari tasan karo
    plakalari. Gercek golge ve kenar isigi verir; prosedurel bump veremez.
    Dort dusey yuze (X-, X+, Y-, Y+) karo doser.
    """
    body = slab(f"{name}_Body", x0, x1, y0, y1, z0, z1, col, mat_grout)
    tw, th = tile
    nz = max(1, int(round((z1 - z0) / th)))
    th_act = (z1 - z0) / nz
    out = [body]
    for axis, (a0, a1, const, face) in (
            ("X-", (y0, y1, x0, -1)), ("X+", (y0, y1, x1, +1)),
            ("Y-", (x0, x1, y0, -1)), ("Y+", (x0, x1, y1, +1))):
        span = a1 - a0
        nt_ = max(1, int(round(span / tw)))
        tw_act = span / nt_
        for i in range(nt_):
            for k in range(nz):
                p0 = a0 + i * tw_act + 0.004
                p1 = a0 + (i + 1) * tw_act - 0.004
                q0 = z0 + k * th_act + 0.004
                q1 = z0 + (k + 1) * th_act - 0.004
                if axis.startswith("X"):
                    t = slab(f"{name}_T{axis}_{i:02d}_{k:02d}",
                             const, const + face * reveal, p0, p1, q0, q1,
                             col, mat_tile)
                else:
                    t = slab(f"{name}_T{axis}_{i:02d}_{k:02d}",
                             p0, p1, const, const + face * reveal, q0, q1,
                             col, mat_tile)
                out.append(t)
    return out


def baffle_ceiling(col, M, x0, x1, y0, y1, z, baffle_w=0.10, gap=0.10,
                   depth=0.15, panel_every=9, prefix="Ceil",
                   plenum_depth=0.95, services=True):
    """Lineer metal lamel (bafl) tavan + gomme isikli paneller + servis boslugu.

    REFERANS (kullanicinin verdigi B1 2024 fotografi):
        - Lameller peron aksina DIK, genis duz bicaklar; ARALIK lamel
          genisliginden BUYUK, aralardan ustteki koyu servis boslugu ve
          icindeki kablo tavalari / kanallar / tasiyici profiller GORUNUYOR.
        - Isikli paneller lamel duzleminde, dizi halinde.
    """
    pitch = baffle_w + gap
    n = max(1, int((y1 - y0) / pitch))
    # tek lamel + Array modifier: 1200+ ayri nesne yerine tek mesh
    b = slab(f"{prefix}_Baffle", x0, x1, y0, y0 + baffle_w, z - depth, z,
             col, M["metal_baffle"])
    array_y(b, n, pitch)
    bevel(b, 0.003, 1, harden=False)

    # PV: isikli paneller lamel tavana GOMULU - panelin isik yuzeyi lamel ALT
    # yuzuyle ayni duzlemde olmali, yoksa lamel + plenum arasinda kapali kalir
    # ve asagiya hic isik dusmez.
    # REFERANS: isikli panel tavanin KUCUK bir kismi - cogunlugu gri lamel.
    # Ilk surumde panel orani %57 idi, tavan bembeyaz okunuyordu.
    panels = []
    span = pitch * 3.0
    y = y0 + pitch * 2
    idx = 0
    while y + span < y1:
        p = slab(f"{prefix}_LightPanel_{idx:03d}", x0 + 1.2, x1 - 1.2,
                 y, y + span, z - depth, z - depth + 0.02, col, M["light_panel"])
        panels.append(p)
        y += pitch * panel_every
        idx += 1
    # Servis boslugu: lamellerin COK uzerinde bir strüktürel tavan. Aralardan
    # bakildiginda derinlik okunmali - referansta en belirgin tavan ozelligi bu.
    plenum = slab(f"{prefix}_PlenumSoffit", x0, x1, y0, y1,
                  z + plenum_depth, z + plenum_depth + 0.25,
                  col, M["concrete_raw"])
    svc = []
    if services:
        # enine tasiyici profiller (lamel askilarinin oturdugu)
        beam = slab(f"{prefix}_PlenumBeam", x0, x1, y0, y0 + 0.11,
                    z + plenum_depth - 0.26, z + plenum_depth,
                    col, M["steel_dark"])
        array_y(beam, max(1, int((y1 - y0) / 2.4)), 2.4)
        svc.append(beam)
        # boyuna kablo tavalari (iki hat) + havalandirma kanali
        for i, (xa, xb, zz, mt) in enumerate((
                (x0 + 1.0, x0 + 1.5, z + plenum_depth - 0.40, "metal_galv"),
                (x1 - 1.5, x1 - 1.0, z + plenum_depth - 0.40, "metal_galv"))):
            t = cable_tray(col, M, xa, xb, y0, y1, zz, prefix=f"{prefix}_PlTray{i}")
            svc.append(t["base"])
        duct = slab(f"{prefix}_PlenumDuct", (x0 + x1) / 2 - 0.45, (x0 + x1) / 2 + 0.45,
                    y0, y1, z + plenum_depth - 0.62, z + plenum_depth - 0.18,
                    col, M["metal_galv"])
        svc.append(duct)
        # lamel askilari
        hang = slab(f"{prefix}_Hanger", (x0 + x1) / 2 - 0.02, (x0 + x1) / 2 + 0.02,
                    y0, y0 + 0.04, z, z + plenum_depth - 0.26, col, M["steel_dark"])
        array_y(hang, max(1, int((y1 - y0) / 2.4)), 2.4)
        svc.append(hang)
    return {"baffle": b, "panels": panels, "plenum": plenum, "services": svc,
            "count": n, "pitch": pitch}


def fascia_band(col, M, x0, x1, y0, y1, z_top, height=0.95, mat=None,
                strip=True, prefix="Fascia"):
    """Ray tarafindaki genis duz alinlik (bulkhead) bandi.

    REFERANS: tavan lamelleri ile ray duvari arasinda, peron boyunca uzanan
    genis duz panel; serit armatur onun ALT kenarina monte. Referans fotografta
    tavanin en okunakli ikinci ogesi.
    """
    m = mat or M["concrete_pale"]
    face = slab(f"{prefix}_Panel", x0, x1, y0, y1, z_top - height, z_top, col, m)
    bevel(face, 0.006, 1, harden=False)
    out = {"panel": face}
    if strip:
        out["light"] = strip_light(col, M, x0 + 0.02, x1 - 0.02, y0, y1,
                                   z_top - height - 0.07, housing=0.07,
                                   prefix=f"{prefix}_Strip")
    return out


# --------------------------------------------------------------------------- yol
def ballasted_track(col, M, x_centre, y0, y1, z_railtop=0.0,
                    sleeper_pitch=0.60, prefix="Track"):
    """Istasyon ici balastli yol: balast dolgu + beton travers + ray.

    PV: traversler arasi bosluk, travers genisliginin ~1.5-2 kati
        -> 0.26 m travers + ~0.34 m bosluk = 0.60 m adim (standart ile uyumlu)
    """
    rail_h = 0.172
    sl_h, sl_w, sl_len = 0.20, 0.26, 2.50
    # balast prizmasi
    bal = slab(f"{prefix}_Ballast", x_centre - 1.90, x_centre + 1.90, y0, y1,
               z_railtop - rail_h - sl_h - 0.30, z_railtop - rail_h - sl_h,
               col, M["ballast"])
    # travers (tek + array)
    sl = slab(f"{prefix}_Sleeper", x_centre - sl_len / 2, x_centre + sl_len / 2,
              y0, y0 + sl_w, z_railtop - rail_h - sl_h, z_railtop - rail_h,
              col, M["sleeper"])
    n = max(1, int((y1 - y0) / sleeper_pitch))
    array_y(sl, n, sleeper_pitch)
    bevel(sl, 0.008, 1, harden=False)
    # raylar
    rails = []
    for side, tag in ((-1, "L"), (+1, "R")):
        rx = x_centre + side * GAUGE / 2
        web = slab(f"{prefix}_Rail{tag}", rx - 0.0085, rx + 0.0085, y0, y1,
                   z_railtop - rail_h + 0.03, z_railtop - 0.028, col, M["steel_rail"])
        head = slab(f"{prefix}_RailHead{tag}", rx - 0.0355, rx + 0.0355, y0, y1,
                    z_railtop - 0.028, z_railtop, col, M["steel_rail"])
        foot = slab(f"{prefix}_RailFoot{tag}", rx - 0.075, rx + 0.075, y0, y1,
                    z_railtop - rail_h, z_railtop - rail_h + 0.03, col, M["steel_rail"])
        rails += [web, head, foot]
    return {"ballast": bal, "sleeper": sl, "sleepers": n, "rails": rails}


# --------------------------------------------------------------------------- donati
def strip_light(col, M, x0, x1, y0, y1, z, housing=0.06, prefix="Strip"):
    """Kesintisiz lineer serit armatur (peron kenari kirisi / eser ustu)."""
    h = slab(f"{prefix}_Housing", x0, x1, y0, y1, z, z + housing, col, M["metal_galv"])
    l = slab(f"{prefix}_Lens", x0 + 0.004, x1 - 0.004, y0, y1,
             z - 0.012, z + 0.002, col, M["light_strip"])
    return {"housing": h, "lens": l}


def station_name_sign(col, M, text, x, y, z, face=+1, w=2.40, h=0.52,
                      prefix="Sign"):
    """PV: beyaz zeminli dikdortgen pano, ust kenarinda ince koyu bant,
    siyah buyuk harf sans-serif istasyon adi. Yuzeyden monte."""
    t = 0.035
    plate = slab(f"{prefix}_Plate", x, x + face * t, y - w / 2, y + w / 2,
                 z - h / 2, z + h / 2, col, M["sign_white"])
    band = slab(f"{prefix}_TopBand", x + face * t, x + face * (t + 0.004),
                y - w / 2, y + w / 2, z + h / 2 - 0.055, z + h / 2, col, M["sign_dark"])
    # metin
    cur = bpy.data.curves.new(f"{prefix}_TextData", type="FONT")
    cur.body = text
    cur.align_x = "CENTER"
    cur.align_y = "CENTER"
    cur.size = 0.26
    cur.extrude = 0.004
    obj = bpy.data.objects.new(f"{prefix}_Text", cur)
    obj.rotation_euler = (1.5707963, 0, 1.5707963 * face)
    obj.location = (x + face * (t + 0.006), y, z - 0.02)
    col.objects.link(obj)
    assign(obj, M["sign_dark"])
    return {"plate": plate, "band": band, "text": obj}


def emergency_button(col, M, x, y, z, face=+1, prefix="Emg"):
    """PV: karo duvara monte gri metal kutu icinde sari govde, kirmizi mantar bas.
    Ustunde kirmizi-beyaz acil tren durdurma talimat levhasi."""
    bw, bh, bd = 0.22, 0.30, 0.11
    bx = slab(f"{prefix}_Box", x, x + face * bd, y - bw / 2, y + bw / 2,
              z - bh / 2, z + bh / 2, col, M["metal_galv"])
    yb = slab(f"{prefix}_Body", x + face * (bd - 0.02), x + face * (bd + 0.01),
              y - 0.075, y + 0.075, z - 0.09, z + 0.09, col, M["emergency_yellow"])
    btn = cylinder(f"{prefix}_Mushroom", 0.028, 0.030,
                   (x + face * (bd + 0.025), y, z + 0.01), 20, col,
                   M["emergency_red"], axis="X")
    lbl = slab(f"{prefix}_Label", x, x + face * 0.006, y - 0.14, y + 0.14,
               z + bh / 2 + 0.03, z + bh / 2 + 0.25, col, M["emergency_red"])
    return {"box": bx, "body": yb, "button": btn, "label": lbl}


def cable_tray(col, M, x0, x1, y0, y1, z, prefix="Tray"):
    """PV: ray ustu ham beton tavanda acikta kablo tavalari ve konsollar."""
    base = slab(f"{prefix}_Base", x0, x1, y0, y1, z, z + 0.02, col, M["metal_galv"])
    l1 = slab(f"{prefix}_LipA", x0, x0 + 0.02, y0, y1, z, z + 0.07, col, M["metal_galv"])
    l2 = slab(f"{prefix}_LipB", x1 - 0.02, x1, y0, y1, z, z + 0.07, col, M["metal_galv"])
    return {"base": base, "lips": [l1, l2]}


def wall_screen(col, M, x, y, z, face=+1, w=2.0, h=0.58, prefix="Screen"):
    """PV: ray duvarina / kolon yuzune monte genis yatay LCD bilgi ekrani."""
    frame = slab(f"{prefix}_Frame", x, x + face * 0.07, y - w / 2, y + w / 2,
                 z - h / 2, z + h / 2, col, M["steel_dark"])
    panel = slab(f"{prefix}_Panel", x + face * 0.07, x + face * 0.078,
                 y - w / 2 + 0.03, y + w / 2 - 0.03,
                 z - h / 2 + 0.03, z + h / 2 - 0.03, col, M["screen_black"])
    return {"frame": frame, "panel": panel}
