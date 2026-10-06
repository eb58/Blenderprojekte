"""Komplettes Museum: Granitskulptur, Architektur und OptiX-Renderpreset.
In Blender ausfuehren. Ersetzt alle vorhandenen Objekte; speichert nicht automatisch.
Keine Besucher. Vorhandene lokale Marmorbuesten werden optional verwendet.
"""
import os
import json

# Einstellungen fuer den gesamten Aufbau
PROJECT_DIR = r"C:\Users\erich\OneDrive\Blenderprojekte"
BODEN = "marmor"  # "parkett" oder "marmor"
WANDGESTALTUNG = "wandteppich"
RENDER_PRESET = "test"  # "test", "final_fast", "animation", "quality"
P = 7

# False = Testbild mit F12; True = PNG-Bildfolge mit Strg+F12
MAKE_VIDEO = True

FPS = 24
DURATION = 5
ORBIT_DEGREES = 360
START_ANGLE = 158

SCULPTURE_SCALE = 3.55
THICKNESS = 0.060

OUTPUT_DIR = os.path.join(PROJECT_DIR, "Render", "kusner_p7_granit_museum")
FRAMES_DIR = os.path.join(OUTPUT_DIR, "frames")
STILL_OUTPUT = os.path.join(OUTPUT_DIR, "kusner_p7_museum_test.png")
ANIMATION_OUTPUT = os.path.join(FRAMES_DIR, "frame_####")
# Vorhandene Frames beim erneuten Animationsrendern ueberspringen.
# Fuer eine geaenderte Szene einen neuen OUTPUT_DIR verwenden.
RESUME_RENDER = True

# Optionale Einstellungen der Windows-Oberflaeche.
RESOLUTION_X, RESOLUTION_Y = 1280, 800
config_path = os.environ.get("MUSEUM_CONFIG")
if config_path:
    with open(config_path, encoding="utf-8-sig") as config_file:
        config = json.load(config_file)
    for setting in ("BODEN", "RENDER_PRESET", "MAKE_VIDEO", "FPS", "DURATION",
                    "ORBIT_DEGREES", "START_ANGLE", "SCULPTURE_SCALE", "THICKNESS",
                    "OUTPUT_DIR", "RESUME_RENDER", "RESOLUTION_X", "RESOLUTION_Y"):
        if setting in config:
            globals()[setting] = config[setting]
    FRAMES_DIR = os.path.join(OUTPUT_DIR, "frames")
    STILL_OUTPUT = os.path.join(OUTPUT_DIR, "kusner_p7_museum_test.png")
    ANIMATION_OUTPUT = os.path.join(FRAMES_DIR, "frame_####")



GRANITE_SPEC = json.loads("{\"interface\":[],\"links\":[[\"Group\",0,\"Material Output\",0]],\"name\":\"Shader Nodetree\",\"nodes\":[{\"idname\":\"ShaderNodeOutputMaterial\",\"in\":{\"2\":[0,0,0],\"3\":0},\"loc\":[1599,420],\"name\":\"Material Output\",\"parent\":null,\"props\":{\"height\":100,\"label\":\"\",\"name\":\"Material Output\",\"target\":\"ALL\",\"width\":140}},{\"group\":{\"interface\":[{\"in_out\":\"OUTPUT\",\"name\":\"BSDF\",\"socket_type\":\"NodeSocketShader\"},{\"default\":1,\"in_out\":\"INPUT\",\"max_value\":3.4028234663852886e+38,\"min_value\":-3.4028234663852886e+38,\"name\":\"Scale\",\"socket_type\":\"NodeSocketFloat\"},{\"default\":[0.17788739502429962,0.07036018371582031,0.031896062195301056,1],\"in_out\":\"INPUT\",\"name\":\"Color 1\",\"socket_type\":\"NodeSocketColor\"},{\"default\":[0.31398674845695496,0.24228137731552124,0.11953852325677872,1],\"in_out\":\"INPUT\",\"name\":\"Color 2\",\"socket_type\":\"NodeSocketColor\"},{\"default\":[0.05612814798951149,0.036889489740133286,0.02315337210893631,1],\"in_out\":\"INPUT\",\"name\":\"Color 3\",\"socket_type\":\"NodeSocketColor\"},{\"default\":[0.3231411874294281,0.23074033856391907,0.1620294749736786,1],\"in_out\":\"INPUT\",\"name\":\"Color 4\",\"socket_type\":\"NodeSocketColor\"},{\"default\":[0.31854474544525146,0.2874411344528198,0.14126339554786682,1],\"in_out\":\"INPUT\",\"name\":\"Color 5\",\"socket_type\":\"NodeSocketColor\"},{\"default\":15,\"in_out\":\"INPUT\",\"max_value\":15,\"min_value\":0,\"name\":\"Detail\",\"socket_type\":\"NodeSocketFloat\"},{\"default\":1,\"in_out\":\"INPUT\",\"max_value\":2,\"min_value\":0,\"name\":\"Rougness\",\"socket_type\":\"NodeSocketFloat\"}],\"links\":[[\"Color Ramp.002\",0,\"Mix.003\",0],[\"Color Ramp\",0,\"Mix\",0],[\"Voronoi Texture\",0,\"Color Ramp.002\",0],[\"Mix.002\",2,\"Mix.003\",6],[\"Hue/Saturation/Value\",0,\"Principled BSDF\",2],[\"Noise Texture.001\",0,\"Color Ramp.001\",0],[\"Noise Texture\",0,\"Color Ramp\",0],[\"Mix.003\",2,\"Color Ramp.003\",0],[\"Mix.001\",2,\"Mix.002\",6],[\"Mapping\",0,\"Noise Texture\",0],[\"Texture Coordinate\",3,\"Mapping\",0],[\"Mapping\",0,\"Noise Texture.001\",0],[\"Color Ramp.001\",0,\"Mix.001\",0],[\"Mapping\",0,\"Noise Texture.002\",0],[\"Mix\",2,\"Mix.002\",7],[\"Mix.003\",2,\"Principled BSDF\",0],[\"Color Ramp.003\",0,\"Hue/Saturation/Value\",4],[\"Noise Texture.002\",1,\"Voronoi Texture\",0],[\"Principled BSDF\",0,\"Group Output\",0],[\"Group Input\",0,\"Mapping\",3],[\"Group Input\",1,\"Mix.001\",6],[\"Group Input\",2,\"Mix.001\",7],[\"Group Input\",3,\"Mix\",6],[\"Group Input\",4,\"Mix\",7],[\"Group Input\",5,\"Mix.003\",7],[\"Group Input\",6,\"Noise Texture.002\",3],[\"Group Input\",6,\"Noise Texture.001\",3],[\"Group Input\",6,\"Noise Texture\",3],[\"Group Input\",7,\"Hue/Saturation/Value\",2]],\"name\":\"Procedural Brown Granite\",\"nodes\":[{\"idname\":\"NodeGroupOutput\",\"in\":{},\"loc\":[1485,0],\"name\":\"Group Output\",\"parent\":null,\"props\":{\"height\":100,\"label\":\"\",\"name\":\"Group Output\",\"width\":140}},{\"idname\":\"NodeGroupInput\",\"in\":{},\"loc\":[-1095,-573],\"name\":\"Group Input\",\"parent\":null,\"props\":{\"height\":100,\"label\":\"\",\"name\":\"Group Input\",\"width\":140}},{\"idname\":\"ShaderNodeBsdfPrincipled\",\"in\":{\"1\":0,\"3\":1.5,\"4\":1,\"5\":false,\"6\":[0,0,0],\"7\":0,\"8\":0,\"9\":0,\"10\":[1,0.20000000298023224,0.10000000149011612],\"11\":0.05000000074505806,\"12\":1.399999976158142,\"13\":0,\"14\":0.5,\"15\":[1,1,1,1],\"16\":0,\"17\":0,\"18\":[0,0,0],\"19\":0,\"20\":0,\"21\":0.029999999329447746,\"22\":1.5,\"23\":[1,1,1,1],\"24\":[0,0,0],\"25\":0,\"26\":0.5,\"27\":[1,1,1,1],\"28\":[1,1,1,1],\"29\":0,\"30\":0,\"31\":1.3300000429153442},\"loc\":[1195,108],\"name\":\"Principled BSDF\",\"parent\":null,\"props\":{\"distribution\":\"MULTI_GGX\",\"height\":100,\"label\":\"\",\"name\":\"Principled BSDF\",\"subsurface_method\":\"RANDOM_WALK_LEGACY\",\"width\":240}},{\"idname\":\"ShaderNodeTexNoise\",\"in\":{\"1\":0,\"2\":4,\"4\":1,\"5\":2,\"6\":0,\"7\":1,\"8\":0},\"loc\":[30,-30],\"name\":\"Noise Texture\",\"parent\":\"Frame\",\"props\":{\"height\":100,\"label\":\"\",\"name\":\"Noise Texture\",\"noise_dimensions\":\"4D\",\"noise_type\":\"FBM\",\"normalize\":false,\"width\":140}},{\"idname\":\"ShaderNodeMapping\",\"in\":{\"1\":[0,0,0],\"2\":[0,0,0]},\"loc\":[210,-30],\"name\":\"Mapping\",\"parent\":\"Frame.001\",\"props\":{\"height\":100,\"label\":\"\",\"name\":\"Mapping\",\"vector_type\":\"POINT\",\"width\":140}},{\"idname\":\"ShaderNodeTexCoord\",\"in\":{},\"loc\":[30,-30],\"name\":\"Texture Coordinate\",\"parent\":\"Frame.001\",\"props\":{\"from_instancer\":false,\"height\":100,\"label\":\"\",\"name\":\"Texture Coordinate\",\"width\":140}},{\"idname\":\"ShaderNodeMix\",\"in\":{\"1\":[0.5,0.5,0.5],\"2\":0,\"3\":0,\"4\":[0,0,0],\"5\":[0,0,0],\"8\":[0,0,0],\"9\":[0,0,0]},\"loc\":[504,-51],\"name\":\"Mix\",\"parent\":\"Frame\",\"props\":{\"blend_type\":\"MIX\",\"clamp_factor\":true,\"clamp_result\":false,\"data_type\":\"RGBA\",\"factor_mode\":\"UNIFORM\",\"height\":100,\"label\":\"\",\"name\":\"Mix\",\"width\":140}},{\"idname\":\"ShaderNodeValToRGB\",\"in\":{},\"loc\":[207,-60],\"name\":\"Color Ramp\",\"parent\":\"Frame\",\"props\":{\"height\":100,\"label\":\"\",\"name\":\"Color Ramp\",\"width\":240},\"ramp\":{\"els\":[[0,[0,0,0,1]],[0.4580153524875641,[1,1,1,1]]],\"interp\":\"LINEAR\",\"mode\":\"RGB\"}},{\"idname\":\"NodeFrame\",\"in\":{},\"loc\":[-677,-380],\"name\":\"Frame\",\"parent\":null,\"props\":{\"height\":361.6744384765625,\"label\":\"\",\"label_size\":20,\"name\":\"Frame\",\"shrink\":true,\"width\":674.1395874023438}},{\"idname\":\"NodeFrame\",\"in\":{},\"loc\":[-1196,-188],\"name\":\"Frame.001\",\"parent\":null,\"props\":{\"height\":349.9535217285156,\"label\":\"\",\"label_size\":20,\"name\":\"Frame.001\",\"shrink\":true,\"width\":380.27911376953125}},{\"idname\":\"ShaderNodeTexNoise\",\"in\":{\"1\":0,\"2\":6,\"4\":0.7300000190734863,\"5\":4.599999904632568,\"6\":0,\"7\":1,\"8\":0},\"loc\":[30,-30],\"name\":\"Noise Texture.001\",\"parent\":\"Frame.002\",\"props\":{\"height\":100,\"label\":\"\",\"name\":\"Noise Texture.001\",\"noise_dimensions\":\"3D\",\"noise_type\":\"FBM\",\"normalize\":true,\"width\":140}},{\"idname\":\"ShaderNodeValToRGB\",\"in\":{},\"loc\":[202,-51],\"name\":\"Color Ramp.001\",\"parent\":\"Frame.002\",\"props\":{\"height\":100,\"label\":\"\",\"name\":\"Color Ramp.001\",\"width\":240},\"ramp\":{\"els\":[[0.3358778655529022,[0,0,0,1]],[0.6755727529525757,[1,1,1,1]]],\"interp\":\"LINEAR\",\"mode\":\"RGB\"}},{\"idname\":\"ShaderNodeMix\",\"in\":{\"1\":[0.5,0.5,0.5],\"2\":0,\"3\":0,\"4\":[0,0,0],\"5\":[0,0,0],\"8\":[0,0,0],\"9\":[0,0,0]},\"loc\":[500,-51],\"name\":\"Mix.001\",\"parent\":\"Frame.002\",\"props\":{\"blend_type\":\"MIX\",\"clamp_factor\":true,\"clamp_result\":false,\"data_type\":\"RGBA\",\"factor_mode\":\"UNIFORM\",\"height\":100,\"label\":\"\",\"name\":\"Mix.001\",\"width\":140}},{\"idname\":\"NodeFrame\",\"in\":{},\"loc\":[-671,53],\"name\":\"Frame.002\",\"parent\":null,\"props\":{\"height\":339.906982421875,\"label\":\"\",\"label_size\":20,\"name\":\"Frame.002\",\"shrink\":true,\"width\":670.7907104492188}},{\"idname\":\"ShaderNodeTexVoronoi\",\"in\":{\"1\":0,\"2\":20,\"3\":6.699999809265137,\"4\":0.4699999988079071,\"5\":5.300000190734863,\"6\":1,\"7\":0.5,\"8\":1},\"loc\":[209,-44],\"name\":\"Voronoi Texture\",\"parent\":\"Frame.003\",\"props\":{\"distance\":\"EUCLIDEAN\",\"feature\":\"DISTANCE_TO_EDGE\",\"height\":100,\"label\":\"\",\"name\":\"Voronoi Texture\",\"normalize\":false,\"voronoi_dimensions\":\"3D\",\"width\":140}},{\"idname\":\"ShaderNodeTexNoise\",\"in\":{\"1\":0,\"2\":2,\"4\":0.6800000071525574,\"5\":2,\"6\":0,\"7\":1,\"8\":0},\"loc\":[30,-30],\"name\":\"Noise Texture.002\",\"parent\":\"Frame.003\",\"props\":{\"height\":100,\"label\":\"\",\"name\":\"Noise Texture.002\",\"noise_dimensions\":\"3D\",\"noise_type\":\"FBM\",\"normalize\":true,\"width\":140}},{\"idname\":\"ShaderNodeValToRGB\",\"in\":{},\"loc\":[369,-50],\"name\":\"Color Ramp.002\",\"parent\":\"Frame.003\",\"props\":{\"height\":100,\"label\":\"\",\"name\":\"Color Ramp.002\",\"width\":240},\"ramp\":{\"els\":[[0.030534353107213974,[0,0,0,1]],[0.27099260687828064,[1,1,1,1]]],\"interp\":\"LINEAR\",\"mode\":\"RGB\"}},{\"idname\":\"NodeFrame\",\"in\":{},\"loc\":[-654,440],\"name\":\"Frame.003\",\"parent\":null,\"props\":{\"height\":344.93023681640625,\"label\":\"\",\"label_size\":20,\"name\":\"Frame.003\",\"shrink\":true,\"width\":638.5115966796875}},{\"idname\":\"ShaderNodeMix\",\"in\":{\"0\":1,\"1\":[0.5,0.5,0.5],\"2\":0,\"3\":0,\"4\":[0,0,0],\"5\":[0,0,0],\"8\":[0,0,0],\"9\":[0,0,0]},\"loc\":[242,-140],\"name\":\"Mix.002\",\"parent\":null,\"props\":{\"blend_type\":\"DARKEN\",\"clamp_factor\":true,\"clamp_result\":false,\"data_type\":\"RGBA\",\"factor_mode\":\"UNIFORM\",\"height\":100,\"label\":\"\",\"name\":\"Mix.002\",\"width\":140}},{\"idname\":\"ShaderNodeMix\",\"in\":{\"1\":[0.5,0.5,0.5],\"2\":0,\"3\":0,\"4\":[0,0,0],\"5\":[0,0,0],\"8\":[0,0,0],\"9\":[0,0,0]},\"loc\":[425,89],\"name\":\"Mix.003\",\"parent\":null,\"props\":{\"blend_type\":\"MIX\",\"clamp_factor\":true,\"clamp_result\":false,\"data_type\":\"RGBA\",\"factor_mode\":\"UNIFORM\",\"height\":100,\"label\":\"\",\"name\":\"Mix.003\",\"width\":140}},{\"idname\":\"ShaderNodeValToRGB\",\"in\":{},\"loc\":[30,-71],\"name\":\"Color Ramp.003\",\"parent\":\"Frame.004\",\"props\":{\"height\":100,\"label\":\"\",\"name\":\"Color Ramp.003\",\"width\":240},\"ramp\":{\"els\":[[0,[0.03820410370826721,0.03820440545678139,0.0382043831050396,1]],[1,[1,1,1,1]]],\"interp\":\"LINEAR\",\"mode\":\"RGB\"}},{\"idname\":\"ShaderNodeHueSaturation\",\"in\":{\"0\":0.5,\"1\":1,\"3\":1},\"loc\":[311,-30],\"name\":\"Hue/Saturation/Value\",\"parent\":\"Frame.004\",\"props\":{\"height\":100,\"label\":\"\",\"name\":\"Hue/Saturation/Value\",\"width\":150}},{\"idname\":\"NodeFrame\",\"in\":{},\"loc\":[601,-42],\"name\":\"Frame.004\",\"parent\":null,\"props\":{\"height\":304.7441711425781,\"label\":\"\",\"label_size\":20,\"name\":\"Frame.004\",\"shrink\":true,\"width\":490.74420166015625}}]},\"idname\":\"ShaderNodeGroup\",\"in\":{\"0\":1,\"1\":[0.08074022829532623,0.11972354352474213,0.18556973338127136,1],\"2\":[0.31398674845695496,0.24228137731552124,0.11953852325677872,1],\"3\":[0.05612814798951149,0.036889489740133286,0.02315337210893631,1],\"4\":[0.22557133436203003,0.16208183765411377,0.11446116119623184,1],\"5\":[0.3443961441516876,0.3106135427951813,0.15228861570358276,1],\"6\":15,\"7\":1},\"loc\":[1395,431],\"name\":\"Group\",\"parent\":null,\"props\":{\"height\":100,\"label\":\"\",\"name\":\"Group\",\"width\":140}}]}")

