local Players=game:GetService('Players')
local UIS=game:GetService('UserInputService')
local RS=game:GetService('ReplicatedStorage')
local Run=game:GetService('RunService')
local player=Players.LocalPlayer
local remote=RS:WaitForChild('MarmarayTrainControl')
local previous=player:WaitForChild('PlayerGui'):FindFirstChild('MarmarayDriving')
if previous then previous:Destroy() end
local gui=Instance.new('ScreenGui');gui.Name='MarmarayDriving';gui.ResetOnSpawn=false;gui.Parent=player.PlayerGui
local frame=Instance.new('Frame');frame.Name='ControlPanel';frame.Size=UDim2.fromOffset(320,342);frame.AnchorPoint=Vector2.new(0,1);frame.Position=UDim2.new(0,16,1,-16);frame.BackgroundColor3=Color3.fromRGB(22,26,30);frame.BorderSizePixel=0;frame.Parent=gui
local corner=Instance.new('UICorner');corner.CornerRadius=UDim.new(0,6);corner.Parent=frame
local scale=Instance.new('UIScale');scale.Parent=frame
local function label(parent,text,x,y,w,h,size,color)
 local p=Instance.new('TextLabel');p.Text=text;p.Position=UDim2.fromOffset(x,y);p.Size=UDim2.fromOffset(w,h);p.BackgroundTransparency=1;p.TextColor3=color or Color3.fromRGB(233,237,239);p.TextSize=size;p.Font=Enum.Font.GothamMedium;p.TextXAlignment=Enum.TextXAlignment.Left;p.Parent=parent;return p
end
local speedText=label(frame,'0',16,6,91,48,38);speedText.Font=Enum.Font.RobotoMono
label(frame,'km/sa',108,26,55,20,12,Color3.fromRGB(151,161,168))
local stateText=label(frame,'BEKLEME',172,12,100,22,12)
local limitText=label(frame,'Sınır 80',172,34,100,18,11,Color3.fromRGB(151,161,168))
local body=Instance.new('Frame');body.Name='Controls';body.Position=UDim2.fromOffset(0,68);body.Size=UDim2.new(1,0,1,-68);body.BackgroundTransparency=1;body.Parent=frame
local function button(text,x,y,w,fn)
 local b=Instance.new('TextButton');b.Text=text;b.Size=UDim2.fromOffset(w,32);b.Position=UDim2.fromOffset(x,y);b.BackgroundColor3=Color3.fromRGB(43,49,54);b.BorderSizePixel=0;b.TextColor3=Color3.fromRGB(225,230,232);b.TextSize=12;b.Font=Enum.Font.GothamMedium;b.Parent=body
 local c=Instance.new('UICorner');c.CornerRadius=UDim.new(0,4);c.Parent=b;b.Activated:Connect(fn);return b
end
local expanded=true
local toggle
toggle=button('−',278,-57,28,function() expanded=not expanded;toggle.Text=expanded and '−' or '+';body.Visible=expanded;frame.Size=UDim2.fromOffset(320,expanded and 342 or 68) end)
toggle.Parent=frame;toggle.Position=UDim2.fromOffset(278,16)
toggle.Name='ToggleControls'
local notch=-4;local direction=1;local driving=false;local lastSeat=nil;local muted=false
local hint=label(body,'Kumanda için bir kabine geç.',16,214,288,40,11,Color3.fromRGB(158,169,176));hint.TextWrapped=true
local messageUntil=0
local function notice(t) hint.Text=t;messageUntil=os.clock()+3 end
local function change(n)
 if not driving then notice('Önce sürücü koltuğuna otur.') return end
 notch=math.clamp(n,-4,4)
