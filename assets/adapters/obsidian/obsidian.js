// Obsidian API shim for filming a real Obsidian plugin outside the app.
// Implements the subset a plugin's UI needs: DOM helpers, Component/Plugin/ItemView, an in-memory
// vault, a workspace that places leaves into film panes, Menu/Modal/Notice, requestUrl backed by
// recorded fixtures, and Lucide icons for setIcon. The plugin's own code runs unmodified.
// Copyright (c) 向阳乔木 — MIT License.
import * as lucide from 'lucide-static';
import { marked } from 'marked';

/* ------------------------------------------------------------------ DOM helpers */
function applyInfo(el, info) {
  if (info == null) return;
  if (typeof info === 'string') info = { cls: info };
  if (info.cls) for (const c of [].concat(info.cls)) String(c).split(/\s+/).filter(Boolean).forEach((x) => el.classList.add(x));
  if (info.text != null) {
    if (info.text instanceof Node) el.appendChild(info.text); else el.textContent = String(info.text);
  }
  if (info.attr) for (const [k, v] of Object.entries(info.attr)) if (v !== null && v !== undefined && v !== false) el.setAttribute(k, v === true ? '' : String(v));
  for (const k of ['title', 'placeholder', 'type', 'value', 'href']) if (info[k] != null) el.setAttribute(k, info[k]);
  if (info.value != null && 'value' in el) el.value = info.value;
  if (info.parent) info.parent.appendChild(el);
}
function createEl(tag, info, cb) {
  const el = document.createElement(tag);
  applyInfo(el, info);
  cb?.(el);
  return el;
}
const P = Node.prototype;
P.createEl = function (tag, info, cb) {
  const el = document.createElement(tag);
  applyInfo(el, info);
  if (info && typeof info === 'object' && info.prepend) this.insertBefore(el, this.firstChild); else this.appendChild(el);
  cb?.(el);
  return el;
};
P.createDiv = function (info, cb) { return this.createEl('div', info, cb); };
P.createSpan = function (info, cb) { return this.createEl('span', info, cb); };
P.createSvg = function (tag, info, cb) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  applyInfo(el, info); this.appendChild(el); cb?.(el); return el;
};
P.empty = function () { while (this.firstChild) this.removeChild(this.firstChild); };
P.detach = function () { this.parentNode?.removeChild(this); };
P.setText = function (t) { this.textContent = t instanceof Node ? '' : String(t); if (t instanceof Node) this.appendChild(t); };
P.appendText = function (t) { this.appendChild(document.createTextNode(t)); };
P.instanceOf = function (T) { return this instanceof T; };
P.indexOf = function (child) { return Array.prototype.indexOf.call(this.childNodes, child); };
Object.defineProperty(P, 'doc', { get() { return this.ownerDocument || document; }, configurable: true });
Object.defineProperty(P, 'win', { get() { return (this.ownerDocument || document).defaultView || window; }, configurable: true });
const E = Element.prototype;
E.addClass = function (...c) { c.flat().forEach((x) => x && this.classList.add(...String(x).split(/\s+/).filter(Boolean))); };
E.addClasses = function (c) { this.addClass(...c); };
E.removeClass = function (...c) { c.flat().forEach((x) => x && this.classList.remove(...String(x).split(/\s+/).filter(Boolean))); };
E.removeClasses = function (c) { this.removeClass(...c); };
E.toggleClass = function (c, v) { [].concat(c).forEach((x) => this.classList.toggle(x, v)); };
E.hasClass = function (c) { return this.classList.contains(c); };
E.setAttr = function (k, v) { if (v === null || v === undefined || v === false) this.removeAttribute(k); else this.setAttribute(k, v === true ? '' : String(v)); };
E.setAttrs = function (o) { for (const [k, v] of Object.entries(o)) this.setAttr(k, v); };
E.getAttr = function (k) { return this.getAttribute(k); };
E.getText = function () { return this.textContent; };
E.find = function (s) { return this.querySelector(s); };
E.findAll = function (s) { return [...this.querySelectorAll(s)]; };
E.matchParent = function (s, last) { const m = this.closest(s); return m && (!last || last.contains(m)) ? m : null; };
E.setCssProps = function (o) { for (const [k, v] of Object.entries(o)) this.style.setProperty(k, v); };
E.setCssStyles = function (o) { Object.assign(this.style, o); };
E.show = function () { this.style.display = ''; };
E.hide = function () { this.style.display = 'none'; };
E.toggle = function (v) { this.style.display = v ? '' : 'none'; };
E.toggleVisibility = function (v) { this.style.visibility = v ? '' : 'hidden'; };
E.isShown = function () { return !!this.offsetParent; };
E.onClickEvent = function (fn, o) { this.addEventListener('click', fn, o); };
E.trigger = function (type) { this.dispatchEvent(new Event(type, { bubbles: true })); };
Object.assign(window, {
  createEl, createDiv: (i, c) => createEl('div', i, c), createSpan: (i, c) => createEl('span', i, c),
  createFragment: (cb) => { const f = document.createDocumentFragment(); cb?.(f); return f; },
  activeDocument: document, activeWindow: window, sleep: (ms) => new Promise((r) => setTimeout(r, ms)),
});

