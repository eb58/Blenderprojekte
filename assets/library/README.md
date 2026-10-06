# Möbelbibliothek

## Gartenbäume

Aktuell verwendet der Garten [Pine Ridge](pine_ridge/README.md). [Tree Small 02](https://polyhaven.com/a/tree_small_02) von Rico Cilliers (CC0) bleibt als ungenutzte Alternative erhalten. Die Vorbereitungsskripte liegen unter `tools/assets/`; `prepare_tree.py` ist nur für diese Alternative erforderlich.

Diese Sammlung enthält drei CC0-Modelle von Poly Haven mit 1K-Texturen:

- [Painted Wooden Bench](https://polyhaven.com/a/painted_wooden_bench), Kirill Sannikov: kleine, rustikale Holzbank mit gealtertem rotem Anstrich.
- [Modular Street Seating](https://polyhaven.com/a/modular_street_seating), Stuart Attenborrow: modulare Sitzflächen mit Holz und Metall, einschließlich gerader und gebogener Teile.
- [Bar Chair Round 01](https://polyhaven.com/a/bar_chair_round_01), Dairon Sanchez: historischer Holz-Barhocker mit rundem Sitz. Je ein Exemplar steht in den vier Ecken des Museums.

Lizenz: [Poly Haven CC0](https://polyhaven.com/license). Nutzung, Bearbeitung und Weitergabe sind erlaubt, auch kommerziell. Die Quellenangaben bleiben hier zur Nachvollziehbarkeit erhalten.

## In Blender verwenden

Unter Bearbeiten → Einstellungen → Dateipfade → Asset-Bibliotheken diesen Ordner hinzufügen. Die Dateien `*_asset.blend` enthalten Collection-Assets samt eingebetteter Texturen. Im Asset Browser die Bibliothek auswählen und das gewünschte Asset in die Szene ziehen. Das modulare System enthält mehrere Bauteile, die nach dem Einfügen arrangiert werden können.

Das Museum verwendet zwei selbst modellierte cognacfarbene Lederbänke auf dunklen Stahlkufen. Die [Blendkit-Polsterbank](blendkit_bench/README.md) bleibt eine lokale Alternative (Royalty Free, nicht CC0; Modelldateien nicht in Git). Auch die Poly-Haven-Holzbänke bleiben in der Bibliothek.

## Erneut herunterladen und vorbereiten

Im Projektordner:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\assets\download_furniture.ps1
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup --python-exit-code 1 --python .\tools\assets\prepare_furniture_library.py
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup --python-exit-code 1 --python .\tools\assets\prepare_pine_ridge.py
```

Der Download prüft die von Poly Haven gelieferten MD5-Prüfsummen. Für Three.js müssen ausgewählte Modelle anschließend mit der Museumsszene nach glTF exportiert werden; deren Texturen und UVs sind dafür bereits vorhanden.
