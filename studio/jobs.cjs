'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {spawn, spawnSync} = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const AUSGABE_DIR = path.join(ROOT, 'Ausgabe');
const RENDER_DIR = path.join(AUSGABE_DIR, 'Render');
const VIDEO_DIR = path.join(AUSGABE_DIR, 'Videos');
const VIDEO_ENCODING = {crf: 18, pixelFormat: 'yuv420p'};
const DEFAULTS = {
    RENDER_PRESET: 'test',
    RESOLUTION_X: 1280,
    RESOLUTION_Y: 800,
    FPS: 24,
    DURATION: 5,
    START_ANGLE: 158,
    ORBIT_DEGREES: 360
};
const TESTBILDER = 'testbilder';
const exists = p => Boolean(p && fs.existsSync(p));
const json = p => JSON.parse(fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, ''));
const writeJSON = (p, value) => fs.writeFileSync(p, JSON.stringify(value, null, 2));
const files = p => exists(p) ? fs.readdirSync(p) : [];
const alive = p => Boolean(p && p.exitCode === null && p.signalCode === null && !p.killed);
// Python round() uses ties-to-even; retain existing frame counts and resume compatibility.
const frameCount = settings => {
    const frames = settings.FPS * settings.DURATION;
    const low = Math.floor(frames);
    return Math.max(2, frames - low === 0.5 ? low + low % 2 : Math.round(frames));
};
const animationFramesFolder = settings => path.join(settings.OUTPUT_DIR, 'frames');
const kurzHash = (settings, keys) => crypto.createHash('sha256')
    .update(JSON.stringify(keys.map(key => settings[key]))).digest('hex').slice(0, 6);
// Jede Einstellungsvariante rendert in einen eigenen Ordner: Gleiche Werte setzen denselben Lauf fort,
// geänderte beginnen einen neuen. Die Prüfsumme deckt alle Einstellungen ab, der Name die wichtigsten.
const variantName = settings =>
    `${settings.RESOLUTION_X}x${settings.RESOLUTION_Y}_${settings.FPS}fps_` +
    `${settings.DURATION}s_${settings.RENDER_PRESET}_${kurzHash(settings, Object.keys(DEFAULTS))}`;
// Fertige Videos tragen den Namen ihrer Variante; der Zeitstempel verhindert Überschreiben bei erneuter Kodierung.
const videoName = (settings, date = new Date()) => {
    const zwei = number => String(number).padStart(2, '0');
    // Windows erlaubt keine Doppelpunkte in Dateinamen, daher auch die Uhrzeit mit Bindestrichen.
    const stamp = `${date.getFullYear()}-${zwei(date.getMonth() + 1)}-${zwei(date.getDate())}_` +
        `${zwei(date.getHours())}-${zwei(date.getMinutes())}-${zwei(date.getSeconds())}`;
    return `museum_${path.basename(settings.OUTPUT_DIR)}_${stamp}.mp4`;
};
// Testbilder sammeln sich je Auflösung und Qualität, den einzigen Einstellungen, die ein Testbild verändern;
// Winkel und reine Animationswerte (Dauer, Bildrate, Umlauf) trennen sie nicht.
// Ein neues Testbild mit gleichem Kamerawinkel ersetzt das vorige.
const testbildPfad = (settings, renderDir = RENDER_DIR) => path.join(
    renderDir, TESTBILDER,
    `${settings.RESOLUTION_X}x${settings.RESOLUTION_Y}_${settings.RENDER_PRESET}`,
    `testbild_${settings.START_ANGLE}grad.png`
);

