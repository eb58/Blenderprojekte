"""Dauerhafter Blender-Prozess fuer schnelle Testbilder des Museum Studios."""
import json
import math
import os
from pathlib import Path
import runpy
import time
import traceback

import bpy


ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = Path(os.environ["MUSEUM_WORKER_DIR"])
COMMAND = WORK_DIR / "command.json"
READY = WORK_DIR / "ready.json"
MODEL = WORK_DIR / "museum_preview.glb"


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)


def render(command):
    scene = bpy.context.scene
    orbit = bpy.data.objects["Kamera Orbit"]
    orbit.rotation_euler.z = math.radians(float(command["START_ANGLE"]))
    scene.render.resolution_x = int(command["RESOLUTION_X"])
    scene.render.resolution_y = int(command["RESOLUTION_Y"])
    scene.render.resolution_percentage = 100
    scene.render.filepath = command["output"]
    presets[command["RENDER_PRESET"]]()
    scene.frame_set(scene.frame_start)
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)


def export_preview():
    """Exportiert die sichtbare Museumsgeometrie für die Browser-Vorschau."""
    # Bei --factory-startup ist selbst das mit Blender ausgelieferte Kern-Add-on
    # zunächst deaktiviert und der Export-Operator noch nicht registriert.
    bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
    _export_preview_model()


def _export_preview_model():
    bpy.ops.object.select_all(action="DESELECT")
    selected = []
    for obj in bpy.context.scene.objects:
        if (obj.type in {"MESH", "CURVE"} and not obj.hide_render
                and not obj.name.startswith("Lichtschacht")):
            obj.select_set(True)
            selected.append(obj)
    if not selected:
        raise RuntimeError("Keine Geometrie für die 3D-Vorschau gefunden.")
    bpy.context.view_layer.objects.active = selected[0]
    print("3D-Vorschaumodell wird exportiert.", flush=True)
    bpy.ops.export_scene.gltf(
        filepath=str(MODEL),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
    )
    print(f"3D-Vorschaumodell gespeichert: {MODEL}", flush=True)


WORK_DIR.mkdir(parents=True, exist_ok=True)
namespace = runpy.run_path(str(ROOT / "museum" / "scene.py"))
presets = {
    "test": namespace["preset_test"],
    "final_fast": namespace["preset_final_fast"],
    "animation": namespace["preset_animation"],
    "quality": namespace["preset_quality"],
}

# Die Animation verwendet einen Treiber. Fuer Standbilder wird der Winkel direkt
# gesetzt, damit ein neues Testbild keinen erneuten Szenenaufbau braucht.
orbit = bpy.data.objects["Kamera Orbit"]
try:
    orbit.driver_remove("rotation_euler", 2)
except TypeError:
    pass

write_json(READY, {"pid": os.getpid(), "ready": True})
print("Museum-Worker bereit.", flush=True)
last_id = None

while True:
    try:
        if COMMAND.exists():
            command = json.loads(COMMAND.read_text(encoding="utf-8"))
            job_id = command.get("id")
            if job_id and job_id != last_id:
                last_id = job_id
                result_path = WORK_DIR / f"result_{job_id}.json"
                try:
                    if command.get("type") == "model":
                        print("3D-Vorschaumodell wird vorbereitet.", flush=True)
                        export_preview()
                        write_json(result_path, {"ok": True, "output": str(MODEL)})
                        print("3D-Vorschaumodell fertig.", flush=True)
                    else:
                        print(f"Testbild {job_id} wird gerendert.", flush=True)
                        render(command)
                        write_json(result_path, {"ok": True, "output": command["output"]})
                        print(f"Testbild {job_id} fertig.", flush=True)
                except Exception as error:
                    traceback.print_exc()
                    write_json(result_path, {"ok": False, "error": str(error)})
        time.sleep(0.10)
    except KeyboardInterrupt:
        break
    except Exception:
        traceback.print_exc()
        time.sleep(0.5)
