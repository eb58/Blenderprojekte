"""Pine Ridge für die Außenansicht des Museums vorbereiten (in Blender)."""
from pathlib import Path
import bpy
root = Path(__file__).resolve().parents[2] / 'assets/library/pine_ridge'
bpy.ops.wm.open_mainfile(filepath=str(root / 'pine_ridge.blend'), load_ui=False)
scene = bpy.context.scene
# Grass scatter is excessive for distant window views; retain terrain and forest.
for obj in scene.objects:
    if obj.name.startswith('grass scatter'):
        for modifier in obj.modifiers:
            modifier.show_viewport = False
depsgraph = bpy.context.evaluated_depsgraph_get()
collection = bpy.data.collections.new('Pine Ridge Museum Exterior')
meshes = {}
for instance in depsgraph.object_instances:
    source = instance.object
    parent_name = instance.parent.original.name if instance.parent else ''
    name = source.original.name
    keep = (name == 'Plane' or name == 'treee scatter' or
            (instance.is_instance and parent_name == 'treee scatter') or
            (name.startswith('TREE.') and int(name.split('.')[-1]) >= 3))
    if not keep or source.type != 'MESH':
        continue
    key = source.data.as_pointer()
    if key not in meshes:
        mesh = bpy.data.meshes.new_from_object(source, preserve_all_data_layers=True, depsgraph=depsgraph)
        if not mesh.polygons:
            bpy.data.meshes.remove(mesh)
            continue
        meshes[key] = mesh
    obj = bpy.data.objects.new('Pine Ridge ' + name, meshes[key])
    collection.objects.link(obj)
    obj.matrix_world = instance.matrix_world.copy()
bpy.ops.file.pack_all()
assert len(collection.objects) > 5, 'Forest instances missing'
bpy.data.libraries.write(str(root / 'pine_ridge_asset.blend'), {collection}, fake_user=True)
print('RIDGE_READY', len(collection.objects), 'objects', len(meshes), 'shared meshes', flush=True)
