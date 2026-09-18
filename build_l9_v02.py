from pathlib import Path
import ast
import hashlib
import math
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path('D:/bowen/demo/blender-demo')
OUTPUT = ROOT / 'output'
original = OUTPUT / 'L9_exterior_v01.blend'
original_hash = hashlib.sha256(original.read_bytes()).hexdigest()
assert not bpy.data.scenes.get('L9_Exterior_v02'), 'V02 already exists; do not replace it.'
scene = bpy.data.scenes.new('L9_Exterior_v02')
bpy.context.window.scene = scene
model = bpy.data.collections.new('AI_Model_L9_v02')
stage = bpy.data.collections.new('L9_Studio_v02')
scene.collection.children.link(model)
scene.collection.children.link(stage)
scene.unit_settings.system = 'METRIC'
source = ast.parse((ROOT / 'build_l9.py').read_text(encoding='utf-8'))
functions = [node for node in source.body if isinstance(node, ast.FunctionDef)]
exec(compile(ast.Module(body=functions, type_ignores=[]), 'l9_shared_functions', 'exec'))

paint = material('V02_Warm_Graphite', (.055,.052,.044), .55,.30)
silver = material('V02_Champagne', (.36,.35,.315), .60,.28)
glass = material('V02_Smoked_Glass', (.008,.014,.017), .18,.19)
frontglass = material('V02_Windshield', (.020,.029,.050), .20,.21)
black = material('V02_Black', (.008,.009,.010), .15,.35)
rubber = material('V02_Rubber', (.011,.012,.014), 0,.62)
chrome = material('V02_Satin_Chrome', (.32,.34,.35), .8,.26)
alloy = material('V02_Wheel_Dark', (.072,.077,.079), .70,.30)
alloy_light = material('V02_Wheel_Facet', (.16,.17,.18), .75,.28)
rotor = material('V02_Brake', (.10,.11,.12), .7,.48)
red = material('V02_Dark_Red', (.15,.008,.009), .2,.25)
lens = material('V02_Lens', (.04,.052,.065), .35,.15)
plate = material('V02_Plate', (.52,.55,.58), .15,.35)

profile = [(0,.29),(.72,.29),(.90,.30),(.959,.37),(.975,.46),(.969,.61),
           (.952,.72),(.964,.82),(.985,.88),(1.003,.98),(1.002,1.10),
           (.985,1.21),(.963,1.255),(.89,1.279),(.69,1.30),(0,1.307)]
profile += [(-width,height) for width,height in reversed(profile[1:-1])]
stations = [(-2.63,.80,-.03),(-2.625,.86,-.005),(-2.60,.94,0),(-2.53,.982,0),
            (-2.40,1,0),(-2.13,1,0),(-1.64,1.012,0),(-1.25,.994,0),(-.9,.986,0),
            (-.2,.988,0),(.4,.986,0),(.93,.996,0),(1.25,1.009,-.005),(1.62,1.014,-.025),
            (1.96,1.008,-.038),(2.20,1,-.05),(2.40,.985,-.07),(2.52,.955,-.09),
            (2.58,.90,-.115),(2.60,.82,-.12),(2.605,.78,-.12)]
body = loft('V02_Body_Shell', [[(along,width*scale,height+offset) for width,height in profile]
                             for along,scale,offset in stations], paint,2)
bpy.context.view_layer.objects.active=body
bpy.ops.object.modifier_apply(modifier='Surface refinement')
for vertex in body.data.vertices:
    along,lateral,height=vertex.co
    if along>2.25:
        factor=min(1,(along-2.25)/.30)
        vertex.co.x += factor*(.054*math.exp(-((height-.56)/.22)**2)-.075*max(0,(height-.86)/.4))
    if along<-2.35:
        factor=min(1,(-along-2.35)/.25)
        vertex.co.x += factor*(.07*math.exp(-((height-.86)/.09)**2)+.055*math.exp(-((height-.38)/.12)**2))


def cut(target, cutter, name):
    bpy.context.view_layer.objects.active=cutter
    for modifier in list(cutter.modifiers):
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    modifier=target.modifiers.new(name,'BOOLEAN')
    modifier.operation='DIFFERENCE'
    modifier.solver='EXACT'
    modifier.object=cutter
    bpy.context.view_layer.objects.active=target
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter,do_unlink=True)


for along in [-1.53,1.66]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.500,depth=2.8,
                                      location=(along,0,.445),rotation=(math.pi/2,0,0))
    cut(body,bpy.context.object,'Wheel arch')
cut(body,box('V02_Intake_Cutter',(2.61,0,.59),(.35,1.36,.405),black,.095),'Recessed intake')
for side in [-1,1]:
    cut(body,box('V02_Lamp_Cutter',(2.57,side*.831,.735),(.29,.181,.485),black,.045),'Recessed headlight')
