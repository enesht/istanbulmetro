--[[
BosphorusGlass (ModuleScript)  —  Boğaz batırma tüpü "CAM TÜP" sahnesi

NEDEN
  Marmaray inşa edilirken halkın büyük kısmı denizin altından geçerken camdan
  denizi/okyanusu göreceğini sandı. Bu sahne o halk hayalini BİLEREK gerçekleştirir;
  gerçekçilik hedefi yoktur. Oyunun imza anı: tren batırma tüpe girer, beton kabuk
  yerini cam panellere bırakır, yukarıdan ışık huzmeleri süzülür, balıklar geçer.

KURULUM (Rojo)
  src/server/scenes/bosphorus_glass.lua -> ServerStorage.MarmarayScenes.bosphorus_glass

  Command Bar (edit modu, BuildMarmaray çalıştıktan SONRA):
    require(game.ServerStorage.MarmarayScenes.bosphorus_glass)()
    require(game.ServerStorage.MarmarayScenes.bosphorus_glass)({ REPLACE_SHELL = false })

  Tekrar çalıştırmadan önce Workspace.Marmaray.BosphorusGlass klasörünü silin
  (modül mevcut klasörü bulursa temizleyip yeniden kurar).

KONUM — SABİT DEĞİL, TARANIR
  Batırma tüp = Layout.track2Offset(s) <= WIDE_TUBE_MAX (9 m) olan aralık; BuildMarmaray
  tünel kabuğunu da tam bu koşulla "tek geniş kutu"ya çevirir, yani kabuk ile sahne
  otomatik örtüşür. SCAN_FROM_KM..SCAN_TO_KM arası 5 m adımla taranır (≈ km 26.18-27.81).

KOORDİNAT (BuildMarmaray ile AYNI)
  Eksen Catmull-Rom ile örneklenir (positionAtChainage doğrusaldır; aynı eğriyi
  kullanmazsak cam tüp mevcut raydan birkaç cm kayar).
  Yanal konum dünya uzayında: p + left * (ofsetMetre * k),  left = Vector3.yAxis:Cross(fwd)
  ORIGIN_KM kaydırması Workspace.Marmaray attribute'undan okunur (config ile ezilebilir).
  Y datumu kaydırılmaz: deniz seviyesi = dünya Y 0, ray üstü km 26.52'de -57.9 m.

KESİT
  10 tepe / 9 faset: iki yanda düşey "pencere" duvarı, omuzlar, yayvan taç.
  Her faset = bir cam panel (PANEL_STEP uzunluğunda). Üstüne RIB_SPACING arayla
  tam çelik kaburga halkası, faset birleşimlerinde boyuna profiller. Tüp bu iskelet
  sayesinde "inşa edilmiş" görünür, sabun kabarcığı gibi değil.

SU
  Terrain su YOK (terrain ±32000 stud, orası kapsam dışı). Yerine katmanlı yarı saydam
  geometri: yanlarda iki mesafede su perdeleri (uzaktaki daha opak = sis), tüpün üstünde
  yatay su katmanları, deniz seviyesinde hafif dalgalı yüzey karoları. Renk derinlikle
  lacivertten turkuaza açılır.

IŞIK
  - God ray: yüzeyden eğik inen uzun Neon kutular, düzensiz aralıklı, güneş tek yönden.
  - Kostik: tüp içinde tavandan aşağı bakan SpotLight dizisi + rayların üstünde yatan
    çok saydam Neon lekeler. Animasyon SCRIPT'İ BU MODÜLDE YOK; her parçaya Phase /
    BaseTransparency / BaseBrightness attribute'u ve CollectionService etiketi bırakılır.
  - Derinlik: en derin noktada karanlık ve mavi, Sirkeci/Üsküdar uçlarında aydınlık.

TETİK
  Scene klasöründe EntryChainage / ExitChainage attribute'ları + iki görünmez tetik
  parçası (MarmarayTubeTrigger etiketli). Ses/efekt scripti bunları okur.

ETİKETLER (CollectionService)
  MarmarayBosphorusGlass, MarmarayTubeTrigger, MarmarayGodRay, MarmarayCaustic,
  MarmarayCausticLight, MarmarayBubble, MarmarayFish, MarmaraySeaSurface

NOT: game.Lighting'e DOKUNULMAZ (global, diğer sahneleri ezer). Önerilen sis/atmosfer
değerleri scene klasörüne Suggested* attribute'u olarak yazılır.
]]

local DEFAULT = {
	STUDS_PER_METER = 1 / 0.28, -- 1 stud = 0.28 m
	V_SCALE = 1,                -- dikey abartı (BuildMarmaray ile AYNI olmalı)
	REPLACE_SHELL = true,       -- mevcut opak tünel kabuğunu Transparency=1 ile gizle
	PARENT = nil,               -- nil = Workspace.Marmaray (yoksa Workspace)
	ORIGIN_KM = nil,            -- nil = Workspace.Marmaray.OriginKm attribute'u
	SEED = 20131029,            -- Marmaray açılışı 29.10.2013; sahne deterministik

	-- tüp aralığının taranması
	SCAN_FROM_KM = 24, SCAN_TO_KM = 31,
	SCAN_STEP = 5,              -- m
	WIDE_TUBE_MAX = 9,          -- BuildMarmaray.WIDE_TUBE_MAX ile AYNI olmalı

	-- cam tüp geometrisi (metre)
	PANEL_STEP = 24,            -- bir cam panelin boyu
	RIB_SPACING = 5,            -- çelik kaburga halkası aralığı
	PROFILE_RUN = 48,           -- boyuna profil parçası boyu
	CROWN_H = 7.6,              -- tüp tabanından taç yüksekliği
	SIDE_CLEAR = 4.4,           -- en dıştaki hattın ekseninden cama kalan pay
	MIN_HALF_W = 8.0,           -- yarı genişlik alt sınırı
	GLASS_T = 0.18,             -- cam panel kalınlığı
	RIB_D = 0.40,               -- kaburga radyal derinliği
	RIB_W = 0.45,               -- kaburga boyuna genişliği
	PROFILE_T = 0.30,

	-- deniz
	SEA_CHUNK = 160,            -- su geometrisinin boyuna parça boyu
	SEA_BANDS = 4,              -- perde başına düşey renk bandı
	SEA_DIST = { 26, 92 },      -- perdelerin tüp merkezine yanal uzaklığı (m)
	CEIL_LAYERS = 3,            -- tüpün üstündeki yatay su katmanı sayısı
	CEIL_WIDTH = 240,
	SURFACE_TILE = 80,          -- deniz yüzeyi karosu (m)
	SURFACE_SPAN = 400,         -- yüzeyin yanal kapsamı (m)
	SEABED = true,

	-- ışık
	RAYS_PER_CHUNK = 8,
	CAUSTIC_STEP = 18,          -- tüp içi kostik leke aralığı (m)
	LIGHT_STEP = 30,            -- SpotLight aralığı (m)

	-- detay
	FISH_SCHOOLS = 6,
	FISH_PER_SCHOOL = 8,
	BUBBLE_COLUMNS = 7,
	SHIPS = 2,

	MAX_PARTS = 6000,           -- aşılırsa sadece uyarır (saydam parça sıralaması bozulur)
	YIELD_EVERY = 300,
}

