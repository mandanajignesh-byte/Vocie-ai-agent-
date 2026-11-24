/* Builds one master GSAP timeline from the VO timeline; window.seek(t) renders any instant deterministically. */
(async function () {
  const TL = window.TL, byId = {};
  TL.scenes.forEach(s => byId[s.id] = s);
  const host = document.getElementById('scenes');
  host.innerHTML = TL.scenes.map(s => SCENES_HTML[s.id] || '').join('');

  // decorative bits that need generated children
  document.querySelectorAll('.wave').forEach(w => { w.innerHTML = '<span></span>'.repeat(+w.dataset.n); });
  document.querySelectorAll('.dots').forEach(d => { d.innerHTML = '<i></i>'.repeat(+d.dataset.dots); });

  // captions
  const capHost = document.getElementById('caps'), caps = [];
  TL.scenes.forEach(s => s.caps.forEach(c => { if (!c.html) return;
    const el = document.createElement('div'); el.className = 'cap'; el.innerHTML = c.html; capHost.appendChild(el);
    caps.push({ el, start: c.start, end: c.end, sceneEnd: s.end }); }));

  // everything must be laid out with final fonts/images before GSAP measures it
  await document.fonts.ready;
  await Promise.all([...document.fonts].map(f => f.load().catch(() => 0)));
  await Promise.all([...document.images].filter(i => i.getAttribute('src')).map(i => i.decode().catch(() => 0)));
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));

  gsap.ticker.lagSmoothing(0);
  const tl = gsap.timeline({ paused: true, defaults: { ease: 'power3.out' } });
  const cue = (s, expr) => {
    const m = /^([sce])(\d+)?([+-][\d.]+)?$/.exec(expr);
    if (!m) throw new Error('bad cue ' + expr);
    const off = m[3] ? parseFloat(m[3]) : 0;
    if (m[1] === 's') return s.start + off;
    if (m[1] === 'e') return s.end + off;
    const c = s.caps[+m[2]]; if (!c) throw new Error(`no caption ${expr} in ${s.id}`);
    return c.start + off;
  };
  const FX = {
    up:   (el, t) => tl.from(el, { autoAlpha: 0, y: 18, duration: .55 }, t),
    left: (el, t) => tl.from(el, { autoAlpha: 0, x: -28, duration: .6 }, t),
    right:(el, t) => tl.from(el, { autoAlpha: 0, x: 28, duration: .6 }, t),
    rise: (el, t) => tl.from(el, { autoAlpha: 0, y: 46, duration: .85 }, t),
    pop:  (el, t) => tl.from(el, { autoAlpha: 0, scale: .93, duration: .55, ease: 'back.out(1.5)' }, t),
    fade: (el, t) => tl.from(el, { autoAlpha: 0, duration: .45, ease: 'power1.out' }, t),
    row:  (el, t) => tl.from(el, { autoAlpha: 0, x: -10, duration: .42 }, t),
    bar:  (el, t) => tl.from(el, { scaleX: 0, transformOrigin: 'left center', duration: 1.0, ease: 'power2.out' }, t),
    msg:  (el, t) => { tl.from(el, { height: 0, paddingTop: 0, duration: .42, ease: 'power2.out' }, t);
                       tl.from(el.firstElementChild, { autoAlpha: 0, y: 12, duration: .42 }, t + .05); },
  };

  TL.scenes.forEach((s, i) => {
    const el = document.getElementById('sc-' + s.id);
    // reveal children first (they measure natural sizes), scene visibility after
    el.querySelectorAll('[data-at]').forEach(n => {
      if (n.classList.contains('wave')) return;
      const t = Math.max(s.start, cue(s, n.dataset.at));
      (FX[n.dataset.fx || 'up'])(n, t);
    });
    el.querySelectorAll('[data-out]').forEach(n => tl.to(n, { autoAlpha: 0, duration: .3, ease: 'power1.in' }, cue(s, n.dataset.out)));
    el.querySelectorAll('.wave').forEach(w => {
      const t0 = cue(s, w.dataset.at), bars = [...w.children];
      tl.from(w, { autoAlpha: 0, duration: .3 }, t0);
      bars.forEach((b, k) => {
        const a = .22 + .5 * Math.abs(Math.sin(k * 1.7 + 1)), d = .26 + .18 * Math.abs(Math.sin(k * 2.9));
        const reps = Math.max(1, Math.ceil((s.end - t0) / d));
        tl.fromTo(b, { scaleY: a * .45 }, { scaleY: Math.min(1, a + .42), duration: d, repeat: reps, yoyo: true, ease: 'sine.inOut' }, t0 + (k % 5) * .04);
      });
    });
    // scenes cross-dissolve into each other; only the very last one fades to the background (clean loop)
    const last = i === TL.scenes.length - 1;
    tl.to(el, { autoAlpha: 1, duration: i ? .5 : .6, ease: 'power1.inOut' }, s.start);
    tl.to(el, { autoAlpha: 0, duration: last ? .45 : .4, ease: 'power1.inOut' }, last ? s.end - .45 : s.end);
    // watermark logo: colour on light scenes, white on blue, hidden where a big logo is on screen
    const m = el.dataset.wm;
    tl.to('#wm', { autoAlpha: m === 'c' ? 1 : 0, duration: .3, ease: 'none' }, s.start + (m === 'c' ? .15 : -.3 < 0 ? Math.max(0, s.start - .3) - s.start : 0));
    tl.to('#wmw', { autoAlpha: m === 'w' ? 1 : 0, duration: .3, ease: 'none' }, m === 'w' ? s.start + .15 : Math.max(0, s.start - .3));
  });

  // scene-specific motion
  { const s = byId.words, w = s.sentences.map(se => se.words[0].t), els = [...document.querySelectorAll('#sc-words .word')];
    els.forEach((el, k) => { const t = k ? w[k] - .08 : s.start + .12;      // first word arrives with the blue card
      tl.fromTo(el, { autoAlpha: 0, scale: .84 }, { autoAlpha: 1, scale: 1, duration: .36, ease: 'back.out(1.7)' }, t);
      if (k < 3) tl.to(el, { autoAlpha: 0, scale: 1.05, duration: .14, ease: 'power1.in' }, w[k + 1] - .08 - .14); }); }
  { const s = byId.pivc; tl.fromTo('#knob', { left: '8%' }, { left: '49%', duration: 1.2, ease: 'power2.inOut' }, cue(s, 'c3+0.25'));
    document.querySelectorAll('#sc-pivc .dots i').forEach((d, k) => {
      const dur = .5, reps = Math.ceil((s.end - s.start) / dur);
      tl.fromTo(d, { scale: .7, opacity: .45 }, { scale: 1.9, opacity: 1, duration: dur, repeat: reps, yoyo: true, ease: 'sine.inOut' }, s.start + (k * .07) % 1); }); }
  { const s = byId.hub;
    document.querySelectorAll('#sc-hub .hl').forEach(l => { const k = +l.dataset.i, len = Math.hypot(l.x2.baseVal.value - 960, l.y2.baseVal.value - 505);
      tl.fromTo(l, { strokeDasharray: len, strokeDashoffset: len }, { strokeDashoffset: 0, duration: .6, ease: 'power2.out' }, s.start + .7 + k * .2); });
    document.querySelectorAll('#sc-hub .hd').forEach(d => { const k = +d.dataset.i;
      tl.from(d, { autoAlpha: 0, scale: 0, transformOrigin: 'center', duration: .35, ease: 'back.out(2)' }, s.start + 1.05 + k * .2); }); }
  { const s = byId.proof, el = document.getElementById('crore'), o = { v: 0 };
    tl.fromTo(o, { v: 0 }, { v: 1.7, duration: 1.0, ease: 'power2.out', onUpdate: () => { el.textContent = '₹' + o.v.toFixed(1) + ' Crore'; } }, cue(s, 'c0+0.5')); }

  // captions: fade/rise in on the spoken word, hold through the phrase, clear before the next
  caps.forEach((c, k) => {
    const next = caps[k + 1];
    const out = next && next.start - c.end < .9 ? next.start - .2 : Math.min(c.end + .45, c.sceneEnd - .05);
    gsap.set(c.el, { xPercent: -50, yPercent: -50 });
    tl.fromTo(c.el, { autoAlpha: 0, y: 10 }, { autoAlpha: 1, y: 0, duration: .26, ease: 'power2.out' }, Math.max(0, c.start - .05));
    tl.to(c.el, { autoAlpha: 0, duration: .16, ease: 'power1.in' }, Math.max(c.start + .5, out));
  });
  tl.set({}, {}, TL.duration);

  // kiosk avatar: frames of the upscaled source clip, time-warped so lips follow the new voice
  const AV = window.AVMAP, avImg = document.getElementById('avatar'), ks = byId.kiosk;
  const nFrames = Math.round((AV.src1 - AV.src0) * AV.fps);
  const A = AV.anchors, a0 = A[0], aN = A[A.length - 1];
  const kPre = Math.min(1, (a0[1] - AV.src0 - .1) / (a0[0] - ks.start)), kPost = Math.min(1, (AV.src1 - aN[1] - .1) / (ks.end - aN[0]));
  const srcTime = t => {
    if (t <= a0[0]) return a0[1] - (a0[0] - t) * kPre;
    if (t >= aN[0]) return aN[1] + (t - aN[0]) * kPost;
    for (let i = 1; i < A.length; i++) if (t <= A[i][0]) { const p = A[i - 1], q = A[i]; return p[1] + (q[1] - p[1]) * (t - p[0]) / (q[0] - p[0]); }
  };
  let curFrame = -1;
  const avatarAt = async t => {
    const tt = Math.min(Math.max(t, ks.start), ks.end);
    const f = Math.min(nFrames - 1, Math.max(0, Math.round((srcTime(tt) - AV.src0) * AV.fps)));
    if (f === curFrame) return;
    curFrame = f;
    avImg.src = `${window.AVATAR_DIR || '../sr/frames_nat'}/a_${String(f).padStart(4, '0')}.jpg`;
    await avImg.decode().catch(() => 0);
  };

  // intervals during which anything is moving, so the renderer can reuse frames across static holds
  const busy = tl.getChildren(true, true, false).map(c => [c.startTime(), c.startTime() + c.totalDuration()]).filter(i => i[1] > i[0]);
  window.isStatic = (tPrev, t) => !(t >= ks.start - .5 && t <= ks.end + .1) && !busy.some(i => i[0] <= t + 1e-4 && i[1] >= tPrev - 1e-4);
  window.duration = TL.duration;
  window.seek = async t => {
    tl.time(Math.min(t, TL.duration), false);
    if (t >= ks.start - .5 && t <= ks.end + .1) await avatarAt(t);
  };
  await window.seek(0);
  window.ready = true;
})();
