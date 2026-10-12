"""Ausstattung des Museums: Plaketten, Wandteppich, Bänke, Hocker und Außengarten."""
import math
import os

import bpy
from mathutils import Matrix, Vector

from bauteile import add_box, box, link, sammlung
from einstellungen import PROJECT_DIR
from materialien import leder, simple_material

D, C = bpy.data, bpy.context
BILDER = os.path.join(PROJECT_DIR, "assets", "bilder")

PLAKETTENTEXTE = {  # Name des Werks, Schöpfer und Jahr
    "Costa": ("Der schwebende Hut", "Celso Costa, 1982"),
    "Henneberg": ("Die Steinrose", "Lebrecht Henneberg, 1875"),
    "Sierpinski-Pyramide": ("Der Spitzenberg", "Wacław Sierpiński, 1915"),
    "Cobra": ("Der Mondring", "Erich Brandl, 2026"),
    "Double Trefoil": ("Das doppelte Glück", "Erich Brandl, 2026"),
    "Kusner": ("Das Siebengestirn", "Robert Kusner, 1987"),
    "S41": ("Das steinerne Band", "Erich Brandl, 2026"),
    "Teppich": ("Der endlose Atem", "Benoit Mandelbrot, 1980"),
}


class Plaketten:
    """Kleine Kupferplaketten mit dunkler Schrift, wie im Museum."""

    def __init__(self):
        self.collection = sammlung("Sockelbeschriftungen")
        self.kupfer = simple_material("Sockelschild Kupfer", (.62, .30, .17, 1), .32, .9)
        self.schrift = simple_material("Sockelschild Schrift", (.025, .012, .007, 1), .55)

    def zeilen(self, name, schluessel, breite, hoehe):
        """Liefert zwei Schriftkurven (Name groß, Schöpfer mit Jahr kleiner) samt Höhenversatz zur Plakettenmitte.

        Die Größe passt den Text grob (0,7 Schrifthöhen je Zeichen) auf die Plakette.
        """
        titel, urheber = PLAKETTENTEXTE[schluessel]
        zeilen = []
        for zeile, text, anteil, versatz in (("Titel", titel, .30, .17), ("Urheber", urheber, .20, -.22)):
            kurve = D.curves.new(f"{name} {zeile}", "FONT"); kurve.body = text
            kurve.align_x = 'CENTER'; kurve.align_y = 'CENTER'
            kurve.size = min(hoehe * anteil, breite * .88 / (len(text) * .7))
            kurve.extrude = .003; kurve.materials.append(self.schrift)
            zeilen.append((f"{name} {zeile}", kurve, hoehe * versatz))
        return zeilen

    def sockelschild(self, name, schluessel, x, y_vorne, z, breite=.75, hoehe=.2):
        """Setzt eine kleine Kupferplakette vor die Sockelseite bei y_vorne (Blick nach +y)."""
        tafel = box(f"{name} Tafel", (x, y_vorne - .006, z), (breite, .012, hoehe), self.collection)
        tafel.data.materials.append(self.kupfer)
        for objektname, kurve, dz in self.zeilen(name, schluessel, breite, hoehe):
            schrift = D.objects.new(objektname, kurve)
            self.collection.objects.link(schrift)
            schrift.location = (x, y_vorne - .0125, z + dz)
            schrift.rotation_euler.x = math.radians(90)


