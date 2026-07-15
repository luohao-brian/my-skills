#!/usr/bin/env node
import { existsSync, readFileSync } from 'node:fs';
import { dirname, isAbsolute, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const SCRIPT = fileURLToPath(import.meta.url);
const ROOT = dirname(dirname(SCRIPT));

function loadContract() {
  return JSON.parse(readFileSync(join(ROOT, 'references/swiss-contract.json'), 'utf8'));
}

export function extractCssClasses(source) {
  const classes = new Set();
  for (const style of source.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/gi)) {
    for (const match of style[1].matchAll(/\.([_a-zA-Z][\w-]*)/g)) classes.add(match[1]);
  }
  return classes;
}

export function extractRecipes(source) {
  const body = source.match(/const\s+RECIPES\s*=\s*\{([\s\S]*?)\n\s*\};/)?.[1] ?? '';
  return new Set([...body.matchAll(/["']([^"']+)["']\s*:/g)].map((match) => match[1]));
}

function parseSlides(source) {
  const clean = source.replace(/<!--[\s\S]*?-->/g, '');
  return [...clean.matchAll(/<section\b[^>]*>[\s\S]*?<\/section>/gi)]
    .map((match, index) => {
      const html = match[0];
      const tag = html.match(/^<section\b[^>]*>/i)?.[0] ?? '';
      const classes = tag.match(/\bclass=["']([^"']*)["']/i)?.[1].split(/\s+/).filter(Boolean) ?? [];
      return { index: index + 1, html, tag, classes };
    })
    .filter((slide) => slide.classes.includes('slide'));
}

function attr(tag, name) {
  return tag.match(new RegExp(`\\b${name}=["']([^"']+)["']`, 'i'))?.[1];
}

function classTokens(source) {
  const tokens = [];
  for (const match of source.matchAll(/\bclass=["']([^"']+)["']/gi)) {
    tokens.push(...match[1].split(/\s+/).filter(Boolean));
  }
  return tokens;
}

function hasClass(source, name) {
  return classTokens(source).includes(name);
}

function containsCjk(source) {
  return /[\u3400-\u9fff\uf900-\ufaff]/u.test(source.replace(/<[^>]+>/g, ''));
}

