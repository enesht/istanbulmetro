local RS=game:GetService('ReplicatedStorage')
local Players=game:GetService('Players')
local R=require(RS:WaitForChild('MarmarayRailRuntime'))
local remote=RS:WaitForChild('MarmarayTrainControl')
local template=game.ServerStorage:WaitForChild('MarmarayTrainTemplate')
local route=R.route()
local train,cars,joints
local s,v,a=R.SpawnS,0,0
local throttle,brake,driver=0,1,nil
local lastCommand,lastSpawn,lastMessage=0,-100,{}
local suspension={}
local spawning=false
local boarding=false
local function notice(p,message) remote:FireClient(p,'Notice',message) end
local function activeSeat(player)
 for _,car in ipairs(cars or {}) do local seat=car:FindFirstChild('DriverSeat') if seat and seat.Occupant and Players:GetPlayerFromCharacter(seat.Occupant.Parent)==player then return seat,car:GetAttribute('CarIndex') end end
end
local function board(player,seat,teleport)
 if spawning or boarding then notice(player,'Kabin giriş işlemi sürüyor.') return end
 if math.abs(v)>0.1 then notice(player,'Kabine geçmek için treni durdur.') return end
 if driver and driver~=player then notice(player,'Treni başka bir makinist kullanıyor.') return end
 for _,c in ipairs(cars or {}) do
  local other=c:FindFirstChild('DriverSeat')
  if other and other.Occupant and Players:GetPlayerFromCharacter(other.Occupant.Parent)~=player then
   notice(player,'Treni başka bir makinist kullanıyor.') return
  end
 end
 local character=player.Character
 local hum=character and character:FindFirstChildOfClass('Humanoid')
 local root=character and character:FindFirstChild('HumanoidRootPart')
 if not hum or hum.Health<=0 or not root or not seat or not seat.Parent then return end
 if seat.Occupant==hum then return end
 if seat.Occupant then notice(player,'Bu koltuk dolu.') return end
 if not teleport and (root.Position-seat.Position).Magnitude>=18 then return end
 -- Reserve before the first yield, across both cab seats.
 boarding=true driver=player throttle=0 brake=1 lastCommand=os.clock()
 train:SetAttribute('DriverUserId',player.UserId)
 local ok,err=pcall(function()
  if hum.SeatPart then hum.Sit=false task.wait(0.15) end
  if player.Character~=character or hum.Health<=0 or not seat.Parent then return end
  if teleport then character:PivotTo(seat.CFrame*CFrame.new(0,3,0)) task.wait(0.15) end
  if player.Character~=character or hum.Health<=0 or not seat.Parent or seat.Occupant then return end
  seat:Sit(hum)
  for _=1,10 do if seat.Occupant==hum then break end task.wait(0.05) end
 end)
 boarding=false
 if not ok then warn('[Marmaray boarding] '..tostring(err)) end
 if not activeSeat(player) then driver=nil throttle=0 brake=1 end
 train:SetAttribute('DriverUserId',driver and driver.UserId or 0)
 lastCommand=os.clock()
end

