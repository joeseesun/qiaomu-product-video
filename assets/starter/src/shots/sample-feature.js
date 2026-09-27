// TECHNICAL SAMPLE — camera push, focus mask and cursor click on a placeholder panel.
// Real films mount the product's own components here (see references/evidence-and-components.md).
import { headline } from '../kit/text.js';
import { rig, focusOn } from '../kit/camera.js';
import { cursor, pointOf, moveAndClick } from '../kit/cursor.js';
import { focusMask, rectOf, focusTo } from '../kit/focus.js';
import { browserWindow } from '../kit/device.js';

function placeholderPanel() {
  const p = document.createElement('div');
  p.dataset.filmPlaceholder = '';
  p.style.cssText = 'width:calc(1100*var(--u));height:calc(640*var(--u));display:grid;grid-template-columns:1fr 1fr;gap:calc(24*var(--u));padding:calc(32*var(--u));box-sizing:border-box;font-size:calc(24*var(--u))';
  p.innerHTML = `
    <div style="display:flex;flex-direction:column;gap:calc(14*var(--u))">
      ${[1, 2, 3, 4].map((i) => `<div style="height:calc(64*var(--u));border-radius:calc(12*var(--u));background:#222428"></div>`).join('')}
      <button class="sample-btn" style="margin-top:auto;height:calc(64*var(--u));border:0;border-radius:calc(12*var(--u));background:var(--accent);color:#fff;font:600 calc(26*var(--u)) var(--font-zh)">运行</button>
    </div>
    <div class="sample-result" style="border-radius:calc(12*var(--u));background:#1c1d21;display:grid;place-items:center;color:var(--muted)">结果</div>`;
  return p;
}

export default {
  view(el, ctx) {
    const frame = document.createElement('div');
    // landscape: product lives in the left 62%, copy in its own column; portrait: copy on top, product below
    frame.style.cssText = ctx.portrait
      ? 'position:absolute;left:0;right:0;top:34%;bottom:0;overflow:hidden'
      : 'position:absolute;left:0;top:0;bottom:0;right:38%;overflow:hidden';
    const panel = placeholderPanel();
    const win = browserWindow(panel, { title: 'Product' });
    win.style.cssText += ';position:absolute;left:calc(80*var(--u));top:calc(120*var(--u))';
    const cam = rig(win);
    frame.appendChild(cam);
    el.appendChild(frame);

    const h = headline({ en: ctx.shot.headlineEn, zh: ctx.shot.headline, desc: ctx.shot.description });
    h.style.cssText = ctx.portrait
      ? 'position:absolute;left:calc(64*var(--u));right:calc(64*var(--u));top:calc(140*var(--u))'
      : 'position:absolute;left:calc(62% + 48*var(--u));right:calc(80*var(--u));top:calc(360*var(--u))';
    el.appendChild(h);

    const btn = panel.querySelector('.sample-btn');
    ctx.cam = cam;
    ctx.push = focusOn(cam, btn, frame, 1.6, { x: 0.5, y: 0.55 });
    ctx.cursor = cursor(win.querySelector('.dev-body'));
    ctx.btnPoint = pointOf(btn, win.querySelector('.dev-body'));
    ctx.mask = focusMask(win.querySelector('.dev-body'));
    ctx.btnRect = rectOf(btn, win.querySelector('.dev-body'));
    ctx.result = panel.querySelector('.sample-result');
    ctx.headline = h;
  },
  build(tl, ctx) {
    const beat = (a) => ctx.shot.actions?.find((x) => x.id === a)?.at ?? 1.2;
    tl.from(ctx.headline, { opacity: 0, x: 30, duration: 0.5, ease: 'power3.out' }, 0);
    tl.fromTo(ctx.cam, { x: 0, y: 0, scale: 1 }, { ...ctx.push, duration: 1.1, ease: 'power3.inOut' }, 0.2);
    tl.set(ctx.cursor, { x: ctx.btnPoint.x + 260, y: ctx.btnPoint.y - 160 }, 0);
    focusTo(tl, ctx.mask, ctx.btnRect, 0.6);
    moveAndClick(tl, ctx.cursor, ctx.btnPoint, beat('click'));
    tl.to(ctx.result, { backgroundColor: 'rgba(124,140,255,.25)', color: '#fff', duration: 0.3 }, beat('click') + 0.1);
  },
};
