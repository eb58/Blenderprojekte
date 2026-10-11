# Assets

## Bilder (`bilder/`, in Git)

- `mandelbrot_tapestry.png`: Motiv des Mandelbrot-Wandteppichs an der Vorderwand.
- `museum_park_panorama.png`: Parkkulisse hinter den Fenstern. Eine zusammenhängende Panoramafläche statt einzelner 3D-Bäume verhindert erkennbar wiederholte Bäume.

Die Herkunft beider Bilder ist bisher nicht dokumentiert. Sie wurden am 5. bzw. 6. Oktober 2026 ins Projekt aufgenommen.

## Materialien (`materialien/`, in Git)

- `granit.json`: Node-Baum des polierten Naturgranits der Skulpturen, gelesen von `museum/materialien.py`. Die enthaltene Node-Gruppe heißt „Procedural Brown Granite“. Ein gleichnamiges Material lag im BlenderKit-Cache des Projekts (`procedural-brown-granite`); vermutlich stammt die Definition daher. Quelle und Lizenz sind noch zu bestätigen.

## Möbel (`moebel/`, nicht in Git)

In den vier Raumecken stehen Exemplare des Barhockers [Bar Chair Round 01](https://polyhaven.com/a/bar_chair_round_01) von Dairon Sanchez (Poly Haven, 1K-Texturen). Lizenz: [CC0](https://polyhaven.com/license). Nutzung, Bearbeitung und Weitergabe sind erlaubt, auch kommerziell.

Die Szene lädt `moebel/bar_chair_round_01_asset.blend`. Diese Datei enthält den Hocker mit eingebetteten Texturen. Fehlt sie, im Projektordner neu herunterladen und erzeugen:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\assets\download_hocker.ps1
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup --python-exit-code 1 --python .\tools\assets\prepare_hocker.py
```

Der Download prüft die von Poly Haven gelieferten MD5-Prüfsummen.
