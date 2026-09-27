// Text helpers: split into spans for per-character motion; bilingual headline block.
// Copyright (c) 向阳乔木 — MIT License.

/** Wrap every character of el's text in <span class="ch">. Returns the spans. */
export function splitChars(el) {
  const text = el.textContent;
  el.textContent = '';
  const spans = [];
  for (const ch of text) {
    const s = document.createElement('span');
    s.className = 'ch';
    s.textContent = ch;
    if (ch === ' ') s.style.whiteSpace = 'pre';
    el.appendChild(s);
    spans.push(s);
  }
  return spans;
}

/**
 * Bilingual headline: English short line + Chinese headline + optional Chinese explanation,
 * each its own element with its own font variable (never rely on font fallback).
 */
export function headline({ en = '', zh = '', desc = '', className = '' } = {}) {
  const box = document.createElement('div');
  box.className = `headline ${className}`.trim();
  if (en) box.insertAdjacentHTML('beforeend', `<div class="hl-en" lang="en"></div>`);
  if (zh) box.insertAdjacentHTML('beforeend', `<div class="hl-zh" lang="zh"></div>`);
  if (desc) box.insertAdjacentHTML('beforeend', `<p class="hl-desc" lang="zh"></p>`);
  if (en) box.querySelector('.hl-en').textContent = en;
  if (zh) box.querySelector('.hl-zh').textContent = zh;
  if (desc) box.querySelector('.hl-desc').textContent = desc;
  return box;
}

/** Characters visible at local time t when typing `text` from t0 at `cps` characters/second. */
export function typedAt(text, t, t0 = 0, cps = 18) {
  const n = Math.max(0, Math.floor((t - t0) * cps));
  return [...text].slice(0, n).join('');
}