/* ------------------------------------------------------------------ icons */
const customIcons = new Map();
const pascal = (n) => n.replace(/^lucide-/, '').split('-').map((p) => p[0]?.toUpperCase() + p.slice(1)).join('');
export function getIcon(name) {
  const custom = customIcons.get(name);
  const raw = custom ? `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="24" height="24">${custom}</svg>` : lucide[pascal(name)];
  if (!raw) return null;
  const tpl = document.createElement('template');
  tpl.innerHTML = raw.trim();
  const svg = tpl.content.firstElementChild;
  svg.setAttribute('class', `svg-icon lucide-${name.replace(/^lucide-/, '')}`);
  svg.removeAttribute('width'); svg.removeAttribute('height');
  return svg;
}
export function setIcon(el, name) {
  el.empty();
  const svg = getIcon(name);
  if (svg) el.appendChild(svg); else console.warn('[obsidian-shim] missing icon', name);
}
export function addIcon(name, svg) { customIcons.set(name, svg); }
export function getIconIds() { return [...customIcons.keys()]; }

/* ------------------------------------------------------------------ misc */
export const Platform = { isDesktop: true, isDesktopApp: true, isMobile: false, isMobileApp: false, isMacOS: true, isWin: false, isLinux: false, isIosApp: false, isAndroidApp: false, isPhone: false, isTablet: false, isSafari: false };
export const apiVersion = '1.13.1';
export function requireApiVersion() { return true; }
export function getLanguage() { return 'zh'; }
export function normalizePath(p) { return String(p).replace(/\\/g, '/').replace(/\/{2,}/g, '/').replace(/^\.\//, '').replace(/^\/+|\/+$/g, '') || '/'; }
export function debounce(fn, ms = 0) { let t; const d = (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); return d; }; d.cancel = () => clearTimeout(t); return d; }
export function sanitizeHTMLToDom(html) { const t = document.createElement('template'); t.innerHTML = html; return t.content; }
export function htmlToMarkdown(html) { return String(html).replace(/<[^>]+>/g, ''); }
export function parseYaml() { return {}; }
export function stringifyYaml(o) { return JSON.stringify(o); }

// Film date: every "today" in the film resolves here (set by the host).
export const filmClock = { now: new Date('2026-09-26T09:30:00+08:00') };
export function moment(input) {
  const d = input ? new Date(input) : filmClock.now;
  const pad = (n) => String(n).padStart(2, '0');
  const api = {
    format(f = 'YYYY-MM-DDTHH:mm:ssZ') {
      return f.replace(/YYYY|MM|DD|HH|mm|ss/g, (k) => ({ YYYY: d.getFullYear(), MM: pad(d.getMonth() + 1), DD: pad(d.getDate()), HH: pad(d.getHours()), mm: pad(d.getMinutes()), ss: pad(d.getSeconds()) }[k]));
    },
    valueOf: () => d.getTime(), toDate: () => d, isValid: () => true, locale: () => api,
  };
  return api;
}
moment.locale = () => 'zh-cn';

/* ------------------------------------------------------------------ Events / Component */
export class Events {
  constructor() { this._ev = {}; }
  on(name, cb, ctx) { (this._ev[name] ||= []).push({ cb, ctx }); return { e: this, name, cb }; }
  off(name, cb) { this._ev[name] = (this._ev[name] || []).filter((x) => x.cb !== cb); }
  offref(ref) { ref?.e?.off(ref.name, ref.cb); }
  trigger(name, ...args) { for (const x of this._ev[name] || []) x.cb.apply(x.ctx, args); }
  tryTrigger(evt, args) { this.trigger(evt, ...args); }
}
export class Component {
  constructor() { this._loaded = false; this._children = []; this._cleanups = []; }
  load() { if (this._loaded) return; this._loaded = true; this.onload?.(); this._children.forEach((c) => c.load()); }
  onload() {}
  unload() { if (!this._loaded) return; this._loaded = false; this._children.forEach((c) => c.unload()); this._cleanups.splice(0).forEach((f) => f()); this.onunload?.(); }
  onunload() {}
  addChild(c) { this._children.push(c); if (this._loaded) c.load(); return c; }
  removeChild(c) { this._children = this._children.filter((x) => x !== c); c.unload(); return c; }
  register(cb) { this._cleanups.push(cb); }
  registerEvent(ref) { this._cleanups.push(() => ref?.e?.offref?.(ref)); }
  registerDomEvent(el, type, cb, opts) { el.addEventListener(type, cb, opts); this._cleanups.push(() => el.removeEventListener(type, cb, opts)); }
  registerInterval(id) { this._cleanups.push(() => clearInterval(id)); return id; }
  registerScopeEvent() {}
}
export class MarkdownRenderChild extends Component { constructor(containerEl) { super(); this.containerEl = containerEl; } }

/* ------------------------------------------------------------------ network (fixtures) */
// Fixtures: { [url]: { status, contentType, text?, b64? } }. Record mode proxies and captures.
export const net = { fixtures: {}, record: false, recorded: {}, pending: 0, missing: [] };
function b64ToBuf(b64) { const s = atob(b64); const u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); return u.buffer; }
function bufToB64(buf) { let s = ''; const u = new Uint8Array(buf); for (let i = 0; i < u.length; i += 0x8000) s += String.fromCharCode(...u.subarray(i, i + 0x8000)); return btoa(s); }
function responseOf(entry) {
  const buf = entry.b64 ? b64ToBuf(entry.b64) : new TextEncoder().encode(entry.text || '').buffer;
  const text = entry.text ?? new TextDecoder().decode(buf);
  return {
    status: entry.status, headers: { 'content-type': entry.contentType || '' }, text, arrayBuffer: buf,
    get json() { return JSON.parse(text); },
  };
}
export async function requestUrl(req) {
  const url = typeof req === 'string' ? req : req.url;
  net.pending++;
  try {
    if (net.record) {
      const r = await fetch(`/__proxy?url=${encodeURIComponent(url)}`);
      const type = r.headers.get('content-type') || '';
      const buf = await r.arrayBuffer();
      const textual = /json|text|xml|javascript/.test(type);
      const entry = { status: r.status, contentType: type, ...(textual ? { text: new TextDecoder().decode(buf) } : { b64: bufToB64(buf) }) };
      net.recorded[url] = entry;
      return responseOf(entry);
    }
    const hit = net.fixtures[url];
    await new Promise((r) => setTimeout(r, 0));
    if (!hit) { net.missing.push(url); if (req.throw !== false) throw new Error(`no fixture: ${url}`); return responseOf({ status: 404, text: '' }); }
    return responseOf(hit);
  } finally { net.pending--; }
}