import bpy
import cmath
import math
from mathutils import Vector


def enable_optix():
    """OptiX aktivieren und ausschliesslich erkannte OptiX-GPUs verwenden."""
    cycles_preferences = bpy.context.preferences.addons["cycles"].preferences

    try:
        cycles_preferences.compute_device_type = "OPTIX"
    except TypeError as exc:
        raise RuntimeError(
            "OptiX ist in dieser Blender-Installation nicht verfuegbar. "
            "Bitte NVIDIA-Treiber und Blender-Version pruefen."
        ) from exc

    cycles_preferences.get_devices()
    optix_devices = [
        device
        for device in cycles_preferences.devices
        if device.type == "OPTIX"
    ]

    if not optix_devices:
        raise RuntimeError("Blender hat kein OptiX-faehiges Geraet gefunden.")

    for device in cycles_preferences.devices:
        device.use = device.type == "OPTIX"

    print(
        "OptiX aktiviert: "
        + ", ".join(device.name for device in optix_devices)
    )


# ============================================================
# EINSTELLUNGEN
# ============================================================

# ============================================================
# SZENE / RENDERER
# ============================================================

# Die Datei vollständig leeren, einschließlich ausgeblendeter oder nicht
# auswählbarer Objekte aus anderen Collections. So bleiben insbesondere keine
# zuvor importierten Personen in der neu aufgebauten Museumsszene zurück.
for existing_object in list(bpy.data.objects):
    bpy.data.objects.remove(existing_object, do_unlink=True)

scene = bpy.context.scene
scene.render.engine = "CYCLES"
enable_optix()
scene.cycles.device = "GPU"
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 8
scene.cycles.diffuse_bounces = 4
scene.cycles.glossy_bounces = 6
scene.render.resolution_x = RESOLUTION_X
scene.render.resolution_y = RESOLUTION_Y
scene.render.resolution_percentage = 100
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = max(2, round(FPS * DURATION))

if MAKE_VIDEO:
    scene.cycles.samples = 48
    os.makedirs(FRAMES_DIR, exist_ok=True)
    scene.render.filepath = ANIMATION_OUTPUT
    scene.render.use_overwrite = not RESUME_RENDER
else:
    scene.cycles.samples = 64
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    scene.render.filepath = STILL_OUTPUT
    scene.render.use_overwrite = True

scene.render.image_settings.media_type = "IMAGE"
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "8"
scene.render.use_file_extension = True
scene.render.use_placeholder = False

try:
    scene.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def set_socket(node, names, value):
    names = (names,) if isinstance(names, str) else names
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return socket
    return None


