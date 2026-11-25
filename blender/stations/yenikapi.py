"""Yenikapi (Marmaray) - peron kati.

KAPSAM
    Yalnizca PERON KATI kurulur. Giris yapilari, bilet/turnike holu, yuruyen
    merdiven, sabit merdiven, asansor ve karsi peron MODELLENMEZ: refs/ altinda
    bu ogelere ait TEK fotograf bile yok (bkz. ARCHITECTURAL_ANALYSIS.md ->
    Yenikapi -> "giris yapilari / bilet holu / merdiven-yuruyen merdiven" =
    confidence "unknown"). Uydurmak yerine disarida birakildi.

PLAN OLCULERI - MarmarayLayout.Stations["Yenikapi"] (OSM'den olculmus)
    l0 = 2.0, l1 = 19.4   -> peron X 2.0 .. 19.4  (17.4 m genislik)
    a0 = -112, a1 = 132   -> peron Y -112 .. 132  (244 m uzunluk)
    track2 = 21.3         -> karsi yol ekseni X = 21.3
    Yol 1 ekseni X = 0. Peron iki yolun ARASINDA (ada peron).

GUVEN ETIKETLERI
    PV = fotograftan turetildi, AS = varsayim (fotografta yok)
"""

import bpy
from common import (box, slab, cylinder, bevel, array_y, collection, put,
                   material, assign, join, PLATFORM_TOP, stats)
import kit

# ---------------------------------------------------------------- plan (MarmarayLayout)
PLAT_X0, PLAT_X1 = 2.00, 19.40      # PV (OSM olcumu)
PLAT_Y0, PLAT_Y1 = -112.0, 132.0    # PV (OSM olcumu)
TRACK1_X = 0.0                      # PV
TRACK2_X = 21.30                    # PV (OSM olcumu)
PLAT_MID = (PLAT_X0 + PLAT_X1) / 2  # 10.70

# ---------------------------------------------------------------- kesit
CEIL_Z = PLATFORM_TOP + 4.20        # AS: tavan kotu fotograftan olculemedi
WALL_TOP = CEIL_Z + 0.55            # AS
TILE = 0.60                         # PV: zemin karosu ~2-2.5 x ayakkabi boyu
COL_PITCH = 7.50                    # AS: kolon araligi fotografta sayilamadi
COL_W, COL_D = 0.90, 1.40           # AS: kesit orani fotograftan kabaca
MURAL_LEN = 42.0                    # AS: mural uzunlugu tam cerceveli cekim yok

# PV: mural yuksekligi, ray ustu gorunen duvar yuksekliginin ~yarisi;
#     ustteki ham beton bant ~mural kadar, alttaki ~mural/5
_H = WALL_TOP                        # ray ustu gorunen duvar yuksekligi
MURAL_H = _H / 2.2
MURAL_Z0 = MURAL_H / 5.0
MURAL_Z1 = MURAL_Z0 + MURAL_H


