// Film UI helpers: captions, rig, cursor. Copyright (c) 向阳乔木 — MIT License.
import { splitChars } from '../kit/text.js';

export function caption(parent, { en = '', zh = '', desc = '' } = {}) {
  const box = parent.createDiv ? parent.createDiv({ cls: 'cap' }) : Object.assign(parent.appendChild(document.createElement('div')), { className: 'cap' });
  const add = (cls, text) => { if (!text) return null; const d = document.createElement('div'); d.className = cls; d.textContent = text; box.appendChild(d); return d; };
  const e = add('cap-en', en), z = add('cap-zh', zh), d = add('cap-desc', desc);
  return { box, en: e, zh: z, desc: d, chars: z ? splitChars(z) : [] };
}

/** Reveal a caption: English fades up, Chinese characters sharpen one by one, description follows. */
export function revealCaption(tl, c, at, { descAt = null } = {}) {
  if (c.en) tl.fromTo(c.en, { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: 0.45, ease: 'power2.out' }, at);
  if (c.chars.length) tl.fromTo(c.chars, { opacity: 0, filter: 'blur(10px)' }, { opacity: 1, filter: 'blur(0px)', duration: 0.5, stagger: 0.03, ease: 'power2.out' }, at + 0.1);
  if (c.desc) tl.fromTo(c.desc, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power2.out' }, descAt ?? at + 0.45);
  return tl;
}
export function hideCaption(tl, c, at) {
  tl.to(c.box, { opacity: 0, y: -6, duration: 0.3, ease: 'power2.in' }, at);
  tl.set(c.box, { opacity: 0 }, at + 0.31);
  return tl;
}

export function div(parent, cls, style = '') {
  const d = document.createElement('div');
  d.className = cls;
  if (style) d.style.cssText = style;
  parent.appendChild(d);
  return d;
}
