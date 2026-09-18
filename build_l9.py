from pathlib import Path
import math
import bpy
import bmesh
from mathutils import Vector

ROOT = Path('D:/bowen/demo/blender-demo')
OUTPUT = ROOT / 'output'
OUTPUT.mkdir(exist_ok=True)
assert not bpy.data.scenes.get('L9_Exterior_v01'), 'Scene already exists; edit it instead of rebuilding.'
scene = bpy.data.scenes.new('L9_Exterior_v01')
bpy.context.window.scene = scene
model = bpy.data.collections.new('AI_Model_L9')
stage = bpy.data.collections.new('L9_Studio')
scene.collection.children.link(model)
scene.collection.children.link(stage)
scene.unit_settings.system = 'METRIC'
scene['accuracy'] = 'Photo-proportioned concept exterior; dimensions estimated, not engineering measurements.'


def material(name, color, metallic=0.0, roughness=0.35):
    value = bpy.data.materials.new('L9_' + name)
    value.diffuse_color = (*color, 1)
    value.use_nodes = True
    shader = value.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = roughness
    return value


paint = material('Graphite_Paint', (.135, .145, .14), .65, .27)
silver = material('Champagne_Roof', (.48, .47, .43), .7, .24)
glass = material('Privacy_Glass', (.015, .026, .031), .35, .16)
front_glass = material('Windshield', (.035, .046, .083), .38, .18)
black = material('Black_Trim', (.012, .015, .016), .25, .3)
rubber = material('Tire_Rubber', (.016, .018, .020), .0, .68)
chrome = material('Bright_Trim', (.55, .59, .62), .85, .2)
alloy = material('Wheel_Alloy', (.25, .28, .29), .8, .27)
rotor = material('Brake_Disc', (.18, .19, .20), .7, .5)
white = material('LED_White', (.80, .91, 1.0), .1, .23)
red = material('Tail_Red', (.3, .01, .012), .35, .23)
for value, color in [(white, (.65, .85, 1, 1)), (red, (.65, .012, .01, 1))]:
    shader = value.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Emission Color'].default_value = color
    shader.inputs['Emission Strength'].default_value = .65


def mesh(name, vertices, faces, mat, collection=model):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def smooth(obj):
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def bevel(obj, width=.025, segments=3):
    modifier = obj.modifiers.new('Edge radii', 'BEVEL')
    modifier.width = width
    modifier.segments = segments
    obj.modifiers.new('Surface normals', 'WEIGHTED_NORMAL')
    return obj


def box(name, location, size, mat, radius=.02, collection=model):
    vertices = [(sx * size[0] / 2, sy * size[1] / 2, sz * size[2] / 2)
                for sx, sy, sz in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),
                                  (1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    obj = mesh(name, vertices, [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)], mat, collection)
    obj.location = location
    if radius:
        bevel(obj, radius)
    return obj


def curve(name, points, mat, thickness=.008, cyclic=False):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 2
    data.bevel_depth = thickness
    data.bevel_resolution = 3
    spline = data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for point, position in zip(spline.points, points):
        point.co = (*position, 1)
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, data)
    model.objects.link(obj)
    data.materials.append(mat)
    return obj


def loft(name, rings, mat, subdiv=0, caps=True):
    count = len(rings[0])
    vertices = [position for ring in rings for position in ring]
    faces = [(index * count + point, index * count + (point+1)%count,
              (index+1)*count + (point+1)%count, (index+1)*count+point)
             for index in range(len(rings)-1) for point in range(count)]
    if caps:
        faces.extend([tuple(reversed(range(count))), tuple(range(len(vertices)-count, len(vertices)))])
    obj = smooth(mesh(name, vertices, faces, mat))
    if subdiv:
        modifier = obj.modifiers.new('Surface refinement', 'SUBSURF')
        modifier.levels = subdiv
    return obj


profile = [(0,.29),(.75,.29),(.93,.32),(.985,.43),(.995,.65),(.978,.81),
           (1.01,1.00),(1.005,1.14),(.969,1.23),(.86,1.275),(.55,1.294),(0,1.303)]
profile += [(-width,height) for width,height in reversed(profile[1:-1])]
stations = [(-2.63,.86,-.06),(-2.60,.94,-.015),(-2.48,1,0),(-2.1,1,0),
            (-1.63,1,0),(-.8,.988,0),(.2,.988,0),(1.1,1,0),(1.63,1,0),
            (2.23,1,-.015),(2.48,.985,-.04),(2.60,.93,-.08),(2.63,.86,-.10)]
body = loft('L9_Body_Shell', [[(along,width*scale,height+offset) for width,height in profile]
                            for along,scale,offset in stations], paint, 2)
