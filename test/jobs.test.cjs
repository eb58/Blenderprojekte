const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {createStudio, validate, frameCount, DEFAULTS} = require('../studio/jobs.cjs');

test('validation and Python-compatible frame counts', () => {
    assert.equal(validate({...DEFAULTS, DURATION: '5,1'}).DURATION, 5.1);
    const invalidSettings = [
        {FPS: 24.5},
        {BODEN: 'x'},
        {THICKNESS: Infinity},
        {OUTPUT_DIR: 'relative'}
    ];
    for (const settings of invalidSettings) {
        assert.throws(() => validate({...DEFAULTS, ...settings}));
    }
    assert.equal(frameCount({FPS: 24, DURATION: 5.1}), 122);
    assert.equal(frameCount({FPS: 1, DURATION: 2.5}), 2);
});

test('job manager has no HTTP server and rejects invalid jobs', async () => {
    const jobs = createStudio();
    try {
        assert.equal(jobs.listen, undefined);
        assert.equal(jobs.status().running, false);
        await assert.rejects(jobs.start('still', {...DEFAULTS, FPS: 0}));
        assert.equal(jobs.mediaPath('arbitrary'), null);
        await jobs.stop();
    } finally {
        await jobs.close();
    }
});

test('real Blender still and FFmpeg encoding through direct job calls', {
    skip: process.env.MUSEUM_INTEGRATION !== '1',
    timeout: 240000
}, async () => {
    const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'museum-ipc-test-'));
    const jobs = createStudio({workDir: path.join(folder, 'worker')});
    const output = path.join(folder, 'output');
    try {
        const settings = {
            ...DEFAULTS,
            BODEN: 'parkett',
            RESOLUTION_X: 64,
            RESOLUTION_Y: 64,
            OUTPUT_DIR: output
        };
        await jobs.start('still', settings);
        let status;
        const deadline = Date.now() + 60000;
        do {
            await new Promise(resolve => setTimeout(resolve, 250));
            status = jobs.status();
        } while (status.running && Date.now() < deadline);

        assert.equal(status.running, false);
        assert.equal(status.code, 0, status.log);
        assert.ok(fs.existsSync(jobs.mediaPath('preview')));
        assert.equal(path.dirname(jobs.mediaPath('preview')), path.join(output, 'frames'));
        await jobs.prepareModel(settings);
        assert.ok(fs.existsSync(jobs.mediaPath('model')));
        const model = fs.readFileSync(jobs.mediaPath('model'));
        const jsonLength = model.readUInt32LE(12);
        const gltf = JSON.parse(model.subarray(20, 20 + jsonLength).toString());
        const park = gltf.materials.find(material => material.name === 'Aussenwelt Parkpanorama');
        const tapestry = gltf.materials.find(material => material.name === 'Mandelbrot Wandteppich');
        assert.ok(park?.emissiveTexture);
        assert.ok(tapestry?.pbrMetallicRoughness?.baseColorTexture);
        assert.ok(gltf.images.some(image => image.name === 'museum_park_panorama'));
        assert.ok(gltf.images.some(image => image.name === 'mandelbrot_tapestry'));
        const floor = gltf.materials.find(material => material.name === 'Polierter Museumsboden');
        assert.equal(floor?.pbrMetallicRoughness?.baseColorTexture?.texCoord, 1);

        const frames = path.join(output, 'frames');
        for (let frame = 1; frame <= 2; frame++) {
            fs.copyFileSync(
                jobs.mediaPath('preview'),
                path.join(frames, `frame_${String(frame).padStart(4, '0')}.png`)
            );
        }
        const videoSettings = {...settings, DURATION: 0.1};
        fs.writeFileSync(
            path.join(output, 'settings.json'),
            JSON.stringify({...videoSettings, MAKE_VIDEO: true, RESUME_RENDER: true})
        );
        await jobs.start('animation_video', videoSettings);
        do {
            await new Promise(resolve => setTimeout(resolve, 100));
            status = jobs.status();
        } while (status.running && Date.now() < deadline);

        assert.equal(status.code, 0, status.log);
        assert.equal(status.video, true);
        assert.ok(fs.statSync(jobs.mediaPath('video')).size > 0);
    } finally {
        await jobs.close();
        fs.rmSync(folder, {recursive: true, force: true});
    }
});

