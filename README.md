# Museum Studio

Museum Studio erzeugt mit Blender eine virtuelle Museumsszene mit zwei mathematischen Granitskulpturen: der Kusner-Fläche für `p=7` und der nichtorientierbaren Minimalfläche `S41_7_5`. In fünf Wandnischen stehen außerdem mathematische Exponate: die Costa-Fläche, die Henneberg-Fläche (`m=5`), die Cobra-Fläche (`m=5`, `t=1`) und das Double Trefoil (`S41_5_3`) – alle aus Granit – sowie die bronzene Sierpiński-Pyramide. Alle Sockel tragen eine Tafel mit Messingschrift (Name und Parameter). Eine lokale Desktopoberfläche steuert Material, Größe, Kamerafahrt, Renderqualität und Ausgabe. Animationen werden zunächst als PNG-Bildfolge gerendert und anschließend mit FFmpeg zu einem MP4 zusammengefügt.

## Voraussetzungen

- Windows
- Node.js ab Version 22 und npm; Electron wird mit `npm install` lokal installiert
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
npm install
npm start
```

Falls PowerShell das Laden von `npm.ps1` blockiert, kann direkt die Windows-Befehlsdatei verwendet werden:

```powershell
npm.cmd start
```

Der Startbefehl öffnet Museum Studio als Electron-Desktop-App. Es gibt keinen HTTP-Server, keinen Port und keinen separaten Browser-Modus. Die Oberfläche kommuniziert über eine schmale IPC-Schnittstelle mit der Node.js-Auftragsverwaltung; Modelle und Bilder werden über das lokale Electron-Protokoll geladen. Beim Schließen werden die zugehörigen Blender-Prozesse beendet.

## Tests

`npm test` prüft Validierung und die serverlose Auftragsverwaltung. Ist Blender installiert (oder `MUSEUM_BLENDER` gesetzt), prüft er außerdem die gemeinsame Sierpiński-Geometrie.

Die schnellen Tests können einmalig als Pre-Commit-Hook aktiviert werden:

```powershell
npm run hooks:install
```

Danach verhindert Git einen Commit, wenn `npm test` fehlschlägt. Der langsamere vollständige Test mit Blender und FFmpeg bleibt bewusst eine separate Prüfung:

```powershell
$env:MUSEUM_INTEGRATION = '1'
npm test
Remove-Item Env:MUSEUM_INTEGRATION
```

Die Electron-Oberfläche und ihre sichere IPC-Anbindung werden separat in einem unsichtbaren Testfenster geprüft:

```powershell
npm run test:electron
```

Die Integrationstests verwenden eigene temporäre Ordner und lassen vorhandene Renderausgaben unangetastet. Electron verwendet ein isoliertes Fenster ohne Node.js-Zugriff der Oberfläche. Ein Installer beziehungsweise eine verteilbare EXE ist noch nicht Bestandteil des Projekts.

## Kommandozeilenaufrufe

### Museum Studio starten

```powershell
npm start
```

### Blender direkt über die Kommandozeile rendern

Die gewünschte Konfiguration wird über `MUSEUM_CONFIG` übergeben. Ein Testbild lässt sich so rendern:

```powershell
$env:MUSEUM_CONFIG = (Resolve-Path ".\Render\kusner_p7_granit_museum\test-settings.json")
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
    --background `
    --factory-startup `
    --python-exit-code 1 `
    --python .\museum\scene.py `
    --render-frame 1
```

Eine Animation mit der vorhandenen `settings.json` wird so gestartet:

```powershell
$env:MUSEUM_CONFIG = (Resolve-Path ".\Render\kusner_p7_granit_museum\settings.json")
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
    --background `
    --factory-startup `
    --python-exit-code 1 `
    --python .\museum\scene.py `
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
3. Mit **Animation erstellen** fehlende PNG-Einzelbilder rendern und anschließend automatisch das MP4-Video erzeugen.
4. Das fertige Video über **Video herunterladen** öffnen oder speichern.

Die Formularwerte werden im `localStorage` der Oberfläche gespeichert und beim nächsten Öffnen wiederhergestellt.

Beim ersten Testbild startet Museum Studio einen Blender-Prozess und baut darin die komplette Szene auf. Dieser Prozess bleibt anschließend im Hintergrund geöffnet. Weitere Testbilder – etwa beim Drehen des Kamerarads – ändern nur Kamera und Rendereinstellungen und müssen die Szene nicht erneut erzeugen. Deshalb ist das erste Bild weiterhin langsamer, die folgenden Perspektiven reagieren aber deutlich schneller. Das GLB-Modell wird unabhängig davon erst beim Öffnen der 3D-Vorschau exportiert. Änderungen an Boden, Skulpturgröße oder Granitdicke starten den Worker automatisch neu; vor einer Animation wird er beendet, damit der GPU-Speicher vollständig für den Animationsrender verfügbar ist.

Über **3D-Vorschau** oberhalb des Bildes kann das Museum ohne erneutes Rendering flüssig in der App gedreht und gezoomt werden. Beim ersten Öffnen dieser Ansicht exportiert Blender dafür ein lokales GLB-Modell. Der horizontale Blickwinkel wird beim Loslassen automatisch mit dem Kamerarad synchronisiert. **Testbild rendern** verwendet dadurch immer die zuletzt gewählte Perspektive. Die 3D-Vorschau ist bewusst vereinfacht; prozedurale Materialien, Volumenlicht und OptiX-Denoising erscheinen erst im Renderbild.