/* ------------------------------------------------------------------ vault */
export class TAbstractFile { constructor(vault, path) { this.vault = vault; this.path = path; this.name = path.split('/').pop(); this.parent = null; } }
export class TFile extends TAbstractFile {
  constructor(vault, path) {
    super(vault, path);
    const i = this.name.lastIndexOf('.');
    this.basename = i > 0 ? this.name.slice(0, i) : this.name;
    this.extension = i > 0 ? this.name.slice(i + 1) : '';
    this.stat = { ctime: filmClock.now.getTime(), mtime: filmClock.now.getTime(), size: 0 };
  }
}
export class TFolder extends TAbstractFile { constructor(vault, path) { super(vault, path); this.children = []; } isRoot() { return this.path === '/'; } }

export class Vault extends Events {
  constructor(name = 'Qiaomu Vault') {
    super();
    this._name = name; this.configDir = '.obsidian'; this.files = new Map(); this.data = new Map();
    this.root = new TFolder(this, '/'); this.files.set('/', this.root);
    const v = this;
    this.adapter = {
      exists: async (p) => v.data.has(normalizePath(p)) || v.files.has(normalizePath(p)),
      read: async (p) => { const d = v.data.get(normalizePath(p)); if (d == null) throw new Error('ENOENT ' + p); return typeof d === 'string' ? d : new TextDecoder().decode(d); },
      write: async (p, s) => { v.data.set(normalizePath(p), s); },
      readBinary: async (p) => { const d = v.data.get(normalizePath(p)); if (d == null) throw new Error('ENOENT ' + p); return d instanceof ArrayBuffer ? d : new TextEncoder().encode(d).buffer; },
      writeBinary: async (p, b) => { v.data.set(normalizePath(p), b); },
      mkdir: async () => {}, remove: async (p) => { v.data.delete(normalizePath(p)); },
      list: async (p) => { const pre = normalizePath(p) + '/'; return { files: [...v.data.keys()].filter((k) => k.startsWith(pre)), folders: [] }; },
      stat: async (p) => (v.data.has(normalizePath(p)) ? { type: 'file', size: 1, mtime: 0, ctime: 0 } : null),
      getName: () => v._name, getBasePath: () => '/vault',
    };
  }
  getName() { return this._name; }
  getRoot() { return this.root; }
  getAbstractFileByPath(p) { return this.files.get(normalizePath(p)) || null; }
  getFileByPath(p) { const f = this.getAbstractFileByPath(p); return f instanceof TFile ? f : null; }
  getFolderByPath(p) { const f = this.getAbstractFileByPath(p); return f instanceof TFolder ? f : null; }
  getFiles() { return [...this.files.values()].filter((f) => f instanceof TFile); }
  getMarkdownFiles() { return this.getFiles().filter((f) => f.extension === 'md'); }
  getAllLoadedFiles() { return [...this.files.values()]; }
  _parentOf(path) { const dir = path.includes('/') ? path.slice(0, path.lastIndexOf('/')) : '/'; return this.files.get(dir) || this.root; }
  async createFolder(p) { p = normalizePath(p); if (this.files.has(p)) throw new Error('Folder already exists.'); const f = new TFolder(this, p); f.parent = this._parentOf(p); f.parent.children.push(f); this.files.set(p, f); return f; }
  async create(p, content = '') {
    p = normalizePath(p); if (this.files.has(p)) throw new Error('File already exists.');
    const f = new TFile(this, p); f.parent = this._parentOf(p); f.parent.children.push(f);
    this.files.set(p, f); this.data.set(p, content); this.trigger('create', f); this.trigger('modify', f); return f;
  }
  async createBinary(p, buf) { const f = await this.create(p, ''); this.data.set(f.path, buf); return f; }
  async read(f) { return String(this.data.get(f.path) ?? ''); }
  async cachedRead(f) { return this.read(f); }
  async readBinary(f) { return this.data.get(f.path); }
  async modify(f, s) { this.data.set(f.path, s); this.trigger('modify', f); }
  async append(f, s) { await this.modify(f, (await this.read(f)) + s); }
  async process(f, fn) { const next = fn(await this.read(f)); await this.modify(f, next); return next; }
  async delete(f) { this.files.delete(f.path); this.data.delete(f.path); this.trigger('delete', f); }
  async trash(f) { return this.delete(f); }
  async rename(f, p) { const old = f.path; this.files.delete(old); f.path = normalizePath(p); this.files.set(f.path, f); this.trigger('rename', f, old); }
  getResourcePath(f) { return `app://vault/${f.path}`; }
}

