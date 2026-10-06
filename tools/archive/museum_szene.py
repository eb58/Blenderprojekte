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

P = 7

# False = Testbild mit F12; True = Video mit Strg+F12
MAKE_VIDEO = True

FPS = 24
DURATION = 12
ORBIT_DEGREES = 360

SCULPTURE_SCALE = 3.25
THICKNESS = 0.060

STILL_OUTPUT = "//kusner_p7_museum_test.png"
VIDEO_OUTPUT = "//kusner_p7_granit_museum.mp4"


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
scene.render.resolution_x = 1280
scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = FPS * DURATION

if MAKE_VIDEO:
    scene.cycles.samples = 48
    scene.render.filepath = VIDEO_OUTPUT
    scene.render.image_settings.media_type = "VIDEO"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.audio_codec = "NONE"
else:
    scene.cycles.samples = 64
    scene.render.filepath = STILL_OUTPUT
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"

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

wall_material = simple_material("Warmer Kalkstein", (0.54, 0.43, 0.31, 1), 0.52)
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
# SOCKEL UND POSITION
# ============================================================

add_box("Sockel unten", (0, 0, 0.30), (7.2, 4.8, 0.60), base_material, 0.07)
add_box("Sockel oben", (0, 0, 0.68), (6.6, 4.2, 0.16), base_material, 0.04)
plinth_top = 0.77
min_z = min(vertex[2] for vertex in vertices)
kusner.location.z = plinth_top - min_z + 0.03
kusner.rotation_euler.z = math.radians(10)
sculpture_center_z = kusner.location.z + (min(v[2] for v in vertices) + max(v[2] for v in vertices)) / 2


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

# Seitliche Kolonnaden betonen die größere Raumhöhe.
for x in (-13.6, 13.6):
    for y in (-10, -4, 2, 8, 14):
        add_cylinder("Saeulenbasis", (x, y, 0.28), 0.72, 0.56, trim_material)
        add_cylinder("Saeule", (x, y, 4.55), 0.45, 8.1, trim_material)
        add_cylinder("Kapitell", (x, y, 8.78), 0.70, 0.38, trim_material)
        add_box("Abakus", (x, y, 9.04), (1.2, 1.2, 0.20), trim_material, 0.025)

add_box("Gesims links", (-13.6, 2, 9.48), (1.35, 35, 0.68), trim_material, 0.04)
add_box("Gesims rechts", (13.6, 2, 9.48), (1.35, 35, 0.68), trim_material, 0.04)
add_box("Seitenwand links", (-16.2, 2, hall_height / 2), (0.50, 38, hall_height), wall_material)
add_box("Seitenwand rechts", (16.2, 2, hall_height / 2), (0.50, 38, hall_height), wall_material)


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

start_angle = math.radians(-22)
rotation_amount = math.radians(ORBIT_DEGREES)
driver = orbit.driver_add("rotation_euler", 2).driver
driver.type = "SCRIPTED"
driver.expression = (
    f"{start_angle} + {rotation_amount} * "
    f"(frame-{scene.frame_start}) / {scene.frame_end-scene.frame_start}"
)

scene.frame_set(1)
print("KUSNER p=7: TESTBILD BEREIT" if not MAKE_VIDEO else "KUSNER p=7: VIDEO BEREIT")
print("F12 rendert das Testbild; bei MAKE_VIDEO=True startet Strg+F12 die 360°-Fahrt.")