end
button('Ön kabin',16,0,89,function() remote:FireServer('Enter',1) end)
button('Arka kabin',115,0,89,function() remote:FireServer('Enter',5) end)
button('Treni getir',214,0,90,function() remote:FireServer('Respawn') end)
local notchText=label(body,'FREN 4',16,42,135,24,16)
local directionButton
directionButton=button('Yön: İleri',180,39,124,function()
 local train=workspace:FindFirstChild('Marmaray_5li_Set')
 if train and (train:GetAttribute('SpeedKmh') or 0)>.5 then notice('Yön değiştirmek için dur.') return end
 direction=-direction;notch=-4;directionButton.Text=direction==1 and 'Yön: İleri' or 'Yön: Geri'
end)
local bars={}
for i=1,8 do local p=Instance.new('Frame');p.Position=UDim2.fromOffset(16+(i-1)*37,73);p.Size=UDim2.fromOffset(29,5);p.BorderSizePixel=0;p.Parent=body;bars[i]=p end
button('− Fren',16,91,89,function() change(notch-1) end)
button('Boşa al',115,91,89,function() change(0) end)
button('Güç +',214,91,90,function() change(notch+1) end)
local emergency=button('ACİL FREN',16,132,188,function() change(-4) end);emergency.BackgroundColor3=Color3.fromRGB(115,43,39)
local soundButton
soundButton=button('Ses: Açık',214,132,90,function() muted=not muted;soundButton.Text=muted and 'Ses: Kapalı' or 'Ses: Açık' end)
UIS.InputBegan:Connect(function(input,processed)
 if processed then return end
 if input.KeyCode==Enum.KeyCode.W then change(notch+1)
 elseif input.KeyCode==Enum.KeyCode.S then change(notch-1)
 elseif input.KeyCode==Enum.KeyCode.Space then change(-4) end
end)
UIS.WindowFocusReleased:Connect(function() notch=-4 end)
remote.OnClientEvent:Connect(function(action,message) if action=='Notice' then notice(message) end end)
local elapsed=0
Run.Heartbeat:Connect(function(dt)
 elapsed+=dt;if elapsed<.1 then return end;elapsed=0
 local camera=workspace.CurrentCamera;if camera then scale.Scale=math.min(1,(camera.ViewportSize.X-24)/320,(camera.ViewportSize.Y-24)/342) end
 local train=workspace:FindFirstChild('Marmaray_5li_Set')
 local hum=player.Character and player.Character:FindFirstChildOfClass('Humanoid');local seat=hum and hum.SeatPart
 if seat~=lastSeat then notch=-4;direction=1;directionButton.Text='Yön: İleri';lastSeat=seat end
 driving=train~=nil and seat~=nil and seat.Name=='DriverSeat' and seat:IsDescendantOf(train)
 local speed=train and train:GetAttribute('SpeedKmh') or 0
 speedText.Text=string.format('%d',math.floor(speed+.5))
 local brake=train and train:GetAttribute('Brake') or 1;local power=train and math.abs(train:GetAttribute('Throttle') or 0) or 0
 stateText.Text=brake>.05 and 'FREN' or power>.05 and 'ÇEKİŞ' or 'BOŞTA'
 limitText.Text='Sınır '..tostring(train and train:GetAttribute('SpeedLimitKmh') or 80)
 notchText.Text=notch<0 and ('FREN '..-notch) or notch>0 and ('GÜÇ '..notch) or 'BOŞTA'
 for i,p in bars do local active=notch<0 and i>4+notch and i<=4 or notch>0 and i>4 and i<=4+notch;p.BackgroundColor3=active and (notch<0 and Color3.fromRGB(215,142,82) or Color3.fromRGB(62,164,155)) or Color3.fromRGB(58,64,69) end
 if os.clock()>messageUntil then hint.Text=driving and 'W / S  kademe   ·   Space  acil fren\nSağ fare: bakış · V: öne dön · C: kamera' or 'Kumanda için bir kabine geç.' end
 if driving then remote:FireServer('Input',{throttle=math.max(notch,0)/4*direction,brake=math.max(-notch,0)/4,direction=direction}) end
 if train then for _,car in train:GetChildren() do local root=car:FindFirstChild('RailRoot');if root then
  local roll=root:FindFirstChild('RailSound');local motor=root:FindFirstChild('MotorSound')
  if roll then roll.Volume=muted and 0 or math.clamp(speed/80,0,1)*.32;roll.PlaybackSpeed=.65+math.clamp(speed/80,0,1)*.65 end
  if motor then motor.Volume=muted and 0 or power*.18;motor.PlaybackSpeed=.75+math.clamp(speed/80,0,1)*.65 end
 end end end
end)