bpy.context.view_layer.objects.active = body
bpy.ops.object.modifier_apply(modifier='Surface refinement')
for along in [-1.63, 1.63]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=.515, depth=2.7,
                                      location=(along,0,.455), rotation=(math.pi/2,0,0))
    cutter = bpy.context.object
    modifier = body.modifiers.new('Wheel opening', 'BOOLEAN')
    modifier.operation = 'DIFFERENCE'
    modifier.object = cutter
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
bevel(body,.009,2)

cabin_stations = [(-2.46,1.285),(-2.42,1.34),(-2.18,1.68),(-1.98,1.79),
                  (-1.88,1.815),(-1.55,1.827),(-.7,1.83),(.22,1.825),
                  (.43,1.79),(.61,1.69),(1.05,1.38),(1.19,1.29)]
cabin_rings = []
for along, height in cabin_stations:
    roof_width = .95 - .28*(height-1.28)
    section = [(0,1.265),(.90,1.265),(.951,1.29),(roof_width,height-.025),
               (roof_width-.045,height),(.5,height+.018),(0,height+.025)]
    section += [(-width,elevation) for width,elevation in reversed(section[1:-1])]
    cabin_rings.append([(along,width,elevation) for width,elevation in section])
loft('L9_Cabin_Champagne',cabin_rings,silver,2)


def rounded_outline(points, fraction=.10, steps=6):
    result = []
    for index, center in enumerate(points):
        center = Vector(center)
        incoming = center.lerp(Vector(points[index-1]),fraction)
        outgoing = center.lerp(Vector(points[(index+1)%len(points)]),fraction)
        for sample in range(steps+1):
            amount = sample/steps
            result.append(tuple((1-amount)**2*incoming+2*(1-amount)*amount*center+amount**2*outgoing))
    return result


window_shapes = [([(1.05,1.333),(.43,1.757),(-.20,1.765),(-.20,1.333)],'Front'),
                 ([(-.255,1.333),(-.255,1.765),(-1.13,1.765),(-1.20,1.333)],'Rear'),
                 ([(-1.255,1.333),(-1.18,1.765),(-1.85,1.748),(-2.16,1.333)],'Quarter')]
for side in [-1,1]:
    for outline,name in window_shapes:
        points = [(along,side*(.95-.28*(height-1.28)+.012),height)
                  for along,height in rounded_outline(outline)]
        mesh(f'L9_{side}_{name}_Glass',points,[tuple(range(len(points)))],glass)
        curve(f'L9_{side}_{name}_Seal',points,black,.009,True)
    perimeter = [(1.075,1.322),(.47,1.774),(-1.88,1.78),(-2.20,1.322)]
    points = [(along,side*(.95-.28*(height-1.28)+.015),height)
              for along,height in rounded_outline(perimeter,.16,10)]
    curve(f'L9_{side}_Window_Chrome',points,chrome,.012,True)


def screen(name, bottom_x, top_x, bottom_z, top_z, bottom_width, top_width, mat):
    vertices, faces = [], []
    for row in range(13):
        amount = row/12
        for column in range(25):
            across = column/12-1
            width = bottom_width*(1-amount)+top_width*amount
            along = bottom_x*(1-amount)+top_x*amount
            along += (.035 if bottom_x>0 else -.035)*(1-across**2)*math.sin(math.pi*amount)
            height = bottom_z*(1-amount)+top_z*amount+.018*(1-across**2)
            vertices.append((along,across*width,height))
    for row in range(12):
        for column in range(24):
            base = row*25+column
            faces.append((base,base+1,base+26,base+25))
    obj = smooth(mesh(name,vertices,faces,mat))
    border = vertices[:25] + [vertices[row*25+24] for row in range(1,13)]
    border += list(reversed(vertices[-25:-1])) + [vertices[row*25] for row in range(11,0,-1)]
    curve(name+'_Seal',border,black,.018,True)
    return obj

screen('L9_Windshield',1.145,.475,1.335,1.779,.875,.755,front_glass)
screen('L9_Rear_Window',-2.495,-2.165,1.35,1.755,.88,.75,glass)
box('L9_Panoramic_Roof',(-.68,0,1.806),(2.20,1.32,.018),glass,.008)
box('L9_Rear_Spoiler',(-2.09,0,1.785),(.24,1.68,.05),silver,.023)
box('L9_Roof_Sensor',(.43,0,1.845),(.21,.22,.085),black,.035)
box('L9_Chassis',(0,0,.32),(4.9,1.66,.15),black,.08)


def radial(name, along, lateral, profile, mat, segments=80):
    rings = [[(along+radius*math.cos(2*math.pi*sample/segments), lateral+depth,
               .455+radius*math.sin(2*math.pi*sample/segments)) for sample in range(segments)]
             for depth,radius in profile]
    return loft(name,rings + [rings[0]],mat,caps=False)


