from pathlib import Path
import bpy

output = Path('D:/bowen/demo/blender-demo/output')
scene = bpy.data.scenes['L9_Exterior_v01']
scene.cycles.samples = 16
for name in ['Front45', 'Side', 'Rear45', 'Front']:
    scene.camera = bpy.data.objects['L9_Camera_' + name]
    scene.render.filepath = str(output / ('L9_' + name + '.png'))
    bpy.ops.render.render(write_still=True, scene=scene.name)
    assert Path(scene.render.filepath).stat().st_size > 10000
print('L9_RENDER_CHECK_OK')
