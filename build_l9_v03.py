from pathlib import Path
import ast
import math
import hashlib
import json
import bpy
import bmesh
from mathutils import Vector

ROOT = Path('D:/bowen/demo/blender-demo')
OUT = ROOT / 'output'
BLUEPRINT = ROOT / 'blueprint/lixiang_l9_2026_preview.jpg'
HASHES = {name: hashlib.sha256((OUT/name).read_bytes()).hexdigest()
          for name in ['L9_exterior_v01.blend', 'L9_exterior_v02.blend']}
rebuild=globals().get('REBUILD_V03',False)
existing=bpy.data.scenes.get('L9_Blueprint_v03')
if rebuild and existing:
    assert existing.name=='L9_Blueprint_v03'
    for obj in list(existing.objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    for collection in list(existing.collection.children):
        bpy.data.collections.remove(collection)
    bpy.data.scenes.remove(existing)
assert not bpy.data.scenes.get('L9_Blueprint_v03'), 'V03 already exists.'
assert rebuild or not (OUT/'L9_blueprint_v03.blend').exists(), 'Never replace an existing version.'
scene = bpy.data.scenes.new('L9_Blueprint_v03')
bpy.context.window.scene = scene
model = bpy.data.collections.new('AI_Model_L9_v03')
stage = bpy.data.collections.new('L9_Studio_v03')
scene.collection.children.link(model)
scene.collection.children.link(stage)
scene.unit_settings.system = 'METRIC'
source = ast.parse((ROOT/'build_l9.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[node for node in source.body if isinstance(node, ast.FunctionDef)],
                       type_ignores=[]), 'shared_blender_primitives', 'exec'))

LENGTH, WIDTH, HEIGHT, WHEELBASE = 5.218, 1.998, 1.800, 3.105
AXLES = (1.661, 1.661-WHEELBASE)
WHEEL_Z, WHEEL_RADIUS = .414, .414
paint = material('V03_Pearl_Silver', (.40,.43,.46), .48,.29)
black = material('V03_Black_Trim', (.008,.010,.012), .08,.35)
glass = material('V03_Privacy_Glass', (.014,.027,.033), .10,.23)
windshield = material('V03_Windshield', (.035,.064,.074), .08,.24)
rubber = material('V03_Rubber', (.012,.014,.017), 0,.65)
chrome = material('V03_Machined_Alloy', (.46,.49,.52), .8,.24)
alloy = material('V03_Alloy_Shadow', (.055,.063,.07), .6,.31)
brake = material('V03_Brake', (.16,.18,.19), .65,.48)
red = material('V03_Taillight', (.40,.008,.012), .25,.22)
led = material('V03_DRL', (.68,.82,.94), .30,.20)
lamp = material('V03_Headlight_Lens', (.07,.11,.15), .3,.18)
plate_mat = material('V03_Numberplate', (.10,.13,.16), .25,.36)
for value in [glass,windshield]:
    value.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.25


def interp(value, knots):
    if value <= knots[0][0]:
        return knots[0][1]
    slopes=[(b[1]-a[1])/(b[0]-a[0]) for a,b in zip(knots,knots[1:])]
    tangents=[slopes[0]]
    for a,b in zip(slopes,slopes[1:]):
        tangents.append(2*a*b/(a+b) if a*b>0 else 0)
    tangents.append(slopes[-1])
    for index,((left, first), (right, second)) in enumerate(zip(knots,knots[1:])):
        if value <= right:
            t=(value-left)/(right-left)
            return ((2*t**3-3*t*t+1)*first+(t**3-2*t*t+t)*(right-left)*tangents[index]
                    +(-2*t**3+3*t*t)*second+(t**3-t*t)*(right-left)*tangents[index+1])
    return knots[-1][1]


def shoulder(along):
    return interp(along,[(-2.609,1.163),(-2.3,1.185),(-1.3,1.196),(.8,1.196),
                         (1.04,1.177),(1.4,1.142),(2.05,1.096),(2.609,1.025)])


def lower(along):
    bottom=interp(along,[(-2.609,.36),(-2.2,.305),(1.9,.305),(2.609,.29)])
    for axle in AXLES:
        delta=along-axle
        if abs(delta)<.478:
            bottom=max(bottom,WHEEL_Z+math.sqrt(.478**2-delta**2))
    return bottom


