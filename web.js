// Eigenständige Webversion: lädt das exportierte Museum, startet im Rundgang und bietet eine
// Smartphone-Fernbedienung für Fernseher an.
import { createMuseumViewer } from './museum3d.js';
import { createRemoteDisplay } from './remote-display.js';

const status = document.getElementById('status');
const viewer = createMuseumViewer({
    stage: document.getElementById('stage'),
    canvas: document.getElementById('viewer'),
    walkButton: document.getElementById('viewerWalk')
});

viewer.load({model: 'museum.glb', park: 'park.png', mandelbrot: 'mandelbrot.png'})
    .then(() => {
        status.hidden = true;
        createRemoteDisplay({onCommand: viewer.fernsteuern});
    })
    .catch(error => {
        status.querySelector('strong').textContent = 'Das Museum konnte nicht geladen werden.';
        status.querySelector('small').textContent = `${error.message} – Die Seite muss über einen Webserver ` +
            'aufgerufen werden, nicht per Doppelklick.';
    });
