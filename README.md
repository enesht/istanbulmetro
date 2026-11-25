# Marmaray (B1 Halkalı → Gebze) — Roblox veri paketi

Rojo projesi. Kod değişiklikleri **diskteki dosyalarda** yapılır, Rojo Studio'ya taşır.

## Klasör yapısı
```
default.project.json              Rojo proje tanımı
rokit.toml                        araç zinciri (rojo 7.7.1)
src/shared/MarmarayData.lua    -> ReplicatedStorage.MarmarayData        ModuleScript
src/shared/MarmarayLayout.lua  -> ReplicatedStorage.MarmarayLayout      ModuleScript
src/server/BuildMarmaray.lua   -> ServerStorage.BuildMarmaray           ModuleScript
src/server/scripts/            -> ServerScriptService.Marmaray          Folder
src/client/                    -> StarterPlayer.StarterPlayerScripts.Marmaray
```
`Workspace` projeye **dahil değil** — kurulmuş raylar/istasyonlar orada ve Rojo onlara dokunmaz.
Servis düğümlerinde `$path` yok, yalnızca alt öğelerde: Rojo o servislerdeki başka şeyleri silmez.

## Dosyalar
| Dosya | Ne işe yarar |
|---|---|
| `src/shared/MarmarayData.lua` | Hat ekseni her 20 m'de bir nokta (X doğu, Y ray üstü kotu, Z güney; **metre**), 43 istasyon, 111 viraj, segment tipleri. |
| `src/shared/MarmarayLayout.lua` | OSM'den ölçülmüş peron + hat düzeni: `track2Offset(s)` (2. hattın yanal ofseti, smoothstep), `hasMainLine(s)`, istasyon peron sınırları. Ofset **metre**, `+` = Halkalı→Gebze yönünün **solu**. |
| `src/server/BuildMarmaray.lua` | Command Bar'dan çalıştırınca edit modunda 3 hat + yatak + tünel kabuğu + peron kurar. |
| `marmaray_stations.csv` | 43 istasyon: kilometraj, lat/lon, yerel x/y, yön, zemin kotu, ray üstü kotu (m/ft), derinlik, yeraltı/yerüstü. |
| `marmaray_track_5m.csv` | Her 5 m'de hat: lat/lon, x/y, zemin, ray kotu (m/ft), eğim %, viraj yarıçapı + SOL/SAĞ, tip (yerüstü/tünel/köprü/yarma). |
| `marmaray_curves.csv` | 111 viraj: başlangıç/bitiş km, min. yarıçap, yön (SOL/SAĞ, Halkalı→Gebze yönünde), dönüş açısı, en yakın istasyon. |
| `marmaray_harita_profil.png` | Harita + tüm hat boy kesiti + Boğaz tüneli yakın plan. |

## Kurulum
```
rokit install          # rojo 7.7.1
rojo plugin install    # Studio eklentisi (sonra Studio'yu yeniden başlat)
rojo serve             # ayrı terminalde açık kalır; Studio'da Plugins > Rojo > Connect
```

## Roblox'ta kullanım
```lua
-- Command Bar (edit modu):
require(game.ServerStorage.BuildMarmaray)({ START_KM = 19, END_KM = 34 })  -- önce sadece tünel bölgesi
require(game.ServerStorage.BuildMarmaray)()                                 -- tüm hat
```
Ayarlar: `STUDS_PER_METER` (varsayılan 1/0.28 = 3.571; 1 stud = 1 ft için 3.28084), `V_SCALE`, `SUBDIV`,
`RAILS`, `TUNNEL_SHELL`, `STATIONS`, `MAIN_LINE`, `PLATFORM_STEP`, `WIDE_TUBE_MAX`.

## Hatlar
| Yol | Yanal ofset (m) | Açıklama |
|---|---|---|
| 1 | `0` | Gebze yönü banliyö = `MarmarayData` ekseni |
| 2 | `Layout.track2Offset(s)` | Halkalı yönü banliyö, **sola** kayık (istasyon aralarında 4,5 m, peronlarda 12–26 m, Sirkeci 45 m) |
| 3 | `Layout.MainLineOffset` = −4,0 | ana hat (YHT/yük), yalnız `hasMainLine(s)`, tünelde yok |

Tünel kabuğu: 2. hat ofseti > 9 m ise her hatta ayrı tek hatlı tüp; ≤ 9 m ise (Boğaz batırma tüpü,
7,6 m) iki hattı saran tek geniş kutu.

**Dikkat:**
- Tam ölçek hat ≈ **270.000 stud**. Orijin hattın ortasında; uçlar X ≈ ±96.700, Z ≈ ±48.000 stud. Roblox'ta ~100k stud ötesinde fizik titremeye başlar: sınırdayız. Gerekirse bölümlere ayır (her bölüm ayrı Place + teleport) ya da yatayı küçült.
- `Workspace.FallenPartsDestroyHeight` varsayılanı −500 stud; tünel en dipte −207 stud. Güvenlik için −2000 yap.
- Tüm hat kurulumu 3 hatla ~70–80 bin Part. `StreamingEnabled` açık olsun, bölüm bölüm kur.
- `MarmarayData` **tek hat ekseni** tutar (OSM'deki Gebze yönü hattı). 2. ve 3. hat `MarmarayLayout`'taki yanal ofsetlerden türetilir.
- Hat yeryüzünde asılı duruyor: terrain/zemin üretilmiyor. 11 stud genişliğinde bir şerit, Baseplate 50 bin stud ötede — Explorer'dan istasyonu seçip **F** ile odaklanmak en kolay gezinme yöntemi.
- `Lighting.Atmosphere` (Density 0,3) birkaç bin stud ötesini siliyor; tüm hattı uzaktan görmek için geçici olarak 0 yap.

## Kaynaklar ve doğruluk
| Veri | Kaynak | Doğruluk |
|---|---|---|
| Yatay güzergâh, istasyon yerleri, tünel/köprü/yarma | OpenStreetMap rel. 9987139 (© OSM katkıcıları, ODbL) | ±2–5 m |
| Yerüstü ray kotları | EU-DEM 25 m (opentopodata), demiryolu profili gibi yumuşatıldı, %1,8 üst sınırlı | ±3–5 m |
| Tünel kotları | Yayınlanmış proje verilerinden türetildi (aşağıda) | tahmini ±3–5 m |
| Viraj yarıçapları | OSM geometrisinden hesap | ±%20–30 (resmî min. 300 m) |

Tünel için kullanılan resmî/yayınlanmış değerler: tüp tünel 1.387 m, en derin nokta 60,46 m (deniz seviyesi altı, yapı tabanı), maks. eğim %1,8, min. kurp yarıçapı 300 m; Üsküdar istasyonu deniz seviyesinin 30 m altına iniyor (kutu yüksekliği 30 m); Yenikapı kutu yüksekliği 24 m; Sirkeci havalandırma şaftları 60 m, istasyon ~58 m derinlikte; Ayrılık Çeşmesi ve Kazlıçeşme yerüstü. Kamuya açık resmî boy kesit çizimi bulunamadı; ray üstü kotları bu değerlerden %1,8 eğim kuralına uyacak şekilde türetildi.
