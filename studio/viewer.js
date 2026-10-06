import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

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

let renderer;
let camera;
let controls;
let scene;
let model;
let loaded = false;
let loading = false;
let currentAngle = 0;
let floorMeshes = [];

const setActiveMode = is3d => {
    globalThis.museumViewMode = is3d ? '3d' : 'render';
    mode3d.classList.toggle('active', is3d);
    modeRender.classList.toggle('active', !is3d);
    canvas.hidden = !is3d;
    viewerActions.hidden = !is3d;
    angleLabel.hidden = !is3d;
    const hasRender = image.hasAttribute('src');
    image.hidden = is3d || !hasRender;
    empty.hidden = is3d || hasRender;
};

const initialize = () => {
    if (renderer) return;
    renderer = new THREE.WebGLRenderer({canvas, antialias: true, preserveDrawingBuffer: true});
    renderer.setPixelRatio(Math.min(globalThis.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 0.72;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    scene = new THREE.Scene();
    // Die Fenster sind offene Wanddurchbrüche: sichtbar ist der Außenhimmel.
    scene.background = new THREE.Color(0xdce9f2);
    const environmentGenerator = new THREE.PMREMGenerator(renderer);
    scene.environment = environmentGenerator.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environmentIntensity = 0.42;
    environmentGenerator.dispose();
    scene.add(new THREE.HemisphereLight(0xffe4bd, 0x252c29, 0.65));
    const key = new THREE.DirectionalLight(0xffd0a0, 1.35);
    key.position.set(6, 11, 8);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    key.shadow.camera.left = key.shadow.camera.bottom = -20;
    key.shadow.camera.right = key.shadow.camera.top = 20;
    key.shadow.camera.near = 0.5;
    key.shadow.camera.far = 50;
    key.shadow.bias = -0.00015;
    scene.add(key);
    camera = new THREE.PerspectiveCamera(42, 1, 0.05, 100);
    controls = new OrbitControls(camera, canvas);
    controls.target.set(0, 2.88, 0);
    controls.enablePan = false;
    controls.enableDamping = true;
    controls.dampingFactor = 0.18;
    controls.minDistance = 8;
    controls.maxDistance = 16;
    controls.minPolarAngle = THREE.MathUtils.degToRad(72);
    controls.maxPolarAngle = THREE.MathUtils.degToRad(102);
    controls.addEventListener('change', updateAngle);
    controls.addEventListener('end', () => globalThis.setViewerAngle(currentAngle));
    new ResizeObserver(resize).observe(stage);
    renderer.setAnimationLoop(() => {
        tick(Math.min(clock.getDelta(), 0.1));
        // OrbitControls richtet die Kamera bei jedem update() auf das Ziel aus und würde den Blick im Rundgang überschreiben.
        if (!walk.active) controls.update();
        renderer.render(scene, camera);
    });
};

const resize = () => {
    if (!renderer) return;
    const width = stage.clientWidth;
    const height = stage.clientHeight;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
};

const setCameraFromDial = () => {
    const angle = Number(document.getElementById('START_ANGLE').value) || 0;
    const radians = THREE.MathUtils.degToRad(angle);
    camera.position.set(12 * Math.sin(radians), 3.13, 12 * Math.cos(radians));
    controls.target.set(0, 2.88, 0);
    controls.update();
    updateAngle();
};

const updateAngle = () => {
    currentAngle = (THREE.MathUtils.radToDeg(Math.atan2(camera.position.x, camera.position.z)) + 360) % 360;
    angleLabel.textContent = `${Math.round(currentAngle)}°`;
};

const placeCamera = angle => {
    const radians = THREE.MathUtils.degToRad(angle);
    camera.position.set(12 * Math.sin(radians), 3.13, 12 * Math.cos(radians));
    camera.lookAt(controls.target);
    updateAngle();
};

const download = (blob, filename) => {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
};

const stoneTexture = (base, variance, darkSpeckles = false) => {
    const size = 256;
    const textureCanvas = document.createElement('canvas');
    textureCanvas.width = textureCanvas.height = size;
    const context = textureCanvas.getContext('2d');
    const imageData = context.createImageData(size, size);
    let seed = 9173;
    const random = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;
    for (let y = 0; y < size; y++) {
        for (let x = 0; x < size; x++) {
            const broad = Math.sin(x * 0.075) * 0.35 + Math.sin((x + y) * 0.031) * 0.25;
            let noise = (random() - 0.5) * variance + broad * variance;
            if (darkSpeckles && random() < 0.035) noise -= 55 * random();
            const offset = (y * size + x) * 4;
            imageData.data[offset] = Math.max(0, Math.min(255, base[0] + noise));
            imageData.data[offset + 1] = Math.max(0, Math.min(255, base[1] + noise * 0.82));
            imageData.data[offset + 2] = Math.max(0, Math.min(255, base[2] + noise * 0.62));
            imageData.data[offset + 3] = 255;
        }
    }
    context.putImageData(imageData, 0, 0);
    const texture = new THREE.CanvasTexture(textureCanvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
    texture.repeat.set(3, 3);
    texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    return texture;
};

const parquetTexture = () => {
    const size = 256;
    const plankUnits = 5;
    const period = 2 * plankUnits;
    const textureCanvas = document.createElement('canvas');
    textureCanvas.width = textureCanvas.height = size;
    const context = textureCanvas.getContext('2d');
    const imageData = context.createImageData(size, size);
    const clampByte = value => Math.round(Math.max(0, Math.min(1, value)) * 255);
    for (let yy = 0; yy < size; yy++) {
        for (let xx = 0; xx < size; xx++) {
            const u = xx / size * period;
            const v = yy / size * period;
            const ix = Math.floor(u);
            const iy = Math.floor(v);
            const difference = ((ix - iy) % period + period) % period;
            const horizontal = difference < plankUnits;
            const along = horizontal ? difference + u % 1 : period - 1 - difference + v % 1;
            const across = horizontal ? v % 1 : u % 1;
            const anchorX = horizontal ? ix - difference : ix;
            const anchorY = horizontal ? iy : iy - (period - 1 - difference);
            const tone = Math.sin(anchorX * 127.1 + anchorY * 311.7) * 0.022;
            const grain = 0.010 * Math.sin(across * 110 + Math.sin(along * 2.8) * 3);
            const edge = Math.min(across, 1 - across, along, plankUnits - along);
            const shade = edge < 0.022 ? 0.76 : 1;
            const offset = (yy * size + xx) * 4;
            imageData.data[offset] = clampByte((0.36 + tone + grain) * shade);
            imageData.data[offset + 1] = clampByte((0.27 + tone * 0.65 + grain) * shade);
            imageData.data[offset + 2] = clampByte((0.18 + tone * 0.35 + grain * 0.5) * shade);
            imageData.data[offset + 3] = 255;
        }
    }
    context.putImageData(imageData, 0, 0);
    const texture = new THREE.CanvasTexture(textureCanvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
    texture.flipY = false;
    texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    return texture;
};

const improveMaterials = (root, imageTextures) => {
    const granite = new THREE.MeshStandardMaterial({
        color: 0xffffff, side: THREE.DoubleSide,
        roughness: 0.42, metalness: 0, envMapIntensity: 0.7
    });
    granite.name = 'Three.js Granit';
    // Die Minimalflächen besitzen keine UVs. Räumliche Körnung bleibt auch an
    // Nähten, Rückseiten und gekrümmten Flächen kontinuierlich sichtbar.
    granite.onBeforeCompile = shader => {
        shader.vertexShader = shader.vertexShader.replace('#include <common>',
            '#include <common>\nvarying vec3 granitePosition;');
        shader.vertexShader = shader.vertexShader.replace('#include <begin_vertex>',
            '#include <begin_vertex>\ngranitePosition = position;');
        shader.fragmentShader = shader.fragmentShader.replace('#include <common>', `
            #include <common>
            varying vec3 granitePosition;
            float graniteHash(vec3 p) {
                p = fract(p * 0.1031);
                p += dot(p, p.yzx + 33.33);
                return fract((p.x + p.y) * p.z);
            }
            vec3 graniteColor(vec3 p) {
                vec3 cell = floor(p * 48.0);
                vec3 f = fract(p * 48.0);
                float nearest = 9.0;
                float grain = 0.0;
                for (int x = -1; x <= 1; x++) {
                    for (int y = -1; y <= 1; y++) {
                        for (int z = -1; z <= 1; z++) {
                            vec3 offset = vec3(float(x), float(y), float(z));
                            vec3 c = cell + offset;
                            vec3 center = vec3(graniteHash(c),
                                graniteHash(c + 17.0), graniteHash(c + 43.0));
                            vec3 delta = offset + center - f;
                            float distanceSquared = dot(delta, delta);
                            if (distanceSquared < nearest) {
                                nearest = distanceSquared;
                                grain = graniteHash(c + 91.0);
                            }
                        }
                    }
                }
                vec3 color = mix(vec3(0.075, 0.048, 0.028),
                                 vec3(0.31, 0.235, 0.145), grain);
                if (grain < 0.18) color = vec3(0.022, 0.028, 0.032);
                if (grain > 0.78) color = vec3(0.39, 0.36, 0.29);
                float fine = graniteHash(floor(p * 260.0));
                return color * mix(0.78, 1.15, fine);
            }
        `);
        shader.fragmentShader = shader.fragmentShader.replace('#include <map_fragment>',
            '#include <map_fragment>\ndiffuseColor.rgb *= graniteColor(granitePosition);');
        shader.fragmentShader = shader.fragmentShader.replace('#include <roughnessmap_fragment>',
            '#include <roughnessmap_fragment>\nroughnessFactor = mix(0.3, 0.57, graniteHash(floor(granitePosition * 48.0)));');
    };
    granite.customProgramCacheKey = () => 'museum-spatial-granite-v1';
    const limestone = new THREE.MeshStandardMaterial({
        map: stoneTexture([151, 132, 105], 18), color: 0xb7a486,
        roughness: 0.72, metalness: 0, envMapIntensity: 0.28
    });
    limestone.name = 'Three.js Kalkstein';
    const floor = new THREE.MeshStandardMaterial({
        map: stoneTexture([82, 64, 48], 22), color: 0x806b55,
        roughness: 0.36, metalness: 0, envMapIntensity: 0.5
    });
    floor.name = 'Three.js Museumsboden';
    const parquet = parquetTexture();
    const ceilingWood = new THREE.MeshStandardMaterial({
        color: 0xffffff, roughness: 0.48, metalness: 0, envMapIntensity: 0.3,
        side: THREE.DoubleSide
    });
    ceilingWood.onBeforeCompile = shader => {
        shader.vertexShader = shader.vertexShader.replace('#include <common>',
            '#include <common>\nvarying vec3 woodPosition;');
        shader.vertexShader = shader.vertexShader.replace('#include <begin_vertex>',
            '#include <begin_vertex>\nwoodPosition = position;');
        shader.fragmentShader = shader.fragmentShader.replace('#include <common>',
            '#include <common>\nvarying vec3 woodPosition;');
        shader.fragmentShader = shader.fragmentShader.replace('#include <map_fragment>', `
            #include <map_fragment>
            float grain = sin(woodPosition.y * 180.0 +
                sin(woodPosition.x * 1.8) * 4.0 + woodPosition.z * 90.0);
            float broad = sin(woodPosition.y * 19.0 + sin(woodPosition.x * 0.7) * 2.0);
            diffuseColor.rgb *= mix(vec3(0.075, 0.026, 0.009),
                vec3(0.32, 0.17, 0.067), clamp(0.5 + grain * 0.15 + broad * 0.25, 0.0, 1.0));
        `);
    };
    ceilingWood.customProgramCacheKey = () => 'museum-ceiling-oak-v1';

    root.traverse(object => {
        if (!object.isMesh) return;
        const original = Array.isArray(object.material) ? object.material[0] : object.material;
        const identity = `${object.name} ${original?.name || ''}`.toLowerCase();
        if (/aussenwelt parkpanorama/.test(identity)) {
            const texture = imageTextures.park;
            object.material = new THREE.MeshBasicMaterial({
                map: texture,
                color: 0xffffff,
                side: THREE.DoubleSide,
                toneMapped: true
            });
            if (texture) texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
        } else if (/mandelbrot wandteppich/.test(identity)) {
            const texture = imageTextures.mandelbrot;
            object.material = new THREE.MeshStandardMaterial({
                map: texture,
                color: 0xffffff,
                roughness: 0.68,
                metalness: 0,
                side: THREE.DoubleSide
            });
            if (texture) texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
        } else if (/kusner|s41_7_5|costa|henneberg|cobra|double[ _]trefoil|brown granite/.test(identity) &&
            !/sockel/.test(identity)) {
            object.material = granite;
            object.castShadow = true;
        } else if (/bordeaux leder|cognac leder/.test(identity)) {
            const material = original;
            material.color.setRGB(0.10, 0.006, 0.017);
            material.roughness = 0.48;
            material.metalness = 0;
            material.envMapIntensity = 0.35;
            material.bumpMap = stoneTexture([128, 128, 128], 28);
            material.bumpScale = 0.0015;
            object.castShadow = true;
            object.receiveShadow = true;
        } else if (/bar_chair_round_01/.test(identity)) {
            // Originale UV-/PBR-Texturen der Bibliotheksbank erhalten.
            const materials = Array.isArray(object.material) ? object.material : [object.material];
            for (const material of materials) {
                if (material.map) material.map.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
                // Holz soll nicht wie Metall die helle Umgebung spiegeln und weiß wirken.
                material.metalness = Math.min(material.metalness ?? 0, 0.1);
                material.roughness = Math.max(material.roughness ?? 1, 0.55);
                // Das dunkle Mahagoni der Textur wirkt in den schwach beleuchteten Ecken fast schwarz: aufhellen.
                material.color.setScalar(2.4);
                material.envMapIntensity = 1.1;
            }
            object.castShadow = true;
            object.receiveShadow = true;
        } else if (/kassettendecke|fensterbank eichenholz/.test(identity)) {
            object.material = ceilingWood;
            object.castShadow = /fensterbank/.test(identity);
            object.receiveShadow = true;
        } else if (/sockelschild/.test(identity)) {
            // Tafeln und Messingschrift behalten ihre Blender-Materialien.
            object.receiveShadow = true;
        } else if (/sockel/.test(identity) && !/statue|büste|buste/.test(identity)) {
            object.material = limestone;
            object.castShadow = true;
            object.receiveShadow = true;
        } else if (/museumsboden|polierter museumsboden/.test(identity)) {
            floorMeshes.push(object);
            // Die Boden-UVs kommen aus Blender; die Textur wird im Viewer zuverlässig erzeugt.
            if (document.getElementById('BODEN').value === 'parkett') {
                parquet.channel = original?.map?.channel ?? 1;
                original.map = parquet;
                original.color.set(0xffffff);
                original.roughness = 0.46;
                original.metalness = 0;
                original.envMapIntensity = 0.32;
                original.needsUpdate = true;
            } else {
                object.material = floor;
            }
            object.receiveShadow = true;
        } else {
            const materials = Array.isArray(object.material) ? object.material : [object.material];
            for (const material of materials) {
                if (!material) continue;
                material.side = THREE.DoubleSide;
                if ('envMapIntensity' in material) material.envMapIntensity = Math.min(material.envMapIntensity ?? 1, 0.4);
                if (material.color && !material.map) {
                    const brightness = Math.max(material.color.r, material.color.g, material.color.b);
                    if (brightness > 0.82) material.color.multiplyScalar(0.64);
                }
                if ('roughness' in material) material.roughness = Math.max(material.roughness, 0.42);
            }
            object.receiveShadow = /boden|wand|arkade|decke|garten/.test(identity);
        }
    });
};

// --- Tastatur, Rundgang und Drehen in der fertigen Bildfolge -------------------------------
const clock = new THREE.Clock();
const keys = new Set();
const walk = {active: false, yaw: 0, pitch: 0};
const walkButton = document.getElementById('viewerWalk');
// Begehbarer Bereich der Halle; die Sockel von Kusner und S41 sind als Rechtecke (x0, x1, z0, z1) gesperrt.
const WALK_LIMIT = {x: 13.6, z: 14.0};
const WALK_PITCH = 0.8; // höchstens etwa 46° nach oben oder unten; steiler wirken Decke und Boden stark verzerrt
const WALK_BLOCKS = [[-6.3, -1.6, -1.7, 1.7], [1.6, 6.3, -1.7, 1.7]];
const MOVE_KEYS = new Set(['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'KeyW', 'KeyA', 'KeyS', 'KeyD']);
const blocked = (x, z) => WALK_BLOCKS.some(([x0, x1, z0, z1]) => x > x0 && x < x1 && z > z0 && z < z1);
let lookDrag = null;

const setWalk = on => {
    walk.active = on;
    keys.clear();
    walkButton.textContent = on ? 'Rundgang beenden' : 'Rundgang';
    walkButton.classList.toggle('active', on);
    controls.enabled = !on;
    canvas.style.cursor = on ? 'grab' : '';
    if (on) {
        camera.position.set(0, 1.65, 11);
        walk.yaw = 0;
        walk.pitch = 0;
        camera.rotation.set(0, 0, 0, 'YXZ');
    } else {
        setCameraFromDial();
    }
};

// Verschiebt die Kamera im Rundgang um (dx, dz) und hält sie in der Halle und außerhalb der gesperrten Sockel.
const walkBy = (dx, dz) => {
    const x = THREE.MathUtils.clamp(camera.position.x + dx, -WALK_LIMIT.x, WALK_LIMIT.x);
    const z = THREE.MathUtils.clamp(camera.position.z + dz, -WALK_LIMIT.z, WALK_LIMIT.z);
    if (!blocked(x, camera.position.z)) camera.position.x = x;
    if (!blocked(camera.position.x, z)) camera.position.z = z;
};

const tick = delta => {
    if (globalThis.museumViewMode !== '3d' || !loaded) return;
    const down = (...codes) => Number(codes.some(code => keys.has(code)));
    if (walk.active) {
        walk.yaw += (down('ArrowLeft') - down('ArrowRight')) * 1.6 * delta;
        const forward = down('ArrowUp', 'KeyW') - down('ArrowDown', 'KeyS');
        const strafe = down('KeyD') - down('KeyA');
        if (forward || strafe) {
            const step = 3.2 * delta;
            walkBy((-Math.sin(walk.yaw) * forward + Math.cos(walk.yaw) * strafe) * step,
                (-Math.cos(walk.yaw) * forward - Math.sin(walk.yaw) * strafe) * step);
        }
        camera.rotation.set(walk.pitch, walk.yaw, 0, 'YXZ');
        return;
    }
    // → wirkt wie Ziehen mit der Maus nach rechts: Das Museum dreht sich nach rechts, die Kamera wandert nach links.
    const turn = down('ArrowLeft') - down('ArrowRight');
    const zoom = down('ArrowDown') - down('ArrowUp');
    if (!turn && !zoom) return;
    const offset = camera.position.clone().sub(controls.target);
    const radius = THREE.MathUtils.clamp(Math.hypot(offset.x, offset.z) * (1 + zoom * 0.8 * delta), 8, 15.9);
    const azimuth = Math.atan2(offset.x, offset.z) + turn * 0.9 * delta;
    camera.position.set(controls.target.x + radius * Math.sin(azimuth), camera.position.y,
        controls.target.z + radius * Math.cos(azimuth));
    controls.update();
    updateAngle();
};

// Fertige Animation: Ziehen oder Pfeiltasten wählen das Einzelbild entlang der Kamerafahrt.
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
        : THREE.MathUtils.clamp(position, 0, steps);
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

// Bild↑ und Bild↓: um 180° umdrehen (Rundgang), um das Museum herum (Rundumansicht) oder in der Bildfolge.
const turnAround = () => {
    if (walk.active) {
        walk.yaw += Math.PI;
        return;
    }
    const offset = camera.position.clone().sub(controls.target);
    camera.position.set(controls.target.x - offset.x, camera.position.y, controls.target.z - offset.z);
    controls.update();
    updateAngle();
    globalThis.setViewerAngle(currentAngle);
};

const typing = event => ['INPUT', 'SELECT', 'TEXTAREA'].includes(event.target?.tagName);
globalThis.addEventListener('keydown', event => {
    if (typing(event) || event.ctrlKey || event.metaKey || event.altKey) return;
    if (globalThis.museumViewMode === 'render') {
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
        return;
    }
    if (globalThis.museumViewMode !== '3d' || !loaded) return;
    if (event.code === 'Escape' && walk.active) {
        setWalk(false);
        return;
    }
    if (['PageUp', 'PageDown'].includes(event.code)) {
        if (!event.repeat) turnAround();
        event.preventDefault();
        return;
    }
    // W, A, S, D gelten nur im Rundgang; die Pfeiltasten drehen und zoomen auch die Rundumansicht.
    if (!MOVE_KEYS.has(event.code) || (!walk.active && event.code.startsWith('Key'))) return;
    keys.add(event.code);
    event.preventDefault();
});
globalThis.addEventListener('keyup', event => {
    if (!keys.delete(event.code)) return;
    if (!walk.active && globalThis.museumViewMode === '3d') globalThis.setViewerAngle(currentAngle);
});
globalThis.addEventListener('blur', () => keys.clear());
// Ein kurzer Klick auf den Boden stellt dich an diese Stelle (Ich-Perspektive im Rundgang).
const raycaster = new THREE.Raycaster();
let press = null;
const standAt = event => {
    const rect = canvas.getBoundingClientRect();
    raycaster.setFromCamera(new THREE.Vector2(
        (event.clientX - rect.left) / rect.width * 2 - 1,
        -((event.clientY - rect.top) / rect.height * 2 - 1)), camera);
    const hit = raycaster.intersectObjects(floorMeshes, false).find(entry => entry.point.y < 0.6);
    if (!hit) return;
    const {x, z} = hit.point;
    if (Math.abs(x) > WALK_LIMIT.x || Math.abs(z) > WALK_LIMIT.z || blocked(x, z)) return;
    if (!walk.active) {
        const view = camera.getWorldDirection(new THREE.Vector3());
        setWalk(true);
        walk.yaw = Math.atan2(-view.x, -view.z);
        walk.pitch = 0;
    }
    camera.position.set(x, 1.65, z);
};
canvas.title = 'Klick auf den Boden: dorthin stellen · Mausrad: vor und zurück (im Rundgang)';
// Mausrad im Rundgang: Rad nach vorn geht vorwärts, Rad nach hinten rückwärts (etwa 0,4 m je Rastung).
canvas.addEventListener('wheel', event => {
    if (!walk.active) return;
    event.preventDefault();
    const forward = -THREE.MathUtils.clamp(event.deltaY, -240, 240) * 0.004;
    walkBy(-Math.sin(walk.yaw) * forward, -Math.cos(walk.yaw) * forward);
}, {passive: false});
canvas.addEventListener('pointerdown', event => {
    press = {x: event.clientX, y: event.clientY, time: performance.now()};
    if (!walk.active) return;
    canvas.setPointerCapture(event.pointerId);
    lookDrag = {x: event.clientX, y: event.clientY};
    canvas.style.cursor = 'grabbing';
});
canvas.addEventListener('pointermove', event => {
    if (!lookDrag) return;
    walk.yaw -= (event.clientX - lookDrag.x) * 0.004;
    walk.pitch = THREE.MathUtils.clamp(walk.pitch - (event.clientY - lookDrag.y) * 0.004, -WALK_PITCH, WALK_PITCH);
    lookDrag = {x: event.clientX, y: event.clientY};
});
canvas.addEventListener('pointerup', event => {
    lookDrag = null;
    if (walk.active) canvas.style.cursor = 'grab';
    const click = press && Math.hypot(event.clientX - press.x, event.clientY - press.y) < 5 &&
        performance.now() - press.time < 500;
    press = null;
    if (click && loaded && globalThis.museumViewMode === '3d') standAt(event);
});
canvas.addEventListener('pointercancel', () => {
    lookDrag = null;
    press = null;
    if (walk.active) canvas.style.cursor = 'grab';
});
walkButton.addEventListener('click', () => {
    if (loaded) setWalk(!walk.active);
});

const savePng = async () => {
    await show3d();
    if (!loaded) return;
    const width = Number(document.getElementById('RESOLUTION_X').value) || 1280;
    const height = Number(document.getElementById('RESOLUTION_Y').value) || 800;
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
    if (blob) download(blob, `museum_three_${Math.round(currentAngle)}grad.png`);
};

const recordVideo = async () => {
    await show3d();
    if (!loaded) return;
    if (walk.active) setWalk(false);
    if (!canvas.captureStream || !globalThis.MediaRecorder) {
        throw new Error('Dieser Browser unterstützt keine Canvas-Videoaufnahme.');
    }
    const fps = Number(document.getElementById('FPS').value) || 24;
    const duration = Number(document.getElementById('DURATION').value) || 5;
    const orbit = Number(document.getElementById('ORBIT_DEGREES').value) || 360;
    const startAngle = currentAngle;
    const stream = canvas.captureStream(fps);
    const preferred = 'video/webm;codecs=vp9';
    const options = globalThis.MediaRecorder.isTypeSupported(preferred) ? {mimeType: preferred} : {};
    const recorder = new globalThis.MediaRecorder(stream, options);
    const chunks = [];
    recorder.addEventListener('dataavailable', event => {
        if (event.data.size) chunks.push(event.data);
    });
    const finished = new Promise(resolve => recorder.addEventListener('stop', resolve, {once: true}));
    controls.enabled = false;
    videoButton.disabled = true;
    videoButton.textContent = 'Aufnahme läuft …';
    recorder.start(250);
    const started = performance.now();
    await new Promise(resolve => {
        const frame = now => {
            const progress = Math.min(1, (now - started) / (duration * 1000));
            placeCamera(startAngle + orbit * progress);
            if (progress < 1) requestAnimationFrame(frame);
            else resolve();
        };
        requestAnimationFrame(frame);
    });
    recorder.stop();
    await finished;
    stream.getTracks().forEach(track => track.stop());
    controls.enabled = true;
    videoButton.disabled = false;
    videoButton.textContent = 'WebM aufnehmen';
    download(new Blob(chunks, {type: recorder.mimeType || 'video/webm'}), 'museum_three.webm');
};

const show3d = async () => {
    setActiveMode(true);
    initialize();
    setCameraFromDial();
    if (loading) return;
    loading = true;
    errorBox.textContent = '';
    empty.hidden = false;
    empty.querySelector('strong').textContent = '3D-Modell wird vorbereitet …';
    empty.querySelector('small').textContent = 'Beim ersten Mal baut Blender die Szene auf.';
    try {
        await globalThis.prepareMuseumModel();
        if (model) {
            scene.remove(model);
            model.traverse(object => {
                if (object.geometry) object.geometry.dispose();
                const materials = Array.isArray(object.material) ? object.material : [object.material];
                for (const material of materials) if (material) material.dispose();
            });
        }
        const textureLoader = new THREE.TextureLoader();
        const [gltf, parkTexture, mandelbrotTexture] = await Promise.all([
            new GLTFLoader().loadAsync(`museum://studio/model.glb?t=${Date.now()}`),
            textureLoader.loadAsync(`museum://studio/park.png?t=${Date.now()}`),
            textureLoader.loadAsync(`museum://studio/mandelbrot.png?t=${Date.now()}`)
        ]);
        for (const texture of [parkTexture, mandelbrotTexture]) {
            texture.colorSpace = THREE.SRGBColorSpace;
            texture.flipY = false;
        }
        model = gltf.scene;
        floorMeshes = [];
        improveMaterials(model, {park: parkTexture, mandelbrot: mandelbrotTexture});
        scene.add(model);
        loaded = true;
        empty.hidden = true;
    } catch (error) {
        errorBox.textContent = `3D-Vorschau: ${error.message}`;
        setActiveMode(false);
    } finally {
        loading = false;
    }
};

const showRender = () => {
    if (walk.active) setWalk(false);
    keys.clear();
    setActiveMode(false);
};

mode3d.addEventListener('click', show3d);
modeRender.addEventListener('click', showRender);
pngButton.addEventListener('click', () => savePng().catch(error => {
    errorBox.textContent = error.message;
}));
videoButton.addEventListener('click', () => recordVideo().catch(error => {
    controls.enabled = true;
    videoButton.disabled = false;
    videoButton.textContent = 'WebM aufnehmen';
    errorBox.textContent = error.message;
}));

if (new URLSearchParams(globalThis.location.search).get('view') === '3d') show3d();
