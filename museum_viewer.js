import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const stage = document.getElementById('previewStage');
const canvas = document.getElementById('viewer');
const image = document.getElementById('preview');
const empty = document.getElementById('empty');
const mode3d = document.getElementById('mode3d');
const modeRender = document.getElementById('modeRender');
const applyButton = document.getElementById('viewerApply');
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
let loadedSettings = '';

function sceneSettingsKey() {
    return ['BODEN', 'SCULPTURE_SCALE', 'THICKNESS']
        .map(id => document.getElementById(id).value).join('|');
}

function setActiveMode(is3d) {
    window.museumViewMode = is3d ? '3d' : 'render';
    mode3d.classList.toggle('active', is3d);
    modeRender.classList.toggle('active', !is3d);
    canvas.hidden = !is3d;
    applyButton.hidden = !is3d;
    angleLabel.hidden = !is3d;
    const hasRender = image.hasAttribute('src');
    image.hidden = is3d || !hasRender;
    empty.hidden = is3d || hasRender;
}

function initialize() {
    if (renderer) return;
    renderer = new THREE.WebGLRenderer({canvas, antialias: true});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x171c19);
    scene.add(new THREE.HemisphereLight(0xffe4bd, 0x34403c, 2.2));
    const key = new THREE.DirectionalLight(0xffd0a0, 3.2);
    key.position.set(6, 11, 8);
    scene.add(key);
    camera = new THREE.PerspectiveCamera(42, 1, 0.05, 100);
    controls = new OrbitControls(camera, canvas);
    controls.target.set(0, 3.2, 0);
    controls.enablePan = false;
    controls.enableDamping = true;
    controls.minDistance = 8;
    controls.maxDistance = 16;
    controls.minPolarAngle = THREE.MathUtils.degToRad(72);
    controls.maxPolarAngle = THREE.MathUtils.degToRad(102);
    controls.addEventListener('change', updateAngle);
    new ResizeObserver(resize).observe(stage);
    renderer.setAnimationLoop(() => {
        controls.update();
        renderer.render(scene, camera);
    });
}

function resize() {
    if (!renderer) return;
    const width = stage.clientWidth;
    const height = stage.clientHeight;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
}

function setCameraFromDial() {
    const angle = Number(document.getElementById('START_ANGLE').value) || 0;
    const radians = THREE.MathUtils.degToRad(angle);
    camera.position.set(12 * Math.sin(radians), 3.45, 12 * Math.cos(radians));
    controls.target.set(0, 3.2, 0);
    controls.update();
    updateAngle();
}

function updateAngle() {
    currentAngle = (THREE.MathUtils.radToDeg(Math.atan2(camera.position.x, camera.position.z)) + 360) % 360;
    angleLabel.textContent = `${Math.round(currentAngle)}°`;
}

async function show3d() {
    setActiveMode(true);
    initialize();
    setCameraFromDial();
    const settingsKey = sceneSettingsKey();
    if (loaded && settingsKey === loadedSettings) return;
    if (loading) return;
    loading = true;
    errorBox.textContent = '';
    empty.hidden = false;
    empty.querySelector('strong').textContent = '3D-Modell wird vorbereitet …';
    empty.querySelector('small').textContent = 'Beim ersten Mal baut Blender die Szene auf.';
    try {
        await window.prepareMuseumModel();
        if (model) {
            scene.remove(model);
            model.traverse(object => {
                if (object.geometry) object.geometry.dispose();
                const materials = Array.isArray(object.material) ? object.material : [object.material];
                for (const material of materials) if (material) material.dispose();
            });
        }
        const gltf = await new GLTFLoader().loadAsync(`/model.glb?t=${Date.now()}`);
        model = gltf.scene;
        model.traverse(object => {
            if (object.isMesh) {
                const materials = Array.isArray(object.material) ? object.material : [object.material];
                for (const material of materials) {
                    if (material) material.side = THREE.DoubleSide;
                }
            }
        });
        scene.add(model);
        loaded = true;
        loadedSettings = settingsKey;
        empty.hidden = true;
    } catch (error) {
        errorBox.textContent = `3D-Vorschau: ${error.message}`;
        setActiveMode(false);
    } finally {
        loading = false;
    }
}

function showRender() {
    setActiveMode(false);
}

mode3d.addEventListener('click', show3d);
modeRender.addEventListener('click', showRender);
applyButton.addEventListener('click', () => {
    window.applyViewerAngle(currentAngle);
    showRender();
});

if (new URLSearchParams(location.search).get('view') === '3d') show3d();
