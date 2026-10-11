// Smartphone-Seite der Fernbedienung: Touchfläche zum Umschauen, Steuerkreuz zum Gehen und Knöpfe für Werke,
// Umdrehen, Rundgang/Übersicht und Eingang. Aufbau wie im Projekt Minimalflächen (remote.js).
import { parseRemoteCredentials, sanitizeRemoteCommand, websocketUrl } from './remote-protocol.js';
import { REMOTE_RELAY_URL } from './remote-config.js';

const {room, secret} = parseRemoteCredentials(location.hash);
const status = document.getElementById('connection-status');
const touchpad = document.getElementById('touchpad');
let socket;
let reconnectTimer;
let lastPoint = null;
let lastDistance = null;
let pendingRotate = {dx: 0, dy: 0};
let rotateFrame = 0;

const setStatus = (text, className = '') => {
    status.textContent = text;
    document.body.classList.remove('connected', 'disconnected');
    if (className) document.body.classList.add(className);
};
const send = command => {
    const clean = sanitizeRemoteCommand(command);
    if (clean && socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(clean));
};
const clamp = value => Math.max(-.5, Math.min(.5, value));
// Drehungen je Bild sammeln, damit der Relay nicht mit Einzelbewegungen überflutet wird.
const queueRotate = (dx, dy) => {
    pendingRotate = {dx: clamp(pendingRotate.dx + dx), dy: clamp(pendingRotate.dy + dy)};
    if (!rotateFrame) rotateFrame = requestAnimationFrame(() => {
        rotateFrame = 0;
        if (pendingRotate.dx || pendingRotate.dy) send({type: 'rotate', ...pendingRotate});
        pendingRotate = {dx: 0, dy: 0};
    });
};
const distance = touches => Math.hypot(touches[0].clientX - touches[1].clientX, touches[0].clientY - touches[1].clientY);

const connect = () => {
    clearTimeout(reconnectTimer);
    if (!room || !secret) {
        setStatus('Ungültiger QR-Code', 'disconnected');
        return;
    }
    setStatus('Verbindung wird aufgebaut …');
    socket = new WebSocket(websocketUrl(REMOTE_RELAY_URL, room, 'controller', secret));
    socket.addEventListener('open', () => setStatus('Mit dem Fernseher verbunden', 'connected'));
    socket.addEventListener('close', () => {
        setStatus('Verbindung unterbrochen – neuer Versuch …', 'disconnected');
        reconnectTimer = setTimeout(connect, 1500);
    });
    socket.addEventListener('error', () => socket.close());
};

touchpad.addEventListener('touchstart', event => {
    if (event.touches.length === 2) lastDistance = distance(event.touches);
    else if (event.touches.length === 1) lastPoint = {x: event.touches[0].clientX, y: event.touches[0].clientY};
}, {passive: true});
touchpad.addEventListener('touchmove', event => {
    event.preventDefault();
    if (event.touches.length === 2) {
        const next = distance(event.touches);
        // Auseinanderziehen geht vorwärts, Zusammenziehen rückwärts.
        if (lastDistance !== null) send({type: 'zoom', delta: clamp(-(next - lastDistance) * .006)});
        lastDistance = next;
        lastPoint = null;
    } else if (event.touches.length === 1 && lastPoint) {
        const point = {x: event.touches[0].clientX, y: event.touches[0].clientY};
        queueRotate((point.x - lastPoint.x) * .006, (point.y - lastPoint.y) * .006);
        lastPoint = point;
    }
}, {passive: false});
touchpad.addEventListener('touchend', () => {
    lastPoint = null;
    lastDistance = null;
});
touchpad.addEventListener('pointerdown', event => {
    if (event.pointerType === 'touch') return;
    touchpad.setPointerCapture(event.pointerId);
    lastPoint = {x: event.clientX, y: event.clientY};
});
touchpad.addEventListener('pointermove', event => {
    if (!lastPoint || event.pointerType === 'touch') return;
    queueRotate((event.clientX - lastPoint.x) * .006, (event.clientY - lastPoint.y) * .006);
    lastPoint = {x: event.clientX, y: event.clientY};
});
touchpad.addEventListener('pointerup', () => {
    lastPoint = null;
});

// Steuerkreuz: Gedrückt halten geht gleichmäßig weiter.
for (const button of document.querySelectorAll('[data-halten]')) {
    let timer = 0;
    const wert = Number(button.dataset.wert);
    const schritt = () => send(button.dataset.halten === 'zoom'
        ? {type: 'zoom', delta: wert}
        : {type: 'object-translate', horizontal: wert, vertical: 0});
    const stop = () => {
        clearInterval(timer);
        timer = 0;
    };
    button.addEventListener('pointerdown', event => {
        event.preventDefault();
        button.setPointerCapture(event.pointerId);
        stop();
        schritt();
        timer = setInterval(schritt, 60);
    });
    for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) button.addEventListener(name, stop);
    button.addEventListener('contextmenu', event => event.preventDefault());
}

for (const button of document.querySelectorAll('[data-command]')) button.addEventListener('click', () => {
    const command = {type: button.dataset.command};
    if (button.dataset.direction) command.direction = Number(button.dataset.direction);
    send(command);
});
connect();
