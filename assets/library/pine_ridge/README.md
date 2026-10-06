# Pine Ridge

Quelle: https://www.blendkit.com/asset-gallery-detail/ba439aad-ce28-4a2c-93df-64176a3d608e/

Kostenlose Szene unter Blendkit Royalty Free, nicht als Ganzes CC0. Lizenz: https://www.blendkit.com/docs/licenses/

`pine_ridge.blend` ist der Originaldownload mit 1K-Texturen. `prepare_pine_ridge.py` erstellt `pine_ridge_asset.blend`: Gelände und Kiefern werden als Meshobjekte mit gemeinsam genutzten Meshdaten vorbereitet. Kamera, Beleuchtung und die Grashalm-Streuung werden nicht übernommen.

`prepare_pine_ridge_runtime.py` reduziert die gemeinsam genutzten Meshes einmalig auf 8 % und schreibt `pine_ridge_runtime.blend`. Museum Studio lädt ausschließlich diese kleinere Laufzeitbibliothek und platziert sie auf beiden Seiten außerhalb der Fensterfassaden. Nach einer Änderung der Pine-Ridge-Quelldatei werden die beiden Vorbereitungsskripte in dieser Reihenfolge ausgeführt:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python .\tools\assets\prepare_pine_ridge.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python .\tools\assets\prepare_pine_ridge_runtime.py
```

Modelldateien bleiben lokal und sind durch die allgemeinen Blend-Datei-Regeln von Git ausgeschlossen. Vor Weitergabe von Modelldateien oder Veröffentlichung herunterladbarer GLB-Dateien Lizenz prüfen.

Die Laufzeitdatei wird sowohl für Cycles als auch für den GLB-Vorschauexport verwendet. Dadurch muss Blender die hochauflösende 270-MB-Bibliothek nicht bei jedem Start laden und die Waldgeometrie nicht bei jedem Vorschauexport erneut reduzieren.
