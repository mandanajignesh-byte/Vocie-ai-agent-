/* Scene markup. Timing lives in data-at attributes:
   s+N = scene start + N seconds, cK+N = when caption K of the scene is spoken (+N s), e-N = before scene end. */
(function () {
const I = (n, s = 24, w = 2) => {
  if (!ICONS[n]) throw new Error('missing icon ' + n);
  return ICONS[n].replace('<svg', `<svg width="${s}" height="${s}"`).replace('stroke-width="2"', `stroke-width="${w}"`);
};
const WA = (s = 22, c = '#25d366') => `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="${c}"><path d="${WA_PATH}"/></svg>`;
const SIG = '<svg width="18" height="12" viewBox="0 0 18 12" fill="#0b0b0f"><rect x="0" y="8" width="3" height="4" rx="1"/><rect x="5" y="5.5" width="3" height="6.5" rx="1"/><rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" y="0" width="3" height="12" rx="1"/></svg>';
const WIFI = '<svg width="17" height="12" viewBox="0 0 17 12" fill="#0b0b0f"><path d="M8.5 2.7c2.3 0 4.4.9 6 2.4l1.1-1.2C13.7 2.1 11.2 1 8.5 1S3.3 2.1 1.4 3.9l1.1 1.2c1.600-1.500 3.700-2.400 6-2.400z"/><path d="M8.5 6.300c1.300 0 2.500.500 3.400 1.300L13 6.400c-1.200-1.100-2.800-1.800-4.500-1.800S5.200 5.300 4 6.400l1.100 1.200c.900-.800 2.100-1.300 3.400-1.300z"/><circle cx="8.5" cy="10" r="1.7"/></svg>';
const BAT = '<svg width="27" height="13" viewBox="0 0 27 13" fill="#0b0b0f"><rect x=".5" y=".5" width="22" height="12" rx="3.6" fill="none" stroke="#0b0b0f" opacity=".4"/><rect x="2" y="2" width="19" height="9" rx="2.3"/><path d="M24 4.500v4c.8-.300 1.500-1.100 1.500-2s-.7-1.700-1.500-2z" opacity=".45"/></svg>';
const TICK = '<svg width="15" height="10" viewBox="0 0 16 11" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M1 6l3 3 6-7.500"/><path d="M6.500 8.200l.8.800 6-7.500"/></svg>';
const OK = '<span class="ok">✓</span>';

const whead = (icon, name, sub, o = {}) => `<div class="whead" ${o.attr || ''} style="${o.style || ''}">
  <span style="color:#2563eb">${I('chevron-left', 26, 2.2)}</span><div class="av" style="${o.av || ''}">${icon ? I(icon, 20) : ''}</div>
  <div><div class="nm">${name}${o.verified === false ? '' : `<span class="vf">${I('check', 10, 3.6)}</span>`}</div><div class="sb">${sub}</div></div>
  ${o.phone === false ? '' : `<span class="ph">${I('phone', 21)}</span>`}</div>`;
const phone = (o) => `<div class="phone" data-fx="rise" data-at="s+0.12" style="${o.left ? `left:${o.left}px` : ''}"><div class="screen">
  <div class="sbar" style="${o.white ? 'background:#fff' : ''}"><span class="tm">10:42</span><span class="isl"></span><span class="st">${SIG}${WIFI}${BAT}</span></div>
  ${o.head || ''}${o.body}
  ${o.input === false ? '' : `<div class="ibar">${I('plus', 23)}<div class="in">${o.input || 'Message'}</div>${I('camera', 21)}${I('mic', 21)}</div>`}
  <div class="home" style="${o.white ? 'background:#fff' : ''}"></div></div></div>`;
const tagH = (tag) => !tag ? '' : Array.isArray(tag) ? `<span class="tag ${tag[1]}">${tag[0]}</span>` : `<span class="tag">${tag}</span>`;
const mi = (at, html, time, tag, cls = '') => `<div class="mw" data-fx="msg" data-at="${at}"><div class="b in ${cls}">${tagH(tag)}${html}<span class="t">${time}</span></div></div>`;
const mo = (at, html, time, cls = '') => `<div class="mw" data-fx="msg" data-at="${at}"><div class="b out ${cls}">${html}<span class="t">${time}${TICK}</span></div></div>`;
const ms = (at, text, g) => `<div class="mw" data-fx="msg" data-at="${at}" style="padding-top:5px"><div class="sys ${g ? 'g' : ''}">${text}</div></div>`;
const ck = (at, text) => `<div class="ck" data-fx="row" data-at="${at}"><span class="bx">${I('check', 17, 3.2)}</span><span>${text}</span></div>`;
const note = (at, icon, h, p, bg = '#e9f9ef') => `<div class="card note" data-at="${at}"><span class="ic" style="background:${bg}">${icon}</span><div><h4>${h}</h4><p>${p}</p></div></div>`;
const wave = (at, n, color, h = 40) => `<div class="wave" data-at="${at}" data-n="${n}" style="height:${h}px;color:${color}"></div>`;

const mod = (o) => `<div class="scene" id="sc-${o.id}" data-wm="c">
  <div class="mhead" data-fx="left" data-at="s+0.05"><div class="micon">${I(o.icon, 38, 2.1)}</div><div><div class="mtitle">${o.title}</div><div class="msub">${o.sub}</div></div></div>
  <div class="feats">${o.feats.map(f => `<div class="feat" data-fx="left" data-at="${f[2]}"><span class="chk">${I('check', 20, 3)}</span><span><b>${f[0]}</b> ${f[1]}</span></div>`).join('')}
    <div class="outcome" data-fx="pop" data-at="${o.outcome[1]}"><small>OUTCOME</small><span>${o.outcome[0]}</span></div></div>
  ${o.center}
  <div class="right" style="${o.rightStyle || ''}">${o.right}</div></div>`;

const CSS = `
.logo-xl{position:absolute;left:50%;top:392px;height:168px;transform:translateX(-50%)}
.kicker{position:absolute;left:0;right:0;top:610px;text-align:center;font-size:25px;font-weight:600;letter-spacing:.52em;color:#3f5fbf;padding-left:.52em}
.word{position:absolute;left:0;right:0;top:372px;text-align:center;font-size:232px;font-weight:800;letter-spacing:-3px;line-height:1;color:#fff}
.word em{font-style:normal;color:#86b3ff}
.chip{display:inline-block;background:#e6edfd;color:var(--blue);font-size:15px;font-weight:700;letter-spacing:.3em;border-radius:9px;padding:10px 18px 9px}
.tagp{display:inline-flex;align-items:center;gap:11px;background:#fff;border-radius:30px;padding:11px 22px;font-size:19px;font-weight:500;color:#1f2a44;box-shadow:var(--shadow-s);white-space:nowrap}
.tagp i{width:7px;height:7px;border-radius:50%;background:var(--blue)}
.h-hero{position:absolute;left:110px;top:270px;font-size:100px;font-weight:700;line-height:1.02;letter-spacing:-2.4px}
.h-hero span{color:var(--blue)}
.plat{position:absolute;left:110px;top:668px;width:980px;height:110px;background:#fff;border-radius:22px;box-shadow:var(--shadow);display:flex;align-items:center;padding:0 34px}
.plat small{display:block;font-size:12.5px;font-weight:700;letter-spacing:.3em;color:#3d4a68;margin-bottom:5px}
.plat strong{font-size:27px;font-weight:600;letter-spacing:-.2px}
.plat .chs{margin-left:auto;display:flex;gap:28px;padding-left:30px}
.plat .ch{display:flex;flex-direction:column;align-items:center;gap:7px;font-size:12.5px;color:var(--mute2);color:#7682a0}
.plat .ch svg{color:var(--blue)}
.pdf{display:flex;gap:10px;align-items:center}
.pdf .pi{width:32px;height:36px;border-radius:6px;background:#e5484d;color:#fff;font-size:8.5px;font-weight:700;display:grid;place-items:center;letter-spacing:.3px}
.h-seven{position:absolute;left:0;right:0;top:132px;text-align:center;font-size:78px;font-weight:700;letter-spacing:-1.6px}
.mcard{position:absolute;width:404px;height:128px;background:#fff;border-radius:17px;display:flex;align-items:center;gap:22px;padding:0 26px;box-shadow:0 24px 50px rgba(8,25,90,.28);color:var(--ink)}
.mcard .ti{width:62px;height:62px;border-radius:15px;background:#e8eefd;color:var(--blue);display:grid;place-items:center;flex:none}
.mcard h3{font-size:27px;font-weight:700;letter-spacing:-.3px;line-height:1.15}
.mcard p{font-size:16px;color:var(--mute);margin-top:3px;line-height:1.3}
.booth{position:absolute;left:50%;top:786px;transform:translateX(-50%);white-space:nowrap;border:1.5px solid rgba(255,255,255,.28);background:rgba(255,255,255,.09);border-radius:40px;padding:15px 32px;font-size:22px;color:#dbe6ff}
.booth b{color:#fff;font-weight:600}
.okc{width:72px;height:72px;border-radius:50%;background:#e4f7ea;color:var(--green);display:grid;place-items:center}
.mem{display:flex;align-items:center;gap:16px;margin-top:13px}
.mem .a{width:46px;height:46px;border-radius:50%;color:#fff;font-size:14.5px;font-weight:700;display:grid;place-items:center;flex:none}
.mem h5{font-size:21px;font-weight:600;line-height:1.2}
.mem p{font-size:15px;color:var(--mute2)}
.photo{height:124px;border-radius:8px;background:radial-gradient(120% 90% at 30% 20%,#8b95a5,#4b5563 55%,#273142);position:relative;display:grid;place-items:center;color:rgba(255,255,255,.92)}
.photo .cp{position:absolute;left:8px;bottom:8px;background:rgba(10,14,22,.62);color:#fff;font-size:11px;border-radius:5px;padding:3px 7px;display:flex;gap:5px;align-items:center}
.fl{font-size:10.5px;color:#8696a0;margin-top:7px}
.fi{border:1px solid #dfe3e6;border-radius:6px;padding:6px 9px;font-size:13.5px;margin-top:3px;background:#fff}
.plans{display:grid;grid-template-columns:1fr 1.12fr 1fr;gap:5px;margin-top:8px}
.plans div{border:1px solid #e1e5ea;border-radius:6px;padding:5px 6px;font-size:10.5px;font-weight:600;line-height:1.35}
.plans small{display:block;font-size:8px;font-weight:600;color:#9aa3ad;letter-spacing:.3px}
.plans .rec{border:1.6px solid var(--blue);background:#f1f5ff}.plans .rec small{color:var(--blue)}
.banner{height:92px;border-radius:12px;background:linear-gradient(110deg,#1d4ed8,#1e9be0);display:grid;place-items:center;color:#fff;margin:14px 0 16px}
.wave{display:flex;align-items:center;gap:4px}
.wave span{display:block;width:4.5px;border-radius:3px;background:currentColor;height:100%}
.tr{border-radius:13px;padding:12px 16px 13px;margin-top:11px;background:#f0f4ff}
.tr.c{background:#f3f4f6}
.tr small{display:block;font-size:11.5px;font-weight:700;letter-spacing:.24em;color:#44506d}
.tr strong{display:block;white-space:nowrap;font-size:18.5px;font-weight:600;line-height:1.5;margin-top:1px}
.tr span{display:block;font-size:14.5px;color:var(--mute2)}
.vn{display:flex;align-items:center;gap:9px;min-width:215px}
.pl{width:30px;height:30px;border-radius:50%;background:#19a35b;color:#fff;display:grid;place-items:center;flex:none}
.conv{display:flex;gap:11px;background:#fff;border-radius:13px;padding:11px 12px 10px;box-shadow:0 1px 2px rgba(11,20,26,.10)}
.conv .a{width:40px;height:40px;border-radius:50%;color:#fff;font-size:12.5px;font-weight:700;display:grid;place-items:center;flex:none;margin-top:3px}
.conv h6{font-size:14.5px;font-weight:600;display:flex;justify-content:space-between}
.conv h6 span{font-size:10.5px;font-weight:400;color:#9aa3ad}
.conv p{font-size:12.5px;color:#667781;margin:1px 0 5px}
.stt{display:inline-block;white-space:nowrap;font-size:10.5px;font-weight:600;border-radius:5px;padding:2px 7px}
.stt.sg{background:#def6e6;color:#12803c}.stt.sa{background:#fdeccb;color:#b45309}.stt.sr{background:#fde2e2;color:#c81e1e}
.tile{flex:1;background:#f3f6fd;border-radius:14px;padding:14px 18px 12px}
.tile small{font-size:14.5px;color:var(--mute)}
.tile strong{display:block;font-size:44px;font-weight:700;line-height:1.15;letter-spacing:-.8px}
.wl{display:grid;grid-template-columns:118px 1fr 34px;align-items:center;gap:12px;margin-top:15px;font-size:18px;font-weight:600}
.wl .trk{height:8px;border-radius:4px;background:#e8ecf5;overflow:hidden}
.wl .trk i{display:block;height:100%;border-radius:4px;background:var(--blue)}
.wl em{font-style:normal;text-align:right}
.call{flex:1;display:flex;flex-direction:column;align-items:center;padding:22px 18px 0}
.clogo{width:92px;height:92px;border-radius:50%;background:#f1f5fe;display:grid;place-items:center;box-shadow:0 8px 22px rgba(29,78,216,.14)}
.clogo img{height:50px}
.cname{font-size:20px;font-weight:700;margin-top:15px;letter-spacing:-.2px}
.csub{font-size:12.5px;color:#8a8f98;margin-top:2px}
.dots{display:flex;gap:5px;margin-top:20px;height:12px;align-items:center}
.dots i{width:4.5px;height:4.5px;border-radius:50%;background:var(--blue)}
.cl{width:100%;margin-top:64px}
.cl div{display:flex;justify-content:space-between;align-items:center;font-size:13.5px;padding:11px 10px;border-radius:8px;color:#3a4252}
.cl div b{color:#12803c;font-weight:600;font-size:13px}
.cl div.q{background:#fff3df}.cl div.q b{color:#c2410c}
.endc{margin-top:auto;margin-bottom:30px;width:68px;height:68px;border-radius:50%;background:#e5383b;color:#fff;display:grid;place-items:center;box-shadow:0 10px 24px rgba(229,56,59,.35)}
.bub{border-radius:15px;padding:13px 18px;font-size:19.5px;line-height:1.42;color:#39445c}
.gauge{height:10px;border-radius:5px;background:linear-gradient(90deg,#22c55e,#eab308 50%,#ef4444);position:relative;margin:12px 0 0}
.gauge i{position:absolute;top:-8px;width:26px;height:26px;margin-left:-13px;border-radius:50%;background:#fff;border:4px solid #0b1020;box-shadow:0 2px 6px rgba(0,0,0,.2)}
.gl{display:flex;justify-content:space-between;font-size:14px;color:var(--mute2);margin-top:14px}
.kiosk{position:absolute;left:815px;top:50px;width:440px}
.kbody{background:#07080c;border-radius:30px;padding:14px 14px 0;box-shadow:0 40px 80px rgba(20,35,90,.24),0 10px 24px rgba(15,23,42,.14)}
.kscr{width:412px;height:627px;border-radius:17px;overflow:hidden;background:#dfe6ee}
.kscr img{width:100%;height:100%;object-fit:cover;display:block}
.kchin{height:52px;display:grid;place-items:center;color:#8a8f9c;font-size:15px;font-weight:500;letter-spacing:.5px}
.kneck{width:108px;height:92px;margin:0 auto;background:linear-gradient(90deg,#c9ced9,#f1f3f7 45%,#d5d9e2);clip-path:polygon(16% 0,84% 0,100% 100%,0 100%)}
.kbase{width:330px;height:24px;margin:0 auto;border-radius:13px;background:linear-gradient(180deg,#eef0f5,#cfd4de);box-shadow:0 14px 26px rgba(20,35,90,.16)}
.gb{flex:1;background:#fff;padding:0;display:flex;flex-direction:column;min-height:0}
.gcover{height:112px;background:linear-gradient(120deg,#cfe0f7,#eef4fc 45%,#d6e6f6);border-bottom:1px solid #e8edf3;display:grid;place-items:center;color:#9db6d8;flex:none}
.gin{padding:13px 14px 0}
.gin h3{font-size:19px;font-weight:700;letter-spacing:-.2px}
.gin .s{font-size:12px;color:#8a8f98;margin-top:1px}
.stars{color:#f5a623;letter-spacing:1px;font-size:13px}
.stars u{text-decoration:none;color:#d9dde3}
.gch{display:flex;gap:8px;margin-top:9px}
.gch span{font-size:12px;font-weight:600;border-radius:14px;padding:5px 12px;background:#e8effd;color:var(--blue)}
.gch span.on{background:var(--blue);color:#fff}
.rv{display:flex;gap:10px;margin-top:14px}
.rv .a{width:32px;height:32px;border-radius:50%;color:#fff;font-size:12px;font-weight:700;display:grid;place-items:center;flex:none}
.rv h6{font-size:13.5px;font-weight:600}.rv h6 span{font-weight:400;color:#9aa3ad;font-size:11px}
.rv p{font-size:12.5px;line-height:1.42;color:#4a5361;margin-top:3px}
.rep{background:#eef3ff;border-radius:9px;padding:9px 11px;margin-top:8px;font-size:12.2px;line-height:1.42;color:#3a4252}
.rep b{display:block;color:var(--blue);font-size:11px;margin-bottom:2px}
.vis{display:grid;grid-template-columns:132px 1fr 52px;align-items:center;gap:12px;margin-top:13px;font-size:17.5px;font-weight:600}
.vis .trk{height:9px;border-radius:5px;background:#e8ecf5;overflow:hidden}.vis .trk i{display:block;height:100%;border-radius:5px}
.vis em{font-style:normal;text-align:right}
.soc{display:flex;gap:14px;font-size:18px;line-height:1.4;color:#39445c;margin-top:10px}
.soc b{color:var(--blue);font-weight:600;flex:none;width:104px}
.h-hub{position:absolute;left:0;right:0;top:104px;text-align:center;font-size:62px;font-weight:700;letter-spacing:-1.3px}
.h-hub span{color:var(--blue)}
.hubc{position:absolute;left:862px;top:407px;width:196px;height:196px;border-radius:50%;background:#fff;box-shadow:0 0 0 12px rgba(29,78,216,.07),0 26px 60px rgba(29,78,216,.18);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;font-size:18.5px;font-weight:600;line-height:1.2;text-align:center}
.hubc img{height:62px}
.node{position:absolute;width:258px;height:74px;margin:-37px 0 0 -129px;background:#fff;border-radius:15px;box-shadow:var(--shadow-s);display:flex;align-items:center;gap:15px;padding:0 16px}
.node .ti{width:44px;height:44px;border-radius:11px;background:#e8eefd;color:var(--blue);display:grid;place-items:center;flex:none}
.node h5{font-size:21px;font-weight:700;letter-spacing:-.2px;line-height:1.15}.node p{font-size:14px;color:var(--mute2)}
.chrow{position:absolute;left:0;right:0;top:820px;display:flex;justify-content:center;gap:16px}
.chrow .tagp svg{color:var(--blue)}
.big{position:absolute;left:104px;top:268px;font-size:196px;font-weight:800;line-height:1;letter-spacing:-6px;background:linear-gradient(95deg,#1746d0 10%,#3b8bf2 95%);-webkit-background-clip:text;background-clip:text;color:transparent;white-space:nowrap;padding-right:20px}
.lg{display:grid;place-items:center;height:92px}
.h-cta{position:absolute;left:222px;top:330px;font-size:106px;font-weight:700;line-height:1.04;letter-spacing:-2.6px}
.h-cta span{color:var(--blue)}
.cbtn{position:absolute;top:706px;height:74px;border-radius:13px;display:flex;align-items:center;gap:12px;padding:0 34px;font-size:26px;font-weight:600}
.qrc{position:absolute;left:1336px;top:232px;width:404px;background:#fff;border-radius:26px;box-shadow:var(--shadow);padding:44px 40px 34px;text-align:center}
.qrc svg{width:324px;height:324px;margin:0 auto}
.qrc h3{font-size:30px;font-weight:600;line-height:1.35;margin-top:26px}
.qrc p{font-size:17px;color:var(--mute2);margin-top:8px}
.endw{position:absolute;left:0;right:0;top:268px;text-align:center}
.h-end{font-size:86px;font-weight:700;line-height:1.1;letter-spacing:-2px;margin-top:34px}
.h-end span{color:var(--blue)}
`;
document.head.appendChild(Object.assign(document.createElement('style'), { textContent: CSS }));

const arcs = `<div class="arc" style="left:-780px;top:-1160px;width:1760px;height:1760px"></div><div class="arc" style="left:1290px;top:580px;width:1500px;height:1500px"></div>`;
const S = {};

S.intro = `<div class="scene" id="sc-intro" data-wm="">${arcs}
  <img class="logo-xl" src="assets/chat360.png" data-fx="pop" data-at="s+0.15">
  <div class="kicker" data-fx="fade" data-at="s+1.9">AGENTIC AI FOR INSURANCE</div></div>`;

S.words = `<div class="scene blue" id="sc-words" data-wm="w">
  ${['QUOTE', 'CLAIM', 'RENEW', 'PROTECT'].map((w, i) => `<div class="word" data-word="${i}">${w}<em>.</em></div>`).join('')}</div>`;

S.hero = `<div class="scene" id="sc-hero" data-wm="c">
  <img src="assets/chat360.png" style="position:absolute;left:110px;top:96px;height:60px" data-fx="left" data-at="s+0.05">
  <div class="chip" style="position:absolute;left:110px;top:206px" data-fx="left" data-at="s+0.2">THE CHAT360 INSURANCE SUITE</div>
  <div class="h-hero" data-fx="left" data-at="s+0.32">Agentic AI for<br><span>Insurance</span></div>
  <div style="position:absolute;left:110px;top:540px;display:flex;gap:16px">
    ${['Life', 'General', 'Health', 'Motor', 'Bancassurance', 'POSP &amp; Agency'].map((t, i) => `<span class="tagp" data-fx="up" data-at="c1+${(0.95 + i * 0.32).toFixed(2)}"><i></i>${t}</span>`).join('')}</div>
  <div class="plat" data-fx="up" data-at="c0+2.1"><div><small>ONE AGENTIC AI PLATFORM</small><strong>Claims · Sales · Renewals · Compliance</strong></div>
    <div class="chs"><span class="ch">${WA(27, '#1d4ed8')}WhatsApp</span><span class="ch">${I('mic', 27)}Voice AI</span><span class="ch">${I('book-user', 27)}Kiosk</span><span class="ch">${I('globe', 27)}Web &amp; App</span></div></div>
  ${phone({ left: 1300, head: whead('shield-check', 'Insure360', 'Business account'), body: `<div class="chat">
    ${mi('s+1.0', 'Your cashless claim is approved. Pre-authorisation of <b>₹45,000</b> has been sent to the hospital.', '10:42', 'Insure360')}
    ${mo('c0+1.5', 'That was quick, thank you!', '10:42')}
    ${mi('c0+3.3', 'Happy to help, Rohan! Your policy summary and approval letter are attached.', '10:43')}
    ${mi('c1+0.9', `<div class="pdf"><span class="pi">PDF</span><div><b>Cashless_Approval.pdf</b><div class="sm">1 page</div></div></div>`, '10:43', null, 'wide')}
  </div>` })}</div>`;

const MODS = [['shield-check', 'Insure360', 'Cashless claims &amp; PIVC compliance'], ['trending-up', 'RM360', 'Quote-to-bind &amp; CKYC onboarding'], ['refresh-cw', 'Engage360', 'Renewals &amp; persistency'], ['users', 'Workforce360', 'Banca, agency &amp; POSP co-pilot'],
  ['book-user', 'Avatar Kiosk', 'Phygital branch experience'], ['eye', 'Agent360', 'Team visibility &amp; supervision'], ['star', 'Reach360', 'Reviews, profiles &amp; social presence']];
S.seven = `<div class="scene blue" id="sc-seven" data-wm="w">
  <div class="h-seven" data-fx="up" data-at="s+0.1">Seven modules. One platform.</div>
  ${MODS.map((m, i) => { const r = i < 4 ? 0 : 1, c = i < 4 ? i : i - 4; const x = r ? 326 + c * 432 : 110 + c * 432, y = r ? 532 : 364;
    return `<div class="mcard" style="left:${x}px;top:${y}px" data-fx="up" data-at="s+${(0.55 + i * 0.16).toFixed(2)}"><span class="ti">${I(m[0], 30)}</span><div><h3>${m[1]}</h3><p>${m[2]}</p></div></div>`; }).join('')}
  <div class="booth" data-fx="fade" data-at="s+2.3">Live demos at our booth &nbsp;·&nbsp; <b>Chat360 Agentic AI OS</b></div></div>`;

S.health = mod({ id: 'health', icon: 'shield-check', title: 'Insure360', sub: 'Cashless claims on WhatsApp',
  feats: [['Cashless claim', 'on WhatsApp in seconds', 'c1'], ['Policy fetched', 'and eligibility checked', 'c3'], ['Pre-authorisation', 'sent to the insurer', 'c5'], ['Pay only your share', 'at discharge', 'c7']],
  outcome: ['Cashless, from request to discharge', 'c9'],
  center: phone({ head: whead('shield-check', 'Insure360', 'Business account'), body: `<div class="chat">
    ${mo('c2', "I've been admitted to City Hospital. Please start a <b>cashless claim</b>.", '10:02')}
    ${mi('c3+0.9', `${OK} Policy found from your number<div class="sm" style="font-size:13.5px">Comprehensive Health Plan</div>`, '10:02', 'Insure360', 'wide')}
    ${mi('c5+0.5', `<b>Cashless Request Sent</b><br>${OK} Eligibility confirmed<br>Pre-authorisation sent to insurer`, '10:03', 'Insure360', 'wide')}
    ${mi('c6+0.5', `Pre-Authorisation Approved:<br><b style="font-size:17px">₹45,000</b>`, '10:45', ['Insurer', 'g'], 'wide')}
    ${mi('c7+0.6', `<span class="ok">✓ Discharge Approved</span><br>Insurer settles the hospital directly`, '11:20', 'Insure360', 'wide')}
    ${mi('c8+0.1', `<div style="display:flex;justify-content:space-between"><span>You pay at desk</span><b>₹7,150</b></div>`, '11:20', null, 'wide')}
  </div>` }),
  right: `<div class="card" data-at="c3"><div class="lbl">Agentic actions</div>
      ${ck('c3+0.5', 'Policy fetched from phone number')}${ck('c4+0.2', 'Eligibility checked')}${ck('c5+0.9', 'Pre-auth request sent to insurer')}${ck('c6+0.9', 'Insurer approval: ₹45,000')}${ck('c7+1.0', 'Discharge cleared, cashless')}</div>
    <div class="card" data-at="c8" style="margin-top:44px"><div class="lbl">At discharge</div>
      <div style="display:flex;justify-content:space-between;align-items:center"><div><div style="font-size:20px;color:var(--mute)">You pay at the desk</div>
      <div style="font-size:56px;font-weight:700;color:var(--blue);line-height:1.18;letter-spacing:-1.2px">₹7,150</div></div><span class="okc">${I('check', 34, 2.6)}</span></div>
      <div style="font-size:19.5px;font-weight:500;color:#27324a;margin-top:10px">Insurer pays the hospital directly</div></div>` });

const mem = (at, ini, col, h, p, extra = '') => `<div class="mem" data-fx="row" data-at="${at}"><span class="a" style="background:${col}">${ini}</span><div><h5>${h}</h5><p>${p}</p></div>${extra}</div>`;
S.motor = mod({ id: 'motor', icon: 'shield-check', title: 'Insure360', sub: 'Cashless motor claims with instant groups',
  feats: [['Photo to cashless claim', 'on WhatsApp', 'c1'], ['Claim group', 'created instantly', 'c3'], ['RM360', 'assesses damage from photos', 'c6'], ['Surveyor and insurer', 'join the group', 'c8']],
  outcome: ['One group. Everyone aligned.', 'c11'],
  center: phone({ head: `<div style="position:relative;height:62px;flex:none">
      ${whead('shield-check', 'Insure360', 'Business account', { style: 'position:absolute;inset:0', attr: 'data-out="c3+0.3"' })}
      ${whead('users', 'Claim CLM-2026-64318', 'You, Service Centre, Insurance Desk, Insurer', { verified: false, av: 'background:#dcf5e3;color:#12803c', style: 'position:absolute;inset:0', attr: 'data-fx="fade" data-at="c3+0.3"' })}</div>`,
    body: `<div class="chat">
    <div class="mw" data-fx="msg" data-at="c1+0.6"><div class="b out" style="padding:4px 4px 5px;width:80%"><div class="photo">${I('car-front', 46, 1.6)}<span class="cp">${I('camera', 12)}Car_Damage.jpg · 2 photos</span></div><span class="t" style="padding-right:5px">10:22${TICK}</span></div></div>
    ${mo('c2+0.3', 'Cashless at garage', '10:23', 'wide')}
    ${ms('c3+0.7', 'Insure360 created this group', true)}${ms('c4+0.9', 'Service Centre joined')}${ms('c5+0.2', 'Insurance Desk joined')}${ms('c5+1.3', 'Insurer joined')}
    ${mi('c7', `<b>Damage Assessment</b><div class="row" style="margin-top:6px"><span>Front Bumper, Headlamp</span><b>₹42,600</b></div>`, '10:24', 'RM360', 'wide')}
    ${mi('c8+1.5', 'Survey done. Estimate approved.', '11:40', ['Surveyor joined · Insurer', 'g'], 'wide')}
    ${mi('c9+0.6', `<span class="ok">✓ Ready for Pick-Up</span><div class="row" style="margin-top:6px"><span>Insurer pays garage</span><b>₹36,200</b></div><div class="row"><span>You pay at garage</span><b>₹6,400</b></div>`, '13:00', 'Insure360', 'wide')}
  </div>` }),
  right: `<div class="card" data-at="c3+0.2"><div class="lbl">Claim group · CLM-2026-64318</div>
      ${mem('c4', 'You', '#1d4ed8', 'Customer', 'Group creator')}${mem('c4+0.9', 'SC', '#f59e0b', 'Service Centre', 'Garage network')}${mem('c5+0.2', 'ID', '#8b5cf6', 'Insurance Desk', 'Claims team')}
      ${mem('c5+1.3', 'IN', '#16a34a', 'Insurer', 'Approvals &amp; payment')}${mem('c6+0.4', 'RM', '#2563eb', 'RM360', 'Assesses damage')}
      ${mem('c8+0.5', 'SV', '#e5484d', 'Surveyor', 'Joined the group', `<span class="pill" style="margin-left:auto;background:#def6e6;color:#12803c;font-size:14px;padding:4px 12px">joined</span>`)}</div>
    <div class="card" data-at="c9+0.9"><div class="lbl">Cashless settlement</div>
      <div class="kv" style="margin-top:0;font-size:22px"><span>Insurer pays garage</span><b style="color:var(--green);font-weight:700">₹36,200</b></div>
      <div class="kv" style="font-size:22px" data-fx="row" data-at="c10+0.5"><span>Customer pays garage</span><b style="font-weight:700">₹6,400</b></div></div>`,
  rightStyle: 'top:104px;gap:30px' });

S.rm = mod({ id: 'rm', icon: 'trending-up', title: 'RM360', sub: 'Quote-to-bind for term, health &amp; motor',
  feats: [['Native WhatsApp Flows,', 'no redirects', 'c0+0.5'], ['AI advisor', 'compares plans and riders', 'c1'], ['Recovers drop-offs', 'with a timely nudge', 'c3']],
  outcome: ['25–35% uplift in quote-to-bind', 'c5'],
  center: phone({ head: whead('trending-up', 'RM360', 'Business account'), body: `<div class="chat">
    ${mi('s+0.9', `<b>Get your health quote</b><div class="fl">Age</div><div class="fi">34</div><div class="fl">City</div><div class="fi">Mumbai</div><div class="fl">Cover</div><div class="fi">₹15 Lakh · Family floater</div><span class="btn" style="background:#0f8a5f;color:#fff">Get quotes</span>`, '10:42', 'WhatsApp Flow', 'wide')}
    ${mo('c0+2.5', 'Get quotes', '10:42', 'wide')}
    ${mi('c1', `Here are 3 plans for you.<br><b>Comprehensive</b> fits your family best.<div class="plans"><div><small>PLAN</small>Base<br>₹9,860</div><div class="rec"><small>RECOMMENDED</small>Comprehensive<br>₹14,200</div><div><small>PLAN</small>Super Top-up<br>₹3,450</div></div>`, '10:42', null, 'wide')}
    ${mo('c1+1.3', 'Does this cover consumables?', '10:42')}
    ${mi('c1+2.2', 'Yes, Comprehensive covers consumables, plus a free annual health check-up.', '10:42', null, 'wide')}
    ${mi('c2+0.7', `${OK} CKYC verified in <b>2 seconds</b><br>Proceed to pay <b>₹14,200</b><span class="btn" style="background:#e6edff;color:var(--blue)">Pay via UPI</span>`, '10:42', null, 'wide')}
  </div>` }),
  right: `<div class="card note" data-at="c3+0.2" style="border:1.5px solid #f6dfb5;gap:18px"><span class="ic" style="background:#fff3dc;border-radius:13px;color:#d97706">${I('triangle-alert', 27)}</span>
      <div><div class="lbl" style="color:#b7791f;margin-bottom:3px;font-size:12.5px">Drop-off detected</div><h4 style="font-size:22px">Checkout paused at payment</h4></div></div>
    <div class="card" data-at="c4"><div style="display:flex;align-items:center;gap:13px"><span class="pill" style="background:#e8effd;color:var(--blue)">RM360</span><span style="font-size:15px;color:var(--mute2)">Nudge on WhatsApp</span></div>
      <div class="banner">${I('shield-check', 40, 2)}</div><h4 style="font-size:23px;font-weight:600">Your plan is saved</h4>
      <p style="font-size:16.5px;line-height:1.5;color:var(--mute);margin:6px 0 16px">Comprehensive Health · ₹15L cover. Complete your purchase in one tap — your KYC is already done.</p>
      <span class="pill" style="background:var(--blue);color:#fff;margin-right:9px;padding:9px 18px">Pay ₹14,200 now</span><span class="pill" style="background:#e8effd;color:var(--blue);padding:9px 18px">Call me</span></div>
    ${note('c4+2.3', WA(27), 'Paid · Policy issued', 'Policy PDF sent on WhatsApp')}`,
  rightStyle: 'top:110px;gap:30px' });

const tr = (at, who, hi, en, c) => `<div class="tr ${c ? 'c' : ''}" data-fx="row" data-at="${at}"><small>${who}</small><strong>${hi}</strong><span>${en}</span></div>`;
S.engage = mod({ id: 'engage', icon: 'refresh-cw', title: 'Engage360', sub: 'Renewals &amp; persistency',
  feats: [['Renewal reminder', 'before the due date', 'c1'], ['Voice AI', 'in 22 languages', 'c3'], ['Payment link', 'on WhatsApp, mid-call', 'c5'], ['Pay in parts,', 'AutoPay keeps it active', 'c7']],
  outcome: ['Renewals on autopilot', 'c8+1.2'],
  center: phone({ head: whead('refresh-cw', 'Engage360', 'Business account'), body: `<div class="chat">
    ${mi('c1+0.3', `<b>Premium Due</b><br>Term Life · ₹1 Crore · <b>₹14,800</b><div style="margin-top:8px"><span class="pill" style="background:var(--blue);color:#fff;font-size:13px;padding:6px 14px;margin-right:7px">Pay now</span><span class="pill" style="background:#e6edff;color:var(--blue);font-size:13px;padding:6px 14px">Talk in Hindi</span></div>`, '10:30', 'Engage360', 'wide')}
    ${mi('c3', `<div style="display:flex;align-items:center;gap:10px"><span class="pl">${I('phone', 15, 2.4)}</span><b>Calling you now…</b></div>`, '10:31', 'Voice AI · Hindi', 'wide')}
    ${mi('c5+0.4', `<span class="sm">Call Summary · 01:12</span><br><b style="font-size:15.5px">ठीक है, लिंक भेज दीजिए।</b><br><span class="ok">✓ Payment Link Sent</span>`, '10:32', 'Voice AI · Hindi', 'wide')}
    ${mi('c7+0.4', `<span class="ok">✓ Paid in 2 Parts</span><div class="row" style="margin-top:6px"><span>Part 1 · Paid Today</span><b>₹7,400</b></div><div class="row"><span>Part 2 · Pending 2027</span><b>₹7,400</b></div>`, '10:40', 'Engage360', 'wide')}
    ${mi('c8+0.3', `<span class="ok">✓ AutoPay Set</span><br>Policy Active`, '10:41', 'Engage360', 'wide')}
  </div>` }),
  right: `<div class="card" data-at="c3+0.1" style="padding-bottom:22px"><div style="display:flex;align-items:center;gap:16px"><span class="note" style="padding:0"><span class="ic" style="background:#e8effd;color:var(--blue)">${I('phone', 24)}</span></span>
        <div><div class="lbl" style="margin-bottom:1px">Voice AI · Live</div><h4 style="font-size:23px;font-weight:600">Renewal call</h4></div></div>
      <div style="margin:15px 0 13px">${wave('c3+0.2', 27, '#19b45c', 38)}</div>
      <span class="pill" style="background:#e8effd;color:var(--blue);margin-right:9px">Regional languages</span><span class="pill" style="background:#e8effd;color:var(--blue)">22 languages</span>
      ${tr('c3+1.1', 'VOICE AI', 'नमस्ते! आपकी पॉलिसी 15 दिनों में रिन्यू होनी है।', 'Your policy is due for renewal in 15 days.')}
      ${tr('c4', 'CUSTOMER', 'प्रीमियम थोड़ा ज़्यादा है।', 'The premium is a bit high.', true)}
      ${tr('c4+1.1', 'VOICE AI', 'आप इसे मासिक किस्तों में भी भर सकते हैं।', 'You can also pay in monthly instalments.')}</div>
    ${note('c5+0.9', WA(27), 'UPI link sent on WhatsApp', 'While the customer is still on the call')}`,
  rightStyle: 'top:96px;gap:28px' });

S.workforce = mod({ id: 'workforce', icon: 'users', title: 'Workforce360', sub: 'Co-pilot for bancassurance, agency &amp; POSP',
  feats: [['Instant quotes', 'from a voice note', 'c1'], ['Co-branded PDFs', 'in seconds', 'c2'], ['Coaching', 'on riders and rules', 'c3'], ['Leads auto-logged', 'in Salesforce', 'c5']],
  outcome: ['Quotes in seconds, not hours', 'c5+1.6'],
  center: phone({ head: whead('users', 'Workforce360', 'Advisor mode'), body: `<div class="chat">
    <div class="mw" data-fx="msg" data-at="s+1.2"><div class="b out"><div class="vn"><span class="pl">${I('mic', 16, 2.2)}</span>${wave('s+1.2', 22, '#5f9a7c', 22)}<span class="sm" style="margin-left:4px">0:09</span></div>
      <div class="sm" style="margin-top:6px;font-style:italic;max-width:250px">“38, non-smoker, ₹1 Cr term cover till 60 with accidental death rider”</div><span class="t">10:40${TICK}</span></div></div>
    ${mi('c1+0.6', `<span class="sm">₹1 Cr term · age 38 · cover till 60</span><div class="row" style="margin-top:6px"><span>Term Plan A + ADB rider</span><b>₹14,980/yr</b></div><div class="row"><span>Term Plan B + ADB rider</span><b>₹15,640/yr</b></div>`, '10:40', 'Quotes', 'wide')}
    ${mo('c2', 'Send a co-branded PDF I can forward to him', '10:41')}
    ${mi('c2+1.0', `<div class="pdf"><span class="pi">PDF</span><div><b>Benefit_Illustration.pdf</b><div class="sm">2 pages · Co-branded</div></div></div><div class="sm" style="margin-top:7px">Talking points: claim settlement ratio, rider benefits, tax savings.</div>`, '10:41', null, 'wide')}
    ${mo('c3+0.3', 'How do I explain the accidental death rider to him?', '10:42')}
    ${mi('c3+1.5', `<div style="font-size:13px;line-height:1.5">1. Pays an extra ₹1 Cr if death is due to an accident<br>2. Adds only a small premium to the base cover<br>3. Ask him: “Do you drive or commute daily?”</div>`, '10:42', 'PITCH IT IN 3 POINTS', 'wide')}
    ${mo('c4+0.7', 'Any medical tests needed?', '10:43')}
    ${mi('c4+1.7', `<div style="font-size:13px;line-height:1.5">For ₹1 Cr at 38, non-smoker: tele-medical + basic tests. Share the checklist in advance.</div>`, '10:43', ['UNDERWRITING RULE', 'g'], 'wide')}
  </div>` }),
  right: `<div class="card" data-at="c1+0.2"><div class="lbl">Co-pilot understood</div>
      <div class="kv" style="margin-top:0" data-fx="row" data-at="c1+0.6"><span>Age</span><b>38</b></div><div class="kv" data-fx="row" data-at="c1+0.9"><span>Habit</span><b>Non-smoker</b></div>
      <div class="kv" data-fx="row" data-at="c1+1.2"><span>Cover</span><b>₹1 Crore · till 60</b></div><div class="kv" data-fx="row" data-at="c1+1.5"><span>Rider</span><b>Accidental death</b></div></div>
    <div class="card" data-at="c3+0.1"><div class="lbl">Advisor coaching</div>
      ${ck('c3+1.6', 'Rider explained in plain language')}${ck('c4+0.9', 'Underwriting rules from product docs')}${ck('c4+2.2', 'Next-best question to ask the client')}</div>
    <div class="card note" data-at="c5+0.4"><span class="ic" style="background:#e3f1fd;border-radius:13px;color:#0f8fe0">${I('cloud', 27, 2.2)}</span><div><div class="lbl" style="margin-bottom:3px;font-size:12.5px">CRM sync</div><h4>Lead + quote ID logged</h4><p>Synced to Salesforce</p></div></div>`,
  rightStyle: 'top:110px;gap:30px' });

const conv = (at, ini, col, name, msg, st, cls, time) => `<div class="mw" data-fx="msg" data-at="${at}"><div class="conv"><span class="a" style="background:${col}">${ini}</span><div style="flex:1"><h6>${name}<span>${time}</span></h6><p>${msg}</p><span class="stt ${cls}">${st}</span></div></div></div>`;
const wl = (name, pct, val, col) => `<div class="wl"><span>${name}</span><span class="trk"><i data-fx="bar" data-at="c1+0.6" style="width:${pct}%;${col ? 'background:' + col : ''}"></i></span><em>${val}</em></div>`;
S.agent = mod({ id: 'agent', icon: 'eye', title: 'Agent360', sub: 'Team visibility &amp; live supervision',
  feats: [['Full visibility', 'of the team', 'c0+0.6'], ['Live chats,', 'workloads, response times', 'c1'], ['Nothing slips', 'through', 'c2']],
  outcome: ['Every conversation, in one view', 'c2+0.8'],
  center: phone({ input: 'Search conversations', head: whead(null, 'Team Inbox', 'Live · 128 conversations', { verified: false, phone: false, av: 'background:#1d4ed8' }), body: `<div class="chat" style="justify-content:flex-start;padding-top:4px">
    ${conv('s+0.9', 'PN', '#1d4ed8', 'Priya Nair', 'Claim status for CLM-64318?', 'Handling · 18s', 'sg', 'now')}
    ${conv('s+1.25', 'AM', '#8b5cf6', 'Arjun Mehta', 'Need renewal quote for term plan', 'Handling · 22s', 'sg', '1m')}
    ${conv('s+1.6', 'SK', '#f59e0b', 'Sana Khan', 'Hospital asking for pre-auth…', 'Busy · 31s', 'sa', '2m')}
    ${conv('s+1.95', 'VR', '#16a34a', 'Vikram Rao', 'Premium receipt please', 'Handling · 20s', 'sg', '3m')}
    ${conv('c2', 'NJ', '#e5484d', 'Neha Joshi', 'No reply for 6 min', 'Needs attention', 'sr', '6m')}
  </div>` }),
  right: `<div class="card" data-at="c0+1.2"><div class="lbl">Live overview</div><div style="display:flex;gap:14px">
      <div class="tile"><small>Live chats</small><strong style="color:var(--blue)">128</strong></div><div class="tile"><small>Avg response</small><strong style="color:var(--green)">24s</strong></div></div></div>
    <div class="card" data-at="c1+0.3"><div class="lbl" style="margin-bottom:6px">Workload per agent</div>
      ${wl('Priya', 80, 11)}${wl('Arjun', 65, 9)}${wl('Sana', 90, 12, '#f59e0b')}${wl('Vikram', 50, 7)}${wl('Neha', 50, 7)}</div>
    <div class="card note" data-at="c2+0.4"><span class="ic" style="background:#fde8e8;color:#dc2626">${I('zap', 25, 2.2)}</span><div><h4>Delayed chat flagged</h4><p>Reassigned to an available agent</p></div></div>`,
  rightStyle: 'top:118px;gap:36px' });

const clr = (at, t, q) => `<div class="${q ? 'q' : ''}" data-fx="row" data-at="${at}"><span>${t}</span><b>${q ? '! Query raised' : '✓ Confirmed'}</b></div>`;
S.pivc = mod({ id: 'pivc', icon: 'clipboard-check', title: 'Insure360', sub: 'Compliance · Voice pre-issuance verification',
  feats: [['Automated PIVC', 'after every proposal', 'c1'], ['Detects hesitation', 'and confusion', 'c2'], ['Timestamped transcript', 'for audit', 'c4']],
  outcome: ['Every policy verified and audit-ready', 'c4+1.3'],
  center: phone({ white: true, input: false, body: `<div class="call">
    <div class="clogo"><img src="assets/chat360-mark.png"></div><div class="cname">Insure360 Voice AI</div><div class="csub">PIVC verification · 01:07</div>
    <div class="dots" data-dots="30"></div>
    <div class="cl">${clr('c1+0.3', 'Identity &amp; date of birth')}${clr('c1+0.9', 'Sum assured ₹50 Lakh')}${clr('c1+1.5', 'Premium term 10 years')}${clr('c1+2.1', 'Medical disclosures')}${clr('c2+0.7', '5-year lock-in', true)}</div>
    <div class="endc">${I('phone-off', 28, 2.2)}</div></div>` }),
  right: `<div class="card" data-at="c2-0.1"><div class="lbl">Live transcript</div>
      <div class="bub" style="background:#f1f2f5;margin-left:40px" data-fx="row" data-at="c2+0.1">“Wait, can I withdraw the full amount after 2 years?”</div>
      <div class="bub" style="background:#e8effd;margin:13px 40px 0 0" data-fx="row" data-at="c2+1.4">“This plan has a 5-year lock-in, so a full withdrawal isn’t possible before then. Shall I explain the options?”</div></div>
    <div class="card" data-at="c3"><div class="lbl" style="margin-bottom:20px">Mis-selling risk</div><div class="gauge"><i id="knob" style="left:8%"></i></div>
      <div class="gl"><span>Low</span><span>Medium</span><span>High</span></div>
      <div style="font-size:21.5px;font-weight:600;color:#b45309;margin-top:14px" data-fx="row" data-at="c3+1.0">Flagged for supervisor review</div></div>
    ${note('c4+0.4', WA(27), 'Consent summary on WhatsApp', 'Transcript stored in the audit vault')}`,
  rightStyle: 'top:112px;gap:30px' });

S.kiosk = mod({ id: 'kiosk', icon: 'book-user', title: 'Avatar Kiosk', sub: 'Phygital branch &amp; booth experience',
  feats: [['Lifelike AI avatar', 'in 12+ languages', 'c0+0.6'], ['Instant policy', 'endorsements', 'c4'], ['Continue on WhatsApp', 'with one scan', 'c5']],
  outcome: ['A 24/7 concierge at every branch', 'c6'],
  center: `<div class="kiosk" data-fx="rise" data-at="s+0.12"><div class="kbody"><div class="kscr"><img id="avatar" alt=""></div><div class="kchin">Chat360</div></div><div class="kneck"></div><div class="kbase"></div></div>`,
  right: `<div class="card" data-at="c1-0.2"><div class="lbl">Customer asks</div><div class="bub" style="background:var(--blue);color:#fff;font-size:21px">How do I add my newborn to my health policy?</div></div>
    <div class="card" data-at="c2"><div class="lbl">Avatar is answering</div>${wave('c2', 26, '#1d4ed8', 36)}
      <h4 style="font-size:19px;font-weight:600;margin:16px 0 4px">Endorsement checklist</h4>
      <div style="font-size:17.5px;color:#39445c;line-height:1.75"><div data-fx="row" data-at="c3+0.9">${OK}&nbsp; Birth certificate</div><div data-fx="row" data-at="c3+2.2">${OK}&nbsp; Endorsement request form</div></div></div>
    <div class="card" data-at="c5+0.3" style="display:flex;gap:20px;align-items:center;padding:22px 24px"><div style="width:116px;height:116px;flex:none">${QRS.site}</div>
      <div><h4 style="font-size:20px;font-weight:600;display:flex;gap:9px;align-items:center">${WA(21)}Continue on WhatsApp</h4><p style="font-size:14.5px;line-height:1.5;color:var(--mute2);margin-top:5px">Scan the code on the kiosk. The checklist follows you, so there are no repeat questions.</p></div></div>
    <div class="card note" data-at="c5+1.9" style="padding:18px 24px"><span class="ic" style="width:44px;height:44px">${WA(24)}</span><div><h4 style="font-size:19.5px">Documents requested on WhatsApp</h4><p>Upload link sent to Priya</p></div></div>`,
  rightStyle: 'top:96px;gap:24px' });

const vis = (n, p, col) => `<div class="vis"><span>${n}</span><span class="trk"><i data-fx="bar" data-at="c3+0.7" style="width:${p}%;background:${col}"></i></span><em>${p}%</em></div>`;
S.reach = mod({ id: 'reach', icon: 'star', title: 'Reach360', sub: 'Reputation &amp; digital presence',
  feats: [['Digital presence', 'and customer trust', 'c0+0.6'], ['Automated', 'review management', 'c2'], ['Google Business', 'profiles, managed', 'c3'], ['Social media', 'presence, strengthened', 'c4']],
  outcome: ['Visible, credible, connected', 'c5+0.5'],
  center: phone({ white: true, input: 'Search', body: `<div class="gb"><div class="gcover">${I('building-2', 46, 1.4)}</div><div class="gin">
      <h3>SecureLife Insurance</h3><div class="s">Andheri West Branch · Insurance agency</div>
      <div style="display:flex;gap:6px;align-items:center;margin-top:6px;font-size:13px"><b>4.6</b><span class="stars">★★★★★</span><span style="color:#9aa3ad;font-size:12px">(1,284)</span></div>
      <div class="gch"><span>Directions</span><span>Call</span><span class="on">Reviews</span></div>
      <div class="rv" data-at="c2+0.2"><span class="a" style="background:#e5484d">N</span><div><h6>Neha Kulkarni <span>a day ago</span></h6><div class="stars">★★<u>★★★</u></div>
        <p>Cashless approval for my mother's surgery took 3 weeks and nobody updated me.</p>
        <div class="rep" data-fx="row" data-at="c2+1.7"><b>Response from the owner · just now</b>Hi Neha, we are sorry for the delay. Your claim has been prioritised and our claims manager will call you today.</div></div></div>
      <div class="rv" data-at="c3+0.2"><span class="a" style="background:#16a34a">A</span><div><h6>Arjun Mehta <span>a day ago</span></h6><div class="stars">★★★★★</div><p>Claim settled on WhatsApp in a day. Very smooth!</p></div></div>
    </div></div>` }),
  right: `<div class="card" data-at="c2+0.7"><div class="lbl">Reach360 · AI reply drafted</div>
      <p style="font-size:19px;line-height:1.5;color:#39445c">Negative review detected (2★, claim delay) → reply drafted, claim escalated to the branch manager.</p>
      <div style="margin-top:14px"><span class="pill" style="background:#fdeccb;color:#b45309;margin-right:9px">Sentiment: negative</span><span class="pill" style="background:#def6e6;color:#12803c">Escalated</span></div></div>
    <div class="card" data-at="c3+0.4"><div class="lbl" style="line-height:1.6;margin-bottom:8px">Visibility · “Best health insurance in Mumbai”</div>
      ${vis('Your brand', 62, '#1d4ed8')}${vis('Competitor A', 54, '#8fa2d8')}${vis('Competitor B', 37, '#8fa2d8')}</div>
    <div class="card" data-at="c4+0.2"><div class="lbl">Social media presence</div>
      <div class="soc" style="margin-top:0"><b>Instagram</b><span>Renewed my health policy on WhatsApp in 2 mins!</span></div>
      <div class="soc" data-fx="row" data-at="c4+0.8"><b>Facebook</b><span>Branch staff were really helpful today</span></div>
      <div class="soc" data-fx="row" data-at="c4+1.4"><b>LinkedIn</b><span>3 posts scheduled this week</span></div></div>`,
  rightStyle: 'top:96px;gap:26px' });

const HUB = [[960, 258, 'shield-check', 'Insure360', 'Claims &amp; compliance'], [1456, 356, 'refresh-cw', 'Engage360', 'Renewals'], [1580, 572, 'trending-up', 'RM360', 'Quote-to-bind'], [1238, 742, 'users', 'Workforce360', 'Sales co-pilot'],
  [682, 742, 'book-user', 'Avatar Kiosk', 'Phygital AI'], [340, 572, 'eye', 'Agent360', 'Team visibility'], [464, 356, 'star', 'Reach360', 'Reputation']];
S.hub = `<div class="scene" id="sc-hub" data-wm="c">
  <div style="position:absolute;left:0;right:0;top:54px;text-align:center" data-fx="fade" data-at="s+0.05"><span class="chip">CHAT360 AGENTIC AI OS</span></div>
  <div class="h-hub" data-fx="up" data-at="s+0.15">One platform for <span>every insurance journey</span></div>
  <svg width="1920" height="1080" style="position:absolute;left:0;top:0" fill="none">
    ${HUB.map((n, i) => `<line class="hl" data-i="${i}" x1="960" y1="505" x2="${n[0]}" y2="${n[1]}" stroke="#9db1e3" stroke-width="2"/><circle class="hd" data-i="${i}" cx="${(960 + n[0]) / 2 + (n[0] - 960) * 0.08}" cy="${(505 + n[1]) / 2 + (n[1] - 505) * 0.08}" r="6" fill="#1d4ed8"/>`).join('')}</svg>
  <div class="hubc" data-fx="pop" data-at="s+0.35"><img src="assets/chat360-mark.png"><div>Agentic<br>AI OS</div></div>
  ${HUB.map((n, i) => `<div class="node" style="left:${n[0]}px;top:${n[1]}px" data-fx="pop" data-at="s+${(0.85 + i * 0.2).toFixed(2)}"><span class="ti">${I(n[2], 23)}</span><div><h5>${n[3]}</h5><p>${n[4]}</p></div></div>`).join('')}
  <div class="chrow">${[[WA(19, '#1d4ed8'), 'WhatsApp'], [I('mic', 19), 'Voice AI'], [I('globe', 19), 'Web &amp; App'], [I('book-user', 19), 'Kiosk'], [I('chart-column', 19), 'CRM &amp; core systems']]
    .map((c, i) => `<span class="tagp" data-fx="up" data-at="c1+${(0.1 + i * 0.22).toFixed(2)}">${c[0]}${c[1]}</span>`).join('')}</div></div>`;

S.proof = `<div class="scene" id="sc-proof" data-wm="c">
  <div class="lbl" style="position:absolute;left:112px;top:128px;color:var(--blue);font-size:15px" data-fx="left" data-at="s+0.05">Proof in production</div>
  <div class="card" style="position:absolute;left:110px;top:168px;padding:14px 22px;border-radius:14px" data-fx="left" data-at="s+0.15"><img src="assets/chola.png" style="height:64px;display:block"></div>
  <div class="big" id="crore" data-fx="left" data-at="c0+0.5">₹1.7 Crore</div>
  <div style="position:absolute;left:112px;top:486px;font-size:35px;font-weight:600;letter-spacing:-.3px;color:#172038" data-fx="left" data-at="c0+1.5">Premium collected through WhatsApp payments</div>
  <span class="pill" style="position:absolute;left:112px;top:604px;background:var(--blue);color:#fff;font-size:27px;padding:15px 32px;border-radius:40px;box-shadow:0 14px 30px rgba(29,78,216,.3)" data-fx="pop" data-at="c1+1.3">In just 3 months</span>
  <div class="card" style="position:absolute;left:1232px;top:128px;width:520px;padding:30px 48px 36px" data-fx="right" data-at="c2+0.1">
    <div style="font-size:126px;font-weight:800;color:var(--blue);line-height:1.1;letter-spacing:-3px">400+</div><div style="font-size:31px;font-weight:600;letter-spacing:-.3px">Brands use Chat360</div></div>
  <div class="card" style="position:absolute;left:1132px;top:448px;width:680px;padding:30px 34px 26px" data-fx="right" data-at="c2+0.7"><div class="lbl" style="margin-bottom:6px">Trusted by</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 20px"><div class="lg"><img src="assets/chola.png" style="height:58px"></div><div class="lg"><img src="assets/iifl.png" style="height:50px"></div>
      <div class="lg"><img src="assets/jm.png" style="height:62px"></div><div class="lg"><img src="assets/motilal.png" style="height:78px"></div></div>
    <div style="border-top:1.5px solid var(--line);margin-top:10px;padding-top:18px;display:flex;align-items:center;gap:26px"><div class="lbl" style="margin:0">Technology partner</div>
      <div style="background:#f1f5fd;border-radius:12px;padding:8px 20px"><img src="assets/meta.png" style="height:60px;display:block"></div></div></div></div>`;

S.cta = `<div class="scene" id="sc-cta" data-wm="">${arcs}
  <img src="assets/chat360.png" style="position:absolute;left:222px;top:150px;height:90px" data-fx="left" data-at="s+0.05">
  <div class="h-cta" data-fx="left" data-at="s+0.2">Ready to put<br><span>Agentic AI</span> to work<br>in insurance?</div>
  <div class="cbtn" style="left:222px;background:#fff;color:var(--blue);box-shadow:var(--shadow-s)" data-fx="up" data-at="c1+1.6">Chat360.ai</div>
  <div class="cbtn" style="left:448px;background:linear-gradient(100deg,#1a45c9,#2a67ea);color:#fff;box-shadow:0 16px 34px rgba(29,78,216,.34)" data-fx="up" data-at="c1+1.8">Book a Demo ${I('arrow-right', 26, 2.4)}</div>
  <div class="qrc" data-fx="pop" data-at="s+0.6">${QRS.demo}<h3>Scan to Book a Demo</h3><p>or visit our booth for a live demo</p></div></div>`;

S.end = `<div class="scene" id="sc-end" data-wm="">${arcs}<div class="endw">
  <div data-fx="fade" data-at="s+0.1"><span class="chip" style="border-radius:30px;padding:12px 24px 11px">THE CHAT360 PLATFORM</span></div>
  <div class="h-end"><div data-fx="up" data-at="s+0.35">One Omnichannel Agentic AI Platform</div><div data-fx="up" data-at="s+0.6"><span>for Every Insurance Journey</span></div></div>
  <div style="font-size:31px;color:var(--mute);margin-top:44px" data-fx="fade" data-at="s+1.0">Intelligent Conversations. Real Results.</div>
  <div style="display:flex;justify-content:center;gap:16px;margin-top:38px">${[[WA(20, '#1d4ed8'), 'WhatsApp'], [`<span style="color:var(--blue)">${I('mic', 20)}</span>`, 'Voice AI'], ['<i style="background:#e1306c;width:10px;height:10px"></i>', 'Instagram'], ['<i style="background:#1877f2;width:10px;height:10px"></i>', 'Facebook'], [`<span style="color:var(--blue)">${I('globe', 20)}</span>`, 'Web &amp; App']]
    .map((c, i) => `<span class="tagp" style="font-size:21px;padding:13px 24px" data-fx="up" data-at="s+${(1.2 + i * 0.12).toFixed(2)}">${c[0]}${c[1]}</span>`).join('')}</div>
  <img src="assets/chat360.png" style="height:92px;margin-top:62px" data-fx="pop" data-at="s+0.15"></div></div>`;

window.SCENES_HTML = S;
})();