local function spawnTrain()
 spawning=true
 if train then train:Destroy() end
 local preview=workspace:FindFirstChild('Marmaray_5li_Set') if preview then preview:Destroy() end
 train=Instance.new('Model') train.Name='Marmaray_5li_Set' train.ModelStreamingMode=Enum.ModelStreamingMode.Persistent train.Parent=workspace
 -- Insert cars separately to keep large map insertion responsive.
 for _,c in ipairs(template:GetChildren()) do if c:IsA('Model') then c:Clone().Parent=train task.wait() end end
 s,v,a=R.SpawnS,0,0 throttle,brake,driver=0,1,nil
 suspension={}
 cars,joints=R.prepare(train,route,s)
 R.setDestination(train,'GEBZE')
 for _,car in ipairs(cars) do
  for _,p in ipairs(car:GetDescendants()) do if p:IsA('BasePart') then p.Anchored=false end end
  for _,p in car:GetDescendants() do if p:IsA('BasePart') then p:SetAttribute('RailLocalCF',car.RailRoot.CFrame:ToObjectSpace(p.CFrame)) end end
  car.RailRoot.Anchored=true
  car.RailRoot.RailPosition.Enabled=false
  car.RailRoot.RailOrientation.Enabled=false
  for _,spec in ipairs({{'RailSound','18940522285'},{'MotorSound','137730930796096'}}) do
   local sound=Instance.new('Sound');sound.Name=spec[1];sound.SoundId='rbxassetid://'..spec[2]
   sound.Looped=true;sound.Volume=0;sound.RollOffMinDistance=8;sound.RollOffMaxDistance=95
   sound.Parent=car.RailRoot;sound:Play()
  end
  local seat=car:FindFirstChild('DriverSeat')
  if seat then
   seat.CanTouch=false -- Only the validated prompt/UI may seat a driver.
   seat.DrivePrompt.Triggered:Connect(function(player) board(player,seat,false) end)
   seat:GetPropertyChangedSignal('Occupant'):Connect(function()
    local hum=seat.Occupant
    if not hum then return end
    local p=Players:GetPlayerFromCharacter(hum.Parent)
    if not p or (driver and driver~=p) then hum.Sit=false return end
    driver=p lastCommand=os.clock()
    train:SetAttribute('DriverUserId',p.UserId)
   end)
  end
 end
 local count=0 for _,c in cars do for _,p in c:GetDescendants() do if p:IsA('BasePart') then count+=1 end end end
 train:SetAttribute('VisualPartCount',count)
 lastSpawn=os.clock()
 spawning=false
