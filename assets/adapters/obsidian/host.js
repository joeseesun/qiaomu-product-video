// Film host: an Obsidian-like workspace shell that runs a real plugin with the shim.
// Copyright (c) 向阳乔木 — MIT License.
import { App, Notice, net, setIcon, filmClock } from './obsidian.js';

export function createHost({ width = 1600, height = 900, split = '38%' } = {}) {
  const root = document.createElement('div');
  root.className = 'qfilm-host';
  Object.assign(root.style, { width: `${width}px`, height: `${height}px` });
  root.style.setProperty('--qfilm-split', split);
  root.innerHTML = `
    <div class="qfilm-titlebar"><div class="qfilm-traffic"><i></i><i></i><i></i></div>
      <div class="qfilm-tabs"><div class="qfilm-tabgroup" data-group="main"></div><div class="qfilm-tabgroup" data-group="split" hidden></div></div></div>
    <div class="qfilm-body"><div class="qfilm-ribbon"></div>
      <div class="qfilm-panes"><div class="qfilm-pane" data-pane="main"></div><div class="qfilm-pane" data-pane="split"></div></div></div>`;
  const pane = (p) => root.querySelector(`.qfilm-pane[data-pane=${p === 'split' ? 'split' : 'main'}]`);
  const shell = {
    root,
    place(leaf) {
      const p = pane(leaf.pane);
      if (leaf.containerEl.parentElement !== p) p.appendChild(leaf.containerEl);
      if (leaf.pane === 'split') { p.classList.add('is-open'); root.querySelector('[data-group=split]').hidden = false; }
    },
    tabs(leaves) {
      for (const g of ['main', 'split']) {
        const bar = root.querySelector(`[data-group=${g}]`);
        bar.innerHTML = '';
        const mine = leaves.filter((l) => (l.pane === 'split' ? 'split' : 'main') === g && l.view);
        mine.forEach((l, i) => {
          const tab = bar.createDiv({ cls: `qfilm-tab${i === mine.length - 1 ? ' is-active' : ''}` });
          setIcon(tab.createSpan(), l.view.getIcon?.() || (l.view.getViewType() === 'markdown' ? 'file-text' : 'rss'));
          tab.createSpan({ text: l.view.getDisplayText?.() || '' });
        });
      }
    },
    reveal() {},
    ribbon(icon, title) {
      const b = root.querySelector('.qfilm-ribbon').createDiv({ cls: 'clickable-icon', attr: { 'aria-label': title } });
      setIcon(b, icon);
      return b;
    },
  };
  for (const icon of ['files', 'search', 'bookmark', 'calendar-days', 'git-fork', 'layout-dashboard']) shell.ribbon(icon, icon);
  return shell;
}

/** Wait until the plugin is quiet: no requests in flight, images decoded, microtasks flushed. */
export async function idle(root, { timeout = 8000 } = {}) {
  const until = performance.now() + timeout;
  for (;;) {
    await new Promise((r) => setTimeout(r, 30));
    const vw = innerWidth, vh = innerHeight;
    const visible = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.bottom > 0 && r.right > 0 && r.top < vh && r.left < vw; };
    // lazy images outside the viewport never load; only wait for what can be seen
    const busy = net.pending > 0 || [...root.querySelectorAll('img')].some((i) => i.src && !i.complete && visible(i));
    if (!busy || performance.now() > until) break;
  }
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
}

/** Boot the real plugin class inside a host. */
export async function bootPlugin({ PluginClass, manifest, shell, data = null, fixtures = {}, record = false, date }) {
  net.fixtures = fixtures; net.record = record;
  if (date) filmClock.now = new Date(date);
  const app = new App(shell);
  const plugin = new PluginClass(app, manifest);
  plugin._data = data;
  app.plugins.plugins[manifest.id] = plugin;
  await plugin.onload();
  plugin._loaded = true;
  return { app, plugin, Notice };
}
