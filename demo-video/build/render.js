// usage: node render.js <startFrame> <endFrame> <out.mp4> [dsf=2]  — frame-accurate render of [start,end)
const { chromium } = require('playwright'); const path = require('path'); const { spawn } = require('child_process');
(async () => {
  const a = +process.argv[2], bEnd = +process.argv[3], out = process.argv[4], dsf = +(process.argv[5] || 2), FPS = 30;
  const browser = await chromium.launch({ args: ['--force-color-profile=srgb', '--disable-lcd-text', '--font-render-hinting=none'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => { console.error('PAGEERROR', e.message); process.exit(2); });
  await page.goto('file://' + path.resolve(__dirname, 'index.html'));
  await page.waitForFunction('window.ready===true', null, { timeout: 120000 });
  const cdp = await page.context().newCDPSession(page);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-vf', 'scale=in_range=pc:out_range=tv:out_color_matrix=bt709:flags=accurate_rnd+full_chroma_int,format=yuv420p',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-g', '60', '-keyint_min', '60', '-sc_threshold', '0', '-bf', '2',
    '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv', '-threads', '2', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now(); let buf = null, shots = 0;
  for (let f = a; f < bEnd; f++) {
    const still = f > a && await page.evaluate(([p, t]) => window.isStatic(p, t), [(f - 1) / FPS, f / FPS]);
    if (!still) {
      await page.evaluate(t => window.seek(t), f / FPS);
      const { data } = await cdp.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true, clip: { x: 0, y: 0, width: 1920, height: 1080, scale: dsf } });
      buf = Buffer.from(data, 'base64'); shots++;
    }
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - a) % 300 === 299) console.log(`${out}: ${f - a + 1}/${bEnd - a} frames, ${((f - a + 1) / ((Date.now() - t0) / 1000)).toFixed(1)} fps`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await browser.close();
  console.log('done', out, shots + ' captured of ' + (bEnd - a), ((Date.now() - t0) / 1000).toFixed(0) + 's');
})();
