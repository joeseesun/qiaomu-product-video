// qiaomu-product-video runtime — every pixel is a function of film time t.
// Copyright (c) 向阳乔木 — MIT License.
//
// A shot module may export:
//   view(el, ctx)      mount DOM / real components into el (may be async)
//   build(tl, ctx)     add GSAP tweens to tl; tl time 0 = shot start
//   drive(local, ctx)  push time-derived state into real components (may be async)
//   render(local, ctx) draw canvas/WebGL for this local time (pure function of local)
// Times always come from plan.json; never hard-code shot boundaries in code.

import { gsap } from 'gsap';

const params = new URLSearchParams(location.search);

export function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function aspectOf(d, plan) {
  const [w, h] = (d?.aspect || '16:9').split(':').map(Number);
  const base = plan.format || { width: 1920, height: 1080 };
  // keep the short side at 1080 (or plan's short side) for every aspect
  const short = Math.min(base.width, base.height);
  return w >= h ? { width: Math.round((short * w) / h), height: short } : { width: short, height: Math.round((short * h) / w) };
}

function freezeNondeterminism(seed) {
  Math.random = mulberry32(seed);
  const fixed = Date.parse('2026-01-01T10:00:00Z');
  const RealDate = Date;
  class FrozenDate extends RealDate {
    constructor(...a) { super(...(a.length ? a : [fixed])); }
    static now() { return fixed; }
  }
  window.Date = FrozenDate;
  const style = document.createElement('style');
  style.textContent = `*:not(.film-keep-anim),*::before,*::after{transition:none!important;animation:none!important;caret-color:transparent}`;
  document.head.appendChild(style);
}

function installFetchFixtures(fixtures, log) {
  if (!fixtures) return;
  const realFetch = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const url = new URL(typeof input === 'string' ? input : input.url, location.href);
    const key = url.pathname + url.search;
    const hit = fixtures[key] ?? fixtures[url.pathname];
    if (hit !== undefined) {
      const body = typeof hit === 'function' ? await hit(url, init) : hit;
      return new Response(typeof body === 'string' ? body : JSON.stringify(body), {
        status: 200, headers: { 'content-type': 'application/json' },
      });
    }
    if (url.origin === location.origin && !url.pathname.startsWith('/api')) return realFetch(input, init);
    log.push(key);
    console.warn('[film] no fixture for', key);
    return new Response('{}', { status: 404, headers: { 'content-type': 'application/json' } });
  };
}

async function settle(root) {
  if (document.fonts) await document.fonts.ready;
  const imgs = [...root.querySelectorAll('img')];
  await Promise.all(imgs.map((img) => (img.complete ? null : img.decode().catch(() => null))));
  const broken = imgs.filter((img) => !(img.complete && img.naturalWidth > 0)).map((img) => img.src);
  if (broken.length) console.error('[film] broken images:', broken.join(', '));
}

const nextFrame = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));

