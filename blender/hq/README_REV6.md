# Marmaray banliyö baş vagonu – Rev 6 (düzenlenebilir altyapı)

Bu belge Rev 6'da kurulan dosya düzenini, obje isimlerini, parametreleri ve düzenleme akışlarını anlatır.
Tüm yollar `blender/hq/` klasörüne göredir (proje kökü nerede olursa olsun; ilk kurulum `C:\Users\enesd\Downloads\marmaray_roblox_paket\` idi).

> Ön yüz ve renk düzeni özgün tasarımdır. Ölçüler teknik dokümandan alınmıştır. Görsel tasarım değişikliklerini aşağıdaki
> parametreler, Bézier kaynak eğrileri ve PNG atlaslar üzerinden kendiniz yapabilirsiniz.

---

## 1. Dosyalar

| Yol | İçerik |
|---|---|
| `cab_car_master.blend` | **High-poly master (Rev 6).** Gövde/kabin/tampon modifier'ları canlı (apply edilmedi). |
| `cab_car_master_rev5_yedek.blend` | Rev 5 yedeği (değiştirilmedi). |
| `rev6/common.py` | Ortak yardımcılar (ray-cast, modifier, sürücü (driver), malzeme). |
| `rev6/cab_geometry.py` | **Kabin geometrisi:** gövde/kabin ayrımı, kesit eğrileri, ön cam açıklığı + cam, silecekler, tampon + kuplör. |
| `rev6/livery.py` | **Renk düzeni:** prosedürel boya, boya panelleri (Bézier → yüzeye izdüşüm), varış göstergesi (LED). |
| `rev6/lamps.py` | **Far sistemi:** parametrik far yuvaları, ayrı optik parçalar, ışıklar, simetri. |
| `rev6/atlas.py` | UV atlas, 4096 bake, SVG UV layout. |
| `rev6/controls.py` | Kapı / tekerlek / boji / ışık kontrolleri (custom property + driver). |
| `rev6/export_roblox.py` | Roblox için FBX + GLB çıktısı (master dosyaya dokunmaz). |
| `rev6/rev6_main.py` | Adımları sırayla çalıştıran sürücü. |
| `textures/T_Body_BaseColor_4096.png`, `T_Body_Roughness_4096.png`, `T_Body_Metallic_4096.png` | Gövde + kapı atlası (UV: `UV_BodyAtlas`). |
| `textures/T_Cab_BaseColor_4096.png`, `T_Cab_Roughness_4096.png`, `T_Cab_Metallic_4096.png` | Ön kabin atlası (UV: `UV_CabAtlas`). |
| `textures/UV_Body_4096.svg`, `textures/UV_Cab_4096.svg` | Boyama için UV yerleşimleri (4096×4096). |
| `export_roblox/Marmaray_CabCar_Rev6.fbx` | Roblox FBX (dokular gömülü). |
| `export_roblox/Marmaray_CabCar_Rev6.glb` | Roblox glTF binary (dokular gömülü). |
| `export_roblox/Marmaray_CabCar_Rev6_parts.txt` | Parça başına üçgen sayıları. |
| `export_roblox/textures/*_1024.png` | Roblox için küçültülmüş atlaslar. |
| `renders/rev6_*.png` | Kontrol renderları. |
| `geom.py` | Gövde ölçüleri, profil, burun matematiği, ön cam ve maske şekilleri (Rev 1–6 ortak). |
| `build_hq.py`, `details.py` … `details4.py` | Rev 1–5 temel kurulum scriptleri (iç mekân, bojiler, çatı, kapılar); Rev 6 modülleri bunların ürettiği sahnenin üzerine çalışır. |
| `docs/837714268-_c-D__-Techizat-Genel-D__-Tasar_m-1.pdf` | Ölçülerin alındığı teknik doküman (TCDD E32000 donanım/genel tasarım). `docs/teknik_dokuman_sayfa_goruntusu_*.png`: kullanılan sayfanın görüntüsü. |
| `references/gercek_dis`, `gercek_ic`, `gercek_boji` | Gerçek araç referans fotoğrafları (dış görünüş, iç mekân, boji). |
| `references/roblox` | Roblox referans ekran görüntüleri. |

---

## 2. Scriptleri çalıştırma (Blender 5.2, master dosya açıkken – Scripting sekmesi)

```python
import sys, os, importlib, bpy
p = os.path.join(os.path.dirname(bpy.data.filepath), "rev6")   # açık master .blend'in yanındaki rev6/
if p not in sys.path: sys.path.insert(0, p)
import rev6_main; importlib.reload(rev6_main)

rev6_main.run(["lamps"])            # örnek: farları parametrelerden yeniden kur
# adımlar: "geometry", "lamps", "paint", "atlas", "controls", "export"
```

Tek tek modüller de çağrılabilir:

```python
import cab_geometry, livery, lamps, atlas, export_roblox, controls
cab_geometry.rebuild_cab_from_curves()   # kesit eğrilerini kabine geri yaz
livery.update_paint()                    # boya panellerini Bézier kaynaklarından yeniden üret
lamps.rebuild_lamps()                    # far yuvaları + optikler
atlas.rebake()                           # prosedürel boyadan 4096 atlasları yeniden üret (PNG'lerin üzerine yazar, ~10 dk)
export_roblox.export_all()               # FBX + GLB
```

> **Dikkat:** `run(["geometry"])` gövde ve kabini sıfırdan kurar: UV'ler yeniden hesaplanır, boya yuvası prosedürel malzemeye döner.
> Ardından sırayla `lamps`, `paint`, `atlas`, `controls` adımlarını da çalıştırın. Sadece kesit düzenlediyseniz `geometry` yerine
> `rebuild_cab_from_curves()` kullanın.

---

## 3. Sahne düzeni ve obje isimleri

### 3.1 Gövde ve kabin (`CabCar_Exterior`)
| Obje | Açıklama | Modifier yığını (canlı) |
|---|---|---|
| `CC_Body_Main` | Ana gövde kafesi (X −10.95 … 9.706), kapı/pencere boşlukları | Subdivision(1) → Solidify(45 mm) → Smooth by Angle(35°) |
| `CC_Cab_Body` | Ön kabin kafesi (burun yuvarlatmaları + ön yüz) | Subdivision(1) → Solidify(45 mm) → Boolean `OpeningsAndLampPods` (koleksiyon `CC_Cab_Cutters`, EXACT) → Smooth by Angle(35°) → WeightedNormal |
| `CC_Ref_Exterior` (`CC_Helpers`, gizli) | Deliksiz tam kafes + Subdivision. Boya panelleri, farlar, cam ve tampon bu yüzeye izdüşürülür. | Subdivision(1) |

Malzeme yuvaları: 0 = boya (`MAT_Body_Atlas` / `MAT_Cab_Atlas`), 1 = `PBR_UnderframeBlack_RAL9005`, 2 = iç kaplama, 3 = kauçuk, (kabin) 4 = siyah plastik (far yuvası iç yüzeyleri).

### 3.2 Kesit eğrileri (`CC_Cab_Sections`)
- `CC_CabSection_00` … `CC_CabSection_09`: kapalı POLY eğriler, **her biri 78 nokta** (gövde profili). 00 = gövde/kabin dikişi (X 9.706), 09 = ön yüz sınırı.
- `CC_CabFaceColumn_01` … `CC_CabFaceColumn_15`: ön yüzün iç noktaları, **her biri 22 nokta** (dikey sütunlar).
- Düzenleme: noktaları Edit Mode'da taşıyın (nokta sayısını değiştirmeyin) → `cab_geometry.rebuild_cab_from_curves()`.
  Sonra yüzeye bağlı parçaları güncelleyin: `lamps.rebuild_lamps()`, `livery.update_paint()`, `cab_geometry.front_glazing()`, `cab_geometry.bumper_and_coupler()`.

### 3.3 Ön cam (`CabCar_Front`, `CC_Cab_Cutters`)
| Obje | Açıklama |
|---|---|
| `CC_Cutter_Windscreen` | Fiziksel cam açıklığını kesen prizma (boolean). Şekil: `geom.py` → `WS_ZC, WS_B, WS_A, WS_TAPER, WS_N` (eğimli süperelips). |
| `CC_Windscreen_Glass` | Açıklığın 30 mm dışına taşan, yüzeyden 6 mm önde, gövdeyle aynı hizada yapıştırılmış cam. |
| `CC_Windscreen_Seal` | Cam kenarı contası. |
| `CC_Wiper_Arm_1/2`, `CC_Wiper_Blade_1/2` | Silecekler. |

### 3.4 Boya panelleri (`CC_Paint`, kaynaklar `CC_Paint_Sources`)
| Kaynak (Bézier, düzenlenebilir) | Üretilen mesh | Malzeme | İzdüşüm |
|---|---|---|---|
| `CC_PaintSrc_Mask` | `CC_Paint_Mask` + `CC_Paint_MaskOutline` (30 mm beyaz kenar) | `PAINT_MaskBlack`, `PAINT_MaskOutlineWhite` | önden (−X) |
| `CC_PaintSrc_Crown` | `CC_Paint_Crown_L` + `CC_Paint_Crown_R` (birebir ayna) | `PAINT_Red_PMS186` | soldan (−Y); sağ taraf otomatik aynalanır |

- Düzenleme: kaynak eğriyi Edit Mode'da şekillendirin (kontrol noktası ekleyebilir/silebilirsiniz) → `livery.update_paint()`.
- Ayarlar `livery.PAINT` sözlüğünde: `offset` (yüzeyden yükseklik, varsayılan 1.2 mm), `spacing` (iç üçgen aralığı: maske 22 mm, taç 14 mm), `mirror`, `outline` (genişlik 30 mm).
- Yeni panel eklemek: yeni bir 2D kapalı Bézier oluşturun, nesnenin yerel −Z ekseni yüzeye baksın (önden izdüşüm için `common.frame_front()`, yandan için `common.frame_side_left()` matrisleri), `PAINT` sözlüğüne bir satır ekleyin.
- Gövde boyunca uzanan şeritler (tavan altı ince kırmızı, alt kırmızı şerit, lacivert bant, pencere bandı) atlas PNG'lerinde ve `PBR_Livery_Procedural` malzemesinde tanımlıdır.

### 3.5 Varış göstergesi
| Obje | Açıklama |
|---|---|
| `CC_Dest_Text` | **Düzenlenebilir metin** (Text nesnesi, varsayılan `GEBZE`). Tab ile metni değiştirin. Geometry Nodes `CC_DecalProjectMesh` ile yüzeye izdüşer. Malzeme `LED_DotMatrix_Orange` (5.5 mm nokta aralığı). |
| `CC_Dest_Panel` | Sönük LED zemini (`LED_DotMatrix_Off`). |
| Parametreler | `livery.DEST`: `center_z 3.315`, `half_width 0.60`, `half_height 0.072`, `corner 0.03`, `text_size 0.105`. |

### 3.6 Far sistemi (`CC_Lamps`)
**Parametreler** – `CC_LampRig` nesnesinin Custom Properties'inde (Object Properties → Custom Properties). Değiştirdikten sonra `lamps.rebuild_lamps()`.

| Özellik | Varsayılan | Anlamı |
|---|---|---|
| `pod_angle_deg` | 35.0 | Yuvanın izdüşüm yönü (+X'ten yana doğru derece) |
| `pod_center_y` | 1.08 | Yuva merkezi, ön yüzde \|y\| (m) |
| `pod_center_z` | 1.42 | Yuva merkezi yüksekliği (m) |
| `pod_length` / `pod_height` | 0.58 / 0.22 | Yuva boyutları (m) |
| `pod_tilt_deg` | 20.0 | Çapraz eğim (+ dışa doğru yükselir) |
| `pod_corner_r` | 0.09 | Köşe yarıçapı (m) |
| `pod_depth` | 0.040 | Gövdeye gömülme derinliği (45 mm kabuk içinde) |
| `head_u` / `head_w` / `head_radius` | −0.13 / −0.004 / 0.078 | Beyaz farın yuva içindeki konumu (u: + dış, w: + yukarı) ve reflektör yarıçapı |
| `tail_u` / `tail_w` / `tail_radius` | 0.175 / 0.014 / 0.048 | Kırmızı kuyruk lambası |
| `aim_forward` | 0.20 | 0 = yüzey normaline, 1 = tam ileriye bakar |
| `head_light_w` / `tail_light_w` | 180 / 6 | Render ışık güçleri (W) |

Farları yer değiştirmek için `head_u` ↔ `tail_u` ve `head_w` ↔ `tail_w` değerlerini değiştirmeniz yeterli.

**Canlı ince ayar:** `CC_HeadLamp_L` / `CC_TailLamp_L` boşluk nesnelerini (empty) taşıyın, döndürün, ölçekleyin. Sağ taraftaki
`CC_HeadLamp_R` / `CC_TailLamp_R` nesneleri `CC_MirrorY` altında driver'larla birebir aynalanır (sağ taraf parçaları sol taraftaki mesh verisini paylaşır).

**Parçalar (her far için ayrı mesh):** `_Bezel` (siyah çerçeve), `_Reflector`, `_Emitter` (ışık kaynağı), `_DRL` (yalnız beyaz farda halka), `_Lens`, `_Light` (Blender ışığı), `CC_RobloxAnchor_*` (Roblox Attachment konumu).
Yuva kesicileri: `CC_Cutter_LampPod_L/_R` (`CC_Cab_Cutters`).

### 3.7 Tampon ve kuplör
- `CC_Bumper` (Solidify canlı), `CC_Bumper_Lip_L/_R` (kauçuk kenar), `CC_ObstacleDeflector`.
- `CC_Coupler` (empty) altında: `CC_Coupler_Pocket`, `_Shank`, `_Head`, `_GuideCone`, `_GuideFunnel`, `_ElectricHead`, `_Hose_L/_R`.
- Parametreler `cab_geometry.BUMPER`: `x_start 10.05`, `z_top 0.915`, `z_bottom_front 0.58`, `z_bottom_side 0.84`, `coupler_half_width 0.27`, `tuck_front 0.055`, `thickness 0.014` → `cab_geometry.bumper_and_coupler()`.

---

## 4. Kontroller (`CC_Controls` nesnesi, Custom Properties)

| Özellik | Aralık | Etki |
|---|---|---|
| `doors_left_open`, `doors_right_open` | 0–1 | Yolcu kapıları kayar (`CC_Door_*` → `delta_location.x`) |
| `cab_door_left_open`, `cab_door_right_open`, `cab_door_max_deg` | 0–1, 95° | Kabin kapıları menteşeden döner |
| `wheel_rotation_deg` | serbest | `CC_B?_Wheelset?` dingil ekseninde döner (animasyon için keyframe verin) |
| `bogie_front_yaw_deg`, `bogie_rear_yaw_deg` | ±15° | `CC_Bogie_F_Pivot` / `CC_Bogie_R_Pivot` |
| `headlights`, `drl`, `taillights` | 0–1 | Far/halka/kuyruk lambası malzeme parlaklığı ve ışık gücü |
| `saloon_lights` | 0–1 | İç aydınlatma |
| `destination_display` | 0–1 | Ön ve yan LED göstergeler |

Hiyerarşi: `CC_Bogie_F_Pivot` → `CC_Wheelset_F1_Pivot`, `CC_Wheelset_F2_Pivot` → `CC_BF_Wheelset1/2` (döner) + dingil kutuları/dişli kutuları.
Driver'lar özellik değiştiğinde güncellenir (gerekirse zaman çizelgesinde bir kare ilerleyin).

---

## 5. UV ve doku atlasları

| Atlas | Nesneler | UV katmanı | Yoğunluk |
|---|---|---|---|
| Gövde 4096² | `CC_Body_Main`, 20 kapı kanadı, 2 kabin kapısı | `UV_BodyAtlas` | 0.0426 UV/m ≈ 174 px/m |
| Kabin 4096² | `CC_Cab_Body` | `UV_CabAtlas` | 0.0870 UV/m ≈ 356 px/m |

- **Gövde yerleşimi:** gövde iki şerit halinde açılmıştır (üst şerit X < −0.50, alt şerit X ≥ −0.50). Yatay eksen = vagon boyu, dikey eksen = profil çevresi (alt orta dikiş). Sağ üst bölge: kapı kanatları (önden görünüş, x–z).
- **Kabin yerleşimi:** alt bant = burun yuvarlatma halkası (yatay = profil çevresi, dikey = yuvarlatma boyunca mesafe). Üstte ön yüz (önden düzlemsel izdüşüm).
- **Boyama akışı:** SVG'yi (`UV_*_4096.svg`) PNG'nin üstüne katman olarak açın, `T_*_BaseColor_4096.png` dosyasını boyayın,
  metal bölgeleri `T_*_Metallic` dosyasında beyaz/siyah, pürüzlülüğü `T_*_Roughness` dosyasında güncelleyin → Blender'da Image Editor → *Image ▸ Reload* (veya dosyayı yeniden açın).
  **Not:** Atlaslar taşınabilirlik için `.blend` içine paketlidir (bkz. bölüm 8). PNG'leri dışarıda düzenlemeden önce
  *File ▸ External Data ▸ Unpack Resources ▸ Use files in current directory* seçin; aksi halde *Reload* paketli kopyayı okur.
- **Prosedürel kaynak:** `PBR_Livery_Procedural` (fake user). `livery.LIV` sözlüğü: `NAVY (1.20, 1.02, 42, 60)`, `RED_LOW (1.68, 1.80, 56)`, `CANT (3.20, 3.26, 10.12)`, `BAND (1.86, 3.06, 66)`, `ROOF_Z 3.30`, palet `livery.PAL`.
  Değiştirip `atlas.rebake()` çalıştırırsanız PNG'lerin üzerine yazılır (elle boyadıklarınızı önce yedekleyin).

---

## 6. Roblox çıktısı

- Dosyalar: `export_roblox/Marmaray_CabCar_Rev6.fbx` ve `.glb` (aynı içerik).
- **182 MeshPart, toplam 330.519 üçgen, en büyük parça 14.862 üçgen** (`Paint_Mask`). Sınır: 20.000 üçgen / mesh.
- Her mesh tek malzemedir (Roblox'ta her MeshPart'a tek malzeme veya SurfaceAppearance atanır). Gövde ve kabin parçaları atlas dokularını kullanır (`*_1024.png` gömülü).
- Parça adları gruplara göre: `Body_Main_*`, `Cab_Body_*`, `Door_L1a_*` … `Door_R5b_*`, `CabDoor_L/R_*`, `Lamp_Head_L_Emitter`, `Lamp_Head_L_DRL`, `Lamp_Tail_R_Emitter` …,
  `LightAnchor_Head_L` …, `Wheelset_F1_*` …, `Bogie_F_*`, `Paint_Mask`, `Paint_Crown_L/R`, `Dest_Text`, `Dest_Panel`, `Windscreen_Glass`, `Front_Bumper_Coupler_*`, `Interior_*`, `Roof_*`, `Underframe_*`, `Gangway_*`.
- **İçe aktarma:** Studio → Import 3D → *Scale Unit = Meter* (25:7 stud/metre; 1 stud = 0.28 m; vagon ≈ 78 stud).
- **Işıklar:** `LightAnchor_*` parçalarının konumuna Attachment + SpotLight (far) / PointLight (kuyruk) ekleyin; `Lamp_*_Emitter` ve `_DRL` parçalarını Neon malzemeyle açıp kapatın – hepsi ayrı parça olduğu için bağımsız kontrol edilir.
- **Varış göstergesi:** `Dest_Panel` üzerine SurfaceGui + TextLabel (turuncu) koyarak metni oyunda değiştirin; `Dest_Text` Blender'daki metnin mesh halidir.
- **Kapılar/tekerlekler:** `Door_*` parçalarını TweenService ile kaydırın (kayma mesafesi kanat başına ≈ 0.84 m); `Wheelset_*` parçalarını dingil ekseninde döndürün.
- Dokular Roblox'ta 1024 sürümleriyle gömülüdür; 4096 asıllar `textures/` klasöründedir.

---

## 7. Teknik notlar
- Master dosyada gövde, kabin ve tampon üzerindeki modifier'lar apply edilmemiştir (high-poly master korunur). Rev 1–5'ten gelen iç mekân, bojiler ve süsler daha önce oluşturulduğu haliyle durur.
- Kabin ile gövde arasındaki dikiş X = 9.706'dadır (profilin sabit olduğu bölge); iki tarafın normalleri bu yüzden kesintisizdir.
- Klima bölümündeki alçak çatı, tavan omzunda yumuşak bir dönüşle (geom `ZKNEE 3.40 → ZFLAT 3.50`) iner; kabin rampası 8.86 → 9.62 m boyunca S-eğrisidir (`WELL_RAMP_FRONT 0.76`).
- Boya panelleri ve far yuvaları canlı modifier değil, kaynaklardan **yeniden üretilen** meshlerdir (yüksek kaliteli, yüzeyi takip eden üçgenleme için). Varış metni ve paneli canlıdır (Geometry Nodes).
- Sağ taraf farlar ve boya panelleri her zaman sol taraftan aynalanır; sağ tarafı elle düzenlemeyin.

---

## 8. Taşınabilirlik (Rev 6 kaynak paketi)

- **Dokular paketli:** `cab_car_master.blend` içindeki 6 adet 4096 atlas (`T_Body_*`, `T_Cab_*`) *Pack Resources* ile dosyaya gömülüdür; yolları göreli (`//textures/…`). Dosya başka bir bilgisayarda açıldığında eksik doku olmaz.
- **Kütüphane bağlantısı kaldırıldı:** "Smooth by Angle" node grubu önceden Blender kurulumundaki `geometry_nodes_essentials.blend` dosyasına bağlıydı (mutlak `Program Files` yolu). Artık dosyanın içinde yereldir; harici `.blend` bağlantısı yoktur.
- **Render çıkış yolları göreli:** `//renders/…`. `cab_car_master_rev5_yedek.blend` tamamen prosedüreldir (harici doku/bağlantı yok).
- **Script yolları:** `rev6/common.py` ve `build_hq.py`, `blender/hq` klasörünü otomatik bulur (sıra: `MARMARAY_HQ` ortam değişkeni → scriptin kendi klasörü → açık `.blend` klasörü → eski `Downloads` yolu). Proje başka bir yere taşınırsa ek ayar gerekmez; gerekirse `MARMARAY_HQ` ile `blender/hq` yolunu verin.
- **PNG ile çalışmak:** *File ▸ External Data ▸ Unpack Resources ▸ Use files in current directory (create when necessary)* → görüntüler `//textures/*.png` dosyalarını kullanır. İş bitince isterseniz *Pack Resources* ile tekrar paketleyin. `atlas.rebake()` PNG'yi diske yazar ve paketli kopyayı da günceller.
- Gerekli sürüm: **Blender 5.2** (Geometry Nodes modifier girişleri `md.properties.inputs` API'siyle ayarlanır; daha eski sürümlerde `common.set_gn_input` geri dönüş yolunu kullanır).
