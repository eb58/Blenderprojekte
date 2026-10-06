"""Gemeinsame Geometrie der Sierpiński-Pyramide für Museumsszene und Entwurfsskript.

Die Kantenberechnung ist reines Python; nur strebenmesh() benötigt Blender.
"""

import math

# Aufrechte reguläre Pyramide: eine Spitze oben, drei Ecken in einer
# waagerechten Grundebene. Frontal entsteht die klare Dreiecksform.
ECKEN = (
    (0.0, 0.0, 1.0),
    (0.0, -math.sqrt(8 / 9), -1 / 3),
    (-math.sqrt(2 / 3), math.sqrt(2 / 9), -1 / 3),
    (math.sqrt(2 / 3), math.sqrt(2 / 9), -1 / 3),
)


def kanten(stufen):
    """Liefert die eindeutigen Kanten aller kleinsten Tetraeder als ((x, y, z), (x, y, z))."""
    gesammelt = set()

    def unterteilen(mitte, massstab, verbleibend):
        if verbleibend:
            for ecke in ECKEN:
                unterteilen(tuple(m + e * massstab / 2 for m, e in zip(mitte, ecke)),
                            massstab / 2, verbleibend - 1)
            return
        punkte = [tuple(m + e * massstab for m, e in zip(mitte, ecke)) for ecke in ECKEN]
        for erster in range(4):
            for zweiter in range(erster + 1, 4):
                start = tuple(round(wert, 6) for wert in punkte[erster])
                ende = tuple(round(wert, 6) for wert in punkte[zweiter])
                gesammelt.add(tuple(sorted((start, ende))))

    unterteilen((0.0, 0.0, 0.0), 1.0, stufen)
    return sorted(gesammelt)


def streben_in_bmesh(bm, stufen, radius, segmente):
    """Fügt jede Kante als achteckiges Zylinderprisma zum bmesh hinzu."""
    import bmesh
    from mathutils import Vector

    for startwerte, endwerte in kanten(stufen):
        start, ende = Vector(startwerte), Vector(endwerte)
        richtung = ende - start
        transformation = richtung.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        transformation.translation = (start + ende) / 2
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segmente,
                              radius1=radius, radius2=radius, depth=richtung.length,
                              matrix=transformation)
