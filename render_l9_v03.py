from pathlib import Path
import bpy
import hashlib
import math
import shutil
from datetime import datetime
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

output=Path('D:/bowen/demo/blender-demo/output')
scene=bpy.data.scenes['L9_Blueprint_v03']
bpy.context.window.scene=scene
floor=bpy.data.objects['V03_Floor']
blend_path=Path(bpy.data.filepath)
blend_hash=hashlib.sha256(blend_path.read_bytes()).hexdigest()
backup=output/('V03_previous_images_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
backup.mkdir()
for image in output.glob('L9_v03_*.png'):
    shutil.copy2(image,backup/image.name)
for name,digest in {
    'L9_exterior_v01.blend':'7c71d3a5f388aedee893dd3dd9dbd1c5a5acf768e061c408a7501f3bbac37ef3',
    'L9_exterior_v02.blend':'dc9e388d61f86afe1338adfbedb92c1ee6c9f5f6aa3dc1be4f5c69779c2d4b90',
}.items():
    assert hashlib.sha256((output/name).read_bytes()).hexdigest()==digest, name+' changed'
graph=bpy.context.evaluated_depsgraph_get()
centers={}
model_points=[]
for obj in bpy.data.collections['AI_Model_L9_v03'].objects:
    evaluated=obj.evaluated_get(graph)
    data=evaluated.to_mesh()
    points=[evaluated.matrix_world@v.co for v in data.vertices]
    model_points.extend(points)
    assert min(p.z for p in points)>-.00001, obj.name+' below ground'
    if obj.name.endswith('_Tire'):
        centers[obj.name]=(min(p.x for p in points)+max(p.x for p in points))/2
    evaluated.to_mesh_clear()
assert len(centers)==4
assert abs(centers['V03_Wheel_Front_1_Tire']-centers['V03_Wheel_Rear_1_Tire']-3.105)<.00001
scene.cycles.samples=48
scene.cycles.use_denoising=True
scene.render.resolution_x=1600
scene.render.resolution_y=1200
scene.render.resolution_percentage=100
scene.render.image_settings.color_mode='RGB'
scene.render.film_transparent=False
scene.render.use_border=False
scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
# Keep studio illumination; only camera rays see the neutral background.
nodes=scene.world.node_tree.nodes
links=scene.world.node_tree.links
light_path=nodes.new('ShaderNodeLightPath')
background=nodes.new('ShaderNodeBackground')
background.inputs['Color'].default_value=(.65,.65,.65,1)
background.inputs['Strength'].default_value=.8
mix=nodes.new('ShaderNodeMixShader')
world_output=next(n for n in nodes if n.type=='OUTPUT_WORLD' and n.is_active_output)
illumination=world_output.inputs['Surface'].links[0].from_socket
links.new(illumination,mix.inputs[1])
links.new(background.outputs[0],mix.inputs[2])
links.new(light_path.outputs['Is Camera Ray'],mix.inputs[0])
links.new(mix.outputs[0],world_output.inputs['Surface'])
target=Vector((0,0,.91))
views={'Front45':(10,-12,5.0),'Rear45':(-10,-12,5.0),
       'Side':(0,12,.91),'RightSide':(0,-12,.91),
       'Front':(12,0,.91),'Rear':(-12,0,.91),'Top':(0,0,12)}
for name,position in views.items():
    camera=bpy.data.objects.get('V03_Camera_'+name)
    if camera is None:
        camera=bpy.data.objects.new('V03_Camera_'+name,bpy.data.cameras.new('V03_Camera_'+name))
        scene.collection.objects.link(camera)
    scene.camera=camera
    camera.location=position
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    if name=='Top':
        camera.rotation_euler=(0,0,math.pi)  # nose left, matching blueprint
        camera.location=(0,0,12)
    camera.data.type='PERSP' if name.endswith('45') else 'ORTHO'
    camera.data.lens=65
    camera.data.sensor_fit='HORIZONTAL'
    camera.data.shift_x=camera.data.shift_y=0
    camera.data.ortho_scale=6.4 if name in ['Side','RightSide','Top'] else 3.25
    camera.data.clip_start=.05
    camera.data.clip_end=500
    camera.data.dof.use_dof=False
    floor.hide_render=not name.endswith('45')
    # Check actual evaluated geometry, including mirrors, fits every camera.
    for attempt in range(12):
        bpy.context.view_layer.update()
        projected=[world_to_camera_view(scene,camera,p) for p in model_points[::12]]
        if all(.07<p.x<.93 and .07<p.y<.93 and p.z>0 for p in projected):
            break
        if camera.data.type=='ORTHO':
            camera.data.ortho_scale*=1.06
        else:
            camera.location=target+(camera.location-target)*1.06
    else:
        raise AssertionError(name+' cannot fit model')
    for point in model_points:
        p=world_to_camera_view(scene,camera,point)
        assert .055<p.x<.945 and .055<p.y<.945 and p.z>0, name+' clips model'
    scene.render.filepath=str(output/('L9_v03_'+name+'.png'))
    bpy.ops.render.render(write_still=True,scene=scene.name)
    assert Path(scene.render.filepath).stat().st_size>10000
assert hashlib.sha256(blend_path.read_bytes()).hexdigest()==blend_hash, 'V03 blend changed'
print('V03_RENDER_CHECK_OK')