def add_box(name, location, dimensions, material, bevel_width=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel_width:
        modifier = obj.modifiers.new("Sanfte Kanten", "BEVEL")
        modifier.width = bevel_width
        modifier.segments = 3
    obj.data.materials.append(material)
    return obj


def add_cylinder(name, location, radius, depth, material, vertices=64):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("Sanfte Kanten", "BEVEL")
    bevel.width = 0.025
    bevel.segments = 3
    return obj


def add_area_light(name, location, energy, size, color, target):
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "RECTANGLE"
    data.size = size
    data.size_y = size * 1.45
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def simple_material(name, color, roughness, metallic=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    set_socket(shader, "Base Color", color)
    set_socket(shader, "Roughness", roughness)
    set_socket(shader, "Metallic", metallic)
    return material


def arch_profile(radius, spring_z, steps=32):
    left = [(-radius, 0.0), (-radius, spring_z)]
    arc = [
        (radius * math.cos(math.pi - math.pi * i / steps),
         spring_z + radius * math.sin(math.pi - math.pi * i / steps))
        for i in range(steps + 1)
    ]
    return left + arc + [(radius, 0.0)]


def add_arch_recess(name, x, y_front, base_z, radius, spring_height, depth,
                    wall_material, recess_material):
    """Tiefe, wirklich räumliche Arkade: Rückfläche plus Laibung bis zur Front."""
    profile = arch_profile(radius, spring_height)
    y_back = y_front + depth
    vertices = []
    for y in (y_front, y_back):
        vertices.extend((x + px, y, base_z + pz) for px, pz in profile)

    n = len(profile)
    faces = []
    # Rückwand in der Form der Öffnung
    faces.append(tuple(range(n, 2 * n)))
    # Laibungsflächen an den beiden Seiten und am Rundbogen; Boden bleibt offen.
    for i in range(n - 1):
        faces.append((i, i + 1, n + i + 1, n + i))

    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(recess_material)

    # Massive Pfeiler und oberes Mauerwerk bilden die reale Öffnung.
    pier_width = 0.62
    add_box(name + "_Pfeiler_L", (x - radius - pier_width / 2, y_front + depth / 2,
                                  base_z + (spring_height + radius) / 2),
            (pier_width, depth, spring_height + radius), wall_material, 0.025)
    add_box(name + "_Pfeiler_R", (x + radius + pier_width / 2, y_front + depth / 2,
                                  base_z + (spring_height + radius) / 2),
            (pier_width, depth, spring_height + radius), wall_material, 0.025)

    # Sichtbarer steinerner Archivoltenring an der Front.
    outer = radius + 0.28
    curve = bpy.data.curves.new(name + "_Archivolte", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.14
    curve.bevel_resolution = 4
    spline = curve.splines.new("POLY")
    points = 48
    spline.points.add(points)
    for i in range(points + 1):
        angle = math.pi - math.pi * i / points
        spline.points[i].co = (
            x + outer * math.cos(angle), y_front - 0.01,
            base_z + spring_height + outer * math.sin(angle), 1.0
        )
    ring = bpy.data.objects.new(name + "_Archivolte", curve)
    bpy.context.collection.objects.link(ring)
    ring.data.materials.append(wall_material)
    return obj


# ============================================================
# MATERIAL: POLIERTER DUNKLER GRANIT, ABER NICHT METALLISCH
# ============================================================

granite = bpy.data.materials.new("Polierter dunkler Naturgranit")
granite.use_nodes = True
nodes = granite.node_tree.nodes
links = granite.node_tree.links
nodes.clear()

output = nodes.new("ShaderNodeOutputMaterial")
bsdf = nodes.new("ShaderNodeBsdfPrincipled")
coord = nodes.new("ShaderNodeTexCoord")
mapping = nodes.new("ShaderNodeMapping")
large = nodes.new("ShaderNodeTexNoise")
medium = nodes.new("ShaderNodeTexNoise")
fine = nodes.new("ShaderNodeTexNoise")
crystals = nodes.new("ShaderNodeTexVoronoi")
base_ramp = nodes.new("ShaderNodeValToRGB")
crystal_ramp = nodes.new("ShaderNodeValToRGB")
mix = nodes.new("ShaderNodeMixRGB")
rough_ramp = nodes.new("ShaderNodeValToRGB")
bump = nodes.new("ShaderNodeBump")

large.noise_dimensions = "3D"
large.inputs["Scale"].default_value = 3.8
large.inputs["Detail"].default_value = 7.0
large.inputs["Roughness"].default_value = 0.72
medium.noise_dimensions = "3D"
medium.inputs["Scale"].default_value = 31.0
medium.inputs["Detail"].default_value = 5.0
fine.noise_dimensions = "3D"
fine.inputs["Scale"].default_value = 145.0
fine.inputs["Detail"].default_value = 2.0
crystals.voronoi_dimensions = "3D"
crystals.distance = "EUCLIDEAN"
crystals.feature = "DISTANCE_TO_EDGE"
crystals.inputs["Scale"].default_value = 46.0

base_ramp.color_ramp.elements[0].position = 0.20
base_ramp.color_ramp.elements[0].color = (0.012, 0.014, 0.016, 1)
middle = base_ramp.color_ramp.elements.new(0.50)
middle.color = (0.050, 0.048, 0.045, 1)
base_ramp.color_ramp.elements[1].position = 0.82
base_ramp.color_ramp.elements[1].color = (0.125, 0.115, 0.100, 1)

crystal_ramp.color_ramp.interpolation = "CONSTANT"
crystal_ramp.color_ramp.elements[0].position = 0.035
crystal_ramp.color_ramp.elements[0].color = (0.48, 0.43, 0.35, 1)
crystal_ramp.color_ramp.elements[1].position = 0.060
crystal_ramp.color_ramp.elements[1].color = (0.035, 0.033, 0.031, 1)
white = crystal_ramp.color_ramp.elements.new(0.018)
white.color = (0.68, 0.66, 0.61, 1)

mix.blend_type = "SCREEN"
mix.inputs[0].default_value = 0.38
rough_ramp.color_ramp.elements[0].color = (0.24, 0.24, 0.24, 1)
rough_ramp.color_ramp.elements[1].color = (0.34, 0.34, 0.34, 1)
bump.inputs["Strength"].default_value = 0.055
bump.inputs["Distance"].default_value = 0.018

set_socket(bsdf, "Metallic", 0.0)
set_socket(bsdf, "IOR", 1.52)
set_socket(bsdf, ["Specular IOR Level", "Specular"], 0.34)
set_socket(bsdf, ["Coat Weight", "Clearcoat"], 0.08)
set_socket(bsdf, ["Coat Roughness", "Clearcoat Roughness"], 0.18)

links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
for texture in (large, medium, fine, crystals):
    links.new(mapping.outputs["Vector"], texture.inputs["Vector"])
links.new(large.outputs["Fac"], base_ramp.inputs["Fac"])
links.new(crystals.outputs["Distance"], crystal_ramp.inputs["Fac"])
links.new(base_ramp.outputs["Color"], mix.inputs[1])
links.new(crystal_ramp.outputs["Color"], mix.inputs[2])
links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
links.new(medium.outputs["Fac"], rough_ramp.inputs["Fac"])
links.new(rough_ramp.outputs["Color"], bsdf.inputs["Roughness"])
links.new(fine.outputs["Fac"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])


# ============================================================
# MATERIALIEN DES MUSEUMS
# ============================================================

# Historischer Materialname bleibt für die späteren Materialzugriffe erhalten.
# Kühler, matter Salbei-/Schieferputz kontrastiert mit den warmen Steinrahmen.
wall_material = simple_material("Warmer Kalkstein", (0.23, 0.32, 0.31, 1), 0.78)
trim_material = simple_material("Heller Naturstein", (0.68, 0.59, 0.47, 1), 0.44)
floor_material = simple_material("Polierter Museumsboden", (0.10, 0.072, 0.048, 1), 0.24)
recess_material = simple_material("Tiefe Arkadennischen", (0.018, 0.013, 0.010, 1), 0.82)
base_material = simple_material("Sockelgranit", (0.022, 0.022, 0.021, 1), 0.30)


# ============================================================
# KUSNER-FLÄCHE p=7 – FUNKTIONIERENDE GEOMETRIE UNVERÄNDERT
# ============================================================

p = P
A = math.sqrt(2 * p - 1)
B = 2 * A / (p - 1)
root_span = math.sqrt(B * B + 4)
inner_pole = ((root_span - B) / 2) ** (1 / p)
outer_pole = ((root_span + B) / 2) ** (1 / p)
margin = min(0.24, (outer_pole - inner_pole) * 0.38)
r1 = inner_pole + margin
r2 = outer_pole - margin
u_segments = 70 + round(p * 4)
v_segments = 361 + round(p * 40)
SEAM_OVERLAP = 0.10
u_count = u_segments + 1
v_count = v_segments + 1


def F(z):
    return 1j * (A * z**p + 1)**2 / (z**(2 * p) + B * z**p - 1)**2


def G(z):
    return z**(p - 1) * (z**p - A) / (A * z**p + 1)


def segment_delta(z0, z1):
    z = (z0 + z1) * 0.5
    dz = z1 - z0
    f = F(z)
    g = G(z)
    x = (f * (1 - g * g) * 0.5 * dz).real
    y = (1j * f * (1 + g * g) * 0.5 * dz).real
    zz = (f * g * dz).real
    return Vector((x, y, zz)) if all(map(math.isfinite, (x, y, zz))) else Vector()


radii = [r1 + (r2 - r1) * i / u_segments for i in range(u_count)]
angles = [(2 * math.pi + SEAM_OVERLAP) * j / v_segments for j in range(v_count)]
grid = [[Vector() for _ in range(u_count)] for _ in range(v_count)]

for i in range(1, u_count):
    grid[0][i] = grid[0][i - 1] + segment_delta(complex(radii[i - 1], 0),
                                                 complex(radii[i], 0))

for j in range(1, v_count):
    e0 = cmath.exp(1j * angles[j - 1])
    e1 = cmath.exp(1j * angles[j])
    for i, radial in enumerate(radii):
        grid[j][i] = grid[j - 1][i] + segment_delta(radial * e0, radial * e1)

all_points = [point for row in grid for point in row]
center = Vector(tuple(sum(getattr(point, axis) for point in all_points) / len(all_points)
                      for axis in ("x", "y", "z")))
centered = [point - center for point in all_points]
normalizing_radius = max(point.length for point in centered)
centered = [point / normalizing_radius for point in centered]

vertices = [
    (point.x * SCULPTURE_SCALE,
     -point.z * SCULPTURE_SCALE,
     point.y * SCULPTURE_SCALE)
    for point in centered
]

faces = []
for j in range(v_count - 1):
    for i in range(u_count - 1):
        a = j * u_count + i
        b = (j + 1) * u_count + i
        faces.append((a, b, b + 1, a + 1))

mesh = bpy.data.meshes.new("Kusner_p7_Mesh")
mesh.from_pydata(vertices, [], faces)
mesh.update()
kusner = bpy.data.objects.new("Kusner p=7", mesh)
bpy.context.collection.objects.link(kusner)
kusner.data.materials.append(granite)
for polygon in mesh.polygons:
    polygon.use_smooth = True

solidify = kusner.modifiers.new("Granitdicke", "SOLIDIFY")
solidify.thickness = THICKNESS
solidify.offset = 0
solidify.use_even_offset = True
bevel = kusner.modifiers.new("Sanfte Kanten", "BEVEL")
bevel.width = 0.012
bevel.segments = 2


# ============================================================
# S41_7_5 – ZWEITE NICHTORIENTIERBARE MINIMALFLÄCHE
# ============================================================

# Dieselbe Weierstrass-Darstellung und derselbe Ringbereich wie in
# https://eb58.github.io/Non-Orientable-Minimal-Surfaces/
S41_M, S41_N = 7, 5
s41_r1, s41_r2 = 1.1, 1.3
s41_u_segments, s41_v_segments = 58, 221
s41_u_count = s41_u_segments + 1
s41_v_count = s41_v_segments + 1


def s41_f(z):
    return 1j * (z**S41_N + 1)**2 / z**(S41_M + 1)


def s41_g(z):
    return z**(S41_M - S41_N) * (z**S41_N - 1) / (z**S41_N + 1)


def s41_segment_delta(z0, z1):
    z = (z0 + z1) * 0.5
    dz = z1 - z0
    f = s41_f(z)
    g = s41_g(z)
    x = (f * (1 - g * g) * 0.5 * dz).real
    y = (1j * f * (1 + g * g) * 0.5 * dz).real
    zz = (f * g * dz).real
    return Vector((x, y, zz)) if all(map(math.isfinite, (x, y, zz))) else Vector()


s41_radii = [s41_r1 + (s41_r2 - s41_r1) * i / s41_u_segments
             for i in range(s41_u_count)]
s41_angles = [(2 * math.pi + SEAM_OVERLAP) * j / s41_v_segments
              for j in range(s41_v_count)]
s41_grid = [[Vector() for _ in range(s41_u_count)] for _ in range(s41_v_count)]

for i in range(1, s41_u_count):
    s41_grid[0][i] = s41_grid[0][i - 1] + s41_segment_delta(
        complex(s41_radii[i - 1], 0), complex(s41_radii[i], 0))

for j in range(1, s41_v_count):
    e0 = cmath.exp(1j * s41_angles[j - 1])
    e1 = cmath.exp(1j * s41_angles[j])
    for i, radial in enumerate(s41_radii):
        s41_grid[j][i] = s41_grid[j - 1][i] + s41_segment_delta(radial * e0, radial * e1)

s41_points = [point for row in s41_grid for point in row]
s41_center = Vector(tuple(sum(getattr(point, axis) for point in s41_points) / len(s41_points)
                           for axis in ("x", "y", "z")))
s41_centered = [point - s41_center for point in s41_points]
s41_radius = max(point.length for point in s41_centered)
s41_centered = [point / s41_radius for point in s41_centered]
s41_vertices = [
    (point.x * SCULPTURE_SCALE, -point.z * SCULPTURE_SCALE, point.y * SCULPTURE_SCALE)
    for point in s41_centered
]
s41_faces = []
for j in range(s41_v_count - 1):
    for i in range(s41_u_count - 1):
        a = j * s41_u_count + i
        b = (j + 1) * s41_u_count + i
        s41_faces.append((a, b, b + 1, a + 1))

s41_mesh = bpy.data.meshes.new("S41_7_5_Mesh")
s41_mesh.from_pydata(s41_vertices, [], s41_faces)
s41_mesh.update()
s41 = bpy.data.objects.new("S41_7_5", s41_mesh)
bpy.context.collection.objects.link(s41)
s41.data.materials.append(granite)
for polygon in s41_mesh.polygons:
    polygon.use_smooth = True

s41_solidify = s41.modifiers.new("Granitdicke", "SOLIDIFY")
s41_solidify.thickness = THICKNESS
s41_solidify.offset = 0
s41_solidify.use_even_offset = True
s41_bevel = s41.modifiers.new("Sanfte Kanten", "BEVEL")
s41_bevel.width = 0.012
s41_bevel.segments = 2


# ============================================================
# SOCKEL UND POSITION
# ============================================================

EXHIBIT_X = 4.4
add_box("Sockel unten", (-EXHIBIT_X, 0, 0.30), (7.2, 4.8, 0.60), base_material, 0.07)
add_box("Sockel oben", (-EXHIBIT_X, 0, 0.68), (6.6, 4.2, 0.16), base_material, 0.04)
add_box("S41 Sockel unten", (EXHIBIT_X, 0, 0.30), (7.2, 4.8, 0.60), base_material, 0.07)
add_box("S41 Sockel oben", (EXHIBIT_X, 0, 0.68), (6.6, 4.2, 0.16), base_material, 0.04)
plinth_top = 0.77
min_z = min(vertex[2] for vertex in vertices)
kusner.location.x = -EXHIBIT_X
kusner.location.z = plinth_top - min_z + 0.03
kusner.rotation_euler.z = math.radians(10)
s41_min_z = min(vertex[2] for vertex in s41_vertices)
s41.location.x = EXHIBIT_X
s41.location.z = plinth_top - s41_min_z + 0.03
s41.rotation_euler.z = math.radians(-10)
sculpture_center_z = max(
    kusner.location.z + (min(v[2] for v in vertices) + max(v[2] for v in vertices)) / 2,
    s41.location.z + (min(v[2] for v in s41_vertices) + max(v[2] for v in s41_vertices)) / 2,
)


# ============================================================
# HÖHERE MUSEUMSHALLE UND TIEFE ARKADEN
# ============================================================

add_box("Museumsboden", (0, 0, -0.13), (36, 38, 0.26), floor_material, 0.015)

# Der Hintergrund liegt weiter entfernt als zuvor.
arcade_front_y = 17.0
arcade_depth = 2.8
hall_height = 13.2
add_box("Rueckwand oben", (0, arcade_front_y + arcade_depth / 2, 11.55),
        (34, arcade_depth, 3.3), wall_material)

for index, x in enumerate((-9.0, -3.0, 3.0, 9.0), 1):
    add_arch_recess(
        f"Tiefe Arkade {index}", x, arcade_front_y, 0.0,
        radius=2.15, spring_height=6.2, depth=arcade_depth,
        wall_material=trim_material, recess_material=recess_material
    )

# Ruhige Seitenwände mit tiefen Fensternischen statt freistehender Kolonnaden.
add_box("Gesims links", (-15.67, 2, 11.15), (0.30, 35, 0.30), trim_material, 0.035)
add_box("Gesims rechts", (15.67, 2, 11.15), (0.30, 35, 0.30), trim_material, 0.035)
add_box("Seitenwand links", (-16.2, 2, hall_height / 2), (0.90, 38, hall_height), wall_material)
add_box("Seitenwand rechts", (16.2, 2, hall_height / 2), (0.90, 38, hall_height), wall_material)


# ============================================================
# RUHIGES, NICHT ÜBERSTRAHLTES FENSTERLICHT
# ============================================================

light_target = (0, 0, sculpture_center_z)
for y in (-8, -2, 4, 10):
    add_area_light("Weiches Fensterlicht", (12.7, y, 6.2), 520, 4.4,
                   (1.0, 0.86, 0.72), light_target)

for y in (-6, 3, 11):
    add_area_light("Kuehles Fuelllicht", (-12.6, y, 5.5), 165, 4.0,
                   (0.72, 0.82, 1.0), light_target)

add_area_light("Grosses Oberlicht", (0, 1, 12.2), 900, 7.0,
               (1.0, 0.92, 0.82), light_target)
add_area_light("Konturlicht", (0, 7.5, 7.0), 650, 5.0,
               (1.0, 0.72, 0.52), light_target)

sun_data = bpy.data.lights.new("Sonne", type="SUN")
sun_data.energy = 0.65
sun_data.angle = math.radians(10)
sun_data.color = (1.0, 0.82, 0.66)
sun = bpy.data.objects.new("Sonne", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(34), math.radians(-25), math.radians(-36))

if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
world_nodes = scene.world.node_tree.nodes
world_links = scene.world.node_tree.links

background = world_nodes.get("Background")
if background is None:
    background = world_nodes.new("ShaderNodeBackground")
    background.name = "Background"

world_output = world_nodes.get("World Output")
if world_output is None:
    world_output = world_nodes.new("ShaderNodeOutputWorld")
    world_output.name = "World Output"

if not background.outputs["Background"].is_linked:
    world_links.new(background.outputs["Background"], world_output.inputs["Surface"])

background.inputs["Color"].default_value = (0.055, 0.040, 0.029, 1)
background.inputs["Strength"].default_value = 0.22


# ============================================================
# KAMERA: BEWÄHRTE PERSPEKTIVE + VORBEREITETER 360°-ORBIT
# ============================================================

bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, sculpture_center_z))
target = bpy.context.object
target.name = "Kamera Ziel"

bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
orbit = bpy.context.object
orbit.name = "Kamera Orbit"

camera_data = bpy.data.cameras.new("Museumskamera")
camera = bpy.data.objects.new("Museumskamera", camera_data)
bpy.context.collection.objects.link(camera)
camera.location = (0, -17.2, sculpture_center_z + 0.20)
camera.data.lens = 50
camera.data.sensor_width = 36
camera.data.dof.use_dof = True
camera.data.dof.focus_object = target
camera.data.dof.aperture_fstop = 8.0

constraint = camera.constraints.new("TRACK_TO")
constraint.target = target
constraint.track_axis = "TRACK_NEGATIVE_Z"
constraint.up_axis = "UP_Y"

camera.parent = orbit
scene.camera = camera

# Frei wählbare Startposition auf der kreisförmigen Kamerafahrt.
start_angle = math.radians(START_ANGLE)
rotation_amount = math.radians(ORBIT_DEGREES)
driver = orbit.driver_add("rotation_euler", 2).driver
driver.type = "SCRIPTED"
driver.expression = (
    f"{start_angle} + {rotation_amount} * "
    f"(frame-{scene.frame_start}) / {scene.frame_end-scene.frame_start}"
)

scene.frame_set(1)
print("KUSNER p=7: TESTBILD BEREIT" if not MAKE_VIDEO else "KUSNER p=7: PNG-BILDFOLGE BEREIT")
print("F12 rendert das Testbild; bei MAKE_VIDEO=True startet Strg+F12 die 360°-Fahrt.")

# MUSEUMSAUSBAU
import bpy, math, sys, runpy, os, json
from mathutils import Vector, Matrix

D, S, C = bpy.data, bpy.context.scene, bpy.context
SCRIPT_DIR = PROJECT_DIR


def obj_by_name(name, *, required=True):
    obj = D.objects.get(name)
    if obj is None and required:
        raise RuntimeError(f"Objekt '{name}' wurde in der Szene nicht gefunden.")
    return obj


def ensure_world():
    if S.world is None:
        S.world = D.worlds.new("World")
    if S.world.node_tree is None:
        S.world.use_nodes = True
    return S.world


def material_by_name(name):
    material = D.materials.get(name)
    if material is None:
        material = D.materials.new(name)
    return material


mat = lambda n: next((m for m in D.materials if m.name == n or m.name.startswith(n + ".")), material_by_name(n))  # Namen tragen in alten Dateien Suffixe (.011)


def link(o, col):
    for c in o.users_collection: c.objects.unlink(o)
    col.objects.link(o)

def box(name, loc, dim, col):
    bpy.ops.mesh.primitive_cube_add(location=loc); o = C.active_object; o.name = name; o.dimensions = dim; link(o, col); return o

def arch(name, loc, r, depth, col):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=r, depth=depth, location=loc, rotation=(0, math.pi / 2, 0)); o = C.active_object; o.name = name; link(o, col); return o