def side_width(along,height):
    width=interp(height,[(.25,.920),(.32,.950),(.48,.965),(.64,.960),(.83,.978),
                         (1.00,.985),(1.13,.978),(1.23,.955)])
    arch=max(math.exp(-((along-axle)/.53)**4) for axle in AXLES)
    width+=.018*arch*math.exp(-((height-.83)/.28)**2)
    return min(.999,width)


def end_x(lateral,height,front=True):
    across=min(1,abs(lateral)/.985)
    if front:
        center=interp(height,[(.24,2.52),(.32,2.595),(.45,2.609),(.73,2.585),(.93,2.565),(1.1,2.516)])
        return center-.095*across**5
    center=interp(height,[(.28,-2.51),(.38,-2.578),(.56,-2.609),(.77,-2.574),(.86,-2.54),(1.02,-2.573),(1.2,-2.574)])
    return center+.090*across**5


def surface_side(along,height,side,offset=0):
    width=side_width(along,height)
    if along>2.30:
        amount=(along-2.30)/.309
        along=2.30+(end_x(width,height)-2.30)*amount
    if along<-2.30:
        amount=(-along-2.30)/.309
        along=-2.30+(end_x(width,height,False)+2.30)*amount
    return (along,side*(width+offset),height)


def grid(name, rows, columns, mapping, mat, omit=None):
    vertices=[mapping(row/rows,column/columns) for row in range(rows+1) for column in range(columns+1)]
    faces=[]
    for row in range(rows):
        for column in range(columns):
            if omit and omit((row+.5)/rows,(column+.5)/columns):
                continue
            base=row*(columns+1)+column
            faces.append((base,base+1,base+columns+2,base+columns+1))
    return smooth(mesh(name,vertices,faces,mat))


for side in [-1,1]:
    grid(f'V03_Body_Side_{side}',240,26,
         lambda along,up: surface_side(-2.609+along*LENGTH,
             lower(-2.609+along*LENGTH)+(shoulder(-2.609+along*LENGTH)-lower(-2.609+along*LENGTH))*up,side),paint)


def hood_point(amount,across):
    along=1.04+amount*1.569
    lateral=(across*2-1)*side_width(along,shoulder(along))
    height=shoulder(along)+.036*(1-(2*across-1)**2)
    if along>2.3:
        along=2.3+(end_x(lateral,height)-2.3)*(along-2.3)/.309
    return (along,lateral,height)


grid('V03_Hood',55,44,hood_point,paint)
grid('V03_Rear_Deck',16,40,
     lambda along,across:(-2.50-along*.076,(across*2-1)*.964,1.175+.02*(1-(across*2-1)**2)),paint)
for front in [True,False]:
    def fascia_point(up,across):
        height=.295+up*((1.06 if front else 1.177)-.295)
        width=side_width(2.609 if front else -2.609,height)
        lateral=(across*2-1)*width
        return(end_x(lateral,height,front),lateral,height)
    grid('V03_Front_Fascia' if front else 'V03_Rear_Fascia',64,100,fascia_point,paint)


def patch(name, outline, mapping, mat, rounding=.10, rings=12):
    border=rounded_outline(outline,rounding,8)
    center=sum((Vector(point) for point in border),Vector((0,0)))/len(border)
    vertices=[mapping(*center)]
    for ring in range(1,rings+1):
        vertices.extend(mapping(*center.lerp(Vector(point),ring/rings)) for point in border)
    count=len(border)
    faces=[(0,1+index,1+(index+1)%count) for index in range(count)]
    for ring in range(rings-1):
        first=1+ring*count
        second=first+count
        faces.extend((first+index,first+(index+1)%count,second+(index+1)%count,second+index) for index in range(count))
    return smooth(mesh(name,vertices,faces,mat)),[mapping(*point) for point in border]


roof_knots=[(-2.50,1.20),(-2.34,1.45),(-2.13,1.67),(-1.98,1.75),(-1.72,1.777),
            (-.8,1.784),(.15,1.76),(.42,1.70),(.64,1.54),(.88,1.34),(1.08,1.19)]