-- Renkler ---------------------------------------------------------------
-- 58 m derinlik paleti. Roblox'ta bolgesel aydinlatma yok; place'in gunduz
-- Lighting'i tupun icini de yikiyor. Bu yuzden su ve cam KOYU tutulur, kontrast
-- isik ogelerinde (god ray / kostik) aranir - yoksa sahne gun isigi gibi okunuyor.
local GLASS_COLOR   = Color3.fromRGB(62, 104, 112)   -- koyu mavi-yesil cam
local STEEL_COLOR   = Color3.fromRGB(52, 58, 64)     -- kaburga / profil
local STEEL_DARK    = Color3.fromRGB(32, 36, 41)
local FLOOR_COLOR   = Color3.fromRGB(40, 42, 46)
local RAY_COLOR     = Color3.fromRGB(205, 248, 242)  -- huzme: parlak kalsin, kontrast
local CAUSTIC_COLOR = Color3.fromRGB(195, 245, 238)
local LIGHT_SHALLOW = Color3.fromRGB(150, 215, 210)  -- uclarda (sig) isik rengi
local LIGHT_DEEP    = Color3.fromRGB(28, 72, 130)    -- en derin noktada
local SEA_SURFACE   = Color3.fromRGB(44, 128, 130)
local SEA_SHALLOW   = Color3.fromRGB(22, 92, 102)    -- yuzeye yakin su
local SEA_MID       = Color3.fromRGB(8, 42, 66)
local SEA_DEEP      = Color3.fromRGB(2, 9, 24)       -- dipte neredeyse siyah lacivert
local SEABED_COLOR  = Color3.fromRGB(20, 22, 25)
local SILHOUETTE    = Color3.fromRGB(7, 12, 20)      -- balik / gemi silueti

