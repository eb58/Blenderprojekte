const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {createStudio, validate, frameCount, testbildPfad, videoName, DEFAULTS, VIDEO_DIR} = require('../studio/jobs.cjs');

// Der Szenenaufbau ist auf mehrere Module in museum/ verteilt.
const museumQuelltext = () => {
    const ordner = path.join(__dirname, '..', 'museum');
    return fs.readdirSync(ordner).filter(datei => datei.endsWith('.py')).sort()
        .map(datei => fs.readFileSync(path.join(ordner, datei), 'utf8')).join('\n');
};

// Die 3D-Ansicht besteht aus dem gemeinsamen Kern (museum3d.js) und dem Studio-Anschluss (viewer.js).
const viewerQuelltext = () => ['museum3d.js', 'viewer.js']
    .map(datei => fs.readFileSync(path.join(__dirname, '..', 'studio', datei), 'utf8')).join('\n');

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
    assert.match(path.basename(ordner), /^1280x800_24fps_5s_test_[0-9a-f]{6}$/);
    assert.equal(validate({...DEFAULTS}).OUTPUT_DIR, ordner, 'gleiche Einstellungen setzen denselben Lauf fort');
    assert.equal(validate({...DEFAULTS, OUTPUT_DIR: 'C:\\anderswo'}).OUTPUT_DIR, ordner, 'Ordner kommt nicht vom Aufrufer');
    for (const [key, value] of Object.entries({START_ANGLE: 159, ORBIT_DEGREES: 180})) {
        assert.notEqual(validate({...DEFAULTS, [key]: value}).OUTPUT_DIR, ordner, key);
    }
    const eigenerOrdner = path.join(os.tmpdir(), 'museum-render');
    assert.equal(path.dirname(validate(DEFAULTS, eigenerOrdner).OUTPUT_DIR), eigenerOrdner);
    const page = fs.readFileSync(path.join(__dirname, '..', 'studio', 'index.html'), 'utf8');
    assert.ok(!page.includes('id="OUTPUT_DIR"'), 'kein Eingabefeld für den Ausgabeordner');
    // Boden, Skulpturgröße und Granitdicke sind fest (Parkett, 4,55, 0,06) und keine Einstellungen mehr.
    for (const key of ['BODEN', 'SCULPTURE_SCALE', 'THICKNESS']) {
        assert.ok(!Object.hasOwn(DEFAULTS, key), key);
        assert.ok(!page.includes(`id="${key}"`), key);
    }
    const einstellungen = fs.readFileSync(path.join(__dirname, '..', 'museum', 'einstellungen.py'), 'utf8');
    assert.match(einstellungen, /^SCULPTURE_SCALE = 4\.55$/m);
    assert.match(einstellungen, /^THICKNESS = 0\.06$/m);
    assert.ok(!museumQuelltext().includes('BODEN'), 'kein Marmor-/Parkett-Schalter mehr in der Szene');
});


test('Testbilder liegen je Szene in einem Ordner und tragen den Kamerawinkel im Namen', () => {
    const renderDir = path.join(os.tmpdir(), 'museum-render');
    const bild = testbildPfad(validate(DEFAULTS), renderDir);
    assert.equal(path.basename(bild), 'testbild_158grad.png');
    assert.match(path.basename(path.dirname(bild)), /^1280x800_test$/);
    assert.equal(path.dirname(path.dirname(bild)), path.join(renderDir, 'testbilder'));
    assert.equal(path.basename(testbildPfad(validate({...DEFAULTS, START_ANGLE: -12.5}), renderDir)), 'testbild_-12.5grad.png');
    const ordner = settings => path.dirname(testbildPfad(validate(settings), renderDir));
    // Nur was das Testbild verändert, trennt die Szenen; Winkel und Animationswerte nicht.
    for (const [key, value] of Object.entries({START_ANGLE: 200, DURATION: 9, FPS: 30, ORBIT_DEGREES: 90})) {
        assert.equal(ordner({...DEFAULTS, [key]: value}), ordner(DEFAULTS), key);
    }
    for (const [key, value] of Object.entries({RESOLUTION_X: 800, RENDER_PRESET: 'quality'})) {
        assert.notEqual(ordner({...DEFAULTS, [key]: value}), ordner(DEFAULTS), key);
    }
});

