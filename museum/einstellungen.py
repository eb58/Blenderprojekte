"""Einstellungen des Szenenaufbaus.

Die Standardwerte gelten beim direkten Ausführen in Blender. Museum Studio
überschreibt sie über die JSON-Datei in der Umgebungsvariablen MUSEUM_CONFIG.
"""
import json
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BODEN = "marmor"  # "parkett" oder "marmor"
RENDER_PRESET = "test"  # "test", "final_fast", "animation", "quality"

# False = Testbild mit F12; True = PNG-Bildfolge mit Strg+F12
MAKE_VIDEO = True

FPS = 24
DURATION = 5
ORBIT_DEGREES = 360
START_ANGLE = 158

SCULPTURE_SCALE = 3.55
THICKNESS = 0.060

OUTPUT_DIR = os.path.join(PROJECT_DIR, "Render", "kusner_p7_granit_museum")
FRAMES_DIR = os.path.join(OUTPUT_DIR, "frames")
# Vorhandene Frames beim erneuten Animationsrendern ueberspringen.
# Fuer eine geaenderte Szene einen neuen OUTPUT_DIR verwenden.
RESUME_RENDER = True

RESOLUTION_X, RESOLUTION_Y = 1280, 800

config_path = os.environ.get("MUSEUM_CONFIG")
if config_path:
    with open(config_path, encoding="utf-8-sig") as config_file:
        config = json.load(config_file)
    for setting in ("BODEN", "RENDER_PRESET", "MAKE_VIDEO", "FPS", "DURATION",
                    "ORBIT_DEGREES", "START_ANGLE", "SCULPTURE_SCALE", "THICKNESS",
                    "OUTPUT_DIR", "RESUME_RENDER", "RESOLUTION_X", "RESOLUTION_Y"):
        if setting in config:
            globals()[setting] = config[setting]
    FRAMES_DIR = config.get("FRAMES_DIR", os.path.join(OUTPUT_DIR, "frames"))

STILL_OUTPUT = os.path.join(OUTPUT_DIR, "kusner_p7_museum_test.png")
ANIMATION_OUTPUT = os.path.join(FRAMES_DIR, "frame_####")
