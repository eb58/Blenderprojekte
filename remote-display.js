// TV-Seite der Smartphone-Fernbedienung: zeigt einen QR-Code zu remote.html, verbindet sich mit dem Relay und
// reicht geprüfte Befehle an die 3D-Ansicht weiter. Aufbau wie im Projekt Minimalflächen (remote-display.js).
import { REMOTE_RELAY_URL } from './remote-config.js';
import {
    PUBLIC_REMOTE_SECRET, randomToken, remoteCredentialsHash, sanitizeRemoteCommand, websocketUrl
} from './remote-protocol.js';

const QR_MODULE = 'https://cdn.jsdelivr.net/npm/qrcode@1.5.4/+esm';
// Smart-TV-Browser (Fire TV, Android TV, Tizen, webOS, HbbTV …) – Liste wie in Minimalflächen.
const TV_USER_AGENT = /(?:\bAFT[A-Z0-9]*\b|Android[ _-]?TV|GoogleTV|SMART[ _-]?TV|SmartTV|webOS(?:\.TV)?|Web0S|Tizen|HbbTV|NetCast|NETTV|BRAVIA|VIERA|VIDAA|VIZIO|SmartCast|MiTV|Roku|CrKey|CE-HTML)/i;

export const isTv = (userAgent = navigator.userAgent || '') => TV_USER_AGENT.test(userAgent);
export const isMobile = (userAgent = navigator.userAgent || '') => navigator.userAgentData?.mobile === true
    || /Android|iPhone|iPad|iPod|Mobile|Tablet/i.test(userAgent)
    || (/Macintosh/i.test(userAgent) && navigator.maxTouchPoints > 1);

export const createRemoteDisplay = ({onCommand}) => {
    const dialog = document.getElementById('remote-dialog');
    const status = document.getElementById('remote-status');
    const link = document.getElementById('remote-link');
    const canvas = document.getElementById('remote-qr');
    const tvMode = isTv();
    let socket = null;
    let reconnectTimer = 0;
    let generation = 0;
    // Auf dem Smartphone selbst ist eine Fernbedienung sinnlos.
    if (!tvMode && isMobile()) return;

    const setConnected = connected => {
        dialog.dataset.connected = String(connected);
    };
    const closeSocket = () => {
        clearTimeout(reconnectTimer);
        generation += 1;
        socket?.close();
        socket = null;
    };

    const start = async () => {
        closeSocket();
        dialog.hidden = false;
        setConnected(false);
        const currentGeneration = generation;
        const room = randomToken(6);
        const controllerUrl = new URL('remote.html', location.href);
        controllerUrl.hash = remoteCredentialsHash(room);
        link.href = controllerUrl.href;
        link.textContent = controllerUrl.href;
        status.textContent = 'QR-Code mit dem Smartphone scannen';
        try {
            const {default: QRCode} = await import(QR_MODULE);
            await QRCode.toCanvas(canvas, controllerUrl.href, {width: 168, margin: 1, errorCorrectionLevel: 'L'});
            canvas.hidden = false;
        } catch {
            canvas.hidden = true;
            status.textContent = 'QR-Code konnte nicht geladen werden. Öffne den Link auf dem Smartphone.';
        }

        const connect = () => {
            if (currentGeneration !== generation) return;
            socket = new WebSocket(websocketUrl(REMOTE_RELAY_URL, room, 'display', PUBLIC_REMOTE_SECRET));
            socket.addEventListener('message', event => {
                let message;
                try {
                    message = JSON.parse(event.data);
                } catch {
                    return;
                }
                if (message.type === 'peer-connected') {
                    setConnected(true);
                    dialog.classList.remove('expanded');
                    status.textContent = 'Smartphone verbunden';
                    return;
                }
                if (message.type === 'peer-disconnected') {
                    setConnected(false);
                    dialog.classList.add('expanded');
                    status.textContent = 'Verbindung zum Smartphone getrennt';
                    return;
                }
                const command = sanitizeRemoteCommand(message);
                if (command) onCommand(command);
            });
            socket.addEventListener('close', () => {
                if (currentGeneration !== generation) return;
                setConnected(false);
                status.textContent = 'Verbindung wird wiederhergestellt …';
                reconnectTimer = setTimeout(connect, 1500);
            });
        };
        connect();
    };

    // Klein als Symbol, aufgeklappt mit QR-Code; auf dem Fernseher gleich aufgeklappt.
    dialog.classList.toggle('expanded', tvMode);
    dialog.addEventListener('click', event => {
        if (event.target.closest('button, a')) return;
        dialog.classList.toggle('expanded');
    });
    document.getElementById('remote-new-session').addEventListener('click', start);
    start();
};
