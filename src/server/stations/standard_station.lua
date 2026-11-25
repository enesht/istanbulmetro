--[[
standard_station (ModuleScript)  —  Marmaray 43 istasyon için STANDART şablon + tabela

AMAÇ
  BuildMarmaray her istasyona yalnızca düz bir peron plakası koyuyor. Bu modül o plakanın
  yerine sade ama düzgün bir istasyon şablonu kurar: eksen takipli peron, peron kenarı
  bantları, peron boyunca tekrar eden çift yüzlü isim panoları, uzaktan okunan totem,
  yerüstünde sundurma / yeraltında kutu tavan, peron uçlarında istasyon no + kilometraj.
  Detaylı kurulan istasyonlar (ör. Yenikapı) SKIP ile dışarıda bırakılır.

KURULUM (Rojo)
  src/server/stations/standard_station.lua -> ServerStorage.MarmarayStations.standard_station

  Command Bar (edit modu):
    require(game.ServerStorage.MarmarayStations.standard_station)()                                   -- 43 istasyon
    require(game.ServerStorage.MarmarayStations.standard_station)({ SKIP = {"Yenikapı", "Sirkeci"} })  -- detaylılar hariç
    require(game.ServerStorage.MarmarayStations.standard_station)({ STATIONS = {"Gebze", "Kartal"} })  -- sadece bunlar

KOORDİNAT
  Eksen noktaları BuildMarmaray ile AYNI Catmull-Rom yumuşatmasıyla üretilir; aksi halde
  peron ray ekseninden birkaç cm kayar. ORIGIN_KM verilmezse Workspace.Marmaray üzerindeki
  OriginKm özniteliği okunur, böylece kaydırılmış hatta da doğru yere oturur.
    left = Vector3.yAxis:Cross(forward).Unit   -> + ofset yönü (seyir yönünün SOLU)
    world = p + left * (ofsetMetre * k)
    p.Y = RAY ÜSTÜ kotu; peron üstü = p.Y + 1.10 m

PERON GEOMETRİSİ (Layout.Stations)
  ISLAND -> l0..l1 yanal sınır, a0..a1 boyuna sınır; iki kenar da tren kenarı
  SIDE   -> sides[] içindeki her peron ayrı; tren kenarı = hatta en yakın kenar
  Layout'ta olmayan istasyon -> D.Stations[].platformLength kadar peron, hattın SAĞINA
  Viraja uysun diye peron ~10 m'lik, bant/sundurma/tavan ~20 m'lik parçalarla kurulur.

PART BÜTÇESİ (ada peron, 250 m)
  peron 25 + bant 52 + sundurma 52 (veya tavan 39) + pano 18 + totem 6  ~=  150 part
]]

local DEFAULT = {
	STUDS_PER_METER = 1 / 0.28, -- 1 stud = 0.28 m (BuildMarmaray ile aynı olmalı)
	V_SCALE = 1,                -- dikey abartı (1 = gerçek)
	ORIGIN_KM = nil,            -- nil = Workspace.Marmaray.OriginKm'den oku, false = kaydırma yok
	STATIONS = nil,             -- isim listesi; nil = 43 istasyonun hepsi
	SKIP = nil,                 -- atlanacak isimler (detaylı kurulanlar)
	PARENT = nil,               -- nil = Workspace.Marmaray.Stations
	CLEAN_OLD = true,           -- BuildMarmaray'in basit peron/hol parçalarını sil (çakışmasın)
	PLATFORM_STEP = 10,         -- peron plakası parça uzunluğu (m)
	DETAIL_STEP = 20,           -- bant / sundurma / tavan parça uzunluğu (m)
	SIGN_SPACING = 40,          -- isim panoları arası hedef aralık (m)
	CANOPY = true,              -- yerüstü istasyonlarda sundurma
	CEILING = true,             -- yeraltı istasyonlarda kutu tavan
	FALLBACK_WIDTH = 8,         -- Layout'ta olmayan istasyonun peron genişliği (m)
	YIELD_EVERY = 400,          -- bu kadar partta bir task.wait()
}

