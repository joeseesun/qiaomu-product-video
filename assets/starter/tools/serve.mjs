// Preview: http://127.0.0.1:<port>/index.html?preview (space = play/pause, slider = scrub, &d=<deliverable>)
import { serve, parseArgs } from './common.mjs';
import { exec } from 'node:child_process';

const args = parseArgs();
const { port } = await serve(Number(args.port || 5178));
const url = `http://127.0.0.1:${port}/index.html?preview${args.d ? `&d=${args.d}` : ''}`;
console.log('preview:', url);
if (args.open) exec(`${process.platform === 'darwin' ? 'open' : process.platform === 'win32' ? 'start' : 'xdg-open'} "${url}"`);