const BLENDER = process.env.MUSEUM_BLENDER || 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe';

test('Sierpiński-Geometrie wird von Szene und Entwurfsskript gemeinsam genutzt', {
    skip: !fs.existsSync(BLENDER) && 'Blender fehlt'
}, () => {
    const root = path.resolve(__dirname, '..');
    for (const file of [path.join('museum', 'scene.py'), path.join('tools', 'sierpinski_pyramide.py')]) {
        const source = fs.readFileSync(path.join(root, file), 'utf8');
        assert.match(source, /import sierpinski/, file);
        assert.doesNotMatch(source, /math\.sqrt\(8 \/ 9\)/, `${file} dupliziert die Pyramidenecken`);
    }
    const {spawnSync} = require('node:child_process');
    const result = spawnSync(BLENDER, [
        '--background', '--factory-startup', '--python-exit-code', '1', '--python-expr',
        'import sys; sys.path.insert(0, "museum"); import sierpinski as s; ' +
        'print("KANTEN", [len(s.kanten(n)) for n in range(5)])'
    ], {cwd: root, encoding: 'utf8', windowsHide: true});
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /KANTEN \[6, 24, 96, 384, 1536\]/);
});

test('Weierstraß-Flächen kommen aus einem gemeinsamen Modul', {
    skip: !fs.existsSync(BLENDER) && 'Blender fehlt'
}, () => {
    const root = path.resolve(__dirname, '..');
    const scene = fs.readFileSync(path.join(root, 'museum', 'scene.py'), 'utf8');
    assert.match(scene, /import weierstrass/);
    assert.doesNotMatch(scene, /def \w*segment_delta/, 'scene.py rechnet die Integration selbst');
    for (const name of ['Kusner p=7', 'S41_7_5', 'Henneberg', 'Cobra', 'Double Trefoil']) assert.ok(scene.includes(`"${name}"`), name);
    const {spawnSync} = require('node:child_process');
    const result = spawnSync(BLENDER, [
        '--background', '--factory-startup', '--python-exit-code', '1', '--python-expr',
        'import sys, math; sys.path.insert(0, "museum"); import weierstrass as w; ' +
        'v, f = w.flaeche(lambda z: (z**12 - 1) / z**8, lambda z: z, 1.8, 2.0, 6, 24, 0.1, 2.0); ' +
        'print("FLAECHE", len(v), len(f), round(max(math.dist(p, (0, 0, 0)) for p in v), 6))'
    ], {cwd: root, encoding: 'utf8', windowsHide: true});
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /FLAECHE 175 144 [\d.]+/);
    const radius = Number(/FLAECHE \d+ \d+ ([\d.]+)/.exec(result.stdout)[1]);
    assert.ok(radius > 0 && radius <= 2.0 + 1e-6, `Normierung: ${radius}`);
});

test('Costa-Fläche liefert ein endliches, normiertes Netz', {
    skip: !fs.existsSync(BLENDER) && 'Blender fehlt'
}, () => {
    const {spawnSync} = require('node:child_process');
    const result = spawnSync(BLENDER, [
        '--background', '--factory-startup', '--python-exit-code', '1', '--python-expr',
        'import sys, math; sys.path.insert(0, "museum"); import costa; ' +
        'v, f = costa.flaeche(2.0, 0.12, 40, 40); ' +
        'zs = [p[2] for p in v]; ' +
        'print("COSTA", len(v), len(f), round(max(math.dist(p, (0, 0, 0)) for p in v), 6), ' +
        'all(math.isfinite(c) for p in v for c in p), round(sum(zs) / len(zs), 3))'
    ], {cwd: path.resolve(__dirname, '..'), encoding: 'utf8', windowsHide: true});
    assert.equal(result.status, 0, result.stderr);
    const [, count, faces, radius, finite] = /COSTA (\d+) (\d+) ([\d.]+) (\w+)/.exec(result.stdout);
    assert.equal(finite, 'True');
    assert.ok(Number(count) > 800 && Number(faces) > 700, `${count} Punkte, ${faces} Flächen`);
    assert.ok(Math.abs(Number(radius) - 2) < 1e-5, `Normierung: ${radius}`);
});

