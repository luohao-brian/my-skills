---
name: volc-search
description: 使用火山引擎融合信息搜索 API 进行联网搜索，只支持 VOLCENGINE_ACCESS_KEY / VOLCENGINE_SECRET_KEY AK/SK 鉴权，返回适合 AI 使用的网页或图片结果。当用户要求联网检索、确认最新信息、搜索新闻、查官网资料、限定站点搜索、获取权威来源，或需要有来源支撑的搜索结果时使用。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/volc-search
metadata: {"openclaw":{"skillKey":"volc-search","emoji":"🔍","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/volc-search","requires":{"anyBins":["python3","python"],"env":["VOLCENGINE_ACCESS_KEY","VOLCENGINE_SECRET_KEY"]},"install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# 火山引擎联网搜索

使用火山引擎融合信息搜索 API 执行联网搜索，返回适合 AI 处理的网页或图片结果。

## Required Reads

- Read [references/docs-index.md](references/docs-index.md) only when you need API parameters, response fields, errors, or official docs links.
- Read `scripts/web_search.py --help` only when exact flags are needed.

## Credential Boundary

This skill only supports AK/SK authentication:

- `VOLCENGINE_ACCESS_KEY`
- `VOLCENGINE_SECRET_KEY`

No other credential path is supported by this skill.

## Command

```bash
python3 {baseDir}/scripts/web_search.py "搜索词"
python3 {baseDir}/scripts/web_search.py "OpenAI 最新发布" --time-range OneWeek --count 10
python3 {baseDir}/scripts/web_search.py "故宫博物院" --type image --count 3
```

## Parameters

- `--type web|image`: defaults to `web`.
- `--count N`: `web` max is 50; `image` max is 5.
- `--time-range OneDay|OneWeek|OneMonth|OneYear|YYYY-MM-DD..YYYY-MM-DD`.
- `--sites "a.com|b.com"`: restrict search to sites.
- `--block-hosts "a.com|b.com"`: exclude sites.
- `--auth-level 1`: prefer authoritative sources.

## Answer Rules

1. Base answers on returned results; do not invent unsupported facts.
2. Preserve title, site name, URL, and publish time when present.
3. For time-sensitive questions, use `--time-range` and state the range in the answer.
4. For high-trust topics, prefer `--sites` or `--auth-level 1`.
5. If results do not support a clear conclusion, say the evidence is insufficient.