def build():
    M = kit.materials()
    root = collection("Yenikapi")
    c_struct = collection("YK_Structure", root)
    c_floor = collection("YK_Floor", root)
    c_ceil = collection("YK_Ceiling", root)
    c_wall = collection("YK_Walls", root)
    c_art = collection("YK_Mural", root)
    c_fit = collection("YK_Fittings", root)
    c_track = collection("YK_Track", root)

    # ------------------------------------------------------------ peron govdesi
    # Peron dolgusu: ustu PLATFORM_TOP, ray kotunun altina iner.
    slab("YK_PlatformBody", PLAT_X0, PLAT_X1, PLAT_Y0, PLAT_Y1,
         -1.05, PLATFORM_TOP - 0.02, c_struct, M["concrete_pale"])
    # Zemin kaplamasi (cilali granit) - ayri ince katman, malzeme farkli
    floor = slab("YK_FloorFinish", PLAT_X0, PLAT_X1, PLAT_Y0, PLAT_Y1,
                 PLATFORM_TOP - 0.02, PLATFORM_TOP, c_floor, M["floor_granite"])
    # PV: cilali yuzey - karo derzi icin ince izgara (kalite: gercek geometri)
    _floor_grid(floor, c_floor, M)

    # ------------------------------------------------------------ peron kenarlari
    # Yol 1 tarafi (x = PLAT_X0), bantlar +X'e dogru
    kit.platform_edge_bands(c_floor, M, PLAT_X0, PLAT_Y0, PLAT_Y1,
                            inward=+1, prefix="YK_Edge1")
    # Yol 2 tarafi (x = PLAT_X1), bantlar -X'e dogru
    kit.platform_edge_bands(c_floor, M, PLAT_X1, PLAT_Y0, PLAT_Y1,
                            inward=-1, prefix="YK_Edge2")
    # kenar alin yuzeyi (perondan raya bakan dusey yuz)
    slab("YK_EdgeFace1", PLAT_X0 - 0.03, PLAT_X0, PLAT_Y0, PLAT_Y1,
         -0.10, PLATFORM_TOP, c_struct, M["concrete_pale"])
    slab("YK_EdgeFace2", PLAT_X1, PLAT_X1 + 0.03, PLAT_Y0, PLAT_Y1,
         -0.10, PLATFORM_TOP, c_struct, M["concrete_pale"])

    # ------------------------------------------------------------ kolonlar
    n_col = int((PLAT_Y1 - PLAT_Y0) / COL_PITCH)
    col0_y = PLAT_Y0 + (PLAT_Y1 - PLAT_Y0 - (n_col - 1) * COL_PITCH) / 2
    pier = slab("YK_Column", PLAT_MID - COL_W / 2, PLAT_MID + COL_W / 2,
                col0_y - COL_D / 2, col0_y + COL_D / 2,
                PLATFORM_TOP, CEIL_Z, c_struct, M["tile_beige"])
    array_y(pier, n_col, COL_PITCH)
    bevel(pier, 0.012, 2)
    # PV: kolon dibinde koyu su basman bandi
    base = slab("YK_ColumnBase", PLAT_MID - COL_W / 2 - 0.015, PLAT_MID + COL_W / 2 + 0.015,
                col0_y - COL_D / 2 - 0.015, col0_y + COL_D / 2 + 0.015,
                PLATFORM_TOP, PLATFORM_TOP + 0.12, c_struct, M["concrete_raw"])
    array_y(base, n_col, COL_PITCH)

    # ------------------------------------------------------------ duvarlar
    # PV: iki ayri duvar dili. Ray tarafi ham beton, peron tarafi bej karo.
    # Yol 1 duvari (x < 0): ham beton, mural burada
    slab("YK_WallTrack1", TRACK1_X - 2.60, TRACK1_X - 2.40, PLAT_Y0, PLAT_Y1,
         -0.60, WALL_TOP, c_wall, M["concrete_raw"])
    # Yol 2 duvari
    slab("YK_WallTrack2", TRACK2_X + 2.40, TRACK2_X + 2.60, PLAT_Y0, PLAT_Y1,
         -0.60, WALL_TOP, c_wall, M["concrete_raw"])
    # PV: peron tarafi karo kaplama - kolon sirasinin arkasindaki dolasim duvari
    #     yok; bunun yerine karo dili kolonlarda ve kenar kirisinde okunuyor.
    #     Kenar kirisi: tavan ile peron kenari arasinda sarkan kiris.
    for tag, xa, xb in (("1", PLAT_X0, PLAT_X0 + 0.35),
                        ("2", PLAT_X1 - 0.35, PLAT_X1)):
        slab(f"YK_EdgeBeam{tag}", xa, xb, PLAT_Y0, PLAT_Y1,
             CEIL_Z - 0.75, CEIL_Z, c_ceil, M["tile_beige"])
        # PV: kirisin yuzunde kesintisiz lineer isik hatti
        kit.strip_light(c_ceil, M, xa + 0.04, xb - 0.04, PLAT_Y0, PLAT_Y1,
                        CEIL_Z - 0.78, prefix=f"YK_EdgeStrip{tag}")

    # ------------------------------------------------------------ tavan
    ceil = kit.baffle_ceiling(c_ceil, M,
                              PLAT_X0 + 0.35, PLAT_X1 - 0.35,
                              PLAT_Y0, PLAT_Y1, CEIL_Z,
                              baffle_w=0.10, gap=0.10, depth=0.15,
                              panel_every=9, prefix="YK_Ceil")
    # PV: ray ustu tavan kaplamasiz koyu beton kutu + acikta kablo tavalari
    for tag, xc in (("1", TRACK1_X), ("2", TRACK2_X)):
        slab(f"YK_TrackSoffit{tag}", xc - 2.40, xc + 2.40, PLAT_Y0, PLAT_Y1,
             WALL_TOP - 0.35, WALL_TOP, c_wall, M["concrete_raw"])
        kit.cable_tray(c_wall, M, xc - 2.30, xc - 1.90, PLAT_Y0, PLAT_Y1,
                       WALL_TOP - 0.62, prefix=f"YK_Tray{tag}")

    # ------------------------------------------------------------ mural
    # PV: ray duvarinda dev yatay seramik rolyef pano + ustunde serit armatur
    my0, my1 = -MURAL_LEN / 2, MURAL_LEN / 2
    mural = slab("YK_Mural", TRACK1_X - 2.40, TRACK1_X - 2.34, my0, my1,
                 MURAL_Z0, MURAL_Z1, c_art, M["band_turquoise"])
    _mural_relief(mural, c_art, M, my0, my1)
    kit.strip_light(c_art, M, TRACK1_X - 2.42, TRACK1_X - 2.20, my0, my1,
                    MURAL_Z1 + 0.18, prefix="YK_MuralStrip")

    # ------------------------------------------------------------ donati
    # PV: en sagdaki payede istasyon adi panosu
    sign_y = col0_y + COL_PITCH * (n_col // 2)
    kit.station_name_sign(c_fit, M, "YENIKAPI",
                          PLAT_MID + COL_W / 2, sign_y, PLATFORM_TOP + 2.35,
                          face=+1, prefix="YK_NameSign")
    # PV: acil durum butonu + acil tren durdurma levhasi (karo yuzeye monte)
    kit.emergency_button(c_fit, M, PLAT_MID + COL_W / 2, sign_y - 1.9,
                         PLATFORM_TOP + 1.35, face=+1, prefix="YK_Emg")
    # PV: iki ayri konumda genis yatay bilgi ekrani
    kit.wall_screen(c_fit, M, PLAT_MID + COL_W / 2, sign_y + 2.6,
                    PLATFORM_TOP + 2.30, face=+1, prefix="YK_ScreenCol")
    kit.wall_screen(c_fit, M, TRACK1_X - 2.40, 24.0, MURAL_Z1 + 0.95,
                    face=+1, prefix="YK_ScreenWall")

    # ------------------------------------------------------------ yol
    t1 = kit.ballasted_track(c_track, M, TRACK1_X, PLAT_Y0 - 30, PLAT_Y1 + 30,
                             prefix="YK_Track1")
    t2 = kit.ballasted_track(c_track, M, TRACK2_X, PLAT_Y0 - 30, PLAT_Y1 + 30,
                             prefix="YK_Track2")
    # PV: ray duvari dibinde servis yuruyus seridi
    for tag, xc, side in (("1", TRACK1_X, -1), ("2", TRACK2_X, +1)):
        slab(f"YK_Walkway{tag}", xc + side * 2.40, xc + side * 1.95,
             PLAT_Y0, PLAT_Y1, -0.60, -0.42, c_track, M["concrete_pale"])

    # ------------------------------------------------------------ katener
    _catenary(c_track, M, TRACK1_X, PLAT_Y0, PLAT_Y1, WALL_TOP, "1")
    _catenary(c_track, M, TRACK2_X, PLAT_Y0, PLAT_Y1, WALL_TOP, "2")

    return {
        "collection": root,
        "ceiling_baffles": ceil["count"],
        "light_panels": len(ceil["panels"]),
        "columns": n_col,
        "sleepers_per_track": t1["sleepers"],
        "platform_m": (PLAT_X1 - PLAT_X0, PLAT_Y1 - PLAT_Y0),
    }


# ---------------------------------------------------------------- yardimcilar
def _floor_grid(floor_obj, col, M):
    """PV: zemin buyuk kare karo, duz izgara. Derzi gercek geometri olarak ac."""
    import bmesh
    me = floor_obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    geom = bm.faces[:] + bm.edges[:] + bm.verts[:]
    # ust yuze X ve Y yonunde karo izgarasi kes
    nx = max(1, int((PLAT_X1 - PLAT_X0) / TILE))
    ny = max(1, int((PLAT_Y1 - PLAT_Y0) / TILE))
    # cok yogun olmasin: izgarayi her 5 karoda bir derin derz olarak isle
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges], cuts=0)
    bm.to_mesh(me)
    bm.free()
    floor_obj["tile_size_m"] = TILE
    floor_obj["tiles_x"] = nx
    floor_obj["tiles_y"] = ny
    return floor_obj


