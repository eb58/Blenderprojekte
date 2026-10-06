"""In Blender ausführen: markiert CC0-Möbel als Collection-Assets."""
from pathlib import Path
import bpy

root = Path(__file__).resolve().parents[2] / 'assets' / 'library'
for asset_id in ('painted_wooden_bench', 'modular_street_seating', 'bar_chair_round_01'):
    path = root / asset_id / f'{asset_id}.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path))
    collection = bpy.data.collections.new(asset_id + ' Asset')
    bpy.context.scene.collection.children.link(collection)
    for obj in list(bpy.context.scene.objects):
        if obj.type == 'MESH':
            collection.objects.link(obj)
    collection.asset_mark()
    collection.asset_data.author = 'Poly Haven'
    collection.asset_data.description = f'CC0 furniture: https://polyhaven.com/a/{asset_id}'
    bpy.ops.file.pack_all()
    # Separate Bibliotheksdatei; Originaldownload bleibt für Prüfsummen erhalten.
    bpy.data.libraries.write(str(root / f'{asset_id}_asset.blend'), {collection},
                             path_remap='RELATIVE', fake_user=True)
    print('ASSET_READY', asset_id, len(collection.objects), flush=True)

for path in root.glob('*_asset.blend'):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    assets = [c for c in bpy.data.collections if c.asset_data]
    images = [i for i in bpy.data.images if i.source == 'FILE']
    assert len(assets) == 1, f'Asset fehlt: {path}'
    assert all(i.packed_file for i in images), f'Texturen fehlen: {path}'
    print('VERIFIED', path.name, len(assets[0].objects), 'objects',
          len(images), 'packed textures', flush=True)
