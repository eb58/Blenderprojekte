const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {createStudio, validate, frameCount, framesFolderName, DEFAULTS, VIDEO_DIR} = require('../studio/jobs.cjs');

// Der Szenenaufbau ist auf mehrere Module in museum/ verteilt.
const museumQuelltext = () => {
    const ordner = path.join(__dirname, '..', 'museum');
    return fs.readdirSync(ordner).filter(datei => datei.endsWith('.py')).sort()
        .map(datei => fs.readFileSync(path.join(ordner, datei), 'utf8')).join('\n');
};

test('Renderdaten und Videos liegen gemeinsam im Projektordner Ausgabe', () => {
    const ausgabe = path.join(path.resolve(__dirname, '..'), 'Ausgabe');
    assert.equal(VIDEO_DIR, path.join(ausgabe, 'Videos'));
    assert.equal(path.dirname(validate(DEFAULTS).OUTPUT_DIR), path.join(ausgabe, 'Render'));
    const einstellungen = fs.readFileSync(path.join(__dirname, '..', 'museum', 'einstellungen.py'), 'utf8');
    assert.ok(einstellungen.includes('os.path.join(PROJECT_DIR, "Ausgabe", "Render", "kusner_p7_granit_museum")'));
});

test('jede Einstellungsvariante einer Animation bekommt automatisch einen eigenen Ordner', () => {
    assert.ok(!Object.hasOwn(DEFAULTS, 'OUTPUT_DIR'), 'Ausgabeordner ist keine Einstellung mehr');
    const ordner = validate(DEFAULTS).OUTPUT_DIR;
    assert.match(path.basename(ordner), /^marmor_1280x800_24fps_5s_test_[0-9a-f]{6}$/);
    assert.equal(validate({...DEFAULTS}).OUTPUT_DIR, ordner, 'gleiche Einstellungen setzen denselben Lauf fort');
    assert.equal(validate({...DEFAULTS, OUTPUT_DIR: 'C:\\anderswo'}).OUTPUT_DIR, ordner, 'Ordner kommt nicht vom Aufrufer');
    for (const [key, value] of Object.entries({START_ANGLE: 159, THICKNESS: 0.07, SCULPTURE_SCALE: 4, ORBIT_DEGREES: 180})) {
        assert.notEqual(validate({...DEFAULTS, [key]: value}).OUTPUT_DIR, ordner, key);
    }
    const eigenerOrdner = path.join(os.tmpdir(), 'museum-render');
    assert.equal(path.dirname(validate(DEFAULTS, eigenerOrdner).OUTPUT_DIR), eigenerOrdner);
    const page = fs.readFileSync(path.join(__dirname, '..', 'studio', 'index.html'), 'utf8');
    assert.ok(!page.includes('id="OUTPUT_DIR"'), 'kein Eingabefeld für den Ausgabeordner');
});


test('Animationsframes liegen in einem Ordner mit den Kodierungseinstellungen', () => {
    assert.equal(
        framesFolderName({...DEFAULTS, RESOLUTION_X: 1920, RESOLUTION_Y: 1080, FPS: 30}),
        'frames_1920x1080_30fps_h264_crf18_yuv420p'
    );
});