def join(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    C.view_layer.objects.active = objs[0]; bpy.ops.object.join(); return C.active_object


# --- Fenster in beiden Seitenwaenden -------------------------------------------------------
fcol = D.collections.new("Fenster"); S.collection.children.link(fcol)
frame = D.materials.new("Fensterrahmen"); frame.use_nodes = True
b = frame.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.06, 0.045, 0.035, 1); b.inputs["Metallic"].default_value = 0.8; b.inputs["Roughness"].default_value = 0.35

YS, W, Z0, ZA = [-7, -1, 5, 11], 3.2, 2.2, 8.4  # Fenstermitten (zwischen den Saeulen), Breite, Sohle, Bogenansatz
R = W / 2


def window_niche(side, x, y, index):
    """Massive Laibung mit echtem halbkreisförmigem Steinbogen."""
    inward = 1 if side == "L" else -1
    front_x = x + inward * 0.50
    back_x = x - inward * 0.10
    center_x = (front_x + back_x) / 2
    depth = abs(front_x - back_x)
    border = 0.24
    prefix = f"Fensternische {side}{index}"
    for sign in (-1, 1):
        obj = add_box(prefix + f" Laibung {sign}",
                      (center_x, y + sign * (R + border / 2), (Z0 + ZA) / 2),
                      (depth, border, ZA - Z0), trim_material, 0.025)
        link(obj, fcol)
    sill = add_box(prefix + " Fensterbank", (front_x - inward * 0.16, y, Z0 - 0.10),
                   (0.95, W + 2 * border + 0.16, 0.20), trim_material, 0.035)
    link(sill, fcol)
    vertices, faces = [], []
    segments = 48
    for xx in (front_x, back_x):
        for radius in (R, R + border):
            for step in range(segments + 1):
                angle = math.pi * step / segments
                vertices.append((xx, y + radius * math.cos(angle), ZA + radius * math.sin(angle)))
    stride = segments + 1
    for step in range(segments):
        for a, b_ in ((0, stride), (2 * stride, 3 * stride),
                      (0, 2 * stride), (stride, 3 * stride)):
            faces.append((a + step, a + step + 1, b_ + step + 1, b_ + step))
    faces.extend(((0, stride, 3 * stride, 2 * stride),
                  (segments, 2 * stride - 1, 4 * stride - 1, 3 * stride - 1)))
    mesh = D.meshes.new(prefix + " Bogen Mesh")
    mesh.from_pydata(vertices, [], faces); mesh.update()
    obj = D.objects.new(prefix + " Steinbogen", mesh); fcol.objects.link(obj)
    obj.data.materials.append(trim_material)
    bevel = obj.modifiers.new("Weiche Steinkanten", "BEVEL")
    bevel.width = 0.02; bevel.segments = 3


for side, x in (("L", -16.2), ("R", 16.2)):
    cut = []
    for i, y in enumerate(YS):
        cut += [box(f"c{i}", (x, y, (Z0 + ZA) / 2), (1.4, W, ZA - Z0), fcol), arch(f"a{i}", (x, y, ZA), R, 1.4, fcol)]
        f = join([box("p", (x, y, (Z0 + ZA + R) / 2), (0.14, 0.12, ZA + R - Z0), fcol),
                  box("q1", (x, y, Z0 + 2.1), (0.14, W, 0.12), fcol), box("q2", (x, y, Z0 + 4.2), (0.14, W, 0.12), fcol), box("q3", (x, y, ZA), (0.14, W, 0.14), fcol),
                  box("l", (x, y - R + 0.06, (Z0 + ZA) / 2), (0.16, 0.14, ZA - Z0), fcol), box("r", (x, y + R - 0.06, (Z0 + ZA) / 2), (0.16, 0.14, ZA - Z0), fcol),
                  box("s", (x, y, Z0), (0.30, W, 0.14), fcol)])
        f.name = f"Fensterrahmen {side}{i + 1}"; f.data.materials.append(frame)
        bpy.ops.mesh.primitive_torus_add(major_radius=R - 0.05, minor_radius=0.07, major_segments=48, minor_segments=8, location=(x, y, ZA), rotation=(0, math.pi / 2, 0))
        t = C.active_object; t.name = f"Fensterbogen {side}{i + 1}"; t.data.materials.append(frame); link(t, fcol)
        # Rahmen weiter außen, Laibungen öffnen sich zum Innenraum.
        f.location.x -= (1 if side == "L" else -1) * 0.10
        t.location.x -= (1 if side == "L" else -1) * 0.10
        window_niche(side, x, y, i + 1)
    c = join(cut); c.name = f"Fensterschnitt {side}"; c.display_type = 'WIRE'; c.hide_render = True
    wall = obj_by_name("Seitenwand links" if side == "L" else "Seitenwand rechts")
    bm = wall.modifiers.new("Fenster", "BOOLEAN")
    bm.operation, bm.object, bm.solver, bm.use_self = 'DIFFERENCE', c, 'EXACT', True  # use_self: Schnittkoerper ueberlappen sich