def roof_z(along):
    return interp(along,roof_knots)


def cabin_y(height):
    return .957-.27*max(0,height-1.19)


for side in [-1,1]:
    grid(f'V03_Cabin_Side_{side}',144,24,
         lambda along,up:(-2.50+along*3.58,
            side*cabin_y(1.18+up*(roof_z(-2.50+along*3.58)-1.18)),
            1.18+up*(roof_z(-2.50+along*3.58)-1.18)),paint)
grid('V03_Roof_and_Screens',160,48,
     lambda along,across:(-2.50+along*3.58,(2*across-1)*cabin_y(roof_z(-2.50+along*3.58)),
                         roof_z(-2.50+along*3.58)+.014*(1-(2*across-1)**2)),paint)

window_outline=[(1.00,1.224),(.80,1.373),(.45,1.615),(.26,1.68),(-.19,1.713),
                (-1.36,1.708),(-1.60,1.667),(-1.84,1.485),(-1.94,1.294),(-1.82,1.245)]
for side in [-1,1]:
    window,border=patch(f'V03_Glass_Band_{side}',window_outline,
                       lambda along,height:(along,side*(cabin_y(height)+.010),height),glass,.15)
    curve(f'V03_Window_Seal_{side}',border,black,.008,True)
    curve(f'V03_Window_Chrome_{side}',[(x,y+side*.003,z) for x,y,z in border],chrome,.0035,True)
    for name,bottom,top,thickness in [('B',-.024,-.108,.098),('C',-1.168,-1.045,.098)]:
        shape=[(bottom-thickness/2,1.23),(bottom+thickness/2,1.23),(top+thickness/2,1.71),(top-thickness/2,1.71)]
        patch(f'V03_Pillar_{name}_{side}',shape,lambda along,height:(along,side*(cabin_y(height)+.021),height),black,.015,2)
    for label,shape in [('Front',[(1.04,1.184),(1.017,1.02),(1.009,.75),(1.008,.322)]),
                        ('Middle',[(-.014,1.19),(-.028,1.00),(-.045,.7),(-.052,.319)]),
                        ('Rear',[(-1.184,1.19),(-1.187,1.06),(-1.19,.988),(-1.04,.835),(-.954,.61),(-.963,.319)])]:
        points=[]
        for first,last in zip(shape,shape[1:]):
            for index in range(14):
                amount=index/13
                along=first[0]+amount*(last[0]-first[0])
                height=first[1]+amount*(last[1]-first[1])
                points.append(surface_side(along,height,side,.0025))
        curve(f'V03_Door_Seam_{label}_{side}',points,black,.0019)
    for along in [.16,-.994]:
        location=surface_side(along,1.078,side,.004)
        box(f'V03_Handle_Recess_{side}_{along}',location,(.213,.015,.034),black,.009)
        box(f'V03_Flush_Handle_{side}_{along}',(location[0],location[1]+side*.008,location[2]+.003),(.186,.012,.020),paint,.007)
    shape=[(.88,.455),(.79,.605),(-.85,.605),(-.94,.45)]
    patch(f'V03_Door_Lower_Scallop_{side}',shape,lambda along,height:surface_side(along,height,side,.003),paint,.23)
    curve(f'V03_Sill_Bright_{side}',[surface_side(along,.327,side,.006) for along in [-.95,-.7,-.3,0,.4,.8,.98]],chrome,.005)
    flap=rounded_outline([(-1.655,1.106),(-1.433,1.106),(-1.433,.95),(-1.655,.95)],.28)
    curve(f'V03_Fuel_Flap_{side}',[surface_side(along,height,side,.003) for along,height in flap],black,.002,True)
    box(f'V03_Mirror_Stem_{side}',(.866,side*1.003,1.234),(.14,.15,.045),black,.018)
    box(f'V03_Mirror_{side}',(.827,side*1.093,1.286),(.22,.22,.132),paint,.047)
    box(f'V03_Mirror_Glass_{side}',(.710,side*1.10,1.288),(.01,.16,.085),glass,.02)
    indicator=[surface_side(along,1.033,side,.008) for along in [1.13,1.19,1.27]]
    curve(f'V03_Fender_Sensor_{side}',indicator,black,.022)


