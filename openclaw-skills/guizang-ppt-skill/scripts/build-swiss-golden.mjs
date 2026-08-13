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
  const notes = [...slides.matchAll(/<section\b[^>]*\bdata-layout=["']([^"']+)["'][^>]*\bdata-slide-id=["']([^"']+)["'][^>]*>/gi)]
    .map((match) => ({
      id: match[2],
      title: `${match[1]} 版式示例`,
      section: 'Swiss Golden',
      purpose: `验证 ${match[1]} 的结构、动效与演讲者模式兼容性`,
      talk: ['说明这一页承载的内容形状', '检查标题、信息层级和底部安全区', '确认动效终态与预览比例正确'],
      transition: '进入下一个登记版式继续检查',
    }));
  return {
    outputPath: join(ROOT, contract.goldenDeck),
    html: assembleDeck({ style: 'swiss', title: 'Swiss Golden · 22 Layouts', slides, notes, template }),
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