def _mural_relief(mural_obj, col, M, y0, y1):
    """Theodosius Limani temali dev seramik rolyef mural.

    PV (ARCHITECTURAL_ANALYSIS -> Yenikapi -> "sanat eseri / mural"):
        modüler pismis toprak/seramik rolyef karolarin KOLAJI - amfora ve
        testiler, gemi iskeleti-kaburga ve halat dokulari, yesil dalgali su
        panelleri, turkuaz Iznik tipi desenli cini bloklar, rozet madalyon
        frizleri, oyma kemer icindeki figur rolyefi, buyuk radyal oyma gul
        pencere motifi, aralara gomulu kazi fotograflari.
    AS: her ogenin tam konumu ve olcusu - tam cerceveli cekim yok, bu yuzden
        duzen "kolaj" mantigina gore kurgulandi.

    Kolaj modüler karo izgarasina oturur: her blok karo katlarina yuvarlanir,
    boylece gercek eserdeki modüler dizilim korunur.
    """
    import math
    xf = -2.34                     # mural on yuzu
    span = y1 - y0
    TM = 0.45                      # AS: seramik karo modulu
    mats = {
        "terracotta": material("MAT_Mural_Terracotta", (0.33, 0.12, 0.055), roughness=0.62),
        "iznik": material("MAT_Mural_IznikTurquoise", (0.05, 0.36, 0.39), roughness=0.26),
        "iznik_dk": material("MAT_Mural_IznikDeep", (0.02, 0.17, 0.26), roughness=0.26),
        "water": material("MAT_Mural_WaterGreen", (0.05, 0.26, 0.17), roughness=0.30),
        "stone": material("MAT_Mural_CarvedStone", (0.46, 0.42, 0.34), roughness=0.70),
        "rope": material("MAT_Mural_Rope", (0.30, 0.22, 0.11), roughness=0.80),
        "photo": material("MAT_Mural_ExcavPhoto", (0.14, 0.13, 0.12), roughness=0.35),
    }
    sub = collection("YK_MuralRelief", col)

    def q(v):                       # karo izgarasina yuvarla
        return round(v / TM) * TM

    def blk(name, ya, yb, za, zb, depth, mat):
        return slab(name, xf, xf + depth, q(ya), q(yb),
                    MURAL_Z0 + MURAL_H * za, MURAL_Z0 + MURAL_H * zb, sub, mat)

    # --- taban: Iznik cini blok alani (modüler sahmerdan dizilim)
    ny = int(span / TM)
    nz = max(3, int(MURAL_H / TM))
    for iy in range(ny):
        for iz in range(nz):
            if (iy + iz) % 3 == 0:          # seyrek desen vurgusu
                yb = y0 + iy * TM
                zb = iz / nz
                slab(f"YK_MR_Iznik_{iy:03d}_{iz}", xf, xf + 0.014,
                     yb, yb + TM * 0.92,
                     MURAL_Z0 + MURAL_H * zb,
                     MURAL_Z0 + MURAL_H * (zb + 0.92 / nz),
                     sub, mats["iznik"] if (iy % 2) else mats["iznik_dk"])

    # --- rozet madalyon frizleri (alt ve ust yatay bant, tekrarli madalyon)
    for fi, zf in ((0, 0.06), (1, 0.90)):
        blk(f"YK_MR_FriezeBand_{fi}", y0, y1, zf, zf + 0.075, 0.022, mats["stone"])
        n_med = int(span / (TM * 2))
        for i in range(n_med):
            cylinder(f"YK_MR_Medallion_{fi}_{i:03d}", TM * 0.34, 0.030,
                     (xf + 0.030, q(y0 + TM) + i * TM * 2,
                      MURAL_Z0 + MURAL_H * (zf + 0.037)),
                     16, sub, mats["terracotta"], axis="X")

    # --- amfora ve testiler (sol ucte gruplu, farkli boy)
    for i in range(9):
        yy = q(y0 + 2.2 + i * 1.35)
        h = 0.17 + 0.055 * ((i * 7) % 3)
        zc = 0.30 + 0.10 * ((i * 5) % 3)
        body = cylinder(f"YK_MR_Amphora_{i}", h, 0.075,
                        (xf + 0.038, yy, MURAL_Z0 + MURAL_H * zc),
                        20, sub, mats["terracotta"], axis="X")
        body.scale = (1.0, 0.72, 1.35)      # amfora govdesi: dar-uzun
        # boyun
        cylinder(f"YK_MR_AmphoraNeck_{i}", h * 0.26, 0.055,
                 (xf + 0.030, yy, MURAL_Z0 + MURAL_H * zc + h * 1.25),
                 12, sub, mats["terracotta"], axis="X")

    # --- gemi iskeleti: omurga + kaburgalar (orta bolum)
    ky = q(y0 + span * 0.42)
    blk("YK_MR_Keel", ky - 4.0, ky + 4.0, 0.16, 0.205, 0.030, mats["rope"])
    for i in range(13):
        ry = ky - 3.6 + i * 0.60
        hh = 0.34 - abs(i - 6) * 0.028      # ortada yuksek, uclarda alcak
        slab(f"YK_MR_Rib_{i:02d}", xf, xf + 0.026, ry, ry + 0.085,
             MURAL_Z0 + MURAL_H * 0.20,
             MURAL_Z0 + MURAL_H * (0.20 + hh), sub, mats["rope"])
    # halat dokusu: omurga boyunca burgulu
    for i in range(26):
        cylinder(f"YK_MR_Rope_{i:02d}", 0.045, 0.028,
                 (xf + 0.028, ky - 3.9 + i * 0.30,
                  MURAL_Z0 + MURAL_H * 0.145), 10, sub, mats["rope"], axis="X")

    # --- yesil dalgali su panelleri (alt bant, kademeli)
    for i in range(6):
        ya = y0 + span * (0.52 + 0.055 * i)
        blk(f"YK_MR_Wave_{i}", ya, ya + span * 0.05, 0.10, 0.10 + 0.055 * (1 + i % 3),
            0.018, mats["water"])

    # --- oyma kemer icinde figur rolyefi
    ay = q(y0 + span * 0.72)
    blk("YK_MR_ArchBack", ay - 1.35, ay + 1.35, 0.17, 0.80, 0.020, mats["stone"])
    # kemer kavsi: yarim daire dilimler
    for i in range(11):
        t = i / 10.0
        ang = math.pi * t
        yy = ay - 1.2 * math.cos(ang)
        zz = 0.62 + 0.16 * math.sin(ang)
        slab(f"YK_MR_ArchVoussoir_{i:02d}", xf, xf + 0.038,
             yy - 0.10, yy + 0.10,
             MURAL_Z0 + MURAL_H * zz, MURAL_Z0 + MURAL_H * (zz + 0.07),
             sub, mats["stone"])
    # figur: govde + bas
    blk("YK_MR_Figure", ay - 0.26, ay + 0.26, 0.24, 0.60, 0.052, mats["terracotta"])
    cylinder("YK_MR_FigureHead", 0.17, 0.055,
             (xf + 0.052, ay, MURAL_Z0 + MURAL_H * 0.655), 16, sub,
             mats["terracotta"], axis="X")

    # --- buyuk radyal gul pencere motifi
    gy = q(y0 + span * 0.26)
    gz = MURAL_Z0 + MURAL_H * 0.54
    R = MURAL_H * 0.30
    cylinder("YK_MR_RoseBack", R, 0.024, (xf + 0.024, gy, gz), 40, sub, mats["stone"])
    cylinder("YK_MR_RoseHub", R * 0.17, 0.060, (xf + 0.055, gy, gz), 20, sub,
             mats["terracotta"], axis="X")
    # slab() mesh'i origin'de merkezler ve obj.location'a merkezi yazar; kolun
    # y/z araligi hub etrafinda simetrik secildigi icin obj origin'i = hub olur,
    # dolayisiyla X ekseninde dondurmek kolu hub cevresinde cevirir.
    for i in range(16):                      # radyal oyma kollar
        a = math.pi * i / 16                 # 16 kol -> 180 derecede yeterli
        spoke = slab(f"YK_MR_RoseSpoke_{i:02d}", xf + 0.024, xf + 0.046,
                     gy - R * 0.80, gy + R * 0.80, gz - 0.035, gz + 0.035,
                     sub, mats["terracotta"])
        spoke.rotation_euler = (a, 0, 0)
    cylinder("YK_MR_RoseRim", R * 1.06, 0.034, (xf + 0.034, gy, gz), 44, sub,
             mats["stone"], axis="X")

    # --- aralara gomulu kazi fotograflari (cerceveli koyu panolar)
    for i in range(5):
        py = q(y0 + span * (0.12 + 0.16 * i))
        blk(f"YK_MR_PhotoFrame_{i}", py - 0.42, py + 0.42, 0.40, 0.66, 0.016, mats["stone"])
        blk(f"YK_MR_Photo_{i}", py - 0.36, py + 0.36, 0.43, 0.63, 0.020, mats["photo"])

    return mural_obj