for along, axle in [(1.63,'Front'),(-1.63,'Rear')]:
    for side in [-1,1]:
        lateral = side*.946
        prefix = f'L9_Wheel_{axle}_{side}'
        radial(prefix+'_Tire',along,lateral,[(-.15,.325),(-.15,.39),(-.125,.44),(-.08,.455),
               (.08,.455),(.125,.44),(.15,.39),(.15,.325)],rubber)
        radial(prefix+'_Rim',along,lateral,[(side*.135,.30),(side*.153,.332),
               (side*.165,.335),(side*.173,.32)],chrome)
        radial(prefix+'_Disc',along,lateral,[(side*.096,0),(side*.096,.285),
               (side*.105,.285),(side*.105,0)],rotor)
        radial(prefix+'_Hub',along,lateral,[(side*.18,0),(side*.18,.079),
               (side*.193,.079),(side*.193,0)],alloy,48)
        for spoke in range(10):
            angle = spoke*math.tau/10
            outline = [(.067,angle-.12),(.29,angle-.16),(.324,angle-.02),
                       (.285,angle+.10),(.09,angle+.10)]
            facepoints = [(along+radius*math.cos(theta),lateral+side*.182,
                           .455+radius*math.sin(theta)) for radius,theta in outline]
            obj = mesh(prefix+f'_Spoke_{spoke}',facepoints,[tuple(range(5))],alloy)
            solid = obj.modifiers.new('Spoke thickness','SOLIDIFY')
            solid.thickness=.025
            bevel(obj,.007,2)
        for radius in [.365,.422]:
            points=[(along+radius*math.cos(angle*math.tau/96),lateral+side*.143,
                     .455+radius*math.sin(angle*math.tau/96)) for angle in range(96)]
            curve(prefix+'_Sidewall',points,rubber,.004,True)
        vertices,faces=[],[]
        for sample in range(64):
            angle=sample*math.tau/64
            for offset,depth in [(-.008,-.075),(.008,-.075),(.045,.075),(.029,.075)]:
                vertices.append((along+.456*math.cos(angle+offset),lateral+depth,
                                 .455+.456*math.sin(angle+offset)))
            faces.append(tuple(range(sample*4,sample*4+4)))
        mesh(prefix+'_Tread',vertices,faces,black)
        archpoints=[(along+.527*math.cos(-.35+sample*(math.pi+.70)/64),side*1.003,
                     .455+.527*math.sin(-.35+sample*(math.pi+.70)/64)) for sample in range(65)]
        curve(prefix+'_Arch_Trim',archpoints,paint,.026)
        curve(prefix+'_Arch_Inner',[(x,y*1.001,z-.016) for x,y,z in archpoints],black,.012)

for side in [-1,1]:
    for along in [-.18,-1.22]:
        curve(f'L9_Door_Seam_{side}_{along}',[(along,side*.967,1.28),(along,side*1.004,1.11),
              (along-.015,side*.979,.82),(along-.025,side*.982,.5),(along-.025,side*.95,.325)],black,.0035)
    curve(f'L9_Front_Door_Seam_{side}',[(1.105,side*.968,1.29),(1.08,side*1.00,1.13),
          (1.08,side*.983,.84),(1.075,side*.975,.36)],black,.0035)
    for along in [-.87,.13]:
        box(f'L9_Handle_{side}_{along}',(along,side*1.003,1.145),(.205,.025,.047),black,.014)
    box(f'L9_Sill_Chrome_{side}',(-.09,side*.988,.43),(1.96,.025,.028),chrome,.012)
    box(f'L9_Mirror_Stem_{side}',(.92,side*1.015,1.315),(.18,.22,.055),black,.025)
    box(f'L9_Mirror_Housing_{side}',(.94,side*1.135,1.385),(.25,.21,.15),silver,.055)
    box(f'L9_Mirror_Glass_{side}',(.808,side*1.145,1.385),(.012,.16,.10),glass,.028)
    outline=rounded_outline([(-1.78,1.16),(-1.57,1.16),(-1.57,1.01),(-1.78,1.01)],.24)
    curve(f'L9_Charge_Flap_{side}',[(x,side*1.012,z) for x,z in outline],black,.003)

for rear in [False,True]:
    sign=-1 if rear else 1
    points=[]
    for sample in range(65):
        lateral=-.947+sample*1.894/64
        points.append((sign*(2.638-.16*(abs(lateral)/.947)**3),lateral,1.213 if not rear else 1.246))
    curve('L9_Rear_Light_Housing' if rear else 'L9_Front_Light_Housing',points,black,.035)
    curve('L9_Rear_Light_Bar' if rear else 'L9_Front_Light_Bar',
          [(x+sign*.027,y,z+.007) for x,y,z in points],red if rear else white,.009)