Nur im 3D-Modus rendert Three.js außerdem ohne Cycles direkt in der App: **PNG speichern** erzeugt ein Bild in der gewählten Auflösung, **WebM aufnehmen** zeichnet die eingestellte Kamerafahrt mit Dauer, Bildrate und Umlaufwinkel auf. Das WebM-Format kann bei Bedarf anschließend mit FFmpeg in MP4 umgewandelt werden.

## Parameter

| Parameter | Bedeutung |
| --- | --- |
| Boden | Marmor- oder Parkettboden |
| Skulpturgröße | Gemeinsame Skalierung der beiden großen Granitskulpturen |
| Granitdicke | Stärke der mittels Solidify erzeugten Oberflächen |
| Dauer | Länge der Animation in Sekunden |
| Bilder/Sekunde | Bildrate des Renders und des MP4-Videos |
| Startposition/Grad | Startpunkt auf der kreisförmigen Kamerafahrt und Perspektive des Testbilds |
| Umlauf/Grad | Drehwinkel der Kamerafahrt |
| Breite/Höhe | Ausgabeauflösung in Pixeln |
| Ausgabeordner | Ziel für Einstellungen, Bilder, Frames, Logs und Videos |

Für MP4 müssen Breite und Höhe gerade Zahlen sein. Die Anzahl der Animationsbilder ergibt sich aus `FPS × Dauer`.

Auf der geschlossenen Museumswand gegenüber den Arkaden hängt ein großer, gewebter Wandteppich mit einer kupfer- und petrolfarbenen Mandelbrot-Welt. Das Motiv liegt als Projekt-Asset unter `assets/mandelbrot_tapestry.png`.

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
├── frames\              Testbilder und PNG-Einzelbilder der Animation
├── logs\                Blender- und FFmpeg-Ausgaben
├── settings.json        Einstellungen der Animation
├── test-settings.json   Einstellungen des Testbilds
└── museum_*.mp4         Fertige Videos
```

PNG-Frames bleiben erhalten, wenn ein Render abgebrochen wird. Eine Animation kann mit identischen Einstellungen fortgesetzt werden. Werden Szenenparameter verändert, sollte ein neuer Ausgabeordner gewählt werden; andernfalls schützt das Studio vorhandene Frames vor einer versehentlichen Mischung unterschiedlicher Einstellungen.

## Lokale Möbelbibliothek

`assets/models/` enthält zusätzliche Modelle wie die Marmorbüsten. `assets/library/` enthält die Möbelbibliotheken. `blenderkit_data/` ist ausschließlich der vom Add-on verwaltete Cache und bleibt getrennt sowie von Git ausgeschlossen.

Das Museum verwendet eigene Lederbänke, vier Poly-Haven-Holzhocker und eine leichte Panorama-Parkkulisse. Weitere Möbelmodelle liegen unter `assets/library/`, Vorbereitungsskripte unter `tools/assets/`. Quellen, Lizenzen und Befehle stehen in der [Anleitung zur Asset-Bibliothek](assets/library/README.md).

## Projektdateien

- `package.json` enthält den Startbefehl für die Electron-App und den Testbefehl.
- `test/` enthält die Tests (`*.test.cjs`); `npm test` führt alle Dateien dort aus.
- `studio/launch.cjs` startet Electron mit einer bereinigten Umgebung.
- `studio/jobs.cjs` validiert Einstellungen und verwaltet Blender-/FFmpeg-Aufträge direkt im Hauptprozess, ohne Netzwerkdienst.
- `studio/preload.cjs` stellt ausschließlich freigegebene IPC-Funktionen für die Oberfläche bereit.
- `studio/electron.cjs` öffnet das isolierte Desktopfenster und beendet die zugehörigen Prozesse beim Schließen.
- `studio/blender_worker.py` hält die aufgebaute Szene für aufeinanderfolgende Testbilder in Blender bereit.
- `studio/viewer.js` zeigt das von Blender exportierte GLB-Modell interaktiv mit Three.js an.
- Three.js, OrbitControls und GLTFLoader werden in der festgelegten Version `0.186.1` über jsDelivr geladen. Für die 3D-Vorschau ist deshalb eine Internetverbindung erforderlich.
- `studio/index.html` enthält Benutzeroberfläche und Statusanzeige.
- `museum/scene.py` baut die Blender-Szene auf, erzeugt die Skulptur und konfiguriert Kamera, Materialien und Cycles.
- `museum/weierstrass.py` berechnet die Minimalflächen (Kusner, S41_7_5, Henneberg, Cobra, Double Trefoil) aus ihrer Weierstraß-Darstellung über einem Kreisring; die Formeln stammen von der [Seite zu nichtorientierbaren Minimalflächen](https://eb58.github.io/Non-Orientable-Minimal-Surfaces/).
- `museum/costa.py` berechnet die Costa-Fläche über dem Einheitstorus (Port der Parametrisierung der oben genannten Seite, Endenausschnitt ε = 0,12).
- `museum/sierpinski.py` enthält die gemeinsame Geometrie der Sierpiński-Pyramide. Szene und Entwurfsskript `tools/sierpinski_pyramide.py` verwenden sie gemeinsam.
- `tools/assets/` enthält aktuelle Werkzeuge zur Modellvorbereitung.
- `tools/archive/` enthält frühere beziehungsweise aufgeteilte Hilfsskripte; sie werden vom Studio nicht verwendet.

## Fehlerbehebung

### PowerShell blockiert `npm.ps1`

```powershell
npm.cmd start
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

### Studio beenden

Das Electron-Fenster schließen. Seine Blender-Prozesse werden dabei beendet. Ein laufender Renderauftrag kann vorher über **Abbrechen** gestoppt werden.
