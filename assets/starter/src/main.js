// Entry: plan.json is the only source of time. Shot implementations live in shots/.
import './film.css';
import plan from '../plan.json';
import { startFilm } from './runtime.js';
import shots from './shots/index.js';
import fixtures from './fixtures/api.js';

startFilm({ plan, shots, fixtures }).catch((err) => {
  console.error('[film] failed to start:', err);
  window.__filmError = String(err?.stack || err);
});
