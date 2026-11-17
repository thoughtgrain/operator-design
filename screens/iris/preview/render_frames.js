// Render every *.svg in a folder to a 480 x 220 PNG at 1:1 with Playwright's Chromium.
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const [inDir, outDir] = process.argv.slice(2); fs.mkdirSync(outDir, { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 480, height: 220 }, deviceScaleFactor: 1 });
  for (const f of fs.readdirSync(inDir).filter(f => f.endsWith('.svg')).sort()) {
    await p.setContent(`<html><body style="margin:0;background:#000">${fs.readFileSync(path.join(inDir, f), 'utf8')}</body></html>`);
    await p.screenshot({ path: path.join(outDir, f.replace(/\.svg$/, '.png')), clip: { x: 0, y: 0, width: 480, height: 220 } });
  }
  await b.close();
})();
