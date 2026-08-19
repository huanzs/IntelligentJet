const fs = require('fs');
const git = require('isomorphic-git');
const http = require('isomorphic-git/http/node');

const PROJECT_DIR = 'C:\\Temp\\IntelligentJet';
const REMOTE_URL = 'https://github.com/huanzs/IntelligentJet.git';
const token = process.argv[2];

async function main() {
    console.log('Pushing to GitHub (retry)...');
    try {
        const pushResult = await git.push({
            fs,
            http,
            dir: PROJECT_DIR,
            remote: 'origin',
            remoteRef: 'main',
            url: REMOTE_URL,
            ref: 'main',
            force: true,
            onAuth: () => ({ username: 'huanzs', password: token }),
            onMessage: (msg) => console.log(`[message] ${msg}`),
            onProgress: (progress) => {
                process.stdout.write(`\r${progress.phase}: ${progress.loaded}/${progress.total || '?'}`);
            }
        });
        console.log('\nPush successful!', JSON.stringify(pushResult.refs, null, 2));
    } catch (err) {
        console.error('\nPush failed:', err.message);
        if (err.data) console.error('Data:', err.data);
        process.exit(1);
    }
}
main();