const validate = (data, renderDir = RENDER_DIR) => {
    if (!data || typeof data !== 'object' || Array.isArray(data)) throw Error('Ungültige Einstellungen.');
    const settings = {...DEFAULTS};
    for (const key of Object.keys(settings)) {
        if (Object.hasOwn(data, key)) settings[key] = data[key];
    }
    if (!['test', 'final_fast', 'animation', 'quality'].includes(settings.RENDER_PRESET)) {
        throw Error('Unbekannte Renderqualität.');
    }
    const limits = {
        RESOLUTION_X: [64, 8192],
        RESOLUTION_Y: [64, 8192],
        FPS: [1, 120],
        DURATION: [0.1, 3600],
        START_ANGLE: [-3600, 3600],
        ORBIT_DEGREES: [-3600, 3600]
    };
    for (const [key, [low, high]] of Object.entries(limits)) {
        const value = Number(String(settings[key]).replace(',', '.'));
        if (!Number.isFinite(value) || value < low || value > high) {
            throw Error(`${key}: Wert muss zwischen ${low} und ${high} liegen.`);
        }
        if (['FPS', 'RESOLUTION_X', 'RESOLUTION_Y'].includes(key) && !Number.isInteger(value)) {
            throw Error(`${key}: ganze Zahl erforderlich.`);
        }
        settings[key] = value;
    }
    if (settings.FPS * settings.DURATION < 2) throw Error('Mindestens zwei Frames erforderlich.');
    settings.OUTPUT_DIR = path.join(renderDir, variantName(settings));
    return settings;
};

const executable = name => {
    const result = spawnSync(process.platform === 'win32' ? 'where.exe' : 'which', [name], {
        encoding: 'utf8',
        windowsHide: true
    });
    return result.status === 0 ? result.stdout.trim().split(/\r?\n/)[0] : null;
};

const findFFmpeg = () => {
    const found = executable('ffmpeg');
    if (found) return found;
    const packages = path.join(process.env.LOCALAPPDATA || ROOT, 'Microsoft', 'WinGet', 'Packages');
    for (const name of files(packages).filter(n => n.startsWith('Gyan.FFmpeg_'))) {
        for (const sub of files(path.join(packages, name))) {
            const candidate = path.join(packages, name, sub, 'bin', 'ffmpeg.exe');
            if (exists(candidate)) return candidate;
        }
    }
    return null;
};

const blenderPath = () => {
    const standard = 'C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe';
    const found = process.env.MUSEUM_BLENDER || (exists(standard) ? standard : executable('blender'));
    if (!found) throw Error('Blender wurde nicht gefunden.');
    return found;
};

