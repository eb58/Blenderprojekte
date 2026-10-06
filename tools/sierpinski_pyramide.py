"""Eigenständiger Blender-Entwurf einer beleuchteten Sierpiński-Pyramide.

Verwendung in Blender:
1. Arbeitsbereich "Scripting" öffnen.
2. Diese Datei laden.
3. "Run Script" drücken.

Das Skript ersetzt beim erneuten Ausführen ausschließlich die Sammlung
"Sierpinski Entwurf". Andere Objekte der geöffneten Blender-Datei bleiben
unangetastet.
"""

import math

import bmesh
import bpy
from mathutils import Vector


# Diese Werte können vor dem Ausführen angepasst werden.
REKURSIONSSTUFEN = 4
HOEHE = 4.2
STREBENRADIUS = 0.018
ZYLINDERSEGMENTE = 8
SAMMLUNGSNAME = "Sierpinski Pyramide"


def material(name, farbe, rauheit, metallisch=0.0):
    werkstoff = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    werkstoff.use_nodes = True
    shader = werkstoff.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = farbe
    shader.inputs["Roughness"].default_value = rauheit
    shader.inputs["Metallic"].default_value = metallisch
    return werkstoff


def sammlung_neu_anlegen():
    vorhanden = bpy.data.collections.get(SAMMLUNGSNAME)
    if vorhanden is not None:
        for objekt in list(vorhanden.objects):
            bpy.data.objects.remove(objekt, do_unlink=True)
        bpy.data.collections.remove(vorhanden)
    sammlung = bpy.data.collections.new(SAMMLUNGSNAME)
    bpy.context.scene.collection.children.link(sammlung)
    return sammlung


def kanten_sammeln(stufen):
    """Liefert die eindeutigen Kanten aller kleinsten Tetraeder."""
    ecken = tuple(Vector(punkt) for punkt in (
        (0, 0, 1),
        (0, -math.sqrt(8 / 9), -1 / 3),
        (-math.sqrt(2 / 3), math.sqrt(2 / 9), -1 / 3),
        (math.sqrt(2 / 3), math.sqrt(2 / 9), -1 / 3),
    ))
    kanten = set()

    def unterteilen(mitte, massstab, verbleibend):
        if verbleibend:
            for ecke in ecken:
                unterteilen(mitte + ecke * massstab / 2,
                            massstab / 2, verbleibend - 1)
            return
        punkte = [mitte + ecke * massstab for ecke in ecken]
        for erster in range(4):
            for zweiter in range(erster + 1, 4):
                start = tuple(round(wert, 7) for wert in punkte[erster])
                ende = tuple(round(wert, 7) for wert in punkte[zweiter])
                kanten.add(tuple(sorted((start, ende))))

    unterteilen(Vector(), 1.0, stufen)
    return kanten


def pyramide_erzeugen(sammlung, bronze):
    mesh = bpy.data.meshes.new("Sierpinski-Pyramide Mesh")
    bm = bmesh.new()
    for startwerte, endwerte in kanten_sammeln(REKURSIONSSTUFEN):
        start, ende = Vector(startwerte), Vector(endwerte)
        richtung = ende - start
        transformation = richtung.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        transformation.translation = (start + ende) / 2
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=ZYLINDERSEGMENTE,
            radius1=STREBENRADIUS,
            radius2=STREBENRADIUS,
            depth=richtung.length,
            matrix=transformation,
        )
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(bronze)

    pyramide = bpy.data.objects.new("Sierpinski-Pyramide", mesh)
    sammlung.objects.link(pyramide)
    bpy.context.view_layer.update()
    faktor = HOEHE / pyramide.dimensions.z
    pyramide.scale = (faktor,) * 3
    bpy.context.view_layer.update()
    sockel_oben = 0.84
    pyramide.location.z = sockel_oben - min(
        ecke[2] for ecke in pyramide.bound_box) * faktor - 0.01
    return pyramide


