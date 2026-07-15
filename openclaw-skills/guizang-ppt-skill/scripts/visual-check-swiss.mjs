#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync } from 'node:fs';
import { basename, dirname, join, resolve } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const SCRIPT = fileURLToPath(import.meta.url);

function parseArgs(argv) {
  const positional = argv.find((arg) => !arg.startsWith('--'));
  const value = (name) => {
    const index = argv.indexOf(name);
    return index >= 0 ? argv[index + 1] : undefined;
  };
  return { file: positional, output: value('--output'), baseline: value('--baseline') };
}

function digest(file) {
  return createHash('sha256').update(readFileSync(file)).digest('hex');
}

async function runCli() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.file) {
    console.error('Usage: node scripts/visual-check-swiss.mjs <index.html> [--output <dir>] [--baseline <dir>]');
    process.exit(2);
  }
  const file = resolve(args.file);
  const output = resolve(args.output ?? join(dirname(file), 'visual-check'));
  mkdirSync(output, { recursive: true });

  const moduleName = process.env.PLAYWRIGHT_MODULE || 'playwright';
  let chromium;
  try {
    ({ chromium } = await import(moduleName));
  } catch (error) {
    console.error(`Playwright is unavailable. Install playwright or set PLAYWRIGHT_MODULE to its index.mjs path. ${error.message}`);
    process.exit(2);
  }

  const launch = { headless: true };
  if (process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE) launch.executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE;
  const browser = await chromium.launch(launch);
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  await page.goto(pathToFileURL(file).href, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1000);
  await page.evaluate(() => window.__setLowPowerMode?.(true, { persist: false }));
  const total = await page.locator('section.slide').count();
  const failures = [];

  for (let index = 0; index < total; index += 1) {
    await page.evaluate((slideIndex) => {
      const deck = document.querySelector('#deck');
      deck.style.transition = 'none';
      deck.style.transform = `translateX(${-slideIndex * 100}vw)`;
      window.__currentSlideIndex = slideIndex;
      window.__playSlide?.(slideIndex);
    }, index);
    await page.waitForTimeout(100);
    const problems = await page.evaluate((slideIndex) => {
      const slide = document.querySelectorAll('section.slide')[slideIndex];
      const slideRect = slide.getBoundingClientRect();
      const selectors = 'h1,h2,h3,h4,h5,h6,p,li,figcaption,img,.ledger-row,.brief-card,.bar-tower';
      return [...slide.querySelectorAll(selectors)].flatMap((element) => {
        const style = getComputedStyle(element);
        if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) return [];
        const rect = element.getBoundingClientRect();
        const issues = [];
        if (rect.left < slideRect.left - 1 || rect.right > slideRect.right + 1) issues.push('horizontal overflow');
        if (rect.top < slideRect.top - 1 || rect.bottom > slideRect.bottom + 1) issues.push('viewport overflow');
        if (rect.bottom > slideRect.top + slideRect.height * .94 && element.matches('p,li,figcaption,h1,h2,h3,h4,h5,h6')) issues.push('enters bottom navigation zone');
        return issues.map((issue) => `${element.tagName.toLowerCase()}.${element.className || '-'}: ${issue}`);
      });
    }, index);
    if (problems.length) failures.push(`Slide ${index + 1}: ${problems.join('; ')}`);
    const screenshot = join(output, `slide-${String(index + 1).padStart(2, '0')}.png`);
    await page.screenshot({ path: screenshot });
    if (args.baseline) {
      const expected = join(resolve(args.baseline), basename(screenshot));
      try {
        if (digest(screenshot) !== digest(expected)) failures.push(`Slide ${index + 1}: screenshot differs from ${expected}.`);
      } catch {
        failures.push(`Slide ${index + 1}: baseline is missing: ${expected}.`);
      }
    }
  }

  await browser.close();
  if (pageErrors.length) failures.push(...pageErrors.map((error) => `Browser error: ${error}`));
  if (failures.length) {
    console.error('Swiss visual check failed:');
    failures.forEach((failure) => console.error(`- ${failure}`));
    process.exit(1);
  }
  console.log(`Swiss visual check passed: ${total} slide(s), screenshots in ${output}.`);
}

if (process.argv[1] && resolve(process.argv[1]) === SCRIPT) runCli();
