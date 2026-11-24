// automated layout QA: captions never touch content/logo, nothing clipped or off-canvas
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + path.resolve(__dirname, 'index.html')); await p.waitForFunction('window.ready===true');
  const caps = await p.evaluate(() => TL.scenes.flatMap(s => s.caps.filter(c => c.html).map(c => ({ id: s.id, t: (c.start + Math.min(c.end, c.start + 1.2)) / 2 + .2, html: c.html }))));
  let problems = 0, maxW = 0, twoLine = 0, minGap = 1e9;
  for (const c of caps) {
    await p.evaluate(t => window.seek(t), c.t);
    const r = await p.evaluate((id) => {
      const vis = e => { const s = getComputedStyle(e); return s.visibility !== 'hidden' && +s.opacity > .05; };
      const cap = [...document.querySelectorAll('.cap')].filter(vis);
      const cr = cap.map(e => e.getBoundingClientRect());
      const sc = document.getElementById('sc-' + id);
      const els = [...sc.querySelectorAll('.phone,.kiosk,.card,.feat,.outcome,.mhead,.plat,.tagp,.node,.mcard,.booth,.qrc,.cbtn,.h-cta,.h-hero,.big,.word,.hubc,.kicker,.logo-xl,.endw')].filter(vis);
      let bottom = 0, off = [];
      for (const e of els) { const q = e.getBoundingClientRect(); bottom = Math.max(bottom, q.bottom); if (q.left < 0 || q.right > 1920 || q.top < 0 || q.bottom > 1080) off.push(e.className); }
      const clipped = [...sc.querySelectorAll('.feat,.outcome span,.msub,.nm,.sb,.tr strong,.mcard h3,.node h5,.note h4')].filter(e => vis(e) && e.scrollWidth > e.clientWidth + 1).map(e => e.textContent.slice(0, 40));
      const wm = [...document.querySelectorAll('#wm,#wmw')].filter(vis).map(e => e.getBoundingClientRect());
      return { n: cap.length, cap: cr[0] && { l: cr[0].left, r: cr[0].right, t: cr[0].top, b: cr[0].bottom, h: cr[0].height, w: cr[0].width }, bottom, off, clipped, wmL: wm[0] ? wm[0].left : null };
    }, c.id);
    const k = r.cap; if (!k) { console.log('NO CAPTION', c.id, c.t.toFixed(2), c.html); problems++; continue; }
    maxW = Math.max(maxW, k.w); if (k.h > 100) twoLine++;
    const gap = k.t - r.bottom; if (c.id !== 'words' && c.id !== 'intro') minGap = Math.min(minGap, gap);
    const bad = [];
    if (r.n !== 1) bad.push('captions visible: ' + r.n);
    if (gap < 12) bad.push('caption-content gap ' + gap.toFixed(0));
    if (Math.abs((k.l + k.r) / 2 - 960) > 1) bad.push('not centred');
    if (r.wmL !== null && k.r > r.wmL - 20) bad.push('caption near logo');
    if (k.b > 1060 || k.t < 900) bad.push('caption outside band');
    if (r.off.length) bad.push('off-canvas: ' + r.off);
    if (r.clipped.length) bad.push('clipped: ' + r.clipped);
    if (bad.length) { problems++; console.log(c.id, c.t.toFixed(1), bad.join(' | '), '::', c.html.replace(/<[^>]+>/g, '')); }
  }
  console.log(`${caps.length} captions checked, ${problems} problems, widest ${maxW.toFixed(0)}px, two-line ${twoLine}, min gap to content ${minGap.toFixed(0)}px`);
  await b.close();
})();
