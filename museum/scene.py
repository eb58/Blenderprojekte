"""Komplettes Museum: Granitskulpturen, Architektur, Ausstattung und OptiX-Renderpreset.
In Blender ausfuehren. Ersetzt alle vorhandenen Objekte; speichert nicht automatisch.

Einstellungen: einstellungen.py; Materialien: materialien.py; Geometrie-Helfer: bauteile.py;
Plaketten, Wandteppich, Möbel und Garten: ausstattung.py; Cycles-Presets: rendering.py.
"""
import importlib
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import einstellungen
import rendering
import materialien
import bauteile
import ausstattung
import costa
import sierpinski
import weierstrass

# Beim erneuten Ausführen in derselben Blender-Sitzung geänderte Module neu laden.
for modul in (einstellungen, rendering, materialien, bauteile, ausstattung, costa, sierpinski, weierstrass):
    importlib.reload(modul)

from einstellungen import HAUPTWERK_FAKTOR, MAKE_VIDEO, ORBIT_DEGREES, SCULPTURE_SCALE, START_ANGLE, THICKNESS
from materialien import ashlar_material, emissive_material, simple_material
from bauteile import add_area_light, add_box, add_niche, box, join, link, obj_by_name, sammlung

D, C = bpy.data, bpy.context
P = 7  # Enden der Kusner-Fläche


# ============================================================
# SZENE / RENDERER
# ============================================================

# Die Datei vollständig leeren, einschließlich ausgeblendeter oder nicht
# auswählbarer Objekte aus anderen Collections.
for existing_object in list(D.objects):
    D.objects.remove(existing_object, do_unlink=True)

scene = C.scene
rendering.grundeinstellungen(scene, einstellungen)


# ============================================================
# MATERIALIEN DES MUSEUMS
# ============================================================

granite = materialien.granit()
# Historischer Materialname bleibt für die späteren Materialzugriffe erhalten.
# Kühler, matter Salbei-/Schieferputz kontrastiert mit den warmen Steinrahmen.
wall_material = simple_material("Warmer Kalkstein", (0.23, 0.32, 0.31, 1), 0.78)
trim_material = simple_material("Heller Naturstein", (0.68, 0.59, 0.47, 1), 0.44)
floor_material = simple_material("Polierter Museumsboden", (0.10, 0.072, 0.048, 1), 0.24)
plinth_stone = materialien.elfenbein_kalkstein()


# ============================================================
# GRANITSKULPTUREN: NICHTORIENTIERBARE MINIMALFLÄCHEN
# ============================================================

def granitskulptur(name, mesh_name, eckpunkte, flaechen):
    """Legt eine Granitfläche mit Granitdicke und sanften Kanten an."""
    mesh = D.meshes.new(mesh_name)
    mesh.from_pydata(eckpunkte, [], flaechen)
    mesh.update()
    skulptur = D.objects.new(name, mesh)
    C.collection.objects.link(skulptur)
    skulptur.data.materials.append(granite)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    solidify = skulptur.modifiers.new("Granitdicke", "SOLIDIFY")
    solidify.thickness = THICKNESS
    solidify.offset = 0
    solidify.use_even_offset = True
    bevel = skulptur.modifiers.new("Sanfte Kanten", "BEVEL")
    bevel.width = 0.012
    bevel.segments = 2
    return skulptur


# Formeln und Ringbereiche wie auf https://eb58.github.io/Non-Orientable-Minimal-Surfaces/
vertices, faces = weierstrass.kusner(P, SCULPTURE_SCALE * HAUPTWERK_FAKTOR)
kusner = granitskulptur("Kusner p=7", "Kusner_p7_Mesh", vertices, faces)
s41_vertices, s41_faces = weierstrass.s41(7, 5, 1.1, 1.3, SCULPTURE_SCALE * HAUPTWERK_FAKTOR)
s41 = granitskulptur("S41_7_5", "S41_7_5_Mesh", s41_vertices, s41_faces)
# Doppeltes Kleeblatt "S41_5_3 Double Trefoil" (m = 5, n = 3, Ring 1,1 bis 1,5).
double_trefoil = granitskulptur("Double Trefoil", "Double_Trefoil_Mesh",
                                *weierstrass.s41(5, 3, 1.1, 1.5, SCULPTURE_SCALE))
