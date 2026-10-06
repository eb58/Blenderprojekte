const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {createStudio, validate, frameCount, DEFAULTS} = require('./jobs.cjs');

test('validation and Python-compatible frame counts', () => {
    assert.equal(validate({...DEFAULTS, DURATION: '5,1'}).DURATION, 5.1);
    const invalidSettings = [
        {FPS: 24.5},
        {BODEN: 'x'},
        {THICKNESS: Infinity},
        {OUTPUT_DIR: 'relative'}
    ];
    for (const settings of invalidSettings) {
        assert.throws(() => validate({...DEFAULTS, ...settings}));
    }
    assert.equal(frameCount({FPS: 24, DURATION: 5.1}), 122);
    assert.equal(frameCount({FPS: 1, DURATION: 2.5}), 2);
});

test('job manager has no HTTP server and rejects invalid jobs', async () => {
    const jobs = createStudio();
    try {
        assert.equal(jobs.listen, undefined);
        assert.equal(jobs.status().running, false);
        await assert.rejects(jobs.start('still', {...DEFAULTS, FPS: 0}));
        assert.equal(jobs.mediaPath('arbitrary'), null);
        await jobs.stop();
    } finally {
        await jobs.close();
    }
});

test('real Blender still and FFmpeg encoding through direct job calls', {
    skip: process.env.MUSEUM_INTEGRATION !== '1',
    timeout: 240000
}, async () => {
    const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'museum-ipc-test-'));
    const jobs = createStudio({workDir: path.join(folder, 'worker')});
    const output = path.join(folder, 'output');
    try {
        const settings = {...DEFAULTS, RESOLUTION_X: 64, RESOLUTION_Y: 64, OUTPUT_DIR: output};
        await jobs.start('still', settings);
        let status;
        const deadline = Date.now() + 60000;
        do {
            await new Promise(resolve => setTimeout(resolve, 250));
            status = jobs.status();
        } while (status.running && Date.now() < deadline);

        assert.equal(status.running, false);
        assert.equal(status.code, 0, status.log);
        assert.ok(fs.existsSync(jobs.mediaPath('preview')));
        await jobs.prepareModel(settings);
        assert.ok(fs.existsSync(jobs.mediaPath('model')));

        const frames = path.join(output, 'frames');
        fs.mkdirSync(frames);
        for (let frame = 1; frame <= 2; frame++) {
            fs.copyFileSync(
                jobs.mediaPath('preview'),
                path.join(frames, `frame_${String(frame).padStart(4, '0')}.png`)
            );
        }
        const videoSettings = {...settings, DURATION: 0.1};
        fs.writeFileSync(
            path.join(output, 'settings.json'),
            JSON.stringify({...videoSettings, MAKE_VIDEO: true, RESUME_RENDER: true})
        );
        await jobs.start('video', videoSettings);
        do {
            await new Promise(resolve => setTimeout(resolve, 100));
            status = jobs.status();
        } while (status.running && Date.now() < deadline);

        assert.equal(status.code, 0, status.log);
        assert.equal(status.video, true);
        assert.ok(fs.statSync(jobs.mediaPath('video')).size > 0);
    } finally {
        await jobs.close();
        fs.rmSync(folder, {recursive: true, force: true});
    }
});
