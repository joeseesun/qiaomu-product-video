// Stills: node tools/stills.mjs <outDir> <t1> <t2> ... [--d deliverable] [--scale 1]
// Or: node tools/stills.mjs <outDir> --shot <id> (4 frames inside that shot)
import fs from 'node:fs';
import path from 'node:path';
import { serve, launch, parseArgs, openFilm } from './common.mjs';
import { build } from './build.mjs';

const args = parseArgs();
const [outDir, ...times] = args._;
if (!outDir) { console.error('usage: stills.mjs <outDir> <times...> [--shot id] [--d deliverable]'); process.exit(2); }
await build();
const { server, port } = await serve();
const browser = await launch();
try {
  const { page, problems, info } = await openFilm(browser, port, args.d, { scale: Number(args.scale || 1) });
  let ts = times.map(Number);
  if (args.shot) {
    const s = info.shots.find((x) => x.id === args.shot);
    if (!s) throw new Error(`no shot ${args.shot}`);
    ts = [0.1, 0.35, 0.65, 0.95].map((f) => +(s.start + (s.end - s.start) * f).toFixed(3));
  }
  fs.mkdirSync(outDir, { recursive: true });
  const written = [];
  for (const t of ts) {
    await page.evaluate((x) => window.__film.seek(x), t);
    const file = path.join(outDir, `${args.d || 'main'}-${t.toFixed(2)}s.png`);
    await page.screenshot({ path: file });
    written.push(file);
  }
  const missing = await page.evaluate(() => window.__film.missingFixtures);
  console.log(JSON.stringify({ stills: written, problems, missingFixtures: missing }, null, 2));
  if (problems.length) process.exitCode = 1;
} finally {
  await browser.close();
  server.close();
}
