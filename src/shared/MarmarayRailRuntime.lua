local R = {}
local K = 1/0.28
R.K = K
R.SpawnS = 41025
R.Spacing = 22.55
R.MaxSpeed = 80/3.6 -- commissioning limit; metres/second

function R.route()
 local nodes={}
 for _,folder in ipairs(workspace.Marmaray:GetChildren()) do
  if folder.Name:match('^Track_') then
   for _,seg in ipairs(folder:GetChildren()) do
    local bed=seg:FindFirstChild('Bed_T1')
    local s=seg:GetAttribute('Chainage_m')
    if bed and s then
     local len=bed.Size.Z-0.05
     local top=bed.CFrame* CFrame.new(0,(0.17+0.25)*K,0)
     table.insert(nodes,{s=s,a=top.Position-top.LookVector*len/2,b=top.Position+top.LookVector*len/2})
    end
   end
   task.wait()
  end
 end
 table.sort(nodes,function(a,b) return a.s<b.s end)
 assert(#nodes>0,'No built T1 track found')
 local maxGap=0
 for i=1,#nodes-1 do maxGap=math.max(maxGap,(nodes[i].b-nodes[i+1].a).Magnitude) end
 assert(maxGap<3,'Track contains gaps: '..maxGap)
 local last=nodes[#nodes]
 local finish=last.s+(last.b-last.a).Magnitude/K
 local function at(s)
  s=math.clamp(s,nodes[1].s,finish)
  local lo,hi=1,#nodes
  while lo<hi do local m=math.ceil((lo+hi)/2) if nodes[m].s<=s then lo=m else hi=m-1 end end
  local n=nodes[lo] local stop=nodes[lo+1] and nodes[lo+1].s or finish
  return n.a:Lerp(n.b,math.clamp((s-n.s)/(stop-n.s),0,1))
 end
 return {at=at,min=nodes[1].s,max=finish,count=#nodes,maxGap=maxGap}
end

function R.frame(route,s,reverse)
 local a,b=route.at(s-8.05),route.at(s+8.05)
 local x=(a-b).Unit
 if reverse then x=-x end
 local z=x:Cross(Vector3.yAxis).Unit
 local y=z:Cross(x).Unit
 return CFrame.fromMatrix((a+b)/2+Vector3.new(0,0.015,0),x,y,z)
end

function R.part(parent,name,size,cf,visible)
 local p=Instance.new('Part') p.Name=name p.Size=size p.CFrame=cf
 p.Anchored=true p.CanCollide=false p.CanTouch=false p.CanQuery=false
 p.Transparency=visible and 0 or 1 p.Color=Color3.fromRGB(45,47,51)
 p.Material=Enum.Material.SmoothPlastic p.Parent=parent
 return p
end

function R.gangways(train)
 local old=train:FindFirstChild('FlexibleGangways') if old then old:Destroy() end
 local folder=Instance.new('Folder') folder.Name='FlexibleGangways' folder.Parent=train
 local joints={}
 for i=1,4 do
  local f=Instance.new('Folder') f.Name='Connection_'..i f.Parent=folder
  local segments={}
  for j=1,18 do
   local parts={}
   for _,n in ipairs({'Floor','Left','Right','Roof','OuterLeft','OuterRight','OuterRoof','OuterBase','Coupler'}) do
    local p=R.part(f,n..j,Vector3.one,CFrame.new(),true)
    p.CollisionGroup='MarmarayTrain'
    p.CanCollide=not n:match('^Outer') and n~='Coupler'
    if n=='Floor' or n=='Left' or n=='Right' or n=='Roof' then p.Transparency=1 end
    if n=='Floor' then p.CanQuery=true p.Color=Color3.fromRGB(104,108,114) p.CustomPhysicalProperties=PhysicalProperties.new(1,0.8,0) end
    parts[n]=p
   end
   table.insert(segments,parts)
  end
  table.insert(joints,segments)
 end
 return joints
end

function R.updateGangways(cars,joints)
 local worst=0
 for i,segments in ipairs(joints) do
  local a=cars[i].RailRoot.CFrame
  local b=cars[i+1].RailRoot.CFrame
  local pa=a:PointToWorldSpace(Vector3.new(39.95,3.77,0))
  local pb=b:PointToWorldSpace(Vector3.new(i==4 and 39.95 or -39.95,3.77,0))
  worst=math.max(worst,(pb-pa).Magnitude)
  local delta=pb-pa
  local outerA=a:PointToWorldSpace(Vector3.new(40.1,3.79,0))
  local outerB=b:PointToWorldSpace(Vector3.new(i==4 and 40.1 or -40.1,3.79,0))
  if delta.Magnitude>0.001 then
   local x=delta.Unit local up=(a.UpVector+b.UpVector).Unit local z=x:Cross(up).Unit local y=z:Cross(x).Unit
   local len=delta.Magnitude/#segments+0.06
   for j,p in ipairs(segments) do
    local cf=CFrame.fromMatrix(pa:Lerp(pb,(j-0.5)/#segments),x,y,z)
    p.Floor.Size=Vector3.new(len,0.10,4.68) p.Floor.CFrame=cf*CFrame.new(0,-0.05,0)
    p.Floor.AssemblyLinearVelocity=Vector3.zero
    local rib=j%2==0 and 0.04 or 0
    p.Left.Size=Vector3.new(len,8.0,0.12+rib) p.Left.CFrame=cf*CFrame.new(0,4,-2.4)
    p.Right.Size=p.Left.Size p.Right.CFrame=cf*CFrame.new(0,4,2.4)
    p.Roof.Size=Vector3.new(len,0.16,4.96) p.Roof.CFrame=cf*CFrame.new(0,8.05,0)
    -- Full-width exterior accordion, separate from the narrow walk-through liner.
    local ribDepth=j%2==0 and 0.09 or 0.05
    local outerLen=(outerB-outerA).Magnitude/#segments+0.025
    local ocf=CFrame.fromMatrix(outerA:Lerp(outerB,(j-0.5)/#segments),x,y,z)
    p.OuterLeft.Size=Vector3.new(outerLen,8.85,ribDepth)
    p.OuterLeft.CFrame=ocf*CFrame.new(0,4.3,-4.62)
    p.OuterRight.Size=p.OuterLeft.Size p.OuterRight.CFrame=ocf*CFrame.new(0,4.3,4.62)
    p.OuterRoof.Size=Vector3.new(outerLen,ribDepth,9.28) p.OuterRoof.CFrame=ocf*CFrame.new(0,8.75,0)
    p.OuterBase.Size=Vector3.new(outerLen,ribDepth,9.28) p.OuterBase.CFrame=ocf*CFrame.new(0,-0.15,0)
    p.Coupler.Size=Vector3.new(outerLen,0.45,0.65) p.Coupler.CFrame=cf*CFrame.new(0,-1.2,0)
    for _,key in ipairs({'OuterLeft','OuterRight','OuterRoof','OuterBase'}) do p[key].Color=j%2==0 and Color3.fromRGB(43,45,48) or Color3.fromRGB(34,36,39) end
   end
  end
 end
 return worst
end

function R.interior(car,pivot)
 if car:FindFirstChild('InteriorRefreshRev11') then return end
 local folder=Instance.new('Folder') folder.Name='InteriorRefreshRev11' folder.Parent=car
 for _,p in ipairs(car:GetDescendants()) do if p:IsA('MeshPart') then
  if p.Name:match('Interior_Seat') then p.Color=Color3.fromRGB(8,174,194)
  elseif p.Name=='Interior_Floor' then p.Color=Color3.fromRGB(104,129,133)
  elseif p.Name:match('_Interior') or p.Name=='Roof_Grey' then p.Color=Color3.fromRGB(235,234,226)
  elseif p.Name:find('NeonOrange') then p.Material=Enum.Material.Neon end
 end end
 local function add(name,size,cf,color,neon)
  local p=R.part(folder,name,size,pivot*cf,true) p.Color=color p.Massless=true p.CollisionGroup='MarmarayTrain'
  if neon then p.Material=Enum.Material.Neon end
  local root=car:FindFirstChild('RailRoot')
  if root then local w=Instance.new('WeldConstraint') w.Part0=root w.Part1=p w.Parent=root end
  return p
 end
 local isCab=car:GetAttribute('CarIndex')==1 or car:GetAttribute('CarIndex')==5
 for j=1,7 do
  local x=-31.5+(j-1)*10.5
  if not isCab or x>-30 then
   add('CeilingPanel'..j,Vector3.new(10.43,0.07,4.45),CFrame.new(x,11.96,0),Color3.fromRGB(236,235,229))
   for side=-1,1,2 do
    local lamp=add('LightStrip'..j..'_'..side,Vector3.new(10.20,0.08,0.59),CFrame.new(x,11.62,side*2.83),Color3.fromRGB(255,251,236),true)
    local light=Instance.new('SurfaceLight') light.Name='PassengerLighting' light.Face=Enum.NormalId.Bottom light.Angle=115 light.Brightness=0.22 light.Range=10 light.Color=Color3.fromRGB(255,250,236) light.Shadows=false light.Parent=lamp
    for k=1,3 do add('VentSlot',Vector3.new(3.1,0.025,0.035),CFrame.new(x,11.91,side*(0.70+k*0.10)),Color3.fromRGB(105,110,109)) end
   end
  end
 end
 -- End vestibules need their own illumination beside the original rounded bellows.
 for _,x in ipairs(isCab and {36} or {-36,36}) do
  local lamp=add('VestibuleLamp',Vector3.new(1.6,0.06,0.55),CFrame.new(x,11.43,0),Color3.fromRGB(255,250,235),true)
  local light=Instance.new('PointLight') light.Brightness=0.18 light.Range=8 light.Shadows=false light.Color=Color3.fromRGB(255,247,229) light.Parent=lamp
 end
end

function R.panels(car)
 if car:FindFirstChild('DriverPanels') then return end
 local root=car:FindFirstChild('RailRoot')
 if not root or not car:FindFirstChild('DriverSeat') then return end
 local folder=Instance.new('Folder') folder.Name='DriverPanels' folder.Parent=car
 for _,spec in ipairs({{'DMI','Driver_DMI',0.47,0.3525,'HIZ / km-sa','000'},{'TCMS','Driver_TCMS',0.53,0.3975,'TREN DURUMU','FREN'},{'CCTV','Driver_CCTV',0.52,0.39,'KAMERA','PASIF'}}) do
  local original=nil for _,p in ipairs(car:GetDescendants()) do if p:IsA('MeshPart') and p.Name:find(spec[2],1,true) then original=p break end end
  if original then
   local n=Vector3.new(0.925,0.38,0).Unit local up=Vector3.new(-0.38,0.925,0).Unit
   local pos=root.CFrame:PointToObjectSpace(original.Position)+n*0.40+Vector3.new(0,0.25,0)
   local cf=root.CFrame*CFrame.fromMatrix(pos,Vector3.zAxis,up,-n)
   local panel=R.part(folder,spec[1],Vector3.new(spec[3]*K,spec[4]*K,0.12),cf,true)
   original.Transparency=1
   panel.Color=Color3.fromRGB(12,22,28) panel.Anchored=false panel.Massless=true
   local w=Instance.new('WeldConstraint') w.Part0=root w.Part1=panel w.Parent=root
   local gui=Instance.new('SurfaceGui') gui.Name='Screen' gui.Face=Enum.NormalId.Front gui.CanvasSize=Vector2.new(600,450) gui.LightInfluence=0 gui.Brightness=1 gui.Parent=panel
   local bg=Instance.new('Frame') bg.Name='Main' bg.Size=UDim2.fromScale(1,1) bg.BackgroundColor3=Color3.fromRGB(9,25,37) bg.BorderSizePixel=0 bg.Parent=gui
   local title=Instance.new('TextLabel') title.Size=UDim2.fromScale(1,0.22) title.BackgroundTransparency=1 title.Text=spec[5] title.TextColor3=Color3.fromRGB(167,206,221) title.Font=Enum.Font.Gotham title.TextSize=34 title.Parent=bg
   local value=title:Clone() value.Name='Value' value.Position=UDim2.fromScale(0,0.28) value.Size=UDim2.fromScale(1,0.55) value.Text=spec[6] value.Font=Enum.Font.GothamBold value.TextSize=spec[1]=='DMI' and 140 or 62 value.TextColor3=Color3.fromRGB(225,237,237) value.Parent=bg
  end
 end
 local lamp=R.part(folder,'ConsoleLight',Vector3.new(0.1,0.1,0.1),root.CFrame*CFrame.new(-34,10.3,0),false)
 lamp.Anchored=false lamp.Massless=true local w=Instance.new('WeldConstraint') w.Part0=root w.Part1=lamp w.Parent=root
 local light=Instance.new('PointLight') light.Brightness=0.28 light.Range=7 light.Color=Color3.fromRGB(238,243,239) light.Shadows=false light.Parent=lamp
end

function R.doorDetails(car)
 if car:FindFirstChild('DoorDetailsRev13') then return end
 local root=car:FindFirstChild('RailRoot') if not root then return end
 local folder=Instance.new('Folder') folder.Name='DoorDetailsRev13' folder.Parent=car
 local white=Color3.fromRGB(230,230,222) local rubber=Color3.fromRGB(28,30,31)
 local yellow=Color3.fromRGB(231,220,16) local metal=Color3.fromRGB(157,164,167)
 local function add(name,size,cf,color,target,shape)
  local p=R.part(folder,name,size,root.CFrame*cf,true) p.Color=color p.Anchored=false p.Massless=true
  if shape then p.Shape=shape end
  p.CollisionGroup='MarmarayTrain'
  if color==metal then p.Material=Enum.Material.Metal p.Reflectance=0.08 end
  local w=Instance.new('WeldConstraint') w.Part0=target or root w.Part1=p w.Parent=p
  return p
 end
 for _,side in ipairs({'L','R'}) do for number=1,5 do
  local prefix='Door_'..side..number
  local a=car:FindFirstChild(prefix..'a_Interior',true) local b=car:FindFirstChild(prefix..'b_Interior',true)
  if a and b then
   local ap=root.CFrame:PointToObjectSpace(a.Position) local bp=root.CFrame:PointToObjectSpace(b.Position)
   local x=(ap.X+bp.X)/2 local z=(ap.Z+bp.Z)/2 local sign=math.sign(z) z-=sign*0.20
   add(prefix..'_Threshold',Vector3.new(6.15,0.045,0.48),CFrame.new(x,3.82,z-sign*0.05),metal)
   for k=-2,2 do add(prefix..'_SillGroove',Vector3.new(6.0,0.012,0.018),CFrame.new(x,3.85,z-sign*0.05+k*0.075),rubber) end
  end
 end end
 local index=car:GetAttribute('CarIndex')
 for _,endSign in ipairs((index==1 or index==5) and {1} or {-1,1}) do
  local x=endSign*38.55
  for _,side in ipairs({-1,1}) do
   local z=side*3.75
   for _,y in ipairs({6.0,9.2}) do
    -- Fine cabinet seams and small black quarter-turn latches.
    for _,dz in ipairs({-0.8,0.8}) do add('EndPanelSeam',Vector3.new(0.018,2.8,0.018),CFrame.new(x,y,z+dz),rubber) end
    for _,dy in ipairs({-1.4,1.4}) do add('EndPanelSeam',Vector3.new(0.018,0.018,1.6),CFrame.new(x,y+dy,z),rubber) end
    add('CabinetLatch',Vector3.new(0.035,0.10,0.10),CFrame.new(x-endSign*0.02,y-1.15,z+0.61),rubber,nil,Enum.PartType.Cylinder)
   end
  end
  add('GangwayThreshold',Vector3.new(0.65,0.045,4.45),CFrame.new(endSign*38.8,3.82,0),metal)
  for k=-2,2 do add('GangwayThresholdGroove',Vector3.new(0.018,0.012,4.4),CFrame.new(endSign*38.8+k*0.10,3.85,0),rubber) end
 end
end

function R.destinations(car)
 if car:FindFirstChild('DestinationDisplays') then return end
 local root=car:FindFirstChild('RailRoot');if not root then return end
 local folder=Instance.new('Folder');folder.Name='DestinationDisplays';folder.Parent=car
 for _,p in car:GetDescendants() do
  if p:IsA('MeshPart') and p.Name=='Dest_Text_NeonOrange' then p.Transparency=1 end
  if p:IsA('MeshPart') and p.Name=='Exterior_Details_NeonOrange' then p.Material=Enum.Material.SmoothPlastic;p.Color=Color3.fromRGB(40,29,15) end
 end
 local function display(name,pos,right,up,back,w,h)
  local p=R.part(folder,name,Vector3.new(w,h,.025),root.CFrame*CFrame.fromMatrix(pos,right,up,back),true)
  p.Color=Color3.fromRGB(6,8,9);p.Anchored=false;p.Massless=true;p.CollisionGroup='MarmarayTrain'
  local weld=Instance.new('WeldConstraint');weld.Part0=root;weld.Part1=p;weld.Parent=p
  local gui=Instance.new('SurfaceGui');gui.Name='Sign';gui.Face=Enum.NormalId.Front;gui.CanvasSize=Vector2.new(640,90);gui.LightInfluence=0;gui.Brightness=1;gui.AlwaysOnTop=false;gui.Parent=p
  local text=Instance.new('TextLabel');text.Name='Destination';text.Size=UDim2.fromScale(1,1);text.BorderSizePixel=0;text.BackgroundColor3=Color3.fromRGB(6,8,9);text.TextColor3=Color3.fromRGB(243,166,59);text.Font=Enum.Font.RobotoMono;text.TextSize=65;text.Text='GEBZE';text.Parent=gui
 end
 for _,side in ipairs({-1,1}) do for j,x in ipairs({-1.97,2.06}) do
  display('Side_'..side..'_'..j,Vector3.new(-x*K,3.13*K,side*1.465*K),Vector3.new(-side,0,0),Vector3.yAxis,Vector3.new(0,0,-side),1*K,.13*K)
 end end
 if car:FindFirstChild('DriverSeat') then display('Front',Vector3.new(-37.60,11.843,0),-Vector3.zAxis,Vector3.yAxis,Vector3.xAxis,4.15,.46) end
end

function R.setDestination(train,destination)
 train:SetAttribute('Destination',destination)
 for _,car in train:GetChildren() do local folder=car:FindFirstChild('DestinationDisplays');if folder then
  for _,p in folder:GetChildren() do local gui=p:FindFirstChild('Sign');if gui then gui.Destination.Text=destination end end
 end end
end

function R.prepare(train,route,s)
 local cars={}
 for _,c in ipairs(train:GetChildren()) do if c:IsA('Model') and c:GetAttribute('CarIndex') then cars[c:GetAttribute('CarIndex')]=c end end
 assert(#cars==5,'Expected five indexed cars')
 for i,car in ipairs(cars) do
  R.interior(car,car:GetPivot())
  if not car:FindFirstChild('RailRoot') then
   local pivot=car:GetPivot()
   local root=R.part(car,'RailRoot',Vector3.new(3,1,3),pivot,false)
   root.RootPriority=127 root.CustomPhysicalProperties=PhysicalProperties.new(10,0.5,0)
   car.PrimaryPart=root
   local function proxy(name,size,localCF)
    local p=R.part(car,name,size,pivot*localCF,false) p.CanCollide=true p.CanQuery=true return p
   end
   proxy('WalkableFloor',Vector3.new(77.4,0.3,9.9),CFrame.new(0,3.6,0))
   for _,side in ipairs({-1,1}) do proxy('SideCollision'..side,Vector3.new(77.4,8.2,0.15),CFrame.new(0,7.7,side*5.1)) end
   if i==1 or i==5 then
    local seat=Instance.new('VehicleSeat') seat.Name='DriverSeat' seat.Size=Vector3.new(2,0.6,2)
    seat.CFrame=pivot*CFrame.new(-32.7,5.1,0)*CFrame.Angles(0,math.pi/2,0)
    seat.Transparency=1 seat.Anchored=true seat.HeadsUpDisplay=false seat.MaxSpeed=0 seat.Torque=0 seat.Parent=car
    local prompt=Instance.new('ProximityPrompt') prompt.Name='DrivePrompt' prompt.ActionText='Sürücü koltuğuna otur' prompt.ObjectText='Marmaray' prompt.MaxActivationDistance=12 prompt.RequiresLineOfSight=false prompt.Parent=seat
   end
   for _,p in ipairs(car:GetDescendants()) do
    if p:IsA('BasePart') then
     p.CollisionGroup='MarmarayTrain'
     if p:IsA('MeshPart') then p.CanCollide=false p.CanTouch=false end
     -- Keep the original authored bellows visible.
     -- Invisible walking supports and a narrow seam seal follow each joint.
     if p.Name:match('^Gangway_') then p.Transparency=0 end
     if p~=root then
      p.Massless=true
      local w=Instance.new('WeldConstraint') w.Name='TrainWeld' w.Part0=root w.Part1=p w.Parent=root
     end
    end
   end
   local att=Instance.new('Attachment') att.Name='RailGuide' att.Parent=root
   local pos=Instance.new('AlignPosition') pos.Name='RailPosition' pos.Mode=Enum.PositionAlignmentMode.OneAttachment pos.Attachment0=att pos.ApplyAtCenterOfMass=true pos.MaxForce=1e9 pos.MaxVelocity=180 pos.Responsiveness=100 pos.Parent=root
   local ori=Instance.new('AlignOrientation') ori.Name='RailOrientation' ori.Mode=Enum.OrientationAlignmentMode.OneAttachment ori.Attachment0=att ori.MaxTorque=1e9 ori.MaxAngularVelocity=5 ori.Responsiveness=100 ori.Parent=root
  end
  for _,p in ipairs(car:GetDescendants()) do if p:IsA('MeshPart') and p.Name:match('^Gangway_') then p.Transparency=0 end end
  car:PivotTo(R.frame(route,s-(i-1)*R.Spacing,i==5))
  local root=car.RailRoot root.RailPosition.Position=root.Position root.RailOrientation.CFrame=root.CFrame.Rotation
  root.RailPosition.RigidityEnabled=true
  root.RailPosition.ApplyAtCenterOfMass=false
  root.RailOrientation.Responsiveness=200
  root.RailOrientation.RigidityEnabled=true
  R.panels(car)
  R.doorDetails(car)
  R.destinations(car)
  task.wait()
 end
 local joints=R.gangways(train)
 R.updateGangways(cars,joints)
 return cars,joints
end

-- One-dimensional traction/brake dynamics; lateral/vertical guidance uses constraints.
function R.integrate(v,a,throttle,brake,grade,dt)
 local drag=0.015+0.00012*v*v
 local desired=throttle*0.9-9.81*grade
 if math.abs(v)>0.01 then desired-=math.sign(v)*(drag+brake*1.25) elseif brake>0 then desired=0 end
 local step=1.1*dt
 a+=math.clamp(desired-a,-step,step)
 local nv=v+a*dt
 if brake>0 and throttle==0 and v*nv<0 then nv=0 a=0 end
 if math.abs(nv)<0.015 and throttle==0 and brake>0 then nv=0 a=0 end
 return math.clamp(nv,-R.MaxSpeed,R.MaxSpeed),a
end
return R