/* ------------------------------------------------------------------ views & workspace */
export class View extends Component {
  constructor(leaf) {
    super();
    this.leaf = leaf; this.app = leaf.app; this.navigation = true;
    this.containerEl = createDiv({ cls: 'workspace-leaf-content' });
    this.containerEl.createDiv({ cls: 'view-header' });
    this.contentEl = this.containerEl.createDiv({ cls: 'view-content' });
  }
  getViewType() { return 'view'; }
  getDisplayText() { return ''; }
  getIcon() { return 'file'; }
  getState() { return {}; }
  async setState() {}
  onResize() {}
  onPaneMenu() {}
}
export class ItemView extends View {
  addAction(icon, title, cb) { const b = this.containerEl.querySelector('.view-header').createDiv({ cls: 'clickable-icon view-action', attr: { 'aria-label': title } }); setIcon(b, icon); b.onclick = cb; return b; }
  async onOpen() {}
  async onClose() {}
}
export class FileView extends ItemView { constructor(leaf) { super(leaf); this.file = null; } }

/** Minimal CodeMirror-like editor over a string buffer. */
class Editor {
  constructor(view) { this.view = view; this.value = ''; this.cursor = { line: 0, ch: 0 }; }
  getValue() { return this.value; }
  setValue(v) { this.value = v; this.view._render(); }
  lineCount() { return this.value.split('\n').length; }
  getLine(n) { return this.value.split('\n')[n] ?? ''; }
  lastLine() { return this.lineCount() - 1; }
  offsetToPos(o) { const before = this.value.slice(0, o).split('\n'); return { line: before.length - 1, ch: before.at(-1).length }; }
  posToOffset(p) { const lines = this.value.split('\n'); let o = 0; for (let i = 0; i < p.line; i++) o += lines[i].length + 1; return o + p.ch; }
  replaceRange(text, from, to = from) { const a = this.posToOffset(from), b = this.posToOffset(to); this.value = this.value.slice(0, a) + text + this.value.slice(b); this.view._render(); }
  replaceSelection(text) { this.replaceRange(text, this.cursor); }
  setCursor(line, ch = 0) { this.cursor = typeof line === 'object' ? line : { line, ch }; }
  getCursor() { return this.cursor; }
  focus() {} blur() {} hasFocus() { return false; } getSelection() { return ''; } scrollIntoView() {}
}