-- Renkler ------------------------------------------------------------------
local PLAT_COLOR  = Color3.fromRGB(200, 200, 195) -- peron betonu (BuildMarmaray ile aynı)
local TACTILE     = Color3.fromRGB(242, 190, 45)  -- sarı taktil (hissedilebilir) şerit
local TURQUOISE   = Color3.fromRGB(0, 158, 170)   -- Marmaray turkuazı
local SIGN_FACE   = Color3.fromRGB(242, 242, 236) -- pano zemini
local SIGN_INK    = Color3.fromRGB(20, 34, 60)    -- pano yazısı
local SIGN_BAND   = Color3.fromRGB(0, 70, 140)    -- pano üst bandı (koyu)
local POLE_COLOR  = Color3.fromRGB(105, 108, 112) -- direk
local COLUMN      = Color3.fromRGB(168, 168, 162) -- sundurma kolonu
local ROOF_COLOR  = Color3.fromRGB(208, 208, 202) -- saçak
local FASCIA      = Color3.fromRGB(150, 150, 145) -- saçak alın bandı
local HALL_COLOR  = Color3.fromRGB(90, 90, 95)    -- yeraltı kutu tavan (BuildMarmaray ile aynı)

-- Türkçe büyük harf ---------------------------------------------------------
-- string.upper bayt tabanlıdır; "Küçükçekmece" -> "KüçüKçEKMECE" olur. Önce çok baytlı
-- harfleri ve i -> İ dönüşümünü elle yap, sonra kalan ASCII'yi upper'a bırak.
local TR_UPPER = {
	["ı"] = "I", ["ç"] = "Ç", ["ğ"] = "Ğ", ["ö"] = "Ö", ["ş"] = "Ş", ["ü"] = "Ü",
	["â"] = "Â", ["î"] = "Î", ["û"] = "Û",
}
local function trUpper(s)
	s = s:gsub("[\128-\255][\128-\191]*", function(ch) return TR_UPPER[ch] end)
	s = s:gsub("i", "İ")
	return (s:upper())
end

