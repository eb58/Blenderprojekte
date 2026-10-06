"""Costa-Fläche über dem Einheitstorus.

Port der Costa-Parametrisierung von
https://eb58.github.io/Non-Orientable-Minimal-Surfaces/ (math.js): Die ℘- und ζ-Funktion
werden über die Jacobi-Thetareihe berechnet. Reines Python; Blender wird nur für das Mesh benötigt.
"""

import cmath
import math

from weierstrass import normiert

Q = math.exp(-math.pi)
E1 = 6.875185818020372
PUNKTIERUNGEN = ((0.0, 0.0), (0.5, 0.0), (0.0, 0.5))


def _theta_ableitungen(z):
    summen = [0j] * 4
    for n in range(4):
        k = 2 * n + 1
        koeffizient = 2 * (-1) ** n * Q ** ((n + 0.5) ** 2)
        sinus, kosinus = cmath.sin(k * z), cmath.cos(k * z)
        summen[0] += koeffizient * sinus
        summen[1] += koeffizient * k * kosinus
        summen[2] += -koeffizient * k ** 2 * sinus
        summen[3] += -koeffizient * k ** 3 * kosinus
    return summen


def zeta(z):
    theta, theta1 = _theta_ableitungen(math.pi * z)[:2]
    return math.pi * (z + theta1 / theta)


def wp(z):
    theta, theta1, theta2 = _theta_ableitungen(math.pi * z)[:3]
    logarithmisch = theta1 / theta
    zweite = theta2 / theta - logarithmisch * logarithmisch
    return -math.pi - math.pi ** 2 * zweite


def punkt(u, v):
    z = complex(u, v)
    z_zeta = zeta(z)
    korrektur = math.pi / (2 * E1) * (zeta(complex(u - 0.5, v)) - zeta(complex(u, v - 0.5)))
    linear = math.pi * z
    verhaeltnis = (wp(z) - E1) / (wp(z) + E1)
    return (
        (-z_zeta + linear + korrektur).real / 2,
        (-1j * (z_zeta + linear + korrektur)).real / 2,
        math.sqrt(2 * math.pi) / 4 * math.log(abs(verhaeltnis)),
    )


def _torusabstand(a, b):
    abstand = abs(a - b)
    return min(abstand, 1 - abstand)


def _torusdifferenz(wert, mitte):
    differenz = wert - mitte
    return differenz - round(differenz)


def _auf_rand(u, v, ausschnitt):
    """Setzt einen Randknoten auf den Kreis mit Radius `ausschnitt` um die nächste Punktierung."""
    nah = min(
        ((pu, pv, _torusdifferenz(u, pu), _torusdifferenz(v, pv)) for pu, pv in PUNKTIERUNGEN),
        key=lambda eintrag: math.hypot(eintrag[2], eintrag[3]))
    faktor = ausschnitt / math.hypot(nah[2], nah[3])
    return (nah[0] + nah[2] * faktor) % 1, (nah[1] + nah[3] * faktor) % 1


def flaeche(massstab, ausschnitt=0.12, u_segmente=160, v_segmente=160):
    """Liefert (Eckpunkte, Vierecke) der Costa-Fläche, zentriert und auf `massstab` normiert.

    Die z-Achse der Fläche bleibt die Höhenachse. Um die drei Enden wird der Torus im
    Abstand `ausschnitt` abgeschnitten.
    """
    knoten = {}
    for zeile in range(v_segmente):
        for spalte in range(u_segmente):
            u, v = spalte / u_segmente, zeile / v_segmente
            if all(math.hypot(_torusabstand(u, pu), _torusabstand(v, pv)) >= ausschnitt
                   for pu, pv in PUNKTIERUNGEN):
                knoten[(zeile, spalte)] = len(knoten)

    def eckpunkt(zeile, spalte):
        return knoten.get((zeile % v_segmente, spalte % u_segmente))

    flaechen, kantenzahl = [], {}
    for zeile in range(v_segmente):
        for spalte in range(u_segmente):
            ecken = [eckpunkt(zeile, spalte), eckpunkt(zeile, spalte + 1),
                     eckpunkt(zeile + 1, spalte + 1), eckpunkt(zeile + 1, spalte)]
            if None in ecken:
                continue
            flaechen.append(tuple(ecken))
            for index in range(4):
                kante = tuple(sorted((ecken[index], ecken[(index + 1) % 4])))
                kantenzahl[kante] = kantenzahl.get(kante, 0) + 1
    rand = {ecke for kante, anzahl in kantenzahl.items() if anzahl == 1 for ecke in kante}

    punkte = []
    for (zeile, spalte), index in sorted(knoten.items(), key=lambda eintrag: eintrag[1]):
        u, v = spalte / u_segmente, zeile / v_segmente
        if index in rand:
            u, v = _auf_rand(u, v, ausschnitt)
        punkte.append(punkt(u, v))
    return normiert(punkte, massstab), flaechen