return function(user)
	local C = table.clone(DEFAULT)
	for key, v in pairs(user or {}) do C[key] = v end

	local RS = game:GetService("ReplicatedStorage")
	local CS = game:GetService("CollectionService")
	local D = require(RS:WaitForChild("MarmarayData"))
	local L = require(RS:WaitForChild("MarmarayLayout"))
	local k = C.STUDS_PER_METER
	local rng = Random.new(C.SEED)

	---------------------------------------------------------------- EKSEN
	-- BuildMarmaray ile birebir aynı örnekleme; yoksa cam tüp raydan kayar.
	local function Pt(i) i = math.clamp(i, 1, #D.S); return D.toStuds(D.X[i], D.Y[i], D.Z[i], k, C.V_SCALE) end
	local function catmull(p0, p1, p2, p3, t)
		local t2, t3 = t * t, t * t * t
		return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
	end
	local function axisRaw(sm)
		local n = #D.S
		sm = math.clamp(sm, D.S[1], D.S[n])
		local i = math.clamp(math.floor(sm / D.Step) + 1, 1, n - 1)
		while i < n - 1 and D.S[i + 1] <= sm do i += 1 end
		while i > 1 and D.S[i] > sm do i -= 1 end
		local t = (sm - D.S[i]) / (D.S[i + 1] - D.S[i])
		return catmull(Pt(i - 1), Pt(i), Pt(i + 1), Pt(i + 2), t)
	end

	local root = workspace:FindFirstChild("Marmaray")
	local originKm = C.ORIGIN_KM
	if originKm == nil and root then originKm = root:GetAttribute("OriginKm") end
	local originOffset = Vector3.zero
	if originKm then
		local o = axisRaw(originKm * 1000)
		originOffset = Vector3.new(o.X, 0, o.Z)
	end
	local function axisAt(sm) return axisRaw(sm) - originOffset end

	-- Kilometrajda tam ortonormal çatı: fwd (teğet), left (+ofset), up (kesit düşeyi).
	-- up = fwd x left; eğimli bölümde de kesit teğete DİK kalır (tüp eğimde 1.8%'e çıkıyor).
	local function frameAt(sm)
		local p = axisAt(sm)
		local fwd = axisAt(sm + 2) - axisAt(sm - 2)
		fwd = (fwd.Magnitude < 1e-5) and Vector3.zAxis or fwd.Unit
		local left = Vector3.yAxis:Cross(fwd)
		left = (left.Magnitude < 1e-5) and Vector3.xAxis or left.Unit
		local up = fwd:Cross(left).Unit
		return { p = p, fwd = fwd, left = left, up = up }
	end
	local function lateral(f, offsetM)
		if offsetM == 0 then return f.p end
		return f.p + f.left * (offsetM * k)
	end
	-- metre cinsinden mutlak kot -> dünya Y (stud). X/Z kaydırmasından etkilenmez.
	local function yOf(ym) return ym * k * C.V_SCALE end
	-- kilometrajda ray üstü kotu (metre)
	local function railTopM(sm) return axisAt(sm).Y / (k * C.V_SCALE) end

	---------------------------------------------------------------- PARÇA
	local NOOPT = {}
	local made = 0
	local function part(name, size, cf, color, material, parent, o)
		local p = Instance.new("Part")
		p.Name = name; p.Anchored = true
		p.Size = size; p.CFrame = cf
		p.Color = color; p.Material = material or Enum.Material.SmoothPlastic
		p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		o = o or NOOPT
		p.Transparency = o.t or 0
		p.Reflectance = o.r or 0
		p.CanCollide = o.collide == true
		p.CanTouch = o.touch == true
		p.CanQuery = o.query == true   -- dekor raycast/mouse'a görünmez, performans
		p.CastShadow = o.shadow == true
		if o.shape then p.Shape = o.shape end
		p.Parent = parent
		made += 1
		if made % C.YIELD_EVERY == 0 then task.wait() end
		return p
	end

	---------------------------------------------------------------- ARALIK
	-- Batırma tüp = track2 ofseti WIDE_TUBE_MAX'in altına indiği kesintisiz aralık.
	local sEntry, sExit = nil, nil
	do
		local s = C.SCAN_FROM_KM * 1000
		local sEnd = C.SCAN_TO_KM * 1000
		while s <= sEnd do
			if L.track2Offset(s) <= C.WIDE_TUBE_MAX then
				if not sEntry then sEntry = s end
				sExit = s
			elseif sEntry then
				break -- ilk kesintisiz aralık yeter (Boğaz geçişi tek parça)
			end
			s += C.SCAN_STEP
		end
	end
	if not sEntry or (sExit - sEntry) < 200 then
		warn(("[BogazCam] Batirma tup araligi bulunamadi (km %g-%g, esik %g m). Iptal.")
			:format(C.SCAN_FROM_KM, C.SCAN_TO_KM, C.WIDE_TUBE_MAX))
		return nil
	end
	local tubeLen = sExit - sEntry

	-- En derin nokta ve derinlik aralığı (ışık/renk zayıflaması bunun üstüne kurulu)
	local depthMin, depthMax, sDeepest = math.huge, -math.huge, sEntry
	do
		local s = sEntry
		while s <= sExit do
			local d = -railTopM(s)
			if d < depthMin then depthMin = d end
			if d > depthMax then depthMax = d; sDeepest = s end
			s += 20
		end
	end
	if depthMax - depthMin < 1 then depthMax = depthMin + 1 end
	-- 0 = tüp uçları (aydınlık), 1 = en derin nokta (karanlık/mavi)
	local function depthT(sm)
		return math.clamp((-railTopM(sm) - depthMin) / (depthMax - depthMin), 0, 1)
	end
	-- uçlara yakınlık: 0 = uçta, 1 = ortada (portal ışığı için)
	local function coreT(sm)
		local d = math.min(sm - sEntry, sExit - sm)
		return math.clamp(d / 260, 0, 1)
	end

	---------------------------------------------------------------- KLASÖRLER
	local parent = C.PARENT or root or workspace
	local old = parent:FindFirstChild("BosphorusGlass")
	if old then old:Destroy() end
	local scene = Instance.new("Folder")
	scene.Name = "BosphorusGlass"
	scene.Parent = parent

	local function folder(name)
		local f = Instance.new("Folder"); f.Name = name; f.Parent = scene; return f
	end
	local fTube    = folder("GlassTube")
	local fFrame   = folder("SteelFrame")
	local fSea     = folder("SeaVolume")
	local fLight   = folder("Light")
	local fDetail  = folder("Detail")
	local fTrigger = folder("Triggers")

	---------------------------------------------------------------- KESİT
	-- Tüp tabanı = ray üstü - (ray + balast) ; BuildMarmaray ile aynı referans.
	local railH, bedH = 0.17, 0.50
	local baseDrop = railH + bedH

	-- Yarı genişlik: en dıştaki hat + pay. Ofset uçlarda 9 m'ye çıktığı için s'ye bağlı.
	local function halfWidth(o2)
		return math.max(C.MIN_HALF_W, o2 / 2 + C.SIDE_CLEAR)
	end
	-- 10 tepe, (u = yanal, v = düşey) metre; tüp merkezine ve tabanına göre.
	-- u > 0 = SOL (left yönü). Sıra: SOL taban -> sol duvar -> omuz -> taç -> sağ omuz
	-- -> sağ duvar -> SAĞ taban. Bu sırada her fasetin DIŞ normali (dv, -du) olur:
	--   sol duvar (du=0, dv>0) -> (+,0) = sol  ✔   taç (du<0, dv=0) -> (0,+) = yukarı ✔
	--   sağ duvar (du=0, dv<0) -> (-,0) = sağ  ✔
	local UFRAC = { 1.00, 1.00, 0.93, 0.66, 0.24 }
	local VFRAC = { 0.00, 0.395, 0.670, 0.908, 1.000 }
	local FACETS = 9
	local function section(o2)
		local W, H = halfWidth(o2), C.CROWN_H
		local s = table.create(10)
		for i = 1, 5 do
			s[i] = { W * UFRAC[i], H * VFRAC[i] }            -- 1..5 : sol taban -> taç
			s[11 - i] = { -W * UFRAC[i], H * VFRAC[i] }      -- 10..6: sağ taban <- taç
		end
		return s, W
	end

	-- kesit noktası -> dünya
	local function secPoint(base, f, u, v)
		return base + f.left * (u * k) + f.up * (v * k)
	end

	---------------------------------------------------------------- CAM TÜP
	local nGlass, nSteel = 0, 0
	do
		local steps = math.max(1, math.ceil(tubeLen / C.PANEL_STEP))
		local segLen = tubeLen / steps
		for q = 0, steps - 1 do
			local sa, sb = sEntry + q * segLen, sEntry + (q + 1) * segLen
			local fa, fb = frameAt(sa), frameAt(sb)
			local oa, ob = L.track2Offset(sa), L.track2Offset(sb)
			local secA, Wa = section(oa)
			local secB, Wb = section(ob)
			local baseA = lateral(fa, oa / 2) - Vector3.yAxis * (baseDrop * k)
			local baseB = lateral(fb, ob / 2) - Vector3.yAxis * (baseDrop * k)
			local run = baseB - baseA
			local len = run.Magnitude
			if len > 0.01 then
				local mid = (baseA + baseB) / 2
				-- iki ucun çatısının ortalaması (panel kirişi gibi davranır)
				local left = (fa.left + fb.left).Unit
				local up = (fa.up + fb.up).Unit
				local mf = { left = left, up = up }
				local sT = depthT((sa + sb) / 2)
				-- derinde cam daha koyu ve daha opak okunsun
				local glassT = 0.40 - 0.13 * sT
				local col = GLASS_COLOR:Lerp(Color3.fromRGB(96, 150, 170), sT * 0.7)

				for i = 1, FACETS do
					local u1 = (secA[i][1] + secB[i][1]) / 2
					local v1 = (secA[i][2] + secB[i][2]) / 2
					local u2 = (secA[i + 1][1] + secB[i + 1][1]) / 2
					local v2 = (secA[i + 1][2] + secB[i + 1][2]) / 2
					local du, dv = u2 - u1, v2 - v1
					local fl = math.sqrt(du * du + dv * dv)
					if fl > 0.05 then
						local nu, nv = du / fl, dv / fl
						local rightW = (mf.left * nu + mf.up * nv).Unit     -- faset boyu yönü
						local normW = (mf.left * nv - mf.up * nu).Unit      -- dış normal
						local pm = secPoint(mid, mf, (u1 + u2) / 2, (v1 + v2) / 2)
						-- fromMatrix(pos, X, Y): Z (back) = X x Y = -fwd  -> Size.Z = boy
						part(("Glass_%03d_%d"):format(q, i),
							Vector3.new(fl * k * 1.03, C.GLASS_T * k, len + 0.4),
							CFrame.fromMatrix(pm, rightW, normW),
							col, Enum.Material.Glass, fTube,
							{ t = glassT, r = 0.06 })
						nGlass += 1
					end
				end

				-- taban plakası: oyuncu tüpten düşmesin diye tek çarpışan parça
				local floorW = (Wa + Wb) * k
				part(("Floor_%03d"):format(q), Vector3.new(floorW, 0.6 * k, len + 0.4),
					CFrame.fromMatrix(mid - up * (0.3 * k), left, up),
					FLOOR_COLOR, Enum.Material.Concrete, fTube, { collide = true, query = true })
			end
		end

		-- Çelik kaburga halkaları: cam panelleri DIŞARIDAN saran tam ring
		local ribs = math.max(2, math.floor(tubeLen / C.RIB_SPACING))
		local ribStep = tubeLen / ribs
		for q = 0, ribs do
			local s = sEntry + q * ribStep
			local f = frameAt(s)
			local o2 = L.track2Offset(s)
			local sec = section(o2)
			local base = lateral(f, o2 / 2) - Vector3.yAxis * (baseDrop * k)
			local ringCol = (q % 4 == 0) and STEEL_DARK or STEEL_COLOR -- her 4. halka vurgulu
			local ringW = (q % 4 == 0) and C.RIB_W * 1.5 or C.RIB_W
			for i = 1, FACETS do
				local u1, v1 = sec[i][1], sec[i][2]
				local u2, v2 = sec[i + 1][1], sec[i + 1][2]
				local du, dv = u2 - u1, v2 - v1
				local fl = math.sqrt(du * du + dv * dv)
				if fl > 0.05 then
					local nu, nv = du / fl, dv / fl
					local rightW = (f.left * nu + f.up * nv).Unit
					local normW = (f.left * nv - f.up * nu).Unit
					local pm = secPoint(base, f, (u1 + u2) / 2, (v1 + v2) / 2)
						+ normW * ((C.GLASS_T / 2 + C.RIB_D / 2) * k)
					part(("Rib_%03d_%d"):format(q, i),
						Vector3.new(fl * k * 1.02, C.RIB_D * k, ringW * k),
						CFrame.fromMatrix(pm, rightW, normW),
						ringCol, Enum.Material.Metal, fFrame, { shadow = false })
					nSteel += 1
				end
			end
		end

		-- Boyuna profiller: faset birleşimlerinde, camı tutan uzun çelikler
		local runs = math.max(1, math.ceil(tubeLen / C.PROFILE_RUN))
		local runLen = tubeLen / runs
		for q = 0, runs - 1 do
			local sa, sb = sEntry + q * runLen, sEntry + (q + 1) * runLen
			local fa, fb = frameAt(sa), frameAt(sb)
			local oa, ob = L.track2Offset(sa), L.track2Offset(sb)
			local secA, secB = section(oa), section(ob)
			local baseA = lateral(fa, oa / 2) - Vector3.yAxis * (baseDrop * k)
			local baseB = lateral(fb, ob / 2) - Vector3.yAxis * (baseDrop * k)
			local run = baseB - baseA
			local len = run.Magnitude
			local mid = (baseA + baseB) / 2
			local mf = { left = (fa.left + fb.left).Unit, up = (fa.up + fb.up).Unit }
			if len > 0.01 then
				local runDir = run.Unit
				for i = 2, 9 do -- taban köşeleri hariç (zaten plaka altında)
					local u = (secA[i][1] + secB[i][1]) / 2
					local v = (secA[i][2] + secB[i][2]) / 2
					-- tepe normali = komşu iki fasetin normal ortalaması
					local function fnorm(j)
						local du = (secA[j + 1][1] + secB[j + 1][1]) / 2 - (secA[j][1] + secB[j][1]) / 2
						local dv = (secA[j + 1][2] + secB[j + 1][2]) / 2 - (secA[j][2] + secB[j][2]) / 2
						local fl = math.max(1e-6, math.sqrt(du * du + dv * dv))
						return Vector2.new(dv / fl, -du / fl)
					end
					local n = fnorm(i - 1) + fnorm(i)
					n = (n.Magnitude < 1e-5) and Vector2.new(0, 1) or n.Unit
					local normW = (mf.left * n.X + mf.up * n.Y).Unit
					local pm = secPoint(mid, mf, u, v) + normW * ((C.GLASS_T / 2 + C.PROFILE_T / 2) * k)
					-- kare kesit: eksen etrafındaki dönüş görsel olarak önemsiz, lookAt yeter
					part(("Profile_%03d_%d"):format(q, i),
						Vector3.new(C.PROFILE_T * k, C.PROFILE_T * k, len + 0.1),
						CFrame.lookAt(pm, pm + runDir, Vector3.yAxis),
						STEEL_COLOR, Enum.Material.Metal, fFrame)
					nSteel += 1
				end
			end
		end

		-- Portal halkaları: tüpün iki ucunda kalın beton/çelik ağız
		for _, s in ipairs({ sEntry + 1, sExit - 1 }) do
			local f = frameAt(s)
			local o2 = L.track2Offset(s)
			local sec = section(o2)
			local base = lateral(f, o2 / 2) - Vector3.yAxis * (baseDrop * k)
			for i = 1, FACETS do
				local u1, v1 = sec[i][1], sec[i][2]
				local u2, v2 = sec[i + 1][1], sec[i + 1][2]
				local du, dv = u2 - u1, v2 - v1
				local fl = math.sqrt(du * du + dv * dv)
				if fl > 0.05 then
					local nu, nv = du / fl, dv / fl
					local rightW = (f.left * nu + f.up * nv).Unit
					local normW = (f.left * nv - f.up * nu).Unit
					local pm = secPoint(base, f, (u1 + u2) / 2, (v1 + v2) / 2)
						+ normW * ((C.GLASS_T / 2 + 1.0 / 2) * k)
					part("Portal_" .. i, Vector3.new(fl * k * 1.02, 1.0 * k, 2.2 * k),
						CFrame.fromMatrix(pm, rightW, normW),
						Color3.fromRGB(86, 86, 90), Enum.Material.Concrete, fFrame)
					nSteel += 1
				end
			end
		end
	end

	---------------------------------------------------------------- DENİZ
	local nSea = 0
	do
		local chunks = math.max(1, math.ceil(tubeLen / C.SEA_CHUNK))
		local chunkLen = tubeLen / chunks
		-- derinliğe göre su rengi: 0 = yüzey (turkuaz), 1 = dip (lacivert)
		local function seaColor(t)
			if t < 0.5 then return SEA_SHALLOW:Lerp(SEA_MID, t / 0.5) end
			return SEA_MID:Lerp(SEA_DEEP, (t - 0.5) / 0.5)
		end

		for q = 0, chunks - 1 do
			local sa, sb = sEntry + q * chunkLen, sEntry + (q + 1) * chunkLen
			local sm = (sa + sb) / 2
			local fa, fb = frameAt(sa), frameAt(sb)
			local pa, pb = fa.p, fb.p
			local len = (Vector3.new(pb.X, 0, pb.Z) - Vector3.new(pa.X, 0, pa.Z)).Magnitude
			local fwdFlat = Vector3.new(pb.X - pa.X, 0, pb.Z - pa.Z)
			fwdFlat = (fwdFlat.Magnitude < 1e-4) and Vector3.zAxis or fwdFlat.Unit
			local leftFlat = Vector3.yAxis:Cross(fwdFlat).Unit
			local o2 = L.track2Offset(sm)
			local centerXZ = lateral(frameAt(sm), o2 / 2)
			local railM = railTopM(sm)
			local bedM = railM - baseDrop - 7.0      -- deniz dibi (tüpün biraz altı)
			local topM = -1.0                         -- su kütlesinin üst sınırı

			local function sliceCF(yMid, lat)
				local p = Vector3.new(centerXZ.X, yOf(yMid), centerXZ.Z) + leftFlat * (lat * k)
				return CFrame.lookAt(p, p + fwdFlat, Vector3.yAxis)
			end

			-- 1) Yanal su perdeleri: iki mesafe, uzaktaki daha opak (sis gibi)
			for di, dist in ipairs(C.SEA_DIST) do
				local opac = 0.74 - 0.12 * (di - 1)  -- yakın perde daha saydam
				for side = -1, 1, 2 do
					for b = 0, C.SEA_BANDS - 1 do
						local y0 = bedM + (topM - bedM) * (b / C.SEA_BANDS)
						local y1 = bedM + (topM - bedM) * ((b + 1) / C.SEA_BANDS)
						local t0 = 1 - ((y0 + y1) / 2 - bedM) / (topM - bedM) -- 1 = dip
						part(("SeaWall_%02d_%d_%d_%d"):format(q, di, side, b),
							Vector3.new(1.2 * k, (y1 - y0) * k, len + 2),
							sliceCF((y0 + y1) / 2, side * dist),
							seaColor(t0), Enum.Material.SmoothPlastic, fSea,
							{ t = opac })
						nSea += 1
					end
				end
			end

			-- 2) Tüpün ÜSTÜNDE yatay su katmanları: yukarı bakınca derinlik hissi
			for c = 1, C.CEIL_LAYERS do
				local fr = c / (C.CEIL_LAYERS + 1)
				local y = (railM + C.CROWN_H - baseDrop) + (topM - (railM + C.CROWN_H - baseDrop)) * fr
				local t = 1 - (y - bedM) / (topM - bedM)
				part(("SeaLayer_%02d_%d"):format(q, c),
					Vector3.new(C.CEIL_WIDTH * k, 0.8 * k, len + 2),
					sliceCF(y, 0), seaColor(t), Enum.Material.SmoothPlastic, fSea,
					{ t = 0.90 - 0.04 * c })
				nSea += 1
			end

			-- 3) Deniz yüzeyi: hafif dalgalı, ışığı geçiren karolar (y = 0 m)
			local across = math.max(1, math.floor(C.SURFACE_SPAN / C.SURFACE_TILE))
			local tiles = math.max(1, math.ceil(len / (C.SURFACE_TILE * k)))
			for ti = 0, tiles - 1 do
				local st = sa + (ti + 0.5) * (chunkLen / tiles)
				local ft = frameAt(st)
				for a = 0, across - 1 do
					local lat = (a - (across - 1) / 2) * C.SURFACE_TILE
					local pxz = lateral(ft, o2 / 2 + lat)
					local p = Vector3.new(pxz.X, yOf(rng:NextNumber(-0.7, 0.7)), pxz.Z)
					local cf = CFrame.lookAt(p, p + ft.fwd, Vector3.yAxis)
						* CFrame.Angles(math.rad(rng:NextNumber(-2.2, 2.2)), 0, math.rad(rng:NextNumber(-2.2, 2.2)))
					local sp = part(("Surface_%02d_%02d_%02d"):format(q, ti, a),
						Vector3.new(C.SURFACE_TILE * k * 1.02, 0.5 * k, C.SURFACE_TILE * k * 1.02),
						cf, SEA_SURFACE, Enum.Material.Glass, fSea,
						{ t = 0.36, r = 0.28 })
					sp:SetAttribute("Phase", rng:NextNumber(0, 1))
					sp:SetAttribute("WaveAmp", rng:NextNumber(0.4, 1.2))
					CS:AddTag(sp, "MarmaraySeaSurface")
					nSea += 1
				end
			end

			-- 4) Deniz dibi + kaya siluetleri
			if C.SEABED then
				part(("Seabed_%02d"):format(q), Vector3.new(300 * k, 2 * k, len + 2),
					sliceCF(bedM - 1, 0), SEABED_COLOR, Enum.Material.Slate, fSea, {})
				nSea += 1
				for _ = 1, 3 do
					local st = rng:NextNumber(sa, sb)
					local lat = rng:NextNumber(14, 95) * (rng:NextInteger(0, 1) == 0 and -1 or 1)
					local pxz = lateral(frameAt(st), o2 / 2 + lat)
					local h = rng:NextNumber(3, 11)
					local p = Vector3.new(pxz.X, yOf(bedM + h / 2), pxz.Z)
					part(("Rock_%02d"):format(q), Vector3.new(rng:NextNumber(5, 16) * k, h * k, rng:NextNumber(5, 16) * k),
						CFrame.new(p) * CFrame.Angles(0, rng:NextNumber(0, 6.28), 0),
						SEABED_COLOR:Lerp(SEA_DEEP, 0.4), Enum.Material.Rock, fSea, {})
					nSea += 1
				end
			end
		end
	end

	---------------------------------------------------------------- IŞIK
	local nRay, nCaustic, nLights = 0, 0, 0
	do
		-- 1) GOD RAY: yüzeyden süzülen eğik huzmeler. Güneş TEK yönden (+left tarafı),
		--    açı küçük rastgelelikle oynar; aralık düzensiz.
		local chunks = math.max(1, math.ceil(tubeLen / C.SEA_CHUNK))
		local chunkLen = tubeLen / chunks
		for q = 0, chunks - 1 do
			local sa = sEntry + q * chunkLen
			for r = 1, C.RAYS_PER_CHUNK do
				local s = rng:NextNumber(sa, sa + chunkLen)
				local f = frameAt(s)
				local o2 = L.track2Offset(s)
				local lat = rng:NextNumber(-70, 70)
				local tilt = rng:NextNumber(0.22, 0.46)
				local dir = (Vector3.new(0, -1, 0) - f.left * tilt + f.fwd * rng:NextNumber(-0.08, 0.08)).Unit
				local topM = rng:NextNumber(-1.5, -4.0)
				local lenM = rng:NextNumber(42, 92) * (1 - 0.35 * depthT(s))
				local pxz = lateral(f, o2 / 2 + lat)
				local top = Vector3.new(pxz.X, yOf(topM), pxz.Z)
				local mid = top + dir * (lenM / 2 * k)
				local w = rng:NextNumber(2.6, 7.0)
				local cf = CFrame.lookAt(mid, mid + dir, f.fwd)
				local tr = 0.90 + 0.05 * depthT(s)
				local p = part(("GodRay_%02d_%02d"):format(q, r),
					Vector3.new(w * k, w * k * rng:NextNumber(0.6, 1.0), lenM * k),
					cf, RAY_COLOR, Enum.Material.Neon, fLight, { t = tr })
				p:SetAttribute("Phase", rng:NextNumber(0, 1))
				p:SetAttribute("BaseTransparency", tr)
				p:SetAttribute("Flicker", rng:NextNumber(0.02, 0.06))
				CS:AddTag(p, "MarmarayGodRay")
				nRay += 1
				-- huzmenin parlak çekirdeği (ince, az sayıda)
				if r % 3 == 0 then
					local p2 = part(("GodRayCore_%02d_%02d"):format(q, r),
						Vector3.new(w * 0.35 * k, w * 0.35 * k, lenM * k),
						cf, Color3.fromRGB(225, 255, 250), Enum.Material.Neon, fLight, { t = 0.82 })
					p2:SetAttribute("Phase", rng:NextNumber(0, 1))
					p2:SetAttribute("BaseTransparency", 0.82)
					CS:AddTag(p2, "MarmarayGodRay")
					nRay += 1
				end
			end
		end

		-- 2) KOSTİK: tüp içinde raylara/zemine düşen oynak açık lekeler
		local steps = math.max(1, math.floor(tubeLen / C.CAUSTIC_STEP))
		for q = 0, steps do
			local s = sEntry + q * (tubeLen / steps)
			local f = frameAt(s)
			local o2 = L.track2Offset(s)
			local _, W = section(o2)
			local base = lateral(f, o2 / 2) - Vector3.yAxis * (baseDrop * k)
			local bright = 0.84 + 0.07 * depthT(s)
			for n = 1, 2 do
				local u = rng:NextNumber(-W + 1.2, W - 1.2)
				local lx, lz = rng:NextNumber(3.5, 9.0), rng:NextNumber(4.0, 11.0)
				local pm = secPoint(base, f, u, 0.06)
				local cf = CFrame.fromMatrix(pm, f.left, f.up) * CFrame.Angles(0, rng:NextNumber(0, 1.2), 0)
				local p = part(("Caustic_%03d_%d"):format(q, n), Vector3.new(lx * k, 0.12 * k, lz * k),
					cf, CAUSTIC_COLOR, Enum.Material.Neon, fLight, { t = bright })
				p:SetAttribute("Phase", rng:NextNumber(0, 1))
				p:SetAttribute("BaseTransparency", bright)
				p:SetAttribute("SwaySpeed", rng:NextNumber(0.18, 0.45))
				p:SetAttribute("SwayAmp", rng:NextNumber(1.5, 4.0))
				p:SetAttribute("LateralOffset_m", u)
				CS:AddTag(p, "MarmarayCaustic")
				nCaustic += 1
			end
		end

		-- 3) SpotLight dizisi: taçtan aşağı, derinlikle sönen su altı ışığı
		local ls = math.max(1, math.floor(tubeLen / C.LIGHT_STEP))
		for q = 0, ls do
			local s = sEntry + q * (tubeLen / ls)
			local f = frameAt(s)
			local o2 = L.track2Offset(s)
			local base = lateral(f, o2 / 2) - Vector3.yAxis * (baseDrop * k)
			local t = depthT(s)
			local edge = 1 - coreT(s) -- uçlarda 1 (portal aydınlığı)
			local pm = secPoint(base, f, rng:NextNumber(-3, 3), C.CROWN_H - 0.4)
			local holder = part(("LightHolder_%03d"):format(q), Vector3.new(0.6 * k, 0.6 * k, 0.6 * k),
				CFrame.fromMatrix(pm, f.left, f.up), Color3.new(1, 1, 1), Enum.Material.Neon, fLight,
				{ t = 1 })
			local sl = Instance.new("SpotLight")
			sl.Face = Enum.NormalId.Bottom
			sl.Angle = 85
			sl.Range = math.min(60, C.CROWN_H * 2.2 * k)
			local br = (1.25 - 0.70 * t) + 0.9 * edge
			sl.Brightness = br
			sl.Color = LIGHT_SHALLOW:Lerp(LIGHT_DEEP, t)
			sl.Shadows = false
			sl.Parent = holder
			holder:SetAttribute("Phase", rng:NextNumber(0, 1))
			holder:SetAttribute("BaseBrightness", br)
			holder:SetAttribute("DepthT", t)
			holder:SetAttribute("Chainage_m", s)
			CS:AddTag(holder, "MarmarayCausticLight")
			nLights += 1
		end
	end

	---------------------------------------------------------------- DETAY
	local nDetail = 0
	do
		-- Balık sürüleri: siluet, az parça, tüpün dışında ve uzakta
		for sch = 1, C.FISH_SCHOOLS do
			local s0 = rng:NextNumber(sEntry + 40, sExit - 40)
			local o2 = L.track2Offset(s0)
			local side = rng:NextInteger(0, 1) == 0 and -1 or 1
			local lat0 = side * rng:NextNumber(16, 55)
			local yBase = railTopM(s0) + rng:NextNumber(4, 26)
			local m = Instance.new("Model"); m.Name = ("FishSchool_%d"):format(sch)
			for i = 1, C.FISH_PER_SCHOOL do
				local s = s0 + rng:NextNumber(-22, 22)
				local f = frameAt(s)
				local pxz = lateral(f, o2 / 2 + lat0 + rng:NextNumber(-8, 8))
				local p = Vector3.new(pxz.X, yOf(yBase + rng:NextNumber(-5, 5)), pxz.Z)
				local bodyL = rng:NextNumber(0.9, 2.4)
				local yaw = rng:NextNumber(-0.5, 0.5)
				local cf = CFrame.lookAt(p, p + f.fwd * side, Vector3.yAxis) * CFrame.Angles(0, yaw, 0)
				part("Body", Vector3.new(bodyL * 0.42 * k, bodyL * 0.38 * k, bodyL * k), cf,
					SILHOUETTE, Enum.Material.SmoothPlastic, m, { t = 0.34 })
				part("Tail", Vector3.new(bodyL * 0.08 * k, bodyL * 0.52 * k, bodyL * 0.34 * k),
					cf * CFrame.new(0, 0, bodyL * 0.6 * k) * CFrame.Angles(0, 0.3, 0),
					SILHOUETTE, Enum.Material.SmoothPlastic, m, { t = 0.42 })
				nDetail += 2
			end
			m:SetAttribute("Chainage_m", s0)
			m:SetAttribute("Phase", rng:NextNumber(0, 1))
			m:SetAttribute("SwimSpeed", rng:NextNumber(0.6, 2.2))
			m:SetAttribute("Direction", side)
			CS:AddTag(m, "MarmarayFish")
			m.Parent = fDetail
		end

		-- Büyük tek siluetler (büyük balık / yunus): uzakta, loş
		for i = 1, 3 do
			local s = rng:NextNumber(sEntry + 80, sExit - 80)
			local f = frameAt(s)
			local o2 = L.track2Offset(s)
			local side = (i % 2 == 0) and 1 or -1
			local pxz = lateral(f, o2 / 2 + side * rng:NextNumber(60, 120))
			local p = Vector3.new(pxz.X, yOf(railTopM(s) + rng:NextNumber(14, 34)), pxz.Z)
			local Lb = rng:NextNumber(5, 9)
			local cf = CFrame.lookAt(p, p + f.fwd * side, Vector3.yAxis) * CFrame.Angles(0, 0, math.rad(8))
			local m = Instance.new("Model"); m.Name = ("BigSilhouette_%d"):format(i)
			part("Body", Vector3.new(Lb * 0.30 * k, Lb * 0.26 * k, Lb * k), cf, SILHOUETTE, Enum.Material.SmoothPlastic, m, { t = 0.48 })
			part("Tail", Vector3.new(Lb * 0.08 * k, Lb * 0.10 * k, Lb * 0.40 * k), cf * CFrame.new(0, 0, Lb * 0.62 * k),
				SILHOUETTE, Enum.Material.SmoothPlastic, m, { t = 0.55 })
			part("Fin", Vector3.new(Lb * 0.06 * k, Lb * 0.30 * k, Lb * 0.18 * k), cf * CFrame.new(0, Lb * 0.16 * k, 0),
				SILHOUETTE, Enum.Material.SmoothPlastic, m, { t = 0.55 })
			m:SetAttribute("Phase", rng:NextNumber(0, 1))
			m:SetAttribute("SwimSpeed", rng:NextNumber(0.3, 0.8))
			CS:AddTag(m, "MarmarayFish")
			m.Parent = fDetail
			nDetail += 3
		end

		-- Yükselen kabarcık sütunları: dipten yüzeye
		for c = 1, C.BUBBLE_COLUMNS do
			local s = rng:NextNumber(sEntry + 30, sExit - 30)
			local f = frameAt(s)
			local o2 = L.track2Offset(s)
			local lat = rng:NextNumber(12, 70) * (rng:NextInteger(0, 1) == 0 and -1 or 1)
			local m = Instance.new("Model"); m.Name = ("BubbleColumn_%d"):format(c)
			local y0 = railTopM(s) - baseDrop - 2
			local y1 = -3
			local n = 11
			for i = 1, n do
				local fr = (i - 1) / (n - 1)
				local pxz = lateral(f, o2 / 2 + lat + rng:NextNumber(-2.5, 2.5))
				local p = Vector3.new(pxz.X, yOf(y0 + (y1 - y0) * fr), pxz.Z)
				local d = rng:NextNumber(0.3, 1.0) * (0.6 + fr)
				local b = part("Bubble", Vector3.new(d * k, d * k, d * k), CFrame.new(p),
					Color3.fromRGB(205, 245, 245), Enum.Material.Glass, m,
					{ t = 0.58, r = 0.25, shape = Enum.PartType.Ball })
				b:SetAttribute("Phase", (fr + rng:NextNumber(0, 0.1)) % 1)
				nDetail += 1
			end
			m:SetAttribute("Chainage_m", s)
			m:SetAttribute("BottomY_m", y0)
			m:SetAttribute("TopY_m", y1)
			m:SetAttribute("RiseSpeed", rng:NextNumber(2.5, 5.5))
			CS:AddTag(m, "MarmarayBubble")
			m.Parent = fDetail
		end

		-- Uzakta loş gemi gövdesi silueti (yüzeyin hemen altı)
		for i = 1, C.SHIPS do
			local s = rng:NextNumber(sEntry + 150, sExit - 150)
			local f = frameAt(s)
			local o2 = L.track2Offset(s)
			local side = (i % 2 == 0) and 1 or -1
			local pxz = lateral(f, o2 / 2 + side * rng:NextNumber(110, 175))
			local m = Instance.new("Model"); m.Name = ("ShipSilhouette_%d"):format(i)
			local hullL = rng:NextNumber(60, 110)
			local p = Vector3.new(pxz.X, yOf(-2.6), pxz.Z)
			local cf = CFrame.lookAt(p, p + f.left * side, Vector3.yAxis) * CFrame.Angles(0, rng:NextNumber(-0.4, 0.4), 0)
			part("Hull", Vector3.new(hullL * 0.16 * k, 5.5 * k, hullL * k), cf,
				SILHOUETTE, Enum.Material.SmoothPlastic, m, { t = 0.52 })
			part("HullLow", Vector3.new(hullL * 0.10 * k, 3.0 * k, hullL * 0.8 * k), cf * CFrame.new(0, -3.4 * k, 0),
				SILHOUETTE, Enum.Material.SmoothPlastic, m, { t = 0.58 })
			part("Keel", Vector3.new(hullL * 0.05 * k, 2.0 * k, hullL * 0.55 * k), cf * CFrame.new(0, -5.4 * k, 0),
				SILHOUETTE, Enum.Material.SmoothPlastic, m, { t = 0.62 })
			-- pervane izi: kabarcık perdesi
			for b = 1, 5 do
				part("Wake", Vector3.new(2.5 * k, 2.5 * k, 2.5 * k),
					cf * CFrame.new(0, -1.5 * k, (-hullL * 0.5 - b * 4) * k),
					Color3.fromRGB(210, 245, 245), Enum.Material.Neon, m,
					{ t = 0.86, shape = Enum.PartType.Ball })
			end
			m:SetAttribute("Phase", rng:NextNumber(0, 1))
			m:SetAttribute("DriftSpeed", rng:NextNumber(1.5, 4.0))
			m.Parent = fDetail
			nDetail += 8
		end
	end

	---------------------------------------------------------------- TETİK
	do
		for _, e in ipairs({ { sEntry, "Entry" }, { sExit, "Exit" } }) do
			local s, label = e[1], e[2]
			local f = frameAt(s)
			local o2 = L.track2Offset(s)
			local _, W = section(o2)
			local base = lateral(f, o2 / 2) - Vector3.yAxis * (baseDrop * k)
			local pm = secPoint(base, f, 0, C.CROWN_H / 2)
			local p = part("Trigger_" .. label,
				Vector3.new(2 * W * k, C.CROWN_H * k, 4 * k),
				CFrame.fromMatrix(pm, f.left, f.up),
				Color3.new(1, 1, 1), Enum.Material.SmoothPlastic, fTrigger,
				{ t = 1, touch = true, query = true })
			p:SetAttribute("Chainage_m", s)
			p:SetAttribute("Edge", label)
			CS:AddTag(p, "MarmarayTubeTrigger")
		end
	end

	---------------------------------------------------------------- KABUK GİZLE
	local hidden = 0
	if C.REPLACE_SHELL and root then
		local scanned = 0
		for _, f in ipairs(root:GetChildren()) do
			if f:IsA("Folder") and f.Name:sub(1, 5) == "Track" then
				for _, seg in ipairs(f:GetChildren()) do
					local ch = seg:GetAttribute("Chainage_m")
					if ch and ch >= sEntry - 40 and ch <= sExit + 40 then
						for _, d in ipairs(seg:GetChildren()) do
							-- BuildMarmaray geniş tüp parçaları: WallL_Tube / WallR_Tube / Roof_Tube
							if d:IsA("BasePart") and d.Name:sub(-5) == "_Tube" then
								d.Transparency = 1
								d.CastShadow = false
								d:SetAttribute("HiddenBy", "BosphorusGlass") -- geri almak icin isaret
								hidden += 1
							end
						end
					end
					scanned += 1
					if scanned % 800 == 0 then task.wait() end
				end
			end
		end
		if hidden == 0 then
			warn("[BogazCam] Gizlenecek tunel kabugu bulunamadi; BuildMarmaray bu araligi kurmus mu?")
		end
	end

	---------------------------------------------------------------- ÖZNİTELİK
	scene:SetAttribute("EntryChainage", sEntry)
	scene:SetAttribute("ExitChainage", sExit)
	scene:SetAttribute("TubeLength_m", tubeLen)
	scene:SetAttribute("DeepestChainage", sDeepest)
	scene:SetAttribute("DepthMin_m", depthMin)
	scene:SetAttribute("DepthMax_m", depthMax)
	scene:SetAttribute("SeaLevelY", yOf(0))
	scene:SetAttribute("StudsPerMeter", k)
	scene:SetAttribute("VScale", C.V_SCALE)
	scene:SetAttribute("OriginKm", originKm)
	scene:SetAttribute("ShellReplaced", C.REPLACE_SHELL and hidden > 0)
	scene:SetAttribute("HiddenShellParts", hidden)
	scene:SetAttribute("Seed", C.SEED)
	-- animasyon scripti icin ortak ayarlar (bu modul animasyon YAPMAZ)
	scene:SetAttribute("CausticSpeed", 0.35)
	scene:SetAttribute("CausticColorA", CAUSTIC_COLOR)
	scene:SetAttribute("CausticColorB", Color3.fromRGB(120, 200, 230))
	scene:SetAttribute("GodRayPulse", 0.22)
	scene:SetAttribute("SurfaceWaveSpeed", 0.5)
	-- game.Lighting GLOBAL oldugu icin degistirilmez; oyuncu tupteyken uygulanacak oneri:
	scene:SetAttribute("SuggestedFogColor", SEA_MID)
	scene:SetAttribute("SuggestedFogStart", 40 * k)
	scene:SetAttribute("SuggestedFogEnd", 420 * k)
	scene:SetAttribute("SuggestedAmbient", Color3.fromRGB(26, 52, 72))
	CS:AddTag(scene, "MarmarayBosphorusGlass")

	print(("[BogazCam] km %.3f - %.3f (%.0f m), en derin km %.3f (-%.1f m)")
		:format(sEntry / 1000, sExit / 1000, tubeLen, sDeepest / 1000, depthMax))
	print(("[BogazCam] parca: cam %d, celik %d, deniz %d, huzme %d, kostik %d, isik %d, detay %d = %d")
		:format(nGlass, nSteel, nSea, nRay, nCaustic, nLights, nDetail, made))
	if hidden > 0 then print(("[BogazCam] %d opak kabuk parcasi gizlendi"):format(hidden)) end
	if made > C.MAX_PARTS then
		warn(("[BogazCam] UYARI: %d parca (butce %d). Saydam parca sirasi bozulabilir; "
			.. "RIB_SPACING / PANEL_STEP degerlerini buyutun."):format(made, C.MAX_PARTS))
	end
	return scene
end
