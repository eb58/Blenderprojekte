// Gemeinsamer Kern der 3D-Ansicht für Museum Studio und die eigenständige Webversion:
// Three.js-Szene, Materialien, Rundgang, Übersicht sowie Tastatur-, Maus- und Klick-Navigation.
// Studio-spezifisches (Blender-Worker, Renderbild, PNG/WebM) liegt in viewer.js.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

// Begehbarer Bereich der Halle; die Sockel von Kusner und S41 sind als Rechtecke (x0, x1, z0, z1) gesperrt.
const WALK_LIMIT = {x: 13.6, z: 14.0};
const WALK_PITCH = 0.8; // höchstens etwa 46° nach oben oder unten; steiler wirken Decke und Boden stark verzerrt
const WALK_BLOCKS = [[-6.3, -1.6, -1.7, 1.7], [1.6, 6.3, -1.7, 1.7]];
const MOVE_KEYS = new Set(['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'KeyW', 'KeyA', 'KeyS', 'KeyD']);
const DEFAULT_START = {x: 0, y: 1.65, z: 11, yaw: 0, pitch: 0};
const blocked = (x, z) => WALK_BLOCKS.some(([x0, x1, z0, z1]) => x > x0 && x < x1 && z > z0 && z < z1);

/**
 * stage: Element, dessen Größe die Ansicht übernimmt; canvas: Zeichenfläche; walkButton: Knopf Rundgang/Übersicht;
 * angleLabel: optionale Winkelanzeige; startAngle(): Winkel der Übersicht; onAngle(winkel): neuer Winkel der Übersicht;
 * isActive(): ob die Ansicht gerade sichtbar ist und Eingaben annimmt.
 */
export const createMuseumViewer = ({
    stage, canvas, walkButton, angleLabel = null,
    startAngle = () => 158, onAngle = () => {}, isActive = () => true
}) => {
    let renderer;
    let camera;
    let controls;
    let scene;
    let model;
    let loaded = false;
    let currentAngle = 0;
    let floorMeshes = [];
    let workMeshes = [];
    const clock = new THREE.Clock();
    const keys = new Set();
    const walk = {active: false, yaw: 0, pitch: 0, saved: null};
    let fly = null;
    let lookDrag = null;

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
        controls.addEventListener('end', () => onAngle(currentAngle));
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

    const resetCamera = () => {
        const radians = THREE.MathUtils.degToRad(Number(startAngle()) || 0);
        camera.position.set(12 * Math.sin(radians), 3.13, 12 * Math.cos(radians));
        controls.target.set(0, 2.88, 0);
        controls.update();
        updateAngle();
    };

    const updateAngle = () => {
        currentAngle = (THREE.MathUtils.radToDeg(Math.atan2(camera.position.x, camera.position.z)) + 360) % 360;
        if (angleLabel) angleLabel.textContent = `${Math.round(currentAngle)}°`;
    };

    const placeCamera = angle => {
        const radians = THREE.MathUtils.degToRad(angle);
        camera.position.set(12 * Math.sin(radians), 3.13, 12 * Math.cos(radians));
        camera.lookAt(controls.target);
        updateAngle();
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
        // Arkadenwand: Blender zeigt sie als Quadermauerwerk, der glTF-Export kennt das Fugenmuster nicht.
        const titaniumFrame = new THREE.MeshStandardMaterial({
            color: 0xa9abb0, roughness: 0.42, metalness: 0.55, envMapIntensity: 0.9
        });
        titaniumFrame.name = 'Three.js Titan';
        // Fensterglas: fast klar, leichte Spiegelung; der Himmel dahinter bleibt sichtbar.
        const windowGlass = new THREE.MeshStandardMaterial({
            color: 0xeaf4ff, transparent: true, opacity: 0.1, roughness: 0.04, metalness: 0,
            envMapIntensity: 1.2, depthWrite: false, side: THREE.DoubleSide
        });
        windowGlass.name = 'Three.js Fensterglas';
        const arcadeStone = new THREE.MeshStandardMaterial({
            color: 0xb9b1a3, roughness: 0.82, metalness: 0, envMapIntensity: 0.25
        });
        arcadeStone.name = 'Three.js Arkadenstein';
        arcadeStone.onBeforeCompile = shader => {
            shader.vertexShader = shader.vertexShader
                .replace('#include <common>', '#include <common>\nvarying vec3 wallPosition;')
                .replace('#include <begin_vertex>',
                    '#include <begin_vertex>\nwallPosition = (modelMatrix * vec4(position, 1.0)).xyz;');
            shader.fragmentShader = shader.fragmentShader
                .replace('#include <common>', '#include <common>\nvarying vec3 wallPosition;')
                .replace('#include <map_fragment>', `
                    #include <map_fragment>
                    // Steinplatten 2,4 m x 1,2 m, jede zweite Reihe um eine halbe Platte versetzt (wie in Blender).
                    float slabRow = floor(wallPosition.y / 1.2);
                    float shifted = wallPosition.x + mod(slabRow, 2.0) * 1.2;
                    float acrossSlab = mod(shifted, 2.4);
                    float upSlab = mod(wallPosition.y, 1.2);
                    float joint = min(min(acrossSlab, 2.4 - acrossSlab), min(upSlab, 1.2 - upSlab));
                    diffuseColor.rgb *= mix(1.0, 0.86, 1.0 - smoothstep(0.0, 0.006, joint));
                    vec2 slabId = vec2(floor(shifted / 2.4), slabRow);
                    diffuseColor.rgb *= 0.95 + 0.08 * fract(sin(dot(slabId, vec2(12.9898, 78.233))) * 43758.5453);
                `);
        };
        arcadeStone.customProgramCacheKey = () => 'museum-arcade-slabs-v1';
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
                diffuseColor.rgb *= mix(vec3(0.36, 0.22, 0.10),
                    vec3(0.66, 0.48, 0.27), clamp(0.5 + grain * 0.15 + broad * 0.25, 0.0, 1.0));
            `);
        };
        ceilingWood.customProgramCacheKey = () => 'museum-ceiling-oak-v1';

        root.traverse(object => {
            if (!object.isMesh) return;
            const original = Array.isArray(object.material) ? object.material[0] : object.material;
            const identity = `${object.name} ${original?.name || ''}`.toLowerCase();
            if (/kusner|s41_7_5|costa|henneberg|cobra|double[ _]trefoil|sierpinski[-_ ]pyramide/.test(identity) &&
                !/sockel/.test(identity)) workMeshes.push(object);
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
            } else if (/fensterrahmen titan/.test(identity)) {
                // Gebürstetes Titan: Metall ohne Umgebungskarte wirkt schwarz, daher mattes Hellgrau mit etwas Glanz.
                object.material = titaniumFrame;
                object.castShadow = false;
            } else if (/fensterglas/.test(identity)) {
                object.material = windowGlass;
                object.castShadow = false;
                object.receiveShadow = false;
            } else if (/arkaden kalkstein/.test(identity)) {
                object.material = arcadeStone;
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
                // Fischgrätparkett: Die Boden-UVs kommen aus Blender; die Textur wird im Viewer zuverlässig erzeugt.
                parquet.channel = original?.map?.channel ?? 1;
                original.map = parquet;
                original.color.set(0xffffff);
                original.roughness = 0.46;
                original.metalness = 0;
                original.envMapIntensity = 0.32;
                original.needsUpdate = true;
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

    // --- Rundgang und Übersicht ------------------------------------------------------------------
    // Wechselt zwischen Rundgang (Ich-Perspektive, Standard) und Übersicht (Rundumansicht mit der Maus).
    const setWalk = (on, start) => {
        fly = null;
        keys.clear();
        if (!on && walk.active) {
            walk.saved = {x: camera.position.x, y: 1.65, z: camera.position.z, yaw: walk.yaw, pitch: walk.pitch};
        }
        walk.active = on;
        walkButton.textContent = on ? 'Übersicht' : 'Rundgang';
        walkButton.classList.toggle('active', on);
        controls.enabled = !on;
        canvas.style.cursor = on ? 'grab' : '';
        if (on) {
            const target = start ?? walk.saved ?? DEFAULT_START;
            camera.position.set(target.x, target.y, target.z);
            walk.yaw = target.yaw;
            walk.pitch = target.pitch;
            camera.rotation.set(target.pitch, target.yaw, 0, 'YXZ');
        } else {
            resetCamera();
        }
    };

    // Aus der Übersicht heraus in den Rundgang wechseln, ohne dass die Ansicht springt.
    const ensureWalk = () => {
        if (walk.active) return;
        const view = camera.getWorldDirection(new THREE.Vector3());
        setWalk(true, {
            x: camera.position.x, y: camera.position.y, z: camera.position.z,
            yaw: Math.atan2(-view.x, -view.z),
            pitch: THREE.MathUtils.clamp(Math.asin(view.y), -WALK_PITCH, WALK_PITCH)
        });
    };

    // Sanfter Kameraflug zu einem Standpunkt {x, y, z, yaw, pitch}.
    const flyTo = target => {
        fly = {
            from: {x: camera.position.x, y: camera.position.y, z: camera.position.z, yaw: walk.yaw, pitch: walk.pitch},
            to: target, t: 0, duration: 0.9
        };
    };

    // Geht zu einem Werk: Standpunkt davor (Richtung Eingangswand), Blick auf die Mitte des Werks.
    const goToWork = object => {
        ensureWalk();
        const box = new THREE.Box3().setFromObject(object);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const x = THREE.MathUtils.clamp(center.x, -WALK_LIMIT.x, WALK_LIMIT.x);
        let z = center.z + THREE.MathUtils.clamp(Math.max(size.x, size.y, size.z) * 1.5, 3.5, 7);
        for (let i = 0; i < 10 && blocked(x, z); i++) z += 0.5;
        z = Math.min(z, WALK_LIMIT.z);
        if (blocked(x, z)) return;
        const dx = center.x - x;
        const dz = center.z - z;
        flyTo({
            x, y: 1.65, z, yaw: Math.atan2(-dx, -dz),
            pitch: THREE.MathUtils.clamp(Math.atan2(center.y - 1.65, Math.hypot(dx, dz)), -WALK_PITCH, WALK_PITCH)
        });
    };

    // Verschiebt die Kamera im Rundgang um (dx, dz) und hält sie in der Halle und außerhalb der gesperrten Sockel.
    const walkBy = (dx, dz) => {
        const x = THREE.MathUtils.clamp(camera.position.x + dx, -WALK_LIMIT.x, WALK_LIMIT.x);
        const z = THREE.MathUtils.clamp(camera.position.z + dz, -WALK_LIMIT.z, WALK_LIMIT.z);
        if (!blocked(x, camera.position.z)) camera.position.x = x;
        if (!blocked(camera.position.x, z)) camera.position.z = z;
    };

    const tick = delta => {
        if (!isActive() || !loaded) return;
        const down = (...codes) => Number(codes.some(code => keys.has(code)));
        if (!walk.active) return;
        if (fly) {
            fly.t = Math.min(1, fly.t + delta / fly.duration);
            const k = fly.t * fly.t * (3 - 2 * fly.t);
            const {from, to} = fly;
            camera.position.set(from.x + (to.x - from.x) * k, from.y + (to.y - from.y) * k, from.z + (to.z - from.z) * k);
            walk.yaw = from.yaw + Math.atan2(Math.sin(to.yaw - from.yaw), Math.cos(to.yaw - from.yaw)) * k;
            walk.pitch = from.pitch + (to.pitch - from.pitch) * k;
            if (fly.t >= 1) fly = null;
        }
        walk.yaw += (down('ArrowLeft') - down('ArrowRight')) * 1.6 * delta;
        const forward = down('ArrowUp', 'KeyW') - down('ArrowDown', 'KeyS');
        const strafe = down('KeyD') - down('KeyA');
        if (forward || strafe) {
            const step = 3.2 * delta;
            walkBy((-Math.sin(walk.yaw) * forward + Math.cos(walk.yaw) * strafe) * step,
                (-Math.cos(walk.yaw) * forward - Math.sin(walk.yaw) * strafe) * step);
        }
        camera.rotation.set(walk.pitch, walk.yaw, 0, 'YXZ');
    };

    // Bild↑ und Bild↓: um 180° umdrehen (Rundgang) oder um das Museum herum (Rundumansicht).
    const turnAround = () => {
        if (walk.active) {
            walk.yaw += Math.PI;
            return;
        }
        const offset = camera.position.clone().sub(controls.target);
        camera.position.set(controls.target.x - offset.x, camera.position.y, controls.target.z - offset.z);
        controls.update();
        updateAngle();
        onAngle(currentAngle);
    };

    const typing = event => ['INPUT', 'SELECT', 'TEXTAREA'].includes(event.target?.tagName);
    globalThis.addEventListener('keydown', event => {
        if (typing(event) || event.ctrlKey || event.metaKey || event.altKey) return;
        if (!isActive() || !loaded) return;
        if (event.code === 'Escape' && walk.active) {
            setWalk(false);
            return;
        }
        if (['PageUp', 'PageDown'].includes(event.code)) {
            if (!event.repeat) turnAround();
            event.preventDefault();
            return;
        }
        // Die Tasten gelten nur im Rundgang; in der Übersicht dreht allein die Maus.
        if (!walk.active || !MOVE_KEYS.has(event.code)) return;
        fly = null;
        keys.add(event.code);
        event.preventDefault();
    });
    globalThis.addEventListener('keyup', event => keys.delete(event.code));
    globalThis.addEventListener('blur', () => keys.clear());

    // Ein kurzer Klick auf den Boden geht dorthin, ein Klick auf ein Werk führt dich davor.
    const raycaster = new THREE.Raycaster();
    let press = null;
    const clickAt = event => {
        const rect = canvas.getBoundingClientRect();
        raycaster.setFromCamera(new THREE.Vector2(
            (event.clientX - rect.left) / rect.width * 2 - 1,
            -((event.clientY - rect.top) / rect.height * 2 - 1)), camera);
        // Werke werden über ihren Umriss gewählt: Gitterwerke wie die Pyramide haben Lücken, durch die der Strahl fällt.
        let work = null;
        let workDistance = Infinity;
        for (const mesh of workMeshes) {
            const point = raycaster.ray.intersectBox(new THREE.Box3().setFromObject(mesh), new THREE.Vector3());
            const distance = point ? point.distanceTo(camera.position) : Infinity;
            if (distance < workDistance) {
                work = mesh;
                workDistance = distance;
            }
        }
        const hit = raycaster.intersectObjects(floorMeshes, false).find(entry => entry.point.y < 0.6);
        if (work && (!hit || workDistance < hit.distance)) {
            goToWork(work);
            return;
        }
        if (!hit) return;
        const {x, z} = hit.point;
        if (Math.abs(x) > WALK_LIMIT.x || Math.abs(z) > WALK_LIMIT.z || blocked(x, z)) return;
        ensureWalk();
        flyTo({x, y: 1.65, z, yaw: walk.yaw, pitch: walk.pitch});
    };
    canvas.title = 'Klick auf den Boden: dorthin gehen · Klick auf ein Werk: hingehen · Mausrad: vor und zurück';
    // Mausrad im Rundgang: Rad nach vorn geht vorwärts, Rad nach hinten rückwärts (etwa 0,4 m je Rastung).
    canvas.addEventListener('wheel', event => {
        if (!walk.active) return;
        event.preventDefault();
        fly = null;
        const forward = -THREE.MathUtils.clamp(event.deltaY, -240, 240) * 0.004;
        walkBy(-Math.sin(walk.yaw) * forward, -Math.cos(walk.yaw) * forward);
    }, {passive: false});
    canvas.addEventListener('pointerdown', event => {
        press = {x: event.clientX, y: event.clientY, time: performance.now()};
        if (!walk.active) return;
        fly = null;
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
        if (click && loaded && isActive()) clickAt(event);
    });
    canvas.addEventListener('pointercancel', () => {
        lookDrag = null;
        press = null;
        if (walk.active) canvas.style.cursor = 'grab';
    });
    walkButton.addEventListener('click', () => {
        if (!loaded) return;
        if (walk.active) setWalk(false);
        else ensureWalk();
    });

    // --- Fernsteuerung (z. B. Smartphone für einen Fernseher) -------------------------------------
    // Befehle wie im Fernbedienungsprotokoll: rotate {dx, dy} schaut sich um, zoom {delta} geht vor/zurück,
    // object-translate {horizontal, vertical} geht seitwärts/vorwärts, surface {direction} geht zum nächsten
    // oder vorigen Werk, rotation wechselt Rundgang/Übersicht, background dreht um, reset führt zum Eingang.
    // Befehle wirken sofort (wie in Minimalflächen); jede Glättung wäre auf langsamen TV-Geräten als Verzögerung spürbar.
    let workIndex = -1;
    const fernsteuern = command => {
        if (!loaded) return;
        if (command.type === 'rotation') {
            if (walk.active) setWalk(false);
            else ensureWalk();
            return;
        }
        if (command.type === 'reset') {
            walk.saved = null;
            setWalk(true, DEFAULT_START);
            return;
        }
        if (command.type === 'background') {
            turnAround();
            return;
        }
        if (command.type === 'surface' && workMeshes.length) {
            // Rundgang-Reihenfolge: erst die Hauptwerke in der Halle, dann die Nischen, jeweils von links nach rechts.
            const center = mesh => new THREE.Box3().setFromObject(mesh).getCenter(new THREE.Vector3());
            const tour = workMeshes.map(mesh => ({mesh, at: center(mesh)}))
                .sort((a, b) => Number(a.at.z < -8) - Number(b.at.z < -8) || a.at.x - b.at.x);
            workIndex = (workIndex + command.direction + tour.length) % tour.length;
            goToWork(tour[workIndex].mesh);
            return;
        }
        if (!walk.active && command.type === 'rotate') {
            // Übersicht: um das Museum herum drehen.
            const offset = camera.position.clone().sub(controls.target)
                .applyAxisAngle(new THREE.Vector3(0, 1, 0), -command.dx * 2);
            camera.position.copy(controls.target).add(offset);
            controls.update();
            updateAngle();
            onAngle(currentAngle);
            return;
        }
        ensureWalk();
        fly = null;
        if (command.type === 'rotate') {
            walk.yaw -= command.dx * 1.2;
            walk.pitch = THREE.MathUtils.clamp(walk.pitch - command.dy * 1.2, -WALK_PITCH, WALK_PITCH);
        } else {
            const forward = command.type === 'zoom' ? -command.delta * 4 : command.vertical * 4;
            const strafe = command.type === 'object-translate' ? command.horizontal * 4 : 0;
            walkBy(-Math.sin(walk.yaw) * forward + Math.cos(walk.yaw) * strafe,
                -Math.cos(walk.yaw) * forward - Math.sin(walk.yaw) * strafe);
        }
        camera.rotation.set(walk.pitch, walk.yaw, 0, 'YXZ');
    };

    // Lädt Modell und Bildtexturen ({model, park, mandelbrot} als URLs), ersetzt ein vorher geladenes Modell
    // und startet im Rundgang.
    const load = async urls => {
        initialize();
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
            new GLTFLoader().loadAsync(urls.model),
            textureLoader.loadAsync(urls.park),
            textureLoader.loadAsync(urls.mandelbrot)
        ]);
        for (const texture of [parkTexture, mandelbrotTexture]) {
            texture.colorSpace = THREE.SRGBColorSpace;
            texture.flipY = false;
        }
        model = gltf.scene;
        floorMeshes = [];
        workMeshes = [];
        workIndex = -1;
        improveMaterials(model, {park: parkTexture, mandelbrot: mandelbrotTexture});
        scene.add(model);
        loaded = true;
        if (!walk.active) setWalk(true);
    };

    // Beim Verlassen der Ansicht: Rundgang beenden und gedrückte Tasten vergessen.
    const leave = () => {
        if (walk.active) setWalk(false);
        keys.clear();
    };

    return {
        initialize,
        resetCamera,
        placeCamera,
        load,
        leave,
        setWalk,
        fernsteuern,
        get loaded() { return loaded; },
        get walking() { return walk.active; },
        get angle() { return currentAngle; },
        get renderer() { return renderer; },
        get scene() { return scene; },
        get camera() { return camera; },
        get controls() { return controls; }
    };
};
