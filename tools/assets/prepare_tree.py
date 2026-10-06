from pathlib import Path
import bpy
root = Path(__file__).resolve().parents[2] / 'assets/library'
bpy.ops.wm.open_mainfile(filepath=str(root / 'tree_small_02/tree_small_02.blend'))
tree = bpy.data.objects['tree_small_02_LOD1']
tree.hide_render = False
tree.hide_viewport = False
for material in tree.data.materials:
    images = [n.image for n in material.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
    nodes = material.node_tree.nodes
    nodes.clear()
    shader = nodes.new('ShaderNodeBsdfPrincipled')
    output = nodes.new('ShaderNodeOutputMaterial')
    links = material.node_tree.links
    links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    for image in images:
        tex = nodes.new('ShaderNodeTexImage'); tex.image = image
        if '_diff' in image.name:
            links.new(tex.outputs['Color'], shader.inputs['Base Color'])
        elif '_rough' in image.name:
            links.new(tex.outputs['Color'], shader.inputs['Roughness'])
        elif '_alpha' in image.name:
            links.new(tex.outputs['Color'], shader.inputs['Alpha'])
        elif '_nor_gl' in image.name:
            normal = nodes.new('ShaderNodeNormalMap')
            links.new(tex.outputs['Color'], normal.inputs['Color'])
            links.new(normal.outputs['Normal'], shader.inputs['Normal'])
    material.use_backface_culling = False
print('TREE_POLYGONS', len(tree.data.polygons), flush=True)
bpy.ops.file.pack_all()
bpy.data.libraries.write(str(root / 'tree_small_02_asset.blend'), {tree}, fake_user=True)
