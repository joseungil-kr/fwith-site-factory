// Fresh headless browser, localhost-only: never attaches to the user's Ego session.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import crypto from 'node:crypto';
const require = createRequire(import.meta.url);
const {chromium} = require(process.env.PLAYWRIGHT_MODULE);
const output = path.resolve('docs/regional-worker-integration/screenshots');
await fs.mkdir(output, {recursive: true});
const browser = await chromium.launch({executablePath: process.env.LOCAL_BROWSER_EXE, headless: true,
  args: ['--no-proxy-server', '--disable-background-networking', '--disable-gpu', '--force-color-profile=srgb',
    '--host-resolver-rules=MAP seoul-dongjak.fwith.kr 127.0.0.1, MAP seoul-geumcheon.fwith.kr 127.0.0.1']});
const rows = [];
const blocked = [];
try {
  for (const [i, region] of ['dongjak', 'geumcheon'].entries()) for (const width of [390, 1280]) {
    const context = await browser.newContext({viewport: {width, height: 900}, deviceScaleFactor: 1, reducedMotion: 'reduce'});
    await context.route('**/*', route => {
      const url = new URL(route.request().url());
      if (url.protocol === 'http:' && url.hostname === `seoul-${region}.fwith.kr` && ['8787','8788','8789'].includes(url.port)) return route.continue();
      blocked.push(url.href);
      return route.abort();
    });
    const page = await context.newPage();
    for (const [label, route] of Object.entries({home: '/', directory: '/regions/', detail: `/regions/${region}-funeral-wreath/`, missing: '/unknown-page'})) {
      const captures = [];
      for (const port of [8788+i, 8787]) {
        const response = await page.goto(`http://seoul-${region}.fwith.kr:${port}${route}`, {waitUntil: 'networkidle'});
        await page.evaluate(async () => {
          for (const image of document.images) image.loading = 'eager';
          await document.fonts.ready;
          await Promise.race([
            Promise.all([...document.images].map(image => image.decode())),
            new Promise((_, reject) => setTimeout(() => reject(new Error('Image decode timeout')), 10000)),
          ]);
          scrollTo(0, 0);
          await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        });
        let image;
        let stable = false;
        for (let attempt = 0; attempt < 6; attempt++) {
          const next = await page.screenshot({fullPage: true, animations: 'disabled'});
          if (image?.equals(next)) { image = next; stable = true; break; }
          image = next;
          await new Promise(resolve => setTimeout(resolve, 250));
        }
        if (!stable) throw new Error('Raster did not stabilize: ' + route);
        captures.push({status: response.status(), sha256: crypto.createHash('sha256').update(image).digest('hex'),
          overflow: await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), image});
      }
      const file = `${region}-${width}-${label}.png`;
      await fs.writeFile(path.join(output, file), captures[1].image);
      if (!captures[0].image.equals(captures[1].image)) await fs.writeFile(path.join(output, `${region}-${width}-${label}-baseline.png`), captures[0].image);
      rows.push({region, width, route, file, equal: captures[0].image.equals(captures[1].image),
        baseline: {...captures[0], image: undefined}, candidate: {...captures[1], image: undefined}});
      console.log(`${region} ${width} ${label}: ${rows.at(-1).equal ? 'identical' : 'DIFF'}`);
    }
    await context.close();
  }
} finally {
  await browser.close();
}
const report = {scope: 'local baseline versus local integrated rendering; no production browser access',
  comparisons: rows.length, failures: rows.filter(row => !row.equal || row.candidate.overflow).length,
  blockedExternalRequests: [...new Set(blocked)], rows};
await fs.writeFile(path.join(output, '../visual-results.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({comparisons: report.comparisons, failures: report.failures, blockedExternalRequests: report.blockedExternalRequests}));
process.exitCode = report.failures ? 1 : 0;