export class MarkdownView extends FileView {
  constructor(leaf) { super(leaf); this.editor = new Editor(this); this.contentEl.addClass('markdown-source-view', 'mod-cm6', 'is-live-preview'); this.renderedEl = this.contentEl.createDiv({ cls: 'markdown-preview-view markdown-rendered qfilm-note' }); }
  getViewType() { return 'markdown'; }
  getDisplayText() { return this.file?.basename || ''; }
  getMode() { return 'source'; }
  async _load(file) { this.file = file; this.editor.value = await this.app.vault.read(file); this._render(); }
  async save() { if (this.file) await this.app.vault.modify(this.file, this.editor.value); }
  _render() {
    const el = this.renderedEl;
    el.empty();
    const h = el.createEl('div', { cls: 'inline-title', text: this.file?.basename || '' });
    h.setAttribute('data-inline-title', '');
    const body = el.createDiv({ cls: 'qfilm-note-body' });
    // obsidian://… links are internal return links; render them like Obsidian does (link + external icon)
    const md = this.editor.value.replace(/\]\(<([^>]+)>\)/g, (_, u) => `](${u.replace(/ /g, '%20')})`);
    body.innerHTML = marked.parse(md, { async: false, breaks: false });
    for (const a of body.querySelectorAll('a')) a.addClass(a.getAttribute('href')?.startsWith('http') || a.getAttribute('href')?.startsWith('obsidian') ? 'external-link' : 'internal-link');
    this.app.workspace.trigger('qfilm:note-rendered', this);
  }
}

export class WorkspaceLeaf extends Events {
  constructor(app, pane) { super(); this.app = app; this.pane = pane; this.view = null; this.parent = pane; this.containerEl = createDiv({ cls: 'workspace-leaf' }); }
  async setViewState({ type, active, state }) {
    const factory = this.app.workspace._views.get(type);
    if (!factory) throw new Error('no view ' + type);
    await this._mount(factory(this));
    await this.view.setState?.(state || {}, {});
  }
  async _mount(view) {
    if (this.view) { await this.view.onClose?.(); this.view.unload(); }
    this.view = view;
    this.containerEl.empty(); this.containerEl.appendChild(view.containerEl);
    this.app.workspace._place(this);
    view.load(); await view.onOpen?.();
    this.app.workspace._tabs();
  }
  async openFile(file) {
    const v = new MarkdownView(this); await this._mount(v); await v._load(file); this.app.workspace._tabs();
    this.app.workspace.activeLeaf = this; this.app.workspace.trigger('file-open', file); this.app.workspace.trigger('active-leaf-change', this);
  }
  async loadIfDeferred() {}
  getViewState() { return { type: this.view?.getViewType() }; }
  getDisplayText() { return this.view?.getDisplayText() || ''; }
  getRoot() { return this.app.workspace.rootSplit; }
  getContainer() { return this.app.workspace.rootSplit; }
  setPinned() {} setGroup() {} togglePinned() {}
  detach() { this.view?.onClose?.(); this.view?.unload(); this.containerEl.detach(); this.app.workspace.leaves = this.app.workspace.leaves.filter((l) => l !== this); this.app.workspace._tabs(); }
  isDeferred = false;
}

