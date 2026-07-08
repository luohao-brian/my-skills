---
name: ark-search
description: 使用 Ark Agent Plan 搜索 API 检索网页和图片，适合查询最新信息、新闻动态、官网资料、限定站点内容，并整理带来源的搜索结果。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-search
metadata: {"openclaw":{"skillKey":"ark-search","emoji":"🔎","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-search","requires":{"anyBins":["python3","python"],"env":["ARK_AGENT_PLAN_API_KEY"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Ark Agent Plan Search

使用 Ark Agent Plan 搜索 API 执行联网搜索，返回适合 AI 处理的网页或图片结果。

## Required Reads

- Read [references/docs-index.md](references/docs-index.md) only when you need API parameters, response fields, errors, or official docs links.
- Read `scripts/web_search.py --help` only when exact flags are needed.

## Credential Boundary

This skill only supports Agent Plan API key authentication:

- `ARK_AGENT_PLAN_API_KEY`

No AK/SK credential path is supported by this skill.

## Command

```bash
python3 {baseDir}/scripts/web_search.py "搜索词"
python3 {baseDir}/scripts/web_search.py "OpenAI 最新发布" --time-range OneWeek --count 10
python3 {baseDir}/scripts/web_search.py "北京旅游攻略" --need-content --need-url
python3 {baseDir}/scripts/web_search.py "故宫博物院" --type image --count 3
```

## Parameters

- `--type web|image`: defaults to `web`.
- `--count N`: defaults to `10` for `web` and `5` for `image`; `web` max is 50; `image` max is 5.
- `--time-range OneDay|OneWeek|OneMonth|OneYear|YYYY-MM-DD..YYYY-MM-DD`: web only.
- `--sites "a.com|b.com"`: restrict search to sites.
- `--block-hosts "a.com|b.com"`: exclude sites.
- `--auth-level 1`: prefer authoritative sources.
- `--need-content`: only return web results with `Content`.
- `--need-url`: only return web results with original `Url`.
- `--query-rewrite`: enable provider query rewrite.
- `--no-summary`: do not request `Summary` for web results.

## Invocation Contract

1. Use `--type web` for text evidence and `--type image` only for image result lists.
2. Use `--time-range` when the caller specifies a recency window or date range.
3. Use `--sites` or `--auth-level 1` when the caller requires specific or authoritative sources.

## Result Handling

1. Treat stdout as the search result list.
2. When passing web evidence forward, keep title, site name, URL, publish time, and summary/snippet when present.
3. When passing image results forward, keep image URL, dimensions, source page URL, title, and site name when present.
4. Treat empty or weak results as a completed skill call with insufficient evidence, not as permission to invent missing facts.