henneberg = granitskulptur("Henneberg", "Henneberg_Mesh", *weierstrass.henneberg(5, SCULPTURE_SCALE))
cobra = granitskulptur("Cobra", "Cobra_Mesh", *weierstrass.cobra(5, 1.0, SCULPTURE_SCALE))
# Endenausschnitt ε = 0,12
costa_skulptur = granitskulptur("Costa", "Costa_Mesh", *costa.flaeche(SCULPTURE_SCALE))


# ============================================================
# SOCKEL UND POSITION DER BEIDEN HAUPTWERKE
# ============================================================

# Abstand wächst mit den Hauptwerken, damit sie sich in der Raummitte nicht berühren.
EXHIBIT_X = 4.4 * HAUPTWERK_FAKTOR
add_box("Sockel unten", (-EXHIBIT_X, 0, 0.30), (7.2, 4.8, 0.60), plinth_stone, 0.07)
add_box("Sockel oben", (-EXHIBIT_X, 0, 0.68), (6.6, 4.2, 0.16), plinth_stone, 0.04)
add_box("S41 Sockel unten", (EXHIBIT_X, 0, 0.30), (7.2, 4.8, 0.60), plinth_stone, 0.07)
add_box("S41 Sockel oben", (EXHIBIT_X, 0, 0.68), (6.6, 4.2, 0.16), plinth_stone, 0.04)
plinth_top = 0.77


def unterkante(skulptur):
    """Tiefster Punkt einschließlich Granitdicke und Kantenrundung, damit nichts über dem Sockel schwebt."""
    C.view_layer.update()
    ausgewertet = skulptur.evaluated_get(C.evaluated_depsgraph_get())
    return min(ecke[2] for ecke in ausgewertet.bound_box)


kusner.location.x = -EXHIBIT_X
kusner.location.z = plinth_top - unterkante(kusner)
kusner.rotation_euler.z = math.radians(10)
s41.location.x = EXHIBIT_X
s41.location.z = plinth_top - unterkante(s41)
s41.rotation_euler.z = math.radians(-10)
sculpture_center_z = max(
    kusner.location.z + (min(v[2] for v in vertices) + max(v[2] for v in vertices)) / 2,
    s41.location.z + (min(v[2] for v in s41_vertices) + max(v[2] for v in s41_vertices)) / 2,
)


# ============================================================
# HÖHERE MUSEUMSHALLE UND TIEFE ARKADEN
# ============================================================

# Der Boden reicht bis in die Nischen hinein (bis zur Rückwand der Arkaden), sonst schimmert dort der Hintergrund durch.
floor_obj = add_box("Museumsboden", (0, 0.55, -0.13), (36, 39.1, 0.26), floor_material, 0.015)

# Geschlossene, ruhige Galeriewand aus großformatigen Steinplatten mit fünf hohen Nischen.
arcade_front_y = 17.0
arcade_depth = 2.8
hall_height = 13.2
arcade_stone = ashlar_material("Arkaden Kalkstein", (0.66, 0.63, 0.57, 1), (0.63, 0.60, 0.55, 1),
                               (0.52, 0.50, 0.46, 1), block_width=2.4, block_height=1.2)
niche_material = simple_material("Tiefe Arkadennischen", (0.075, 0.12, 0.10, 1), 0.62)
niche_light = emissive_material("Nischen Lichtkante", (1.0, 0.86, 0.66, 1), 9.0)

