// Product frame: boots the real Obsidian plugin inside an Obsidian-like host.
// Loaded in an iframe per shot so viewport-fixed popups, selection and rects stay self-consistent
// under the film camera. The parent drives it through window.__product.
import './host/host.css';
import '<PRODUCT_REPO>/styles.css'   // the plugin's own stylesheet;
import PluginClass from 'product/main.ts'           // alias "product" → <PRODUCT_REPO>/src in film.config.json;
import manifest from '<PRODUCT_REPO>/manifest.json';
import { createHost, bootPlugin, idle } from './host/host.js';
import { net, Notice, Menu } from './host/obsidian.js';

const params = new URLSearchParams(location.search);
const W = Number(params.get('w') || 1600), H = Number(params.get('h') || 900);

let fixturesPromise;
function fixtures() {
  fixturesPromise ||= fetch(params.get('fixtures') || 'src/fixtures/requests.json').then((r) => (r.ok ? r.json() : {})).catch(() => ({}));
  return fixturesPromise;
}

/** Find the text node containing `text` inside root; returns a Range over it. */
function rangeOf(root, text, upto = text.length) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    const i = node.textContent.indexOf(text);
    if (i >= 0) { const r = document.createRange(); r.setStart(node, i); r.setEnd(node, i + Math.max(0, Math.min(upto, text.length))); return r; }
  }
  return null;
}

async function boot() {
  document.body.innerHTML = '';
  const shell = createHost({ width: W, height: H, split: params.get('split') || '38%' });
  if (params.get('accent')) document.documentElement.style.setProperty('--qfilm-accent', params.get('accent'));
  if (params.get('layout')) shell.root.dataset.layout = params.get('layout');
  document.body.appendChild(shell.root);
  Notice.log.length = 0;
  const { app, plugin } = await bootPlugin({ PluginClass, manifest, shell, fixtures: params.has('record') ? {} : await fixtures(), record: params.has('record'), date: '2026-09-26T09:30:00+08:00' });
  await plugin.openReader();
  await idle(shell.root);
  const api = {
    app, plugin, shell, net, notices: Notice.log, root: shell.root, doc: document,
    idle: () => idle(shell.root),
    $: (s) => (typeof s === 'string' ? document.querySelector(s) : s),
    $$: (s) => [...document.querySelectorAll(s)],
    /** Rect of an element (or a Range) in product-viewport px. */
    rect(target) {
      const el = typeof target === 'string' ? document.querySelector(target) : target;
      if (!el) throw new Error(`rect: nothing matches ${target}`);
      const r = el.getBoundingClientRect();
      return { x: r.left, y: r.top, w: r.width, h: r.height, cx: r.left + r.width / 2, cy: r.top + r.height / 2 };
    },
    async click(target) {
      const el = typeof target === 'string' ? document.querySelector(target) : target;
      if (!el) throw new Error(`click: nothing matches ${target}`);
      el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
      el.click();
      await new Promise((r) => setTimeout(r, 30));
      await idle(shell.root);
    },
    async openEntry(title) {
      const entry = [...document.querySelectorAll('.qrs-entry')].find((e) => e.textContent.includes(title));
      if (!entry) throw new Error(`no entry ${title}`);
      await api.click(entry);
    },
    rangeOf: (text, upto) => rangeOf(document.querySelector('.qrs-reader') || document.body, text, upto),
    /** Select `upto` characters of `text` like a user dragging, then let the plugin react (pointerup). */
    async select(text, upto = text.length, { release = false } = {}) {
      const r = rangeOf(document.querySelector('.qrs-prose') || document.body, text, upto);
      if (!r) throw new Error(`select: text not found: ${text}`);
      const sel = document.getSelection(); sel.removeAllRanges(); sel.addRange(r);
      if (release) { document.querySelector('.qrs-prose').dispatchEvent(new PointerEvent('pointerup', { bubbles: true })); await new Promise((r) => setTimeout(r, 20)); }
      return r;
    },
    clearSelection() { document.getSelection().removeAllRanges(); },
    /** Scroll a text into view and let scroll events settle (plugins often clear popups on scroll). */
    async scrollTo(text, block = 'center') {
      const r = rangeOf(document.querySelector('.qrs-reader'), text);
      const el = r?.startContainer.parentElement;
      el?.scrollIntoView({ block });
      await new Promise((res) => requestAnimationFrame(() => requestAnimationFrame(res)));
      await new Promise((res) => setTimeout(res, 50));
      await idle(shell.root);
    },
    dismissNotices() { for (const n of [...document.querySelectorAll('.notice')]) n.remove(); },
    closeMenus() { Menu.last?.hide(); },
    async keys(key) { document.querySelector('.qrs-root').dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true })); await idle(shell.root); },
    async save(name = 'requests') { await fetch(`/__record?name=${name}`, { method: 'POST', body: JSON.stringify({ ...(await fixtures()), ...net.recorded }) }); },
    reboot: boot,
  };
  window.__product = api;
  return api;
}

window.__productReady = boot();
