'use strict';

// Stellt die eigenständige Webversion der 3D-Ansicht zusammen: exportiert das Museum mit Blender als GLB
// und kopiert Seite, Viewer-Kern und Bildtexturen in einen Ordner (Standard: Ausgabe/Web).
// Aufruf: npm run web   oder   node tools/web/export.cjs <zielordner>

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const {blenderPath} = require('../../studio/jobs.cjs');

const ROOT = path.resolve(__dirname, '..', '..');
const ziel = path.resolve(process.argv[2] || path.join(ROOT, 'Ausgabe', 'Web'));
const dateien = {
    'index.html': path.join(ROOT, 'web', 'index.html'),
    'web.js': path.join(ROOT, 'web', 'web.js'),
    'museum3d.js': path.join(ROOT, 'studio', 'museum3d.js'),
    'park.png': path.join(ROOT, 'assets', 'bilder', 'museum_park_panorama.png'),
    'mandelbrot.png': path.join(ROOT, 'assets', 'bilder', 'mandelbrot_tapestry.png')
};

fs.mkdirSync(ziel, {recursive: true});
// Die Szene legt beim Aufbau ihren Ausgabeordner an; er soll nicht im Projekt landen.
const arbeit = fs.mkdtempSync(path.join(os.tmpdir(), 'museum-web-export-'));
try {
    const config = path.join(arbeit, 'settings.json');
    fs.writeFileSync(config, JSON.stringify({MAKE_VIDEO: false, OUTPUT_DIR: arbeit}));
    console.log('Blender baut das Museum auf und exportiert museum.glb …');
    const result = spawnSync(blenderPath(), [
        '--background', '--factory-startup', '--python-exit-code', '1',
        '--python', path.join(__dirname, 'blender_export.py'), '--', path.join(ziel, 'museum.glb')
    ], {cwd: ROOT, env: {...process.env, MUSEUM_CONFIG: config}, stdio: 'inherit', windowsHide: true});
    if (result.error) throw result.error;
    if (result.status !== 0) throw Error(`Blender-Export fehlgeschlagen (Exit-Code ${result.status}).`);
} finally {
    fs.rmSync(arbeit, {recursive: true, force: true});
}
for (const [name, quelle] of Object.entries(dateien)) fs.copyFileSync(quelle, path.join(ziel, name));
console.log(`Webversion fertig: ${ziel}`);
console.log(`Lokal ansehen, z. B.: npx serve "${ziel}"`);