# --- Decke, Rueckwand hinter den Arkaden, Vorderwand -----------------------------------------
kalk = mat("Warmer Kalkstein")
for n, loc, dim in (("Decke", (0, 2, 13.45), (32.9, 38, 0.5)), ("Rueckwand hinten", (0, 20.75, 6.6), (32.9, 0.5, 13.2)), ("Vorderwand", (0, -17.25, 6.6), (32.9, 0.5, 13.2))):
    bpy.ops.mesh.primitive_cube_add(location=loc); o = C.active_object; o.name = n; o.dimensions = dim; o.data.materials.append(kalk)

# --- Umlaufende Naturstein-Fußleisten ------------------------------------------------------
# 18 cm hoch, 6 cm vor der Wand; abgerundete Kanten als ruhiger Bodenabschluss.
skirting_material = simple_material("Fussleisten Naturstein", (0.48, 0.43, 0.35, 1), 0.62)
skirting_collection = D.collections.new("Fussleisten")
S.collection.children.link(skirting_collection)
for name, location, dimensions in (
        ("Fussleiste links", (-15.72, 1.75, 0.09), (0.06, 37.5, 0.18)),
        ("Fussleiste rechts", (15.72, 1.75, 0.09), (0.06, 37.5, 0.18)),
        ("Fussleiste Vorderwand", (0, -16.97, 0.09), (31.38, 0.06, 0.18)),
        ("Fussleiste Rueckwand", (0, 20.47, 0.09), (31.38, 0.06, 0.18))):
    skirting = add_box(name, location, dimensions, skirting_material, 0.008)
    link(skirting, skirting_collection)

# --- Himmel: fuer die Kamera hell (Strength 1.9), als Beleuchtung gedaempft (0.7) ---------------
ensure_world()
nt = S.world.node_tree; nt.nodes.clear()
out, bg, sky, lp, mul = (nt.nodes.new(t) for t in ("ShaderNodeOutputWorld", "ShaderNodeBackground", "ShaderNodeTexSky", "ShaderNodeLightPath", "ShaderNodeMath"))
sky.sky_type = 'MULTIPLE_SCATTERING' if 'MULTIPLE_SCATTERING' in sky.bl_rna.properties['sky_type'].enum_items else 'NISHITA'
sky.sun_disc, sky.sun_elevation, sky.sun_rotation = False, math.radians(38), math.radians(90)
mul.operation = 'MULTIPLY_ADD'; mul.inputs[1].default_value = 1.6; mul.inputs[2].default_value = 0.4
for a, b_ in ((lp.outputs["Is Camera Ray"], mul.inputs[0]), (sky.outputs[0], bg.inputs["Color"]), (mul.outputs[0], bg.inputs["Strength"]), (bg.outputs[0], out.inputs[0])): nt.links.new(a, b_)

# --- Sonne flach durch die +X-Fenster, alte Flaechenlichter dimmen ---------------------------
sun = obj_by_name("Sonne")
sun.rotation_euler = Vector((-0.8, 0.22, -0.56)).normalized().to_track_quat('-Z', 'Y').to_euler()
# Zurückhaltendes Tageslicht: weniger direkte Energie, weichere Schatten.
sun.data.energy = 5.5
sun.data.angle = math.radians(3.0)
for o in D.objects:
    if o.type == 'LIGHT' and o.name != "Sonne": o.data.energy *= 0.35

# --- Boden: polierter Marmor mit Schachbrett oder Parkett (BODEN) ----------------------------- ---------------------------------
nt = mat("Polierter Museumsboden").node_tree; N, L = nt.nodes, nt.links; p = N["Principled BSDF"]
tc, ck, nz, mix, rr = (N.new(t) for t in ("ShaderNodeTexCoord", "ShaderNodeTexChecker", "ShaderNodeTexNoise", "ShaderNodeMix", "ShaderNodeMapRange"))
ck.inputs["Scale"].default_value = 11; ck.inputs["Color1"].default_value = (0.82, 0.76, 0.66, 1); ck.inputs["Color2"].default_value = (0.66, 0.60, 0.51, 1)
nz.inputs["Scale"].default_value = 6; nz.inputs["Detail"].default_value = 12; nz.inputs["Roughness"].default_value = 0.6
mix.data_type, mix.blend_type = 'RGBA', 'MULTIPLY'; mix.inputs["Factor"].default_value = 0.6
rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = 0.06, 0.16
for a, b_ in ((tc.outputs["Generated"], ck.inputs["Vector"]), (tc.outputs["Generated"], nz.inputs["Vector"]), (ck.outputs["Color"], mix.inputs["A"]), (nz.outputs["Color"], mix.inputs["B"]),
              (mix.outputs["Result"], p.inputs["Base Color"]), (nz.outputs["Fac"], rr.inputs["Value"]), (rr.outputs["Result"], p.inputs["Roughness"])): L.new(a, b_)
p.inputs["Coat Weight"].default_value = 0.6; p.inputs["Coat Roughness"].default_value = 0.03
if BODEN == "parkett":  # Dielen im Halbverband: Brick-Textur, pro Diele leicht anderer Ton, Maserung quer zur Dielenlaenge
    bk, wv2, gm2 = (N.new(t) for t in ("ShaderNodeTexBrick", "ShaderNodeTexWave", "ShaderNodeMix"))
    bk.offset, bk.offset_frequency, bk.squash = 0.5, 2, 1.0
    for k, v in (("Scale", 30), ("Color1", (0.60, 0.38, 0.19, 1)), ("Color2", (0.42, 0.25, 0.12, 1)), ("Mortar", (0.05, 0.03, 0.02, 1)), ("Mortar Size", 0.006), ("Mortar Smooth", 0.1), ("Brick Width", 1.0), ("Row Height", 0.12)): bk.inputs[k].default_value = v
    wv2.wave_type, wv2.bands_direction = 'BANDS', 'Y'
    for k, v in (("Scale", 250), ("Distortion", 3.0), ("Detail", 3.0), ("Detail Scale", 3.0), ("Detail Roughness", 0.6)): wv2.inputs[k].default_value = v
    gm2.data_type, gm2.blend_type = 'RGBA', 'MULTIPLY'; gm2.inputs["Factor"].default_value = 0.45
    mix.inputs["Factor"].default_value = 0.25; rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = 0.2, 0.32; p.inputs["Coat Weight"].default_value = 0.3
    for a, b_ in ((tc.outputs["Generated"], bk.inputs["Vector"]), (tc.outputs["Generated"], wv2.inputs["Vector"]), (bk.outputs["Color"], gm2.inputs["A"]), (wv2.outputs["Color"], gm2.inputs["B"]), (gm2.outputs["Result"], mix.inputs["A"])): L.new(a, b_)

# Fischgrät als gemeinsame Bildtextur für Cycles und glTF/Three.js.
if BODEN == "parkett":
    size, plank_units = 512, 5
    period = 2 * plank_units
    parquet_image = D.images.new("Fischgraet Eiche", width=size, height=size)
    pixels = []
    for yy in range(size):
        for xx in range(size):
            u, v = xx / size * period, yy / size * period
            ix, iy = math.floor(u), math.floor(v)
            difference = (ix - iy) % period
            horizontal = difference < plank_units
            if horizontal:
                along, across = difference + u % 1, v % 1
                anchor_x, anchor_y = ix - difference, iy
            else:
                along, across = period - 1 - difference + v % 1, u % 1
                anchor_x, anchor_y = ix, iy - (period - 1 - difference)
            tone = math.sin(anchor_x * 127.1 + anchor_y * 311.7) * 0.09
            grain = 0.028 * math.sin(across * 110 + math.sin(along * 2.8) * 3)
            edge = min(across, 1 - across, along, plank_units - along)
            shade = 0.42 if edge < 0.022 else 1.0
            pixels.extend(((0.48 + tone + grain) * shade,
                           (0.29 + tone * 0.65 + grain) * shade,
                           (0.13 + tone * 0.35 + grain * 0.5) * shade, 1.0))
    parquet_image.pixels.foreach_set(pixels)
    parquet_image.pack()
    texture = N.new("ShaderNodeTexImage"); texture.image = parquet_image
    texture.extension = 'REPEAT'
    L.new(texture.outputs["Color"], p.inputs["Base Color"])
    for socket in (p.inputs["Roughness"],):
        for connection in list(socket.links): L.remove(connection)
    p.inputs["Roughness"].default_value = 0.30
    p.inputs["Coat Weight"].default_value = 0.25
    # 18 cm breite, 90 cm lange Stäbe, diagonal zur Raumachse verlegt.
    floor_obj = obj_by_name("Museumsboden")
    uv_layer = floor_obj.data.uv_layers.new(name="Fischgraet UV")
    uv_layer.active_render = True
    uv_node = N.new("ShaderNodeUVMap"); uv_node.uv_map = uv_layer.name
    L.new(uv_node.outputs["UV"], texture.inputs["Vector"])
    for polygon in floor_obj.data.polygons:
        for loop_index in polygon.loop_indices:
            vertex = floor_obj.matrix_world @ floor_obj.data.vertices[floor_obj.data.loops[loop_index].vertex_index].co
            uv_layer.data[loop_index].uv = ((vertex.x + vertex.y) / (math.sqrt(2) * 1.8),
                                            (vertex.y - vertex.x) / (math.sqrt(2) * 1.8))

# --- Material-Import fuer prozedurale Materialien (z. B. granit_material.json) ----------------
def load_nodes(nt, spec):
    if spec["interface"]:
        for i in spec["interface"]:
            s = nt.interface.new_socket(i["name"], in_out=i["in_out"], socket_type=i["socket_type"])
            for k, a in (("default", "default_value"), ("min_value", "min_value"), ("max_value", "max_value")):
                if k in i: setattr(s, a, i[k])
    nt.nodes.clear(); ns = {}
    for d in spec["nodes"]:
        n = nt.nodes.new(d["idname"]); n.name = d["name"]; n.location = d["loc"]; ns[d["name"]] = n
        for k, v in d["props"].items():
            try: setattr(n, k, v)
            except (AttributeError, TypeError, ValueError): pass
        if "group" in d: g = D.node_groups.new(d["group"]["name"], "ShaderNodeTree"); load_nodes(g, d["group"]); n.node_tree = g
        for k, v in d["in"].items():
            try: n.inputs[int(k)].default_value = v
            except (TypeError, ValueError, IndexError): pass
        if "ramp" in d:
            r = n.color_ramp; r.interpolation, r.color_mode = d["ramp"]["interp"], d["ramp"]["mode"]
            for j, (pos, col) in enumerate(d["ramp"]["els"]):
                e = r.elements[j] if j < len(r.elements) else r.elements.new(pos); e.position, e.color = pos, col
    for d in spec["nodes"]:
        if d["parent"]: ns[d["name"]].parent = ns[d["parent"]]
    for fn, fi, tn, ti in spec["links"]: nt.links.new(ns[fn].outputs[fi], ns[tn].inputs[ti])

# --- Skulptur: prozeduraler Naturgranit -----------------------------------------------------
granite = material_by_name("Polierter dunkler Naturgranit")
granite.use_nodes = True
load_nodes(granite.node_tree, GRANITE_SPEC)

# Naturstein bleibt auch in verschachtelten Node-Gruppen nichtmetallisch.
def make_nonmetallic(node_tree):
    for node in node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            node.inputs["Metallic"].default_value = 0.0
            for incoming in list(node.inputs["Metallic"].links):
                node_tree.links.remove(incoming)
        elif node.type == 'GROUP' and node.node_tree is not None:
            make_nonmetallic(node.node_tree)

make_nonmetallic(granite.node_tree)
sculpture = obj_by_name("Kusner p=7")
sculpture.data.materials.clear()
sculpture.data.materials.append(granite)