# Rückwand, oberes Wandband und breite gemeinsame Pfeiler bilden eine ruhige Einheit.
# 2 cm Abstand zur Rückfläche der Nischen: Sonst liegen beide in einer Ebene und flimmern (Z-Fighting) in Echtzeitansichten.
add_box("Arkadengalerie Rueckwand", (0, arcade_front_y + arcade_depth + 0.18, hall_height / 2),
        (34, 0.32, hall_height), arcade_stone)
add_box("Arkadengalerie Wandband", (0, arcade_front_y + arcade_depth / 2, 10.75),
        (34, arcade_depth, 4.9), arcade_stone)
NICHE_XS = (-11.0, -5.5, 0.0, 5.5, 11.0)
NICHE_WIDTH = 3.7
PIER_WIDTH, PIER_HEIGHT = 1.05, 8.3  # Pfeiler zwischen den Nischen; darüber beginnt das Wandband
for index, x in enumerate((-13.75, -8.25, -2.75, 2.75, 8.25, 13.75), 1):
    add_box(f"Arkadengalerie Pfeiler {index}", (x, arcade_front_y + arcade_depth / 2, PIER_HEIGHT / 2),
            (PIER_WIDTH, arcade_depth, PIER_HEIGHT), arcade_stone)
for index, x in enumerate((-15.75, 15.75), 1):
    add_box(f"Arkadengalerie Randfeld {index}", (x, arcade_front_y + arcade_depth / 2, PIER_HEIGHT / 2),
            (3.0, arcade_depth, PIER_HEIGHT), arcade_stone)  # reicht bis an den äußeren Pfeiler heran, kein Spalt

for index, x in enumerate(NICHE_XS, 1):
    add_niche(f"Nische {index}", x, arcade_front_y, NICHE_WIDTH, PIER_HEIGHT, arcade_depth,
              niche_material, arcade_stone, niche_light)
    # Weiches Licht oben in der Nische, das die Rückwand und die Laibung aufhellt; selbst unsichtbar für die Kamera.
    wall_wash = add_area_light(f"Nischenlicht {index}", (x, arcade_front_y + 0.6, 7.7), 260, 1.8,
                               (1.0, 0.85, 0.68), (x, arcade_front_y + arcade_depth - 0.2, 3.0))
    wall_wash.visible_camera = False

# Ruhige Seitenwände mit tiefen Fensternischen statt freistehender Kolonnaden.
# Innenflächen der Seitenwände liegen bei x = ±15,75.
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


# ============================================================
# FENSTER IN BEIDEN SEITENWÄNDEN
# ============================================================

fcol = sammlung("Fenster")
titanium = materialien.titan()
FRAME_WIDTH = 0.05  # sichtbare Breite des Titanrahmens in der Ansicht
glass = materialien.fensterglas()

# Hohe, schlichte Rechteckfenster zwischen den Säulen: Fenstermitten (y), Breite, Sohle und Oberkante der Öffnung.
YS, W, Z0, ZA = [-7, -1, 5, 11], 2.6, 1.0, 9.6


def window_niche(side, x, y, index):
    """Schlichte, tiefe Laibung aus Naturstein ohne Bogen: zwei Wangen, ein Sturz und eine schlanke Sohlbank."""
    inward = 1 if side == "L" else -1
    front_x = x + inward * 0.50
    back_x = x - inward * 0.10
    center_x = (front_x + back_x) / 2
    depth = abs(front_x - back_x)
    border = 0.20
    prefix = f"Fensternische {side}{index}"
    for sign in (-1, 1):
        obj = add_box(prefix + f" Laibung {sign}",
                      (center_x, y + sign * (W / 2 + border / 2), (Z0 + ZA) / 2),
                      (depth, border, ZA - Z0 + border), trim_material, 0.01)
        link(obj, fcol)
    lintel = add_box(prefix + " Sturz", (center_x, y, ZA + border / 2), (depth, W + 2 * border, border),
                     trim_material, 0.01)
    link(lintel, fcol)
    sill = add_box(prefix + " Fensterbank", (front_x - inward * 0.14, y, Z0 - 0.04),
                   (0.62, W + 2 * border, 0.08), trim_material, 0.01)
    link(sill, fcol)


