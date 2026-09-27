// TECHNICAL SAMPLE — proves the pipeline only. Replace with shots derived in DIRECTION.md.
import { headline, splitChars } from '../kit/text.js';

export default {
  view(el, ctx) {
    el.style.display = 'grid';
    el.style.placeItems = 'center';
    const h = headline({ en: ctx.shot.headlineEn || 'Sample', zh: ctx.shot.headline || '技术样片' });
    h.dataset.filmPlaceholder = '';
    h.style.alignItems = 'center';
    h.style.textAlign = 'center';
    el.appendChild(h);
    ctx.chars = splitChars(h.querySelector('.hl-zh'));
    ctx.en = h.querySelector('.hl-en');
  },
  build(tl, ctx) {
    // first frame already carries content: characters start visible but soft, then sharpen
    tl.fromTo(ctx.chars, { opacity: 0.25, y: 18, filter: 'blur(8px)' },
      { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.5, stagger: 0.035, ease: 'power3.out' }, 0);
    tl.fromTo(ctx.en, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' }, 0.15);
  },
};