export function validateSwissHtml({ html, filePath = '', allowExperimental = false, checkRuntime = true }) {
  const contract = loadContract();
  const templatePath = join(ROOT, contract.template);
  const template = readFileSync(templatePath, 'utf8');
  const cssClasses = extractCssClasses(`${template}\n${html}`);
  const recipes = extractRecipes(template);
  const runtimeClasses = new Set(contract.runtimeClasses ?? []);
  const errors = [];
  const warnings = [];

  if (checkRuntime) {
    for (const marker of [contract.slideRegion.start, contract.slideRegion.end, ...contract.requiredRuntimeMarkers]) {
      if (!html.includes(marker)) errors.push(`Runtime is incomplete: missing marker ${JSON.stringify(marker)}.`);
    }
  }

  const slides = parseSlides(html);
  if (!slides.length) errors.push('No <section class="slide"> pages found.');

  slides.forEach((slide) => {
    const label = `Slide ${slide.index}`;
    const layout = attr(slide.tag, 'data-layout');
    const recipe = attr(slide.tag, 'data-animate');
    const stable = layout ? contract.layouts[layout] : undefined;
    const experimental = layout ? contract.experimentalLayouts[layout] : undefined;

    if (!layout) {
      errors.push(`${label}: missing data-layout.`);
    } else if (!stable && !experimental) {
      errors.push(`${label}: data-layout="${layout}" is not registered in swiss-contract.json.`);
    } else if (experimental && !allowExperimental) {
      errors.push(`${label}: data-layout="${layout}" is experimental; pass --allow-experimental only with explicit user approval.`);
    }

    if (!recipe) {
      errors.push(`${label}: missing data-animate.`);
    } else if (!recipes.has(recipe)) {
      errors.push(`${label}: data-animate="${recipe}" is not defined by template RECIPES.`);
    }

    const layoutContract = stable ?? experimental;
    if (layoutContract && recipe && !layoutContract.recipes.includes(recipe)) {
      errors.push(`${label}: ${layout} must use ${layoutContract.recipes.join(' or ')}, found ${recipe}.`);
    }
    for (const required of layoutContract?.requiredClasses ?? []) {
      if (!hasClass(slide.html, required)) errors.push(`${label}: ${layout} requires class "${required}".`);
    }

    const unknownClasses = [...new Set(classTokens(slide.html).filter((name) =>
      !cssClasses.has(name) && !runtimeClasses.has(name) && !name.startsWith('lucide-') && !name.startsWith('maplibregl-')
    ))].sort();
    if (unknownClasses.length) errors.push(`${label}: undefined CSS class(es): ${unknownClasses.join(', ')}.`);

    const isStatement = ['S01', 'S03', 'S09', 'S10', 'SWISS-COVER-ASCII', 'SWISS-CLOSING-ASCII'].includes(layout);
    const topChunk = slide.html.slice(0, 2200);
    if (!isStatement && /text-align\s*:\s*center/i.test(topChunk) && /<h[12]\b/i.test(topChunk)) {
      errors.push(`${label}: top heading is centered; Swiss body titles must stay on the left-top axis.`);
    }
    if (!isStatement && /align-self\s*:\s*center/i.test(topChunk) && /<h[12]\b/i.test(topChunk)) {
      errors.push(`${label}: top heading appears vertically centered.`);
    }

    if (/<svg\b[\s\S]*?<text\b/i.test(slide.html)) {
      errors.push(`${label}: SVG contains visible <text>; use HTML labels and keep SVG geometric.`);
    }
    if (/style=["'][^"']*(?:box-shadow\s*:|linear-gradient\s*\(|border-radius\s*:\s*(?!0(?:[;\s"']|px)))/i.test(slide.html)) {
      errors.push(`${label}: inline style uses a shadow, gradient, or non-zero radius.`);
    }

    for (const match of slide.html.matchAll(/<img\b[^>]*>/gi)) {
      const tag = match[0];
      const src = attr(tag, 'src') ?? '';
      const slot = attr(tag, 'data-image-slot');
      if (src.startsWith('images/') && !slot) errors.push(`${label}: local image ${src} is missing data-image-slot.`);
      if (src.startsWith('images/') && filePath) {
        const imagePath = resolve(dirname(filePath), src);
        if (!existsSync(imagePath)) errors.push(`${label}: local image does not exist: ${imagePath}.`);
      }
    }

    if (layout === 'S22') {
      if (!/data-image-slot=["']s22-hero-21x9["']/.test(slide.html)) {
        errors.push(`${label}: S22 must use data-image-slot="s22-hero-21x9".`);
      }
      if (/object-position\s*:\s*top center/i.test(slide.html)) {
        errors.push(`${label}: S22 uses object-position:top center; use center 35% or center center.`);
      }
    }

    for (const match of slide.html.matchAll(/<[^>]*class=["'][^"']*\bt-meta\b[^"']*["'][^>]*>([\s\S]*?)<\/[^>]+>/gi)) {
      if (containsCjk(match[1])) errors.push(`${label}: .t-meta contains CJK text; use sans/sans-zh instead of mono meta.`);
    }
    const hasLowBottom = [...slide.html.matchAll(/style=["']([^"']*)["']/gi)]
      .some((match) => /(?:^|;)\s*bottom\s*:\s*[0-7](?:\.\d+)?vh/i.test(match[1]));
    if (hasLowBottom && /<(?:p|h[1-6]|figcaption|span)\b/i.test(slide.html)) {
      warnings.push(`${label}: positioned text may enter the bottom 8vh navigation safety zone.`);
    }
  });

  return { slides: slides.length, errors, warnings };
}

export function validateSwissDeck(filePath, options = {}) {
  const absolute = isAbsolute(filePath) ? filePath : resolve(filePath);
  return validateSwissHtml({
    html: readFileSync(absolute, 'utf8'),
    filePath: absolute,
    allowExperimental: options.allowExperimental,
    checkRuntime: options.checkRuntime ?? true,
  });
}

function runCli() {
  const args = process.argv.slice(2);
  const file = args.find((arg) => !arg.startsWith('-'));
  const allowExperimental = args.includes('--allow-experimental');
  if (!file) {
    console.error('Usage: node scripts/validate-swiss-deck.mjs <index.html> [--allow-experimental]');
    process.exit(2);
  }
  const result = validateSwissDeck(file, { allowExperimental });
  if (result.warnings.length) {
    console.warn('Warnings:');
    result.warnings.forEach((warning) => console.warn(`- ${warning}`));
  }
  if (result.errors.length) {
    console.error('Swiss deck validation failed:');
    result.errors.forEach((error) => console.error(`- ${error}`));
    process.exit(1);
  }
  console.log(`Swiss deck validation passed: ${result.slides} slide(s).`);
}

if (process.argv[1] && resolve(process.argv[1]) === SCRIPT) runCli();