export class Workspace extends Events {
  constructor(app, host) { super(); this.app = app; this.host = host; this.leaves = []; this._views = new Map(); this.activeLeaf = null; this.rootSplit = { type: 'root' }; this.layoutReady = true; this.containerEl = host?.root || document.body; }
  _place(leaf) { this.host?.place(leaf); }
  _tabs() { this.host?.tabs(this.leaves); }
  _new(pane) { const l = new WorkspaceLeaf(this.app, pane); this.leaves.push(l); return l; }
  getLeaf(kind) { if (kind === 'split') return this._new('split'); return this._new('main'); }
  createLeafBySplit() { return this._new('split'); }
  getRightLeaf() { return this._new('right'); }
  getLeftLeaf() { return this._new('left'); }
  getLeavesOfType(type) { return this.leaves.filter((l) => l.view?.getViewType() === type); }
  getActiveViewOfType(T) { const v = this.activeLeaf?.view; return v instanceof T ? v : null; }
  getMostRecentLeaf() { return this.activeLeaf; }
  getActiveFile() { return this.activeLeaf?.view?.file || null; }
  async revealLeaf(leaf) { this.activeLeaf = leaf; this.host?.reveal(leaf); }
  setActiveLeaf(leaf) { this.activeLeaf = leaf; }
  onLayoutReady(cb) { setTimeout(cb, 0); }
  iterateAllLeaves(cb) { this.leaves.forEach(cb); }
  iterateRootLeaves(cb) { this.leaves.forEach(cb); }
  async openLinkText(path) { const f = this.app.vault.getAbstractFileByPath(path) || this.app.vault.getAbstractFileByPath(path + '.md'); if (f) await this.getLeaf('tab').openFile(f); }
  requestSaveLayout() {}
  detachLeavesOfType(type) { this.getLeavesOfType(type).forEach((l) => l.detach()); }
}

export class FileManager {
  constructor(app) { this.app = app; }
  generateMarkdownLink(file, source, sub = '', alias) { return `![[${file.path}${sub}${alias ? '|' + alias : ''}]]`; }
  async getAvailablePathForAttachment(name) { return normalizePath(`attachments/${name}`); }
  async trashFile(f) { await this.app.vault.delete(f); }
  async processFrontMatter(f, fn) { fn({}); }
}

export class App {
  constructor(host) {
    this.vault = new Vault();
    this.workspace = new Workspace(this, host);
    this.fileManager = new FileManager(this);
    this.metadataCache = new Events(); this.metadataCache.getFileCache = () => null; this.metadataCache.getFirstLinkpathDest = (p) => this.vault.getAbstractFileByPath(p);
    this.setting = { open() {}, openTabById() {}, close() {} };
    this.commands = { executeCommandById() {} };
    this.plugins = { plugins: {}, enabledPlugins: new Set(), getPlugin: (id) => this.plugins.plugins[id] || null };
    this.internalPlugins = { getPluginById: () => null, plugins: {} };
    this.keymap = {}; this.scope = {};
    this.loadLocalStorage = () => null; this.saveLocalStorage = () => {};
  }
}

export class Plugin extends Component {
  constructor(app, manifest) { super(); this.app = app; this.manifest = manifest; this._data = null; }
  async loadData() { return this._data; }
  async saveData(d) { this._data = JSON.parse(JSON.stringify(d)); }
  addCommand(c) { return c; }
  registerView(type, factory) { this.app.workspace._views.set(type, factory); }
  addRibbonIcon(icon, title, cb) { return this.app.workspace.host?.ribbon(icon, title, cb) || createDiv(); }
  addStatusBarItem() { return createDiv(); }
  addSettingTab() {}
  registerMarkdownPostProcessor() {}
  registerMarkdownCodeBlockProcessor() {}
  registerObsidianProtocolHandler() {}
  registerEditorExtension() {}
  registerExtensions() {}
  registerHoverLinkSource() {}
}
export class PluginSettingTab { constructor(app, plugin) { this.app = app; this.plugin = plugin; this.containerEl = createDiv(); } display() {} hide() {} }

/* ------------------------------------------------------------------ UI primitives */
function host() { return document.querySelector('.qfilm-host') || document.body; }

export class Notice {
  constructor(message, duration = 4500) {
    let box = host().querySelector('.notice-container');
    if (!box) box = host().createDiv({ cls: 'notice-container' });
    this.noticeEl = box.createDiv({ cls: 'notice' });
    this.messageEl = this.noticeEl;
    this.setMessage(message);
    Notice.log.push({ message: this.noticeEl.textContent, el: this.noticeEl });
    if (duration && Notice.autoHide) this._t = setTimeout(() => this.hide(), duration);
  }
  setMessage(m) { this.noticeEl.empty(); if (m instanceof Node) this.noticeEl.appendChild(m); else this.noticeEl.setText(m); return this; }
  hide() { clearTimeout(this._t); this.noticeEl.detach(); }
}
Notice.log = [];
Notice.autoHide = false; // film steps dismiss notices at chosen film times

