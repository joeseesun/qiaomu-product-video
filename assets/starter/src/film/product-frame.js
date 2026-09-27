// Product frames for the film: each shot owns a same-origin iframe running the real plugin.
// Steps are async actions at shot-local times; a rehearsal pass records measured rects (marks)
// so camera moves in build() can target real layout. Seeking backwards replays from a fresh boot.
// Copyright (c) 向阳乔木 — MIT License.

export async function productFrame(parent, { w = 1600, h = 900, params = {} } = {}) {
  const iframe = document.createElement('iframe');
  const q = new URLSearchParams({ w, h, ...params });
  iframe.src = `product.html?${q}`;
  Object.assign(iframe.style, { position: 'absolute', left: '0', top: '0', width: `${w}px`, height: `${h}px`, border: '0', background: '#fff' });
  parent.appendChild(iframe);
  await new Promise((r) => iframe.addEventListener('load', r, { once: true }));
  await iframe.contentWindow.__productReady;
  return iframe;
}

/**
 * steps: [{ at, run: async (api, ctx) => {} }] sorted by `at` (shot-local seconds).
 * setup: async (api, ctx) => {} runs after every boot (state before the shot begins).
 * track: (local, api, ctx) => {} runs every seek for continuous, time-derived state.
 */
export function director({ iframe, setup, steps = [], track }) {
  const d = {
    iframe, done: 0, last: -1, marks: {},
    get api() { return iframe.contentWindow.__product; },
    mark(name, value) { d.marks[name] = value; return value; },
    async reset() {
      await iframe.contentWindow.__product.reboot();
      d.done = 0; d.last = -1;
      await setup?.(d.api, d);
      await d.api.idle();
    },
    async rehearse(until = Infinity) {
      await d.reset();
      for (const s of steps) if (s.at <= until) { await s.run(d.api, d); await d.api.idle(); }
      const marks = { ...d.marks };
      await d.reset();
      d.marks = marks;
      return marks;
    },
    async drive(local) {
      if (local < d.last - 1e-6 && steps.slice(0, d.done).some((s) => s.at > local)) await d.reset();
      while (d.done < steps.length && steps[d.done].at <= local + 1e-6) {
        await steps[d.done].run(d.api, d);
        await d.api.idle();
        d.done++;
      }
      track?.(local, d.api, d);
      d.last = local;
    },
  };
  return d;
}

/** Camera transform that puts host point (px, py) at frame point (fx, fy) with scale s. */
export function cam(px, py, s, fx = 960, fy = 540) {
  return { x: fx - px * s, y: fy - py * s, scale: s };
}
