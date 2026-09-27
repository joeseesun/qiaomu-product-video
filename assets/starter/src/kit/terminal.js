// Terminal replay: render a recorded asciicast v2 (from scripts/record_terminal.py) at time t.
// Real output, real timing (optionally compressed). Supports basic SGR colours.
// Copyright (c) 向阳乔木 — MIT License.

const COLORS = ['#1e1e1e', '#ff6b6b', '#4ade80', '#facc15', '#60a5fa', '#c084fc', '#22d3ee', '#e5e5e5'];
const BRIGHT = ['#6b7280', '#ff8787', '#86efac', '#fde047', '#93c5fd', '#d8b4fe', '#67e8f9', '#ffffff'];

export function parseCast(text) {
  const lines = text.trim().split('\n');
  const header = JSON.parse(lines[0]);
  const events = lines.slice(1).map((l) => JSON.parse(l)).filter((e) => e[1] === 'o').map(([at, , data]) => ({ at, data }));
  return { header, events };
}

/** Output text up to time t. `speed` compresses time; `maxGap` caps idle waits (seconds, recorded time). */
export function outputAt(cast, t, { speed = 1, maxGap = 0.6 } = {}) {
  let clock = 0;
  let prev = 0;
  let out = '';
  for (const e of cast.events) {
    clock += Math.min(e.at - prev, maxGap) / speed;
    prev = e.at;
    if (clock > t) break;
    out += e.data;
  }
  return out;
}

function escapeHtml(s) {
  return s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
}

/** Minimal ANSI → HTML: SGR colours/bold/dim; strips other escapes; handles \r and backspace. */
export function ansiToHtml(raw) {
  const lines = [''];
  for (const chunk of raw.replace(/\x1b\][^\x07]*\x07/g, '').split('\n')) {
    let line = '';
    for (const part of chunk.split('\r')) line = part.length >= line.length ? part : part + line.slice(part.length);
    lines.push(line);
  }
  const text = lines.slice(1).join('\n').replace(/.\x08/g, '');
  let html = '';
  let open = false;
  let last = 0;
  const re = /\x1b\[([0-9;?]*)([A-Za-z])/g;
  let m;
  while ((m = re.exec(text))) {
    html += escapeHtml(text.slice(last, m.index));
    last = re.lastIndex;
    if (m[2] !== 'm') continue;
    const codes = (m[1] || '0').split(';').map(Number);
    const style = [];
    for (const c of codes) {
      if (c === 1) style.push('font-weight:700');
      else if (c === 2) style.push('opacity:.6');
      else if (c >= 30 && c <= 37) style.push(`color:${COLORS[c - 30]}`);
      else if (c >= 90 && c <= 97) style.push(`color:${BRIGHT[c - 90]}`);
    }
    if (open) { html += '</span>'; open = false; }
    if (style.length) { html += `<span style="${style.join(';')}">`; open = true; }
  }
  html += escapeHtml(text.slice(last));
  if (open) html += '</span>';
  return html;
}

export function terminalView({ title = 'terminal' } = {}) {
  const el = document.createElement('div');
  el.className = 'term';
  el.innerHTML = `<div class="term-bar"><i></i><i></i><i></i><span></span></div><pre class="term-body"></pre>`;
  el.querySelector('.term-bar span').textContent = title;
  return el;
}

/** Render the replay into a terminalView at local time t; keeps the last `rows` lines. */
export function drawTerminal(view, cast, t, { rows = 18, ...opts } = {}) {
  const out = outputAt(cast, t, opts);
  const tail = out.split('\n').slice(-rows).join('\n');
  const body = view.querySelector('.term-body');
  const html = ansiToHtml(tail) + '<span class="term-caret">▍</span>';
  if (body.innerHTML !== html) body.innerHTML = html;
}