class MenuItem {
  constructor(menu) { this.menu = menu; this.dom = createDiv({ cls: 'menu-item' }); this.iconEl = this.dom.createDiv({ cls: 'menu-item-icon' }); this.titleEl = this.dom.createDiv({ cls: 'menu-item-title' }); this.dom.onclick = (e) => { this.menu.hide(); this._cb?.(e); }; }
  setTitle(t) { this.titleEl.setText(t instanceof Node ? t : t); return this; }
  setIcon(i) { if (i) setIcon(this.iconEl, i); return this; }
  onClick(cb) { this._cb = cb; return this; }
  setChecked(c) { this.dom.toggleClass('mod-checked', !!c); return this; }
  setDisabled(d) { this.dom.toggleClass('is-disabled', !!d); return this; }
  setSection() { return this; } setWarning(w) { this.dom.toggleClass('mod-warning', !!w); return this; } setIsLabel() { return this; } setSubmenu() { return new Menu(); }
}
export class Menu extends Component {
  constructor() { super(); this.dom = createDiv({ cls: 'menu' }); this.items = []; Menu.last = this; }
  setUseNativeMenu() { return this; } setNoIcon() { return this; }
  addItem(cb) { const i = new MenuItem(this); cb(i); this.items.push(i); this.dom.appendChild(i.dom); return this; }
  addSeparator() { this.dom.createDiv({ cls: 'menu-separator' }); return this; }
  showAtPosition({ x, y }) {
    const h = host(); h.appendChild(this.dom);
    const r = h.getBoundingClientRect(); const s = h.__scale || 1;
    this.dom.style.left = `${(x - r.left) / s}px`; this.dom.style.top = `${(y - r.top) / s + 4}px`;
    this._outside = (e) => { if (!this.dom.contains(e.target)) this.hide(); };
    setTimeout(() => document.addEventListener('pointerdown', this._outside, true), 0);
    return this;
  }
  showAtMouseEvent(e) { return this.showAtPosition({ x: e.clientX, y: e.clientY }); }
  hide() { document.removeEventListener('pointerdown', this._outside, true); this.dom.detach(); this._onHide?.(); return this; }
  onHide(cb) { this._onHide = cb; }
  close() { this.hide(); }
}

export class Modal extends Component {
  constructor(app) {
    super(); this.app = app;
    this.containerEl = createDiv({ cls: 'modal-container mod-dim' });
    this.containerEl.createDiv({ cls: 'modal-bg' }).onclick = () => this.close();
    this.modalEl = this.containerEl.createDiv({ cls: 'modal' });
    this.modalEl.createDiv({ cls: 'modal-close-button' }).onclick = () => this.close();
    this.titleEl = this.modalEl.createDiv({ cls: 'modal-title' });
    this.contentEl = this.modalEl.createDiv({ cls: 'modal-content' });
    this.scope = {};
  }
  setTitle(t) { this.titleEl.setText(t); return this; }
  setContent(c) { this.contentEl.empty(); if (c instanceof Node) this.contentEl.appendChild(c); else this.contentEl.setText(c); return this; }
  open() { host().appendChild(this.containerEl); this.onOpen?.(); }
  close() { this.containerEl.detach(); this.onClose?.(); }
  onOpen() {} onClose() {}
}
export class SuggestModal extends Modal {
  constructor(app) {
    super(app); this.modalEl.addClass('prompt'); this.inputEl = this.modalEl.createEl('input', { cls: 'prompt-input', type: 'text' });
    this.resultContainerEl = this.modalEl.createDiv({ cls: 'prompt-results' }); this.limit = 50;
    this.inputEl.addEventListener('input', () => this._refresh());
  }
  setPlaceholder(p) { this.inputEl.placeholder = p; }
  setInstructions() {}
  async _refresh() {
    this.resultContainerEl.empty();
    const items = await this.getSuggestions(this.inputEl.value);
    for (const it of items.slice(0, this.limit)) { const el = this.resultContainerEl.createDiv({ cls: 'suggestion-item' }); this.renderSuggestion(it, el); el.onclick = (e) => { this.close(); this.onChooseSuggestion(it, e); }; }
  }
  onOpen() { this._refresh(); }
}
export class FuzzySuggestModal extends SuggestModal {
  getSuggestions(q) { return this.getItems().filter((i) => this.getItemText(i).toLowerCase().includes(q.toLowerCase())).map((item) => ({ item, match: { score: 0, matches: [] } })); }
  renderSuggestion(m, el) { el.setText(this.getItemText(m.item)); }
  onChooseSuggestion(m, e) { this.onChooseItem(m.item, e); }
}
export class AbstractInputSuggest { constructor(app, el) { this.app = app; this.el = el; } close() {} setValue(v) { this.el.value = v; } onSelect() { return this; } }