test('Viewer ordnet jeder Granitfläche der Szene das Granitmaterial zu', () => {
    const root = path.resolve(__dirname, '..');
    const scene = fs.readFileSync(path.join(root, 'museum', 'scene.py'), 'utf8');
    const viewer = fs.readFileSync(path.join(root, 'studio', 'viewer.js'), 'utf8');
    const pattern = /\/([^/\n]*brown granite[^/\n]*)\/\.test\(identity\)/.exec(viewer);
    assert.ok(pattern, 'Granit-Zuordnung im Viewer nicht gefunden');
    const granite = new RegExp(pattern[1]);
    const names = [...scene.matchAll(/granitskulptur\("([^"]+)"/g)].map(match => match[1]);
    assert.ok(names.length >= 5, `Granitflächen in scene.py: ${names}`);
    // Three.js ersetzt Leerzeichen in Knotennamen durch Unterstriche.
    for (const name of names) assert.match(name.toLowerCase().replaceAll(' ', '_'), granite, name);
});

test('3D-Vorschau exportiert auch Textobjekte (Sockelbeschriftungen)', () => {
    const worker = fs.readFileSync(path.join(__dirname, '..', 'studio', 'blender_worker.py'), 'utf8');
    assert.match(worker, /obj\.type in \{[^}]*"FONT"/);
});

test('fertige Frames werden begrenzt ausgeliefert und als vollständig gemeldet', async () => {
    const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'museum-frames-'));
    const jobs = createStudio({workDir: path.join(folder, 'worker')});
    try {
        jobs.state.settings = {...DEFAULTS, OUTPUT_DIR: folder, FPS: 1, DURATION: 2, START_ANGLE: 30, ORBIT_DEGREES: 90};
        fs.mkdirSync(path.join(folder, 'frames'));
        fs.writeFileSync(path.join(folder, 'frames', 'frame_0001.png'), 'x');
        assert.equal(jobs.status().complete, false);
        fs.writeFileSync(path.join(folder, 'frames', 'frame_0002.png'), 'x');
        const status = jobs.status();
        assert.equal(status.complete, true);
        assert.deepEqual(status.orbit, {start: 30, degrees: 90});
        assert.equal(jobs.mediaPath('frame', 2), path.join(folder, 'frames', 'frame_0002.png'));
        for (const index of [0, 3, 1.5, '1', -1, NaN, undefined]) assert.equal(jobs.mediaPath('frame', index), null, String(index));
    } finally {
        await jobs.close();
        fs.rmSync(folder, {recursive: true, force: true});
    }
});

test('Viewer startet im Rundgang und bietet Klick-Navigation, Tasten, Mausrad und Drehen der Bildfolge', () => {
    const viewer = fs.readFileSync(path.join(__dirname, '..', 'studio', 'viewer.js'), 'utf8');
    const page = fs.readFileSync(path.join(__dirname, '..', 'studio', 'index.html'), 'utf8');
    for (const part of ['ArrowLeft', 'KeyW', 'WALK_BLOCKS', 'museum://studio/frame/', 'clickAt', 'goToWork', 'flyTo', 'intersectBox', 'floorMeshes.push', "addEventListener('wheel'", 'PageUp', 'turnAround']) assert.ok(viewer.includes(part), part);
    // OrbitControls.update() setzt per lookAt den Blick; im Rundgang darf es nicht laufen.
    assert.match(viewer, /if \(!walk\.active\) controls\.update\(\)/);
    assert.ok(page.includes('id="viewerWalk"'));
});

test('Content-Security-Policy erlaubt blob: für eingebettete GLB-Texturen', () => {
    // Der GLTF-Lader holt eingebettete Texturen per fetch auf blob:-Adressen; ohne blob: in connect-src bleiben sie weiß.
    const main = fs.readFileSync(path.join(__dirname, '..', 'studio', 'electron.cjs'), 'utf8');
    const connect = /connect-src ([^;]*);/.exec(main);
    assert.ok(connect, 'connect-src fehlt');
    assert.match(connect[1], /\bblob:/);
    assert.ok(!/\*/.test(connect[1]), 'connect-src darf nicht offen sein');
});