# --- Weisser Marmor (Sockel der Skulptur, Statuen) ---------------------------------------------
import bmesh
mm = D.materials.new("Weisser Marmor"); mm.use_nodes = True; N, L = mm.node_tree.nodes, mm.node_tree.links; p = N["Principled BSDF"]
tc, mp, wv, ramp = N.new("ShaderNodeTexCoord"), N.new("ShaderNodeMapping"), N.new("ShaderNodeTexWave"), N.new("ShaderNodeValToRGB")
mp.inputs["Scale"].default_value = (0.5, 0.5, 0.5); wv.wave_type, wv.bands_direction = 'BANDS', 'DIAGONAL'
for k, v in (("Scale", 0.9), ("Distortion", 6.0), ("Detail", 8.0), ("Detail Scale", 1.2), ("Detail Roughness", 0.65)): wv.inputs[k].default_value = v
ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.0, (0.55, 0.52, 0.49, 1)
ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.035, (0.88, 0.86, 0.81, 1)
e = ramp.color_ramp.elements.new(0.965); e.color = (0.88, 0.86, 0.81, 1); e = ramp.color_ramp.elements.new(1.0); e.color = (0.55, 0.52, 0.49, 1)
p.inputs["Roughness"].default_value = 0.18; p.inputs["Coat Weight"].default_value = 0.25
for a, b_ in ((tc.outputs["Object"], mp.inputs["Vector"]), (mp.outputs["Vector"], wv.inputs["Vector"]), (wv.outputs["Color"], ramp.inputs["Fac"]), (ramp.outputs["Color"], p.inputs["Base Color"])): L.new(a, b_)
# Ruhiger, geschliffener Kalkstein für die beiden Hauptsockel. Er hebt die
# dunklen Granitflächen ab, ohne mit starken Marmoradern zu konkurrieren.
plinth_stone = D.materials.new("Geschliffener Elfenbein-Kalkstein")
plinth_stone.use_nodes = True
pn, pl = plinth_stone.node_tree.nodes, plinth_stone.node_tree.links
pbsdf = pn["Principled BSDF"]
ptc = pn.new("ShaderNodeTexCoord")
pnoise = pn.new("ShaderNodeTexNoise")
pdetail = pn.new("ShaderNodeTexNoise")
pramp = pn.new("ShaderNodeValToRGB")
prough = pn.new("ShaderNodeMapRange")
pbump = pn.new("ShaderNodeBump")
pnoise.noise_dimensions = '3D'
pnoise.inputs["Scale"].default_value = 2.6
pnoise.inputs["Detail"].default_value = 7.0
pnoise.inputs["Roughness"].default_value = 0.62
pdetail.noise_dimensions = '3D'
pdetail.inputs["Scale"].default_value = 135.0
pdetail.inputs["Detail"].default_value = 3.0
pdetail.inputs["Roughness"].default_value = 0.68
pramp.color_ramp.elements[0].position = 0.22
pramp.color_ramp.elements[0].color = (0.25, 0.17, 0.095, 1)
pramp.color_ramp.elements[1].position = 0.78
pramp.color_ramp.elements[1].color = (0.58, 0.45, 0.28, 1)
mid = pramp.color_ramp.elements.new(0.50)
mid.color = (0.42, 0.31, 0.18, 1)
prough.inputs["To Min"].default_value = 0.46
prough.inputs["To Max"].default_value = 0.68
pbump.inputs["Strength"].default_value = 0.28
pbump.inputs["Distance"].default_value = 0.035
pbsdf.inputs["Roughness"].default_value = 0.56
pbsdf.inputs["Coat Weight"].default_value = 0.04
for source, target in (
        (ptc.outputs["Generated"], pnoise.inputs["Vector"]),
        (ptc.outputs["Generated"], pdetail.inputs["Vector"]),
        (pnoise.outputs["Fac"], pramp.inputs["Fac"]),
        (pramp.outputs["Color"], pbsdf.inputs["Base Color"]),
        (pnoise.outputs["Fac"], prough.inputs["Value"]),
        (prough.outputs["Result"], pbsdf.inputs["Roughness"]),
        (pdetail.outputs["Fac"], pbump.inputs["Height"]),
        (pbump.outputs["Normal"], pbsdf.inputs["Normal"])):
    pl.new(source, target)

for n in ("Sockel unten", "Sockel oben", "S41 Sockel unten", "S41 Sockel oben"):
    D.objects[n].material_slots[0].material = plinth_stone

# --- Statuen in den Arkadennischen: Drehprofil (Gewand, Rumpf, Kopf) + Arme, auf Marmorsockel ---
scol = D.collections.new("Statuen"); S.collection.children.link(scol)
PROFIL = [(0, 0), (.34, 0), (.36, .05), (.31, .5), (.27, .9), (.21, 1.15), (.24, 1.3), (.26, 1.42), (.27, 1.5), (.13, 1.58), (.075, 1.62), (.085, 1.67), (.11, 1.75), (.09, 1.84), (0, 1.87)]
def statue(i, x, y, h, arm_up):
    bm = bmesh.new(); vs = [bm.verts.new((r, 0, z)) for r, z in PROFIL]; es = [bm.edges.new((vs[j], vs[j + 1])) for j in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=2 * math.pi, steps=32, use_merge=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for j, (sx, up) in enumerate(((-1, False), (1, arm_up))):  # Arme als schlanke Kegel, einer erhoben
        a = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.06, radius2=0.04, depth=0.75, matrix=Matrix.Translation((0, 0, -0.375)))
        rot = Matrix.Rotation(math.radians(sx * (150 if up else 18)), 4, 'Y')
        bmesh.ops.transform(bm, verts=a["verts"], matrix=Matrix.Translation((sx * 0.29, 0, 1.47)) @ rot)
    me = D.meshes.new(f"Statue {i}"); bm.to_mesh(me); bm.free()
    o = D.objects.new(f"Statue {i}", me); scol.objects.link(o); o.location = (x, y, h); o.scale = (1.5, 1.5, 1.5); o.rotation_euler.z = math.radians((-1) ** i * 12)
    for pl in me.polygons: pl.use_smooth = True
    sm = o.modifiers.new("Glatt", "SUBSURF"); sm.levels = sm.render_levels = 1; me.materials.append(mm)
    sk = box(f"Statuensockel {i}", (x, y, h / 2), (1.5, 1.5, h), scol); sk.data.materials.append(mm)
    sp = D.lights.new(f"Statuenlicht {i}", "SPOT"); sp.energy, sp.spot_size, sp.spot_blend, sp.color, sp.shadow_soft_size = 900, math.radians(38), 0.6, (1.0, 0.86, 0.68), 0.3
    so = D.objects.new(f"Statuenlicht {i}", sp); scol.objects.link(so); so.location = (x, y - 4.5, 8.5); so.rotation_euler = (Vector((0, 4.5, -8.5 + h + 1.4)).to_track_quat('-Z', 'Y')).to_euler()
    kp = box(f"Statuensockel Deckplatte {i}", (x, y, h + 0.06), (1.7, 1.7, 0.12), scol); kp.data.materials.append(mm)
for i, x in enumerate((-9, -3, 3, 9)):
    statue(i, x, 18.2, 1.1, arm_up=i % 2 == 0)
    al = D.lights.new(f"Nischenlicht {i}", "AREA"); al.energy, al.size, al.color = 350, 2.5, (1.0, 0.85, 0.66)
    ao = D.objects.new(f"Nischenlicht {i}", al); scol.objects.link(ao); ao.location = (x, 18.0, 9.5)  # zeigt nach unten (Standard)
mat("Tiefe Arkadennischen").node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.16, 0.23, 0.22, 1)

# --- Echte Marmorbueste (Poly Haven "Marble Bust 01", CC0) statt der Platzhalter-Figuren -------------
BUSTE = os.path.join(PROJECT_DIR, "assets", "models", "marble_bust_01")
if os.path.exists(os.path.join(BUSTE, "marble_bust_01.blend")):
    with D.libraries.load(os.path.join(BUSTE, "marble_bust_01.blend"), link=False) as (src, dst): dst.objects = list(src.objects)
    for im in D.images:
        if "marble_bust_01" in im.name: im.filepath = os.path.join(BUSTE, "textures", os.path.basename(im.filepath)); im.reload()
    base = dst.objects[0]; BS = 3.4; zmin = min(v[2] for v in base.bound_box) * BS
    for i, x in enumerate((-9, -3, 3, 9)):
        D.objects.remove(D.objects[f"Statue {i}"])
        o = base if i == 0 else base.copy(); scol.objects.link(o)
        o.scale = (BS,) * 3; o.location = (x, 18.2, 1.1 + 0.12 - zmin); o.rotation_euler = (0, 0, math.radians((-1) ** i * 9))

# --- Gestaltbare, geschlossene Museumswand gegenüber den Arkaden ----------------------------
gcol = D.collections.new("Wandgestaltung"); S.collection.children.link(gcol)
WALL_Y = -16.96  # Innenseite der Vorderwand; sichtbar in der zweiten Hälfte des Orbits.


def wall_material(name, color, roughness=0.4, metallic=0.0):
    material = D.materials.new(name); material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return material


anthracite = wall_material("Wandtafel Anthrazit", (0.012, 0.016, 0.015, 1), 0.38)
brass = wall_material("Wandtafel Messing", (0.72, 0.43, 0.12, 1), 0.22, 0.9)
relief_stone = wall_material("Relief Naturstein", (0.70, 0.61, 0.47, 1), 0.48)
parchment = wall_material("Historisches Pergament", (0.42, 0.25, 0.11, 1), 0.62)


def wall_box(name, x, z, width, height, depth, material, y=WALL_Y):
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z))
    obj = C.active_object; obj.name = name; obj.dimensions = (width, depth, height)
    obj.data.materials.append(material); link(obj, gcol)
    return obj


def wall_text(name, body, x, z, size, material, y=WALL_Y + 0.09):
    curve = D.curves.new(name, "FONT"); curve.body = body
    curve.align_x = 'CENTER'; curve.align_y = 'CENTER'; curve.size = size
    curve.extrude = 0.008; curve.bevel_depth = 0.002; curve.materials.append(material)
    obj = D.objects.new(name, curve); gcol.objects.link(obj)
    obj.location = (x, y, z)
    obj.rotation_euler.x = math.radians(90)
    obj.scale.x = -1
    obj.scale.z = -1
    return obj


def wall_frame(name, x, z, width, height, material=brass):
    for index, (dx, dz, w, h) in enumerate(((0, height / 2, width, 0.06),
                                             (0, -height / 2, width, 0.06),
                                             (-width / 2, 0, 0.06, height),
                                             (width / 2, 0, 0.06, height))):
        wall_box(f"{name} {index}", x + dx, z + dz, w, h, 0.05, material, WALL_Y + 0.07)


def wall_ring(name, x, z, radius, material, scale_x=1.0, scale_z=1.0):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=0.055,
                                    major_segments=64, minor_segments=8,
                                    location=(x, WALL_Y + 0.11, z), rotation=(math.pi / 2, 0, 0))
    obj = C.active_object; obj.name = name; obj.scale = (scale_x, scale_z, 1)
    obj.data.materials.append(material); link(obj, gcol)
    return obj


if WANDGESTALTUNG == "mathe_tafeln":
    for index, (x, title, subtitle) in enumerate((
            (-5.1, "WEIERSTRASS", "X(z) = Re integral Phi"),
            (0.0, "PARAMETERLINIEN", "u = |z|     v = arg(z)"),
            (5.1, "MINIMALFLAECHEN", "KUSNER p=7     S41_7_5")), 1):
        wall_box(f"Mathematiktafel {index}", x, 8.9, 4.45, 2.25, 0.13, anthracite)
        wall_frame(f"Tafelrahmen {index}", x, 8.9, 4.55, 2.35)
        wall_text(f"Tafeltitel {index}", title, x, 9.35, 0.28, brass)
        wall_box(f"Tafeltrennlinie {index}", x, 8.95, 3.7, 0.025, 0.04, brass, WALL_Y + 0.09)
        wall_text(f"Tafeltext {index}", subtitle, x, 8.48, 0.20, brass)

elif WANDGESTALTUNG == "steinreliefs":
    for index, x in enumerate((-5.2, 0, 5.2), 1):
        wall_box(f"Reliefplatte {index}", x, 8.5, 4.4, 4.4, 0.18, trim_material)
        wall_ring(f"Reliefring {index}a", x, 8.5, 1.35, relief_stone, 1.0, 0.72)
        wall_ring(f"Reliefring {index}b", x, 8.5, 1.05, relief_stone, 0.62, 1.0)
        wall_ring(f"Reliefring {index}c", x, 8.5, 0.72, brass, 1.15, 0.55)

