"""Lädt die 3D-Modelle für museum_build.py von Poly Haven (CC0) nach Modelle/. Aufruf: python modelle_laden.py"""
import json, os, urllib.request

MODELLE, AUFLOESUNG = ("marble_bust_01",), "2k"
H = {"User-Agent": "museum-build-script/1.0"}  # ohne User-Agent antwortet die API mit 403
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers=H)).read()

def speichern(url, pfad): os.makedirs(os.path.dirname(pfad), exist_ok=True); open(pfad, "wb").write(get(url))

for a in MODELLE:
    info = json.loads(get(f"https://api.polyhaven.com/files/{a}"))["blend"][AUFLOESUNG]["blend"]
    speichern(info["url"], f"Modelle/{a}/{a}.blend")
    for rel, inc in info.get("include", {}).items(): speichern(inc["url"], f"Modelle/{a}/{rel}")
    print("geladen:", a)
