"""Erzeugt eine dauerhaft vereinfachte Pine-Ridge-Laufzeitbibliothek."""

from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[2] / 'assets' / 'library' / 'pine_ridge'
SOURCE = ROOT / 'pine_ridge_asset.blend'
TARGET = ROOT / 'pine_ridge_runtime.blend'
COLLECTION_NAME = 'Pine Ridge Museum Exterior'
DECIMATE_RATIO = 0.08


bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False)
collection = bpy.data.collections.get(COLLECTION_NAME)
if collection is None:
    raise RuntimeError(f'Sammlung fehlt in {SOURCE}: {COLLECTION_NAME}')

reduced_meshes = {}
original_faces = 0
reduced_faces = 0

for obj in collection.objects:
    if obj.type != 'MESH':
        continue
    original = obj.data
    key = original.as_pointer()
    original_faces += len(original.polygons)
    if key not in reduced_meshes:
        helper = bpy.data.objects.new('Pine Ridge Runtime Reduction', original)
        bpy.context.scene.collection.objects.link(helper)
        modifier = helper.modifiers.new('Runtime LOD', 'DECIMATE')
        modifier.ratio = DECIMATE_RATIO
        bpy.context.view_layer.update()
        reduced = bpy.data.meshes.new_from_object(
            helper.evaluated_get(bpy.context.evaluated_depsgraph_get()),
            preserve_all_data_layers=True,
            depsgraph=bpy.context.evaluated_depsgraph_get(),
        )
        bpy.data.objects.remove(helper, do_unlink=True)
        reduced.name = original.name + ' Runtime LOD'
        reduced_meshes[key] = reduced
    obj.data = reduced_meshes[key]
    reduced_faces += len(obj.data.polygons)

bpy.data.orphans_purge(do_recursive=True)
bpy.data.libraries.write(str(TARGET), {collection}, fake_user=True, compress=True)
print(
    'RIDGE_RUNTIME_READY',
    len(collection.objects),
    'objects',
    len(reduced_meshes),
    'shared meshes',
    original_faces,
    '->',
    reduced_faces,
    'faces',
    flush=True,
)
