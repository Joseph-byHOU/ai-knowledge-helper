import { chromium } from 'playwright';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

(async () => {
  const htmlPath = path.resolve(__dirname, 'src', 'renderer', 'index.html');
  const fileUrl = 'file://' + htmlPath.replace(/\\/g, '/');

  console.log('Loading:', fileUrl);

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  await page.goto(fileUrl, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1500);

  const screenshotPath = path.resolve(__dirname, 'screenshot.png');
  await page.screenshot({ path: screenshotPath, fullPage: false });

  console.log('✅ Screenshot saved to:', screenshotPath);
  await browser.close();
})();