return function(user)
	local C = table.clone(DEFAULT)
	for key, v in pairs(user or {}) do C[key] = v end
	local RS = game:GetService("ReplicatedStorage")
	local D = require(RS:WaitForChild("MarmarayData"))
	local L = require(RS:WaitForChild("MarmarayLayout"))
	local k = C.STUDS_PER_METER

	---------------------------------------------------------------- hedef klasör
	local root = workspace:FindFirstChild("Marmaray")
	if not root then
		root = Instance.new("Folder"); root.Name = "Marmaray"; root.Parent = workspace
	end
	local fSt = C.PARENT
	if not fSt then
		fSt = root:FindFirstChild("Stations") or Instance.new("Folder")
		fSt.Name = "Stations"; fSt.Parent = root
	end

	---------------------------------------------------------------- isim filtreleri
	local function nameSet(t)
		if t == nil then return nil end
		local out = {}
		for key, v in pairs(t) do
			if type(v) == "string" then out[v] = true
			elseif v == true and type(key) == "string" then out[key] = true end
		end
		return out
	end
	local only = nameSet(C.STATIONS)
	local skip = nameSet(C.SKIP) or {}

	---------------------------------------------------------------- eksen (BuildMarmaray ile aynı)
	local function P(i) i = math.clamp(i, 1, #D.S); return D.toStuds(D.X[i], D.Y[i], D.Z[i], k, C.V_SCALE) end
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
		return catmull(P(i - 1), P(i), P(i + 1), P(i + 2), t)
	end
	-- Yatay kaydırma: hat ORIGIN_KM ile kurulduysa istasyonlar da aynı kadar kaymalı.
	local originKm = C.ORIGIN_KM
	if originKm == nil then originKm = root:GetAttribute("OriginKm") end
	if originKm == false then originKm = nil end
	local originOffset = Vector3.zero
	if originKm then
		local o = axisRaw(originKm * 1000)
		originOffset = Vector3.new(o.X, 0, o.Z)
	end
	local function axisAt(sm) return axisRaw(sm) - originOffset end
	local function frameAt(sm)
		local p = axisAt(sm)
		local fwd = axisAt(sm + 2) - axisAt(sm - 2)
		if fwd.Magnitude < 1e-5 then fwd = Vector3.zAxis else fwd = fwd.Unit end
		local left = Vector3.yAxis:Cross(fwd)
		if left.Magnitude < 1e-5 then left = Vector3.xAxis else left = left.Unit end
		return { p = p, fwd = fwd, left = left }
	end
	local function lateral(f, offsetM)
		if offsetM == 0 then return f.p end
		return f.p + f.left * (offsetM * k)
	end

	---------------------------------------------------------------- ölçüler (stud)
	local railH, bedH = 0.17 * k, 0.5 * k  -- BuildMarmaray ile aynı; formasyon üstü = -railH-bedH
	local wall   = 0.5 * k
	local platH  = 1.1 * k                  -- peron yüksekliği (ray üstünden)
	local bandT  = 0.04 * k                 -- bant kalınlığı
	local canopyClear = 4.0 * k             -- peron üstünden saçak altı
	local roofT  = 0.25 * k
	local hallH  = 9 * k                    -- yeraltı kutu iç yüksekliği (formasyondan)

	---------------------------------------------------------------- part yardımcıları
	local partCount = 0
	local function yieldMaybe()
		if partCount > 0 and partCount % C.YIELD_EVERY == 0 then task.wait() end
	end
	local function part(name, size, cf, color, material, parent, canCollide)
		local p = Instance.new("Part")
		p.Name = name
		p.Anchored = true
		p.Size = size
		p.CFrame = cf
		p.Color = color
		p.Material = material or Enum.Material.SmoothPlastic
		p.CanCollide = (canCollide ~= false)
		p.TopSurface = Enum.SurfaceType.Smooth
		p.BottomSurface = Enum.SurfaceType.Smooth
		p.Parent = parent
		partCount += 1
		yieldMaybe()
		return p
	end

	-- a0..a1 (istasyon kilometrajına göre, m) aralığını ~step'lik parçalara böler;
	-- parça uçlarının frame'lerini döndürür. Bütün yüzeyler bu frame'leri paylaşır.
	local function stripFrames(sSt, a0, a1, step)
		local n = math.max(1, math.ceil((a1 - a0) / step))
		local segLen = (a1 - a0) / n
		local fr = table.create(n + 1)
		for q = 0, n do fr[q + 1] = frameAt(sSt + a0 + q * segLen) end
		return fr, n
	end
	-- q. parçanın (1..n) orta CFrame'i + uzunluğu; latM yanal ofsette
	local function pieceCF(fr, q, latM)
		local pa, pb = lateral(fr[q], latM), lateral(fr[q + 1], latM)
		local len = (pb - pa).Magnitude
		if len <= 0.01 then return nil, 0 end
		return CFrame.lookAt((pa + pb) / 2, pb, Vector3.yAxis), len
	end
	-- tek kilometrajda, latM ofsetinde, yerel +Z = hat yönü olan CFrame
	local function spotCF(sm, latM)
		local f = frameAt(sm)
		local pos = lateral(f, latM)
		return CFrame.lookAt(pos, pos + f.fwd, Vector3.yAxis)
	end

	---------------------------------------------------------------- yazı yardımcıları
	-- Panonun HER İKİ yüzüne de aynı metni koyar; hangi yönden gelirsen gel okunur.
	local function faceText(p, text, color, pps, maxDist)
		for _, face in ipairs({ Enum.NormalId.Right, Enum.NormalId.Left }) do
			local sg = Instance.new("SurfaceGui")
			sg.Name = "Yazi_" .. face.Name
			sg.Face = face
			sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
			sg.PixelsPerStud = pps or 24
			sg.LightInfluence = 0
			sg.MaxDistance = maxDist or 500
			sg.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
			sg.Parent = p
			local tl = Instance.new("TextLabel")
			tl.Name = "Metin"
			tl.AnchorPoint = Vector2.new(0.5, 0.5)
			tl.Position = UDim2.fromScale(0.5, 0.5)
			tl.Size = UDim2.fromScale(0.94, 0.78)
			tl.BackgroundTransparency = 1
			tl.TextColor3 = color
			tl.Font = Enum.Font.GothamBold
			tl.TextScaled = true
			tl.TextXAlignment = Enum.TextXAlignment.Center
			tl.Text = text
			tl.Parent = sg
		end
	end

	---------------------------------------------------------------- 1) PERON PLAKASI
	-- Hat eksenini ~10 m'lik parçalarla takip eder (tek kutu yok, viraja uyar).
	local function deck(parent, name, sSt, a0, a1, l0, l1, color)
		local lo, hi = math.min(l0, l1), math.max(l0, l1)
		local width = (hi - lo) * k
		if width < 0.1 then return nil end
		local latC = (lo + hi) / 2
		local fr, n = stripFrames(sSt, a0, a1, C.PLATFORM_STEP)
		local middle = nil
		for q = 1, n do
			local cf, len = pieceCF(fr, q, latC)
			if cf then
				local p = part(("%s_%02d"):format(name, q - 1), Vector3.new(width, platH, len + 0.05),
					cf * CFrame.new(0, platH / 2, 0), color, Enum.Material.Concrete, parent)
				if q == math.ceil(n / 2) then middle = p end
			end
		end
		return middle
	end

	---------------------------------------------------------------- 2) KENAR BANTLARI
	-- edges = {{lat = kenar ofseti, dir = peron içine doğru işaret (+1/-1)}, ...}
	-- Sarı taktil şerit en dışta, turkuaz bant onun içinde. Bantlar ~20 m'lik parçalarla
	-- kurulduğu için virajda kirişin dışa taşmaması adına 0.25 m içeriden başlatılır.
	local function edgeBands(parent, name, sSt, a0, a1, edges)
		local fr, n = stripFrames(sSt, a0, a1, C.DETAIL_STEP)
		local y = platH + bandT / 2
		for ei, e in ipairs(edges) do
			local tacC = e.lat + e.dir * 0.55   -- 0.25 .. 0.85 m
			local turC = e.lat + e.dir * 1.15   -- 0.95 .. 1.35 m
			for q = 1, n do
				local cfT, lenT = pieceCF(fr, q, tacC)
				if cfT then
					part(("%s%d_Taktil_%02d"):format(name, ei, q - 1), Vector3.new(0.60 * k, bandT, lenT + 0.05),
						cfT * CFrame.new(0, y, 0), TACTILE, Enum.Material.Pebble, parent, false)
				end
				local cfB, lenB = pieceCF(fr, q, turC)
				if cfB then
					part(("%s%d_Bant_%02d"):format(name, ei, q - 1), Vector3.new(0.40 * k, bandT, lenB + 0.05),
						cfB * CFrame.new(0, y, 0), TURQUOISE, Enum.Material.SmoothPlastic, parent, false)
				end
			end
		end
	end

	---------------------------------------------------------------- 3) İSİM PANOLARI
	-- Peron boyunca ~SIGN_SPACING aralıkla tekrarlar. Pano düzlemi hat yönüne paralel,
	-- büyük yüzleri yanlara (her iki hatta) bakar; iki yüzde de SurfaceGui vardır.
	local function nameSigns(parent, suffix, sSt, a0, a1, latC, widthM, text)
		local sA, sB = a0 + 15, a1 - 15
		if sB - sA < 10 then sA, sB = a0 + (a1 - a0) * 0.25, a0 + (a1 - a0) * 0.75 end
		local nSign = math.max(1, math.floor((sB - sA) / C.SIGN_SPACING))
		-- Panoyu peron ortasından biraz kaydır: sundurma kolonları eksende duruyor.
		local lat = latC + math.min(1.4, math.max(0, widthM / 2 - 0.8))
		local panelW, panelH, panelT = 3.2 * k, 0.70 * k, 0.12 * k
		local mastH = 2.45 * k
		for i = 0, nSign do
			local aa = sA + (sB - sA) * (i / nSign)
			local cf = spotCF(sSt + aa, lat)
			part(("Pano%s%02d_Direk"):format(suffix, i), Vector3.new(0.13 * k, mastH, 0.13 * k),
				cf * CFrame.new(0, platH + mastH / 2, 0), POLE_COLOR, Enum.Material.Metal, parent)
			local panel = part(("Pano%s%02d"):format(suffix, i), Vector3.new(panelT, panelH, panelW),
				cf * CFrame.new(0, platH + mastH + panelH / 2, 0), SIGN_FACE, Enum.Material.SmoothPlastic, parent, false)
			-- üst kenardaki ince koyu bant
			part(("Pano%s%02d_Bant"):format(suffix, i), Vector3.new(panelT * 1.15, 0.10 * k, panelW),
				cf * CFrame.new(0, platH + mastH + panelH + 0.05 * k, 0), SIGN_BAND, Enum.Material.SmoothPlastic, parent, false)
			faceText(panel, text, SIGN_INK, 26, 600)
		end
	end

	---------------------------------------------------------------- 3b) TOTEM + UÇ LEVHASI
	-- Peronun iki ucunda: uzaktan okunan BillboardGui'li totem (MaxDistance 1200) +
	-- istasyon numarası ve kilometrajı taşıyan levha.
	local function totem(parent, name, sSt, aa, latC, text, endText)
		local cf = spotCF(sSt + aa, latC)
		local poleH = 4.6 * k
		part(name .. "_Direk", Vector3.new(0.26 * k, poleH, 0.26 * k),
			cf * CFrame.new(0, platH + poleH / 2, 0), POLE_COLOR, Enum.Material.Metal, parent)
		local box = part(name, Vector3.new(0.18 * k, 0.95 * k, 2.60 * k),
			cf * CFrame.new(0, platH + poleH - 0.55 * k, 0), SIGN_FACE, Enum.Material.SmoothPlastic, parent, false)
		faceText(box, text, SIGN_INK, 26, 900)
		local plate = part(name .. "_Kunye", Vector3.new(0.14 * k, 0.45 * k, 1.90 * k),
			cf * CFrame.new(0, platH + poleH - 1.70 * k, 0), SIGN_BAND, Enum.Material.SmoothPlastic, parent, false)
		faceText(plate, endText, Color3.new(1, 1, 1), 26, 450)
		-- uzaktan görünen isim
		local bb = Instance.new("BillboardGui")
		bb.Name = "Uzak"
		bb.Size = UDim2.fromOffset(300, 64)
		bb.StudsOffset = Vector3.new(0, 4, 0)
		bb.AlwaysOnTop = true
		bb.MaxDistance = 1200
		bb.Parent = box
		local tl = Instance.new("TextLabel")
		tl.Size = UDim2.fromScale(1, 1)
		tl.BackgroundColor3 = SIGN_BAND
		tl.BackgroundTransparency = 0.1
		tl.TextColor3 = Color3.new(1, 1, 1)
		tl.TextScaled = true
		tl.Font = Enum.Font.GothamBold
		tl.Text = text
		tl.Parent = bb
		local corner = Instance.new("UICorner")
		corner.CornerRadius = UDim.new(0, 8)
		corner.Parent = tl
		return box
	end

	---------------------------------------------------------------- 4a) SUNDURMA (yerüstü)
	-- İnce kolonlar peron ekseninde, üstünde düz saçak + iki yanda alın bandı.
	-- Peron 10 m'den genişse tek sıra kolon sarkık durur; iki sıraya çıkılır.
	local function canopy(parent, name, sSt, a0, a1, l0, l1)
		local lo, hi = math.min(l0, l1), math.max(l0, l1)
		local latC = (lo + hi) / 2
		local widthM = hi - lo
		local roofW = math.max(2.0, widthM - 1.0) * k
		local colLats = { latC }
		if widthM > 10 then
			local off = widthM / 2 - 2.2
			colLats = { latC - off, latC + off }
		end
		local fr, n = stripFrames(sSt, a0, a1, C.DETAIL_STEP)
		local colH = canopyClear - roofT
		for q = 1, n do
			local cf, len = pieceCF(fr, q, latC)
			if cf then
				part(("%s_Sacak_%02d"):format(name, q - 1), Vector3.new(roofW, roofT, len + 0.05),
					cf * CFrame.new(0, platH + canopyClear - roofT / 2, 0), ROOF_COLOR, Enum.Material.Metal, parent)
				for _, side in ipairs({ -1, 1 }) do
					part(("%s_Alin_%02d"):format(name, q - 1), Vector3.new(0.12 * k, 0.34 * k, len + 0.05),
						cf * CFrame.new(side * (roofW / 2 - 0.06 * k), platH + canopyClear - roofT - 0.17 * k, 0),
						FASCIA, Enum.Material.Metal, parent, false)
				end
				-- kolon(lar): parçanın ortasında
				local cm = sSt + a0 + (a1 - a0) * ((q - 0.5) / n)
				for ci, cl in ipairs(colLats) do
					local ccf = spotCF(cm, cl)
					part(("%s_Kolon%d_%02d"):format(name, ci, q - 1), Vector3.new(0.34 * k, colH, 0.34 * k),
						ccf * CFrame.new(0, platH + colH / 2, 0), COLUMN, Enum.Material.Metal, parent)
				end
			end
		end
	end

	---------------------------------------------------------------- 4b) KUTU TAVAN (yeraltı)
	local function hallBox(parent, name, sSt, a0, a1, latLo, latHi)
		local w = (latHi - latLo) * k + 2 * wall
		local latC = (latLo + latHi) / 2
		local fr, n = stripFrames(sSt, a0, a1, C.DETAIL_STEP)
		for q = 1, n do
			local cf, len = pieceCF(fr, q, latC)
			if cf then
				local base = cf * CFrame.new(0, -railH - bedH, 0)
				part(("%sTavan_%02d"):format(name, q - 1), Vector3.new(w, wall, len + 0.05),
					base * CFrame.new(0, hallH, 0), HALL_COLOR, Enum.Material.Concrete, parent)
				part(("%sDuvarL_%02d"):format(name, q - 1), Vector3.new(wall, hallH, len + 0.05),
					base * CFrame.new(-w / 2, hallH / 2, 0), HALL_COLOR, Enum.Material.Concrete, parent)
				part(("%sDuvarR_%02d"):format(name, q - 1), Vector3.new(wall, hallH, len + 0.05),
					base * CFrame.new(w / 2, hallH / 2, 0), HALL_COLOR, Enum.Material.Concrete, parent)
			end
		end
	end

	---------------------------------------------------------------- eski içeriği temizle
	-- BuildMarmaray'in parçaları: Platform_00, Platform1_00, HallRoof_0, Hall2WallL_3 ...
	-- PlatformMain* (ana hat / YHT peronları) DOKUNULMAZ.
	local function isOldSimple(n)
		return n:match("^Platform_%d+$") ~= nil
			or n:match("^Platform%d+_%d+$") ~= nil
			or n:match("^Hall") ~= nil
	end

	---------------------------------------------------------------- tek istasyon
	local function buildStation(st)
		local lay = L.Stations[st.name]
		local model = fSt:FindFirstChild(st.name)
		if not model or not model:IsA("Model") then
			model = Instance.new("Model"); model.Name = st.name; model.Parent = fSt
		end
		if C.CLEAN_OLD then
			for _, ch in ipairs(model:GetChildren()) do
				if ch:IsA("BasePart") and isOldSimple(ch.Name) then ch:Destroy() end
			end
		end
		local old = model:FindFirstChild("Standart")
		if old then old:Destroy() end

		local m = Instance.new("Model"); m.Name = "Standart"
		local label  = trUpper(st.name)
		local kunye  = ("%d  ·  km %.2f"):format(st.no, st.s / 1000)
		local anchor = nil

		-- peronları topla: {l0, l1, trackLat, bothEdges}
		local plats = {}
		if lay == nil then
			-- Layout'ta yok: hattın SAĞINA (negatif ofset) tek peron
			local hl = st.platformLength / 2
			plats[1] = { a0 = -hl, a1 = hl, l0 = -(1.5 + C.FALLBACK_WIDTH), l1 = -1.5,
				trackLat = 0, both = false, hall = { -(1.5 + C.FALLBACK_WIDTH) - 1, 4.5 } }
		elseif lay.type == "SIDE" then
			for idx, sd in ipairs(lay.sides) do
				local trackLat = (idx == 1) and 0 or (lay.track2 or 0)
				plats[idx] = { a0 = lay.a0, a1 = lay.a1, l0 = sd.l0, l1 = sd.l1,
					trackLat = trackLat, both = false,
					hall = { math.min(sd.l0, trackLat - 4.5), math.max(sd.l1, trackLat + 4.5) } }
			end
		else -- ISLAND: iki kenar da tren kenarı
			plats[1] = { a0 = lay.a0, a1 = lay.a1, l0 = lay.l0, l1 = lay.l1,
				trackLat = nil, both = true,
				hall = { math.min(lay.l0, -4.5), math.max(lay.l1, (lay.track2 or 0) + 4.5) } }
		end

		for idx, pl in ipairs(plats) do
			local suffix = (#plats > 1) and tostring(idx) or ""
			local lo, hi = math.min(pl.l0, pl.l1), math.max(pl.l0, pl.l1)
			local widthM = hi - lo
			local latC = (lo + hi) / 2

			-- 1) peron
			local mid = deck(m, "Peron" .. suffix, st.s, pl.a0, pl.a1, lo, hi, PLAT_COLOR)
			anchor = anchor or mid

			-- 2) kenar bantları
			local edges
			if pl.both then
				edges = { { lat = lo, dir = 1 }, { lat = hi, dir = -1 } }
			else
				-- tren kenarı = hatta en yakın kenar
				local tl2 = pl.trackLat or 0
				if math.abs(tl2 - lo) <= math.abs(tl2 - hi) then
					edges = { { lat = lo, dir = 1 } }
				else
					edges = { { lat = hi, dir = -1 } }
				end
			end
			edgeBands(m, "Kenar" .. suffix, st.s, pl.a0, pl.a1, edges)

			-- 4) üst örtü
			if st.underground then
				if C.CEILING then hallBox(m, "Hol" .. suffix, st.s, pl.a0, pl.a1, pl.hall[1], pl.hall[2]) end
			else
				-- Sundurma peron uçlarından 12 m geride biter: hem gerçekçi, hem de
				-- uçlardaki totemler (5.7 m) saçağı (3.75 m) delmez.
				if C.CANOPY and (pl.a1 - pl.a0) > 40 then
					canopy(m, "Sundurma" .. suffix, st.s, pl.a0 + 12, pl.a1 - 12, lo, hi)
				end
			end

			-- 3) isim panoları + 5) uçlarda no & kilometraj
			nameSigns(m, suffix, st.s, pl.a0, pl.a1, latC, widthM, label)
			totem(m, "Totem" .. suffix .. "_A", st.s, pl.a0 + 5, latC, label, kunye)
			totem(m, "Totem" .. suffix .. "_B", st.s, pl.a1 - 5, latC, label, kunye)
		end

		m:SetAttribute("StationNo", st.no)
		m:SetAttribute("Chainage_m", st.s)
		m:SetAttribute("Underground", st.underground)
		m:SetAttribute("PlatformType", lay and lay.type or "FALLBACK")
		m:SetAttribute("Template", "standard_station")
		m.Parent = model
		if anchor then
			m.PrimaryPart = anchor
			if model.PrimaryPart == nil then model.PrimaryPart = anchor end
		end
		return true
	end

	---------------------------------------------------------------- ana döngü
	local built, skipped = 0, 0
	local names = {}
	for _, st in ipairs(D.Stations) do
		if skip[st.name] or (only and not only[st.name]) then
			skipped += 1
		else
			local ok, err = pcall(buildStation, st)
			if ok then
				built += 1
				table.insert(names, st.name)
			else
				warn(("[StandardStation] %s kurulamadi: %s"):format(st.name, tostring(err)))
			end
			task.wait() -- her istasyondan sonra nefes: Studio donmasin
		end
	end

	print(("[StandardStation] bitti: %d istasyon, %d part (atlanan %d), OriginKm=%s")
		:format(built, partCount, skipped, tostring(originKm)))
	return { stations = names, built = built, skipped = skipped, parts = partCount, parent = fSt }
end
