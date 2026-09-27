// Bundle src/main.js → dist/film.js + dist/film.css. Optional film.config.json:
//   { "alias": { "@": "../product/src", "obsidian": "./src/host/obsidian.js" },
//     "nodePaths": ["../product/node_modules"], "define": {}, "loader": { ".woff2": "dataurl" },
//     "entries": { "lab": "src/lab.js" } }      // extra pages → dist/<name>.js
import * as esbuild from 'esbuild';
import fs from 'node:fs';
import path from 'node:path';
import { ROOT } from './common.mjs';

const cfgPath = path.join(ROOT, 'film.config.json');
const cfg = fs.existsSync(cfgPath) ? JSON.parse(fs.readFileSync(cfgPath, 'utf8')) : {};
const alias = Object.fromEntries(Object.entries(cfg.alias || {}).map(([k, v]) => [k, path.resolve(ROOT, v)]));

export async function build() {
  const entries = { film: 'src/main.js', ...(cfg.entries || {}) };
  await esbuild.build({
    entryPoints: Object.fromEntries(Object.entries(entries).map(([k, v]) => [k, path.join(ROOT, v)])),
    outdir: path.join(ROOT, 'dist'),
    bundle: true, format: 'iife', target: 'chrome120', sourcemap: 'inline', jsx: 'automatic',
    loader: { '.svg': 'dataurl', '.png': 'dataurl', '.jpg': 'dataurl', '.woff2': 'dataurl', '.woff': 'dataurl', '.ttf': 'dataurl', '.otf': 'dataurl', '.cast': 'text', '.txt': 'text', '.md': 'text', ...(cfg.loader || {}) },
    alias, nodePaths: (cfg.nodePaths || []).map((p) => path.resolve(ROOT, p)),
    define: { 'process.env.NODE_ENV': '"production"', ...(cfg.define || {}) },
    logLevel: 'warning',
  });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await build();
  console.log('built dist/film.js');
}
