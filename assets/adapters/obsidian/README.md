# Obsidian plugin adapter

Films a real Obsidian plugin outside Obsidian: the plugin's own `main.ts`, views and `styles.css` run
unmodified against a shim of the Obsidian API and a reconstructed default-theme host (tab bar, ribbon,
split panes, Live-Preview-looking notes). First used for Qiaomu AI RSS (2026-09).

## Files

| file | role |
|---|---|
| `obsidian.js` | API shim: DOM helpers (`createEl`, `empty`, `toggleClass`…), Component/Plugin/ItemView, in-memory Vault + adapter, Workspace that places leaves in film panes, MarkdownView with an editor buffer, Menu/Modal/Notice/SuggestModal, `requestUrl` backed by recorded fixtures, Lucide icons for `setIcon` |
| `host.css` / `host.js` | Obsidian-like chrome (default light theme variables on `:root`), `createHost`, `bootPlugin`, `idle` |
| `stubs.js` | `@codemirror/*`, `electron`, `node:fs/path` stand-ins for code paths the film never runs |
| `product.example.js` + `product.html` | the page loaded **in an iframe per shot**; exposes `window.__product` (click, select, rect, scrollTo, openEntry…) |

## Wire-up

1. `npm i lucide-static marked` plus the plugin's runtime deps (same versions as its package.json) in the video project.
2. Copy `obsidian.js host.css host.js stubs.js` to `src/host/`, `product.example.js` to `src/product.js` (replace `<PRODUCT_REPO>`), `product.html` to the project root.
3. `film.config.json`:
   ```json
   { "alias": { "obsidian": "./src/host/obsidian.js", "@codemirror/view": "./src/host/stubs.js", "@codemirror/state": "./src/host/stubs.js",
                "electron": "./src/host/stubs.js", "node:fs": "./src/host/stubs.js", "node:path": "./src/host/stubs.js", "product": "../<repo>/src" },
     "nodePaths": ["node_modules"], "entries": { "product": "src/product.js" } }
   ```
4. Record real data once: `FILM_RECORD=1 node tools/lab.mjs --record --steps lab/flows.mjs` (drive every flow the film shows; responses land in `src/fixtures/requests.json`). Renders then replay offline and deterministically.
5. Shots mount `productFrame()` + `director()` from `src/film/product-frame.js`.

## Why an iframe per shot

Plugins attach popups to `document.body` with `position: fixed` in viewport coordinates. Under a CSS
camera transform those land in the wrong place. Inside an iframe sized to the Obsidian window, the
viewport, fixed positioning, `getBoundingClientRect` and the text selection are all self-consistent,
and the camera simply transforms the iframe. Each shot also gets its own selection and notices.

## Honest-film rules for this adapter

- The host chrome is a reconstruction; say so in `evidence/component-usage.json` (`reuseMode: original` for the plugin, `rebuild` for the host).
- Wall-clock timers (debounced popups, notices) are not film time: hold or dismiss them with explicit steps.
- Plugin appearance settings the user could really set (e.g. Obsidian accent colour) are fair game; invented states are not.
