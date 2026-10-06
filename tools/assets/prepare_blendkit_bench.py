from pathlib import Path
import bpy
from mathutils import Vector
root = Path(__file__).resolve().parents[2] / 'assets/library/blendkit_bench'
bpy.ops.wm.open_mainfile(filepath=str(root / 'bench.blend'), load_ui=False)
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        print('BENCH_PART', obj.name, tuple(obj.dimensions), [m.name for m in obj.data.materials], flush=True)
bpy.ops.file.pack_all()
objects = {o for o in bpy.context.scene.objects if o.type == 'MESH'}
for obj in objects:
    obj.data = obj.data.copy()
    obj.data.transform(obj.matrix_world)
    obj.parent = None
    obj.matrix_world.identity()
    points = [v.co for v in obj.data.vertices]
    offset = Vector(((min(p.x for p in points) + max(p.x for p in points)) / 2,
                     (min(p.y for p in points) + max(p.y for p in points)) / 2,
                     min(p.z for p in points)))
    for vertex in obj.data.vertices:
        vertex.co -= offset
    for material in obj.data.materials:
        material.name = 'Blendkit Museumsbank ' + material.name
bpy.data.libraries.write(str(root / 'bench_asset.blend'), objects, fake_user=True)