def wandteppich(plaketten, wall_y, hall_height):
    """Mandelbrot-Wandteppich mit Messingsaum, Fransen, Plakette und Wandlicht an der Vorderwand (Blick nach -y)."""
    gcol = sammlung("Wandgestaltung")
    brass = simple_material("Wandtafel Messing", (0.72, 0.43, 0.12, 1), 0.22, 0.9)

    def wall_box(name, x, z, width, height, depth, material, y):
        bpy.ops.mesh.primitive_cube_add(location=(x, y, z))
        obj = C.active_object; obj.name = name; obj.dimensions = (width, depth, height)
        obj.data.materials.append(material); link(obj, gcol)
        return obj

    textile = D.materials.new("Mandelbrot Wandteppich"); textile.use_nodes = True
    nodes = textile.node_tree.nodes; links = textile.node_tree.links; nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    image_node = nodes.new("ShaderNodeTexImage")
    grayscale = nodes.new("ShaderNodeRGBToBW")
    bump = nodes.new("ShaderNodeBump")
    image_node.image = D.images.load(os.path.join(BILDER, "mandelbrot_tapestry.png"), check_existing=True)
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
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, wall_y + 0.10, tapestry_center_z),
                                    rotation=(math.pi / 2, 0, 0))
    tapestry = C.active_object; tapestry.name = "Mandelbrot Wandteppich"
    tapestry.scale = (-7.4, 3.3, 1)  # negative X gleicht die Betrachtung der Rückseite aus
    tapestry.data.materials.append(textile); link(tapestry, gcol)
    solidify = tapestry.modifiers.new("Gewebedicke", "SOLIDIFY"); solidify.thickness = 0.055
    bevel = tapestry.modifiers.new("Weicher Teppichrand", "BEVEL"); bevel.width = 0.035; bevel.segments = 3
    # Messingsaum
    width, height = 14.95, 6.75
    for index, (dx, dz, w, h) in enumerate(((0, height / 2, width, 0.06),
                                             (0, -height / 2, width, 0.06),
                                             (-width / 2, 0, 0.06, height),
                                             (width / 2, 0, 0.06, height))):
        wall_box(f"Teppichsaum {index}", dx, tapestry_center_z + dz, w, h, 0.05, brass, wall_y + 0.07)
    for x in (-6.8, -5.8, -4.8, -3.8, -2.8, -1.8, -0.8, 0.2, 1.2, 2.2, 3.2, 4.2, 5.2, 6.2):
        wall_box("Teppichfranse", x, tapestry_center_z - 3.57, 0.04, 0.38, 0.03, brass, wall_y + 0.11)
    # Kleine Kupferplakette rechts unten neben dem Teppich (Blick nach -y: rechts ist -x).
    plaque_x, plaque_z = -(7.4 + 0.75), tapestry_center_z - 2.9
    plaque_width, plaque_height = 1.15, 0.26
    wall_box("Teppichtafel", plaque_x, plaque_z, plaque_width, plaque_height, 0.012, plaketten.kupfer, wall_y + 0.066)
    for objektname, kurve, dz in plaketten.zeilen("Teppichtafel", "Teppich", plaque_width, plaque_height):
        plaque_text = D.objects.new(objektname, kurve)
        gcol.objects.link(plaque_text)
        plaque_text.location = (plaque_x, wall_y + 0.0725, plaque_z + dz)
        plaque_text.rotation_euler.x = math.radians(90)
        plaque_text.scale.x = -1
        plaque_text.scale.z = -1

    # Warmes, flaches Museumslicht für den Wandteppich.
    for index, x in enumerate((-5.5, 0, 5.5), 1):
        lamp_data = D.lights.new(f"Wandlicht {index}", "AREA")
        lamp_data.energy = 220; lamp_data.shape = 'RECTANGLE'; lamp_data.size = 3.2
        lamp_data.size_y = 0.4; lamp_data.color = (1.0, 0.72, 0.42)
        lamp = D.objects.new(f"Wandlicht {index}", lamp_data); gcol.objects.link(lamp)
        lamp.location = (x, -14.8, 11.8)
        lamp.rotation_euler = Vector((0, -2.2, -3.0)).to_track_quat('-Z', 'Y').to_euler()


def museumsbaenke():
    """Eigener Entwurf: bordeauxrote Lederpolster auf dunklen Stahlkufen. Liefert die Möbel-Collection."""
    bcol = sammlung("Bank")
    leather = leder()
    steel = simple_material("Museumsbank Stahl Anthrazit", (.022, .025, .028, 1), .38)
    steel.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = .7
    seam = simple_material("Museumsbank Leder Naht", (.035, .002, .005, 1), .65)
    for index, (bench_x, bench_y, rotation) in enumerate(((-4.5, -7.0, 180), (4.5, -7.0, 180)), 1):
        bench = D.objects.new(f"Museumsbank {index}", None); bcol.objects.link(bench)
        bench.location = (bench_x, bench_y, 0); bench.rotation_euler.z = math.radians(rotation)
        bench.scale = (1.26, 1.26, 1.26)

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
    return bcol