cut(body,box('V02_Rear_Plate_Cutter',(-2.65,0,1.03),(.25,.80,.225),black,.05),'Rear plate recess')
bevel(body,.008,3)
bpy.context.view_layer.update()
surface=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())


def body_side(along,height,side,offset=.004):
    hit=surface.ray_cast(Vector((along,side*3,height)),Vector((0,-side,0)))[0]
    return (along,hit.y+side*offset if hit else side*.97,height)


def body_end(lateral,height,front=True,offset=.004):
    side=1 if front else -1
    hit=surface.ray_cast(Vector((side*4,lateral,height)),Vector((-side,0,0)))[0]
    return (hit.x+side*offset if hit else side*2.6,lateral,height)


cabin_stations=[(-2.46,1.27),(-2.42,1.32),(-2.30,1.51),(-2.14,1.73),(-2.00,1.798),
                (-1.8,1.824),(-1.4,1.838),(-.8,1.842),(-.2,1.838),(.19,1.811),
                (.38,1.75),(.62,1.60),(.87,1.41),(1.07,1.285)]
cabin_rings=[]
for along,height in cabin_stations:
    width=.952-.245*(height-1.27)
    section=[(0,1.253),(.91,1.253),(.952,1.275),(width,height-.034),
             (width-.022,height-.009),(width-.06,height+.007),(.5,height+.022),(0,height+.033)]
    section += [(-lateral,elevation) for lateral,elevation in reversed(section[1:-1])]
    cabin_rings.append([(along,lateral,elevation) for lateral,elevation in section])
cabin=loft('V02_Cabin_Roof',cabin_rings,silver,2)


def side_glass_point(along,height,side,offset=0):
    return (along,side*(.955-.245*(height-1.27)+offset),height)


outline=[(.995,1.306),(.80,1.444),(.45,1.681),(.19,1.753),(-.16,1.772),
         (-1.47,1.766),(-1.69,1.713),(-1.82,1.558),(-1.965,1.313)]
for side in [-1,1]:
    perimeter=rounded_outline(outline,.16,10)
    points=[side_glass_point(along,height,side,.008) for along,height in perimeter]
    mesh(f'V02_Window_Band_{side}',points,[tuple(range(len(points)))],glass)
    curve(f'V02_Window_Outer_Seal_{side}',points,black,.010,True)
    curve(f'V02_Window_Perimeter_Chrome_{side}',
          [side_glass_point(along,height,side,.019) for along,height in perimeter],chrome,.005,True)
    for name,lower,upper,width,height in [('B',-.045,.025,.067,1.768),('C',-1.045,-.979,.050,1.764)]:
        vertices=[side_glass_point(along,elevation,side,.02) for along,elevation in
                  [(lower-width/2,1.31),(lower+width/2,1.31),(upper+width/2,height),(upper-width/2,height)]]
        mesh(f'V02_{name}_Pillar_{side}',vertices,[(0,1,2,3)],black)
    belt=[body_side(along,1.258,side,.007) for along in [-2.3,-2.1,-1.9,-1.5,-1,-.5,0,.5,.95]]
    curve(f'V02_Belt_Chrome_{side}',belt,chrome,.005)
    for label,polyline in [('Front',[(.99,1.275),(.99,1.18),(.965,.94),(.94,.7),(.96,.37)]),
                           ('Middle',[(-.045,1.29),(-.05,1.15),(-.045,.95),(-.06,.72),(-.05,.36)]),
                           ('Rear',[(-1.20,1.28),(-1.23,1.15),(-1.25,1.06),(-1.1,.89),(-1.04,.64),(-1.07,.36)])]:
        points=[]
        for start,end in zip(polyline,polyline[1:]):
            for sample in range(12):
                fraction=sample/11
                along=start[0]*(1-fraction)+end[0]*fraction
                height=start[1]*(1-fraction)+end[1]*fraction
                points.append(body_side(along,height,side))
        curve(f'V02_Door_{label}_{side}',points,black,.0022)
    for along in [.16,-1.03]:
        location=body_side(along,1.154,side,.008)
        box(f'V02_Flush_Handle_{side}_{along}',location,(.205,.014,.043),black,.009)
        box(f'V02_Handle_Insert_{side}_{along}',(location[0],location[1]+side*.008,1.161),(.163,.008,.012),paint,.004)
    curve(f'V02_Sill_{side}',[body_side(along,.391,side,.008) for along in [-1.0,-.8,-.4,0,.4,.78,.92]],chrome,.009)
    outline_flap=rounded_outline([(-1.77,1.16),(-1.58,1.16),(-1.58,1.01),(-1.77,1.01)],.3)
    curve(f'V02_Fuel_Flap_{side}',[body_side(along,height,side) for along,height in outline_flap],black,.002,True)
    box(f'V02_Mirror_Stem_{side}',(.91,side*1.007,1.315),(.15,.19,.046),black,.02)
    box(f'V02_Mirror_Housing_{side}',(.86,side*1.103,1.369),(.22,.19,.132),silver,.053)
    box(f'V02_Mirror_Base_{side}',(.86,side*1.103,1.322),(.215,.19,.035),black,.015)
    box(f'V02_Mirror_Glass_{side}',(.746,side*1.10,1.373),(.011,.143,.079),glass,.02)

