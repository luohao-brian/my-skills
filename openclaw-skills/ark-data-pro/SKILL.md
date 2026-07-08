---
name: ark-data-pro
description: 使用 Ark Agent Plan 专业数据集后端 API 查询金融、企业工商、企业风险和学术数据，适合需要结构化专业实体数据、财务指标、工商档案、风险事件或论文检索结果时使用。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-data-pro
metadata: {"openclaw":{"skillKey":"ark-data-pro","emoji":"📊","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-data-pro","requires":{"anyBins":["python3","python"],"env":["ARK_AGENT_PLAN_API_KEY"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Ark Agent Plan DataPro

使用 Ark Agent Plan 专业数据集后端 HTTP endpoint 查询金融、企业工商、企业风险和学术数据。

## Required Reads

- Read [references/docs-index.md](references/docs-index.md) only when you need API parameters, response fields, supported dataset boundaries, errors, or official docs links.
- Read `scripts/data_pro_search.py --help` only when exact flags are needed.

## Credential Boundary

This skill only supports Agent Plan API key authentication:

- `ARK_AGENT_PLAN_API_KEY`

Run `scripts/data_pro_search.py` for every professional-dataset request. The script sends JSON-RPC HTTP directly to the DataPro endpoint and sets `X-Agent-Plan-Key` from `ARK_AGENT_PLAN_API_KEY`.

## Command

```bash
python3 {baseDir}/scripts/data_pro_search.py "比亚迪 ROE 盈利水平" --category finance
python3 {baseDir}/scripts/data_pro_search.py "北京字节跳动科技有限公司 注册资本 经营范围" --category enterprise-info
python3 {baseDir}/scripts/data_pro_search.py "科大讯飞股份有限公司 是否为失信被执行人 司法诉讼 行政处罚" --category enterprise-risk
python3 {baseDir}/scripts/data_pro_search.py "大语言模型 检索增强生成 2025 综述 论文" --category academic --raw
```

## Parameters

- `query`: natural-language query; include explicit stock code, company name, DOI, author, paper topic, or dataset name.
- `--category finance|enterprise-info|enterprise-risk|academic`: required dataset routing hint.
- `--raw`: print the parsed tool payload as JSON.
- `--timeout N`: defaults to `120`.

## Invocation Contract

1. Always set `--category`; choose one of `finance`, `enterprise-info`, `enterprise-risk`, or `academic`.
2. Use `--raw` when the caller needs the parsed payload or exact provider fields.

## Result Handling

1. Treat stdout as the professional-dataset result.
2. When passing finance results forward, keep security code, indicator name, value, unit, period, and caliber when present.
3. When passing enterprise results forward, keep company name, unified social credit code, legal representative, address, registration status, business scope, and capital fields when present.
4. When passing academic results forward, keep title/name, URL, publication date, snippet/abstract, authors, DOI, journal, and citation count when present.
5. Treat an out-of-scope or not-billed provider message as a terminal skill result. Retry only with a different user-provided query or category.