test('Der Rundgang ist der Standard, die Übersicht wird per Knopf gewählt', () => {
    const viewer = fs.readFileSync(path.join(__dirname, '..', 'studio', 'viewer.js'), 'utf8');
    // Nach dem Laden des Modells startet der Rundgang; in der Übersicht gibt es keine Pfeiltasten-Drehung mehr.
    assert.match(viewer, /loaded = true;[\s\S]{0,80}if \(!walk\.active\) setWalk\(true\)/);
    assert.match(viewer, /on \? 'Übersicht' : 'Rundgang'/);
    assert.ok(!viewer.includes('zoom * 0.8 * delta'), 'Pfeiltasten dürfen die Übersicht nicht mehr drehen');
});

test('Die Arkadenwand hat kein durchgehendes Sockelband mehr', () => {
    // Es überlappte die Pfeilerbasen in derselben Ebene und flimmerte in Echtzeitansichten.
    const scene = fs.readFileSync(path.join(__dirname, '..', 'museum', 'scene.py'), 'utf8');
    assert.ok(!scene.includes('Arkadengalerie Sockelband'));
    assert.ok(scene.includes('Arkadengalerie Pfeilerbasis'));
});

test('Die Arkaden haben gestufte Steinbögen mit Schlussstein statt runder Röhren', () => {
    const scene = fs.readFileSync(path.join(__dirname, '..', 'museum', 'scene.py'), 'utf8');
    assert.ok(!scene.includes('_Archivolte", "CURVE"'), 'Archivolte darf keine runde Kurve (Röhre) mehr sein');
    for (const part of ['_Archivolte_Innen', '_Archivolte_Aussen', '_Schlussstein', '_Kaempfer_']) {
        assert.ok(scene.includes(part), part);
    }
});

test('Fensterrahmen sind aus hellem, nicht metallischem Holz', () => {
    const scene = fs.readFileSync(path.join(__dirname, '..', 'museum', 'scene.py'), 'utf8');
    const match = /b\.inputs\["Base Color"\]\.default_value = \(([\d.]+), ([\d.]+), ([\d.]+), 1\); b\.inputs\["Metallic"\]\.default_value = ([\d.]+)/.exec(scene);
    assert.ok(match, 'Fensterrahmen-Material nicht gefunden');
    const [red, green, blue, metallic] = match.slice(1).map(Number);
    assert.ok(Math.max(red, green, blue) >= 0.5, 'Holz soll hell sein');
    assert.equal(metallic, 0);
});

test('Die Seitenwände haben ein profiliertes Kranzgesims statt eines Kantholzes', () => {
    const scene = fs.readFileSync(path.join(__dirname, '..', 'museum', 'scene.py'), 'utf8');
    assert.ok(!/add_box\("Gesims (links|rechts)"/.test(scene), 'Gesims darf kein einfacher Quader sein');
    assert.match(scene, /add_cornice\("Gesims links"/);
    assert.match(scene, /add_cornice\("Gesims rechts"/);
});

test('Das Abschlussgesims der Arkadenwand ist ein Kranzgesims', () => {
    const scene = fs.readFileSync(path.join(__dirname, '..', 'museum', 'scene.py'), 'utf8');
    assert.ok(!scene.includes('add_box("Arkadengalerie Abschlussgesims"'));
    assert.match(scene, /add_cornice\("Arkadengalerie Abschlussgesims"/);
});

test('Die Arkadenwand hat Quadermauerwerk, kannelierte Pilaster und ein Gurtgesims', () => {
    const scene = fs.readFileSync(path.join(__dirname, '..', 'museum', 'scene.py'), 'utf8');
    for (const part of ['ashlar_material(', 'ShaderNodeTexBrick', 'add_pilaster(f"Pilaster {index}"', 'Arkadengalerie Gurtgesims']) {
        assert.ok(scene.includes(part), part);
    }
    // Der Rückfall der Grundfarbe sorgt dafür, dass die 3D-Vorschau die Wand nicht weiß zeigt.
    assert.match(scene, /bsdf\.inputs\["Base Color"\]\.default_value = light/);
});

test('Der Viewer ersetzt das Material der Arkadenwand durch einen eigenen Stein', () => {
    const viewer = fs.readFileSync(path.join(__dirname, '..', 'studio', 'viewer.js'), 'utf8');
    assert.ok(viewer.includes('arkaden kalkstein'));
    assert.ok(viewer.includes('Three.js Arkadenstein'));
});
