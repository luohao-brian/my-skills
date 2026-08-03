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

## Command

```bash
python3 {baseDir}/scripts/data_pro_search.py "比亚迪 ROE 盈利水平" --category finance
python3 {baseDir}/scripts/data_pro_search.py "北京字节跳动科技有限公司 注册资本 经营范围" --category enterprise-info
python3 {baseDir}/scripts/data_pro_search.py "科大讯飞股份有限公司 是否为失信被执行人 司法诉讼 行政处罚" --category enterprise-risk
python3 {baseDir}/scripts/data_pro_search.py "大语言模型 检索增强生成 2025 综述 论文" --category academic
```

## Parameters

- `query`: natural-language query; include explicit stock code, company name, DOI, author, paper topic, or dataset name.
- `--category finance|enterprise-info|enterprise-risk|academic`: required dataset routing hint.

## Contract

1. The script reads only `ARK_AGENT_PLAN_API_KEY` and uses the fixed DataPro endpoint.
2. Always set `--category`.
3. Stdout is the complete parsed JSON result; non-zero exit is failure.

## Result Handling

1. Treat the query as intent, not proof that the response uses the requested period or caliber.
2. For every finance value, keep its exact indicator path and matching `field_meta.caliber`, including period, unit, report type, trade date, or TTM basis when present.
3. If the requested period or caliber is absent, say so; never relabel another value as the requested one.
4. Preserve exact identity and source fields for enterprise and academic results.
5. Report out-of-scope or unbilled responses directly; do not invent data.
