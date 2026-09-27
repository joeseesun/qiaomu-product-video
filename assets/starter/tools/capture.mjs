// Capture a live web product (URL-only input, or a local dev server) as high-DPR stills + element boxes.
//   node tools/capture.mjs steps.json
// steps.json: { "url": "https://…", "viewport": [1440, 900], "scale": 2, "out": "public/capture",
//   "steps": [ {"shot": "home"}, {"click": "text=Pricing"}, {"type": ["#q", "hello"]}, {"wait": 800},
//              {"shot": "search", "element": ".results", "boxes": [".card", "button.primary"]} ] }
// Output: PNGs + capture.json (per shot: file, viewport, element boxes). Use them as layered images in shots.
// Only capture what the user is entitled to show; never log in with the user's credentials.
import fs from 'node:fs';
import path from 'node:path';
import { ROOT, launch } from './common.mjs';

const spec = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = path.resolve(ROOT, spec.out || 'public/capture');
fs.mkdirSync(out, { recursive: true });
const browser = await launch();
const manifest = { url: spec.url, capturedAt: new Date().toISOString(), shots: [] };
try {
  const [w, h] = spec.viewport || [1440, 900];
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: spec.scale || 2 });
  await page.goto(spec.url, { waitUntil: 'networkidle' });
  await page.addStyleTag({ content: '*{caret-color:transparent!important}' });
  for (const s of spec.steps || [{ shot: 'page' }]) {
    if (s.click) await page.click(s.click);
    if (s.type) await page.fill(s.type[0], s.type[1]);
    if (s.hover) await page.hover(s.hover);
    if (s.scroll) await page.evaluate((y) => window.scrollTo(0, y), s.scroll);
    if (s.wait) await page.waitForTimeout(s.wait);
    if (s.shot) {
      const file = path.join(out, `${s.shot}.png`);
      const target = s.element ? await page.$(s.element) : null;
      if (target) await target.screenshot({ path: file }); else await page.screenshot({ path: file, fullPage: Boolean(s.fullPage) });
      const origin = target ? await target.boundingBox() : { x: 0, y: 0 };
      const boxes = {};
      for (const sel of s.boxes || []) {
        const b = await page.$(sel).then((e) => e && e.boundingBox());
        if (b) boxes[sel] = { x: b.x - origin.x, y: b.y - origin.y, width: b.width, height: b.height };
      }
      manifest.shots.push({ id: s.shot, file: path.relative(ROOT, file), scale: spec.scale || 2, boxes });
    }
  }
} finally {
  await browser.close();
}
fs.writeFileSync(path.join(out, 'capture.json'), JSON.stringify(manifest, null, 2));
console.log(JSON.stringify(manifest, null, 2));