def top_mapping(along,lateral,offset=.009):
    return(along,lateral,roof_z(along)+.014*(1-(lateral/cabin_y(roof_z(along)))**2)+offset)


for name,outline,mat in [
    ('Windscreen',[(.975,-.82),(.975,.82),(.374,.766),(.337,.55),(.337,-.55),(.374,-.766)],windshield),
    ('Rear_Window',[(-2.455,-.82),(-2.455,.82),(-2.037,.727),(-2.037,-.727)],glass),
    ('Panoramic_Front',[(.17,-.63),(.17,.63),(-.63,.63),(-.63,-.63)],glass),
    ('Panoramic_Rear',[(-.78,-.63),(-.78,.63),(-1.73,.60),(-1.73,-.60)],glass)]:
    border2d=rounded_outline(outline,.15,16)
    first=min(p[0] for p in border2d)+.00001
    last=max(p[0] for p in border2d)-.00001
    def screen_point(u,v):
        along=first+(last-first)*u
        crosses=[]
        for a,b in zip(border2d,border2d[1:]+border2d[:1]):
            if min(a[0],b[0])<=along<=max(a[0],b[0]) and abs(b[0]-a[0])>1e-10:
                crosses.append(a[1]+(b[1]-a[1])*(along-a[0])/(b[0]-a[0]))
        return top_mapping(along,min(crosses)+(max(crosses)-min(crosses))*v,.013)
    grid('V03_'+name,120,48,screen_point,mat)
    border=[top_mapping(*p,.013) for p in border2d]
    curve('V03_'+name+'_Seal',border,black,.005,True)

box('V03_Spoiler',(-2.066,0,1.744),(.25,1.66,.045),paint,.021)
box('V03_Spoiler_Underside',(-2.115,0,1.711),(.16,1.57,.021),black,.01)
box('V03_Lidar',(.455,0,1.755),(.19,.19,.060),black,.024)
for side in [-1,1]:
    curve('V03_Roof_Rail',[(along,side*.733,roof_z(along)+.012) for along in [-1.80,-1.6,-1.2,-.8,-.4,0,.18]],chrome,.008)


for along,axle in [(AXLES[0],'Front'),(AXLES[1],'Rear')]:
    for side in [-1,1]:
        prefix=f'V03_Wheel_{axle}_{side}'
        lateral=side*.846
        radial(prefix+'_Tire',along,lateral,[(-.136,.295),(-.136,.348),(-.113,.395),(-.073,.414),
               (.073,.414),(.113,.395),(.136,.348),(.136,.295)],rubber,112)
        radial(prefix+'_Rim',along,lateral,[(side*.130,.278),(side*.143,.315),(side*.149,.317),(side*.151,.3)],chrome,96)
        radial(prefix+'_Disc',along,lateral,[(side*.09,0),(side*.09,.269),(side*.10,.269),(side*.10,0)],brake)
        radial(prefix+'_Hub',along,lateral,[(side*.15,0),(side*.15,.073),(side*.174,.073),(side*.174,0)],chrome,64)
        for spoke in range(5):
            for branch in [-1,1]:
                angle=spoke*math.tau/5
                shape=[(.071,angle+branch*.13),(.18,angle+branch*.13),(.302,angle+branch*.19),
                       (.302,angle+branch*.31),(.15,angle+branch*.31),(.071,angle+branch*.24)]
                vertices=[(along+radius*math.cos(theta),lateral+side*.154,.455+radius*math.sin(theta)) for radius,theta in shape]
                obj=mesh(prefix+f'_SplitSpoke_{spoke}_{branch}',vertices,[tuple(range(len(vertices)))],chrome)
                obj.modifiers.new('Spoke depth','SOLIDIFY').thickness=.018
                bevel(obj,.004,2)
        for bolt in range(5):
            angle=bolt*math.tau/5
            box(prefix+'_Bolt',(along+.048*math.cos(angle),lateral+side*.178,.455+.048*math.sin(angle)),(.016,.007,.016),alloy,.006)
        for radius in [.341,.385]:
            curve(prefix+'_Sidewall',[(along+radius*math.cos(sample*math.tau/96),lateral+side*.132,
                  .455+radius*math.sin(sample*math.tau/96)) for sample in range(96)],rubber,.003,True)
        for obj in list(model.objects):
            if obj.name.startswith(prefix):
                obj.location.z+=WHEEL_Z-.455
        ringpoints=[]
        for index in range(91):
            angle=-.22+index*(math.pi+.44)/90
            position=along+.482*math.cos(angle)
            height=WHEEL_Z+.482*math.sin(angle)
            ringpoints.append(surface_side(position,height,side,.004))
        curve(prefix+'_Arch_Lip',ringpoints,paint,.012)
        curve(prefix+'_Wheelwell',[(x,y-side*.020,z-.012) for x,y,z in ringpoints],black,.013)


