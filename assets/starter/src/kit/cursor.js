// Cursor: a pointer that moves in the product's coordinate space and "clicks" on beats.
// Copyright (c) 向阳乔木 — MIT License.

const SVG = `<svg viewBox="0 0 24 24" width="36" height="36"><path d="M4 2l15 11-6.5 1.2L9 21z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>`;

export function cursor(parent) {
  const el = document.createElement('div');
  el.className = 'film-cursor';
  el.innerHTML = SVG + '<i class="film-ripple"></i>';
  parent.appendChild(el);
  return el;
}

/** Centre of target relative to container (both untransformed at call time). */
export function pointOf(target, container) {
  const a = target.getBoundingClientRect();
  const b = container.getBoundingClientRect();
  return { x: a.left - b.left + a.width / 2, y: a.top - b.top + a.height / 2 };
}

/** Add move + click to tl: arrive at `at`, click ripple at `at`. Short, decisive paths read as speed. */
export function moveAndClick(tl, cur, point, at, { travel = 0.45, ease = 'power3.inOut' } = {}) {
  tl.to(cur, { x: point.x, y: point.y, duration: travel, ease }, at - travel);
  tl.fromTo(cur.querySelector('.film-ripple'), { scale: 0, opacity: 0.55 },
    { scale: 2.6, opacity: 0, duration: 0.45, ease: 'power2.out' }, at);
  tl.to(cur, { scale: 0.88, duration: 0.08, yoyo: true, repeat: 1 }, at);
  return tl;
}
