from pathlib import Path
import ast
import math
import hashlib
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path('D:/bowen/demo/blender-demo')
scene=bpy.data.scenes['L9_Exterior_v02']
bpy.context.window.scene=scene
model=bpy.data.collections['AI_Model_L9_v02']
stage=bpy.data.collections['L9_Studio_v02']
source=ast.parse((ROOT/'build_l9.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[node for node in source.body if isinstance(node,ast.FunctionDef)],type_ignores=[]),'helpers','exec'))
assert not scene.get('refinement_complete'), 'Refinement already applied.'


def mat(name):
    return bpy.data.materials['L9_V02_'+name]


black=mat('Black')
glass=mat('Smoked_Glass')
frontglass=mat('Windshield')
chrome=mat('Satin_Chrome')
paint=mat('Warm_Graphite')
silver=mat('Champagne')
for name,color,roughness in [('Warm_Graphite',(.040,.038,.033),.31),
                             ('Champagne',(.26,.255,.23),.3),
                             ('Wheel_Facet',(.075,.080,.083),.31),
                             ('Wheel_Dark',(.036,.04,.043),.30),
                             ('Smoked_Glass',(.006,.01,.013),.24),
                             ('Windshield',(.014,.023,.051),.24)]:
    value=mat(name)
    value.diffuse_color=(*color,1)
    shader=value.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=(*color,1)
    shader.inputs['Roughness'].default_value=roughness
    if 'Glass' in name or name=='Windshield':
        shader.inputs['Specular IOR Level'].default_value=.22
        shader.inputs['Metallic'].default_value=.08

body=bpy.data.objects['V02_Body_Shell']
for polygon in body.data.polygons:
    if abs(polygon.normal.x)>.80:
        polygon.use_smooth=False
for modifier in body.modifiers:
    if modifier.type=='WEIGHTED_NORMAL':
        modifier.keep_sharp=True
        modifier.weight=75
for vertex in body.data.vertices:
    along,lateral,height=vertex.co
    if along>2.1 and height<.42:
        vertex.co.z += .075*min(1,(along-2.1)/.40)*min(1,(.42-height)/.20)

cabin=bpy.data.objects['V02_Cabin_Roof']
bpy.context.view_layer.update()
cabin_surface=BVHTree.FromObject(cabin,bpy.context.evaluated_depsgraph_get())
for front,name in [(True,'V02_Windshield'),(False,'V02_Rear_Window')]:
    for oldname in [name,name+'_Seal']:
        bpy.data.objects.remove(bpy.data.objects[oldname],do_unlink=True)
    sign=1 if front else -1
    outline=[(-.85,1.337),(.85,1.337),(.765,1.765),(-.765,1.765)] if front else [(-.847,1.365),(.847,1.365),(.74,1.76),(-.74,1.76)]
    boundary=rounded_outline(outline,.14,12)
    def mapped(lateral,height):
        hit=cabin_surface.ray_cast(Vector((sign*4,lateral,height)),Vector((-sign,0,0)))[0]
        assert hit is not None,(name,lateral,height)
        return (hit.x+sign*.045,lateral,height)
    center=Vector((0,1.55))
    vertices=[mapped(*center)]
    for ring in range(1,9):
        fraction=ring/8
        vertices.extend(mapped(*center.lerp(Vector(point),fraction)) for point in boundary)
    count=len(boundary)
    faces=[(0,1+index,1+(index+1)%count) for index in range(count)]
    for ring in range(7):
        inner=1+ring*count
        outer=inner+count
        faces.extend((inner+index,outer+index,outer+(index+1)%count,inner+(index+1)%count) for index in range(count))
    smooth(mesh(name,vertices,faces,frontglass if front else glass))
    curve(name+'_Seal',vertices[-count:],black,.007,True)

for obj in model.objects:
    if '_Wheel_' in obj.name and '_Fan_' in obj.name:
        side=-1 if '_-1_' in obj.name else 1
        for vertex in obj.data.vertices:
            center_x=1.66 if '_Front_' in obj.name else -1.53
            offset=Vector((vertex.co.x-center_x,vertex.co.z-.455))
            radius=offset.length
            if radius>.28:
                angle=math.atan2(offset.y,offset.x)
                angle+=.11
                vertex.co.x=center_x+radius*math.cos(angle)
                vertex.co.z=.455+radius*math.sin(angle)
        obj.modifiers['Spoke depth'].thickness=.006
    if '_Wheel_' in obj.name and '_Facet_' in obj.name:
        obj.hide_render=True
        obj.hide_viewport=True
    if obj.name.startswith('V02_Intake_Vertical'):
        obj.scale.y=2.3
        obj.scale.x=.8

for obj in model.objects:
    if obj.name.startswith('V02_Window_Perimeter_Chrome'):
        obj.data.bevel_depth=.004
    if obj.name.startswith('V02_Sill_'):
        obj.data.bevel_depth=.007

for name,position,lens_value in [('Front45',(11,-12,3.0),82),('Rear45',(-11,-12,3.0),82),
                                 ('Side',(0,-16,2.4),82),('Front',(14,0,2.15),94),('Rear',(-14,0,2.15),94)]:
    camera=bpy.data.objects['V02_Camera_'+name]
    camera.location=position
    camera.rotation_euler=(Vector((0,0,.93))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.lens=lens_value

floor=bpy.data.objects['V02_Studio_Floor']
floor.scale=(20,20,1)
backdrop=material('V02_Studio_Backdrop',(.45,.47,.48),0,.8)
bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=60,location=(0,0,0))
dome=bpy.context.object
dome.name='V02_Studio_Dome'
for collection in list(dome.users_collection):
    collection.objects.unlink(dome)
stage.objects.link(dome)
dome.data.materials.append(backdrop)
smooth(dome)
dome.hide_render=True
dome.hide_viewport=True
for obj in stage.objects:
    if obj.type=='CAMERA':
        obj.data.clip_end=100000
scene.camera=bpy.data.objects['V02_Camera_Front45']
scene['refinement_complete']=True
for polygon in body.data.polygons:
    polygon.use_smooth=True
rear_vertices=[]
rear_faces=[]
for row in range(41):
    height=.31+row*.96/40
    width=.922-.030*math.exp(-((height-.31)/.10)**2)
    for column in range(65):
        lateral=width*(column/32-1)
        along=-2.696+.035*(lateral/width)**4+.025*math.exp(-((height-.83)/.10)**2)
        rear_vertices.append((along,lateral,height))
for row in range(40):
    for column in range(64):
        base=row*65+column
        rear_faces.append((base,base+1,base+66,base+65))
smooth(mesh('V02_Rear_Fascia_Quad_Surface',rear_vertices,rear_faces,paint))
for name in ['V02_Rear_Plate_Back','V02_Rear_Plate']:
    bpy.data.objects[name].location.x-=.157
for obj in model.objects:
    if obj.type=='CURVE' and (obj.name.startswith('V02_Rear_Light') or obj.name.startswith('V02_Rear_Lower') or obj.name.startswith('V02_Rear_Reflector') or obj.name=='V02_Tailgate_Seam'):
        for spline in obj.data.splines:
            for point in spline.points:
                lateral,height=point.co.y,point.co.z
                point.co.x=-2.706+.035*(lateral/.922)**4+.025*math.exp(-((height-.83)/.10)**2)
assert hashlib.sha256((ROOT/'output/L9_exterior_v01.blend').read_bytes()).hexdigest()==scene['v01_sha256']
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'output/L9_exterior_v02.blend'))
print('V02_REFINEMENT_CHECK_OK')