const createStudio = ({
    renderDir = RENDER_DIR,
    workDir = path.join(renderDir, '.museum_worker'),
    videoDir = VIDEO_DIR
} = {}) => {
    const model = path.join(workDir, 'museum_preview.glb');
    const stillsFolder = path.join(renderDir, TESTBILDER);
    const state = {
        process: null,
        worker: null,
        signature: null,
        job: null,
        settings: validate(DEFAULTS, renderDir),
        kind: '',
        log: null,
        started: 0,
        preview: null,
        video: null,
        code: null,
        preparing: false,
        phase: ''
    };
    let mutation = false;
    let closed = false;
    const modified = file => {
        try {
            return fs.statSync(file).mtimeMs;
        } catch {
            return null;
        }
    };
    // Jede Änderung an Szenenmodulen, Bildtexturen oder Materialdaten erfordert einen neu aufgebauten Worker.
    const sources = folder => files(folder).filter(name => /\.(py|json|png)$/.test(name)).sort()
        .map(name => [name, modified(path.join(folder, name))]);
    const signature = () => JSON.stringify([
        sources(path.join(ROOT, 'museum')),
        modified(path.join(__dirname, 'blender_worker.py')),
        sources(path.join(ROOT, 'assets', 'bilder')),
        sources(path.join(ROOT, 'assets', 'materialien'))
    ]);
    const launch = (command, args, logFile, env, cwd) => {
        const fd = fs.openSync(logFile, 'w');
        let child;
        try {
            child = spawn(command, args, {cwd, env, windowsHide: true, stdio: ['ignore', fd, fd]});
        } finally {
            fs.closeSync(fd);
        }
        child.on('error', error => {
            state.code = 1;
            fs.appendFileSync(logFile, `\n${error.message}\n`);
        });
        return child;
    };
    const terminate = async child => {
        if (!alive(child)) return;
        const ended = new Promise(resolve => child.once('close', resolve));
        child.kill();
        let timer;
        await Promise.race([ended, new Promise(resolve => {
            timer = setTimeout(() => {
                if (child.exitCode === null && child.signalCode === null) child.kill('SIGKILL');
                resolve();
            }, 5000);
        })]);
        clearTimeout(timer);
    };
    const stopWorker = async () => {
        await terminate(state.worker);
        state.worker = null;
        state.signature = null;
        state.job = null;
    };
    const ensureWorker = async settings => {
        const sig = signature();
        if (alive(state.worker) && state.signature === sig) return;
        await stopWorker();
        if (closed) throw Error('Studio wurde beendet.');
        fs.mkdirSync(workDir, {recursive: true});
        for (const name of files(workDir)) {
            if (/^result_.*\.json$/.test(name) || /^command_.*\.tmp$/.test(name) ||
                ['command.json', 'ready.json', 'museum_preview.glb'].includes(name)) {
                fs.unlinkSync(path.join(workDir, name));
            }
        }
        const config = path.join(workDir, 'settings.json');
        // Der Worker rendert nur Testbilder; so entsteht kein leerer Animationsordner je Einstellung.
        writeJSON(config, {...settings, OUTPUT_DIR: stillsFolder, MAKE_VIDEO: false, RESUME_RENDER: true});
        state.log = path.join(workDir, 'worker.log');
        state.worker = launch(
            blenderPath(),
            ['--background', '--factory-startup', '--python-exit-code', '1',
                '--python', path.join(__dirname, 'blender_worker.py')],
            state.log,
            {...process.env, MUSEUM_CONFIG: config, MUSEUM_WORKER_DIR: workDir},
            ROOT
        );
        state.signature = sig;
        state.preparing = true;
        state.started = Date.now();
        try {
            const deadline = Date.now() + 180000;
            while (Date.now() < deadline && !closed) {
                if (exists(path.join(workDir, 'ready.json'))) return;
                if (!alive(state.worker)) throw Error('Blender-Worker konnte die Szene nicht aufbauen. Details stehen im Render-Log.');
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            await stopWorker();
            throw Error('Blender-Worker war nach 180 Sekunden noch nicht bereit.');
        } finally {
            state.preparing = false;
        }
    };
    const writeWorkerCommand = async command => {
        const target = path.join(workDir, 'command.json');
        const temporary = path.join(workDir, `command_${command.id}.tmp`);
        writeJSON(temporary, command);
        for (let attempt = 0; attempt < 40; attempt++) {
            try {
                if (exists(target)) fs.unlinkSync(target);
                fs.renameSync(temporary, target);
                return;
            } catch (error) {
                if (!['EACCES', 'EBUSY', 'EPERM'].includes(error.code) || attempt === 39) throw error;
                await new Promise(resolve => setTimeout(resolve, 25));
            }
        }
    };
    const prepareWorkerModel = async () => {
        if (exists(model)) return;
        const id = crypto.randomUUID().replaceAll('-', '');
        const resultFile = path.join(workDir, `result_${id}.json`);
        await writeWorkerCommand({id, type: 'model'});
        const deadline = Date.now() + 180000;
        while (Date.now() < deadline && !closed) {
            if (exists(resultFile)) {
                const result = json(resultFile);
                fs.unlinkSync(resultFile);
                if (!result.ok) throw Error(result.error || '3D-Vorschaumodell konnte nicht exportiert werden.');
                if (!exists(model)) throw Error('3D-Vorschaumodell wurde nicht erzeugt.');
                return;
            }
            if (!alive(state.worker)) {
                throw Error('Blender-Worker wurde während des 3D-Exports beendet.');
            }
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        throw Error('3D-Vorschaumodell war nach 180 Sekunden noch nicht bereit.');
    };
    const prepareVideo = (settings, folder) => {
        const framesFolder = animationFramesFolder(settings);
        for (let frame = 1; frame <= frameCount(settings); frame++) {
            if (!exists(path.join(framesFolder, `frame_${String(frame).padStart(4, '0')}.png`))) {
                throw Error(`Frame ${frame} fehlt. Animation erst fertig rendern.`);
            }
        }
        const command = findFFmpeg();
        if (!command) throw Error('FFmpeg fehlt im PATH. PNG-Frames können bereits gerendert werden.');
        if (settings.RESOLUTION_X % 2 || settings.RESOLUTION_Y % 2) {
            throw Error('Für MP4 bitte eine gerade Bildbreite und -höhe verwenden.');
        }
        fs.mkdirSync(videoDir, {recursive: true});
        const output = path.join(videoDir, videoName(settings));
        return {
            command,
            output,
            args: [
                '-n', '-framerate', String(settings.FPS), '-start_number', '1',
                '-i', path.join(framesFolder, 'frame_%04d.png'),
                '-frames:v', String(frameCount(settings)), '-c:v', 'libx264',
                '-crf', String(VIDEO_ENCODING.crf), '-pix_fmt', VIDEO_ENCODING.pixelFormat, output
            ]
        };
    };
    const startJob = async (kind, data) => {
        if (alive(state.process) || state.job) throw Error('Ein Auftrag läuft bereits.');
        let s = validate(data, renderDir);
        const folder = s.OUTPUT_DIR;
        if (kind === 'still') {
            s = {...s, MAKE_VIDEO: false, RESUME_RENDER: true};
            const output = testbildPfad(s, renderDir);
            fs.mkdirSync(path.dirname(output), {recursive: true});
            writeJSON(path.join(path.dirname(output), 'test-settings.json'), s);
            await ensureWorker(s);
            const id = crypto.randomUUID().replaceAll('-', '');
            const command = {id, type: 'render', output};
            for (const key of ['START_ANGLE', 'RESOLUTION_X', 'RESOLUTION_Y', 'RENDER_PRESET']) {
                command[key] = s[key];
            }
            await writeWorkerCommand(command);
            Object.assign(state, {
                process: null,
                job: {result: path.join(workDir, `result_${id}.json`), output},
                settings: s,
                kind,
                started: Date.now(),
                preview: null,
                video: null,
                code: null
            });
            return;
        }
        const env = {...process.env};
        let args;
        let command;
        if (kind === 'animation' || kind === 'animation_video') {
            s = {...s, MAKE_VIDEO: true, RESUME_RENDER: true, FRAMES_DIR: animationFramesFolder(s)};
            fs.mkdirSync(folder, {recursive: true});
            const config = path.join(folder, 'settings.json');
            if (files(s.FRAMES_DIR).some(name => /^frame_.*\.png$/.test(name))) {
                const saved = exists(config) ? json(config) : null;
                if (!saved || Object.keys(s).some(key => saved[key] !== s[key]) ||
                    Object.keys(saved).some(key => !Object.hasOwn(s, key))) {
                    throw Error(`Vorhandene Frames in ${folder} passen nicht zu dessen settings.json.`);
                }
            }
            await stopWorker();
            writeJSON(config, s);
            env.MUSEUM_CONFIG = config;
            command = blenderPath();
            args = [
                '--background', '--factory-startup', '--python-exit-code', '1',
                '--python', path.join(ROOT, 'museum', 'scene.py'), '--render-anim'
            ];
            state.preview = null;
            state.video = null;
        } else if (kind === 'video') {
            const config = path.join(folder, 'settings.json');
            if (!exists(config)) throw Error('Bitte zuerst eine Animation rendern.');
            s = validate(json(config), renderDir);
            // Never accept a settings file redirecting encoding into a different folder.
            if (s.OUTPUT_DIR !== folder) throw Error('Ausgabeordner stimmt nicht mit settings.json überein.');
            const video = prepareVideo(s, folder);
            command = video.command;
            args = video.args;
            state.video = video.output;
        } else throw Error('Unbekannter Auftrag.');
        fs.mkdirSync(path.join(folder, 'logs'), {recursive: true});
        const log = path.join(folder, 'logs', `${kind}_${Date.now()}.log`);
        const child = launch(command, args, log, env, folder);
        Object.assign(state, {
            process: child,
            job: null,
            settings: s,
            kind,
            phase: kind === 'animation_video' ? 'animation' : kind,
            log,
            started: Date.now(),
            code: null
        });
        if (kind === 'animation_video') {
            child.once('close', code => {
                if (closed || state.process !== child || state.kind !== kind) return;
                if (code !== 0) {
                    state.code = code ?? 1;
                    return;
                }
                try {
                    const video = prepareVideo(s, folder);
                    const videoLog = path.join(folder, 'logs', `video_${Date.now()}.log`);
                    const videoChild = launch(video.command, video.args, videoLog, process.env, folder);
                    Object.assign(state, {
                        process: videoChild,
                        phase: 'video',
                        video: video.output,
                        log: videoLog,
                        started: Date.now(),
                        code: null
                    });
                } catch (error) {
                    state.process = null;
                    state.code = 1;
                    fs.appendFileSync(log, `\n${error.message}\n`);
                }
            });
        }
    };
    const status = () => {
        if (state.job) {
            if (exists(state.job.result)) {
                const result = json(state.job.result);
                state.code = result.ok ? 0 : 1;
                if (result.ok && exists(state.job.output)) state.preview = state.job.output;
                state.job = null;
            } else if (!alive(state.worker)) {
                state.code = 1;
                state.job = null;
            }
        }
        const framesFolder = animationFramesFolder(state.settings);
        const frames = files(framesFolder).filter(name => /^frame_.*\.png$/.test(name)).sort();
        const sceneStills = path.dirname(testbildPfad(state.settings, renderDir));
        const stills = files(sceneStills).filter(name => /^testbild_.*\.png$/.test(name))
            .map(name => path.join(sceneStills, name))
            .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
        state.preview = !['animation', 'animation_video'].includes(state.kind) && stills.length
            ? stills[0]
            : frames.length ? path.join(framesFolder, frames.at(-1)) : null;
        if (state.process && state.process.exitCode !== null) state.code = state.process.exitCode;
        const running = Boolean(alive(state.process) || state.job || state.preparing);
        let log = '';
        if (exists(state.log)) {
            const fd = fs.openSync(state.log, 'r');
            try {
                const size = fs.fstatSync(fd).size;
                const buffer = Buffer.alloc(Math.min(size, 14000));
                fs.readSync(fd, buffer, 0, buffer.length, Math.max(0, size - buffer.length));
                log = buffer.toString('utf8');
            } finally {
                fs.closeSync(fd);
            }
        }
        return {
            running,
            code: state.code,
            kind: state.kind,
            phase: state.phase,
            frames: frames.length,
            total: frameCount(state.settings),
            preview: exists(state.preview) ? fs.statSync(state.preview).mtimeMs : null,
            video: exists(state.video) && state.code === 0,
            complete: frames.length >= frameCount(state.settings),
            orbit: {start: state.settings.START_ANGLE, degrees: state.settings.ORBIT_DEGREES},
            log,
            elapsed: running ? Math.floor((Date.now() - state.started) / 1000) : 0,
            ffmpeg: Boolean(findFFmpeg())
        };
    };
    const stop = async () => {
        await terminate(state.process);
        if (state.job || state.preparing) await stopWorker();
        state.code = -15;
    };
    const exclusive = async action => {
        if (closed) throw Error('Studio wurde beendet.');
        if (mutation) throw Error('Ein Auftrag wird bereits vorbereitet.');
        mutation = true;
        try {
            return await action();
        } finally {
            mutation = false;
        }
    };
    const prepareModel = async data => {
        if (alive(state.process) || state.job) throw Error('Während eines Renderauftrags ist keine neue 3D-Vorschau verfügbar.');
        const settings = validate(data, renderDir);
        await ensureWorker(settings);
        state.settings = settings;
        state.preparing = true;
        try {
            await prepareWorkerModel();
        } finally {
            state.preparing = false;
        }
    };
    const close = async () => {
        closed = true;
        await terminate(state.process);
        await stopWorker();
    };
    const mediaPath = (kind, index) => {
        const frame = kind === 'frame' && Number.isInteger(index) && index >= 1 && index <= frameCount(state.settings)
            ? path.join(animationFramesFolder(state.settings), `frame_${String(index).padStart(4, '0')}.png`) : null;
        const file = kind === 'model' ? model
            : kind === 'preview' ? state.preview
                : kind === 'video' ? state.video : frame;
        return exists(file) ? file : null;
    };
    return {
        close,
        stop,
        status,
        mediaPath,
        state,
        start: (kind, data) => exclusive(() => startJob(kind, data)),
        prepareModel: data => exclusive(() => prepareModel(data))
    };
};

module.exports = {createStudio, validate, frameCount, testbildPfad, videoName, blenderPath, DEFAULTS, VIDEO_DIR};
