--[[
Yenikapı (Marmaray) — DETAYLI PERON KATI  (ModuleScript)

KURULUM (Rojo)
  src/server/stations/yenikapi_detail.lua -> ServerStorage.MarmarayStations.yenikapi_detail

  Command Bar (edit modu):
    local old = workspace.Marmaray.Stations:FindFirstChild("Yenikapı")
    if old then old:Destroy() end
    require(game.ServerStorage.MarmarayStations.yenikapi_detail)()

  Not: mevcut basit "Yenikapı" modelini SILMEK cagiranin isi. Bu modul yalnizca
  yenisini kurar ve dondurur. Ayni isimde bir kardes varsa "_Detay" ekiyle kurar.

KAPSAM
  Yalnizca PERON KATI. Giris yapilari, bilet/turnike holu, yuruyen merdiven,
  sabit merdiven ve asansor MODELLENMEZ: refs/ altinda bu ogelere ait tek
  fotograf bile yok (ARCHITECTURAL_ANALYSIS.md -> Yenikapı -> "giris yapilari /
  bilet holu / merdiven-yuruyen merdiven" = ❌ fotografta yok). Uydurulmadi.

KAYNAK
  Tasarim blender/stations/yenikapi.py + kit.py icinde modellendi; buradaki tum
  olculer ve malzeme mantigi oradan birebir tasindi. Guven etiketleri korundu:
      PV = fotograftan turetildi      AS = fotografta yok, varsayim

PLAN (MarmarayLayout.Stations["Yenikapı"] — DEGISTIRILMEDI, modulden okunur)
  l0 = 2.0, l1 = 19.4    -> peron yanal 2.0 .. 19.4 m (17.4 m genislik)
  a0 = -112, a1 = 132    -> peron boyuna -112 .. 132 m (244 m)
  track2 = 21.3          -> karsi yol ekseni; Yol 1 ekseni = 0
  Peron IKI YOLUN ARASINDA (ada peron). s = 22736 m, railTop = -18.0 m.

YEREL KOORDINAT SISTEMI (yapinin tamami bu uc sayiyla tarif edilir)
  x = YANAL ofset (metre), + = seyir yonunun SOLU — MarmarayLayout ile ayni isaret
  y = ISTASYON KILOMETRAJINA gore boyuna ofset (metre), + = seyir yonu
  z = RAY USTU kotuna gore yukseklik (metre); peron ustu z = +1.10

  Dunya donusumu:
      local p = D.positionAtChainage(s, k, V)        -- eksen, ray ustu kotunda
      local f = (pos(s+2) - pos(s-2)).Unit
      local left = Vector3.yAxis:Cross(f).Unit       -- +ofset yonu
      world = p + left * (x * k) + Vector3.new(0, z * k * V, 0)

  BU ISTASYONDA EKSEN DUZ: km 22.624..22.868 arasinda hat ekseninin kirise
  en buyuk sapmasi 0.385 m (R ~ 3300 m) ve railTop 244 m boyunca sabit -18.0 m.
  OSM verisindeki yon gurultusu (±0.35°/20 m) peron genisliginde ~0.1 m'lik
  kirilmalara yol acardi; bu yuzden istasyonun TAMAMI tek bir RIJIT cerceveye
  (BASE) oturtuldu. Boylece 244 m'lik ogeler tek parca gecebiliyor — hem daha
  dogru hem cok daha ucuz. Egri istasyonlarda bu yaklasim KULLANILAMAZ.

  BASE = CFrame.lookAt(p0, p0 + fwd, Vector3.yAxis) oldugundan:
      BASE yerel +X = SAG  = -left   -> yerel X = -x * k
      BASE yerel +Y = YUKARI          -> yerel Y = +z * k * V
      BASE yerel +Z = -fwd            -> yerel Z = -y * k
  Part boyutlari da bu sirayla: Size = (yanal, dusey, boyuna).

ROBLOX'A OZGU DUZELTMELER (Blender surumunden sapmalar — bilincli)
  * Part minimum olcusu 0.05 stud (= 0.014 m). Derz/kabartma gibi milimetrik
    degerler bu esige yuvarlanir; kolon karo derzi 0.006 -> 0.015 m, mural
    rolyef derinlikleri rel() ile 0.06 m'yi gecmeyecek sekilde buyutuldu.
    Gerekce: Roblox'ta bump/normal map yok, kabartma yalnizca GERCEK derinlikle
    okunuyor.
  * Zemin derzi ve peron kenari bantlari kaplamanin icine gomulu, yalnizca
    2-6 mm disari tasar (CSG yok, oyuk acilamiyor).
  * Gul pencere cemberi (RoseRim) Blender'da kollarin onunde duran dolu disk;
    burada ARKAYA alindi, yoksa kollari ve gobek kismini kapatiyordu.
  * Katener konsolu her yolda KENDI ray duvarindan cikiyor (Blender'da ikisi de
    -X yonune bakiyordu; Yol 2'nin duvari +X tarafinda).
  * Istasyon adi panosu ve kolon ekrani 1.30 m'ye indirildi: Blender'daki 2.40 /
    2.00 m varsayilanlari 1.40 m'lik kolon yuzunden tasiyordu.
  * Renkler: Blender degerleri LINEER. lin() sRGB'ye cevirir, sayilar kaynakta
    yazildigi gibi birakildi.

PART BUTCESI (yaklasik, varsayilan config)
  zemin+derz 432 | kenar bantlari 210 | kolonlar 1344 | tavan 787 | alinlik 6
  duvarlar 356 | mural 366 | donati ~22 | katener 204     -> toplam ~3700
]]

local DEFAULT = {
	STUDS_PER_METER = 1 / 0.28, -- Roblox karakter olcegi (1 stud = 0.28 m)
	V_SCALE = 1,                -- dikey abarti (1 = gercek)
	PARENT = nil,               -- varsayilan: Workspace.Marmaray.Stations
	NAME = "Yenikapı",
	ORIGIN_KM = nil,            -- nil ise Workspace.Marmaray.OriginKm niteliginden okunur
	CATENARY = true,            -- PV: istasyon icinde gorunur havai hat
	TRACK = false,              -- balast + travers; BuildMarmaray zaten yatak+ray seriyor
	FLOOR_JOINTS = true,        -- 60 cm karo derz izgarasi (~430 part)
	LIGHTS = true,              -- PointLight / SurfaceLight (Neon yuzeyler zaten var)
	YIELD_EVERY = 350,          -- bu kadar partta bir task.wait()
	VERBOSE = true,
}

return function(config)
	local C = table.clone(DEFAULT)
	for key, v in pairs(config or {}) do C[key] = v end

	local RS = game:GetService("ReplicatedStorage")
	local D = require(RS:WaitForChild("MarmarayData"))
	local L = require(RS:WaitForChild("MarmarayLayout"))
	local k, V = C.STUDS_PER_METER, C.V_SCALE

	---------------------------------------------------------------- plan verisi
	local NAME = "Yenikapı"
	local lay = L.Stations[NAME]
	local st
	for _, s in ipairs(D.Stations) do
		if s.name == NAME then st = s end
	end
	assert(lay and st, "[Yenikapı] MarmarayData/MarmarayLayout icinde istasyon bulunamadi")

	local S_ST = st.s                 -- 22736 m
	local PX0, PX1 = lay.l0, lay.l1   -- 2.00 .. 19.40  (PV, OSM olcumu)
	local PY0, PY1 = lay.a0, lay.a1   -- -112 .. 132    (PV, OSM olcumu)
	local TRACK1_X = 0.0              -- PV
	local TRACK2_X = lay.track2       -- 21.30 (PV)
	local PLAT_MID = (PX0 + PX1) / 2  -- 10.70

	---------------------------------------------------------------- kesit sabitleri
	local PLAT_TOP = 1.10             -- PV: peron ustu ray ustunden 1.10 m
	local CEIL_Z   = PLAT_TOP + 4.20  -- AS: tavan kotu fotograftan olculemedi
	local WALL_TOP = CEIL_Z + 0.55    -- AS
	local TILE     = 0.60             -- PV: zemin karosu ~2-2.5 x ayakkabi boyu
	local COL_PITCH = 7.50            -- AS: kolon araligi fotografta sayilamadi
	local COL_W, COL_D = 0.90, 1.40   -- AS: kesit orani fotograftan kabaca
	local MURAL_LEN = 42.0            -- AS: tam cerceveli mural cekimi yok

	-- PV: mural yuksekligi, ray ustu gorunen duvar yuksekliginin ~yarisi;
	--     ustteki ham beton bant ~mural kadar, alttaki ~mural/5
	local MURAL_H = WALL_TOP / 2.2            -- 2.659
	local MZ0 = MURAL_H / 5.0                 -- 0.532  (peron ustunun ALTINDA — dogru)
	local MZ1 = MZ0 + MURAL_H                 -- 3.191

	local EDGE_TOTAL = 0.15 + 0.60 + 0.60 + 0.10  -- 1.45 m kenar bant kompozisyonu

	---------------------------------------------------------------- malzemeler
	-- Blender degerleri LINEER (sRGB degil); lin() Roblox rengine cevirir.
	local function lin(r, g, b)
		local function f(c)
			c = math.clamp(c, 0, 1)
			if c <= 0.0031308 then
				c = c * 12.92
			else
				c = 1.055 * c ^ (1 / 2.4) - 0.055
			end
			return c
		end
		return Color3.new(f(r), f(g), f(b))
	end
	local EM = Enum.Material
	local M = {
		-- PV: cilali acik gri benekli granit — tavan isiklari zeminde yansiyor
		floor_granite = { c = lin(0.52, 0.52, 0.53), m = EM.Granite, r = 0.10 },
		floor_grout   = { c = lin(0.26, 0.26, 0.265), m = EM.SmoothPlastic },
		-- PV: sicak bej / sutlu kahve buyuk format mat seramik
		tile_beige    = { c = lin(0.66, 0.57, 0.45), m = EM.SmoothPlastic, r = 0.04 },
		tile_grout    = { c = lin(0.085, 0.072, 0.058), m = EM.SmoothPlastic },
		-- PV: ray tarafi ham puskurtme beton, koyu gri-siyah
		concrete_raw  = { c = lin(0.045, 0.045, 0.048), m = EM.Concrete },
		concrete_seam = { c = lin(0.028, 0.028, 0.030), m = EM.Concrete },
		concrete_pale = { c = lin(0.38, 0.375, 0.365), m = EM.Concrete },
		fascia_grey   = { c = lin(0.47, 0.465, 0.45), m = EM.SmoothPlastic },
		-- REFERANS: mural BAKIR/TERRAKOTA (turkuaz DEGIL — turkuaz olan yalnizca
		-- peron kenarindaki grafik bant). Derinlik farki renkle degil isik-golge
		-- ile okunsun diye palet dar tutuldu.
		cu            = { c = lin(0.34, 0.145, 0.055), m = EM.Slate },
		cu_mid        = { c = lin(0.28, 0.115, 0.045), m = EM.Slate },
		cu_deep       = { c = lin(0.19, 0.075, 0.028), m = EM.Slate },
		cu_patina     = { c = lin(0.22, 0.135, 0.070), m = EM.Slate },
		cu_light      = { c = lin(0.44, 0.215, 0.090), m = EM.Granite },
		cu_rope       = { c = lin(0.25, 0.105, 0.040), m = EM.Slate },
		excav_photo   = { c = lin(0.10, 0.055, 0.030), m = EM.SmoothPlastic, r = 0.08 },
		mural_frame   = { c = lin(0.035, 0.032, 0.030), m = EM.Concrete },
		-- PV: peron kenari bantlari
		band_white    = { c = lin(0.84, 0.84, 0.82), m = EM.SmoothPlastic },
		band_tactile  = { c = lin(0.80, 0.56, 0.03), m = EM.Pebble },
		band_turq     = { c = lin(0.05, 0.38, 0.40), m = EM.SmoothPlastic },
		band_turq_lt  = { c = lin(0.22, 0.58, 0.58), m = EM.SmoothPlastic },
		band_orange   = { c = lin(0.85, 0.28, 0.02), m = EM.SmoothPlastic },
		-- REFERANS: lameller MAT gri-antrasit bicaklar; ayna gibi metalik degil
		metal_baffle  = { c = lin(0.115, 0.118, 0.122), m = EM.Metal },
		metal_galv    = { c = lin(0.42, 0.43, 0.44), m = EM.Metal, r = 0.06 },
		steel_rail    = { c = lin(0.26, 0.25, 0.24), m = EM.Metal, r = 0.12 },
		steel_dark    = { c = lin(0.08, 0.08, 0.085), m = EM.Metal },
		copper_pipe   = { c = lin(0.22, 0.09, 0.035), m = EM.CorrodedMetal },
		rust          = { c = lin(0.16, 0.07, 0.03), m = EM.CorrodedMetal },
		light_panel   = { c = Color3.fromRGB(255, 250, 240), m = EM.Neon },
		light_strip   = { c = Color3.fromRGB(255, 248, 235), m = EM.Neon },
		sign_white    = { c = lin(0.80, 0.80, 0.79), m = EM.SmoothPlastic },
		sign_dark     = { c = lin(0.045, 0.045, 0.05), m = EM.SmoothPlastic },
		sign_blue     = { c = Color3.fromRGB(0, 72, 140), m = EM.SmoothPlastic },
		emg_red       = { c = lin(0.52, 0.02, 0.02), m = EM.SmoothPlastic },
		emg_yellow    = { c = lin(0.70, 0.50, 0.02), m = EM.SmoothPlastic },
		screen_black  = { c = lin(0.012, 0.012, 0.014), m = EM.SmoothPlastic, r = 0.15 },
		ballast       = { c = lin(0.11, 0.108, 0.105), m = EM.Slate },
		sleeper       = { c = lin(0.20, 0.195, 0.185), m = EM.Concrete },
	}

	---------------------------------------------------------------- hedef klasor
	local parent = C.PARENT
	if parent == nil then
		local root = workspace:FindFirstChild("Marmaray")
		if root == nil then
			root = Instance.new("Folder")
			root.Name = "Marmaray"
			root.Parent = workspace
		end
		local fs = root:FindFirstChild("Stations")
		if fs == nil then
			fs = Instance.new("Folder")
			fs.Name = "Stations"
			fs.Parent = root
		end
		parent = fs
	end

	-- ORIGIN_KM: BuildMarmaray hatti yatayda kaydirmis olabilir; ayni kaydirmayi
	-- uygulamazsak istasyon hattan kopar.
	local originKm = C.ORIGIN_KM
	if originKm == nil then
		local anc = parent
		while anc and anc ~= game and anc.Name ~= "Marmaray" do anc = anc.Parent end
		if anc and anc ~= game then originKm = anc:GetAttribute("OriginKm") end
	end
	local originOffset = Vector3.zero
	if originKm then
		local o = D.positionAtChainage(originKm * 1000, k, V)
		originOffset = Vector3.new(o.X, 0, o.Z)
	end
	local function axisAt(sm)
		return D.positionAtChainage(sm, k, V) - originOffset
	end

	---------------------------------------------------------------- rijit cerceve
	local p0 = axisAt(S_ST)
	local fwd = axisAt(S_ST + PY1) - axisAt(S_ST + PY0)
	fwd = Vector3.new(fwd.X, 0, fwd.Z)       -- peron yatay (bu istasyonda egim 0)
	fwd = (fwd.Magnitude > 1e-5) and fwd.Unit or Vector3.zAxis
	local left = Vector3.yAxis:Cross(fwd)
	left = (left.Magnitude > 1e-5) and left.Unit or Vector3.xAxis
	local BASE = CFrame.lookAt(p0, p0 + fwd, Vector3.yAxis)
	-- Tum yerlesimin dayandigi isaret kurali: BASE'in yerel +X'i TAM olarak
	-- -left olmali (yani yerel X = -x * k dogru). Bozulursa istasyon aynalanir.
	assert((BASE.RightVector + left).Magnitude < 1e-3, "[Yenikapı] yanal eksen isareti bozuk")

	---------------------------------------------------------------- model iskeleti
	local wanted = C.NAME or NAME
	if parent:FindFirstChild(wanted) then
		warn(("[Yenikapı] '%s' zaten var; detayli model '%s_Detay' olarak kuruluyor."):format(wanted, wanted))
		wanted = wanted .. "_Detay"
	end
	local model = Instance.new("Model")
	model.Name = wanted

	local function folder(n)
		local f = Instance.new("Folder")
		f.Name = n
		f.Parent = model
		return f
	end
	local fStruct = folder("Yapi")
	local fFloor  = folder("Zemin")
	local fEdge   = folder("PeronKenari")
	local fCol    = folder("Kolonlar")
	local fCeil   = folder("Tavan")
	local fWall   = folder("Duvarlar")
	local fMural  = folder("Mural")
	local fFit    = folder("Donati")
	local fTrack  = folder("Yol")

	---------------------------------------------------------------- part fabrikasi
	local MIN = 0.05            -- stud; Roblox part alt siniri
	local made = 0
	local function part(name, size, cf, mat, into, opt)
		local p = Instance.new("Part")
		p.Name = name
		p.Anchored = true
		p.Size = Vector3.new(math.max(MIN, size.X), math.max(MIN, size.Y), math.max(MIN, size.Z))
		p.CFrame = cf
		p.Color = mat.c
		p.Material = mat.m
		p.Reflectance = mat.r or 0
		p.TopSurface = Enum.SurfaceType.Smooth
		p.BottomSurface = Enum.SurfaceType.Smooth
		local cc, cs = true, true
		if opt then
			if opt.canCollide ~= nil then cc = opt.canCollide end
			if opt.castShadow ~= nil then cs = opt.castShadow end
			if opt.shape then p.Shape = opt.shape end
			if opt.transparency then p.Transparency = opt.transparency end
			if opt.reflectance then p.Reflectance = opt.reflectance end
		end
		p.CanCollide = cc
		p.CastShadow = cs
		p.Parent = into
		made += 1
		if made % C.YIELD_EVERY == 0 then task.wait() end
		return p
	end

	-- ince kaplama / sus parcalari: carpismaz, golge dusurmez (3700 partta sart)
	-- deco() HER CAGRIDA YENI tablo dondurur; asagidaki sabitler paylasimlidir,
	-- onlara yazan hicbir yer olmamali (bkz. cyl()).
	local function deco(extra)
		local t = { canCollide = false, castShadow = false }
		for key, v in pairs(extra or {}) do t[key] = v end
		return t
	end
	local DECO  = { canCollide = false, castShadow = false }
	local SOLID = { canCollide = true, castShadow = true }
	local NOCOL = { canCollide = false, castShadow = true }

	-- merkez (x yanal, y boyuna, z dusey) + boyut (sx yanal, sy boyuna, sz dusey)
	-- Boyut, partin KENDI eksenlerinde verilir: Size = (sx, sz, sy).
	--   roll      : yanal eksen (yerel X) etrafinda donus — yerel Y/Z duzleminde
	--               (yukari/hat boyu) dondurur; gul pencere kollari, capraz barlar
	--   axis="up" : yerel X -> YUKARI  (silindir ekseni dusey)
	--   axis="fwd": yerel X -> HAT BOYU (silindir ekseni boyuna)
	local function prim(into, name, cx, cy, cz, sx, sy, sz, mat, opt)
		local cf = BASE * CFrame.new(-cx * k, cz * k * V, -cy * k)
		if opt then
			if opt.roll and opt.roll ~= 0 then
				cf = cf * CFrame.Angles(opt.roll, 0, 0)          -- yanal eksen etrafinda
			elseif opt.axis == "up" then
				cf = cf * CFrame.Angles(0, 0, math.pi / 2)       -- silindir ekseni = dusey
			elseif opt.axis == "fwd" then
				cf = cf * CFrame.Angles(0, math.pi / 2, 0)       -- silindir ekseni = hat boyu
			end
		end
		return part(name, Vector3.new(sx * k, sz * k * V, sy * k), cf, mat, into, opt)
	end

	-- iki kose noktasindan kutu (Blender'daki slab() ile ayni imza mantigi)
	local function box(into, name, x0, x1, y0, y1, z0, z1, mat, opt)
		return prim(into, name, (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2,
			math.abs(x1 - x0), math.abs(y1 - y0), math.abs(z1 - z0), mat, opt)
	end

	-- Silindir. opt.axis: "lat" (varsayilan, duvardan disari), "up", "fwd".
	--   len = eksen boyu
	--   d1  = "lat" icin dusey cap, "up" icin yanal cap, "fwd" icin dusey cap
	--   d2  = kesitin diger capi
	-- Uc eksende de prim'e ayni sirayla gider: prim'in boyut eslemesi ile
	-- donusum tam olarak birbirini goturur (bkz. prim).
	-- NOT: V_SCALE ~= 1 iken silindir kesitleri bozulur (dusey olcek caplara da
	-- uygulanir); bu modul V_SCALE = 1 icin tasarlandi.
	local function cyl(into, name, cx, cy, cz, len, d1, d2, mat, opt)
		-- opt KOPYALANIR: DECO gibi paylasilan sabit tablolara shape yazmak
		-- sonraki tum kutulari silindire cevirirdi.
		local t = { shape = Enum.PartType.Cylinder }
		for key, v in pairs(opt or {}) do t[key] = v end
		t.shape = Enum.PartType.Cylinder
		return prim(into, name, cx, cy, cz, len, d2, d1, mat, t)
	end

	-- Dusey yuze SurfaceGui yazi. Yerel +X = SAG = -yanal oldugu icin, YANAL
	-- ARTAN yone bakan yuz NormalId.Left, azalan yone bakan NormalId.Right.
	local function faceId(dir)
		if dir > 0 then return Enum.NormalId.Left end
		return Enum.NormalId.Right
	end
	local function label(p, nid, text, fg, bg, font, lightInf)
		local sg = Instance.new("SurfaceGui")
		sg.Name = "Yazi"
		sg.Face = nid
		sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		sg.PixelsPerStud = 50
		sg.LightInfluence = lightInf or 0
		local tl = Instance.new("TextLabel")
		tl.Size = UDim2.fromScale(1, 1)
		tl.BackgroundTransparency = bg and 0 or 1
		if bg then tl.BackgroundColor3 = bg end
		tl.TextColor3 = fg
		tl.Font = font or Enum.Font.GothamBold
		tl.TextScaled = true
		tl.Text = text
		tl.Parent = sg
		sg.Parent = p
		return sg
	end

	local lightCount = 0
	local function surfaceLight(p, nid, range, brightness)
		if not C.LIGHTS then return nil end
		local sl = Instance.new("SurfaceLight")
		sl.Face = nid
		sl.Range = range or 16
		sl.Brightness = brightness or 2
		sl.Angle = 140
		sl.Color = Color3.fromRGB(255, 248, 238)
		sl.Parent = p
		lightCount += 1
		return sl
	end

	----------------------------------------------------------------------------
	-- 1) PERON GOVDESI + CILALI GRANIT ZEMIN
	----------------------------------------------------------------------------
	-- Peron dolgusu: ustu PLATFORM_TOP-0.02, ray kotunun altina iner.
	local body = box(fStruct, "PeronGovdesi", PX0, PX1, PY0, PY1,
		-1.05, PLAT_TOP - 0.02, M.concrete_pale, SOLID)
	-- Zemin kaplamasi ayri ince katman (malzeme farkli: cilali granit)
	box(fFloor, "ZeminGranit", PX0, PX1, PY0, PY1,
		PLAT_TOP - 0.02, PLAT_TOP, M.floor_granite, SOLID)
	-- Kenar alin yuzeyi (perondan raya bakan dusey yuz)
	box(fStruct, "KenarAlin_Yol1", PX0 - 0.03, PX0, PY0, PY1, -0.10, PLAT_TOP, M.concrete_pale, SOLID)
	box(fStruct, "KenarAlin_Yol2", PX1, PX1 + 0.03, PY0, PY1, -0.10, PLAT_TOP, M.concrete_pale, SOLID)

	-- PV: duz izgara, dekoratif desen yok. 60 cm karo GERCEK derz olarak kuruldu
	-- (prosedurel bump yok). Derz kaplamaya gomulu, 3 mm disari tasar.
	local tiled0, tiled1 = PX0 + EDGE_TOTAL, PX1 - EDGE_TOTAL   -- 3.45 .. 17.95
	if C.FLOOR_JOINTS then
		local jz0, jz1 = PLAT_TOP - 0.027, PLAT_TOP + 0.003
		local nLong = math.floor((tiled1 - tiled0) / TILE)
		for i = 1, nLong - 1 do
			local x = tiled0 + i * TILE
			box(fFloor, ("Derz_Boyuna_%02d"):format(i), x - 0.010, x + 0.010,
				PY0, PY1, jz0, jz1, M.floor_grout, DECO)
		end
		local nTrans = math.floor((PY1 - PY0) / TILE)
		for i = 1, nTrans - 1 do
			local y = PY0 + i * TILE
			box(fFloor, ("Derz_Enine_%03d"):format(i), tiled0, tiled1,
				y - 0.010, y + 0.010, jz0, jz1, M.floor_grout, DECO)
		end
	end

	----------------------------------------------------------------------------
	-- 2) PERON KENARI — DORT BANT
	--    PV: rayin kenarindan iceri dogru beyaz 0.15 -> sari taktil 0.60 ->
	--    turkuaz grafik 0.60 -> turuncu uyari 0.10. Peron kapisi (PSD) YOK.
	----------------------------------------------------------------------------
	local EDGE_BANDS = {
		{ "KenarBeyaz",     0.15, "band_white",   0.002 },
		{ "TaktilSari",     0.60, "band_tactile", 0.006 }, -- PV: kabartma noktali
		{ "GrafikTurkuaz",  0.60, "band_turq",    0.002 },
		{ "UyariTuruncu",   0.10, "band_orange",  0.002 },
	}
	local function edgeBands(xEdge, inward, tag)
		local x = xEdge
		for _, b in ipairs(EDGE_BANDS) do
			local name, w, matkey, lift = b[1], b[2], b[3], b[4]
			local x2 = x + inward * w
			local z1 = PLAT_TOP + lift
			box(fEdge, ("%s_%s"):format(tag, name), math.min(x, x2), math.max(x, x2),
				PY0, PY1, z1 - 0.04, z1, M[matkey], DECO)
			if matkey == "band_turq" then
				-- PV: turkuaz zeminli Iznik/arabesk desenli grafik bant. Desen
				-- AS: tam motif okunamadi; modüler rozet dizisi olarak kuruldu.
				local xc = (x + x2) / 2
				local n = math.floor((PY1 - PY0) / 2.4)
				for i = 0, n - 1 do
					cyl(fEdge, ("%s_IznikRozet_%03d"):format(tag, i), xc,
						PY0 + 1.2 + i * 2.4, z1 - 0.012, 0.030, 0.34, 0.34,
						M.band_turq_lt, deco({ axis = "up" }))
				end
			end
			x = x2
		end
	end
	edgeBands(PX0, 1, "Yol1")    -- bantlar +x yonune
	edgeBands(PX1, -1, "Yol2")   -- bantlar -x yonune

	----------------------------------------------------------------------------
	-- 3) PERON ORTASINDA TEK SIRA DIKDORTGEN KOLON
	--    PV: duvarla ayni sicak bej buyuk format karo, kare izgara derzli.
	--    Kameraya en yakin oge oldugu icin derz GERCEK GEOMETRI: koyu derz
	--    govdesi + govdeden disari tasan karo plakalari.
	----------------------------------------------------------------------------
	local nCol = math.floor((PY1 - PY0) / COL_PITCH)                    -- 32
	local col0Y = PY0 + ((PY1 - PY0) - (nCol - 1) * COL_PITCH) / 2      -- -106.25
	local REVEAL = 0.015   -- karo plakasinin govdeden tasma payi (Roblox min olcu)
	local GAP = 0.012      -- karolar arasi derz bosluğu (her kenarda)
	local TW, TH = 0.60, 0.90                                           -- karo modulu

	local function cladColumn(idx, yc)
		local x0, x1 = PLAT_MID - COL_W / 2, PLAT_MID + COL_W / 2
		local y0, y1 = yc - COL_D / 2, yc + COL_D / 2
		local z0, z1 = PLAT_TOP, CEIL_Z
		local tag = ("Kolon_%02d"):format(idx)
		box(fCol, tag .. "_Govde", x0, x1, y0, y1, z0, z1, M.tile_grout, SOLID)
		-- PV: kolon dibinde koyu su basman bandi
		box(fCol, tag .. "_SuBasman", x0 - 0.015, x1 + 0.015, y0 - 0.015, y1 + 0.015,
			z0, z0 + 0.12, M.concrete_raw, NOCOL)
		local nz = math.max(1, math.floor((z1 - z0) / TH + 0.5))        -- 5 sira
		local thAct = (z1 - z0) / nz
		-- dort dusey yuz: yanal bakan ikisi (boyu COL_D), boyuna bakan ikisi (COL_W)
		local faces = {
			{ "Xm", "x", x0, -1, y0, y1 },
			{ "Xp", "x", x1,  1, y0, y1 },
			{ "Ym", "y", y0, -1, x0, x1 },
			{ "Yp", "y", y1,  1, x0, x1 },
		}
		for _, fdef in ipairs(faces) do
			local fname, kind, const, dir, a0, a1 = fdef[1], fdef[2], fdef[3], fdef[4], fdef[5], fdef[6]
			local span = a1 - a0
			local nt = math.max(1, math.floor(span / TW + 0.5))
			local twAct = span / nt
			for i = 0, nt - 1 do
				for row = 0, nz - 1 do
					local p0 = a0 + i * twAct + GAP
					local p1 = a0 + (i + 1) * twAct - GAP
					local q0 = z0 + row * thAct + GAP
					local q1 = z0 + (row + 1) * thAct - GAP
					local nm = ("%s_Karo%s_%02d_%02d"):format(tag, fname, i, row)
					if kind == "x" then
						box(fCol, nm, const, const + dir * REVEAL, p0, p1, q0, q1, M.tile_beige, NOCOL)
					else
						box(fCol, nm, p0, p1, const, const + dir * REVEAL, q0, q1, M.tile_beige, NOCOL)
					end
				end
			end
		end
	end
	for i = 0, nCol - 1 do
		cladColumn(i, col0Y + i * COL_PITCH)
	end

	----------------------------------------------------------------------------
	-- 5) RAY TARAFINDA GENIS DUZ ALINLIK (FASCIA) + SERIT ARMATUR
	--    REFERANS: tavan lamelleri ile ray duvari arasinda GENIS DUZ panel;
	--    serit armatur onun ALT kenarina monte (tavanin en okunakli 2. ogesi).
	----------------------------------------------------------------------------
	local function fascia(x0, x1, height, tag)
		local zTop = CEIL_Z
		box(fCeil, tag .. "_Panel", x0, x1, PY0, PY1, zTop - height, zTop, M.fascia_grey, NOCOL)
		local z = zTop - height - 0.07
		box(fCeil, tag .. "_ArmaturKutu", x0 + 0.02, x1 - 0.02, PY0, PY1, z, z + 0.07, M.metal_galv, DECO)
		box(fCeil, tag .. "_ArmaturLens", x0 + 0.04, x1 - 0.04, PY0, PY1, z - 0.03, z, M.light_strip, DECO)
	end
	fascia(PX0 + 0.55, PX0 + 0.95, 1.15, "Alinlik_Yol1")   -- genis
	fascia(PX1 - 0.35, PX1, 0.80, "Alinlik_Yol2")          -- karsi tarafta daha dar

	----------------------------------------------------------------------------
	-- 4) TAVAN — LAMEL (BAFL) + DERIN SERVIS BOSLUGU
	--    REFERANS: genis duz bicaklar peron aksina DIK; ARALIK lamelden buyuk,
	--    aralardan ustteki koyu servis boslugu ve icindeki tavalar/kanallar
	--    gorunuyor. Bu, referansin en belirgin tavan ozelligi.
	----------------------------------------------------------------------------
	local CX0, CX1 = PX0 + 0.95, PX1 - 0.35     -- lamel tavanin yanal siniri
	local BW, GAPB, BDEPTH = 0.18, 0.26, 0.16
	local PITCH = BW + GAPB                      -- 0.44
	local PLENUM = 1.05                          -- lamel ustundeki servis boslugu
	local nBaf = math.max(1, math.floor((PY1 - PY0) / PITCH))     -- 554
	for i = 0, nBaf - 1 do
		local y = PY0 + i * PITCH
		box(fCeil, ("Lamel_%03d"):format(i), CX0, CX1, y, y + BW,
			CEIL_Z - BDEPTH, CEIL_Z, M.metal_baffle, DECO)
	end
	-- PV: isikli paneller lamel tavana GOMULU — isik yuzeyi lamel ALT yuzuyle
	-- ayni duzlemde, yoksa asagiya hic isik dusmez. REFERANS: panel tavanin
	-- KUCUK bir kismi; cogunlugu gri lamel.
	local panelEvery, nPanel = 24, 0
	do
		local span = PITCH * 3.0
		local y = PY0 + PITCH * 2
		while y + span < PY1 do
			-- 12 mm asagi kacirildi: panelin alt yuzu lamel alt yuzuyle TAM ayni
			-- duzlemde olursa Roblox'ta z-fighting yapiyor.
			local p = box(fCeil, ("IsikliPanel_%03d"):format(nPanel), CX0 + 1.2, CX1 - 1.2,
				y, y + span, CEIL_Z - BDEPTH - 0.012, CEIL_Z - BDEPTH + 0.008, M.light_panel, DECO)
			if nPanel % 3 == 0 then surfaceLight(p, Enum.NormalId.Bottom, 22, 2.2) end
			nPanel += 1
			y += PITCH * panelEvery
		end
	end
	-- Servis boslugu: lamellerin COK uzerinde strüktürel tavan + tesisat
	box(fCeil, "ServisTavani", CX0, CX1, PY0, PY1,
		CEIL_Z + PLENUM, CEIL_Z + PLENUM + 0.25, M.concrete_raw, NOCOL)
	do
		local nb = math.max(1, math.floor((PY1 - PY0) / 2.4))
		local xm = (CX0 + CX1) / 2
		for i = 0, nb - 1 do
			local y = PY0 + i * 2.4
			box(fCeil, ("ServisKiris_%03d"):format(i), CX0, CX1, y, y + 0.11,
				CEIL_Z + PLENUM - 0.26, CEIL_Z + PLENUM, M.steel_dark, DECO)
			box(fCeil, ("LamelAski_%03d"):format(i), xm - 0.02, xm + 0.02, y, y + 0.04,
				CEIL_Z, CEIL_Z + PLENUM - 0.26, M.steel_dark, DECO)
		end
	end
	-- PV: kablo tavalari + havalandirma kanali (aralardan gorunen tesisat)
	local function cableTray(into, x0, x1, y0, y1, z, tag)
		box(into, tag .. "_Taban", x0, x1, y0, y1, z, z + 0.02, M.metal_galv, DECO)
		box(into, tag .. "_KenarA", x0, x0 + 0.02, y0, y1, z, z + 0.07, M.metal_galv, DECO)
		box(into, tag .. "_KenarB", x1 - 0.02, x1, y0, y1, z, z + 0.07, M.metal_galv, DECO)
	end
	cableTray(fCeil, CX0 + 1.0, CX0 + 1.5, PY0, PY1, CEIL_Z + PLENUM - 0.40, "ServisTava1")
	cableTray(fCeil, CX1 - 1.5, CX1 - 1.0, PY0, PY1, CEIL_Z + PLENUM - 0.40, "ServisTava2")
	box(fCeil, "ServisKanal", (CX0 + CX1) / 2 - 0.45, (CX0 + CX1) / 2 + 0.45, PY0, PY1,
		CEIL_Z + PLENUM - 0.62, CEIL_Z + PLENUM - 0.18, M.metal_galv, DECO)

	-- Genel aydinlatma: lamel altinda 20 m'de bir nokta isik (Neon yuzeyler tek
	-- basina mekani aydinlatmaz; yuzlerce isik ise performansi dusurur).
	if C.LIGHTS then
		local nL = math.floor((PY1 - PY0) / 20)
		for i = 0, nL do
			local anchor = box(fCeil, ("MekanIsik_%02d"):format(i), PLAT_MID - 0.08, PLAT_MID + 0.08,
				PY0 + i * 20 - 0.08, PY0 + i * 20 + 0.08, CEIL_Z - BDEPTH - 0.02, CEIL_Z - BDEPTH,
				M.light_panel, DECO)
			local pl = Instance.new("PointLight")
			pl.Range = 42
			pl.Brightness = 1.6
			pl.Color = Color3.fromRGB(255, 250, 240)
			pl.Parent = anchor
			lightCount += 1
		end
	end

	----------------------------------------------------------------------------
	-- 6) DUVARLAR — RAY TARAFI HAM KOYU BETON
	--    PV: iki ayri duvar dili. Peron tarafi bej karo (kolonlar), ray tarafi
	--    kaplamasiz koyu puskurtme beton + duzenli kalip derzleri, ankraj izleri,
	--    dipte surekli kablo/boru hatti ve dusey paslanmis inis borusu.
	----------------------------------------------------------------------------
	local W1X = TRACK1_X - 2.40      -- Yol 1 duvarinin peron tarafina bakan yuzu
	local W2X = TRACK2_X + 2.40      -- Yol 2 duvarinin peron tarafina bakan yuzu
	box(fWall, "Duvar_Yol1", W1X - 0.20, W1X, PY0, PY1, -0.60, WALL_TOP, M.concrete_raw, SOLID)
	box(fWall, "Duvar_Yol2", W2X, W2X + 0.20, PY0, PY1, -0.60, WALL_TOP, M.concrete_raw, SOLID)

	-- Duvar yuzeyine monte her sey YOLUN ICINE dogru tasar: Yol 1 duvarinda
	-- +x yonune (W1X -> W1X+d), Yol 2 duvarinda -x yonune (W2X-d -> W2X).
	-- (Mural da ayni mantikla W1X'in onunde, XF = W1X + 0.06'da duruyor.)
	-- kalip/panel derzleri + ankraj plakalari (gorunur yuz: Yol 1 duvari)
	do
		local n1 = math.floor((PY1 - PY0) / 2.4)
		for i = 0, n1 do
			local y = PY0 + i * 2.4
			box(fWall, ("Duvar1_Derz_%03d"):format(i), W1X, W1X + 0.04, y - 0.015, y + 0.015,
				-0.60, WALL_TOP, M.concrete_seam, DECO)
		end
		box(fWall, "Duvar1_DerzYatay", W1X, W1X + 0.04, PY0, PY1, 2.58, 2.62, M.concrete_seam, DECO)
		local n2 = math.floor((PY1 - PY0) / 4.8)
		for i = 0, n2 do
			local y = PY0 + 2.4 + i * 4.8
			for r, z in ipairs({ 1.60, 4.20 }) do
				box(fWall, ("Duvar1_Ankraj_%03d_%d"):format(i, r), W1X, W1X + 0.06,
					y - 0.09, y + 0.09, z - 0.09, z + 0.09, M.rust, DECO)
			end
			box(fWall, ("Duvar2_Derz_%03d"):format(i), W2X - 0.04, W2X, y - 0.015, y + 0.015,
				-0.60, WALL_TOP, M.concrete_seam, DECO)
		end
	end
	-- PV: duvar dibinde 2-3 sirali bakir/kahverengi boru-kablo hatti + kelepceler
	for r, z in ipairs({ 0.18, 0.38, 0.56 }) do
		cyl(fWall, ("Duvar1_Boru_%d"):format(r), W1X + 0.09, (PY0 + PY1) / 2, z,
			PY1 - PY0, 0.075, 0.075, M.copper_pipe, deco({ axis = "fwd" }))
		cyl(fWall, ("Duvar2_Boru_%d"):format(r), W2X - 0.09, (PY0 + PY1) / 2, z,
			PY1 - PY0, 0.075, 0.075, M.copper_pipe, deco({ axis = "fwd" }))
	end
	do
		local nc = math.floor((PY1 - PY0) / 3.0)
		for i = 0, nc do
			local y = PY0 + i * 3.0
			box(fWall, ("Duvar1_Kelepce_%03d"):format(i), W1X, W1X + 0.14, y - 0.03, y + 0.03,
				0.10, 0.64, M.metal_galv, DECO)
		end
	end
	-- PV: dusey paslanmis celik inis borusu
	for i, y in ipairs({ -68.0, 58.0 }) do
		cyl(fWall, ("Duvar1_InisBorusu_%d"):format(i), W1X + 0.11, y, (WALL_TOP - 0.60) / 2,
			WALL_TOP + 0.60, 0.16, 0.16, M.rust, deco({ axis = "up" }))
	end

	-- PV: ray ustu kaplamasiz koyu beton kutu tavan + acikta kablo tavalari
	for _, tdef in ipairs({ { "1", TRACK1_X }, { "2", TRACK2_X } }) do
		local tag, xc = tdef[1], tdef[2]
		box(fWall, "RayTavani_Yol" .. tag, xc - 2.40, xc + 2.40, PY0, PY1,
			WALL_TOP - 0.35, WALL_TOP, M.concrete_raw, NOCOL)
		cableTray(fWall, xc - 2.30, xc - 1.90, PY0, PY1, WALL_TOP - 0.62, "RayTava" .. tag)
	end
	-- PV: ray duvari dibinde servis yuruyus seridi
	box(fTrack, "ServisYolu_Yol1", TRACK1_X - 2.40, TRACK1_X - 1.95, PY0, PY1, -0.60, -0.42, M.concrete_pale, SOLID)
	box(fTrack, "ServisYolu_Yol2", TRACK2_X + 1.95, TRACK2_X + 2.40, PY0, PY1, -0.60, -0.42, M.concrete_pale, SOLID)

	----------------------------------------------------------------------------
	-- 7) DEV SERAMIK ROLYEF MURAL — Yol 1 duvarinda
	--    PV (ARCHITECTURAL_ANALYSIS -> "sanat eseri / mural"): modüler pismis
	--    toprak/seramik rolyef karolarin KOLAJI — amfora ve testiler, gemi
	--    iskeleti-kaburga ve halat dokulari, dalgali su panelleri, Iznik tipi
	--    cini bloklar, rozet madalyon frizleri, oyma kemer icinde figur rolyefi,
	--    buyuk radyal gul pencere motifi, aralara gomulu kazi fotograflari.
	--    Tema: Yenikapı kazilari / Theodosius Limani.
	--    REFERANS: eserin TAMAMI bakir/terrakota ailesinde — turkuaz DEGIL.
	--    Derinlik farki renkle degil ISIK-GOLGE ile okunur.
	--    AS: her ogenin tam konumu/olcusu; tam cerceveli cekim yok, duzen
	--    "kolaj" mantigina gore kurgulandi, modüler karo izgarasina oturtuldu.
	----------------------------------------------------------------------------
	local XF = TRACK1_X - 2.34                   -- mural on yuzu
	local MY0, MY1 = -MURAL_LEN / 2, MURAL_LEN / 2
	local TM = 0.45                              -- AS: seramik karo modulu
	local SPAN = MY1 - MY0

	-- Roblox'ta bump/normal map yok: milimetrik rolyef hic okunmaz. Kucuk
	-- derinlikler buyutulur, zaten derin olanlar aynen kalir (tavan 0.06 m).
	local function rel(d)
		return math.max(d, math.min(d * 2.0, 0.06))
	end
	local function q(v)                          -- karo izgarasina yuvarla
		return math.floor(v / TM + 0.5) * TM
	end
	local function blk(name, ya, yb, za, zb, depth, mat)
		return box(fMural, name, XF, XF + rel(depth), q(ya), q(yb),
			MZ0 + MURAL_H * za, MZ0 + MURAL_H * zb, mat, DECO)
	end

	box(fMural, "Mural_Cerceve", TRACK1_X - 2.41, TRACK1_X - 2.33,
		MY0 - 0.16, MY1 + 0.16, MZ0 - 0.16, MZ1 + 0.16, M.mural_frame, NOCOL)
	box(fMural, "Mural_Zemin", TRACK1_X - 2.40, XF, MY0, MY1, MZ0, MZ1, M.cu_deep, NOCOL)

	-- --- taban: Iznik cini blok alani (modüler sahmerdan dizilim)
	do
		local ny = math.floor(SPAN / TM)                       -- 93
		local nz = math.max(3, math.floor(MURAL_H / TM))       -- 5
		for iy = 0, ny - 1 do
			for iz = 0, nz - 1 do
				if (iy + iz) % 3 == 0 then                     -- seyrek desen vurgusu
					local yb = MY0 + iy * TM
					local zb = iz / nz
					box(fMural, ("MR_Iznik_%03d_%d"):format(iy, iz), XF, XF + rel(0.014),
						yb, yb + TM * 0.92,
						MZ0 + MURAL_H * zb, MZ0 + MURAL_H * (zb + 0.92 / nz),
						(iy % 2 == 1) and M.cu_mid or M.cu_deep, DECO)
				end
			end
		end
	end

	-- --- rozet madalyon frizleri (alt ve ust yatay bant)
	for fi, zf in ipairs({ 0.06, 0.90 }) do
		blk(("MR_FrizBant_%d"):format(fi), MY0, MY1, zf, zf + 0.075, 0.022, M.cu_light)
		local nMed = math.floor(SPAN / (TM * 2))               -- 46
		for i = 0, nMed - 1 do
			cyl(fMural, ("MR_Madalyon_%d_%03d"):format(fi, i), XF + 0.030,
				q(MY0 + TM) + i * TM * 2, MZ0 + MURAL_H * (zf + 0.037),
				rel(0.030), TM * 0.68, TM * 0.68, M.cu, DECO)
		end
	end

	-- --- amfora ve testiler (sol ucte gruplu, farkli boy)
	for i = 0, 8 do
		local yy = q(MY0 + 2.2 + i * 1.35)
		local h = 0.17 + 0.055 * ((i * 7) % 3)
		local zc = 0.30 + 0.10 * ((i * 5) % 3)
		local zAbs = MZ0 + MURAL_H * zc
		-- govde: dar-uzun amfora (Blender'da scale (1, 0.72, 1.35))
		cyl(fMural, ("MR_Amfora_%d"):format(i), XF + 0.038, yy, zAbs,
			0.075, 2 * h * 1.35, 2 * h * 0.72, M.cu, DECO)
		cyl(fMural, ("MR_AmforaBoyun_%d"):format(i), XF + 0.030, yy, zAbs + h * 1.25,
			rel(0.055), 2 * h * 0.26, 2 * h * 0.26, M.cu, DECO)
	end

	-- --- gemi iskeleti: omurga + kaburgalar + halat dokusu (orta bolum)
	do
		local ky = q(MY0 + SPAN * 0.42)
		blk("MR_Omurga", ky - 4.0, ky + 4.0, 0.16, 0.205, 0.030, M.cu_rope)
		for i = 0, 12 do
			local ry = ky - 3.6 + i * 0.60
			local hh = 0.34 - math.abs(i - 6) * 0.028          -- ortada yuksek
			box(fMural, ("MR_Kaburga_%02d"):format(i), XF, XF + rel(0.026), ry, ry + 0.085,
				MZ0 + MURAL_H * 0.20, MZ0 + MURAL_H * (0.20 + hh), M.cu_rope, DECO)
		end
		for i = 0, 25 do
			cyl(fMural, ("MR_Halat_%02d"):format(i), XF + 0.028, ky - 3.9 + i * 0.30,
				MZ0 + MURAL_H * 0.145, rel(0.028), 0.090, 0.090, M.cu_rope, DECO)
		end
	end

	-- --- dalgali su panelleri (alt bant, kademeli)
	for i = 0, 5 do
		local ya = MY0 + SPAN * (0.52 + 0.055 * i)
		blk(("MR_Dalga_%d"):format(i), ya, ya + SPAN * 0.05,
			0.10, 0.10 + 0.055 * (1 + i % 3), 0.018, M.cu_patina)
	end

	-- --- oyma kemer icinde figur rolyefi
	do
		local ay = q(MY0 + SPAN * 0.72)
		blk("MR_KemerArka", ay - 1.35, ay + 1.35, 0.17, 0.80, 0.020, M.cu_light)
		for i = 0, 10 do
			local ang = math.pi * (i / 10.0)
			local yy = ay - 1.2 * math.cos(ang)
			local zz = 0.62 + 0.16 * math.sin(ang)
			box(fMural, ("MR_KemerTas_%02d"):format(i), XF, XF + rel(0.038),
				yy - 0.10, yy + 0.10,
				MZ0 + MURAL_H * zz, MZ0 + MURAL_H * (zz + 0.07), M.cu_light, DECO)
		end
		blk("MR_Figur", ay - 0.26, ay + 0.26, 0.24, 0.60, 0.052, M.cu)
		cyl(fMural, "MR_FigurBas", XF + 0.052, ay, MZ0 + MURAL_H * 0.655,
			rel(0.055), 0.34, 0.34, M.cu, DECO)
	end

	-- --- buyuk radyal gul pencere motifi
	do
		local gy = q(MY0 + SPAN * 0.26)
		local gz = MZ0 + MURAL_H * 0.54
		local R = MURAL_H * 0.30
		-- ROBLOX DUZELTMESI: cember Blender'da kollarin ONUNDE duran dolu disk;
		-- burada arkaya alindi, yoksa kollari ve gobek kismini orter. Arka
		-- diskin derinligi de rel() ile buyutulmuyor: buyurse kollari yutuyor,
		-- kollarin on yuzu XF+0.056'da ve disk XF+0.036'da bitmeli.
		cyl(fMural, "MR_GulCember", XF + 0.006, gy, gz, 0.024, R * 2.12, R * 2.12, M.cu_light, DECO)
		cyl(fMural, "MR_GulArka", XF + 0.018, gy, gz, 0.036, R * 2, R * 2, M.cu_light, DECO)
		for i = 0, 15 do                                       -- 16 radyal oyma kol
			local a = math.pi * i / 16
			box(fMural, ("MR_GulKol_%02d"):format(i), XF + 0.034, XF + 0.056,
				gy - R * 0.80, gy + R * 0.80, gz - 0.035, gz + 0.035, M.cu, deco({ roll = a }))
		end
		cyl(fMural, "MR_GulGobek", XF + 0.055, gy, gz, rel(0.060), R * 0.34, R * 0.34, M.cu, DECO)
	end

	-- --- aralara gomulu kazi fotograflari (cerceveli koyu panolar)
	for i = 0, 4 do
		local py = q(MY0 + SPAN * (0.12 + 0.16 * i))
		blk(("MR_FotoCerceve_%d"):format(i), py - 0.42, py + 0.42, 0.40, 0.66, 0.016, M.cu_light)
		blk(("MR_Foto_%d"):format(i), py - 0.36, py + 0.36, 0.43, 0.63, 0.020, M.excav_photo)
	end

	-- --- murala OZEL surekli serit armatur (eseri yikamak icin)
	do
		local z = MZ1 + 0.18
		box(fMural, "MuralArmatur_Kutu", TRACK1_X - 2.42, TRACK1_X - 2.20, MY0, MY1,
			z, z + 0.06, M.metal_galv, DECO)
		local nSeg = 7
		for i = 0, nSeg - 1 do
			local y0 = MY0 + i * (SPAN / nSeg)
			local lens = box(fMural, ("MuralArmatur_Lens_%d"):format(i),
				TRACK1_X - 2.415, TRACK1_X - 2.205, y0, y0 + SPAN / nSeg,
				z - 0.03, z, M.light_strip, DECO)
			surfaceLight(lens, Enum.NormalId.Bottom, 14, 2.6)
		end
	end

	----------------------------------------------------------------------------
	-- 8) DONATI
	--    PV: beyaz zeminli 'YENİKAPI' panosu (ust kenarinda ince koyu bant),
	--    kirmizi-beyaz SIGARA ICILMEZ, sari kare '4' peron numarasi, gri kutu
	--    icinde sari govdeli kirmizi mantar basli acil durum butonu, siyah
	--    cerceveli yatay bilgi ekranlari, tavandan sarkan yonlendirme levhasi.
	--    Peronda arka duvar yok (ada peron): karo yuzey = kolon yuzu.
	----------------------------------------------------------------------------
	local colA = col0Y + COL_PITCH * math.floor(nCol / 2)        -- 13.75
	local colB = colA + COL_PITCH                                -- 21.25
	local XR = PLAT_MID + COL_W / 2                              -- 11.15 (+x yuzu)
	local XL = PLAT_MID - COL_W / 2                              -- 10.25 (-x yuzu)

	-- istasyon adi panosu (1.30 m: 2.40 m Blender varsayilani kolon yuzunden tasiyordu)
	do
		local w, h, t = 1.30, 0.52, 0.035
		local z = PLAT_TOP + 2.35
		local plate = box(fFit, "AdPanosu", XR, XR + t, colA - w / 2, colA + w / 2,
			z - h / 2, z + h / 2, M.sign_white, NOCOL)
		label(plate, faceId(1), "YENİKAPI", M.sign_dark.c, nil, Enum.Font.GothamBold, 0.15)
		box(fFit, "AdPanosu_UstBant", XR + t, XR + t + 0.014, colA - w / 2, colA + w / 2,
			z + h / 2 - 0.055, z + h / 2, M.sign_dark, DECO)
	end

	-- SIGARA ICILMEZ (kirmizi halka + capraz bar) — kolonun -x yuzunde
	do
		local s, z = 0.45, PLAT_TOP + 2.50
		box(fFit, "SigaraIcilmez", XL - 0.030, XL, colA - s / 2, colA + s / 2,
			z - s / 2, z + s / 2, M.sign_white, NOCOL)
		cyl(fFit, "SigaraIcilmez_Halka", XL - 0.042, colA, z, 0.016, 0.36, 0.36, M.emg_red, DECO)
		cyl(fFit, "SigaraIcilmez_Ic", XL - 0.050, colA, z, 0.016, 0.28, 0.28, M.sign_white, DECO)
		-- katmanlar one dogru siralanir (daha kucuk x = peronun -x tarafina bakan yuz)
		box(fFit, "SigaraIcilmez_Sigara", XL - 0.062, XL - 0.058, colA - 0.11, colA + 0.11,
			z - 0.018, z + 0.018, M.sign_dark, DECO)
		box(fFit, "SigaraIcilmez_Capraz", XL - 0.068, XL - 0.062, colA - 0.17, colA + 0.17,
			z - 0.022, z + 0.022, M.emg_red, deco({ roll = math.pi / 4 }))
		local txt = box(fFit, "SigaraIcilmez_Yazi", XL - 0.034, XL, colA - 0.30, colA + 0.30,
			z - s / 2 - 0.17, z - s / 2 - 0.02, M.sign_white, DECO)
		label(txt, faceId(-1), "SİGARA İÇİLMEZ", M.emg_red.c, nil, Enum.Font.GothamBold, 0.15)
	end

	-- sari kare '4' peron numarasi
	do
		local s, z = 0.55, PLAT_TOP + 1.60
		local p = box(fFit, "PeronNo4", XL - 0.030, XL, colA - s / 2, colA + s / 2,
			z - s / 2, z + s / 2, M.emg_yellow, NOCOL)
		label(p, faceId(-1), "4", M.sign_dark.c, nil, Enum.Font.GothamBlack, 0.15)
	end

	-- acil durum butonu (gri kutu + sari govde + kirmizi mantar bas)
	do
		local bw, bh, bd = 0.22, 0.30, 0.11
		local y, z = colA - 0.45, PLAT_TOP + 1.35
		box(fFit, "AcilButon_Kutu", XR, XR + bd, y - bw / 2, y + bw / 2,
			z - bh / 2, z + bh / 2, M.metal_galv, NOCOL)
		box(fFit, "AcilButon_Govde", XR + bd - 0.02, XR + bd + 0.01, y - 0.075, y + 0.075,
			z - 0.09, z + 0.09, M.emg_yellow, DECO)
		cyl(fFit, "AcilButon_Mantar", XR + bd + 0.040, y, z + 0.01, 0.030, 0.056, 0.056,
			M.emg_red, DECO)
		local lbl = box(fFit, "AcilButon_Levha", XR, XR + 0.012, y - 0.14, y + 0.14,
			z + bh / 2 + 0.03, z + bh / 2 + 0.25, M.emg_red, DECO)
		label(lbl, faceId(1), "ACİL TREN DURDURMA", Color3.new(1, 1, 1), nil, Enum.Font.GothamBold, 0.15)
	end

	-- bilgi ekranlari: kolon yuzunde (1.30 m) ve ray duvarinda (2.00 m)
	local function wallScreen(name, x, y, z, w, h, dir, into)
		local frame = box(into, name .. "_Cerceve", x, x + dir * 0.07, y - w / 2, y + w / 2,
			z - h / 2, z + h / 2, M.steel_dark, NOCOL)
		local pnl = box(into, name .. "_Panel", x + dir * 0.07, x + dir * 0.082,
			y - w / 2 + 0.03, y + w / 2 - 0.03, z - h / 2 + 0.03, z + h / 2 - 0.03,
			M.screen_black, DECO)
		label(pnl, faceId(dir), "YENİKAPI  ·  B1\nGEBZE      3 dk\nHALKALI     6 dk",
			Color3.fromRGB(255, 196, 60), nil, Enum.Font.Code, 0)
		return frame, pnl
	end
	wallScreen("EkranKolon", XR, colB, PLAT_TOP + 2.30, 1.30, 0.58, 1, fFit)
	wallScreen("EkranDuvar", W1X, 24.0, MZ1 + 0.95, 2.00, 0.58, 1, fFit)

	-- PV: peron ortasinda tavandan sarkan kucuk mavi-beyaz yonlendirme levhasi
	do
		local y, z = colA - 3.6, CEIL_Z - BDEPTH - 0.62
		box(fFit, "Yonlendirme_Aski1", PLAT_MID - 0.52, PLAT_MID - 0.48, y - 0.02, y + 0.02,
			z + 0.22, CEIL_Z - BDEPTH, M.steel_dark, DECO)
		box(fFit, "Yonlendirme_Aski2", PLAT_MID + 0.48, PLAT_MID + 0.52, y - 0.02, y + 0.02,
			z + 0.22, CEIL_Z - BDEPTH, M.steel_dark, DECO)
		for _, dir in ipairs({ 1, -1 }) do
			local p = box(fFit, ("Yonlendirme_Pano_%s"):format(dir > 0 and "A" or "B"),
				PLAT_MID, PLAT_MID + dir * 0.012, y - 0.70, y + 0.70,
				z - 0.20, z + 0.22, M.sign_blue, DECO)
			label(p, faceId(dir), "↑ Akşemsettin   Ⓜ", Color3.new(1, 1, 1), nil, Enum.Font.GothamBold, 0.1)
		end
	end

	----------------------------------------------------------------------------
	-- 9) YOL + KATENER
	--    PV: istasyon icinde BALASTLI yol (slab track degil) ve tavan altinda
	--    gorunur havai hat; ucuncu ray YOK.
	----------------------------------------------------------------------------
	if C.TRACK then
		-- PV: traversler arasi bosluk, travers genisliginin ~1.5-2 kati
		local railH, slH, slW, slLen = 0.172, 0.20, 0.26, 2.50
		for _, tdef in ipairs({ { "1", TRACK1_X }, { "2", TRACK2_X } }) do
			local tag, xc = tdef[1], tdef[2]
			box(fTrack, "Balast_Yol" .. tag, xc - 1.90, xc + 1.90, PY0, PY1,
				-railH - slH - 0.30, -railH - slH, M.ballast, SOLID)
			local n = math.floor((PY1 - PY0) / 0.60)
			for i = 0, n - 1 do
				local y = PY0 + i * 0.60
				box(fTrack, ("Travers_Yol%s_%03d"):format(tag, i), xc - slLen / 2, xc + slLen / 2,
					y, y + slW, -railH - slH, -railH, M.sleeper, NOCOL)
			end
			for _, sd in ipairs({ { -1, "L" }, { 1, "R" } }) do
				local rx = xc + sd[1] * D.Gauge / 2
				box(fTrack, ("Ray%s_Yol%s"):format(sd[2], tag), rx - 0.0085, rx + 0.0085,
					PY0, PY1, -railH + 0.03, -0.028, M.steel_rail, NOCOL)
				box(fTrack, ("RayBasi%s_Yol%s"):format(sd[2], tag), rx - 0.0355, rx + 0.0355,
					PY0, PY1, -0.028, 0.0, M.steel_rail, SOLID)
				box(fTrack, ("RayTabani%s_Yol%s"):format(sd[2], tag), rx - 0.075, rx + 0.075,
					PY0, PY1, -railH, -railH + 0.03, M.steel_rail, NOCOL)
			end
		end
	end

	if C.CATENARY then
		local zWire = WALL_TOP - 1.05
		-- Konsol her yolda KENDI ray duvarindan cikar (Blender'da ikisi de -X idi)
		for _, tdef in ipairs({ { "1", TRACK1_X, -1 }, { "2", TRACK2_X, 1 } }) do
			local tag, xc, side = tdef[1], tdef[2], tdef[3]
			box(fTrack, "Katener" .. tag .. "_TasiyiciTel", xc - 0.012, xc + 0.012, PY0, PY1,
				zWire + 0.42, zWire + 0.45, M.steel_dark, DECO)
			box(fTrack, "Katener" .. tag .. "_TemasTeli", xc - 0.014, xc + 0.014, PY0, PY1,
				zWire, zWire + 0.028, M.steel_rail, DECO)
			local pitch = 12.0                                   -- AS
			local n = math.max(1, math.floor((PY1 - PY0) / pitch))
			for i = 0, n - 1 do
				local y = PY0 + 2.0 + i * pitch
				local xa, xb = xc + side * 2.35, xc - side * 0.05
				box(fTrack, ("Katener%s_Konsol_%02d"):format(tag, i), math.min(xa, xb), math.max(xa, xb),
					y, y + 0.08, zWire + 0.50, zWire + 0.58, M.metal_galv, DECO)
				for j = 0, 3 do
					local dy = y + j * (pitch / 4)
					box(fTrack, ("Katener%s_Aski_%02d_%d"):format(tag, i, j),
						xc - 0.008, xc + 0.008, dy, dy + 0.02,
						zWire + 0.028, zWire + 0.42, M.steel_dark, DECO)
				end
			end
		end
	end

	----------------------------------------------------------------------------
	-- model kapanisi
	----------------------------------------------------------------------------
	model.PrimaryPart = body
	do
		local bb = Instance.new("BillboardGui")
		bb.Size = UDim2.fromOffset(260, 50)
		bb.StudsOffset = Vector3.new(0, 14, 0)
		bb.AlwaysOnTop = true
		bb.MaxDistance = 3000
		local tl = Instance.new("TextLabel")
		tl.Size = UDim2.fromScale(1, 1)
		tl.BackgroundColor3 = Color3.fromRGB(0, 70, 140)
		tl.TextColor3 = Color3.new(1, 1, 1)
		tl.TextScaled = true
		tl.Font = Enum.Font.GothamBold
		tl.Text = ("%d · %s (%+.0f m)"):format(st.no, NAME, st.railTop)
		tl.Parent = bb
		bb.Parent = body
	end
	for key, v in pairs(st) do
		if type(v) ~= "table" then model:SetAttribute(key, v) end
	end
	model:SetAttribute("PlatformType", lay.type)
	model:SetAttribute("Detail", true)
	model:SetAttribute("StudsPerMeter", k)
	model:SetAttribute("VScale", V)
	model:SetAttribute("OriginKm", originKm)
	model:SetAttribute("PartCount", made)
	model:SetAttribute("Columns", nCol)
	model:SetAttribute("CeilingBaffles", nBaf)
	model:SetAttribute("LightPanels", nPanel)
	model:SetAttribute("Source", "blender/stations/yenikapi.py + kit.py")
	model.Parent = parent

	if C.VERBOSE then
		print(("[Yenikapı] peron kati kuruldu: %d part, %d kolon, %d lamel, %d isikli panel, %d isik kaynagi")
			:format(made, nCol, nBaf, nPanel, lightCount))
	end
	return model
end