for side, x in (("L", -16.2), ("R", 16.2)):
    cut = []
    for i, y in enumerate(YS):
        cut.append(box(f"c{i}", (x, y, (Z0 + ZA) / 2), (1.4, W, ZA - Z0), fcol))
        # Glasscheibe in der Öffnung, umlaufend gefasst von einem schlanken Titanrahmen.
        pane = box(f"Fensterglas {side}{i + 1}", (x, y, (Z0 + ZA) / 2), (0.03, W, ZA - Z0), fcol)
        pane.data.materials.append(glass)
        rim = join([box("l", (x, y - W / 2 + FRAME_WIDTH / 2, (Z0 + ZA) / 2), (0.07, FRAME_WIDTH, ZA - Z0), fcol),
                    box("r", (x, y + W / 2 - FRAME_WIDTH / 2, (Z0 + ZA) / 2), (0.07, FRAME_WIDTH, ZA - Z0), fcol),
                    box("t", (x, y, ZA - FRAME_WIDTH / 2), (0.07, W, FRAME_WIDTH), fcol),
                    box("b", (x, y, Z0 + FRAME_WIDTH / 2), (0.07, W, FRAME_WIDTH), fcol)])
        rim.name = f"Fensterrahmen Titan {side}{i + 1}"; rim.data.materials.append(titanium)
        window_niche(side, x, y, i + 1)
    c = join(cut); c.name = f"Fensterschnitt {side}"; c.display_type = 'WIRE'; c.hide_render = True
    wall = obj_by_name("Seitenwand links" if side == "L" else "Seitenwand rechts")
    bm = wall.modifiers.new("Fenster", "BOOLEAN")
    bm.operation, bm.object, bm.solver, bm.use_self = 'DIFFERENCE', c, 'EXACT', True  # use_self: Schnittkoerper ueberlappen sich


# ============================================================
# DECKE, WÄNDE, FUSSLEISTEN
# ============================================================

for n, loc, dim in (("Decke", (0, 2, 13.45), (32.9, 38, 0.5)), ("Rueckwand hinten", (0, 20.75, 6.6), (32.9, 0.5, 13.2)), ("Vorderwand", (0, -17.25, 6.6), (32.9, 0.5, 13.2))):
    bpy.ops.mesh.primitive_cube_add(location=loc); o = C.active_object; o.name = n; o.dimensions = dim; o.data.materials.append(wall_material)

# 18 cm hoch, 6 cm vor der Wand; abgerundete Kanten als ruhiger Bodenabschluss.
skirting_material = simple_material("Fussleisten Naturstein", (0.48, 0.43, 0.35, 1), 0.62)
skirting_collection = sammlung("Fussleisten")
for name, location, dimensions in (
        ("Fussleiste links", (-15.72, 1.75, 0.09), (0.06, 37.5, 0.18)),
        ("Fussleiste rechts", (15.72, 1.75, 0.09), (0.06, 37.5, 0.18)),
        ("Fussleiste Vorderwand", (0, -16.97, 0.09), (31.38, 0.06, 0.18)),
        ("Fussleiste Rueckwand", (0, 20.47, 0.09), (31.38, 0.06, 0.18))):
    skirting = add_box(name, location, dimensions, skirting_material, 0.008)
    link(skirting, skirting_collection)


# ============================================================
# HIMMEL UND SONNE
# ============================================================

# Himmel: für die Kamera sichtbar, als Beleuchtung zurückhaltend.
if scene.world is None:
    scene.world = D.worlds.new("World")
