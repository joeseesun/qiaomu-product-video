// Streaming text for AI / agent replies: the visible prefix is a pure function of time.
// Copyright (c) 向阳乔木 — MIT License.

/**
 * events: [{at, text}] chunks with the time they arrived in the recorded run (seconds).
 * speed compresses recorded time (2 = twice as fast) while keeping the order of steps.
 */
export function streamAt(events, t, { speed = 1, cps = 40 } = {}) {
  let out = '';
  for (const e of events) {
    const start = e.at / speed;
    if (t < start) break;
    const n = Math.floor((t - start) * cps);
    out += n >= e.text.length ? e.text : e.text.slice(0, n);
    if (n < e.text.length) break;
  }
  return out;
}
