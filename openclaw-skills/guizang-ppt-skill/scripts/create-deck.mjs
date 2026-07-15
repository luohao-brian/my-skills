#!/usr/bin/env node
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateSwissHtml } from './validate-swiss-deck.mjs';

const SCRIPT = fileURLToPath(import.meta.url);
const ROOT = dirname(dirname(SCRIPT));

function escapeHtml(value) {
  return value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
}

function parseArgs(argv) {
  const out = {};
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    if (!key.startsWith('--')) continue;
    out[key.slice(2)] = argv[index + 1];
    index += 1;
  }
  return out;
}

export function assembleDeck({ style, title, slides, template }) {
  const start = '<!-- SLIDES_START -->';
  const end = '<!-- SLIDES_END -->';
  const startIndex = template.indexOf(start);
  const endIndex = template.indexOf(end);
  if (startIndex < 0 || endIndex < 0 || endIndex <= startIndex) {
    throw new Error(`Template is missing ordered ${start}/${end} markers.`);
  }
  if (!/<section\b[^>]*class=["'][^"']*\bslide\b/i.test(slides)) {
    throw new Error('Slides input must contain at least one <section class="slide"> block.');
  }
  const assembled = `${template.slice(0, startIndex + start.length)}\n${slides.trim()}\n${template.slice(endIndex)}`
    .replace(/<title>[\s\S]*?<\/title>/i, `<title>${escapeHtml(title)}</title>`);
  if (style === 'swiss') {
    const result = validateSwissHtml({ html: assembled, checkRuntime: true });
    if (result.errors.length) throw new Error(`Swiss validation failed:\n- ${result.errors.join('\n- ')}`);
  }
  return assembled;
}

export function createDeck({ style, title, slidesPath, outputPath }) {
  const templateName = style === 'swiss' ? 'template-swiss.html' : style === 'magazine' ? 'template.html' : '';
  if (!templateName) throw new Error('--style must be swiss or magazine.');
  const template = readFileSync(join(ROOT, 'assets', templateName), 'utf8');
  const slides = readFileSync(resolve(slidesPath), 'utf8');
  const output = assembleDeck({ style, title, slides, template });
  const absoluteOutput = resolve(outputPath);
  mkdirSync(dirname(absoluteOutput), { recursive: true });
  writeFileSync(absoluteOutput, output);
  return absoluteOutput;
}

function runCli() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.style || !args.title || !args.slides || !args.output) {
    console.error('Usage: node scripts/create-deck.mjs --style <swiss|magazine> --title <title> --slides <slides.html> --output <index.html>');
    process.exit(2);
  }
  try {
    const output = createDeck({ style: args.style, title: args.title, slidesPath: args.slides, outputPath: args.output });
    console.log(output);
  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }
}

if (process.argv[1] && resolve(process.argv[1]) === SCRIPT) runCli();