scene.world.use_nodes = True
nt = scene.world.node_tree; nt.nodes.clear()
out, bg, sky, lp, mul = (nt.nodes.new(t) for t in ("ShaderNodeOutputWorld", "ShaderNodeBackground", "ShaderNodeTexSky", "ShaderNodeLightPath", "ShaderNodeMath"))
sky.sky_type = 'MULTIPLE_SCATTERING' if 'MULTIPLE_SCATTERING' in sky.bl_rna.properties['sky_type'].enum_items else 'NISHITA'
sky.sun_disc, sky.sun_elevation, sky.sun_rotation = False, math.radians(38), math.radians(90)
mul.operation = 'MULTIPLY_ADD'; mul.inputs[1].default_value = 0.25; mul.inputs[2].default_value = 0.4
for a, b_ in ((lp.outputs["Is Camera Ray"], mul.inputs[0]), (sky.outputs[0], bg.inputs["Color"]), (mul.outputs[0], bg.inputs["Strength"]), (bg.outputs[0], out.inputs[0])): nt.links.new(a, b_)

# Zurückhaltendes Tageslicht flach durch die +X-Fenster: wenig direkte Energie, weiche Schatten.
SUNDIR = Vector((-0.8, 0.22, -0.56)).normalized()
sun_data = D.lights.new("Sonne", type="SUN")
sun_data.energy = 5.5
sun_data.angle = math.radians(3.0)
sun_data.color = (1.0, 0.82, 0.66)
sun = D.objects.new("Sonne", sun_data)
C.collection.objects.link(sun)
sun.rotation_euler = SUNDIR.to_track_quat('-Z', 'Y').to_euler()
# Die bisherigen Flächenlichter neben der Sonne dimmen.
for o in D.objects:
    if o.type == 'LIGHT' and o.name != "Sonne": o.data.energy *= 0.35

materialien.museumsboden(floor_material, floor_obj)


# ============================================================
# DIE FÜNF MATHEMATISCHEN EXPONATE IN DEN NISCHEN
# ============================================================

scol = sammlung("Nischenexponate")
sierpinski_bronze = simple_material("Sierpinski Bronze", (.40, .085, .018, 1), .26, .78)
exponate = ("Costa", "Henneberg", "Sierpinski-Pyramide", "Cobra", "Double Trefoil")
# Granitflächen aus dem Hauptaufbau ziehen in ihre Nische um.
granit_exponate = {"Costa": costa_skulptur, "Henneberg": henneberg, "Cobra": cobra,
                   "Double Trefoil": double_trefoil}
# Costa-Fläche aufgerichtet: Man blickt frontal in die Öffnung des oberen Endes und durch den Tunnel.
NISCHENDREHUNG = {"Costa": (math.radians(82), 0, math.radians(-12))}
plaketten = ausstattung.Plaketten()


