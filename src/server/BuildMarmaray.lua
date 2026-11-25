--[[
BuildMarmaray (ModuleScript)  —  Marmaray ray + istasyon kurucu (3 hat)

KURULUM (Rojo)
  src/shared/MarmarayData.lua    -> ReplicatedStorage.MarmarayData
  src/shared/MarmarayLayout.lua  -> ReplicatedStorage.MarmarayLayout
  src/server/BuildMarmaray.lua   -> ServerStorage.BuildMarmaray

  Command Bar (edit modu):
    require(game.ServerStorage.BuildMarmaray)({ START_KM = 19, END_KM = 34 })  -- sadece tünel bölgesi
    require(game.ServerStorage.BuildMarmaray)()                                 -- tüm hat (~76 km)
  Not: Workspace > FallenPartsDestroyHeight değerini -2000 yap (tünel -58 m ≈ -207 stud).

HATLAR  (yanal ofset metre; + = seyir yönünün (Halkalı->Gebze) SOLU, - = SAĞI)
  Yol 1   ofset 0                       Gebze yönü banliyö  = MarmarayData ekseni
  Yol 2   ofset Layout.track2Offset(s)  Halkalı yönü banliyö (SOLA kayık)
  Yol 3   ofset Layout.MainLineOffset    ana hat (YHT/yük); sadece Layout.hasMainLine(s), tünelde yok

  Dünya uzayında sol vektör: left = Vector3.yAxis:Cross(forward).Unit
  Bütün yanal konumlandırma dünya uzayında `left` ile yapılır; parçanın yerel CFrame'i
  yalnızca düşey ofset ve simetrik genişlikler için kullanılır (yerel +X = SAĞ).

TÜNEL KABUĞU
  Yol 2 ofseti > 9 m  -> her hatta ayrı tek hatlı tüp
  Yol 2 ofseti <= 9 m -> Boğaz batırma tüpü: iki hattı saran tek geniş kutu

PERONLAR (Layout.Stations)
  ISLAND -> l0..l1 yanal sınır, a0..a1 boyuna sınır (istasyon kilometrajına göre)
  SIDE   -> sides[] içindeki her hat için ayrı peron
  extra  -> ana hat / YHT peronları, farklı renk
  Peron üstü = ray üstü + 1.1 m. Viraja uysun diye ~10 m'lik parçalarla eksen takip edilir.
]]

local DEFAULT = {
	STUDS_PER_METER = 1 / 0.28, -- Roblox karakter ölçeği (1 stud = 0.28 m). 1 stud = 1 ft için 3.28084
	V_SCALE = 1,               -- dikey abartı (1 = gerçek)
	SUBDIV = 2,                -- her 20 m'lik veri aralığını kaç parçaya böl (Catmull-Rom yumuşatma)
	START_KM = 0, END_KM = 80, -- kurulacak kilometraj aralığı
	ORIGIN_KM = nil,           -- verilirse hat YATAYDA kaydırılır: bu kilometraj (0,y,0)'a gelir.
	                           -- Terrain ±32000 stud ile sınırlı; bölümü kendi merkezine almak
	                           -- 1:1 ölçeği bozmadan terrain'i mümkün kılar. Y (deniz seviyesi)
	                           -- datumu KORUNUR, sadece X/Z kayar. nil = kaydırma yok.
	RAILS = true,              -- iki ray parçası ekle
	TUNNEL_SHELL = true,       -- tünel segmentlerine duvar + tavan ekle
	STATIONS = true,
	MAIN_LINE = true,          -- 3. hat (ana hat)
	PLATFORM_STEP = 10,        -- peron parçası uzunluğu (m)
	WIDE_TUBE_MAX = 9,         -- bu ofsete kadar (m) tek geniş kutu, üstünde ayrı tüpler
	YIELD_EVERY = 400,
}

