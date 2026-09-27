// Lab driver: open product.html (optionally ?record), run a steps module, screenshot, save recordings.
//   FILM_RECORD=1 node tools/lab.mjs --record --steps lab/steps.mjs --shot evidence/stills/lab.png
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { ROOT, serve, launch, parseArgs } from './common.mjs';
import { build } from './build.mjs';

const args = parseArgs();
await build();
const { server, port } = await serve();
const browser = await launch();
try {
  const page = await browser.newPage({ viewport: { width: Number(args.w || 1600), height: Number(args.h || 900) } });
  const problems = [];
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`));
  page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) problems.push(`${m.type()}: ${m.text()}`); });
  await page.goto(`http://127.0.0.1:${port}/product.html${args.record ? '?record' : ''}`);
  await page.waitForFunction(() => window.__productReady && window.__product, null, { timeout: 60000 });
  await page.evaluate(() => window.__productReady);
  if (args.steps) {
    const mod = await import(pathToFileURL(path.resolve(ROOT, args.steps)).href);
    await mod.default(page);
  }
  if (args.shot) await page.screenshot({ path: path.resolve(ROOT, args.shot) });
  if (args.record) await page.evaluate(async () => window.__product.save());
  const info = await page.evaluate(async () => { const l = window.__product; return { missing: l.net.missing, recorded: Object.keys(l.net.recorded).length, notices: l.notices }; });
  console.log(JSON.stringify({ problems: problems.slice(0, 30), ...info }, null, 2));
} finally {
  await browser.close();
  server.close();
}
