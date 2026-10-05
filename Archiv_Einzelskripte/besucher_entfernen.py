"""Entfernt die vom Museumsumbau erzeugten Besucher aus der offenen Szene."""
import bpy

visitors = [obj for obj in bpy.data.objects if obj.name.startswith("Besucher ")]
for obj in visitors:
    bpy.data.objects.remove(obj, do_unlink=True)
print(f"{len(visitors)} Besucher-Objekte entfernt. Szene zum Behalten speichern.")