def end_mapping(front,offset=.009):
    sign=1 if front else -1
    return lambda lateral,height:(end_x(lateral,height,front)+sign*offset,lateral,height)


for front in [True,False]:
    mapping=end_mapping(front)
    if front:
        shape=[(-.87,.401),(.87,.401),(.82,.566),(.71,.605),(-.71,.605),(-.82,.566)]
        patch('V03_Low_Intake',shape,mapping,black,.14)
        for height in [.426,.465,.505,.544]:
            curve('V03_Grille_Louver',[end_mapping(True,.018)(lateral,height) for lateral in [-.75,-.5,0,.5,.75]],alloy,.009)
        for side in [-1,1]:
            shape=[(side*.756,.596),(side*.922,.596),(side*.916,.847),(side*.754,.867)]
            patch(f'V03_Split_Headlight_{side}',shape,end_mapping(True,.010),black,.15)
            for height in [.647,.745,.815]:
                shape=[(side*.779,height-.028),(side*.893,height-.028),(side*.893,height+.028),(side*.779,height+.028)]
                patch(f'V03_Headlamp_Lens_{side}_{height}',shape,end_mapping(True,.015),lamp,.25,4)
                curve('V03_Lens_Bright',[end_mapping(True,.020)(side*.797,height+.01),end_mapping(True,.020)(side*.875,height+.01)],chrome,.006)
        shape=[(-.46,.650),(.46,.650),(.26,.823),(-.26,.823)]
        obj,border=patch('V03_Front_Center_Panel',shape,end_mapping(True,.004),paint,.20)
        curve('V03_Front_Center_Outline',border,alloy,.0017,True)
        points=[end_mapping(True,.012)(-.943+index*1.886/120,1.009+.024*(1-(-1+index/60)**2)) for index in range(121)]
        curve('V03_DRL_Housing',points,black,.018)
        curve('V03_DRL_Strip',[(x+.020,y,z+.005) for x,y,z in points],led,.005)
    else:
        points=[end_mapping(False,.037)(-.93+index*1.86/120,1.147+.006*(1-(-1+index/60)**2)) for index in range(121)]
        curve('V03_Tail_Housing',points,black,.030)
        curve('V03_Tail_Light',[(x-.029,y,z+.009) for x,y,z in points],red,.014)
        curve('V03_Tail_Light_Lower',[(x-.030,y,z-.010) for x,y,z in points],red,.006)
        for side in [-1,1]:
            wrap=[surface_side(-2.60+i*.35/40,1.151,side,.006) for i in range(41)]
            curve('V03_Tail_Wrap_Housing',wrap,black,.020)
            curve('V03_Tail_Wrap',[(x,y+side*.014,z+.005) for x,y,z in wrap],red,.011)
        outline=[(-.44,.78),(.44,.78),(.43,1.043),(-.43,1.043)]
        patch('V03_Rear_Plate_Recess',outline,end_mapping(False,.009),black,.1)
        patch('V03_Rear_Plate',[(-.25,.825),(.25,.825),(.25,.963),(-.25,.963)],end_mapping(False,.015),plate_mat,.04)
        perimeter=rounded_outline([(-.835,1.151),(.835,1.151),(.831,.726),(.735,.679),(-.735,.679),(-.831,.726)],.08)
        curve('V03_Tailgate_Seam',[end_mapping(False,.006)(*point) for point in perimeter],black,.002,True)
        patch('V03_Rear_Diffuser',[(-.86,.33),(.86,.33),(.81,.452),(.65,.5),(-.65,.5),(-.81,.452)],end_mapping(False,.009),black,.17)
        for side in [-1,1]:
            curve('V03_Rear_Reflector',[end_mapping(False,.012)(side*lateral,.556+.028*(lateral-.6)) for lateral in [.63,.70,.78,.85]],red,.014)
    curve('V03_Bumper_Lower_Bright', [end_mapping(front,.012)(lateral,.352) for lateral in [-.86,-.7,-.4,0,.4,.7,.86]],chrome,.008)