export async function startFilm({ plan, shots, fixtures = null, seed = 7 }) {
  freezeNondeterminism(seed);
  const missingFixtures = [];
  installFetchFixtures(fixtures, missingFixtures);

  const deliverableId = params.get('d') || plan.deliverables?.[0]?.id || 'hero';
  const deliverable = plan.deliverables?.find((d) => d.id === deliverableId) || { id: deliverableId, aspect: '16:9' };
  const { width, height } = aspectOf(deliverable, plan);
  const aspectKey = (deliverable.aspect || '16:9').replace(':', 'x');
  const fps = plan.format?.fps || 30;
  const only = deliverable.shots ? new Set(deliverable.shots) : null;

  // A deliverable with its own shot list is re-timed back to back from 0.
  let cursor = 0;
  const timeline = plan.shots
    .filter((s) => !only || only.has(s.id))
    .map((s) => {
      const len = s.end - s.start;
      const start = only ? cursor : s.start;
      cursor = start + len;
      return { ...s, start, end: start + len };
    });
  const duration = only ? cursor : plan.duration;

  document.documentElement.dataset.aspect = aspectKey;
  document.documentElement.dataset.deliverable = deliverable.id;
  const stage = document.getElementById('stage');
  Object.assign(stage.style, { width: `${width}px`, height: `${height}px` });
  // 1u = 1px at 1080 short side; size everything in u so re-layouts keep proportions
  stage.style.setProperty('--u', `${Math.min(width, height) / 1080}px`);

  const entries = [];
  for (const s of timeline) {
    const impl = shots[s.id];
    if (!impl) { console.error(`[film] shot "${s.id}" has no implementation in src/shots/index.js`); continue; }
    const el = document.createElement('section');
    el.className = `shot shot-${s.id}`;
    el.dataset.shot = s.id;
    el.style.visibility = 'hidden';
    stage.appendChild(el);
    const ctx = {
      plan, shot: s, stage, el, width, height, fps, aspect: aspectKey, deliverable,
      random: mulberry32(seed + entries.length * 101),
      portrait: height > width,
    };
    entries.push({ s, impl, el, ctx });
  }
  for (const e of entries) await e.impl.view?.(e.el, e.ctx);
  await settle(stage);

  gsap.ticker.lagSmoothing(0);
  const master = gsap.timeline({ paused: true });
  for (const e of entries) {
    const tl = gsap.timeline();
    e.impl.build?.(tl, e.ctx);
    master.add(tl, e.s.start);
  }
  // keep the master at least as long as the film so seek(t) is always valid
  master.set({}, {}, duration);

  let last = -1;
  async function seek(t) {
    t = Math.max(0, Math.min(t, duration));
    const active = [];
    for (const e of entries) {
      const on = t >= e.s.start && (t < e.s.end || (e.s.end >= duration && t <= duration));
      e.el.style.visibility = on ? 'visible' : 'hidden';
      if (on) active.push(e);
    }
    for (const e of active) await e.impl.drive?.(t - e.s.start, e.ctx);
    master.seek(t, false);
    for (const e of active) e.impl.render?.(t - e.s.start, e.ctx);
    last = t;
    await nextFrame();
    return t;
  }

  const placeholders = () => [...stage.querySelectorAll('[data-film-placeholder]')]
    .filter((n) => n.closest('.shot')?.style.visibility === 'visible').length;

  window.__film = {
    duration, fps, width, height, deliverable: deliverable.id, seek,
    now: () => last, missingFixtures, placeholders,
    shots: timeline.map(({ id, start, end }) => ({ id, start, end })),
  };
  await seek(0);

  if (params.has('preview')) runPreview(duration, seek);
  return window.__film;
}

function runPreview(duration, seek) {
  const bar = document.createElement('input');
  Object.assign(bar, { type: 'range', min: 0, max: duration, step: 0.001, value: 0 });
  bar.className = 'film-scrubber';
  document.body.appendChild(bar);
  let playing = true;
  let t0 = performance.now();
  let base = 0;
  let busy = false;
  bar.addEventListener('input', () => { base = Number(bar.value); t0 = performance.now(); seek(base); });
  addEventListener('keydown', (ev) => {
    if (ev.code === 'Space') { playing = !playing; base = Number(bar.value); t0 = performance.now(); }
  });
  const loop = async () => {
    if (playing && !busy) {
      busy = true;
      const t = (base + (performance.now() - t0) / 1000) % duration;
      bar.value = t;
      await seek(t);
      busy = false;
    }
    requestAnimationFrame(loop);
  };
  loop();
}

/** Screen-space center of an element at film time t (restores the current time afterwards). */
export async function screenCenterAt(el, t) {
  const back = window.__film.now();
  await window.__film.seek(t);
  const r = el.getBoundingClientRect();
  await window.__film.seek(back);
  return { x: r.left + r.width / 2, y: r.top + r.height / 2, width: r.width, height: r.height };
}

export { gsap };
