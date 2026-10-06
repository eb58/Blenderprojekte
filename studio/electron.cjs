'use strict';

const {app, BrowserWindow, session, dialog, ipcMain, protocol, net} = require('electron');
const path = require('node:path');
const fs = require('node:fs/promises');
const {pathToFileURL} = require('node:url');
const {createStudio, DEFAULTS} = require('./jobs.cjs');

protocol.registerSchemesAsPrivileged([{
    scheme: 'museum',
    privileges: {
        standard: true,
        secure: true,
        supportFetchAPI: true,
        corsEnabled: true,
        stream: true
    }
}]);

const page = 'museum://studio/index.html';
const smokeTest = process.argv.includes('--smoke-test');
let studio;
let window;
let quitting = false;

const trusted = event => {
    const mainFrame = window?.webContents.mainFrame;
    if (event.sender !== window?.webContents || event.senderFrame !== mainFrame || mainFrame.url !== page) {
        throw Error('Unerlaubter IPC-Aufruf.');
    }
};

const serveMuseumFile = async request => {
    const url = new URL(request.url);
    if (url.host !== 'studio' || request.method !== 'GET') {
        return new Response('Not found', {status: 404});
    }

    const staticFiles = {'/index.html': 'index.html', '/viewer.js': 'viewer.js'};
    const imageFiles = {
        '/park.png': path.join('assets', 'museum_park_panorama.png'),
        '/mandelbrot.png': path.join('assets', 'mandelbrot_tapestry.png')
    };
    const media = {'/model.glb': 'model', '/preview': 'preview'};
    const file = Object.hasOwn(staticFiles, url.pathname)
        ? path.join(__dirname, staticFiles[url.pathname])
        : Object.hasOwn(imageFiles, url.pathname)
            ? path.join(__dirname, '..', imageFiles[url.pathname])
        : Object.hasOwn(media, url.pathname)
            ? studio.mediaPath(media[url.pathname])
            : null;

    if (!file) return new Response('Not found', {status: 404});

    const response = await net.fetch(pathToFileURL(file).href);
    const headers = new Headers(response.headers);
    headers.set('Cache-Control', 'no-store');
    headers.set(
        'Content-Security-Policy',
        `default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; ` +
        `style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; ` +
        `connect-src 'self' https://cdn.jsdelivr.net; media-src 'self' blob:; ` +
        `object-src 'none'; base-uri 'none'; frame-ancestors 'none'`
    );
    if (url.pathname === '/viewer.js') headers.set('Content-Type', 'text/javascript');
    if (url.pathname === '/index.html') headers.set('Content-Type', 'text/html; charset=utf-8');
    return new Response(response.body, {status: response.status, headers});
};

const saveVideo = async () => {
    if (!studio.status().video) throw Error('Noch kein fertiges Video vorhanden.');

    const source = studio.mediaPath('video');
    const result = await dialog.showSaveDialog(window, {
        defaultPath: path.basename(source),
        filters: [{name: 'MP4 Video', extensions: ['mp4']}]
    });
    if (!result.canceled && result.filePath && path.resolve(result.filePath) !== path.resolve(source)) {
        await fs.copyFile(source, result.filePath);
    }
    return !result.canceled;
};

const start = async () => {
    studio = createStudio();
    protocol.handle('museum', serveMuseumFile);

    ipcMain.on('museum:defaults', event => {
        try {
            trusted(event);
            event.returnValue = DEFAULTS;
        } catch {
            event.returnValue = null;
        }
    });

    const actions = {
        'museum:status': () => studio.status(),
        'museum:start': (kind, settings) => studio.start(kind, settings),
        'museum:stop': () => studio.stop(),
        'museum:model': settings => studio.prepareModel(settings),
        'museum:save-video': saveVideo
    };
    for (const [channel, action] of Object.entries(actions)) {
        ipcMain.handle(channel, (event, ...args) => {
            trusted(event);
            return action(...args);
        });
    }

    session.defaultSession.setPermissionRequestHandler((_webContents, _permission, callback) => callback(false));
    window = new BrowserWindow({
        width: 1500,
        height: 1000,
        title: 'Museum Studio',
        show: !smokeTest,
        webPreferences: {
            preload: path.join(__dirname, 'preload.cjs'),
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: true
        }
    });
    window.setMenuBarVisibility(false);
    window.webContents.setWindowOpenHandler(() => ({action: 'deny'}));
    window.webContents.on('will-navigate', (event, target) => {
        if (target !== page) event.preventDefault();
    });
    await window.loadURL(page);

    if (!smokeTest) return;

    const ready = await window.webContents.executeJavaScript(
        '(async () => {' +
        "const images = await Promise.all(['/park.png', '/mandelbrot.png'].map(path => fetch(path)));" +
        'return Boolean(globalThis.museumStudio.defaults && document.getElementById(\'previewStage\') && ' +
        '(await globalThis.museumStudio.status()) && images.every(response => response.ok));' +
        '})()'
    );
    if (!ready) throw Error('IPC/Oberfläche wurde nicht geladen.');
    console.log('ELECTRON_IPC_SMOKE_OK');
    app.quit();
};

if (!app.requestSingleInstanceLock()) {
    app.quit();
} else {
    app.on('second-instance', () => {
        if (!window) return;
        if (window.isMinimized()) window.restore();
        window.focus();
    });
    app.whenReady().then(start).catch(error => {
        console.error(error);
        if (!smokeTest) dialog.showErrorBox('Museum Studio', error.message);
        app.quit();
    });
    app.on('window-all-closed', () => app.quit());
    app.on('before-quit', event => {
        if (!studio || quitting) return;
        event.preventDefault();
        quitting = true;
        studio.close().finally(() => app.quit());
    });
}