test('fertige Videos tragen Variante und Zeitpunkt im Namen', () => {
    const settings = validate(DEFAULTS);
    assert.equal(videoName(settings, new Date(2026, 9, 11, 15, 12, 30)),
        `museum_${path.basename(settings.OUTPUT_DIR)}_2026-10-11_15-12-30.mp4`);
});

test('validation and Python-compatible frame counts', () => {
    assert.equal(validate({...DEFAULTS, DURATION: '5,1'}).DURATION, 5.1);
    const invalidSettings = [
        {FPS: 24.5},
        {DURATION: Infinity},
        {RENDER_PRESET: 'x'}
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
    const videos = path.join(folder, 'videos');
    const jobs = createStudio({workDir: path.join(folder, 'worker'), renderDir: output, videoDir: videos});
    try {
        const settings = {
            ...DEFAULTS,
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
        assert.equal(jobs.mediaPath('preview'), testbildPfad(validate(settings, output), output));
        assert.equal(path.basename(jobs.mediaPath('preview')), 'testbild_158grad.png');
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
        const frames = path.join(variante, 'frames');
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
        assert.equal(path.dirname(jobs.mediaPath('video')), videos, 'Testvideos landen nicht im echten Videoordner');
        assert.ok(path.basename(jobs.mediaPath('video')).startsWith(`museum_${path.basename(variante)}_`));
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
    const viewer = viewerQuelltext();
    const pattern = /\/([^/\n]*brown granite[^/\n]*)\/\.test\(identity\)/.exec(viewer);
    assert.ok(pattern, 'Granit-Zuordnung im Viewer nicht gefunden');
    const granite = new RegExp(pattern[1]);
    const names = [...scene.matchAll(/granitskulptur\("([^"]+)"/g)].map(match => match[1]);
    assert.ok(names.length >= 5, `Granitflächen in scene.py: ${names}`);
    // Three.js ersetzt Leerzeichen in Knotennamen durch Unterstriche.
    for (const name of names) assert.match(name.toLowerCase().replaceAll(' ', '_'), granite, name);
});

test('das fertige Video wird im Explorer gezeigt statt kopiert', () => {
    const studio = name => fs.readFileSync(path.join(__dirname, '..', 'studio', name), 'utf8');
    const preload = studio('preload.cjs');
    assert.match(preload, /showVideo: \(\) => ipcRenderer\.invoke\('museum:show-video'\)/);
    assert.ok(!preload.includes('saveVideo'));
    const main = studio('electron.cjs');
    // Den Pfad bestimmt allein der Hauptprozess.
    assert.match(main, /shell\.showItemInFolder\(video\)/);
    assert.match(main, /studio\.mediaPath\('video'\)/);
    assert.ok(!main.includes('showSaveDialog'));
    const page = studio('index.html');
    assert.ok(page.includes('Im Ordner zeigen') && !page.includes('Video herunterladen'));
});

test('3D-Vorschau und Rendern sind getrennte Arbeitsbereiche', () => {
    const studio = name => fs.readFileSync(path.join(__dirname, '..', 'studio', name), 'utf8');
    const page = studio('index.html');
    const header = /<header>[\s\S]*?<\/header>/.exec(page)[0];
    assert.ok(header.includes('id="mode3d"') && header.includes('id="modeRender"'), 'Umschalter im Kopf');
    assert.match(page, /<body data-modus="render">/);
    // Öffnende Tags des Elements und aller umschließenden Elemente.
    const vorfahren = id => {
        const start = page.lastIndexOf('<', page.indexOf(`id="${id}"`));
        const offen = [];
        for (const match of page.slice(0, start).matchAll(/<(\/?)([a-z0-9]+)\b[^>]*>/gi)) {
            if (match[1]) offen.pop();
            else if (!/^(input|img|br|meta|link)$/i.test(match[2])) offen.push(match[0]);
        }
        return [...offen, page.slice(start, page.indexOf('>', start) + 1)];
    };
    const nurRender = id => vorfahren(id).some(tag => tag.includes('data-nur="render"'));
    for (const element of ['renderStill', 'renderAnimation', 'stop', 'showVideo', 'progress', 'log', 'RENDER_PRESET', 'orbitDial']) {
        assert.ok(nurRender(element), `${element} gehört nur zum Render-Modus`);
    }
    // Der 3D-Export braucht Auflösung, Dauer, Bildrate und Umlauf, deshalb bleiben sie in beiden Modi.
    for (const element of ['RESOLUTION_PRESET', 'DURATION', 'FPS', 'ORBIT_DEGREES']) {
        assert.ok(!nurRender(element), `${element} wird auch in der 3D-Vorschau gebraucht`);
    }
    assert.match(studio('styles.css'), /body\[data-modus="3d"\] \[data-nur="render"\]/);
    assert.match(studio('viewer.js'), /document\.body\.dataset\.modus = is3d \? '3d' : 'render'/);
});

test('3D-Vorschau exportiert auch Textobjekte (Sockelbeschriftungen)', () => {
    const exporter = fs.readFileSync(path.join(__dirname, '..', 'museum', 'vorschau_export.py'), 'utf8');
    assert.match(exporter, /obj\.type in \{[^}]*"FONT"/);
});

test('Smartphone-Fernbedienung: Protokoll wie in Minimalflächen, TV-Erkennung und Anbindung', async () => {
    const web = name => require('node:url').pathToFileURL(path.join(__dirname, '..', 'web', name)).href;
    const protokoll = await import(web('remote-protocol.js'));
    // Nur Befehle, die der gemeinsame Relay kennt, und nur in seinen Grenzen.
    assert.deepEqual(protokoll.sanitizeRemoteCommand({type: 'zoom', delta: -0.05, extra: 1}), {type: 'zoom', delta: -0.05});
    assert.deepEqual(protokoll.sanitizeRemoteCommand({type: 'surface', direction: 1}), {type: 'surface', direction: 1});
    for (const falsch of [{type: 'zoom', delta: 2}, {type: 'surface', direction: 2}, {type: 'shell'}, null]) {
        assert.equal(protokoll.sanitizeRemoteCommand(falsch), null, JSON.stringify(falsch));
    }
    const raum = protokoll.randomToken(6);
    assert.match(raum, /^[a-f0-9]{12}$/, 'Raum-IDs wie vom Relay verlangt');
    assert.deepEqual(protokoll.parseRemoteCredentials(`#${protokoll.remoteCredentialsHash(raum)}`),
        {room: raum, secret: protokoll.PUBLIC_REMOTE_SECRET});
    const anzeige = await import(web('remote-display.js'));
    assert.ok(anzeige.isTv('Mozilla/5.0 (Linux; Android 9; AFTMM Build/PS7292) Silk/112.1'));
    assert.ok(anzeige.isTv('Mozilla/5.0 (Web0S; Linux/SmartTV) AppleWebKit/537.41'));
    assert.ok(!anzeige.isTv('Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/140.0'));
    const kern = fs.readFileSync(path.join(__dirname, '..', 'studio', 'museum3d.js'), 'utf8');
    for (const befehl of ['rotation', 'reset', 'background', 'surface', 'rotate', 'zoom', 'object-translate']) {
        assert.ok(kern.includes(`'${befehl}'`), `museum3d.js verarbeitet ${befehl}`);
    }
    assert.match(fs.readFileSync(path.join(__dirname, '..', 'web', 'web.js'), 'utf8'),
        /createRemoteDisplay\(\{onCommand: viewer\.fernsteuern\}\)/);
});

test('die 3D-Ansicht läuft auch als eigenständige Webseite', () => {
    const datei = (...teile) => fs.readFileSync(path.join(__dirname, '..', ...teile), 'utf8');
    const kern = datei('studio', 'museum3d.js');
    assert.match(kern, /export const createMuseumViewer/);
    assert.ok(!/museumStudio|museum:\/\/|getElementById/.test(kern), 'Der Kern kennt weder Studio noch Seitenaufbau');
    const web = datei('web', 'web.js');
    assert.match(web, /import \{ createMuseumViewer \} from '\.\/museum3d\.js'/);
    assert.match(web, /model: 'museum\.glb'/);
    const page = datei('web', 'index.html');
    for (const teil of ['id="viewer"', 'id="viewerWalk"', 'src="web.js"', '"three"']) assert.ok(page.includes(teil), teil);
    assert.ok(!/PNG speichern|WebM/.test(page), 'Die Webversion dient nur zum Anschauen und Herumgehen');
    // Studio und Webversion exportieren das Modell mit derselben Funktion.
    assert.match(datei('studio', 'blender_worker.py'), /vorschau_export\.exportieren\(/);
    assert.match(datei('tools', 'web', 'blender_export.py'), /vorschau_export\.exportieren\(/);
    assert.equal(JSON.parse(datei('package.json')).scripts.web, 'node tools/web/export.cjs');
});

test('Webversion wird als Branch gh-pages mit genau einer Version veröffentlicht', () => {
    const {spawnSync} = require('node:child_process');
    const ordner = fs.mkdtempSync(path.join(os.tmpdir(), 'museum-publish-'));
    const git = (...args) => spawnSync('git', args, {encoding: 'utf8', windowsHide: true});
    try {
        const web = path.join(ordner, 'web');
        fs.mkdirSync(web);
        for (const name of ['index.html', 'museum.glb', 'web.js']) fs.writeFileSync(path.join(web, name), name);
        const ziel = path.join(ordner, 'ziel.git');
        assert.equal(git('init', '--bare', '--quiet', ziel).status, 0);
        const veroeffentlichen = () => spawnSync(process.execPath,
            [path.join(__dirname, '..', 'tools', 'web', 'publish.cjs'), web, ziel], {encoding: 'utf8', windowsHide: true});
        for (let lauf = 0; lauf < 2; lauf++) {
            const result = veroeffentlichen();
            assert.equal(result.status, 0, result.stdout + result.stderr);
        }
        const dateien = git('--git-dir', ziel, 'ls-tree', '--name-only', 'gh-pages').stdout.trim().split('\n').sort();
        assert.deepEqual(dateien, ['.nojekyll', 'index.html', 'museum.glb', 'web.js']);
        // Jede Veröffentlichung ersetzt die vorige; das Repo wächst nicht mit jeder GLB-Version.
        assert.equal(git('--git-dir', ziel, 'rev-list', '--count', 'gh-pages').stdout.trim(), '1');
        fs.rmSync(path.join(web, 'museum.glb'));
        assert.notEqual(veroeffentlichen().status, 0, 'ohne museum.glb wird nichts veröffentlicht');
    } finally {
        fs.rmSync(ordner, {recursive: true, force: true});
    }
    assert.equal(JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8')).scripts['web:publish'],
        'node tools/web/publish.cjs');
});

test('Webversion lässt sich mit Blender exportieren', {
    skip: process.env.MUSEUM_INTEGRATION !== '1',
    timeout: 240000
}, () => {
    const ziel = fs.mkdtempSync(path.join(os.tmpdir(), 'museum-web-'));
    try {
        const {spawnSync} = require('node:child_process');
        const result = spawnSync(process.execPath, [path.join(__dirname, '..', 'tools', 'web', 'export.cjs'), ziel],
            {encoding: 'utf8', windowsHide: true});
        assert.equal(result.status, 0, result.stdout + result.stderr);
        assert.deepEqual(fs.readdirSync(ziel).sort(),
            ['index.html', 'mandelbrot.png', 'museum.glb', 'museum3d.js', 'park.png', 'remote-config.js',
                'remote-display.js', 'remote-protocol.js', 'remote.css', 'remote.html', 'remote.js', 'web.js']);
        assert.ok(fs.statSync(path.join(ziel, 'museum.glb')).size > 100000);
    } finally {
        fs.rmSync(ziel, {recursive: true, force: true});
    }
});

test('fertige Frames werden begrenzt ausgeliefert und als vollständig gemeldet', async () => {
    const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'museum-frames-'));
    const jobs = createStudio({workDir: path.join(folder, 'worker')});
    try {
        jobs.state.settings = {...DEFAULTS, OUTPUT_DIR: folder, FPS: 1, DURATION: 2, START_ANGLE: 30, ORBIT_DEGREES: 90};
        // Auflösung und Bildrate stehen schon im Variantenordner; die Frames liegen schlicht in frames/.
        const framesFolder = path.join(folder, 'frames');
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
    const viewer = viewerQuelltext();
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
    const viewer = viewerQuelltext();
    // Nach dem Laden des Modells startet der Rundgang; in der Übersicht gibt es keine Pfeiltasten-Drehung mehr.
    assert.match(viewer, /loaded = true;[\s\S]{0,80}if \(!walk\.active\) setWalk\(true\)/);
    assert.match(viewer, /on \? 'Übersicht' : 'Rundgang'/);
    assert.ok(!viewer.includes('zoom * 0.8 * delta'), 'Pfeiltasten dürfen die Übersicht nicht mehr drehen');
});

test('Der Viewer ersetzt das Material der Arkadenwand durch einen eigenen Stein', () => {
    const viewer = viewerQuelltext();
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
    const viewer = viewerQuelltext();
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
    const viewer = viewerQuelltext();
    assert.ok(viewer.includes('fensterglas') && viewer.includes('fensterrahmen titan'));
});