elif WANDGESTALTUNG == "historische_tafel":
    wall_box("Historische Mathematiktafel", 0, 8.4, 13.2, 5.2, 0.16, parchment)
    wall_frame("Historischer Rahmen", 0, 8.4, 13.35, 5.35, relief_stone)
    wall_text("Historischer Titel", "THEORIA SUPERFICIERUM MINIMALIUM", 0, 10.05, 0.43, relief_stone)
    wall_text("Historische Formel 1", "Phi = ( f(1-g^2)/2,  i f(1+g^2)/2,  f g ) dz", 0, 8.75, 0.30, relief_stone)
    wall_text("Historische Formel 2", "X(z) = Re integral Phi", 0, 7.65, 0.38, relief_stone)
    wall_text("Historische Signatur", "Kusner p=7   |   S41 m=7 n=5", 0, 6.65, 0.24, relief_stone)

elif WANDGESTALTUNG == "flaechen_triptychon":
    for index, x in enumerate((-5.1, 0, 5.1), 1):
        wall_box(f"Triptychon {index}", x, 8.6, 4.35, 4.9, 0.15, anthracite)
        wall_frame(f"Triptychonrahmen {index}", x, 8.6, 4.48, 5.03)
        for ring_index, (dx, dz, radius, sx, sz) in enumerate((
                (0, 0.45, 1.25, 1.0, 0.55), (-0.55, -0.45, 0.82, 0.65, 1.0),
                (0.65, -0.38, 0.72, 1.0, 0.7))):
            wall_ring(f"Flaechenlinie {index}-{ring_index}", x + dx, 8.6 + dz,
                      radius, brass, sx, sz)
        wall_text(f"Triptychontext {index}", ("KRÜMMUNG", "TOPOLOGIE", "SYMMETRIE")[index - 1],
                  x, 6.75, 0.24, brass)

elif WANDGESTALTUNG == "messing_formeln":
    wall_text("Messing Formel 1", "X(z) = Re integral Phi", 0, 10.2, 0.72, brass)
    wall_text("Messing Formel 2", "f(z) = i (z^5 + 1)^2 / z^8", 0, 8.55, 0.58, brass)
    wall_text("Messing Formel 3", "g(z) = z^2 (z^5 - 1) / (z^5 + 1)", 0, 7.05, 0.48, brass)
    wall_box("Messing Horizont", 0, 5.95, 13.0, 0.045, 0.05, brass, WALL_Y + 0.08)

elif WANDGESTALTUNG == "digitales_panel":
    digital = D.materials.new("Digitales Leuchten"); digital.use_nodes = True
    nodes = digital.node_tree.nodes; links = digital.node_tree.links; nodes.clear()
    emission = nodes.new("ShaderNodeEmission"); output = nodes.new("ShaderNodeOutputMaterial")
    emission.inputs["Color"].default_value = (0.05, 0.55, 0.80, 1); emission.inputs["Strength"].default_value = 4.0
    links.new(emission.outputs[0], output.inputs[0])
    wall_box("Digitalwand", 0, 8.5, 14.0, 5.6, 0.14, anthracite)
    wall_frame("Digitalrahmen", 0, 8.5, 14.15, 5.75, brass)
    for index, (x, z, radius, sx, sz) in enumerate(((-4.2, 8.7, 1.55, 1, .65),
                                                    (0, 8.7, 1.65, .7, 1),
                                                    (4.2, 8.7, 1.55, 1, .65)), 1):
        wall_ring(f"Digitale Minimalflaeche {index}", x, z, radius, digital, sx, sz)
    wall_text("Digitaltitel", "NON-ORIENTABLE MINIMAL SURFACES", 0, 6.35, 0.32, digital)

elif WANDGESTALTUNG == "wandteppich":
    textile = D.materials.new("Mandelbrot Wandteppich"); textile.use_nodes = True
    nodes = textile.node_tree.nodes; links = textile.node_tree.links; nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    image_node = nodes.new("ShaderNodeTexImage")
    grayscale = nodes.new("ShaderNodeRGBToBW")
    bump = nodes.new("ShaderNodeBump")
    image_path = os.path.join(PROJECT_DIR, "Assets", "mandelbrot_tapestry.png")
    image_node.image = D.images.load(image_path, check_existing=True)
    image_node.interpolation = 'Linear'
    shader.inputs["Roughness"].default_value = 0.68
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.025
    links.new(image_node.outputs["Color"], shader.inputs["Base Color"])
    links.new(image_node.outputs["Color"], grayscale.inputs["Color"])
    links.new(grayscale.outputs["Val"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    # Größer als die frühere Variante und deutlich tiefer an der Wand.
    tapestry_center_z = hall_height / 2
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, WALL_Y + 0.10, tapestry_center_z),
                                    rotation=(math.pi / 2, 0, 0))
    tapestry = C.active_object; tapestry.name = "Mandelbrot Wandteppich"
    tapestry.scale = (-7.4, 3.3, 1)  # negative X gleicht die Betrachtung der Rückseite aus
    tapestry.data.materials.append(textile); link(tapestry, gcol)
    solidify = tapestry.modifiers.new("Gewebedicke", "SOLIDIFY"); solidify.thickness = 0.055
    bevel = tapestry.modifiers.new("Weicher Teppichrand", "BEVEL"); bevel.width = 0.035; bevel.segments = 3
    wall_frame("Teppichsaum", 0, tapestry_center_z, 14.95, 6.75, brass)
    for x in (-6.8, -5.8, -4.8, -3.8, -2.8, -1.8, -0.8, 0.2, 1.2, 2.2, 3.2, 4.2, 5.2, 6.2):
        wall_box("Teppichfranse", x, tapestry_center_z - 3.57, 0.04, 0.38, 0.03, brass, WALL_Y + 0.11)

# Warmes, flaches Museumslicht für den Wandteppich.
for index, x in enumerate((-5.5, 0, 5.5), 1):
    lamp_data = D.lights.new(f"Wandlicht {index}", "AREA")
    lamp_data.energy = 220; lamp_data.shape = 'RECTANGLE'; lamp_data.size = 3.2
    lamp_data.size_y = 0.4; lamp_data.color = (1.0, 0.72, 0.42)
    lamp = D.objects.new(f"Wandlicht {index}", lamp_data); gcol.objects.link(lamp)
    lamp.location = (x, -14.8, 11.8)
    lamp.rotation_euler = Vector((0, -2.2, -3.0)).to_track_quat('-Z', 'Y').to_euler()

# --- Kassettendecke: Balkenraster unter der Decke, kleiner Rahmen in jedem Feld, Oberlicht in der Mitte --------
ccol = D.collections.new("Kassettendecke"); S.collection.children.link(ccol)
NX, NY, X0, Y0, DX, DY, ZD = 10, 10, -16.45, -17.0, 3.29, 3.8, 13.2  # Felder, Ursprung, Feldgroesse, Unterkante der Decke
bm = bmesh.new()
def bx(c, sz): bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*sz, 1)))
for i in range(NX + 1): bx((X0 + i * DX, Y0 + NY * DY / 2, ZD - 0.2), (0.32, NY * DY, 0.4))   # Balken laengs
for j in range(NY + 1): bx((0, Y0 + j * DY, ZD - 0.2), (NX * DX, 0.32, 0.4))                   # Balken quer
SKY = {(i, j) for i in (4, 5) for j in (4, 5)}                                                  # Felder des Oberlichts
for i in range(NX):
    for j in range(NY):
        if (i, j) in SKY: continue
        cx, cy = X0 + (i + .5) * DX, Y0 + (j + .5) * DY; fx, fy = DX - 1.1, DY - 1.1
        for dx, dy, sx, sy in ((0, fy / 2, fx, .12), (0, -fy / 2, fx, .12), (fx / 2, 0, .12, fy), (-fx / 2, 0, .12, fy)): bx((cx + dx, cy + dy, ZD - 0.075), (sx, sy, 0.15))
        bx((cx, cy, ZD - 0.05), (0.5, 0.5, 0.1))
ceiling_wood = simple_material("Kassettendecke Eichenholz", (0.23, 0.105, 0.038, 1), 0.48)
wood_nodes = ceiling_wood.node_tree.nodes; wood_links = ceiling_wood.node_tree.links
wood_coords = wood_nodes.new("ShaderNodeTexCoord")
wood_mapping = wood_nodes.new("ShaderNodeMapping")
wood_mapping.inputs["Scale"].default_value = (0.8, 24, 24)
wood_noise = wood_nodes.new("ShaderNodeTexNoise")
wood_noise.inputs["Scale"].default_value = 3.0
wood_noise.inputs["Detail"].default_value = 3.0
wood_ramp = wood_nodes.new("ShaderNodeValToRGB")
wood_ramp.color_ramp.elements[0].color = (0.075, 0.026, 0.009, 1)
wood_ramp.color_ramp.elements[1].color = (0.32, 0.17, 0.067, 1)
wood_shader = wood_nodes["Principled BSDF"]
wood_links.new(wood_coords.outputs["Object"], wood_mapping.inputs["Vector"])
wood_links.new(wood_mapping.outputs["Vector"], wood_noise.inputs["Vector"])
wood_links.new(wood_noise.outputs["Fac"], wood_ramp.inputs["Fac"])
wood_links.new(wood_ramp.outputs["Color"], wood_shader.inputs["Base Color"])
wood_bump = wood_nodes.new("ShaderNodeBump")
wood_bump.inputs["Strength"].default_value = 0.12
wood_bump.inputs["Distance"].default_value = 0.008
wood_links.new(wood_noise.outputs["Fac"], wood_bump.inputs["Height"])
wood_links.new(wood_bump.outputs["Normal"], wood_shader.inputs["Normal"])
me = D.meshes.new("Kassettendecke"); bm.to_mesh(me); bm.free(); ko = D.objects.new("Kassettendecke", me); ccol.objects.link(ko); me.materials.append(ceiling_wood)
# Auch der Hintergrund der Kassetten erhält dieselbe Holzoberfläche.
obj_by_name("Decke").data.materials.clear()
obj_by_name("Decke").data.materials.append(ceiling_wood)

# Fensterbänke aus Eiche statt Stein; Maserung längs der Fensterbreite (Y).
sill_wood = ceiling_wood.copy()
sill_wood.name = "Fensterbank Eichenholz"
sill_wood.node_tree.nodes.get(wood_mapping.name).inputs["Scale"].default_value = (24, 0.8, 24)
for obj in fcol.objects:
    if obj.type == 'MESH' and "Fensterbank" in obj.name:
        obj.data.materials.clear()
        obj.data.materials.append(sill_wood)
sw, sh = 2 * DX - 0.32, 2 * DY - 0.32
bpy.ops.mesh.primitive_plane_add(size=1, location=(X0 + 5 * DX, Y0 + 5 * DY, ZD - 0.02), rotation=(math.pi, 0, 0)); sk = C.active_object; sk.name = "Oberlicht"; sk.scale = (sw, sh, 1); link(sk, ccol)
om = D.materials.new("Oberlicht"); om.use_nodes = True; onm = om.node_tree; onm.nodes.clear(); em, oo = onm.nodes.new("ShaderNodeEmission"), onm.nodes.new("ShaderNodeOutputMaterial")
em.inputs["Color"].default_value, em.inputs["Strength"].default_value = (1.0, 0.94, 0.82, 1), 7.0; onm.links.new(em.outputs[0], oo.inputs[0]); sk.data.materials.append(om)

