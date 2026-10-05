# Museum Studio

Museum Studio erzeugt mit Blender eine virtuelle Museumsszene mit einer mathematischen Granitskulptur. Eine lokale Weboberfläche steuert Material, Größe, Kamerafahrt, Renderqualität und Ausgabe. Animationen werden zunächst als PNG-Bildfolge gerendert und anschließend mit FFmpeg zu einem MP4 zusammengefügt.

## Voraussetzungen

- Windows
- Blender 5.2 unter `C:\Program Files\Blender Foundation\Blender 5.2`
- NVIDIA-Grafikkarte mit OptiX-Unterstützung für die vorgesehenen GPU-Einstellungen
- FFmpeg für die MP4-Erstellung

FFmpeg kann mit WinGet installiert werden:

```powershell
winget install --id Gyan.FFmpeg -e
```

Installation prüfen:

```powershell
ffmpeg -version
```

Museum Studio sucht FFmpeg sowohl im `PATH` als auch in der üblichen WinGet-Installation unter `%LOCALAPPDATA%\Microsoft\WinGet\Packages`.

## Start

Im Projektordner:

```powershell
.\museum_studio.ps1
```

Falls PowerShell die Skriptausführung blockiert, kann das Skript einmalig ohne Änderung der systemweiten Richtlinie gestartet werden:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\museum_studio.ps1
```

Das Skript startet den lokalen Dienst im Hintergrund und öffnet anschließend:

```text
http://127.0.0.1:8765
```

Der Server ist ausschließlich vom eigenen Rechner erreichbar.

## Kommandozeilenaufrufe

### Museum Studio starten

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\museum_studio.ps1
```

### Webserver direkt starten

Mit dem in Blender 5.2 enthaltenen Python:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe" -B .\museum_studio.py
```

Optional kann ein anderer Port gewählt werden:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe" -B .\museum_studio.py --port 9000
```

Die Oberfläche ist dann unter `http://127.0.0.1:9000` erreichbar.

### Blender direkt über die Kommandozeile rendern

Die gewünschte Konfiguration wird über `MUSEUM_CONFIG` übergeben. Ein Testbild lässt sich so rendern:

```powershell
$env:MUSEUM_CONFIG = (Resolve-Path ".\Render\kusner_p7_granit_museum\test-settings.json")
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
    --background `
    --factory-startup `
    --python-exit-code 1 `
    --python .\museum_komplett.py `
    --render-frame 1
```

Eine Animation mit der vorhandenen `settings.json` wird so gestartet:

```powershell
$env:MUSEUM_CONFIG = (Resolve-Path ".\Render\kusner_p7_granit_museum\settings.json")
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
    --background `
    --factory-startup `
    --python-exit-code 1 `
    --python .\museum_komplett.py `
    --render-anim
```

### PNG-Frames manuell als MP4 zusammenfügen

```powershell
ffmpeg -framerate 24 `
    -start_number 1 `
    -i ".\Render\kusner_p7_granit_museum\frames\frame_%04d.png" `
    -c:v libx264 `
    -crf 18 `
    -pix_fmt yuv420p `
    ".\Render\kusner_p7_granit_museum\museum.mp4"
```

Die Zahl hinter `-framerate` muss dem Wert `FPS` in `settings.json` entsprechen. Existiert `museum.mp4` bereits, fragt FFmpeg vor dem Überschreiben nach; mit `-n` kann ein Überschreiben grundsätzlich verhindert werden.

## Bedienung

1. Rechts die gewünschten Szenen- und Rendereinstellungen wählen.
2. Mit **Testbild rendern** Licht, Material und Perspektive prüfen.
3. Mit **Animation rendern** die PNG-Einzelbilder erzeugen.
4. Nach abgeschlossenem Rendern mit **MP4 erstellen** die Bildfolge in ein Video umwandeln.
5. Das fertige Video über **Video herunterladen** öffnen oder speichern.

Die Formularwerte werden im `localStorage` des Browsers gespeichert und beim nächsten Öffnen wiederhergestellt.

