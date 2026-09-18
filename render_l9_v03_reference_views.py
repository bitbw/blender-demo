from pathlib import Path
import bpy
from mathutils import Vector

out=Path('D:/bowen/demo/blender-demo/output')
scene=bpy.data.scenes['L9_Blueprint_v03']
scene.render.engine='CYCLES'
scene.cycles.samples=48
scene.cycles.use_denoising=True
scene.render.resolution_x=1600
scene.render.resolution_y=1200
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
bpy.data.objects['V03_Floor'].hide_render=False

target=Vector((0,0,.72))
for name,location in {'FrontRight45':(10.5,-12,2.45),'RearLeft45':(-10.5,-12,2.45)}.items():
    data=bpy.data.cameras.new('Render_'+name)
    camera=bpy.data.objects.new('Render_'+name,data)
    scene.collection.objects.link(camera)
    data.type='PERSP'
    data.lens=68
    data.sensor_fit='HORIZONTAL'
    data.clip_start=.05
    data.clip_end=500
    camera.location=location
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.camera=camera
    scene.render.filepath=str(out/('L9_v03_'+name+'.png'))
    bpy.ops.render.render(write_still=True,scene=scene.name)
    assert Path(scene.render.filepath).stat().st_size>10000
    bpy.data.objects.remove(camera,do_unlink=True)
print('V03_REFERENCE_VIEWS_OK')