# --- Eigener Entwurf: cognacfarbene Lederpolster auf dunklen Stahlkufen --------------------
bcol = D.collections.new("Bank"); S.collection.children.link(bcol)
leather = simple_material("Museumsbank Cognac Leder", (0.28, 0.095, 0.028, 1), 0.48)
nodes, links = leather.node_tree.nodes, leather.node_tree.links
grain = nodes.new('ShaderNodeTexNoise')
grain.inputs['Scale'].default_value = 230
grain.inputs['Detail'].default_value = 2
coords = nodes.new('ShaderNodeTexCoord')
links.new(coords.outputs['Object'], grain.inputs['Vector'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .18
bump.inputs['Distance'].default_value = .0015
links.new(grain.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs['Normal'], nodes['Principled BSDF'].inputs['Normal'])
steel = simple_material("Museumsbank Stahl Anthrazit", (.022, .025, .028, 1), .38)
steel.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = .7
seam = simple_material("Museumsbank Leder Naht", (.15, .047, .012, 1), .65)
for index, (bench_x, bench_y, rotation) in enumerate(((-4.5, -7.0, 180), (4.5, -7.0, 180)), 1):
    bench = D.objects.new(f"Museumsbank {index}", None); bcol.objects.link(bench)
    bench.location = (bench_x, bench_y, 0); bench.rotation_euler.z = math.radians(rotation)
    def bench_piece(label, position, dimensions, material, bevel):
        part = add_box(f"Museumsbank {index} {label}", position, dimensions, material, bevel)
        link(part, bcol)
        part.parent = bench
        return part
    bench_piece('Unterrahmen', (0, 0, .335), (2.30, .56, .05), steel, .012)
    for cushion in range(3):
        cx = (cushion - 1) * .8
        bench_piece('Lederpolster', (cx, 0, .40), (.79, .65, .12), leather, .042)
        for y in (-.31, .31):
            bench_piece('Polsternaht', (cx, y, .407), (.72, .003, .003), seam, .001)
    for x in (-.87, .87):
        for y in (-.255, .255):
            bench_piece('Stahlbein', (x, y, .17), (.045, .045, .30), steel, .006)
        bench_piece('Stahlkufe', (x, 0, .02), (.045, .555, .04), steel, .006)

# Je ein historischer Holzhocker in den vier Ecken mit Wandabstand.
stool_library = os.path.join(PROJECT_DIR, "assets", "library", "bar_chair_round_01_asset.blend")
with D.libraries.load(stool_library, link=False) as (source, imported_stools):
    imported_stools.objects = ["bar_chair_round_01"]
stool_template = imported_stools.objects[0]
if stool_template is None:
    raise RuntimeError("Hocker fehlt in der Möbelbibliothek: " + stool_library)
stool_transform = stool_template.matrix_basis.copy()
points = [stool_transform @ Vector(corner) for corner in stool_template.bound_box]
stool_center = Vector(((min(p.x for p in points) + max(p.x for p in points)) / 2,
                       (min(p.y for p in points) + max(p.y for p in points)) / 2,
                       min(p.z for p in points)))
stool_transform.translation -= stool_center
for index, (x, y) in enumerate(((-14.7, -15.8), (14.7, -15.8),
                                (-14.7, 19.1), (14.7, 19.1)), 1):
    stool = stool_template.copy()
    stool.name = f"Eckhocker {index} bar_chair_round_01"
    bcol.objects.link(stool)
    stool.matrix_basis = stool_transform.copy()
    stool.location += Vector((x, y, 0))
D.objects.remove(stool_template, do_unlink=True)

# Vorhandene Besucher entfernen; keine neuen Personen erzeugen.
for visitor in list(D.objects):
    if visitor.name.startswith("Besucher "):
        D.objects.remove(visitor, do_unlink=True)

# --- Sonnenstrahlen: pro Fenster der Sonnenseite ein Lichtschacht (Volumen-Quader entlang der Sonnenrichtung) -------
vm = D.materials.new("Dunst"); vm.use_nodes = True; nt_ = vm.node_tree; nt_.nodes.clear()
pv, vo = nt_.nodes.new("ShaderNodeVolumePrincipled"), nt_.nodes.new("ShaderNodeOutputMaterial")
pv.inputs["Density"].default_value, pv.inputs["Anisotropy"].default_value = 0.025, 0.35
nt_.links.new(pv.outputs["Volume"], vo.inputs["Volume"])
SUNDIR = Vector((-0.8, 0.22, -0.56)).normalized(); LEN = 10.0
for i, y in enumerate(YS):
    o = box(f"Lichtschacht {i + 1}", Vector((16.0, y, (Z0 + ZA) / 2)) + SUNDIR * LEN / 2, (LEN, W - 0.3, ZA - Z0 - 0.3), fcol)
    o.rotation_euler = SUNDIR.to_track_quat('X', 'Z').to_euler(); o.data.materials.append(vm); o.visible_shadow = False; o.display_type = 'WIRE'
S.cycles.volume_bounces = 0

# --- Zwei Hauptwerke gemeinsam inszenieren -----------------------------------------------
# Beide Minimalflaechen stehen als Paar auf getrennten Sockeln; die Kamera erfasst beide.
SK = 0.58
main_works = (obj_by_name("Kusner p=7"), obj_by_name("S41_7_5"))
for work in main_works:
    work.scale = (SK,) * 3
    work.location.z += 0.80 - (work.location.z + min(v[2] for v in work.bound_box) * SK)
    if not any(modifier.type == 'SUBSURF' for modifier in work.modifiers):
        modifier = work.modifiers.new("Subdivision", "SUBSURF")
        modifier.levels, modifier.render_levels = 1, 2
for n in ("Sockel unten", "Sockel oben", "S41 Sockel unten", "S41 Sockel oben"):
    obj_by_name(n).scale.x *= 0.6
    obj_by_name(n).scale.y *= 0.6

work_centers = [work.location.z + (min(v[2] for v in work.bound_box) +
                                   max(v[2] for v in work.bound_box)) * SK / 2
                for work in main_works]
ZC = sum(work_centers) / len(work_centers)
obj_by_name("Kamera Ziel").location = (0, 0, ZC)
cam = obj_by_name("Museumskamera")
# Die Bahn liegt innerhalb der seitlichen Säulenreihe. Bei größerem Radius
# schnitt die Kamera um 75°/285° durch eine Säule und zeigte nur deren Oberfläche.
# Die kürzere Brennweite erhält dabei ungefähr denselben Bildausschnitt.
cam.location = (0, -12.0, ZC + 0.25)
cam.data.lens = 29

# Raum und Kunstwerke um 10 Prozent verkleinern; Möbel bleiben im Originalmaß.
# Nur Wurzelobjekte verändern, damit Kinder nicht doppelt skaliert werden.
MUSEUM_SIZE_FACTOR = 0.90
for obj in S.objects:
    if obj.parent is not None or obj.type == 'CAMERA' or obj.name == 'Kamera Orbit':
        continue
    obj.location *= MUSEUM_SIZE_FACTOR
    if bcol not in obj.users_collection:
        obj.scale *= MUSEUM_SIZE_FACTOR
    else:
        # Möbel einschließlich der Bank-Kindobjekte einmalig um 10 % vergrößern.
        obj.scale *= 1.10
bpy.context.view_layer.update()

# --- Außenwelt: Pine Ridge, ohne fremde Kamera oder Beleuchtung ---------------------------
garden_col = D.collections.new("Aussengarten")
S.collection.children.link(garden_col)
ridge_library = os.path.join(PROJECT_DIR, 'assets', 'library', 'pine_ridge', 'pine_ridge_asset.blend')
with D.libraries.load(ridge_library, link=False) as (source, ridge):
    ridge.collections = ['Pine Ridge Museum Exterior']
ridge_template = ridge.collections[0]
from mathutils.bvhtree import BVHTree
ridge_terrain = next(obj for obj in ridge_template.objects if obj.name == 'Pine Ridge Plane')
root_points = {}
ground_material = simple_material('Aussenwelt Waldboden', (.12, .18, .055, 1), .95)
for side in (-1, 1):
    transform = Matrix.Translation((side * 47, 0, -2.7))
    if side < 0:
        transform @= Matrix.Rotation(math.pi, 4, 'Z')
    terrain_matrix = transform @ ridge_terrain.matrix_basis
    terrain_bvh = BVHTree.FromPolygons(
        [terrain_matrix @ v.co for v in ridge_terrain.data.vertices],
        [tuple(p.vertices) for p in ridge_terrain.data.polygons])
    ground = add_box(f'Aussenwelt Waldboden {side}', (side * 95, 0, -2.85),
                     (160, 240, .30), ground_material, 0)
    link(ground, garden_col)
    for template in ridge_template.objects:
        obj = template.copy()
        obj.name = f"Aussenwelt Pine Ridge {side} {template.name}"
        garden_col.objects.link(obj)
        obj.matrix_basis = transform @ template.matrix_basis
        # Die zusätzlichen Randbäume der Quellszene stehen teils außerhalb des Hangs.
        # Baumwurzel aus den tiefsten Meshpunkten bestimmen und aufs Gelände setzen.
        if 'TREE' in template.name:
            key = template.data.as_pointer()
            if key not in root_points:
                low = min(v.co.z for v in template.data.vertices)
                roots = [v.co for v in template.data.vertices if v.co.z < low + .025]
                root_points[key] = sum(roots, Vector()) / len(roots)
            root = obj.matrix_basis @ root_points[key]
            hit, _, _, _ = terrain_bvh.ray_cast(Vector((root.x, root.y, 100)), Vector((0, 0, -1)), 200)
            ground_z = hit.z if hit is not None else -2.7
            obj.location.z += ground_z - root.z - .04
        obj.hide_render = False
        obj.hide_viewport = False
for template in list(ridge_template.objects):
    D.objects.remove(template, do_unlink=True)
D.collections.remove(ridge_template)



# GPU-PRESETS
def setup_cycles():
    """Gemeinsame Einstellungen für alle Cycles-Presets setzen."""
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPTIX'
    scene.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    scene.cycles.volume_bounces = 0
    scene.cycles.sample_clamp_direct = 0.0
    scene.render.use_persistent_data = True


def preset_test():
    c = scene.cycles

    c.adaptive_threshold = 0.05
    c.samples = 16

    c.denoising_prefilter = 'FAST'
    c.denoising_quality = 'BALANCED'

    c.max_bounces = 4
    c.diffuse_bounces = 1
    c.glossy_bounces = 2
    c.transmission_bounces = 2
    c.transparent_max_bounces = 2

    c.sample_clamp_indirect = 3.0

    c.caustics_reflective = False
    c.caustics_refractive = False

    print("Preset aktiviert: SCHNELLER TEST")


def preset_final_fast():
    c = scene.cycles

    c.adaptive_threshold = 0.03
    c.samples = 32

    c.denoising_prefilter = 'FAST'
    c.denoising_quality = 'BALANCED'

    c.max_bounces = 5
    c.diffuse_bounces = 2
    c.glossy_bounces = 3
    c.transmission_bounces = 3
    c.transparent_max_bounces = 3

    c.sample_clamp_indirect = 4.0

    c.caustics_reflective = False
    c.caustics_refractive = False

    print("Preset aktiviert: FINAL FAST")


def preset_animation():
    c = scene.cycles

    c.adaptive_threshold = 0.02
    c.samples = 48

    c.denoising_prefilter = 'FAST'
    c.denoising_quality = 'BALANCED'

    c.max_bounces = 6
    c.diffuse_bounces = 2
    c.glossy_bounces = 4
    c.transmission_bounces = 4
    c.transparent_max_bounces = 4

    c.sample_clamp_indirect = 5.0

    c.caustics_reflective = False
    c.caustics_refractive = False

    print("Preset aktiviert: ANIMATION SCHNELL")


def preset_quality():
    c = scene.cycles

    c.adaptive_threshold = 0.01
    c.samples = 128

    c.denoising_prefilter = 'ACCURATE'
    c.denoising_quality = 'HIGH'

    c.max_bounces = 8
    c.diffuse_bounces = 4
    c.glossy_bounces = 6
    c.transmission_bounces = 8
    c.transparent_max_bounces = 8

    c.sample_clamp_indirect = 10.0

    c.caustics_reflective = True
    c.caustics_refractive = True

    print("Preset aktiviert: QUALITÄT")



# Gewaehltes GPU-Preset auf die fertig aufgebaute Szene anwenden.
scene = bpy.context.scene
setup_cycles()
{"test": preset_test, "final_fast": preset_final_fast,
 "animation": preset_animation, "quality": preset_quality}[RENDER_PRESET]()
scene.frame_set(scene.frame_start)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == "VIEW_3D":
            area.spaces.active.region_3d.view_perspective = "CAMERA"
print("Museum mit Granit und ohne Besucher bereit. F12: Bild; Strg+F12: Animation.")
print("Renderausgabe: " + scene.render.filepath)