screen('V02_Windshield',1.065,.364,1.323,1.77,.864,.754,frontglass)
screen('V02_Rear_Window',-2.455,-2.145,1.363,1.755,.846,.740,glass)
for name in ['V02_Windshield_Seal','V02_Rear_Window_Seal']:
    bpy.data.objects[name].data.bevel_depth=.010
box('V02_Spoiler',(-2.15,0,1.796),(.20,1.67,.045),silver,.021)
box('V02_Spoiler_Shadow',(-2.153,0,1.768),(.13,1.54,.019),black,.009)
box('V02_Lidar',(.37,0,1.826),(.16,.18,.063),black,.025)
box('V02_Lidar_Lens',(.455,0,1.828),(.008,.114,.024),lens,.009)

for along,axle in [(1.66,'Front'),(-1.53,'Rear')]:
    for side in [-1,1]:
        lateral=side*.863
        prefix=f'V02_Wheel_{axle}_{side}'
        radial(prefix+'_Tire',along,lateral,[(-.14,.344),(-.14,.386),(-.118,.425),(-.085,.442),
               (.085,.442),(.118,.425),(.14,.386),(.14,.344)],rubber,112)
        radial(prefix+'_Rim',along,lateral,[(side*.139,.323),(side*.146,.354),
               (side*.151,.357),(side*.158,.347)],alloy,112)
        radial(prefix+'_Rotor',along,lateral,[(side*.10,0),(side*.10,.301),
               (side*.106,.301),(side*.106,0)],rotor)
        radial(prefix+'_Inner',along,lateral,[(side*.115,.078),(side*.116,.325),
               (side*.119,.325),(side*.119,.078)],black)
        radial(prefix+'_Hub',along,lateral,[(side*.164,0),(side*.164,.075),
               (side*.177,.075),(side*.177,0)],alloy,64)
        for spoke in range(10):
            angle=spoke*math.tau/10
            shape=[(.07,angle-.16),(.22,angle-.14),(.348,angle-.035),(.348,angle+.17),(.18,angle+.055)]
            points=[(along+radius*math.cos(theta),lateral+side*(.166 if radius<.1 else .157),
                     .455+radius*math.sin(theta)) for radius,theta in shape]
            obj=mesh(prefix+f'_Fan_{spoke}',points,[tuple(range(len(points)))],alloy)
            obj.modifiers.new('Spoke depth','SOLIDIFY').thickness=.013
            bevel(obj,.003,2)
            facet=[points[0],points[1],points[2],points[4]]
            mesh(prefix+f'_Facet_{spoke}',[(x,y+side*.002,z) for x,y,z in facet],[(0,1,2,3)],alloy_light)
        for radius in [.381,.411]:
            curve(prefix+'_Sidewall',[(along+radius*math.cos(sample*math.tau/112),lateral+side*.137,
                  .455+radius*math.sin(sample*math.tau/112)) for sample in range(112)],rubber,.003,True)
        arch=[]
        for sample in range(81):
            angle=-.27+sample*(math.pi+.54)/80
            arch.append(body_side(along+.516*math.cos(angle),.445+.516*math.sin(angle),side,.004))
        curve(prefix+'_Arch',arch,paint,.018)
        for obj in list(model.objects):
            if obj.name.startswith(prefix) and 'Arch' not in obj.name:
                obj.location.z=-.010

box('V02_Underbody',(0,0,.30),(4.72,1.68,.15),black,.065)
box('V02_Intake_Back',(2.449,0,.59),(.022,1.24,.30),black,.055)
for height in [.455,.515,.575,.635]:
    box('V02_Intake_Louver',(2.485,0,height),(.06,1.16,.022),black,.009)
for lateral in [-.535,0,.535]:
    box('V02_Intake_Vertical',(2.523,lateral,.553),(.085,.038,.25),paint,.012)
for side in [-1,1]:
    box(f'V02_Headlamp_Back_{side}',(2.467,side*.831,.735),(.055,.153,.432),black,.033)
    for height in [.765,.857]:
        box(f'V02_Headlamp_Lens_{side}_{height}',(2.505,side*.831,height),(.019,.106,.065),lens,.019)
    for height in [.711,.726]:
        box(f'V02_Headlamp_Strip_{side}_{height}',(2.519,side*.831,height),(.015,.11,.009),chrome,.004)

