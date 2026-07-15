#!/usr/bin/env node
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { assembleDeck } from './create-deck.mjs';

const SCRIPT = fileURLToPath(import.meta.url);
const ROOT = dirname(dirname(SCRIPT));

export function buildGolden() {
  const contract = JSON.parse(readFileSync(join(ROOT, 'references/swiss-contract.json'), 'utf8'));
  const template = readFileSync(join(ROOT, contract.template), 'utf8');
  const slides = readFileSync(join(ROOT, contract.goldenSlides), 'utf8');
  return {
    outputPath: join(ROOT, contract.goldenDeck),
    html: assembleDeck({ style: 'swiss', title: 'Swiss Golden · 22 Layouts', slides, template }),
  };
}

function runCli() {
  const check = process.argv.includes('--check');
  const { outputPath, html } = buildGolden();
  if (check) {
    const current = readFileSync(outputPath, 'utf8');
    if (current !== html) {
      console.error(`${outputPath} is stale. Run node scripts/build-swiss-golden.mjs.`);
      process.exit(1);
    }
    console.log(`Golden deck is current: ${outputPath}`);
    return;
  }
  writeFileSync(outputPath, html);
  console.log(outputPath);
}

if (process.argv[1] && resolve(process.argv[1]) === SCRIPT) runCli();