box('L9_Front_Intake',(2.617,0,.605),(.07,1.31,.34),black,.065)
for height in [.49,.55,.61,.67]:
    box('L9_Intake_Slat',(2.659,0,height),(.02,1.13,.024),paint,.008)
for side in [-1,1]:
    box(f'L9_Headlamp_Pocket_{side}',(2.624,side*.847,.773),(.09,.15,.405),black,.044)
    for height in [.765,.858]:
        box(f'L9_Headlamp_Lens_{side}_{height}',(2.675,side*.847,height),(.016,.09,.048),glass,.012)
    box(f'L9_Headlamp_LED_{side}',(2.684,side*.847,.739),(.012,.10,.014),white,.006)
    box(f'L9_Rear_Reflector_{side}',(-2.596,side*.64,.432),(.03,.35,.026),red,.012)
curve('L9_Front_Bumper_Bright',[(2.59-.10*abs(y),y,.385+.02*abs(y)) for y in [-.94,-.7,-.4,0,.4,.7,.94]],chrome,.018)
curve('L9_Rear_Bumper_Bright',[(-2.60+.09*abs(y),y,.385+.035*abs(y)) for y in [-.9,-.7,-.4,0,.4,.7,.9]],chrome,.018)
box('L9_Front_Plate',(2.68,0,.782),(.016,.47,.145),silver,.014)
box('L9_Rear_Plate_Recess',(-2.635,0,.997),(.02,.74,.25),black,.045)
box('L9_Rear_Plate',(-2.654,0,1.014),(.016,.47,.145),silver,.014)
tailgate=rounded_outline([(-.78,1.23),(.78,1.23),(.76,.80),(-.76,.80)],.1)
curve('L9_Tailgate_Seam',[(-2.643+.035*abs(y),y,z) for y,z in tailgate],black,.0035,True)
for side in [-1,1]:
    curve('L9_Hood_Seam',[(1.19,side*.80,1.30),(1.65,side*.81,1.297),(2.22,side*.82,1.272),
                         (2.48,side*.81,1.241)],black,.003)

references=bpy.data.collections.new('L9_Reference_Images')
scene.collection.children.link(references)
references.hide_render=True
references.hide_viewport=True
for index,path in enumerate(sorted((ROOT/'素材'/'理想L9-外观').glob('*.jpg'))):
    image=bpy.data.images.load(str(path),check_existing=True)
    image.pack()
    obj=bpy.data.objects.new('REF_'+path.stem,None)
    obj.empty_display_type='IMAGE'
    obj.data=image
    obj.empty_display_size=5.25
    obj.location=(0,4+index*.05,1)
    references.objects.link(obj)

floor=material('Studio_Floor',(.21,.235,.26),.05,.5)
box('L9_Studio_Floor',(0,0,-.085),(200,200,.15),floor,.0,stage)
world=bpy.data.worlds.new('L9_Studio_World')
world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.24,.27,.32,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.45
scene.world=world
for name,position,power,size in [('Key',(3,-4,7),1800,5),('Fill',(1,5,5),1300,4),('Rim',(-4,-1,6),2100,4)]:
    data=bpy.data.lights.new('L9_'+name,'AREA')
    data.energy=power
    data.shape='DISK'
    data.size=size
    obj=bpy.data.objects.new('L9_'+name,data)
    stage.objects.link(obj)
    obj.location=position
    obj.rotation_euler=(Vector((0,0,.8))-obj.location).to_track_quat('-Z','Y').to_euler()

for name,position in [('Front45',(8,-9,4.1)),('Rear45',(-8,-9,3.6)),('Side',(0,-11,2.2)),('Front',(11,0,2.0))]:
    data=bpy.data.cameras.new('L9_Camera_'+name)
    obj=bpy.data.objects.new(data.name,data)
    stage.objects.link(obj)
    obj.location=position
    obj.rotation_euler=(Vector((0,0,.88))-obj.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO'
    data.clip_end=500
    data.ortho_scale=6.9 if name!='Front' else 3.4
    if name == 'Side':
        data.type='PERSP'
        data.lens=55
scene.camera=bpy.data.objects['L9_Camera_Front45']
scene.render.engine='CYCLES'
scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.render.resolution_x=1200
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA'
        area.spaces.active.shading.color_type='MATERIAL'
        area.spaces.active.overlay.show_overlays=False

assert len([obj for obj in model.objects if obj.name.endswith('_Tire')]) == 4
assert len(references.objects) == 8
assert all(math.isfinite(value) for obj in model.objects for value in obj.location)
assert bpy.data.objects.get('Cube') and bpy.data.objects.get('Camera') and bpy.data.objects.get('Light')
scene['checks']='4 wheels, 8 packed reference images, finite transforms, original scene objects preserved'
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT/'L9_exterior_v01.blend'))
print('L9_BUILD_OK',len(model.objects),'model objects')
