import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const base = 'http://127.0.0.1:8787';
const out = path.resolve('qa-browser-artifacts');
fs.mkdirSync(out, { recursive: true });

for (let i = 0; i < 80; i++) {
  try {
    const r = await fetch(base + '/');
    if (r.ok && (await r.text()).includes('백세푸드')) break;
  } catch (e) {
    if (i === 79) throw e;
  }
  await new Promise(resolve => setTimeout(resolve, 1000));
}
assert.equal((await fetch(base + '/api/state')).status, 401, 'Anonymous inventory API must deny access');
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    timezoneId: 'Asia/Seoul',
    locale: 'ko-KR',
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  page.on('dialog', dialog => dialog.accept());
  const issues = [];
  page.on('pageerror', e => issues.push(e.message));
  await page.goto(base, { waitUntil: 'networkidle' });
  await page.locator('#login-form [name=password]').fill('ci-only-strong-example-password-2026');
  await page.locator('#login-form button[type=submit]').click();
  await page.locator('#app:not(.hidden) #metrics').waitFor();
  assert.equal(await page.locator('#login').isVisible(), false, 'Login screen should be hidden');
  async function noPageOverflow(label) {
    const measures = await page.evaluate(() => ({
      width: window.innerWidth,
      body: document.body.scrollWidth,
      html: document.documentElement.scrollWidth,
    }));
    assert.ok(measures.html <= measures.width + 2, label + ': horizontal overflow: ' + JSON.stringify(measures));
  }

  await noPageOverflow('dashboard390');
  await page.screenshot({path: path.join(out, 'mobile-dashboard.png'), fullPage: true});

  await page.locator('[data-tab=clients]').click();
  await page.locator('[data-client-edit]').first().click();
  await page.locator('#client-form [name=person]').fill('CI 테스트담당');
  await page.locator('#client-form [name=phone]').fill('010-1111-2222');
  await page.locator('#client-form button[type=submit]').click();
  await page.locator('#client-list').getByText('CI 테스트담당').waitFor();
  await noPageOverflow('customer390');
  await page.screenshot({path: path.join(out, 'mobile-customers.png'), fullPage: true});

  await page.locator('[data-tab=stock]').click();
  await page.locator('#stock-qty').fill('20');
  await page.locator('#stock-form button[type=submit]').click();
  await page.locator('#stock-list').getByText('20개').first().waitFor();
  await noPageOverflow('stock390');

  await page.locator('[data-tab=order]').click();
  await page.locator('#order-items input[data-id="1"]').fill('2');
  await page.locator('#add-extra').click();
  await page.locator('[data-extra=name]').fill('기타 배송비');
  await page.locator('[data-extra=qty]').fill('1');
  await page.locator('[data-extra=price]').fill('1000');
  await page.locator('#vat').selectOption('tax');
  await page.locator('#order-total .grand').getByText('25,300원').waitFor();
  await noPageOverflow('order390');
  await page.screenshot({path: path.join(out, 'mobile-order.png'), fullPage: true});

  await page.locator('#order-form button[type=submit]').click();
  await page.locator('#bill-preview:not(.hidden)').waitFor();
  const billText = await page.locator('#bill-sheet').innerText();
  for (const word of ['잉어반죽','기타 배송비','23,000원','2,300원','25,300원']) {
    assert.ok(billText.includes(word), 'Invoice missing ' + word);
  }
  const response = await page.evaluate(async () => (await (await fetch('/api/state')).json()).products);
  assert.equal(response.find(p => p.name === '잉어반죽').stock, 18);

  await page.emulateMedia({media: 'print'});
  for (const mode of ['a4', '58', '80']) {
    await page.evaluate(m => {
      document.body.classList.remove('print-58','print-80');
      if (m !== 'a4') document.body.classList.add('print-' + m);
    }, mode);
    if (mode !== 'a4') {
      const width = await page.locator('#bill-sheet').evaluate(el => el.getBoundingClientRect().width);
      const max = mode === '58' ? 220 : 298;
      assert.ok(width > 0 && width <= max, mode + 'mm print width too large: ' + width);
    }
    const p = path.join(out, 'invoice-' + mode + '.pdf');
    const pdf = await page.pdf({path:p,printBackground:true,preferCSSPageSize:true});
    assert.equal(pdf.subarray(0,4).toString('utf8'),'%PDF');
    assert.ok(pdf.length > 1500, 'Empty PDF ' + mode);
  }

  await page.evaluate(() => document.body.classList.remove('print-58','print-80'));
  await page.emulateMedia({media:'screen'});
  await page.setViewportSize({width:1440,height:900});
  await page.locator('[data-tab=bills]').click();
  await noPageOverflow('bills1440');
  await page.screenshot({path:path.join(out,'desktop-invoice.png'),fullPage:true});
  assert.deepEqual(issues,[], 'JavaScript page errors');
  console.log('BROWSER_QA_PASS: Mobile390, Desktop1440, login, customer data, stock, VAT 10% excluded, custom line, invoice, print PDF A4/58/80');
} finally {
  await browser.close();
}
