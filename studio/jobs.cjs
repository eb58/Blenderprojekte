'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {spawn, spawnSync} = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const DEFAULTS = {
    RENDER_PRESET: 'test',
    BODEN: 'marmor',
    RESOLUTION_X: 1280,
    RESOLUTION_Y: 800,
    FPS: 24,
    DURATION: 5,
    SCULPTURE_SCALE: 3.55,
    THICKNESS: 0.06,
    START_ANGLE: 158,
    ORBIT_DEGREES: 360,
    OUTPUT_DIR: path.join(ROOT, 'Render', 'kusner_p7_granit_museum')
};
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

const validate = data => {
    if (!data || typeof data !== 'object' || Array.isArray(data)) throw Error('Ungültige Einstellungen.');
    const settings = {...DEFAULTS};
    for (const key of Object.keys(settings)) {
        if (Object.hasOwn(data, key)) settings[key] = data[key];
    }
    if (!['test', 'final_fast', 'animation', 'quality'].includes(settings.RENDER_PRESET)) {
        throw Error('Unbekannte Renderqualität.');
    }
    if (!['marmor', 'parkett'].includes(settings.BODEN)) throw Error('Unbekannter Boden.');
    const limits = {
        RESOLUTION_X: [64, 8192],
        RESOLUTION_Y: [64, 8192],
        FPS: [1, 120],
        DURATION: [0.1, 3600],
        SCULPTURE_SCALE: [0.1, 10],
        THICKNESS: [0.001, 1],
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
    if (typeof settings.OUTPUT_DIR !== 'string' || !path.isAbsolute(settings.OUTPUT_DIR)) {
        throw Error('Bitte einen absoluten Ausgabeordner angeben.');
    }
    settings.OUTPUT_DIR = path.resolve(settings.OUTPUT_DIR);
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

const createStudio = ({workDir = path.join(ROOT, 'Render', '.museum_worker')} = {}) => {
    const model = path.join(workDir, 'museum_preview.glb');
    const state = {
        process: null,
        worker: null,
        signature: null,
        job: null,
        settings: {...DEFAULTS},
        kind: '',
        log: null,
        started: 0,
        preview: null,
        video: null,
        code: null,
        preparing: false
    };
    let mutation = false;
    let closed = false;
    const signature = settings => JSON.stringify([
        settings.BODEN,
        settings.SCULPTURE_SCALE,
        settings.THICKNESS,
        fs.statSync(path.join(ROOT, 'museum', 'scene.py')).mtimeMs,
        fs.statSync(path.join(__dirname, 'blender_worker.py')).mtimeMs
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
        const sig = signature(settings);
        if (alive(state.worker) && state.signature === sig) return;
        await stopWorker();
        if (closed) throw Error('Studio wurde beendet.');
        fs.mkdirSync(workDir, {recursive: true});
        for (const name of files(workDir)) {
            if (/^result_.*\.json$/.test(name) || ['command.json', 'ready.json', 'museum_preview.glb'].includes(name)) {
                fs.unlinkSync(path.join(workDir, name));
            }
        }
        const config = path.join(workDir, 'settings.json');
        writeJSON(config, {...settings, MAKE_VIDEO: false, RESUME_RENDER: true});
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
    const prepareWorkerModel = async () => {
        if (exists(model)) return;
        const id = crypto.randomUUID().replaceAll('-', '');
        const resultFile = path.join(workDir, `result_${id}.json`);
        writeJSON(path.join(workDir, 'command.json.tmp'), {id, type: 'model'});
        fs.renameSync(path.join(workDir, 'command.json.tmp'), path.join(workDir, 'command.json'));
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
    const startJob = async (kind, data) => {
        if (alive(state.process) || state.job) throw Error('Ein Auftrag läuft bereits.');
        let s = validate(data);
        const folder = s.OUTPUT_DIR;
        fs.mkdirSync(folder, {recursive: true});
        if (kind === 'still') {
            s = {...s, MAKE_VIDEO: false, RESUME_RENDER: true};
            writeJSON(path.join(folder, 'test-settings.json'), s);
            await ensureWorker(s);
            const id = crypto.randomUUID().replaceAll('-', '');
            const output = path.join(folder, `kusner_p7_museum_test_${id}.png`);
            const command = {id, type: 'render', output};
            for (const key of ['START_ANGLE', 'RESOLUTION_X', 'RESOLUTION_Y', 'RENDER_PRESET']) {
                command[key] = s[key];
            }
            writeJSON(path.join(workDir, 'command.json.tmp'), command);
            fs.renameSync(path.join(workDir, 'command.json.tmp'), path.join(workDir, 'command.json'));
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
        if (kind === 'animation') {
            s = {...s, MAKE_VIDEO: true, RESUME_RENDER: true};
            const config = path.join(folder, 'settings.json');
            if (files(path.join(folder, 'frames')).some(name => /^frame_.*\.png$/.test(name))) {
                const saved = exists(config) ? json(config) : null;
                if (!saved || Object.keys(s).some(key => saved[key] !== s[key]) ||
                    Object.keys(saved).some(key => !Object.hasOwn(s, key))) {
                    throw Error('Vorhandene Frames gehören zu anderen Einstellungen. Bitte einen neuen Ausgabeordner wählen.');
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
            s = validate(json(config));
            // Never accept a settings file redirecting encoding into a different folder.
            if (s.OUTPUT_DIR !== folder) throw Error('Ausgabeordner stimmt nicht mit settings.json überein.');
            for (let frame = 1; frame <= frameCount(s); frame++) {
                if (!exists(path.join(folder, 'frames', `frame_${String(frame).padStart(4, '0')}.png`))) {
                    throw Error(`Frame ${frame} fehlt. Animation erst fertig rendern.`);
                }
            }
            command = findFFmpeg();
            if (!command) throw Error('FFmpeg fehlt im PATH. PNG-Frames können bereits gerendert werden.');
            if (s.RESOLUTION_X % 2 || s.RESOLUTION_Y % 2) throw Error('Für MP4 bitte eine gerade Bildbreite und -höhe verwenden.');
            state.video = path.join(folder, `museum_${Date.now()}_${crypto.randomBytes(3).toString('hex')}.mp4`);
            args = [
                '-n', '-framerate', String(s.FPS), '-start_number', '1',
                '-i', path.join(folder, 'frames', 'frame_%04d.png'),
                '-frames:v', String(frameCount(s)), '-c:v', 'libx264',
                '-crf', '18', '-pix_fmt', 'yuv420p', state.video
            ];
        } else throw Error('Unbekannter Auftrag.');
        fs.mkdirSync(path.join(folder, 'logs'), {recursive: true});
        const log = path.join(folder, 'logs', `${kind}_${Date.now()}.log`);
        const child = launch(command, args, log, env, folder);
        Object.assign(state, {process: child, job: null, settings: s, kind, log, started: Date.now(), code: null});
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
        const folder = state.settings.OUTPUT_DIR;
        const frames = files(path.join(folder, 'frames')).filter(name => /^frame_.*\.png$/.test(name)).sort();
        const stills = files(folder).filter(name => /^kusner_p7_museum_test.*\.png$/.test(name))
            .map(name => path.join(folder, name))
            .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
        state.preview = state.kind !== 'animation' && stills.length
            ? stills[0]
            : frames.length ? path.join(folder, 'frames', frames.at(-1)) : null;
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
            frames: frames.length,
            total: frameCount(state.settings),
            preview: exists(state.preview) ? fs.statSync(state.preview).mtimeMs : null,
            video: exists(state.video) && state.code === 0,
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
        const settings = validate(data);
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
    const mediaPath = kind => {
        const file = kind === 'model' ? model
            : kind === 'preview' ? state.preview
                : kind === 'video' ? state.video : null;
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

module.exports = {createStudio, validate, frameCount, DEFAULTS};
