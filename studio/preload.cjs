'use strict';

const {contextBridge, ipcRenderer} = require('electron');

contextBridge.exposeInMainWorld('museumStudio', {
    defaults: ipcRenderer.sendSync('museum:defaults'),
    status: () => ipcRenderer.invoke('museum:status'),
    start: (kind, settings) => ipcRenderer.invoke('museum:start', kind, settings),
    stop: () => ipcRenderer.invoke('museum:stop'),
    prepareModel: settings => ipcRenderer.invoke('museum:model', settings),
    saveVideo: () => ipcRenderer.invoke('museum:save-video')
});