for front in [True,False]:
    points=[]
    for sample in range(121):
        lateral=-.934+sample*1.868/120
        height=(1.164+.022*(1-(lateral/.934)**2)) if front else 1.244
        points.append(body_end(lateral,height,front,.010))
    curve('V02_Front_Light_Housing' if front else 'V02_Rear_Light_Housing',points,black,.021)
    curve('V02_Front_Light_Strip' if front else 'V02_Rear_Light_Strip',
          [(x+(.012 if front else -.012),y,z+.004) for x,y,z in points],lens if front else red,.005)
    curve('V02_Front_Light_Lip' if front else 'V02_Rear_Light_Lip',
          [(x,y,z+.025) for x,y,z in points],silver if front else paint,.006)
    lower=[]
    for sample in range(91):
        lateral=-.885+sample*1.77/90
        lower.append(body_end(lateral,.36+.025*abs(lateral),front,.012))
    curve('V02_Front_Lower_Trim' if front else 'V02_Rear_Lower_Trim',lower,chrome,.012)
box('V02_Front_Plate',(2.632,0,.803),(.024,.445,.15),plate,.008)
box('V02_Rear_Plate_Back',(-2.541,0,1.03),(.02,.70,.18),black,.035)
box('V02_Rear_Plate',(-2.562,0,1.03),(.018,.445,.143),plate,.007)
tailgate=rounded_outline([(-.80,1.243),(.80,1.243),(.77,.813),(-.77,.813)],.13,12)
curve('V02_Tailgate_Seam',[body_end(lateral,height,False,.006) for lateral,height in tailgate],black,.0023,True)
for side in [-1,1]:
    points=[body_end(side*(.43+sample*.004),.419,False,.009) for sample in range(85)]
    curve(f'V02_Rear_Reflector_{side}',points,red,.012)
for front in [True,False]:
    for lateral in [-.022,.022]:
        obj=box('V02_Li_Emblem',((2.25 if front else -2.478),lateral,(1.238 if front else 1.298)),(.05,.025,.007),chrome,.003)

refs=bpy.data.collections.get('L9_Reference_Images')
if refs:
    scene.collection.children.link(refs)
floor=material('V02_Studio_Floor',(.45,.47,.48),.08,.40)
box('V02_Studio_Floor',(0,0,-.09),(2000,2000,.15),floor,0,stage)
world=bpy.data.worlds.new('V02_Studio_World')
world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.58,.62,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.40
scene.world=world
for name,location,energy,size in [('Key',(3,-5,7),1500,5),('Fill',(0,5,5),1100,5),('Rim',(-5,-2,6),1700,4)]:
    data=bpy.data.lights.new('V02_'+name,'AREA')
    data.energy=energy
    data.shape='DISK'
    data.size=size
    obj=bpy.data.objects.new(data.name,data)
    stage.objects.link(obj)
    obj.location=location
    obj.rotation_euler=(Vector((0,0,.9))-obj.location).to_track_quat('-Z','Y').to_euler()
for name,location,lens_value in [('Front45',(10,-12,3.35),64),('Rear45',(-10,-12,3.35),64),
                                 ('Side',(0,-16,2.95),67),('Front',(14,0,2.45),90),('Rear',(-14,0,2.45),90)]:
    data=bpy.data.cameras.new('V02_Camera_'+name)
    obj=bpy.data.objects.new(data.name,data)
    stage.objects.link(obj)
    obj.location=location
    obj.rotation_euler=(Vector((0,0,.91))-obj.location).to_track_quat('-Z','Y').to_euler()
    data.lens=lens_value
    data.clip_end=3000
scene.camera=bpy.data.objects['V02_Camera_Front45']
scene.render.engine='CYCLES'
scene.cycles.samples=32
scene.cycles.use_denoising=True
scene.render.resolution_x=1400
scene.render.resolution_y=1050
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene['accuracy']='V02: photo-matched proportions, not measured CAD. No interior, rigging or production UVs.'
scene['v01_sha256']=original_hash
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA'
        area.spaces.active.shading.color_type='MATERIAL'
        area.spaces.active.overlay.show_overlays=False
assert len([obj for obj in model.objects if obj.name.endswith('_Tire')])==4
assert hashlib.sha256(original.read_bytes()).hexdigest()==original_hash
assert bpy.data.scenes.get('L9_Exterior_v01')
assert len(refs.objects)==8
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT/'L9_exterior_v02.blend'))
print('L9_V02_CHECK_OK',len(model.objects),'objects; V01 unchanged')
