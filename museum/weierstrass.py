"""Minimalflächen aus der Weierstraß-Darstellung über einem Kreisring.

Gleiche Konstruktion wie https://eb58.github.io/Non-Orientable-Minimal-Surfaces/:
Die Fläche entsteht durch Integration von (f(1 - g²)/2, i·f(1 + g²)/2, f·g) dz.
Reines Python; Blender wird nur zum Anlegen des Meshes benötigt.
"""

import cmath
import math


def _schritt(f, g, z0, z1):
    z = (z0 + z1) * 0.5
    dz = z1 - z0
    fz, gz = f(z), g(z)
    x = (fz * (1 - gz * gz) * 0.5 * dz).real
    y = (1j * fz * (1 + gz * gz) * 0.5 * dz).real
    zz = (fz * gz * dz).real
    return (x, y, zz) if all(map(math.isfinite, (x, y, zz))) else (0.0, 0.0, 0.0)


def flaeche(f, g, r1, r2, u_segmente, v_segmente, ueberlappung, massstab):
    """Liefert (Eckpunkte, Flächen) einer zentrierten, auf `massstab` normierten Fläche.

    Die Eckpunkte sind für Blender gedreht: x, -z, y der Weierstraß-Koordinaten.
    """
    u_anzahl, v_anzahl = u_segmente + 1, v_segmente + 1
    radien = [r1 + (r2 - r1) * i / u_segmente for i in range(u_anzahl)]
    winkel = [(2 * math.pi + ueberlappung) * j / v_segmente for j in range(v_anzahl)]
    gitter = [[(0.0, 0.0, 0.0)] * u_anzahl for _ in range(v_anzahl)]

    def addiere(punkt, delta):
        return (punkt[0] + delta[0], punkt[1] + delta[1], punkt[2] + delta[2])

    for i in range(1, u_anzahl):
        gitter[0][i] = addiere(gitter[0][i - 1],
                               _schritt(f, g, complex(radien[i - 1], 0), complex(radien[i], 0)))
    for j in range(1, v_anzahl):
        e0, e1 = cmath.exp(1j * winkel[j - 1]), cmath.exp(1j * winkel[j])
        for i, radius in enumerate(radien):
            gitter[j][i] = addiere(gitter[j - 1][i], _schritt(f, g, radius * e0, radius * e1))

    eckpunkte = normiert([punkt for zeile in gitter for punkt in zeile], massstab,
                         ((0, 1), (2, -1), (1, 1)))
    flaechen = [(j * u_anzahl + i, (j + 1) * u_anzahl + i, (j + 1) * u_anzahl + i + 1,
                 j * u_anzahl + i + 1)
                for j in range(v_anzahl - 1) for i in range(u_anzahl - 1)]
    return eckpunkte, flaechen


def normiert(punkte, massstab, achsen=((0, 1), (1, 1), (2, 1))):
    """Zentriert die Punkte, normiert den größten Abstand auf `massstab` und ordnet die Achsen.

    `achsen` gibt je Ausgabeachse (Quellachse, Vorzeichen) an. Standard: unverändert.
    """
    mitte = tuple(sum(punkt[achse] for punkt in punkte) / len(punkte) for achse in range(3))
    zentriert = [tuple(punkt[achse] - mitte[achse] for achse in range(3)) for punkt in punkte]
    normierung = max(math.sqrt(x * x + y * y + z * z) for x, y, z in zentriert)
    return [tuple(vorzeichen * punkt[quelle] / normierung * massstab for quelle, vorzeichen in achsen)
            for punkt in zentriert]


# --- Die Flächen des Museums, Voreinstellungen wie auf der oben genannten Seite --------------
NAHTUEBERLAPPUNG = 0.10


def kusner(p, massstab):
    """Kusner-Fläche mit p Enden; der Ring endet mit Abstand vor den Polen von f."""
    a = math.sqrt(2 * p - 1)
    b = 2 * a / (p - 1)
    root_span = math.sqrt(b * b + 4)
    inner_pole = ((root_span - b) / 2) ** (1 / p)
    outer_pole = ((root_span + b) / 2) ** (1 / p)
    margin = min(0.24, (outer_pole - inner_pole) * 0.38)

    def f(z):
        return 1j * (a * z**p + 1)**2 / (z**(2 * p) + b * z**p - 1)**2

    def g(z):
        return z**(p - 1) * (z**p - a) / (a * z**p + 1)

    return flaeche(f, g, inner_pole + margin, outer_pole - margin, 70 + round(p * 4),
                   361 + round(p * 40), NAHTUEBERLAPPUNG, massstab)


def s41(m, n, r1, r2, massstab):
    """Familie S41_m_n (S41_7_5; S41_5_3 ist das doppelte Kleeblatt)."""
    def f(z):
        return 1j * (z**n + 1)**2 / z**(m + 1)

    def g(z):
        return z**(m - n) * (z**n - 1) / (z**n + 1)

    return flaeche(f, g, r1, r2, 58, 221, NAHTUEBERLAPPUNG, massstab)


def henneberg(m, massstab):
    phase = (1, 1j, -1, -1j)[(m - 1) % 4]

    def f(z):
        return phase * (z**(2 * m + 2) - 1) / z**(m + 3)

    def g(z):
        return z

    return flaeche(f, g, 1.8, 2.0, 60, 241 + 24 * m, NAHTUEBERLAPPUNG, massstab)


def cobra(m, t, massstab):
    def f(z):
        return t**2 * (z + 1)**2 * (z + 1j / t)**2 / z**(m + 1)

    def g(z):
        return (z**(m - 2) * (z - 1) * (z - 1j * t)
                / (t * (z + 1) * (z + 1j / t)))

    return flaeche(f, g, 1.0, 1.2, 58, 221, NAHTUEBERLAPPUNG, massstab)
