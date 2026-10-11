"""Geometrie-Helfer für den Szenenaufbau: Quader, Nischen, Lichter und Collections."""
import bpy
from mathutils import Vector

D, C = bpy.data, bpy.context


def obj_by_name(name):
    obj = D.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Objekt '{name}' wurde in der Szene nicht gefunden.")
    return obj


def sammlung(name):
    """Neue Collection unterhalb der Szenen-Collection."""
    collection = D.collections.new(name)
    C.scene.collection.children.link(collection)
    return collection


def link(o, col):
    for c in o.users_collection: c.objects.unlink(o)
    col.objects.link(o)


def add_box(name, location, dimensions, material, bevel_width=0.0):
    """Quader mit angewandter Skalierung, optional abgerundeten Kanten und Material."""
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = C.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel_width:
        modifier = obj.modifiers.new("Sanfte Kanten", "BEVEL")
        modifier.width = bevel_width
        modifier.segments = 3
    obj.data.materials.append(material)
    return obj


def box(name, loc, dim, col):
    """Einfacher Quader ohne Material in der Collection `col` (Skalierung bleibt am Objekt)."""
    bpy.ops.mesh.primitive_cube_add(location=loc); o = C.active_object; o.name = name; o.dimensions = dim; link(o, col); return o


def join(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    C.view_layer.objects.active = objs[0]; bpy.ops.object.join(); return C.active_object


def add_area_light(name, location, energy, size, color, target):
    data = D.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "RECTANGLE"
    data.size = size
    data.size_y = size * 1.45
    data.color = color
    obj = D.objects.new(name, data)
    C.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def add_niche(name, x, y_front, width, height, depth, back_material, reveal_material, light_material):
    """Schlichte, hohe Rechtecknische: dunkle Rückwand, glatte steinerne Laibung und eine Lichtkante unter dem Sturz."""
    half = width / 2
    profile = [(-half, 0.0), (-half, height), (half, height), (half, 0.0)]
    y_back = y_front + depth
    vertices = [(x + px, y, pz) for y in (y_front, y_back) for px, pz in profile]
    faces = [(4, 5, 6, 7)] + [(i, i + 1, 4 + i + 1, 4 + i) for i in range(3)]  # Rückwand, links/oben/rechts
    mesh = D.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = D.objects.new(name, mesh)
    C.collection.objects.link(obj)
    obj.data.materials.append(back_material)
    obj.data.materials.append(reveal_material)
    for polygon in mesh.polygons[1:]:
        polygon.material_index = 1
    # Zwischen Laibung und Pfeiler bleibt sonst ein Spalt: mit Mauerwerk füllen.
    for side, sign in (("L", -1), ("R", 1)):
        add_box(f"{name}_Laibungsfuellung_{side}", (x + sign * (half + 0.205), y_front + depth / 2, height / 2),
                (0.39, depth, height), reveal_material)
    add_box(name + "_Lichtkante", (x, y_front + 0.22, height - 0.04), (width - 0.24, 0.05, 0.03), light_material)
    return obj
