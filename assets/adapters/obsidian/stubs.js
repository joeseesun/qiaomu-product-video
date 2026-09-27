// Modules the plugin imports but the film never exercises (desktop export, CM6 link handling).
export const EditorView = { findFromDOM: () => null };
export const StateField = { define: () => ({}) };
export class Compartment { of(x) { return x; } reconfigure(x) { return x; } }
export const StateEffect = { define: () => ({ of: (x) => x }), appendConfig: { of: (x) => x } };
EditorView.domEventHandlers = () => ({});
EditorView.updateListener = { of: () => ({}) };
export const shell = { showItemInFolder() {}, openPath() {} };
export const remote = { dialog: { showSaveDialog: async () => ({ canceled: true }) } };
export const ipcRenderer = { invoke: async () => null, send() {} };
export const promises = { writeFile: async () => {}, mkdir: async () => {}, readFile: async () => '' };
export const writeFileSync = () => {}; export const existsSync = () => false; export const mkdirSync = () => {};
export const join = (...p) => p.join('/'); export const dirname = (p) => p.split('/').slice(0, -1).join('/'); export const basename = (p) => p.split('/').pop();
export const extname = (p) => (p.match(/\.[^.]+$/) || [''])[0]; export const resolve = join; export const sep = '/';
export default { EditorView, shell, remote, ipcRenderer, promises, writeFileSync, existsSync, mkdirSync, join, dirname, basename, extname, resolve, sep };