def nischenexponat(index, name, x, y=18.2, pedestal_height=1.1):
    if name in granit_exponate:
        solid = granit_exponate[name]
        link(solid, scol)
        modifier = solid.modifiers.new("Subdivision", "SUBSURF")
        modifier.levels, modifier.render_levels = 1, 2
        C.view_layer.update()
        uniform_scale = 3.0 / max(solid.dimensions)
        solid.scale = (uniform_scale,) * 3
        C.view_layer.update()
        solid.rotation_euler = NISCHENDREHUNG.get(name, (0, 0, 0))
        solid.location = (x, y, 0)
    else:
        mesh = D.meshes.new(name + " Mesh")
        bm = bmesh.new()
        sierpinski.streben_in_bmesh(bm, 4, .018, 8)
        bm.to_mesh(mesh); bm.free()
        solid = D.objects.new(name, mesh); scol.objects.link(solid)
        C.view_layer.update()
        uniform_scale = 3.25 / max(solid.dimensions)
        solid.scale = (uniform_scale,) * 3
        C.view_layer.update()
        solid.location = (x, y, 0)
        solid.rotation_euler = (0, 0, 0)
        mesh.materials.append(sierpinski_bronze)
    # Mit der Unterkante genau auf die Deckplatte setzen; der Ursprung liegt nicht unbedingt in der Mitte.
    C.view_layer.update()
    lowest = min((solid.matrix_world @ Vector(corner)).z for corner in solid.bound_box)
    solid.location.z = pedestal_height + .26 - lowest

    pedestal_base = box(f"Koerpersockel Basis {index}", (x, y, .12), (1.62, 1.48, .24), scol)
    pedestal_base.data.materials.append(plinth_stone)
    pedestal = box(f"Koerpersockel {index}", (x, y, pedestal_height / 2 + .12),
                   (1.28, 1.18, pedestal_height), scol)
    pedestal.data.materials.append(plinth_stone)
    cap = box(f"Koerpersockel Deckplatte {index}", (x, y, pedestal_height + .18),
              (1.58, 1.42, .16), scol)
    cap.data.materials.append(plinth_stone)
    plaketten.sockelschild(f"Nische {index}", name, x, y - .59, pedestal_height / 2 + .12)

    light_data = D.lights.new(f"Koerperlicht {index}", "SPOT")
    light_data.energy = 1100 if name == "Sierpinski-Pyramide" else 780
    light_data.spot_size = math.radians(28 if name == "Sierpinski-Pyramide" else 34)
    light_data.spot_blend, light_data.color, light_data.shadow_soft_size = .65, (1.0, .78, .52), .35
    light = D.objects.new(f"Koerperlicht {index}", light_data); scol.objects.link(light)
    light.location = (x, y - 3.8, 7.8)
    light.rotation_euler = (Vector((x, y, 2.2)) - light.location).to_track_quat('-Z', 'Y').to_euler()

    if name == "Sierpinski-Pyramide":
        target = Vector((x, y, solid.location.z + .25))
        for suffix, location, energy, color, angle in (
                ("Front", (x - 1.45, y - 2.45, 3.75), 440, (1.0, .70, .42), 25),
                ("Kante", (x + 1.25, y + .75, 4.35), 560, (.58, .72, 1.0), 22)):
            fill_data = D.lights.new(f"Sierpinski {suffix}", "SPOT")
            fill_data.energy, fill_data.color = energy, color
            fill_data.spot_size, fill_data.spot_blend = math.radians(angle), .62
            fill_data.shadow_soft_size = .18
            fill = D.objects.new(f"Sierpinski {suffix}", fill_data)
            scol.objects.link(fill)
            fill.location = location
            fill.rotation_euler = (target - fill.location).to_track_quat('-Z', 'Y').to_euler()


for index, (name, x) in enumerate(zip(exponate, NICHE_XS), 1):
    nischenexponat(index, name, x)

# Geschlossene Museumswand gegenüber den Arkaden; sichtbar in der zweiten Hälfte des Orbits.
WALL_Y = -16.96  # Innenseite der Vorderwand
ausstattung.wandteppich(plaketten, WALL_Y, hall_height)


# ============================================================
# KASSETTENDECKE MIT OBERLICHT
# ============================================================

ccol = sammlung("Kassettendecke")
# Das Raster füllt den Innenraum genau: x zwischen den Seitenwänden (±15,75), y von der Vorderwand (-16,96)
# bis zur Arkadenwand (17), damit kein Feld von einer Wand angeschnitten wird.
NX, NY, ZD = 10, 10, 13.2  # Felder, Unterkante der Decke
CEILING_X_MIN, CEILING_X_MAX, CEILING_Y_MIN, CEILING_Y_MAX = -15.75, 15.75, -16.96, 17.0
X0, Y0 = CEILING_X_MIN, CEILING_Y_MIN
DX, DY = (CEILING_X_MAX - CEILING_X_MIN) / NX, (CEILING_Y_MAX - CEILING_Y_MIN) / NY  # Feldgröße
bm = bmesh.new()
def bx(c, sz): bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*sz, 1)))
BEAM, EDGE_BEAM, BEAM_DROP = 0.14, 0.26, 0.20  # Breite der Balken, Breite der Randbalken an den Wänden, Balkenhöhe
for i in range(NX + 1):  # Balken laengs
    edge = i in (0, NX)
    inward = (EDGE_BEAM / 2 - 0.01) * (1 if i == 0 else -1) if edge else 0.0
    bx((X0 + i * DX + inward, Y0 + NY * DY / 2, ZD - BEAM_DROP / 2), (EDGE_BEAM if edge else BEAM, NY * DY, BEAM_DROP))