## Parameter

| Parameter | Bedeutung |
| --- | --- |
| Boden | Marmor- oder Parkettboden |
| Skulpturgröße | Skalierung der Granitskulptur |
| Granitdicke | Stärke der mittels Solidify erzeugten Oberfläche |
| Dauer | Länge der Animation in Sekunden |
| Bilder/Sekunde | Bildrate des Renders und des MP4-Videos |
| Umlauf/Grad | Drehwinkel der Kamerafahrt |
| Breite/Höhe | Ausgabeauflösung in Pixeln |
| Ausgabeordner | Ziel für Einstellungen, Bilder, Frames, Logs und Videos |

Für MP4 müssen Breite und Höhe gerade Zahlen sein. Die Anzahl der Animationsbilder ergibt sich aus `FPS × Dauer`.

## Render-Presets

Alle Presets verwenden Cycles, GPU-Rendering, adaptives Sampling und OptiX-Denoising.

| Preset | Samples | Verwendung |
| --- | ---: | --- |
| Schneller Test | 16 | Sehr schnelle Vorschau |
| Schnelles Ergebnis | 32 | Bessere Vorschau oder schneller finaler Render |
| Animation | 48 | Empfohlener Kompromiss für Kamerafahrten |
| Hohe Qualität | 128 | Finales Standbild oder hochwertige Animation |

128 Samples sind wegen der deutlich längeren Renderzeit vor allem für finale Standbilder sinnvoll. Für Animationen reichen häufig 48 oder 64 Samples, sofern dunkle Bereiche nicht sichtbar rauschen.

## Ausgabe

Standardmäßig werden die Ergebnisse hier abgelegt:

```text
Render\kusner_p7_granit_museum\
├── frames\              PNG-Einzelbilder der Animation
├── logs\                Blender- und FFmpeg-Ausgaben
├── settings.json        Einstellungen der Animation
├── test-settings.json   Einstellungen des Testbilds
└── museum_*.mp4         Fertige Videos
```

PNG-Frames bleiben erhalten, wenn ein Render abgebrochen wird. Eine Animation kann mit identischen Einstellungen fortgesetzt werden. Werden Szenenparameter verändert, sollte ein neuer Ausgabeordner gewählt werden; andernfalls schützt das Studio vorhandene Frames vor einer versehentlichen Mischung unterschiedlicher Einstellungen.

## Projektdateien

- `museum_studio.ps1` startet den lokalen Dienst und öffnet die Weboberfläche.
- `museum_studio.py` validiert Einstellungen, startet Blender beziehungsweise FFmpeg und stellt die lokale API bereit.
- `museum_studio.html` enthält Benutzeroberfläche und Statusanzeige.
- `museum_komplett.py` baut die Blender-Szene auf, erzeugt die Skulptur und konfiguriert Kamera, Materialien und Cycles.
- `Archiv_Einzelskripte/` enthält frühere beziehungsweise aufgeteilte Hilfsskripte.

## Fehlerbehebung

### PowerShell meldet, dass Skripts deaktiviert sind

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\museum_studio.ps1
```

### FFmpeg wird im Terminal nicht gefunden

Ein neues PowerShell- oder VS-Code-Fenster öffnen und prüfen:

```powershell
Get-Command ffmpeg
ffmpeg -version
```

Die Anwendung kann eine WinGet-Installation auch dann direkt erkennen, wenn das aktuelle Terminal noch einen alten `PATH` verwendet.

### Geänderte Parameter scheinen ignoriert zu werden

- Die Seite mit `Strg+F5` neu laden.
- Prüfen, ob ein alter Renderauftrag noch läuft.
- Für eine geänderte Animation einen neuen Ausgabeordner verwenden.
- Unter **Render-Meldungen** das aktuelle Blender-Log ansehen.

### Ein vorhandener Hintergrunddienst soll beendet werden

```powershell
Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like "*museum_studio.py*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId }
```

Danach kann Museum Studio normal neu gestartet werden.
