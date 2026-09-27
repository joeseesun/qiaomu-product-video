// Covers: node tools/cover.mjs [cover/cover.html] → covers/cover-<ratio>.png at 2x.
// Each cover is an element with data-cover="3x4" | "4x3" | "16x9" (sizes: 1080x1440, 1440x1080, 1920x1080).
import fs from 'node:fs';
import path from 'node:path';
import { ROOT, serve, launch, parseArgs } from './common.mjs';

const SIZES = { '3x4': [1080, 1440], '4x3': [1440, 1080], '16x9': [1920, 1080], '9x16': [1080, 1920], '1x1': [1080, 1080] };
const args = parseArgs();
const file = args._[0] || 'cover/cover.html';
const { server, port } = await serve();
const browser = await launch();
try {
  const page = await browser.newPage({ viewport: { width: 2000, height: 2000 }, deviceScaleFactor: 2 });
  const problems = [];
  page.on('pageerror', (e) => problems.push(e.message));
  page.on('requestfailed', (r) => problems.push(`requestfailed: ${r.url()}`));
  await page.goto(`http://127.0.0.1:${port}/${file}`);
  await page.evaluate(() => document.fonts.ready);
  fs.mkdirSync(path.join(ROOT, 'covers'), { recursive: true });
  const out = [];
  for (const el of await page.$$('[data-cover]')) {
    const ratio = await el.getAttribute('data-cover');
    const box = await el.boundingBox();
    const want = SIZES[ratio];
    if (want && (Math.round(box.width) !== want[0] || Math.round(box.height) !== want[1])) {
      problems.push(`${ratio}: element is ${box.width}x${box.height}, expected ${want.join('x')}`);
    }
    const p = path.join(ROOT, 'covers', `cover-${ratio}.png`);
    await el.screenshot({ path: p });
    out.push(path.relative(ROOT, p));
  }
  console.log(JSON.stringify({ covers: out, problems }, null, 2));
  if (problems.length) process.exitCode = 1;
} finally {
  await browser.close();
  server.close();
}