def _catenary(col, M, x_centre, y0, y1, z_top, tag):
    """PV: istasyon tavani altinda havai hat; duvara/tavana ankrajli konsol
    profilleri, capraz tasiyici tel ve askilar. Ucuncu ray YOK."""
    z_wire = z_top - 1.05
    # tasiyici tel
    slab(f"YK_Cat{tag}_Messenger", x_centre - 0.012, x_centre + 0.012, y0, y1,
         z_wire + 0.42, z_wire + 0.45, col, M["steel_dark"])
    # temas teli
    slab(f"YK_Cat{tag}_Contact", x_centre - 0.014, x_centre + 0.014, y0, y1,
         z_wire, z_wire + 0.028, col, M["steel_rail"])
    # konsol + aski (her 12 m - AS)
    pitch = 12.0
    n = max(1, int((y1 - y0) / pitch))
    arm = slab(f"YK_Cat{tag}_Arm", x_centre - 2.35, x_centre + 0.05,
               y0 + 2.0, y0 + 2.08, z_wire + 0.50, z_wire + 0.58,
               col, M["metal_galv"])
    array_y(arm, n, pitch)
    drop = slab(f"YK_Cat{tag}_Dropper", x_centre - 0.008, x_centre + 0.008,
                y0 + 2.0, y0 + 2.02, z_wire + 0.028, z_wire + 0.42,
                col, M["steel_dark"])
    array_y(drop, n * 4, pitch / 4)
    return True
