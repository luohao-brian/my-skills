#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildGolden } from './build-swiss-golden.mjs';
import { extractCssClasses, extractRecipes, validateSwissHtml } from './validate-swiss-deck.mjs';

const SCRIPT = fileURLToPath(import.meta.url);
const ROOT = dirname(dirname(SCRIPT));

function sameSet(left, right) {
  return left.size === right.size && [...left].every((item) => right.has(item));
}

function runCli() {
  const contract = JSON.parse(readFileSync(join(ROOT, 'references/swiss-contract.json'), 'utf8'));
  const template = readFileSync(join(ROOT, contract.template), 'utf8');
  const layouts = readFileSync(join(ROOT, 'references/layouts-swiss.md'), 'utf8');
  const lock = readFileSync(join(ROOT, 'references/swiss-layout-lock.md'), 'utf8');
  const slidesSource = readFileSync(join(ROOT, contract.goldenSlides), 'utf8');
  const cssClasses = extractCssClasses(template);
  const templateRecipes = extractRecipes(template);
  const contractRecipes = new Set(Object.values(contract.layouts).flatMap((layout) => layout.recipes));
  const errors = [];

  if (!sameSet(templateRecipes, contractRecipes)) {
    errors.push(`RECIPES mismatch. Template-only: ${[...templateRecipes].filter((item) => !contractRecipes.has(item)).join(', ') || 'none'}; contract-only: ${[...contractRecipes].filter((item) => !templateRecipes.has(item)).join(', ') || 'none'}.`);
  }
  for (const [id, layout] of Object.entries(contract.layouts)) {
    for (const className of layout.requiredClasses ?? []) {
      if (!cssClasses.has(className)) errors.push(`${id}: required class ${className} is missing from template CSS.`);
    }
  }

  const stableIds = Object.keys(contract.layouts).filter((id) => /^S\d{2}$/.test(id));
  for (const id of stableIds) {
    const count = [...slidesSource.matchAll(new RegExp(`data-layout=["']${id}["']`, 'g'))].length;
    if (count !== 1) errors.push(`${id}: golden slide source must contain exactly one page, found ${count}.`);
  }
  const unexpected = [...slidesSource.matchAll(/data-layout=["']([^"']+)["']/g)]
    .map((match) => match[1]).filter((id) => !stableIds.includes(id));
  if (unexpected.length) errors.push(`Golden slide source contains unexpected layouts: ${unexpected.join(', ')}.`);

  for (const [name, source] of [['layouts-swiss.md', layouts], ['swiss-layout-lock.md', lock]]) {
    if (/\/Users\/[A-Za-z0-9._-]+\//.test(source)) errors.push(`${name}: contains a machine-local absolute path.`);
  }
  for (const match of layouts.matchAll(/data-animate=["']([^"']+)["']/g)) {
    if (!templateRecipes.has(match[1])) errors.push(`layouts-swiss.md uses unknown data-animate recipe ${match[1]}.`);
  }

  const { outputPath, html } = buildGolden();
  const current = readFileSync(outputPath, 'utf8');
  if (current !== html) errors.push(`${contract.goldenDeck} is stale; rebuild it.`);
  const validation = validateSwissHtml({ html, filePath: outputPath, checkRuntime: true });
  errors.push(...validation.errors.map((error) => `golden: ${error}`));

  const negativeCases = [
    {
      name: 'unknown recipe',
      html: html.replace('data-animate="hero"', 'data-animate="tower-grow"'),
      expected: 'not defined by template RECIPES',
    },
    {
      name: 'undefined class',
      html: html.replace('class="canvas-card"', 'class="canvas-card-typo"'),
      expected: 'undefined CSS class(es)',
    },
    {
      name: 'truncated runtime',
      html: html.slice(0, html.indexOf('<div id="nav"></div>')),
      expected: 'Runtime is incomplete',
    },
  ];
  for (const testCase of negativeCases) {
    const result = validateSwissHtml({ html: testCase.html, checkRuntime: true });
    if (!result.errors.some((error) => error.includes(testCase.expected))) {
      errors.push(`Negative validator test did not catch ${testCase.name}.`);
    }
  }

  if (errors.length) {
    console.error('Swiss contract verification failed:');
    errors.forEach((error) => console.error(`- ${error}`));
    process.exit(1);
  }
  console.log(`Swiss contract verified: ${stableIds.length} layouts, ${templateRecipes.size} recipes, ${cssClasses.size} CSS classes.`);
}

if (process.argv[1] && resolve(process.argv[1]) === SCRIPT) runCli();