for j in range(NY + 1):  # Balken quer
    edge = j in (0, NY)
    inward = (EDGE_BEAM / 2 - 0.01) * (1 if j == 0 else -1) if edge else 0.0
    bx((X0 + NX * DX / 2, Y0 + j * DY + inward, ZD - BEAM_DROP / 2), (NX * DX, EDGE_BEAM if edge else BEAM, BEAM_DROP))
SKY = {(i, j) for i in (4, 5) for j in (4, 5)}                                                  # Felder des Oberlichts
for i in range(NX):
    for j in range(NY):
        if (i, j) in SKY: continue
        # Moderne Ruhe: glatte, tiefe Putzfelder mit nur einer feinen Holzeinlage statt Zierrahmen und Mittelblock.
        cx, cy = X0 + (i + .5) * DX, Y0 + (j + .5) * DY; fx, fy = DX - 0.62, DY - 0.62
        for dx, dy, sx, sy in ((0, fy / 2, fx, .035), (0, -fy / 2, fx, .035), (fx / 2, 0, .035, fy), (-fx / 2, 0, .035, fy)): bx((cx + dx, cy + dy, ZD - 0.015), (sx, sy, 0.03))
ceiling_wood = materialien.eichenholz("Kassettendecke Eichenholz", (0.8, 24, 24))
me = D.meshes.new("Kassettendecke"); bm.to_mesh(me); bm.free(); ko = D.objects.new("Kassettendecke", me); ccol.objects.link(ko); me.materials.append(ceiling_wood)
# Die Felder zwischen den Balken sind warm weißer Putz.
ceiling_plaster = simple_material("Deckenputz", (0.80, 0.76, 0.68, 1), 0.88)
obj_by_name("Decke").data.materials.clear()
obj_by_name("Decke").data.materials.append(ceiling_plaster)

# Fensterbänke aus Eiche statt Stein; Maserung längs der Fensterbreite (Y).
sill_wood = materialien.eichenholz("Fensterbank Eichenholz", (24, 0.8, 24))
for obj in fcol.objects:
    if obj.type == 'MESH' and "Fensterbank" in obj.name:
        obj.data.materials.clear()
        obj.data.materials.append(sill_wood)
sw, sh = 2 * DX - 0.32, 2 * DY - 0.32
bpy.ops.mesh.primitive_plane_add(size=1, location=(X0 + 5 * DX, Y0 + 5 * DY, ZD - 0.02), rotation=(math.pi, 0, 0)); sk = C.active_object; sk.name = "Oberlicht"; sk.scale = (sw, sh, 1); link(sk, ccol)
sk.data.materials.append(materialien.emission_material("Oberlicht", (1.0, 0.94, 0.82, 1), 7.0))


# ============================================================
# MÖBEL UND SONNENSTRAHLEN
# ============================================================

bcol = ausstattung.museumsbaenke()
ausstattung.eckhocker(bcol)

# Pro Fenster der Sonnenseite ein Lichtschacht (Volumen-Quader entlang der Sonnenrichtung).
vm = materialien.dunst()
LEN = 10.0
for i, y in enumerate(YS):
    o = box(f"Lichtschacht {i + 1}", Vector((16.0, y, (Z0 + ZA) / 2)) + SUNDIR * LEN / 2, (LEN, W - 0.3, ZA - Z0 - 0.3), fcol)
    o.rotation_euler = SUNDIR.to_track_quat('X', 'Z').to_euler(); o.data.materials.append(vm); o.visible_shadow = False; o.display_type = 'WIRE'
