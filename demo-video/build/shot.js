// usage: node shot.js out.png t [dsf]   — single still for QA
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const [out, t, dsf] = [process.argv[2], parseFloat(process.argv[3]), parseFloat(process.argv[4] || '1')];
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: dsf });
  p.on('pageerror', e => console.log('PAGEERROR', e.message)); p.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
  await p.goto('file://' + path.resolve(__dirname, 'index.html'));
  await p.waitForFunction('window.ready===true', null, { timeout: 60000 });
  const times = (process.argv[3] || '0').split(',').map(Number);
  for (let i = 0; i < times.length; i++) { await p.evaluate(x => window.seek(x), times[i]); await p.screenshot({ path: times.length > 1 ? out.replace('.png', `_${i}.png`) : out }); }
  await b.close();
})();
