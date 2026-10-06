"""Lädt die 3D-Modelle von Poly Haven (CC0) nach assets/models/."""
import json, os, urllib.request
from pathlib import Path

MODEL_ROOT = Path(__file__).resolve().parents[2] / 'assets' / 'models'

MODELLE, AUFLOESUNG = ("marble_bust_01",), "2k"
H = {"User-Agent": "museum-build-script/1.0"}  # ohne User-Agent antwortet die API mit 403
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers=H)).read()

def speichern(url, pfad): os.makedirs(os.path.dirname(pfad), exist_ok=True); open(pfad, "wb").write(get(url))

for a in MODELLE:
    info = json.loads(get(f"https://api.polyhaven.com/files/{a}"))["blend"][AUFLOESUNG]["blend"]
    speichern(info["url"], MODEL_ROOT / a / f"{a}.blend")
    for rel, inc in info.get("include", {}).items(): speichern(inc["url"], MODEL_ROOT / a / rel)
    print("geladen:", a)