// Settings UI is never filmed here; a chainable stub keeps settings tabs from crashing.
const chain = () => new Proxy(function () {}, { get: (t, k) => (k === 'then' ? undefined : k.endsWith?.('El') ? createDiv() : chain()), apply: () => chain() });
export class Setting {
  constructor(el) { this.settingEl = el.createDiv({ cls: 'setting-item' }); this.nameEl = this.settingEl.createDiv(); this.descEl = this.settingEl.createDiv(); this.controlEl = this.settingEl.createDiv(); this.infoEl = this.settingEl.createDiv(); }
  setName() { return this; } setDesc() { return this; } setClass() { return this; } setHeading() { return this; } setTooltip() { return this; } setDisabled() { return this; }
  addText(cb) { cb?.(chain()); return this; } addTextArea(cb) { cb?.(chain()); return this; } addToggle(cb) { cb?.(chain()); return this; } addDropdown(cb) { cb?.(chain()); return this; }
  addButton(cb) { cb?.(chain()); return this; } addExtraButton(cb) { cb?.(chain()); return this; } addSlider(cb) { cb?.(chain()); return this; } addSearch(cb) { cb?.(chain()); return this; } addColorPicker(cb) { cb?.(chain()); return this; }
  then(cb) { cb?.(this); return this; }
}
export class ButtonComponent { constructor(el) { this.buttonEl = el.createEl('button'); } setButtonText(t) { this.buttonEl.setText(t); return this; } setCta() { this.buttonEl.addClass('mod-cta'); return this; } onClick(cb) { this.buttonEl.onclick = cb; return this; } setIcon(i) { setIcon(this.buttonEl, i); return this; } setTooltip() { return this; } setDisabled(d) { this.buttonEl.disabled = d; return this; } setClass(c) { this.buttonEl.addClass(c); return this; } setWarning() { return this; } }
export class ToggleComponent { constructor(el) { this.toggleEl = el.createDiv({ cls: 'checkbox-container' }); } setValue() { return this; } onChange() { return this; } }
export class TextComponent { constructor(el) { this.inputEl = el.createEl('input', { type: 'text' }); } setValue(v) { this.inputEl.value = v; return this; } getValue() { return this.inputEl.value; } setPlaceholder(p) { this.inputEl.placeholder = p; return this; } onChange(cb) { this.inputEl.oninput = () => cb(this.inputEl.value); return this; } }
export class SearchComponent extends TextComponent { constructor(el) { super(el); this.inputEl.type = 'search'; this.clearButtonEl = el.createDiv(); } }
export class DropdownComponent { constructor(el) { this.selectEl = el.createEl('select'); } addOption(v, t) { this.selectEl.createEl('option', { value: v, text: t }); return this; } addOptions(o) { for (const [v, t] of Object.entries(o)) this.addOption(v, t); return this; } setValue(v) { this.selectEl.value = v; return this; } getValue() { return this.selectEl.value; } onChange(cb) { this.selectEl.onchange = () => cb(this.selectEl.value); return this; } }
export class ExtraButtonComponent { constructor(el) { this.extraSettingsEl = el.createDiv({ cls: 'clickable-icon' }); } setIcon(i) { setIcon(this.extraSettingsEl, i); return this; } setTooltip() { return this; } onClick(cb) { this.extraSettingsEl.onclick = cb; return this; } }

export const MarkdownRenderer = {
  async render(app, md, el) { el.insertAdjacentHTML('beforeend', marked.parse(md, { async: false })); },
  async renderMarkdown(md, el) { el.insertAdjacentHTML('beforeend', marked.parse(md, { async: false })); },
};
export const Keymap = { isModEvent: () => false, isModifier: () => false };
export class Scope { register() {} unregister() {} }
export default {};
