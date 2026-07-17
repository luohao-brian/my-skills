#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { basename, dirname, join, resolve } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const SCRIPT = fileURLToPath(import.meta.url);
const DEFAULT_VIEWPORTS = [[1600, 900], [1280, 720], [1024, 768], [720, 1280]];

function parseArgs(argv) {
  const positional = argv.find((arg) => !arg.startsWith('--'));
  const value = (name) => {
    const index = argv.indexOf(name);
    return index >= 0 ? argv[index + 1] : undefined;
  };
  return {
    file: positional,
    output: value('--output'),
    baseline: value('--baseline'),
    viewports: value('--viewports'),
  };
}

function parseViewports(raw) {
  if (!raw) return DEFAULT_VIEWPORTS;
  return raw.split(',').map((token) => {
    const match = token.trim().match(/^(\d+)x(\d+)$/i);
    if (!match) throw new Error(`Invalid viewport "${token}"; expected WIDTHxHEIGHT.`);
    const viewport = [Number(match[1]), Number(match[2])];
    if (viewport[0] < 320 || viewport[1] < 320) throw new Error(`Viewport is too small: ${token}.`);
    return viewport;
  });
}

function digest(file) {
  return createHash('sha256').update(readFileSync(file)).digest('hex');
}

function ancestorModules(start) {
  const candidates = [];
  let directory = resolve(start);
  while (true) {
    candidates.push(join(directory, 'node_modules', 'playwright', 'index.mjs'));
    const parent = dirname(directory);
    if (parent === directory) return candidates;
    directory = parent;
  }
}

function findCachedPlaywright() {
  const roots = [process.env.XDG_CACHE_HOME, join(homedir(), '.cache'), join(homedir(), 'Library', 'Caches')]
    .filter((value, index, values) => value && values.indexOf(value) === index && existsSync(value));
  for (const root of roots) {
    try {
      const found = execFileSync('find', [root, '-path', '*/node_modules/playwright/index.mjs', '-print', '-quit'], {
        encoding: 'utf8',
        timeout: 5000,
      }).trim();
      if (found) return found;
    } catch {
      // Try the next cache root.
    }
  }
  return undefined;
}

async function loadChromium() {
  const candidates = [];
  if (process.env.PLAYWRIGHT_MODULE) candidates.push(process.env.PLAYWRIGHT_MODULE);
  candidates.push('playwright');
  candidates.push(...ancestorModules(process.cwd()), ...ancestorModules(dirname(SCRIPT)), ...ancestorModules(dirname(process.execPath)));
  try {
    const globalRoot = execFileSync('npm', ['root', '-g'], { encoding: 'utf8', timeout: 3000 }).trim();
    if (globalRoot) candidates.push(join(globalRoot, 'playwright', 'index.mjs'));
  } catch {
    // Global npm packages are optional.
  }

  const errors = [];
  for (const candidate of [...new Set(candidates)]) {
    if (candidate !== 'playwright' && !existsSync(candidate)) continue;
    try {
      const moduleName = candidate === 'playwright' ? candidate : pathToFileURL(candidate).href;
      const { chromium } = await import(moduleName);
      if (chromium) return { chromium, source: candidate };
    } catch (error) {
      errors.push(`${candidate}: ${error.message}`);
    }
  }

  const cached = findCachedPlaywright();
  if (cached) {
    try {
      const { chromium } = await import(pathToFileURL(cached).href);
      if (chromium) return { chromium, source: cached };
    } catch (error) {
      errors.push(`${cached}: ${error.message}`);
    }
  }
  throw new Error(`Playwright module not found.${errors.length ? ` ${errors.join(' | ')}` : ''}`);
}

async function launchBrowser(chromium) {
  const attempts = [];
  const choices = [];
  if (process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE) {
    choices.push({ label: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE, executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE });
  }
  choices.push({ label: 'Playwright Chromium' }, { label: 'Chrome channel', channel: 'chrome' }, { label: 'Edge channel', channel: 'msedge' });
  for (const executablePath of [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
  ]) {
    if (existsSync(executablePath)) choices.push({ label: executablePath, executablePath });
  }

  for (const choice of choices) {
    try {
      const { label, ...launch } = choice;
      const browser = await chromium.launch({ headless: true, ...launch });
      return { browser, source: label };
    } catch (error) {
      attempts.push(`${choice.label}: ${error.message}`);
    }
  }
  throw new Error(`Browser not found. ${attempts.join(' | ')}`);
}

