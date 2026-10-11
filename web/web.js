// Eigenständige Webversion: lädt das exportierte Museum und startet im Rundgang.
import { createMuseumViewer } from './museum3d.js';

const status = document.getElementById('status');
const viewer = createMuseumViewer({
    stage: document.getElementById('stage'),
    canvas: document.getElementById('viewer'),
    walkButton: document.getElementById('viewerWalk')
});

viewer.load({model: 'museum.glb', park: 'park.png', mandelbrot: 'mandelbrot.png'})
    .then(() => {
        status.hidden = true;
    })
    .catch(error => {
        status.querySelector('strong').textContent = 'Das Museum konnte nicht geladen werden.';
        status.querySelector('small').textContent = `${error.message} – Die Seite muss über einen Webserver ` +
            'aufgerufen werden, nicht per Doppelklick.';
    });
