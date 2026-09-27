// Focus: dim / blur everything except one rectangle. A framing layer — never edits the component.
// Copyright (c) 向阳乔木 — MIT License.

export function focusMask(parent) {
  const m = document.createElement('div');
  m.className = 'film-focus';
  m.innerHTML = '<div class="film-focus-hole"></div>';
  parent.appendChild(m);
  return m;
}

/** Rect of target relative to parent (untransformed), padded. */
export function rectOf(target, parent, pad = 12) {
  const a = target.getBoundingClientRect();
  const b = parent.getBoundingClientRect();
  return { x: a.left - b.left - pad, y: a.top - b.top - pad, w: a.width + pad * 2, h: a.height + pad * 2 };
}

/** Tween the mask onto rect; strength 0..1 controls dimming. */
export function focusTo(tl, mask, rect, at, { strength = 0.62, duration = 0.5, radius = 14 } = {}) {
  const hole = mask.querySelector('.film-focus-hole');
  tl.to(hole, { left: rect.x, top: rect.y, width: rect.w, height: rect.h, borderRadius: radius,
    duration, ease: 'power3.inOut' }, at);
  tl.to(mask, { '--dim': strength, duration, ease: 'power2.out' }, at);
  return tl;
}
