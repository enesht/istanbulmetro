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
    # PV: peron kenari bantlari
    M["band_white"] = material("MAT_Band_EdgeWhite", (0.84, 0.84, 0.82), roughness=0.32)
    M["band_tactile"] = material("MAT_Band_TactileYellow", (0.80, 0.56, 0.03), roughness=0.55)
    M["band_turquoise"] = material("MAT_Band_IznikTurquoise", (0.05, 0.38, 0.40), roughness=0.28)
    M["band_orange"] = material("MAT_Band_WarnOrange", (0.85, 0.28, 0.02), roughness=0.45)
    # metaller
    M["metal_baffle"] = material("MAT_Metal_BaffleGrey", (0.17, 0.175, 0.18),
                                 roughness=0.42, metallic=0.85)
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
def baffle_ceiling(col, M, x0, x1, y0, y1, z, baffle_w=0.10, gap=0.10,
                   depth=0.15, panel_every=9, prefix="Ceil"):
    """Lineer metal lamel (bafl) tavan + gomme isikli paneller.

    PV: lamel alt yuzu ile ara bosluk kabaca 1:1; isikli panel 4-5 lamel araligi.
    AS: lamel genisligi/derinligi ve tavan kotu fotograftan olculemedi.
    Lameller peron aksina DIK (X boyunca) uzanir.
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
    panels = []
    span = pitch * 4.5
    y = y0 + pitch * 2
    idx = 0
    while y + span < y1:
        p = slab(f"{prefix}_LightPanel_{idx:03d}", x0 + 1.2, x1 - 1.2,
                 y, y + span, z - depth, z - depth + 0.02, col, M["light_panel"])
        panels.append(p)
        y += pitch * panel_every
        idx += 1
    # Teknik bosluk tavani: lamellerin USTUNDE, panellere degmeyecek kadar yukarida.
    # Lamel araliklarindan koyu bir derinlik olarak okunur.
    plenum = slab(f"{prefix}_Plenum", x0, x1, y0, y1, z + 0.30, z + 0.55,
                  col, M["concrete_raw"])
    return {"baffle": b, "panels": panels, "plenum": plenum, "count": n, "pitch": pitch}


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
