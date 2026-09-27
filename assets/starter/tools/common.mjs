// Shared helpers: static server, browser launch, arg parsing.
// Copyright (c) 向阳乔木 — MIT License.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml',
  '.webp': 'image/webp', '.gif': 'image/gif', '.woff': 'font/woff', '.woff2': 'font/woff2', '.ttf': 'font/ttf',
  '.otf': 'font/otf', '.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.mp4': 'video/mp4', '.cast': 'text/plain; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
};

/**
 * Serve ROOT; /public/* is also served at / so product assets referenced as "/icons/x.svg" resolve.
 * Record mode (FILM_RECORD=1): GET /__proxy?url= fetches a real URL server-side (so the page can
 * reach real APIs without CORS), and POST /__record?name=x writes the body to src/fixtures/x.json.
 */
export function serve(port = 0) {
  const server = http.createServer(async (req, res) => {
    const u = new URL(req.url, 'http://x');
    if (process.env.FILM_RECORD && u.pathname === '/__proxy') {
      try {
        const r = await fetch(u.searchParams.get('url'), { headers: { 'user-agent': 'qiaomu-film-recorder', accept: '*/*' }, redirect: 'follow' });
        res.writeHead(r.status, { 'content-type': r.headers.get('content-type') || 'application/octet-stream' });
        res.end(Buffer.from(await r.arrayBuffer()));
      } catch (e) { res.writeHead(502); res.end(String(e)); }
      return;
    }
    if (process.env.FILM_RECORD && u.pathname === '/__record' && req.method === 'POST') {
      const chunks = []; for await (const c of req) chunks.push(c);
      const name = (u.searchParams.get('name') || 'requests').replace(/[^\w-]/g, '');
      fs.mkdirSync(path.join(ROOT, 'src/fixtures'), { recursive: true });
      fs.writeFileSync(path.join(ROOT, `src/fixtures/${name}.json`), Buffer.concat(chunks));
      res.writeHead(204); res.end(); return;
    }
    const url = decodeURIComponent(u.pathname);
    const candidates = [path.join(ROOT, url), path.join(ROOT, 'public', url)];
    if (url.endsWith('/')) candidates.unshift(path.join(ROOT, url, 'index.html'));
    const file = candidates.find((f) => f.startsWith(ROOT) && fs.existsSync(f) && fs.statSync(f).isFile());
    if (!file) { res.writeHead(404); res.end('not found'); return; }
    res.writeHead(200, { 'content-type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream', 'cache-control': 'no-store' });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise((resolve) => server.listen(port, '127.0.0.1', () => resolve({ server, port: server.address().port })));
}

const ARGS = ['--enable-unsafe-swiftshader', '--use-gl=angle', '--use-angle=swiftshader', '--hide-scrollbars',
  '--force-color-profile=srgb', '--font-render-hinting=none', '--autoplay-policy=no-user-gesture-required'];

/** Launch Chromium: FILM_CHROME path → system Chrome → Edge → Playwright's own browser. */
export async function launch() {
  const { chromium } = await import('playwright-core');
  const tries = [];
  if (process.env.FILM_CHROME) tries.push({ executablePath: process.env.FILM_CHROME });
  tries.push({ channel: 'chrome' }, { channel: 'msedge' }, {});
  const errors = [];
  for (const opt of tries) {
    try { return await chromium.launch({ headless: true, args: ARGS, ...opt }); } catch (e) { errors.push(e.message.split('\n')[0]); }
  }
  throw new Error('No Chromium found. Install Google Chrome, set FILM_CHROME=/path/to/chrome, or run `npx playwright install chromium`.\n' + errors.join('\n'));
}

export function parseArgs(argv = process.argv.slice(2)) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const k = a.slice(2);
      const v = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : true;
      out[k] = v;
    } else out._.push(a);
  }
  return out;
}

export function readPlan() {
  return JSON.parse(fs.readFileSync(path.join(ROOT, 'plan.json'), 'utf8'));
}

/** Open the film page for a deliverable and wait until ready. Collects page errors. */
export async function openFilm(browser, port, deliverable, { scale = 1 } = {}) {
  const plan = readPlan();
  const d = plan.deliverables?.find((x) => x.id === deliverable) || plan.deliverables?.[0] || { aspect: '16:9' };
  const [w, h] = (d.aspect || '16:9').split(':').map(Number);
  const short = Math.min(plan.format?.width || 1920, plan.format?.height || 1080);
  const size = w >= h ? { width: Math.round((short * w) / h), height: short } : { width: short, height: Math.round((short * h) / w) };
  const page = await browser.newPage({ viewport: size, deviceScaleFactor: scale });
  const problems = [];
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`));
  page.on('console', (m) => { if (m.type() === 'error') problems.push(`console: ${m.text()}`); });
  page.on('requestfailed', (r) => problems.push(`requestfailed: ${r.url()}`));
  page.on('response', (r) => { if (r.status() >= 400) problems.push(`http ${r.status()}: ${r.url()}`); });
  await page.goto(`http://127.0.0.1:${port}/index.html?d=${encodeURIComponent(d.id || deliverable || '')}`);
  await page.waitForFunction(() => window.__film || window.__filmError, null, { timeout: Number(process.env.FILM_START_TIMEOUT || 300000), polling: 250 });
  const err = await page.evaluate(() => window.__filmError);
  if (err) throw new Error(err);
  const info = await page.evaluate(() => ({ duration: window.__film.duration, fps: window.__film.fps, width: window.__film.width, height: window.__film.height, shots: window.__film.shots }));
  return { page, problems, info, plan, deliverable: d };
}
