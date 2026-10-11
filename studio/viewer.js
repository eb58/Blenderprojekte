// Studio-Anschluss der 3D-Ansicht: Moduswechsel, Modell aus dem Blender-Worker, Drehen durch die
// gerenderten Frames sowie PNG- und WebM-Export. Szene und Navigation stecken in museum3d.js.
import { createMuseumViewer } from './museum3d.js';

const stage = document.getElementById('previewStage');
const canvas = document.getElementById('viewer');
const image = document.getElementById('preview');
const empty = document.getElementById('empty');
const mode3d = document.getElementById('mode3d');
const modeRender = document.getElementById('modeRender');
const viewerActions = document.getElementById('viewerActions');
const pngButton = document.getElementById('viewerPng');
const videoButton = document.getElementById('viewerVideo');
const angleLabel = document.getElementById('viewerAngle');
const errorBox = document.getElementById('error');
const numberField = (id, fallback) => Number(document.getElementById(id).value) || fallback;

const viewer = createMuseumViewer({
    stage, canvas, angleLabel,
    walkButton: document.getElementById('viewerWalk'),
    startAngle: () => numberField('START_ANGLE', 0),
    onAngle: angle => globalThis.setViewerAngle(angle),
    isActive: () => globalThis.museumViewMode === '3d'
});
let loading = false;

const setActiveMode = is3d => {
    globalThis.museumViewMode = is3d ? '3d' : 'render';
    document.body.dataset.modus = is3d ? '3d' : 'render';
    mode3d.classList.toggle('active', is3d);
    modeRender.classList.toggle('active', !is3d);
    canvas.hidden = !is3d;
    viewerActions.hidden = !is3d;
    angleLabel.hidden = !is3d;
    const hasRender = image.hasAttribute('src');
    image.hidden = is3d || !hasRender;
    empty.hidden = is3d || hasRender;
};

const download = (blob, filename) => {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
};

// --- Fertige Animation: Ziehen oder Pfeiltasten wählen das Einzelbild entlang der Kamerafahrt ---
const scrub = {offset: 0, shown: 0, drag: null};
const scrubInfo = () => {
    const info = globalThis.museumRender;
    return info?.complete && info.total > 1 && info.degrees ? info : null;
};
const showScrubFrame = () => {
    const info = scrubInfo();
    if (!info) return;
    const steps = info.total - 1;
    const position = Math.round(scrub.offset / info.degrees * steps);
    const wrapped = Math.abs(info.degrees) >= 360
        ? ((position % steps) + steps) % steps
        : Math.min(Math.max(position, 0), steps);
    if (wrapped + 1 === scrub.shown) return;
    scrub.shown = wrapped + 1;
    image.src = `museum://studio/frame/${scrub.shown}`;
};
image.draggable = false;
image.style.touchAction = 'none';
image.addEventListener('pointerenter', () => {
    const info = scrubInfo();
    image.style.cursor = info ? 'ew-resize' : '';
    image.title = info ? 'Ziehen oder ←/→: durch die fertige Animation drehen' : '';
});
image.addEventListener('pointerdown', event => {
    if (!scrubInfo()) return;
    image.setPointerCapture(event.pointerId);
    scrub.drag = event.clientX;
});
image.addEventListener('pointermove', event => {
    if (scrub.drag === null) return;
    scrub.offset -= (event.clientX - scrub.drag) * 0.35;
    scrub.drag = event.clientX;
    showScrubFrame();
});
for (const name of ['pointerup', 'pointercancel']) image.addEventListener(name, () => { scrub.drag = null; });

// Im Render-Modus: ←/→ und Bild↑/Bild↓ drehen durch die Bildfolge; die 3D-Tasten behandelt museum3d.js.
globalThis.addEventListener('keydown', event => {
    if (globalThis.museumViewMode !== 'render' || event.ctrlKey || event.metaKey || event.altKey) return;
    if (['INPUT', 'SELECT', 'TEXTAREA'].includes(event.target?.tagName)) return;
    const info = scrubInfo();
    if (info && ['PageUp', 'PageDown'].includes(event.code)) {
        scrub.offset += 180;
        showScrubFrame();
        event.preventDefault();
        return;
    }
    if (!info || !['ArrowLeft', 'ArrowRight'].includes(event.code)) return;
    scrub.offset += (event.code === 'ArrowRight' ? -1 : 1) * info.degrees / (info.total - 1);
    showScrubFrame();
    event.preventDefault();
});