box('V03_Chassis',(0,0,.264),(4.7,1.66,.12),black,.05)
for side in [-1,1]:
    points=[]
    for index in range(51):
        along=1.08+index*1.36/50
        height=shoulder(along)+.036*(1-(.78/side_width(along,shoulder(along)))**2)+.003
        points.append((along,side*.78,height))
    curve('V03_Hood_Seam',points,black,.0018)

refs=bpy.data.collections.new('V03_Blueprint_Reference')
scene.collection.children.link(refs)
image=bpy.data.images.load(str(BLUEPRINT),check_existing=True)
image.pack()
reference=bpy.data.objects.new('V03_Blueprint_2024_Label',None)
reference.empty_display_type='IMAGE'
reference.data=image
reference.empty_display_size=8.1
reference.location=(0,3,1.7)
reference.rotation_euler=(math.pi/2,0,0)
refs.objects.link(reference)
refs.hide_render=True
refs.hide_viewport=True

floor=material('V03_Studio_Floor',(.31,.34,.38),.03,.6)
box('V03_Floor',(0,0,-.065),(200,200,.12),floor,0,stage)
world=bpy.data.worlds.new('V03_Studio_World')
world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.4,.45,.52,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.45
scene.world=world
for name,location,power,size in [('Key',(3,-4,7),1800,5),('Fill',(1,5,5),1400,5),('Rim',(-4,-1,6),1600,4)]:
    data=bpy.data.lights.new('V03_'+name,'AREA')
    data.energy=power
    data.shape='DISK'
    data.size=size
    obj=bpy.data.objects.new('V03_'+name,data)
    stage.objects.link(obj)
    obj.location=location
    obj.rotation_euler=(Vector((0,0,.8))-obj.location).to_track_quat('-Z','Y').to_euler()
for name,location,target,scale in [('Front45',(9,-11,4),(0,0,.85),6.7),('Rear45',(-9,-11,4),(0,0,.85),6.7),
                                    ('Side',(0,12,.90),(0,0,.90),6.1),('Front',(12,0,.9),(0,0,.9),3.2),
                                    ('Rear',(-12,0,.9),(0,0,.9),3.2),('Top',(0,0,12),(0,0,0),6.1)]:
    data=bpy.data.cameras.new('V03_Camera_'+name)
    obj=bpy.data.objects.new('V03_Camera_'+name,data)
    stage.objects.link(obj)
    obj.location=location
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO'
    data.ortho_scale=scale
    data.clip_end=500
    if name=='Top':
        obj.rotation_euler=(0,0,0)
scene.camera=bpy.data.objects['V03_Camera_Front45']
scene.render.engine='CYCLES'
scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.render.resolution_x=1400
scene.render.resolution_y=1050
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene['blueprint_note']='Filename 2026; drawing label Lixiang L9 (2024). Geometry follows drawing, not earlier photo set.'
scene['target_dimensions_m']=[LENGTH,WIDTH,HEIGHT,WHEELBASE]
scene['previous_file_hashes']=json.dumps(HASHES)
scene['accuracy']='Main dimensions and axle locations constrained; detailed curves traced approximately from raster preview. Not CAD.'
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA'
        area.spaces.active.shading.color_type='MATERIAL'
        area.spaces.active.overlay.show_overlays=False
assert abs(AXLES[0]-AXLES[1]-WHEELBASE)<1e-9
assert len([obj for obj in model.objects if obj.name.endswith('_Tire')])==4
assert image.packed_file
for name,digest in HASHES.items():
    assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==digest
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'L9_blueprint_v03.blend'))
print('V03_BUILD_CHECK_OK',len(model.objects),'objects; V01/V02 unchanged')
