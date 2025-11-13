#!/usr/bin/env node
/**
 * NPM Postinstall Hook
 * Automatically runs data update check after npm install
 */

const { spawn } = require('child_process');
const path = require('path');

console.log('\n🔄 Running post-install data update check...\n');

const scriptPath = path.join(__dirname, '..', 'scripts', 'auto_update_data.py');

const python = spawn('python', [scriptPath], {
    stdio: 'inherit',
    shell: true
});

python.on('close', (code) => {
    if (code !== 0) {
        console.error(`\n⚠️  Data update check exited with code ${code}`);
        console.error('This is not critical - continuing...\n');
    } else {
        console.log('\n✅ Data update check completed\n');
    }
});

python.on('error', (err) => {
    console.error('\n⚠️  Could not run data update check:', err.message);
    console.error('This is not critical - continuing...\n');
});