def eckhocker(bcol):
    """Je ein historischer Holzhocker (Poly Haven, assets/moebel) in den vier Ecken mit Wandabstand."""
    stool_library = os.path.join(PROJECT_DIR, "assets", "moebel", "bar_chair_round_01_asset.blend")
    with D.libraries.load(stool_library, link=False) as (source, imported_stools):
        imported_stools.objects = ["bar_chair_round_01"]
    stool_template = imported_stools.objects[0]
    if stool_template is None:
        raise RuntimeError("Hocker fehlt, siehe assets/README.md: " + stool_library)
    stool_transform = stool_template.matrix_basis.copy()
    points = [stool_transform @ Vector(corner) for corner in stool_template.bound_box]
    stool_center = Vector(((min(p.x for p in points) + max(p.x for p in points)) / 2,
                           (min(p.y for p in points) + max(p.y for p in points)) / 2,
                           min(p.z for p in points)))
    stool_transform.translation -= stool_center
    # Um den Fußpunkt skalieren, damit der Hocker auf dem Boden bleibt.
    stool_transform = Matrix.Scale(1.30, 4) @ stool_transform
    for index, (x, y) in enumerate(((-14.7, -15.8), (14.7, -15.8),
                                    (-14.7, 19.1), (14.7, 19.1)), 1):
        stool = stool_template.copy()
        stool.name = f"Eckhocker {index} bar_chair_round_01"
        bcol.objects.link(stool)
        # Die Lehne zeigt im Modell nach +Y; sie soll diagonal in die Raumecke weisen.
        facing = math.atan2(math.copysign(1, y), math.copysign(1, x)) - math.pi / 2
        stool.matrix_basis = Matrix.Rotation(facing, 4, 'Z') @ stool_transform
        stool.location += Vector((x, y, 0))
    D.objects.remove(stool_template, do_unlink=True)


def aussengarten():
    """Ruhiger Museumspark als leichte Panoramakulisse vor beiden Fensterseiten."""
    garden_col = sammlung("Aussengarten")
    ground_material = simple_material('Aussenwelt Parkboden', (.16, .25, .065, 1), .92)
    for side in (-1, 1):
        ground = add_box(f'Aussenwelt Parkboden {side}', (side * 58, 2, -2.85),
                         (84, 100, .30), ground_material, 0)
        link(ground, garden_col)
    panorama_path = os.path.join(BILDER, 'museum_park_panorama.png')
    if not os.path.exists(panorama_path):
        raise RuntimeError(f'Parkpanorama fehlt: {panorama_path}')

    panorama_image = D.images.load(panorama_path, check_existing=True)
    panorama_material = D.materials.new('Aussenwelt Parkpanorama')
    panorama_material.use_nodes = True
    panorama_nodes = panorama_material.node_tree.nodes
    panorama_nodes.clear()
    panorama_output = panorama_nodes.new('ShaderNodeOutputMaterial')
    panorama_emission = panorama_nodes.new('ShaderNodeEmission')
    panorama_texture = panorama_nodes.new('ShaderNodeTexImage')
    panorama_texture.image = panorama_image
    panorama_texture.interpolation = 'Linear'
    panorama_texture.extension = 'EXTEND'
    panorama_emission.inputs['Strength'].default_value = 0.8
    panorama_material.node_tree.links.new(panorama_texture.outputs['Color'], panorama_emission.inputs['Color'])
    panorama_material.node_tree.links.new(panorama_emission.outputs['Emission'], panorama_output.inputs['Surface'])

    for side in (-1, 1):
        bpy.ops.mesh.primitive_plane_add(
            size=2,
            location=(side * 32, 2, 6.5),
            rotation=(math.pi / 2, 0, math.pi / 2),
        )
        panorama = C.object
        panorama.name = f'Aussenwelt Parkpanorama {side}'
        panorama.scale = (35, 11.67, 1)
        panorama.data.materials.append(panorama_material)
        link(panorama, garden_col)
