from pathlib import Path
import math

import bpy
from mathutils import Matrix, Vector


SOURCE = Path(r"D:\18211132604_64538\Desktop\3d_modles\2023_l9\l9.blend")
OUTPUT = Path(r"D:\bowen\demo\blender-demo\output\L9_2022_clean_assembly.blend")
PREVIEW = OUTPUT.with_suffix('.png')
LENGTH_M = 5.218


def bounds(objects):
    points = [obj.matrix_world @ vertex.co for obj in objects for vertex in obj.data.vertices]
    low = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    high = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    return low, high


scene = bpy.context.scene
meshes = [obj for obj in scene.objects if obj.type == 'MESH' and obj.name != 'Cube']
assert len(meshes) >= 50, f'Expected the converted L9 mesh set, found {len(meshes)} meshes.'

# The converted MAX scene uses X=width, Y=length, Z=height. Map it to
# Blender's conventional X=length, Y=width, Z=height, then scale by L9 length.
low, high = bounds(meshes)
scale = LENGTH_M / (high.y - low.y)
transform = Matrix.Rotation(-math.pi / 2, 4, 'Z') @ Matrix.Scale(scale, 4)
for obj in meshes:
    obj.matrix_world = transform @ obj.matrix_world

bpy.ops.object.select_all(action='DESELECT')
for obj in meshes:
    obj.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

low, high = bounds(meshes)
offset = Vector((-(low.x + high.x) / 2, -(low.y + high.y) / 2, -low.z))
for obj in meshes:
    obj.location += offset

for obj in list(scene.objects):
    if obj not in meshes:
        bpy.data.objects.remove(obj, do_unlink=True)
for collection in list(scene.collection.children):
    bpy.data.collections.remove(collection)

assembly = bpy.data.collections.new('L9_2022_Assembly')
parts = bpy.data.collections.new('Vehicle_Parts')
wheels = bpy.data.collections.new('Wheel_Assemblies')
studio = bpy.data.collections.new('Studio')
scene.collection.children.link(assembly)
assembly.children.link(parts)
assembly.children.link(wheels)
scene.collection.children.link(studio)

wheel_candidates = sorted(
    [obj for obj in meshes if obj.dimensions.x > .65 and obj.dimensions.z > .65 and .18 < obj.dimensions.y < .32],
    key=lambda obj: (obj.location.x, obj.location.y),
)
assert len(wheel_candidates) == 4, f'Expected 4 wheel assemblies, found {len(wheel_candidates)}.'
wheel_set = set(wheel_candidates)

root = bpy.data.objects.new('L9_2022_Root', None)
assembly.objects.link(root)
root.empty_display_type = 'PLAIN_AXES'
root.empty_display_size = .4
for index, obj in enumerate(sorted(meshes, key=lambda item: item.name), 1):
    source_name = obj.name
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    (wheels if obj in wheel_set else parts).objects.link(obj)
    obj.parent = root
    obj['source_object_name'] = source_name
    obj.name = f'Wheel_{wheel_candidates.index(obj) + 1:02d}' if obj in wheel_set else f'L9_Part_{index:03d}'

scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene['source_max'] = r'D:\18211132604_64538\Desktop\3d_modles\2023_l9\2022.max'
scene['source_converted_blend'] = str(SOURCE)
scene['target_length_m'] = LENGTH_M
scene['assembly_note'] = 'Geometry retained from the converted 2022.max asset; only transforms, hierarchy, names, and presentation were cleaned.'

floor_mat = bpy.data.materials.new('Studio_Floor')
floor_mat.diffuse_color = (.07, .08, .10, 1)
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.object
floor.name = 'Studio_Floor'
for collection in list(floor.users_collection):
    collection.objects.unlink(floor)
studio.objects.link(floor)
floor.data.materials.append(floor_mat)

world = bpy.data.worlds.new('Studio_World')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.055, .065, .09, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .35
scene.world = world

target = Vector((0, 0, .85))
for name, location, energy, size in [('Key', (5, -6, 6), 1200, 4), ('Fill', (1, 5, 4), 900, 5), ('Rim', (-5, -3, 5), 1100, 3)]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = energy
    data.shape = 'DISK'
    data.size = size
    light = bpy.data.objects.new(name, data)
    studio.objects.link(light)
    light.location = location
    light.rotation_euler = (target - light.location).to_track_quat('-Z', 'Y').to_euler()

camera_data = bpy.data.cameras.new('Camera')
camera = bpy.data.objects.new('Camera', camera_data)
studio.objects.link(camera)
camera.location = (7.6, -8.0, 4.1)
camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera_data.lens = 55
scene.camera = camera

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1400
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(PREVIEW)
scene.view_settings.look = 'AgX - Medium High Contrast'

bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
bpy.ops.render.render(write_still=True)

low, high = bounds(meshes)
assert abs((high.x - low.x) - LENGTH_M) < .01, (low, high)
assert len(wheel_candidates) == 4
assert OUTPUT.exists() and PREVIEW.exists()
print('L9_2022_ASSEMBLY_OK', tuple(round(value, 3) for value in high - low))
