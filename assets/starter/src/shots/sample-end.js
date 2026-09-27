// TECHNICAL SAMPLE — pull-out ending: content shrinks to a mark, then the product name lands.
export default {
  view(el, ctx) {
    el.style.display = 'grid';
    el.style.placeItems = 'center';
    el.innerHTML = `<div class="end-mark" data-film-placeholder style="width:calc(120*var(--u));height:calc(120*var(--u));border-radius:calc(28*var(--u));background:var(--accent)"></div>
      <div class="end-name" style="position:absolute;top:58%;font:700 calc(56*var(--u)) var(--font-en)"></div>`;
    el.querySelector('.end-name').textContent = ctx.plan.title || 'Product';
    ctx.mark = el.querySelector('.end-mark');
    ctx.name = el.querySelector('.end-name');
  },
  build(tl, ctx) {
    tl.fromTo(ctx.mark, { scale: 6, opacity: 0.2, borderRadius: '2%' }, { scale: 1, opacity: 1, borderRadius: '24%', duration: 0.8, ease: 'expo.out' }, 0);
    tl.fromTo(ctx.name, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' }, 0.45);
  },
};
