'use strict';

// Veröffentlicht die zusammengestellte Webversion (Standard: Ausgabe/Web) als Branch gh-pages für GitHub Pages.
// Der Branch enthält immer genau eine Version: Jede Veröffentlichung ersetzt die vorige, damit das Repo nicht
// mit jeder museum.glb wächst. Arbeitsverzeichnis und andere Branches bleiben unberührt.
// Aufruf: npm run web:publish   oder   node tools/web/publish.cjs <ordner> <remote>

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');

const ROOT = path.resolve(__dirname, '..', '..');
const git = (args, cwd) => {
    const result = spawnSync('git', args, {cwd, encoding: 'utf8', windowsHide: true});
    if (result.status !== 0) throw Error(`git ${args[0]} fehlgeschlagen: ${result.stderr.trim()}`);
    return result.stdout.trim();
};

const quelle = path.resolve(process.argv[2] || path.join(ROOT, 'Ausgabe', 'Web'));
for (const name of ['index.html', 'museum.glb']) {
    if (!fs.existsSync(path.join(quelle, name))) throw Error(`${name} fehlt in ${quelle}. Zuerst npm run web ausführen.`);
}
const remote = process.argv[3] || git(['remote', 'get-url', 'origin'], ROOT);
const autor = ['user.name', 'user.email'].flatMap(key => {
    const result = spawnSync('git', ['config', key], {cwd: ROOT, encoding: 'utf8', windowsHide: true});
    return result.status === 0 ? ['-c', `${key}=${result.stdout.trim()}`] : [];
});

const arbeit = fs.mkdtempSync(path.join(os.tmpdir(), 'museum-gh-pages-'));
try {
    git(['init', '--quiet', '-b', 'gh-pages'], arbeit);
    fs.cpSync(quelle, arbeit, {recursive: true});
    // Ohne .nojekyll verarbeitet GitHub Pages die Dateien mit Jekyll.
    fs.writeFileSync(path.join(arbeit, '.nojekyll'), '');
    git(['add', '--all'], arbeit);
    git([...autor, 'commit', '--quiet', '-m', `Webversion vom ${new Date().toISOString().slice(0, 10)}`], arbeit);
    git(['push', '--quiet', '--force', remote, 'gh-pages:gh-pages'], arbeit);
} finally {
    fs.rmSync(arbeit, {recursive: true, force: true});
}
console.log(`Veröffentlicht als Branch gh-pages: ${remote}`);
