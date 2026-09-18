from pathlib import Path
import bpy

output=Path('D:/bowen/demo/blender-demo/output')
scene=bpy.data.scenes['L9_Exterior_v02']
scene.cycles.samples=24
for name in ['Front45','Side','Rear45','Front','Rear']:
    scene.camera=bpy.data.objects['V02_Camera_'+name]
    scene.render.filepath=str(output/('L9_v02_'+name+'.png'))
    bpy.ops.render.render(write_still=True,scene=scene.name)
    assert Path(scene.render.filepath).stat().st_size>10000
print('L9_V02_RENDER_CHECK_OK')
