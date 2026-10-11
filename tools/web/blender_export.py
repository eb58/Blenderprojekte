"""In Blender ausführen: baut die Museumsszene auf und exportiert sie als GLB für die Webversion.

Aufruf: blender --background --factory-startup --python blender_export.py -- <ziel.glb>
"""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "museum"))
import vorschau_export  # noqa: E402

ziel = Path(sys.argv[sys.argv.index("--") + 1])
runpy.run_path(str(ROOT / "museum" / "scene.py"))
vorschau_export.exportieren(ziel)
