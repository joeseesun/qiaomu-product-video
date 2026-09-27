// Springs as pure functions of time (seek-safe): no state, no timers, no GSAP.
// Copyright (c) 向阳乔木 — MIT License.
//
// springStep(t)   closed-form step response of a damped spring, 0 at t<=0 → 1 at rest.
// springTrack()   a value whose target changes many times is the SUM of one spring per change,
//                 so it stays a pure function of t and can be sought to any frame in any order.
// Two edges on different springs (leading stiffer than trailing) give the "stretchy" tab indicator
// or toggle knob without any simulation.

export const SPRINGS = {
  snappy: { stiffness: 260, damping: 30 },  // UI state changes, tiny overshoot at most
  smooth: { stiffness: 170, damping: 26 },  // camera moves, panels (≈ critically damped)
  gentle: { stiffness: 90, damping: 19 },   // large, slow reveals
  lively: { stiffness: 220, damping: 18 },  // visible overshoot — use sparingly, and not on text
};

export function springStep(t, { stiffness = 170, damping = 26, mass = 1 } = {}) {
  if (t <= 0) return 0;
  const w0 = Math.sqrt(stiffness / mass);
  const zeta = damping / (2 * Math.sqrt(stiffness * mass));
  if (zeta < 1) {
    const wd = w0 * Math.sqrt(1 - zeta * zeta);
    return 1 - Math.exp(-zeta * w0 * t) * (Math.cos(wd * t) + ((zeta * w0) / wd) * Math.sin(wd * t));
  }
  if (zeta === 1) return 1 - Math.exp(-w0 * t) * (1 + w0 * t);
  const s = Math.sqrt(zeta * zeta - 1);
  const r1 = -w0 * (zeta - s);
  const r2 = -w0 * (zeta + s);
  return 1 - (r2 * Math.exp(r1 * t) - r1 * Math.exp(r2 * t)) / (r2 - r1);
}

/** Seconds until the response stays within eps of 1 — use it to size shot lengths. */
export function settleTime(opts, eps = 0.002, maxT = 5) {
  let last = 0;
  for (let t = 0; t <= maxT; t += 1 / 240) if (Math.abs(1 - springStep(t, opts)) > eps) last = t;
  return last;
}

/**
 * keys: [{ t, v, spring? }] sorted by t; keys[0].v is the value before the first change.
 * Returns value at time `t`. Numbers only; animate each channel (x, width, radius…) separately.
 */
export function springTrack(keys, t, defaults = SPRINGS.smooth) {
  let v = keys[0].v;
  for (let i = 1; i < keys.length; i++) {
    const k = keys[i];
    if (t <= k.t) break;
    v += (k.v - keys[i - 1].v) * springStep(t - k.t, k.spring || defaults);
  }
  return v;
}

/** Leading/trailing edges for a stretchy indicator moving between [left, right] spans. */
export function stretchySpan(spans, t, { lead = SPRINGS.snappy, trail = SPRINGS.gentle } = {}) {
  // spans: [{ t, left, right }]; the edge in the direction of travel uses `lead`.
  const leftKeys = [{ v: spans[0].left }];
  const rightKeys = [{ v: spans[0].right }];
  for (let i = 1; i < spans.length; i++) {
    const forward = spans[i].left > spans[i - 1].left;
    leftKeys.push({ t: spans[i].t, v: spans[i].left, spring: forward ? trail : lead });
    rightKeys.push({ t: spans[i].t, v: spans[i].right, spring: forward ? lead : trail });
  }
  return { left: springTrack(leftKeys, t), right: springTrack(rightKeys, t) };
}