local COLORS = {
	[0] = Color3.fromRGB(120, 105, 90),  -- yerüstü balast
	[1] = Color3.fromRGB(70, 70, 75),    -- tünel
	[2] = Color3.fromRGB(170, 170, 165), -- köprü
	[3] = Color3.fromRGB(135, 115, 95),  -- yarma
}
local RAIL_COLOR     = Color3.fromRGB(90, 90, 95)
local MAINLINE_COLOR = Color3.fromRGB(95, 90, 80)   -- 3. hat yatağı
local PLAT_COLOR     = Color3.fromRGB(200, 200, 195) -- banliyö peronu
local PLAT_EXTRA     = Color3.fromRGB(196, 168, 110) -- ana hat / YHT peronu
local HALL_COLOR     = Color3.fromRGB(90, 90, 95)

return function(user)
	local C = table.clone(DEFAULT)
	for k, v in pairs(user or {}) do C[k] = v end
	local RS = game:GetService("ReplicatedStorage")
	local D = require(RS:WaitForChild("MarmarayData"))
	local L = require(RS:WaitForChild("MarmarayLayout"))
	local k = C.STUDS_PER_METER

	local root = workspace:FindFirstChild("Marmaray") or Instance.new("Folder")
	root.Name = "Marmaray"; root.Parent = workspace
	-- Koordinatlarin anlami ORIGIN_KM'ye bagli; kaydedilmezse sonradan cozulemez.
	local prevOrigin = root:GetAttribute("OriginKm")
	if prevOrigin ~= C.ORIGIN_KM then
		if #root:GetChildren() > 0 then
			warn(("[Marmaray] UYARI: mevcut icerik OriginKm=%s ile kurulmus, simdi %s isteniyor. "
				.. "Farkli origin'ler ayni klasorde KARISIR; once Workspace.Marmaray'i silin."):format(
				tostring(prevOrigin), tostring(C.ORIGIN_KM)))
		end
		root:SetAttribute("OriginKm", C.ORIGIN_KM)
	end
	local fTrack = Instance.new("Folder")
	fTrack.Name = ("Track_%g-%gkm"):format(C.START_KM, C.END_KM)
	fTrack:SetAttribute("OriginKm", C.ORIGIN_KM)
	fTrack:SetAttribute("StudsPerMeter", k)
	fTrack.Parent = root
	local fSt = root:FindFirstChild("Stations") or Instance.new("Folder"); fSt.Name = "Stations"; fSt.Parent = root

	local function P(i) i = math.clamp(i, 1, #D.S); return D.toStuds(D.X[i], D.Y[i], D.Z[i], k, C.V_SCALE) end
	local function catmull(p0, p1, p2, p3, t)
		local t2, t3 = t * t, t * t * t
		return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
	end
	-- kilometrajdan (m) Catmull-Rom eksen noktası (kaydırmasız, ham dünya koordinatı)
	local function axisRaw(sm)
		local n = #D.S
		sm = math.clamp(sm, D.S[1], D.S[n])
		local i = math.clamp(math.floor(sm / D.Step) + 1, 1, n - 1)
		while i < n - 1 and D.S[i + 1] <= sm do i += 1 end
		while i > 1 and D.S[i] > sm do i -= 1 end
		local t = (sm - D.S[i]) / (D.S[i + 1] - D.S[i])
		return catmull(P(i - 1), P(i), P(i + 1), P(i + 2), t)
	end
	-- Yatay kaydırma: ORIGIN_KM verilirse o kilometraj X=0,Z=0'a oturur.
	-- Y kaydırılmaz; deniz seviyesi datumu korunur (tünel dibi yine ~-207 stud).
	local originOffset = Vector3.zero
	if C.ORIGIN_KM then
		local o = axisRaw(C.ORIGIN_KM * 1000)
		originOffset = Vector3.new(o.X, 0, o.Z)
	end
	local function axisAt(sm)
		return axisRaw(sm) - originOffset
	end
	-- kilometrajda konum + teğet + sol vektör
	local function frameAt(sm)
		local p = axisAt(sm)
		local fwd = axisAt(sm + 2) - axisAt(sm - 2)
		if fwd.Magnitude < 1e-5 then fwd = Vector3.zAxis else fwd = fwd.Unit end
		local left = Vector3.yAxis:Cross(fwd)
		if left.Magnitude < 1e-5 then left = Vector3.xAxis else left = left.Unit end
		return { p = p, fwd = fwd, left = left }
	end
	local function lateral(f, offsetM) -- dünya uzayında yanal ofset
		if offsetM == 0 then return f.p end
		return f.p + f.left * (offsetM * k)
	end

	local function part(name, size, cf, color, material, parent)
		local p = Instance.new("Part")
		p.Name = name; p.Anchored = true; p.Size = size; p.CFrame = cf
		p.Color = color; p.Material = material or Enum.Material.SmoothPlastic
		p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		p.Parent = parent
		return p
	end

	local bedW, bedH = 3.2 * k, 0.5 * k
	local railW, railH = 0.07 * k, 0.17 * k
	local halfG = (D.Gauge / 2 + 0.035) * k
	local tunW, tunH, wall = 7.0 * k, 6.5 * k, 0.5 * k
	local platH = 1.1 * k

	-- bir hattın tek segmenti: a -> b (ofset uygulanmış dünya noktaları)
	local function trackPiece(parent, suffix, a, b, typ, bedColor)
		local len = (b - a).Magnitude
		if len <= 0.01 then return 0 end
		local mid = (a + b) / 2
		local cf = CFrame.lookAt(mid, b, Vector3.yAxis) -- rayın üst yüzeyi = mid
		local n = 0
		part("Bed" .. suffix, Vector3.new(bedW, bedH, len + 0.05), cf * CFrame.new(0, -railH - bedH / 2, 0),
			bedColor, typ == 0 and Enum.Material.Slate or Enum.Material.Concrete, parent)
		n += 1
		if C.RAILS then
			for _, side in ipairs({ -1, 1 }) do
				part("Rail" .. suffix, Vector3.new(railW, railH, len + 0.05), cf * CFrame.new(side * halfG, -railH / 2, 0),
					RAIL_COLOR, Enum.Material.Metal, parent)
				n += 1
			end
		end
		return n
	end

	-- tünel tüpü: merkez ekseni a -> b, iç genişlik widthStuds
	local function tube(parent, suffix, a, b, widthStuds)
		local len = (b - a).Magnitude
		if len <= 0.01 then return 0 end
		local mid = (a + b) / 2
		local cf = CFrame.lookAt(mid, b, Vector3.yAxis)
		local base = cf * CFrame.new(0, -railH - bedH, 0)
		part("WallL" .. suffix, Vector3.new(wall, tunH, len + 0.05), base * CFrame.new(-widthStuds / 2, tunH / 2, 0), COLORS[1], Enum.Material.Concrete, parent)
		part("WallR" .. suffix, Vector3.new(wall, tunH, len + 0.05), base * CFrame.new(widthStuds / 2, tunH / 2, 0), COLORS[1], Enum.Material.Concrete, parent)
		part("Roof" .. suffix, Vector3.new(widthStuds + wall, wall, len + 0.05), base * CFrame.new(0, tunH, 0), COLORS[1], Enum.Material.Concrete, parent)
		return 3
	end

	---------------------------------------------------------------- HAT
	local count, partCount = 0, 0
	local sMin, sMax = C.START_KM * 1000, C.END_KM * 1000
	local step = D.Step / C.SUBDIV
	local prevS = nil
	local prevF = nil

	for i = 1, #D.S - 1 do
		local s0 = D.S[i]
		if s0 >= sMin and s0 < sMax then
			local typ = D.T[i]
			if prevS ~= s0 then prevS, prevF = s0, frameAt(s0) end
			for j = 1, C.SUBDIV do
				local sb = s0 + j * step
				local fb = frameAt(sb)
				local sa = sb - step
				local sMid = sa + step / 2

				local seg = Instance.new("Model")
				seg.Name = ("seg_%06d"):format(math.floor(sa))

				-- Yol 1: eksen
				partCount += trackPiece(seg, "_T1", prevF.p, fb.p, typ, COLORS[typ] or COLORS[0])

				-- Yol 2: Halkalı yönü, SOLA kayık
				local o2a, o2b = L.track2Offset(sa), L.track2Offset(sb)
				local t2a, t2b = lateral(prevF, o2a), lateral(fb, o2b)
				partCount += trackPiece(seg, "_T2", t2a, t2b, typ, COLORS[typ] or COLORS[0])

				-- Yol 3: ana hat (sağda), tünelde yok
				if C.MAIN_LINE and typ ~= 1 and L.hasMainLine(sMid) then
					partCount += trackPiece(seg, "_T3",
						lateral(prevF, L.MainLineOffset), lateral(fb, L.MainLineOffset), typ, MAINLINE_COLOR)
				end

				-- Tünel kabuğu
				if C.TUNNEL_SHELL and typ == 1 then
					local o2m = L.track2Offset(sMid)
					if o2m > C.WIDE_TUBE_MAX then
						partCount += tube(seg, "_T1", prevF.p, fb.p, tunW)
						partCount += tube(seg, "_T2", t2a, t2b, tunW)
					else
						-- Boğaz batırma tüpü: iki hattı saran tek kutu
						local ca, cb = lateral(prevF, o2a / 2), lateral(fb, o2b / 2)
						partCount += tube(seg, "_Tube", ca, cb, math.max(o2a, o2b) * k + tunW)
					end
				end

				seg:SetAttribute("Chainage_m", sa)
				seg:SetAttribute("Type", D.TypeNames[typ])
				seg:SetAttribute("Track2Offset_m", o2b)
				seg.Parent = fTrack
				count += 1
				prevF, prevS = fb, sb
				if count % C.YIELD_EVERY == 0 then
					task.wait()
					print(("[Marmaray] %d segment, km %.2f"):format(count, s0 / 1000))
				end
			end
		else
			prevS, prevF = nil, nil
		end
	end

	---------------------------------------------------------------- PERONLAR
	-- ~10 m'lik parçalarla hat eksenini takip eden peron şeridi
	local function platformStrip(parent, name, sSt, a0, a1, l0, l1, color)
		local width = math.abs(l1 - l0) * k
		if width < 0.1 then return 0, nil end
		local latC = (l0 + l1) / 2
		local n = math.max(1, math.ceil((a1 - a0) / C.PLATFORM_STEP))
		local segLen = (a1 - a0) / n
		local made, middle = 0, nil
		for q = 0, n - 1 do
			local fa = frameAt(sSt + a0 + q * segLen)
			local fb = frameAt(sSt + a0 + (q + 1) * segLen)
			local pa, pb = lateral(fa, latC), lateral(fb, latC)
			local len = (pb - pa).Magnitude
			if len > 0.01 then
				local mid = (pa + pb) / 2
				local cf = CFrame.lookAt(mid, pb, Vector3.yAxis)
				local p = part(("%s_%02d"):format(name, q), Vector3.new(width, platH, len + 0.05),
					cf * CFrame.new(0, platH / 2, 0), color, Enum.Material.Concrete, parent)
				made += 1
				if q == math.floor(n / 2) then middle = p end
			end
		end
		return made, middle
	end

	-- yeraltı istasyon kutusu (latLo..latHi yanal aralığını saran)
	local function hallBox(parent, name, sSt, a0, a1, latLo, latHi)
		local hallH = 9 * k
		local w = (latHi - latLo) * k + 2 * wall
		local latC = (latLo + latHi) / 2
		local n = math.max(1, math.ceil((a1 - a0) / 20))
		local segLen = (a1 - a0) / n
		local made = 0
		for q = 0, n - 1 do
			local fa = frameAt(sSt + a0 + q * segLen)
			local fb = frameAt(sSt + a0 + (q + 1) * segLen)
			local pa, pb = lateral(fa, latC), lateral(fb, latC)
			local len = (pb - pa).Magnitude
			if len > 0.01 then
				local mid = (pa + pb) / 2
				local cf = CFrame.lookAt(mid, pb, Vector3.yAxis)
				local base = cf * CFrame.new(0, -railH - bedH, 0)
				part(name .. "Roof_" .. q, Vector3.new(w, wall, len + 0.05), base * CFrame.new(0, hallH, 0), HALL_COLOR, Enum.Material.Concrete, parent)
				part(name .. "WallL_" .. q, Vector3.new(wall, hallH, len + 0.05), base * CFrame.new(-w / 2, hallH / 2, 0), HALL_COLOR, Enum.Material.Concrete, parent)
				part(name .. "WallR_" .. q, Vector3.new(wall, hallH, len + 0.05), base * CFrame.new(w / 2, hallH / 2, 0), HALL_COLOR, Enum.Material.Concrete, parent)
				made += 3
			end
		end
		return made
	end

	local stCount = 0
	if C.STATIONS then
		for _, st in ipairs(D.Stations) do
			if st.s >= sMin and st.s <= sMax and not fSt:FindFirstChild(st.name) then
				local lay = L.Stations[st.name]
				local m = Instance.new("Model"); m.Name = st.name
				local anchor = nil

				if lay == nil then
					-- Layout'ta yoksa: eski basit peron (hattın sağına)
					local _, mid = platformStrip(m, "Platform", st.s, -st.platformLength / 2, st.platformLength / 2,
						1.5, 1.5 + 8, PLAT_COLOR)
					anchor = mid
				elseif lay.type == "SIDE" then
					for idx, sd in ipairs(lay.sides) do
						local _, mid = platformStrip(m, ("Platform%d"):format(idx), st.s, lay.a0, lay.a1, sd.l0, sd.l1, PLAT_COLOR)
						anchor = anchor or mid
						if st.underground then
							-- her hat kendi istasyon tüneli içinde
							local trackLat = (idx == 1) and 0 or lay.track2
							local lo = math.min(sd.l0, trackLat - 4.5)
							local hi = math.max(sd.l1, trackLat + 4.5)
							hallBox(m, ("Hall%d"):format(idx), st.s, lay.a0, lay.a1, lo, hi)
						end
					end
				else -- ISLAND
					local _, mid = platformStrip(m, "Platform", st.s, lay.a0, lay.a1, lay.l0, lay.l1, PLAT_COLOR)
					anchor = mid
					if st.underground then
						local lo = math.min(lay.l0, -4.5)
						local hi = math.max(lay.l1, (lay.track2 or 0) + 4.5)
						hallBox(m, "Hall", st.s, lay.a0, lay.a1, lo, hi)
					end
				end

				-- ana hat / YHT peronları (farklı renk)
				if lay and lay.extra then
					for idx, ex in ipairs(lay.extra) do
						platformStrip(m, ("PlatformMain%d"):format(idx), st.s, ex.a0, ex.a1, ex.l0, ex.l1, PLAT_EXTRA)
					end
				end

				if anchor then
					local bb = Instance.new("BillboardGui"); bb.Size = UDim2.fromOffset(240, 50); bb.StudsOffset = Vector3.new(0, 12, 0); bb.AlwaysOnTop = true
					bb.MaxDistance = 3000
					local tl = Instance.new("TextLabel"); tl.Size = UDim2.fromScale(1, 1); tl.BackgroundColor3 = Color3.fromRGB(0, 70, 140)
					tl.TextColor3 = Color3.new(1, 1, 1); tl.TextScaled = true; tl.Font = Enum.Font.GothamBold
					tl.Text = ("%d · %s (%+.0f m)"):format(st.no, st.name, st.railTop); tl.Parent = bb; bb.Parent = anchor
					m.PrimaryPart = anchor
				end
				for key, v in pairs(st) do
					if type(v) ~= "table" then m:SetAttribute(key, v) end
				end
				if lay then
					m:SetAttribute("PlatformType", lay.type)
					if lay.platforms then m:SetAttribute("Platforms", lay.platforms) end
					if lay.note then m:SetAttribute("Note", lay.note) end
				end
				m.Parent = fSt
				stCount += 1
				task.wait()
			end
		end
	end

	print(("[Marmaray] bitti: %d segment, %d hat parcasi, %d istasyon"):format(count, partCount, stCount))
	return root
end