-- Render all five cars from one timestamp, before the camera and gangways.
local poseQueue={}
local poseTrain=nil
local renderParts,renderOffsets,renderIndices={},{},{}
local function resetPoses(train)
 poseTrain=train;poseQueue={};renderParts={};renderOffsets={};renderIndices={}
end
remote.OnClientEvent:Connect(function(action,data)
 if action~='Pose' or type(data)~='table' or not data.train then return end
 if poseTrain~=data.train then resetPoses(data.train) end
 if #poseQueue>0 and data.time<=poseQueue[#poseQueue].time then return end
 table.insert(poseQueue,data)
 while #poseQueue>12 do table.remove(poseQueue,1) end
end)
local passengerFrames=nil
local passengerCar=nil
local passengerCharacter=nil
local passengerAirUntil=0
local passengerRay=RaycastParams.new()
passengerRay.FilterType=Enum.RaycastFilterType.Include
passengerRay.RespectCanCollide=true
Run.PreSimulation:Connect(function()
 if not poseTrain or not poseTrain.Parent or #poseQueue<2 then return end
 if #renderParts==0 then
  local parts,offsets,indices={},{},{}
  for _,car in poseTrain:GetChildren() do local i=car:GetAttribute('CarIndex');if i then
   for _,p in car:GetDescendants() do if p:IsA('BasePart') then
    local offset=p:GetAttribute('RailLocalCF');if not offset then return end
    table.insert(parts,p);table.insert(offsets,offset);table.insert(indices,i)
   end end
  end end
  if #parts~=(poseTrain:GetAttribute('VisualPartCount') or -1) then return end
  renderParts,renderOffsets,renderIndices=parts,offsets,indices
 end
 local target=workspace:GetServerTimeNow()-.10
 while #poseQueue>2 and poseQueue[2].time<=target do table.remove(poseQueue,1) end
 local a,b=poseQueue[1],poseQueue[2]
 local alpha=math.clamp((target-a.time)/math.max(b.time-a.time,.001),0,1)
 -- Hold the latest complete sample on a network stall; never stretch one car ahead.
 if target>b.time then a=poseQueue[#poseQueue-1];b=poseQueue[#poseQueue];alpha=1 end
 local frames={} for i=1,5 do frames[i]=a.poses[i]:Lerp(b.poses[i],alpha) end
 local poses=table.create(#renderParts)
 for j,p in renderParts do
  if not p.Parent then renderParts={};return end
  poses[j]=frames[renderIndices[j]]*renderOffsets[j]
 end

 local character=player.Character
 local hum=character and character:FindFirstChildOfClass('Humanoid')
 local root=character and character:FindFirstChild('HumanoidRootPart')
 if character~=passengerCharacter then
  passengerCharacter=character;passengerCar=nil;passengerFrames=nil
 end
 if root and hum and hum.Health>0 and not hum.SeatPart and passengerFrames then
  passengerRay.FilterDescendantsInstances={poseTrain}
  local hit=workspace:Raycast(root.Position,Vector3.new(0,-(hum.HipHeight+root.Size.Y/2+1.2),0),passengerRay)
  local grounded=hit and (hit.Instance.Name=='WalkableFloor' or hit.Instance.Name:match('^Floor%d+$'))
  local selected=nil
  local best=math.huge
  for i,cf in ipairs(passengerFrames) do
   local q=cf:PointToObjectSpace(root.Position)
   if math.abs(q.X)<43 and math.abs(q.Z)<4.9 and q.Y>3.2 and q.Y<12 then
    if grounded or (passengerCar==i and os.clock()<passengerAirUntil) then
     if math.abs(q.X)<best then best=math.abs(q.X);selected=i end
    end
   end
  end
  if selected then
   if grounded then passengerAirUntil=os.clock()+1 end
   local delta=frames[selected]*passengerFrames[selected]:Inverse()
   local displacement=(delta*root.CFrame).Position-root.Position
   if displacement.Magnitude<8 then
    root.CFrame=delta*root.CFrame
    root.AssemblyLinearVelocity=delta:VectorToWorldSpace(root.AssemblyLinearVelocity)
   end
   passengerCar=selected
  else passengerCar=nil end
 else passengerCar=nil end
 workspace:BulkMoveTo(renderParts,poses,Enum.BulkMoveMode.FireCFrameChanged)
 passengerFrames=frames
 for _,car in poseTrain:GetChildren() do
  local railRoot=car:FindFirstChild('RailRoot')
  if railRoot then railRoot.AssemblyLinearVelocity=Vector3.zero;railRoot.AssemblyAngularVelocity=Vector3.zero end
 end
 gui:SetAttribute('PassengerCar',passengerCar or 0)
 poseTrain:SetAttribute('ClientPoseAge',workspace:GetServerTimeNow()-b.time)
end)

-- Draw bellows from the currently displayed car poses, avoiding replication lag
-- between many independent anchored strips and their neighbouring car bodies.
local gangwayRuntime=require(RS:WaitForChild('MarmarayRailRuntime'))
local visualTrain,visualCars,visualJoints=nil,nil,nil
game:GetService('RunService'):BindToRenderStep('MarmarayGangwayVisuals',Enum.RenderPriority.Camera.Value+2,function()
 local train=workspace:FindFirstChild('Marmaray_5li_Set')
 if train~=visualTrain then visualTrain=train visualCars=nil visualJoints=nil end
 if not train then return end
 if not visualCars then
  local cars={} for _,c in ipairs(train:GetChildren()) do if c:IsA('Model') and c:GetAttribute('CarIndex') and c:FindFirstChild('RailRoot') then cars[c:GetAttribute('CarIndex')]=c end end
  local folder=train:FindFirstChild('FlexibleGangways') if #cars~=5 or not folder then return end
  local joints={}
  for i=1,4 do
   local f=folder:FindFirstChild('Connection_'..i) if not f then return end
   local segments={}
   for j=1,18 do local parts={} for _,key in ipairs({'Floor','Left','Right','Roof','OuterLeft','OuterRight','OuterRoof','OuterBase','Coupler'}) do
    local part=f:FindFirstChild(key..j) if not part then return end parts[key]=part
   end table.insert(segments,parts) end
   joints[i]=segments
  end
  visualCars=cars visualJoints=joints
 end
 gangwayRuntime.updateGangways(visualCars,visualJoints)
end)

-- Damped cab movement: acceleration and curves have direction, not random shaking.
local Run=game:GetService('RunService')
local CAS=game:GetService('ContextActionService')
local cabView=true local wasDriving=false local yaw,pitch=0,0
local targetYaw,targetPitch=0,-0.17
local lookHeld=false
local savedMouse=Enum.MouseBehavior.Default
local stick=Vector2.zero
local orbitYaw,orbitPitch,orbitDistance=.7,.27,60
local orbitTargetYaw,orbitTargetPitch=.7,.27
local function toggleCamera()
 cabView=not cabView;lookHeld=false;UIS.MouseBehavior=Enum.MouseBehavior.Default
end
button('Kamera (C)',16,173,139,toggleCamera)
button('Kalk (X)',165,173,139,function() local h=player.Character and player.Character:FindFirstChildOfClass('Humanoid') if h then h.Sit=false end end)
local sway,rate=Vector3.zero,Vector3.zero
local baseFov=workspace.CurrentCamera.FieldOfView
local previousForward=nil local phase=0
UIS.InputBegan:Connect(function(input,processed)
 if not processed and input.KeyCode==Enum.KeyCode.C then toggleCamera() end
 if not processed and input.KeyCode==Enum.KeyCode.X then local h=player.Character and player.Character:FindFirstChildOfClass('Humanoid') if h then h.Sit=false end end
end)
UIS.InputBegan:Connect(function(input,processed)
 if processed then return end
 if input.UserInputType==Enum.UserInputType.MouseButton2 then lookHeld=true end
 if input.KeyCode==Enum.KeyCode.V then targetYaw,targetPitch=0,-.17;orbitTargetYaw,orbitTargetPitch=.7,.27 end
end)
UIS.InputEnded:Connect(function(input)
 if input.UserInputType==Enum.UserInputType.MouseButton2 then lookHeld=false;UIS.MouseBehavior=savedMouse end
end)
UIS.WindowFocusReleased:Connect(function() lookHeld=false;UIS.MouseBehavior=savedMouse end)
UIS.InputChanged:Connect(function(input)
 if input.KeyCode==Enum.KeyCode.Thumbstick2 then stick=Vector2.new(input.Position.X,input.Position.Y) end
 if wasDriving and not cabView and input.UserInputType==Enum.UserInputType.MouseWheel then orbitDistance=math.clamp(orbitDistance-input.Position.Z*7,20,180) end
end)
local lookTouch=nil
UIS.TouchStarted:Connect(function(input,processed)
 if not processed and input.Position.X>workspace.CurrentCamera.ViewportSize.X*.45 then lookTouch=input end
end)
UIS.TouchMoved:Connect(function(input)
 if input==lookTouch and wasDriving then
  if not cabView then orbitTargetYaw-=input.Delta.X*.004;orbitTargetPitch=math.clamp(orbitTargetPitch+input.Delta.Y*.004,-.15,1.2);return end
  targetYaw=math.clamp(targetYaw-input.Delta.X*.004,-2.95,2.95)
  targetPitch=math.clamp(targetPitch-input.Delta.Y*.004,-1.05,.95)
 end
end)
UIS.TouchEnded:Connect(function(input) if input==lookTouch then lookTouch=nil end end)
Run:BindToRenderStep('MarmarayCabSuspension',Enum.RenderPriority.Camera.Value+1,function(dt)
 local camera=workspace.CurrentCamera
 local h=player.Character and player.Character:FindFirstChildOfClass('Humanoid')
 local seat=h and h.SeatPart
 local driving=seat~=nil and seat.Name=='DriverSeat'
 if player.Character and (driving or wasDriving) then
  for _,p in ipairs(player.Character:GetDescendants()) do if p:IsA('BasePart') then p.LocalTransparencyModifier=(driving and cabView) and 1 or 0 end end
 end
 if driving and not wasDriving then
  savedMouse=UIS.MouseBehavior
  yaw,pitch=0,-0.17 targetYaw,targetPitch=0,-0.17 previousForward=nil sway,rate=Vector3.zero,Vector3.zero
  CAS:BindActionAtPriority('MarmarayBrakeNoJump',function(_,state) if state==Enum.UserInputState.Begin then notch=-4 end return Enum.ContextActionResult.Sink end,false,3000,Enum.KeyCode.Space)
 elseif not driving and wasDriving then
  lookHeld=false UIS.MouseBehavior=savedMouse
  CAS:UnbindAction('MarmarayBrakeNoJump') camera.CameraType=Enum.CameraType.Custom camera.CameraSubject=h camera.FieldOfView=baseFov
 end
 wasDriving=driving
 if not driving then return end
 local train=workspace:FindFirstChild('Marmaray_5li_Set') if not train then return end
 if not cabView then
  camera.CameraType=Enum.CameraType.Scriptable
  if lookHeld then
   UIS.MouseBehavior=Enum.MouseBehavior.LockCurrentPosition
   local delta=UIS:GetMouseDelta();orbitTargetYaw-=delta.X*.004;orbitTargetPitch=math.clamp(orbitTargetPitch+delta.Y*.004,-.15,1.2)
  else UIS.MouseBehavior=Enum.MouseBehavior.Default end
  if stick.Magnitude>.15 then orbitTargetYaw-=stick.X*dt*1.8;orbitTargetPitch=math.clamp(orbitTargetPitch-stick.Y*dt*1.4,-.15,1.2) end
  local alpha=1-math.exp(-14*dt)
  orbitYaw+=(orbitTargetYaw-orbitYaw)*alpha;orbitPitch+=(orbitTargetPitch-orbitPitch)*alpha
  local root=seat.Parent:FindFirstChild('RailRoot');if not root then return end
  local focus=root.CFrame:PointToWorldSpace(Vector3.new(0,6,0))
  local basis=seat.CFrame.Rotation*CFrame.Angles(0,orbitYaw,0)
  local offset=basis:VectorToWorldSpace(Vector3.new(0,math.sin(orbitPitch)*orbitDistance,math.cos(orbitPitch)*orbitDistance))
  local params=RaycastParams.new();params.FilterType=Enum.RaycastFilterType.Exclude;params.FilterDescendantsInstances={train,player.Character}
  local hit=workspace:Raycast(focus,offset,params)
  local pos=hit and hit.Position+hit.Normal*.8 or focus+offset
  if (pos-focus).Magnitude>.1 then camera.CFrame=CFrame.lookAt(pos,focus) end
  camera.Focus=CFrame.new(focus);camera.FieldOfView=baseFov
  gui:SetAttribute('CameraMode','Exterior');gui:SetAttribute('OrbitDistance',orbitDistance)
  previousForward=nil
  return
 end
 gui:SetAttribute('CameraMode','Cab')
 camera.CameraType=Enum.CameraType.Scriptable
 if lookHeld then
  UIS.MouseBehavior=Enum.MouseBehavior.LockCurrentPosition
  local delta=UIS:GetMouseDelta()
  targetYaw=math.clamp(targetYaw-delta.X*.003,-2.95,2.95)
  targetPitch=math.clamp(targetPitch-delta.Y*.003,-1.05,.95)
 else UIS.MouseBehavior=savedMouse end
 if stick.Magnitude>.15 then
  targetYaw=math.clamp(targetYaw-stick.X*dt*1.8,-2.95,2.95)
  targetPitch=math.clamp(targetPitch+stick.Y*dt*1.4,-1.05,.95)
 end
 local smooth=1-math.exp(-18*dt)
 yaw+=(targetYaw-yaw)*smooth;pitch+=(targetPitch-pitch)*smooth
 gui:SetAttribute('LookYaw',yaw);gui:SetAttribute('LookPitch',pitch)
 dt=math.min(dt,1/30)
 local speed=(train:GetAttribute('SpeedKmh') or 0)/3.6
 local accel=train:GetAttribute('AccelerationMps2') or 0
 local f=seat.CFrame.LookVector
 local turn=previousForward and previousForward:Cross(f).Y/math.max(dt,0.001) or 0 previousForward=f
 local lat=math.clamp(turn*speed,-2,2)
 local cabSign=seat.Parent:GetAttribute('CarIndex')==5 and -1 or 1
 phase+=speed*dt
 local bounce=math.sin(phase*1.7)*math.min(speed/22,1)*0.018
 local target=Vector3.new(-accel*cabSign*0.025+bounce,0,-lat*0.022+math.sin(phase*0.63)*math.min(speed/22,1)*0.008)
 rate+=(target-sway)*(28*dt)-rate*(8*dt) sway+=rate*dt
 camera.CFrame=seat.CFrame*CFrame.new(0,4.2,-0.6)*CFrame.Angles(pitch,yaw,0)*CFrame.Angles(sway.X,0,sway.Z)
 camera.FieldOfView=baseFov+math.min(speed/22,1)*3
end)