async function runCli() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.file) {
    console.error('Usage: node scripts/visual-check-swiss.mjs <index.html> [--output <dir>] [--baseline <dir>] [--viewports 1600x900,1280x720,1024x768,720x1280]');
    process.exit(2);
  }
  let viewports;
  try {
    viewports = parseViewports(args.viewports);
  } catch (error) {
    console.error(error.message);
    process.exit(2);
  }
  const file = resolve(args.file);
  const output = resolve(args.output ?? join(dirname(file), 'visual-check'));
  mkdirSync(output, { recursive: true });

  let chromium;
  let playwrightSource;
  try {
    ({ chromium, source: playwrightSource } = await loadChromium());
  } catch (error) {
    console.error(error.message);
    process.exit(2);
  }

  let browser;
  let browserSource;
  try {
    ({ browser, source: browserSource } = await launchBrowser(chromium));
  } catch (error) {
    console.error(error.message);
    process.exit(2);
  }
  console.log(`Playwright: ${playwrightSource}`);
  console.log(`Browser: ${browserSource}`);
  const failures = [];
  const warnings = [];
  let total = 0;

  for (const [width, height] of viewports) {
    const viewportName = `${width}x${height}`;
    const viewportOutput = join(output, viewportName);
    mkdirSync(viewportOutput, { recursive: true });
    const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
    const pageErrors = [];
    page.on('pageerror', (error) => pageErrors.push(error.message));
    await page.goto(pathToFileURL(file).href, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);
    await page.evaluate(() => window.__setLowPowerMode?.(true, { persist: false }));
    const viewportTotal = await page.locator('section.slide').count();
    if (!total) total = viewportTotal;
    if (viewportTotal !== total) failures.push(`${viewportName}: slide count changed from ${total} to ${viewportTotal}.`);

    for (let index = 0; index < viewportTotal; index += 1) {
      await page.evaluate((slideIndex) => {
        const deck = document.querySelector('#deck');
        deck.style.transition = 'none';
        deck.style.transform = `translateX(${-slideIndex * 100}vw)`;
        window.__currentSlideIndex = slideIndex;
        window.__playSlide?.(slideIndex);
      }, index);
      await page.waitForTimeout(150);
      const audit = await page.evaluate((slideIndex) => {
        const slide = document.querySelectorAll('section.slide')[slideIndex];
        const slideRect = slide.getBoundingClientRect();
        const errors = [];
        const warnings = [];
        const selector = (element) => {
          const classes = typeof element.className === 'string' ? element.className.trim().split(/\s+/).slice(0, 2) : [];
          return `${element.tagName.toLowerCase()}${classes.length ? `.${classes.join('.')}` : ''}`;
        };
        const rect = (element) => element.getBoundingClientRect();
        const visible = (element) => {
          const style = getComputedStyle(element);
          const box = rect(element);
          return style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) > .001 && box.width > 1 && box.height > 1;
        };
        const contains = (outer, inner, tolerance = 1.5) =>
          inner.left >= outer.left - tolerance && inner.top >= outer.top - tolerance &&
          inner.right <= outer.right + tolerance && inner.bottom <= outer.bottom + tolerance;
        const intersection = (a, b) => {
          const width = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left));
          const height = Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
          return { width, height, area: width * height };
        };
        const inspected = [...slide.querySelectorAll('h1,h2,h3,h4,h5,h6,p,li,blockquote,figcaption,img,video,canvas,svg,.ledger-row,.brief-card,.bar-tower,[data-image-slot]')].filter(visible);

        if (document.documentElement.scrollWidth > innerWidth + 1 || document.documentElement.scrollHeight > innerHeight + 1) {
          errors.push(`document exceeds viewport: ${document.documentElement.scrollWidth}x${document.documentElement.scrollHeight}`);
        }
        for (const element of inspected) {
          const box = rect(element);
          if (!contains(slideRect, box)) errors.push(`${selector(element)} exceeds slide/viewport bounds`);
          if (box.bottom > slideRect.top + slideRect.height * .94 && element.matches('h1,h2,h3,h4,h5,h6,p,li,blockquote,figcaption')) {
            errors.push(`${selector(element)} enters bottom navigation zone`);
          }
        }

        const containers = [...slide.querySelectorAll('.canvas-card,.brief-card,.ledger-row,figure,[class*="card"],[class*="panel"]')].filter(visible);
        for (const container of containers) {
          const outer = rect(container);
          for (const child of [...container.children].filter(visible)) {
            if (!contains(outer, rect(child), 2)) {
              errors.push(`${selector(child)} exceeds container ${selector(container)}`);
            }
          }
        }

        const overlapCandidates = inspected.filter((element) => element.matches('h1,h2,h3,h4,h5,h6,p,li,blockquote,figcaption,img,[data-image-slot]'));
        for (let left = 0; left < overlapCandidates.length; left += 1) {
          for (let right = left + 1; right < overlapCandidates.length; right += 1) {
            const a = overlapCandidates[left];
            const b = overlapCandidates[right];
            if (a.contains(b) || b.contains(a)) continue;
            const image = a.matches('img,[data-image-slot]') ? a : b.matches('img,[data-image-slot]') ? b : null;
            const overlay = image === a ? b : image === b ? a : null;
            const overlayRoot = image?.parentElement;
            if (image && overlay && overlayRoot?.contains(overlay) && getComputedStyle(image).position === 'absolute') continue;
            const aRect = rect(a);
            const bRect = rect(b);
            const hit = intersection(aRect, bRect);
            if (hit.width < 3 || hit.height < 3) continue;
            const ratio = hit.area / Math.max(1, Math.min(aRect.width * aRect.height, bRect.width * bRect.height));
            if (ratio < .08) continue;
            const bothText = a.matches('h1,h2,h3,h4,h5,h6,p,li,blockquote,figcaption') && b.matches('h1,h2,h3,h4,h5,h6,p,li,blockquote,figcaption');
            const message = `${selector(a)} overlaps ${selector(b)} (${Math.round(ratio * 100)}%)`;
            (bothText ? errors : warnings).push(message);
          }
        }

        const content = inspected.filter((element) => !element.closest('.chrome,.chrome-min,.foot,.nav,.progress-wrap'));
        if (content.length) {
          const boxes = content.map(rect);
          const bounds = {
            left: Math.min(...boxes.map((box) => box.left)),
            top: Math.min(...boxes.map((box) => box.top)),
            right: Math.max(...boxes.map((box) => box.right)),
            bottom: Math.max(...boxes.map((box) => box.bottom)),
          };
          const widthUse = (bounds.right - bounds.left) / slideRect.width;
          const heightUse = (bounds.bottom - bounds.top) / slideRect.height;
          if (widthUse < .55 && heightUse < .45) {
            warnings.push(`content uses only ${Math.round(widthUse * 100)}% width × ${Math.round(heightUse * 100)}% height`);
          }
        }
        return { errors: [...new Set(errors)], warnings: [...new Set(warnings)] };
      }, index);
      const label = `${viewportName} slide ${index + 1}`;
      failures.push(...audit.errors.map((problem) => `${label}: ${problem}`));
      warnings.push(...audit.warnings.map((problem) => `${label}: ${problem}`));
      const screenshot = join(viewportOutput, `slide-${String(index + 1).padStart(2, '0')}.png`);
      await page.screenshot({ path: screenshot });
      if (args.baseline) {
        const expected = join(resolve(args.baseline), viewportName, basename(screenshot));
        try {
          if (digest(screenshot) !== digest(expected)) failures.push(`${label}: screenshot differs from ${expected}.`);
        } catch {
          failures.push(`${label}: baseline is missing: ${expected}.`);
        }
      }
    }
    failures.push(...pageErrors.map((error) => `${viewportName} browser error: ${error}`));
    await page.close();
  }

  await browser.close();
  if (warnings.length) {
    console.warn('Swiss visual check warnings:');
    warnings.forEach((warning) => console.warn(`- ${warning}`));
  }
  if (failures.length) {
    console.error('Swiss visual check failed:');
    failures.forEach((failure) => console.error(`- ${failure}`));
    process.exit(1);
  }
  console.log(`Swiss visual check passed: ${total} slide(s) × ${viewports.length} viewport(s), ${warnings.length} warning(s), screenshots in ${output}.`);
}

if (process.argv[1] && resolve(process.argv[1]) === SCRIPT) runCli();
