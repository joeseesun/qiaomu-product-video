// Render: node tools/render.mjs [--d hero] [--out renders/hero.mp4] [--audio assets/master.wav]
//                               [--from 0] [--to 5] [--png] [--crf 16] [--final] [--blur 4] [--shutter 0.5]
// Seeks every frame (never plays in real time), screenshots, pipes to FFmpeg, muxes audio.
// --blur N renders N subframes per output frame spread over the shutter (0.5 = 180°) and averages
// them with ffmpeg tmix: real motion blur on camera moves, whips and fast UI. Costs N× render time,
// so use it for finals, not drafts.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { ROOT, serve, launch, parseArgs, openFilm } from './common.mjs';
import { build } from './build.mjs';

const args = parseArgs();
await build();
const { server, port } = await serve();
const browser = await launch();
const started = Date.now();

function sha(file) { return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex').slice(0, 16); }

try {
  const { page, problems, info, plan, deliverable } = await openFilm(browser, port, args.d);
  const id = deliverable.id || 'hero';
  const final = Boolean(args.final) || plan.demo === false;
  const fps = info.fps;
  const from = Number(args.from || 0);
  const to = Math.min(Number(args.to || info.duration), info.duration);
  const total = Math.round((to - from) * fps);
  const blur = args.blur === true ? 4 : Math.max(1, Math.floor(Number(args.blur || 1)));
  const shutter = Math.min(1, Math.max(0, Number(args.shutter ?? 0.5)));
  const out = path.resolve(ROOT, args.out || `renders/${id}.mp4`);
  fs.mkdirSync(path.dirname(out), { recursive: true });

  let audio = args.audio ? path.resolve(ROOT, args.audio) : null;
  if (!audio && deliverable.sound === 'on' && fs.existsSync(path.join(ROOT, 'assets/master.wav'))) audio = path.join(ROOT, 'assets/master.wav');
  if (deliverable.sound === 'none' || deliverable.sound === 'off') audio = args.audio ? audio : null;

  const ffArgs = ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps * blur), '-i', '-'];
  if (audio) ffArgs.push('-ss', String(from), '-i', audio);
  if (blur > 1) ffArgs.push('-vf', `tmix=frames=${blur},select=eq(mod(n\\,${blur})\\,${blur - 1}),setpts=N/${fps}/TB`, '-r', String(fps));
  ffArgs.push('-c:v', 'libx264', '-preset', 'medium', '-crf', String(args.crf || 16), '-pix_fmt', 'yuv420p', '-movflags', '+faststart');
  if (audio) ffArgs.push('-c:a', 'aac', '-b:a', '192k', '-shortest');
  else ffArgs.push('-an');
  ffArgs.push(out);
  const ff = spawn('ffmpeg', ffArgs, { stdio: ['pipe', 'inherit', 'inherit'] });
  const ffDone = new Promise((res, rej) => ff.on('close', (c) => (c === 0 ? res() : rej(new Error(`ffmpeg exited ${c}`)))));

  let placeholderFrames = 0;
  const last = info.duration - 1e-4;
  for (let i = 0; i < total; i++) {
    const t = from + i / fps;
    let ph = false;
    for (let k = 0; k < blur; k++) {
      // subframes centred on t, monotonic across frames (shutter ≤ 1), clamped to the film
      const st = blur > 1 ? Math.min(last, Math.max(0, t + (((k + 0.5) / blur) - 0.5) * shutter / fps)) : t;
      ph = (await page.evaluate(async (x) => { await window.__film.seek(x); return window.__film.placeholders(); }, st)) || ph;
      const buf = await page.screenshot(args.png ? { type: 'png' } : { type: 'jpeg', quality: 95 });
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    }
    if (ph) placeholderFrames++;
    if (i % (fps * 2) === 0) process.stderr.write(`\r[render ${id}] ${(t).toFixed(1)}s / ${to.toFixed(1)}s`);
  }
  ff.stdin.end();
  await ffDone;
  process.stderr.write('\n');

  const missing = await page.evaluate(() => window.__film.missingFixtures);
  const report = {
    deliverable: id, output: path.relative(ROOT, out), width: info.width, height: info.height, fps,
    from, to, frames: total, motionBlur: blur > 1 ? { subframes: blur, shutter } : null, audio: audio ? path.relative(ROOT, audio) : null, audioSha: audio ? sha(audio) : null,
    planSha: sha(path.join(ROOT, 'plan.json')), placeholderFrames, problems, missingFixtures: missing,
    seconds: Math.round((Date.now() - started) / 1000),
  };
  fs.mkdirSync(path.join(ROOT, 'evidence'), { recursive: true });
  fs.writeFileSync(path.join(ROOT, `evidence/render-${id}.json`), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (final && placeholderFrames) { console.error(`final render has ${placeholderFrames} frames with placeholders`); process.exitCode = 1; }
  if (final && problems.length) { console.error('page problems during final render'); process.exitCode = 1; }
} finally {
  await browser.close();
  server.close();
}
