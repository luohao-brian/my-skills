# Ark Agent Plan DataPro Reference

Use this reference only when request or response details are needed.

## Endpoint

- URL: `https://datapro.hqd.cn-beijing.volces.com/mcp`
- Method: `POST`
- Authentication: `X-Agent-Plan-Key: $ARK_AGENT_PLAN_API_KEY`
- Content type: `application/json`
- Accept: `application/json, text/event-stream`
- Official docs: https://www.volcengine.com/docs/82379/2479086?lang=zh

Runtime path: run `scripts/data_pro_search.py`. The script sends JSON-RPC over HTTP to this endpoint and supplies the `X-Agent-Plan-Key` header.

Use `tools/call` with:

```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"dataPro_search","arguments":{"query":"比亚迪 ROE 盈利水平"}}}
```

The service also supports `initialize` and `tools/list`; `tools/list` returns `dataPro_search` with a single required `query` string argument.

## Supported Data

- Finance: domestic and global stocks, funds, futures, options, bonds, foreign exchange, financial indicators, quotes, and reports.
- Enterprise information: domestic company profiles, business scope, legal representative, shareholders, registration status, intellectual property, and related business fields.
- Enterprise risk: judicial litigation, court announcements, judgment documents, enforcement, administrative penalties, abnormal operations, and related risk information.
- Academic search: papers, literature, journals, authors, DOI, research topics, snippets, abstracts, publication dates, authors, and citation fields when present.

## Request Rules

- Put the user's professional-data request in `arguments.query`.
- Set `--category` for every request:
  - `finance`: financial instruments, prices, fundamentals, reports, or financial indicators.
  - `enterprise-info`: company profiles, registration, legal representative, shareholders, business scope, patents, or investments.
  - `enterprise-risk`: litigation, enforcement, administrative penalties, abnormal operations, lost trust, court announcements, or negative events.
  - `academic`: papers, literature, journals, authors, DOI, or research topics.
- The public backend tool only accepts `query`; the script applies category by prepending a concise Chinese dataset hint to the query before sending it.
- Include explicit entities: stock code, full company name, unified social credit code, DOI, author, journal, or paper topic.
- For finance, mention the target stock/security and metric. Single query limit is at most 3 stocks, securities, or entities.
- For enterprise information or risk, use full company names where possible. Single query limit is at most 5 companies.
- For academic search, mention academic intent such as paper, literature, journal, author, DOI, or research topic. Single query limit is at most 50 papers or articles.

## Response Rules

- Parse `result.structuredContent` when present; otherwise parse JSON from `result.content[].text`.
- Preserve `code`, `msg`, `trace_id`, `dataset_type`, and item count in failure reports or reproducibility notes.
- Common `dataset_type` values include `stock_finance`, `enterprise_info`, `enterprise_risk`, and `academic_search`.
- For finance records, preserve `security_code`, `indicator_name`, `value`, `unit`, `period`, and `caliber`.
- For enterprise records, preserve company name, unified social credit code, legal representative, address, registration status, business scope, and capital fields when present.
- For academic records, preserve title/name, URL, publication date, snippet/abstract, authors, DOI, journal, and citation count when present.
- If the response says the query is outside the supported scope or not billed, report that directly instead of inventing a dataset answer.
