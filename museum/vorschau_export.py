"""Exportiert die sichtbare Museumsgeometrie als GLB für die 3D-Ansicht (Studio und Webversion)."""
import bpy


def exportieren(ziel):
    # Bei --factory-startup ist selbst das mit Blender ausgelieferte Kern-Add-on
    # zunächst deaktiviert und der Export-Operator noch nicht registriert.
    bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
    bpy.ops.object.select_all(action="DESELECT")
    selected = []
    for obj in bpy.context.scene.objects:
        if (obj.type in {"MESH", "CURVE", "FONT"} and not obj.hide_render
                and not obj.name.startswith("Lichtschacht")):
            obj.select_set(True)
            selected.append(obj)
    if not selected:
        raise RuntimeError("Keine Geometrie für die 3D-Vorschau gefunden.")
    bpy.context.view_layer.objects.active = selected[0]
    # Die Unterteilung der Skulpturen ist für Cycles gedacht; im Browser genügt das feine Grundnetz mit
    # geglätteten Normalen. Ohne sie wird das Modell etwa viermal kleiner.
    unterteilungen = [modifier for obj in selected for modifier in obj.modifiers
                      if modifier.type == "SUBSURF" and modifier.show_viewport]
    for modifier in unterteilungen:
        modifier.show_viewport = False
    print("3D-Vorschaumodell wird exportiert.", flush=True)
    try:
        bpy.ops.export_scene.gltf(
            filepath=str(ziel),
            export_format="GLB",
            use_selection=True,
            export_apply=True,
            export_cameras=False,
            export_lights=False,
        )
    finally:
        for modifier in unterteilungen:
            modifier.show_viewport = True
    print(f"3D-Vorschaumodell gespeichert: {ziel}", flush=True)