end
spawnTrain()
remote.OnServerEvent:Connect(function(player,action,value)
 if type(action)~='string' then return end
 if spawning then return end
 local now=os.clock()
 if action=='Input' then if now-(lastMessage[player] or 0)<0.045 then return end lastMessage[player]=now end
 if action=='Enter' then
  board(player,cars[value==5 and 5 or 1].DriverSeat,true)
 elseif action=='Respawn' then
  if boarding or (driver and driver~=player) then notice(player,'Kabin kullanımda.') return end
  if math.abs(v)>0.05 then notice(player,'Tren hareket ederken yeniden getirilemez.') return end
  if now-lastSpawn<15 then notice(player,'Yeniden getirmeden önce birkaç saniye bekle.') return end
  -- Never remove a train containing another passenger.
  for _,p in ipairs(Players:GetPlayers()) do
   local root=p.Character and p.Character:FindFirstChild('HumanoidRootPart')
   if root then for _,c in ipairs(cars) do local q=c.RailRoot.CFrame:PointToObjectSpace(root.Position) if math.abs(q.X)<43 and math.abs(q.Z)<7 and q.Y>-1 and q.Y<16 then notice(player,'Yeniden getirmek için trendeki herkes dışarı çıkmalı.') return end end end
  end
  spawnTrain()
 elseif action=='Input' and type(value)=='table' then
  local seat,index=activeSeat(player) if not seat or (driver and driver~=player) then return end
  local t,b=value.throttle,value.brake
  if type(t)~='number' or type(b)~='number' or t~=t or b~=b or math.abs(t)==math.huge or math.abs(b)==math.huge then return end
  if math.abs(v)<.14 and (value.direction==1 or value.direction==-1) then
   local destination=value.direction*(index==5 and -1 or 1)>0 and 'GEBZE' or 'HALKALI'
   if train:GetAttribute('Destination')~=destination then R.setDestination(train,destination) end
  end
  driver=player throttle=math.clamp(t,-1,1)*(index==5 and -1 or 1) brake=math.clamp(b,0,1) lastCommand=now
 end
end)
Players.PlayerRemoving:Connect(function(p) lastMessage[p]=nil if driver==p then driver=nil throttle=0 brake=1 end end)
local accumulator=0
local poseAccumulator=0
game:GetService('RunService').Heartbeat:Connect(function(dt)
 if not train or not train.Parent then return end
 dt=math.min(dt,0.1)
 if driver and not boarding and (not activeSeat(driver) or os.clock()-lastCommand>0.6) then throttle=0 brake=1 if not activeSeat(driver) then driver=nil end end
 if not driver then throttle=0 brake=1 end
 local p0,p1=route.at(s-1),route.at(s+1)
 local grade=(p1.Y-p0.Y)/math.max((p1-p0).Magnitude,0.01)
 local edge= v>=0 and route.max-s-14 or s-route.min-4*R.Spacing-14
 if edge<v*v/(2*0.8)+5 then throttle=0 brake=1 end
 if throttle*v<0 and math.abs(v)>0.5 then throttle=0 brake=1 end
 v,a=R.integrate(v,a,throttle,brake,grade,dt)
 s=math.clamp(s+v*dt,route.min+4*R.Spacing+12,route.max-12)
 local maxError=0 local maxTilt=0
 for i,c in ipairs(cars) do
  local cf=R.frame(route,s-(i-1)*R.Spacing,i==5)
  local ahead=R.frame(route,s-(i-1)*R.Spacing+3,i==5)
  local turn=cf.RightVector:Cross(ahead.RightVector).Y/6
  local lateral=math.clamp(turn*v*v,-1.5,1.5)
  local state=suspension[i] or {roll=0,pitch=0}
  local alpha=1-math.exp(-dt*3.5)
  state.roll+=(math.clamp(lateral*0.003,-0.008,0.008)-state.roll)*alpha
  state.pitch+=(math.clamp(a*0.0025,-0.004,0.004)-state.pitch)*alpha
  suspension[i]=state
  cf=cf*CFrame.Angles(state.roll,0,state.pitch*(i==5 and -1 or 1))
  local old=c.RailRoot.CFrame
  c:PivotTo(cf)
  c.RailRoot.AssemblyLinearVelocity=Vector3.zero
  c.RailRoot.AssemblyAngularVelocity=Vector3.zero
  c.RailRoot.RailPosition.Position=cf.Position c.RailRoot.RailOrientation.CFrame=cf.Rotation
  maxError=math.max(maxError,(c.RailRoot.Position-cf.Position).Magnitude)
  maxTilt=math.max(maxTilt,math.deg(math.acos(math.clamp(c.RailRoot.CFrame.UpVector:Dot(cf.UpVector),-1,1))))
 end
 poseAccumulator+=dt
 if poseAccumulator>=.05 then
  poseAccumulator=0
  local poses={} for i,c in ipairs(cars) do poses[i]=c.RailRoot.CFrame end
  remote:FireAllClients('Pose',{train=train,time=workspace:GetServerTimeNow(),poses=poses})
 end
 local gap=R.updateGangways(cars,joints)
 if maxError>12 then throttle=0 brake=1 end
 accumulator+=dt
 if accumulator>0.1 then
  accumulator=0 train:SetAttribute('SpeedKmh',math.abs(v)*3.6) train:SetAttribute('SignedSpeedMps',v)
  train:SetAttribute('SpeedLimitKmh',R.MaxSpeed*3.6) train:SetAttribute('ChainageM',s) train:SetAttribute('Brake',brake) train:SetAttribute('Throttle',throttle)
  train:SetAttribute('GuideErrorStuds',maxError) train:SetAttribute('GangwaySpanStuds',gap)
  train:SetAttribute('GuideTiltErrorDegrees',maxTilt)
  train:SetAttribute('DriverUserId',driver and driver.UserId or 0)
  train:SetAttribute('AccelerationMps2',a) train:SetAttribute('Grade',grade)
  for _,c in ipairs(cars) do local panels=c:FindFirstChild('DriverPanels') if panels then
   if panels:FindFirstChild('DMI') then panels.DMI.Screen.Main.Value.Text=string.format('%03d',math.floor(math.abs(v)*3.6+0.5)) end
   if panels:FindFirstChild('TCMS') then panels.TCMS.Screen.Main.Value.Text=brake>0.1 and 'FREN' or math.abs(throttle)>0.1 and 'CEKIS' or 'BOSTA' end
  end end
  for _,c in ipairs(cars) do local seat=c:FindFirstChild('DriverSeat') if seat then seat.DrivePrompt.Enabled=not boarding and not driver and math.abs(v)<0.1 and seat.Occupant==nil end end
 end
end)
print('[Marmaray] Five-car train ready at Bostanci; rail guided physics active.')