// --- Export aus der 3D-Vorschau ---------------------------------------------------------------
const savePng = async () => {
    await show3d();
    if (!viewer.loaded) return;
    const {renderer, scene, camera} = viewer;
    const width = numberField('RESOLUTION_X', 1280);
    const height = numberField('RESOLUTION_Y', 800);
    const oldWidth = stage.clientWidth;
    const oldHeight = stage.clientHeight;
    renderer.setPixelRatio(1);
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.render(scene, camera);
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
    renderer.setPixelRatio(Math.min(globalThis.devicePixelRatio, 2));
    renderer.setSize(oldWidth, oldHeight, false);
    camera.aspect = oldWidth / oldHeight;
    camera.updateProjectionMatrix();
    if (blob) download(blob, `museum_three_${Math.round(viewer.angle)}grad.png`);
};

const recordVideo = async () => {
    await show3d();
    if (!viewer.loaded) return;
    if (viewer.walking) viewer.setWalk(false);
    if (!canvas.captureStream || !globalThis.MediaRecorder) {
        throw new Error('Dieser Browser unterstützt keine Canvas-Videoaufnahme.');
    }
    const fps = numberField('FPS', 24);
    const duration = numberField('DURATION', 5);
    const orbit = numberField('ORBIT_DEGREES', 360);
    const startAngle = viewer.angle;
    const stream = canvas.captureStream(fps);
    const preferred = 'video/webm;codecs=vp9';
    const options = globalThis.MediaRecorder.isTypeSupported(preferred) ? {mimeType: preferred} : {};
    const recorder = new globalThis.MediaRecorder(stream, options);
    const chunks = [];
    recorder.addEventListener('dataavailable', event => {
        if (event.data.size) chunks.push(event.data);
    });
    const finished = new Promise(resolve => recorder.addEventListener('stop', resolve, {once: true}));
    viewer.controls.enabled = false;
    videoButton.disabled = true;
    videoButton.textContent = 'Aufnahme läuft …';
    recorder.start(250);
    const started = performance.now();
    await new Promise(resolve => {
        const frame = now => {
            const progress = Math.min(1, (now - started) / (duration * 1000));
            viewer.placeCamera(startAngle + orbit * progress);
            if (progress < 1) requestAnimationFrame(frame);
            else resolve();
        };
        requestAnimationFrame(frame);
    });
    recorder.stop();
    await finished;
    stream.getTracks().forEach(track => track.stop());
    viewer.controls.enabled = true;
    videoButton.disabled = false;
    videoButton.textContent = 'WebM aufnehmen';
    download(new Blob(chunks, {type: recorder.mimeType || 'video/webm'}), 'museum_three.webm');
};

// --- Moduswechsel -------------------------------------------------------------------------------
const show3d = async () => {
    setActiveMode(true);
    viewer.initialize();
    viewer.resetCamera();
    if (loading) return;
    loading = true;
    errorBox.textContent = '';
    empty.hidden = false;
    empty.querySelector('strong').textContent = '3D-Modell wird vorbereitet …';
    empty.querySelector('small').textContent = 'Beim ersten Mal baut Blender die Szene auf.';
    try {
        await globalThis.prepareMuseumModel();
        const stamp = Date.now();
        await viewer.load({
            model: `museum://studio/model.glb?t=${stamp}`,
            park: `museum://studio/park.png?t=${stamp}`,
            mandelbrot: `museum://studio/mandelbrot.png?t=${stamp}`
        });
        empty.hidden = true;
    } catch (error) {
        errorBox.textContent = `3D-Vorschau: ${error.message}`;
        setActiveMode(false);
    } finally {
        loading = false;
    }
};

const showRender = () => {
    viewer.leave();
    setActiveMode(false);
};

mode3d.addEventListener('click', show3d);
modeRender.addEventListener('click', showRender);
pngButton.addEventListener('click', () => savePng().catch(error => {
    errorBox.textContent = error.message;
}));
videoButton.addEventListener('click', () => recordVideo().catch(error => {
    viewer.controls.enabled = true;
    videoButton.disabled = false;
    videoButton.textContent = 'WebM aufnehmen';
    errorBox.textContent = error.message;
}));

if (new URLSearchParams(globalThis.location.search).get('view') === '3d') show3d();