test('validation and Python-compatible frame counts', () => {
    assert.equal(validate({...DEFAULTS, DURATION: '5,1'}).DURATION, 5.1);
    const invalidSettings = [
        {FPS: 24.5},
        {BODEN: 'x'},
        {THICKNESS: Infinity}
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
    const output = path.join(folder, 'output');
    const jobs = createStudio({workDir: path.join(folder, 'worker'), renderDir: output});
    try {
        const settings = {
            ...DEFAULTS,
            BODEN: 'parkett',
            RESOLUTION_X: 64,
            RESOLUTION_Y: 64
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
        assert.equal(path.dirname(jobs.mediaPath('preview')), path.join(output, 'testbilder'));
        assert.deepEqual(fs.readdirSync(output).sort(), ['testbilder'], 'Testbilder legen keine Animationsordner an');
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

        const videoSettings = {...settings, DURATION: 0.1};
        const variante = validate(videoSettings, output).OUTPUT_DIR;
        const frames = path.join(variante, framesFolderName(videoSettings));
        fs.mkdirSync(frames, {recursive: true});
        for (let frame = 1; frame <= 2; frame++) {
            fs.copyFileSync(
                jobs.mediaPath('preview'),
                path.join(frames, `frame_${String(frame).padStart(4, '0')}.png`)
            );
        }
        fs.writeFileSync(
            path.join(variante, 'settings.json'),
            JSON.stringify({...validate(videoSettings, output), MAKE_VIDEO: true, RESUME_RENDER: true, FRAMES_DIR: frames})
        );
        await jobs.start('animation_video', videoSettings);
        do {
            await new Promise(resolve => setTimeout(resolve, 100));
            status = jobs.status();
        } while (status.running && Date.now() < deadline);

        assert.equal(status.code, 0, status.log);
        assert.equal(status.video, true);
        assert.ok(fs.statSync(jobs.mediaPath('video')).size > 0);
        assert.equal(path.dirname(jobs.mediaPath('video')), VIDEO_DIR);
    } finally {
        await jobs.close();
        fs.rmSync(folder, {recursive: true, force: true});
    }
});

const BLENDER = process.env.MUSEUM_BLENDER || 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe';

test('Der Szenenaufbau ist nach Verantwortlichkeit auf Module verteilt', () => {
    const ordner = path.join(__dirname, '..', 'museum');
    const scene = fs.readFileSync(path.join(ordner, 'scene.py'), 'utf8');
    for (const modul of ['einstellungen', 'rendering', 'materialien', 'bauteile', 'ausstattung']) {
        assert.ok(fs.existsSync(path.join(ordner, `${modul}.py`)), `${modul}.py fehlt`);
        assert.match(scene, new RegExp(`^import ${modul}$`, 'm'), `scene.py nutzt ${modul}.py nicht`);
    }
    // Übernommene Materialdefinitionen sind Assets mit dokumentierter Herkunft, kein Szenencode.
    assert.ok(fs.existsSync(path.join(__dirname, '..', 'assets', 'materialien', 'granit.json')));
    assert.ok(!fs.readdirSync(ordner).some(datei => datei.endsWith('.json')), 'JSON-Daten gehören nach assets/');
    // Die Renderpresets stehen genau einmal und werden vom Worker direkt verwendet.
    const worker = fs.readFileSync(path.join(__dirname, '..', 'studio', 'blender_worker.py'), 'utf8');
    assert.match(worker, /rendering\.preset_anwenden\(/);
    assert.doesNotMatch(museumQuelltext(), /def preset_test/);
});

test('Die Szene nutzt die gemeinsame Sierpiński-Geometrie', {
    skip: !fs.existsSync(BLENDER) && 'Blender fehlt'
}, () => {
    const root = path.resolve(__dirname, '..');
    const scene = fs.readFileSync(path.join(root, 'museum', 'scene.py'), 'utf8');
    assert.match(scene, /import sierpinski/);
    assert.doesNotMatch(scene, /math\.sqrt\(8 \/ 9\)/, 'scene.py dupliziert die Pyramidenecken');
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
    const scene = museumQuelltext();
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
    const scene = museumQuelltext();
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
        const framesFolder = path.join(folder, framesFolderName(jobs.state.settings));
        fs.mkdirSync(framesFolder);
        fs.writeFileSync(path.join(framesFolder, 'frame_0001.png'), 'x');
        assert.equal(jobs.status().complete, false);
        fs.writeFileSync(path.join(framesFolder, 'frame_0002.png'), 'x');
        const status = jobs.status();
        assert.equal(status.complete, true);
        assert.deepEqual(status.orbit, {start: 30, degrees: 90});
        assert.equal(jobs.mediaPath('frame', 2), path.join(framesFolder, 'frame_0002.png'));
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

test('Der Viewer ersetzt das Material der Arkadenwand durch einen eigenen Stein', () => {
    const viewer = fs.readFileSync(path.join(__dirname, '..', 'studio', 'viewer.js'), 'utf8');
    assert.ok(viewer.includes('arkaden kalkstein'));
    assert.ok(viewer.includes('Three.js Arkadenstein'));
});

test('Das Kassettenraster der Decke füllt den Raum genau aus', () => {
    const scene = museumQuelltext();
    const match = /CEILING_X_MIN, CEILING_X_MAX, CEILING_Y_MIN, CEILING_Y_MAX = ([-\d.]+), ([-\d.]+), ([-\d.]+), ([-\d.]+)/.exec(scene);
    assert.ok(match, 'Rasterbereich der Decke nicht gefunden');
    const [xMin, xMax, yMin, yMax] = match.slice(1).map(Number);
    // Innenflächen: Seitenwände bei ±15,75, Vorderwand bei -16,96, Arkadenwand bei 17.
    assert.deepEqual([xMin, xMax, yMin, yMax], [-15.75, 15.75, -16.96, 17]);
    assert.ok(!scene.includes('-16.45, -17.0, 3.29, 3.8'), 'altes, zu großes Raster');
});

test('Die Kassettendecke ist modern: helles Holz, Putzfelder, keine Zierrahmen mit Mittelblock', () => {
    const scene = museumQuelltext();
    assert.ok(scene.includes('Deckenputz'));
    assert.ok(!scene.includes('bx((cx, cy, ZD - 0.03), (0.34, 0.34, 0.06))'), 'kein Mittelblock mehr');
    const match = /wood_ramp\.color_ramp\.elements\[1\]\.color = \(([\d.]+), ([\d.]+), ([\d.]+)/.exec(scene);
    assert.ok(match && Math.max(...match.slice(1).map(Number)) >= 0.5, 'helles Holz erwartet');
});

test('Die Arkadenwand ist modern: Steinplatten, schlichte Nischen mit Lichtkante, keine klassischen Zierelemente', () => {
    const scene = museumQuelltext();
    for (const part of ['ashlar_material(', 'ShaderNodeTexBrick', 'add_niche(f"Nische {index}"', 'Nischen Lichtkante']) {
        assert.ok(scene.includes(part), part);
    }
    for (const klassisch of ['Archivolte', 'Schlussstein', 'Kaempfer', 'add_pilaster', 'Pfeilerbasis', 'Gurtgesims', 'Zwickel']) {
        assert.ok(!scene.includes(klassisch), `${klassisch} passt nicht zu einem modernen Museum`);
    }
});

test('Der Viewer zeichnet die Steinplatten der Arkadenwand mit Fugen', () => {
    const viewer = fs.readFileSync(path.join(__dirname, '..', 'studio', 'viewer.js'), 'utf8');
    assert.ok(viewer.includes('museum-arcade-slabs'));
    assert.ok(viewer.includes('wallPosition'));
});

test('Die Fenster sind schlichte, hohe Rechteckfenster ohne Bogen', () => {
    const scene = museumQuelltext();
    for (const altmodisch of ['Steinbogen', 'Fensterbogen', 'arch(f"a{i}"']) {
        assert.ok(!scene.includes(altmodisch), `${altmodisch} passt nicht zu modernen Fenstern`);
    }
    assert.ok(scene.includes('" Sturz"'));
    const match = /YS, W, Z0, ZA = \[[^\]]+\], ([\d.]+), ([\d.]+), ([\d.]+)/.exec(scene);
    assert.ok(match, 'Fensterabmessungen nicht gefunden');
    const [width, sill, top] = match.slice(1).map(Number);
    assert.ok(top - sill > 2.5 * width, 'hohes, schlankes Format erwartet');
});

test('Zwischen Wand und Decke gibt es keine Leiste oder Gesimse', () => {
    const scene = museumQuelltext();
    for (const leiste of ['add_cornice', 'CORNICE', 'Gesims', 'Kranzgesims']) {
        assert.ok(!scene.includes(leiste), `${leiste} hat in der modernen Raumhülle keinen Platz`);
    }
});


test('Die Fenster sind Glas mit schlankem Titanrahmen, ohne Sprossen und Pfosten', () => {
    const scene = museumQuelltext();
    assert.ok(scene.includes('Fensterglas {side}{i + 1}'));
    assert.ok(scene.includes('Fensterrahmen Titan {side}{i + 1}'));
    const frame = /FRAME_WIDTH = ([\d.]+)/.exec(scene);
    assert.ok(frame && Number(frame[1]) <= 0.08, 'Rahmen soll schlank bleiben');
    assert.match(scene, /titanium_bsdf\.inputs\["Metallic"\]\.default_value = 1\.0/);
    assert.ok(!scene.includes('box("m", (x, y'), 'kein Mittelpfosten');
    // Für Schattenstrahlen ist das Glas durchsichtig, sonst bliebe das Sonnenlicht draußen.
    assert.ok(scene.includes('Is Shadow Ray'));
    const viewer = fs.readFileSync(path.join(__dirname, '..', 'studio', 'viewer.js'), 'utf8');
    assert.ok(viewer.includes('fensterglas') && viewer.includes('fensterrahmen titan'));
});