scene.cycles.volume_bounces = 0


# ============================================================
# ZWEI HAUPTWERKE GEMEINSAM INSZENIEREN
# ============================================================

# Beide Minimalflaechen stehen als Paar auf getrennten Sockeln; die Kamera erfasst beide.
SK = 0.58
main_works = (kusner, s41)
for work in main_works:
    work.scale = (SK,) * 3
    work.location.z += 0.80 - (work.location.z + min(v[2] for v in work.bound_box) * SK)
    modifier = work.modifiers.new("Subdivision", "SUBSURF")
    modifier.levels, modifier.render_levels = 1, 2
for n in ("Sockel unten", "Sockel oben", "S41 Sockel unten", "S41 Sockel oben"):
    obj_by_name(n).scale.x *= 0.6
    obj_by_name(n).scale.y *= 0.6
plaketten.sockelschild("Kusner", "Kusner", -EXHIBIT_X, -1.44, 0.30, 1.2, 0.26)
plaketten.sockelschild("S41", "S41", EXHIBIT_X, -1.44, 0.30, 1.2, 0.26)

work_centers = [work.location.z + (min(v[2] for v in work.bound_box) +
                                   max(v[2] for v in work.bound_box)) * SK / 2
                for work in main_works]
ZC = sum(work_centers) / len(work_centers)


# ============================================================
# KAMERA: 360°-ORBIT UM DIE BEIDEN HAUPTWERKE
# ============================================================

bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, ZC))
target = C.object
target.name = "Kamera Ziel"

bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
orbit = C.object
orbit.name = "Kamera Orbit"

camera_data = D.cameras.new("Museumskamera")
camera = D.objects.new("Museumskamera", camera_data)
C.collection.objects.link(camera)
# Die Bahn liegt innerhalb der seitlichen Säulenreihe. Bei größerem Radius
# schnitt die Kamera um 75°/285° durch eine Säule und zeigte nur deren Oberfläche.
# Die kürzere Brennweite erhält dabei ungefähr denselben Bildausschnitt.
camera.location = (0, -12.0, ZC + 0.25)
camera.data.lens = 29
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


# ============================================================
# MASSSTAB UND AUSSENWELT
# ============================================================

# Raum und Kunstwerke um 10 Prozent verkleinern; Möbel bleiben im Originalmaß.
# Nur Wurzelobjekte verändern, damit Kinder nicht doppelt skaliert werden.
MUSEUM_SIZE_FACTOR = 0.90
for obj in scene.objects:
    if obj.parent is not None or obj.type == 'CAMERA' or obj.name == 'Kamera Orbit':
        continue
    obj.location *= MUSEUM_SIZE_FACTOR
    if bcol not in obj.users_collection:
        obj.scale *= MUSEUM_SIZE_FACTOR
    else:
        # Möbel einschließlich der Bank-Kindobjekte einmalig um 10 % vergrößern.
        obj.scale *= 1.10
C.view_layer.update()

ausstattung.aussengarten()


# ============================================================
# GEWÄHLTES GPU-PRESET
# ============================================================

rendering.setup_cycles()
rendering.preset_anwenden(einstellungen.RENDER_PRESET)
scene.frame_set(scene.frame_start)
for screen in D.screens:
    for area in screen.areas:
        if area.type == "VIEW_3D":
            area.spaces.active.region_3d.view_perspective = "CAMERA"
print("Museum bereit (" + ("PNG-Bildfolge" if MAKE_VIDEO else "Testbild") + "). F12: Bild; Strg+F12: Animation.")
print("Renderausgabe: " + scene.render.filepath)