def quader(name, position, abmessungen, werkstoff, sammlung, abrundung=0.0):
    bpy.ops.mesh.primitive_cube_add(location=position)
    objekt = bpy.context.object
    objekt.name = name
    objekt.dimensions = abmessungen
    for alte_sammlung in list(objekt.users_collection):
        alte_sammlung.objects.unlink(objekt)
    sammlung.objects.link(objekt)
    objekt.data.materials.append(werkstoff)
    if abrundung:
        modifier = objekt.modifiers.new("Sanfte Kanten", "BEVEL")
        modifier.width, modifier.segments = abrundung, 3
    return objekt


def licht(name, typ, position, ziel, energie, farbe, sammlung, groesse):
    daten = bpy.data.lights.new(name, typ)
    daten.energy, daten.color = energie, farbe
    if typ == 'AREA':
        daten.shape, daten.size = 'DISK', groesse
    else:
        daten.spot_size, daten.spot_blend = math.radians(groesse), 0.62
    objekt = bpy.data.objects.new(name, daten)
    sammlung.objects.link(objekt)
    objekt.location = position
    objekt.rotation_euler = (Vector(ziel) - objekt.location).to_track_quat('-Z', 'Y').to_euler()
    return objekt


def kamera_anlegen(sammlung):
    daten = bpy.data.cameras.new("Sierpinski Kamera")
    daten.lens = 52
    kamera = bpy.data.objects.new("Sierpinski Kamera", daten)
    sammlung.objects.link(kamera)
    kamera.location = (6.8, -9.5, 4.7)
    ziel = Vector((0, 0, 2.45))
    kamera.rotation_euler = (ziel - kamera.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = kamera


def main():
    if not 0 <= REKURSIONSSTUFEN <= 5:
        raise ValueError("REKURSIONSSTUFEN muss zwischen 0 und 5 liegen.")
    if HOEHE <= 0 or STREBENRADIUS <= 0:
        raise ValueError("HOEHE und STREBENRADIUS müssen positiv sein.")

    sammlung = sammlung_neu_anlegen()
    bronze = material("Sierpinski Bronze", (0.44, 0.09, 0.018, 1), 0.26, 0.78)
    stein = material("Sierpinski Kalkstein", (0.58, 0.45, 0.29, 1), 0.48)
    wand = material("Sierpinski Hintergrund", (0.012, 0.018, 0.015, 1), 0.88)

    pyramide = pyramide_erzeugen(sammlung, wand)
    quader("Sockel Basis", (0, 0, .22), (4.4, 3.4, .44), stein, sammlung, .07)
    quader("Sockel Deckplatte", (0, 0, .64), (3.8, 2.9, .40), stein, sammlung, .05)
    quader("Dunkle Rückwand", (0, 1.7, 3.1), (7.5, .18, 6.2), wand, sammlung)

    ziel = (0, 0, 2.7)
    licht("Hauptlicht", 'SPOT', (-2.6, -3.0, 7.4), ziel,
          1050, (1.0, .68, .40), sammlung, 32)
    licht("Aufhelllicht", 'AREA', (2.8, -2.0, 4.1), ziel,
          420, (.76, .66, .54), sammlung, 2.0)
    licht("Kantenlicht", 'SPOT', (1.8, .9, 6.0), ziel,
          720, (1.0, .45, .22), sammlung, 28)
    kamera_anlegen(sammlung)

    bpy.context.view_layer.objects.active = pyramide
    pyramide.select_set(True)
    for objekt in bpy.context.selected_objects:
        if objekt != pyramide:
            objekt.select_set(False)
    print(f"Sierpiński-Pyramide erzeugt: {4 ** REKURSIONSSTUFEN} Tetraeder, "
          f"{len(kanten_sammeln(REKURSIONSSTUFEN))} eindeutige Streben")


if __name__ == "__main__":
    main()
