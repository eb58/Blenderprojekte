# Arbeitsanweisungen für Coding Agents

## Geltungsbereich und Sprache

- Diese Datei gilt für das gesamte Repository.
- Antworte dem Benutzer auf Deutsch, sofern er keine andere Sprache verlangt.
- Verwende in Quelltext, Dokumentation und sichtbaren Oberflächentexten korrektes UTF-8 mit deutschen Umlauten. Ändere vorhandene Bezeichner oder technische Schlüssel nicht allein zur sprachlichen Vereinheitlichung.
- Halte Änderungen klein, nachvollziehbar und auf die aktuelle Aufgabe begrenzt. Bewahre nicht zugehörige Änderungen im Arbeitsverzeichnis.

## Projektziel und Architektur

Museum Studio ist eine lokale Windows-Desktop-Anwendung. Electron steuert Blender und FFmpeg ohne HTTP-Server:

- `studio/electron.cjs`: Electron-Hauptprozess, Fenster, lokales `museum://`-Protokoll und IPC.
- `studio/preload.cjs`: schmale, ausdrücklich freigegebene IPC-Schnittstelle.
- `studio/jobs.cjs`: Validierung sowie Lebenszyklus der Blender- und FFmpeg-Aufträge.
- `studio/index.html` und `studio/viewer.js`: Oberfläche und Three.js-Vorschau.
- `studio/blender_worker.py`: langlebiger Blender-Worker für schnelle Vorschaubilder.
- `museum/scene.py`: Aufbau und Rendering der Blender-Szene.
- `tools/assets/`: aktive Werkzeuge zur Asset-Aufbereitung; `tools/archive/` ist nur Archiv.

Behalte diese Trennung bei. Fachlogik und Validierung gehören nicht unnötig in die Oberfläche. Das Projekt soll lokal und serverlos bleiben, solange die Aufgabe nicht ausdrücklich eine andere Architektur verlangt.

## Sicherheit und Daten

- Behalte für den Renderer `nodeIntegration: false`, `contextIsolation: true` und `sandbox: true` bei.
- Erweitere `preload.cjs` und IPC nur um eng begrenzte Funktionen. Validiere Aufrufer und Eingaben im Hauptprozess; reiche keine allgemeinen Datei-, Shell- oder Node-Zugriffe an den Renderer durch.
- Verwende für externe Prozesse Argumentlisten statt zusammengesetzter Shell-Befehle. Behandle Pfade und Formularwerte als nicht vertrauenswürdig.
- Keine Zugangsdaten, Tokens, lokalen Benutzerpfade oder maschinenspezifischen Geheimnisse einchecken.
- Lösche oder überschreibe Renderausgaben, Frames, Modelle und andere Benutzerdaten nicht ohne ausdrücklichen Auftrag. Fortsetzbare Renderläufe und vorhandene Ausgaben müssen geschützt bleiben.

## Abhängigkeiten und Assets

- Nutze Node.js 22 oder neuer und die im Lockfile festgelegten Versionen. Füge Abhängigkeiten nur hinzu, wenn die vorhandenen Plattformmittel nicht sinnvoll ausreichen.
- Bevorzuge – wie in den anderen Projekten dieses Besitzers – lokale beziehungsweise vendorte Assets, wenn das Offline-Verhalten dadurch wesentlich verbessert wird. Dokumentiere unvermeidbare Netzwerkabhängigkeiten.
- Bewahre Quellen und Lizenzen externer Modelle, Bilder und Bibliotheken nachvollziehbar auf.
- `Render/`, `node_modules/`, BlenderKit-Caches, Texturen-Caches sowie Blender-, Video- und sonstige generierte Binärdateien gehören nicht in Git, soweit `.gitignore` sie ausschließt.

## Implementierung

- Folge dem vorhandenen Stil der jeweiligen Datei (CommonJS in `studio/`, Python in `museum/` und `tools/`). Führe keine großflächige Formatierung ohne sachlichen Grund durch.
- Bevorzuge in JavaScript `const` und Arrow Functions. Verwende `let` nur, wenn eine Variable tatsächlich neu zugewiesen wird, und einfache Anführungszeichen für Stringliterale.
- Verwende für plattformübergreifende globale Zugriffe `globalThis` statt `window`, sofern nicht ausdrücklich das Browserfenster gemeint ist.
- Halte Lösungen nach dem KISS-Prinzip so einfach wie möglich, ohne Lesbarkeit, Fehlerbehandlung oder Sicherheit zu opfern.
- Verwende für fachliche Konzepte deutsche Begriffe, sofern dadurch keine bestehenden Schnittstellen, gespeicherten Schlüssel oder etablierten Bezeichner gebrochen werden.
- Halte Module nach Verantwortlichkeit getrennt und vermeide doppelte Konstanten oder voneinander abweichende Berechnungen in JavaScript und Python.
- Änderungen an Einstellungen müssen zusammenhängend geprüft werden: Standardwerte, Validierung, UI, Übergabe an Blender, Persistenz und Dokumentation.
- MP4-Auflösungen müssen gerade Werte haben. Framezahl, FPS und Dauer müssen zwischen Node.js, Blender und FFmpeg konsistent bleiben.
- Lang laufende Blender-/FFmpeg-Prozesse müssen abbrechbar sein und beim Schließen der Anwendung zuverlässig beendet werden. Fehler sollen in Status/Log sichtbar werden und dürfen nicht still verschwinden.
- Halte die Oberfläche auch während rechenintensiver Arbeit bedienbar. Blockiere den Electron-Hauptprozess nicht mit synchroner Langzeitarbeit.

## Arbeitsablauf und Prüfung

1. Lies vor Änderungen die betroffenen Module und ihre Aufrufer sowie die passenden Abschnitte in `README.md`.
2. Schreibe für neues oder geändertes Verhalten passende Tests beziehungsweise passe bestehende Tests im selben Arbeitsgang an. Führe nach Codeänderungen mindestens die relevanten Tests aus:

   ```powershell
   npm.cmd test
   ```

   Unter Windows ist `npm.cmd` robuster als `npm`, falls die PowerShell-Ausführungsrichtlinie `npm.ps1` blockiert.

3. Prüfe Änderungen am Electron-Start oder an IPC zusätzlich mit:

   ```powershell
   node studio/launch.cjs --smoke-test
   ```

4. Führe den vollständigen Blender-/FFmpeg-Integrationstest nur aus, wenn die Änderung diesen Pfad betrifft und die benötigten Programme verfügbar sind:

   ```powershell
   $env:MUSEUM_INTEGRATION = '1'
   npm.cmd test
   Remove-Item Env:MUSEUM_INTEGRATION
   ```

5. Behaupte keine erfolgreiche visuelle, Blender-, GPU- oder FFmpeg-Prüfung, wenn sie nicht tatsächlich ausgeführt wurde. Nenne ausgelassene Prüfungen und den Grund.
6. Aktualisiere `README.md`, wenn sich Voraussetzungen, Bedienung, Befehle, Architektur, Parameter oder Ausgabeformate ändern.
7. Ergänze dauerhaft relevantes Projektwissen in dieser `AGENTS.md`, statt es nur in einer einzelnen Unterhaltung festzuhalten.

## Git-Regeln

- Prüfe vor und nach der Arbeit `git status --short` und unterscheide eigene Änderungen von bereits vorhandenen Änderungen.
- Committe, pushe, veröffentliche oder deploye nur auf ausdrücklichen Wunsch.
- Verwende keine destruktiven Git-Befehle und setze fremde Änderungen nicht zurück.
- Nimm keine großen generierten Dateien oder lokalen Renderergebnisse in Commits auf.
