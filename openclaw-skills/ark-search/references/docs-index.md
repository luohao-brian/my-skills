# Ark Agent Plan Search Reference

Use this reference only when request or response details are needed.

## Endpoint

- URL: `https://open.feedcoopapi.com/search_api/web_search`
- Method: `POST`
- Authentication: `Authorization: Bearer $ARK_AGENT_PLAN_API_KEY`
- Content type: `application/json`
- Official docs: https://www.volcengine.com/docs/87772/2272953?lang=zh

## Request Rules

Build requests with these rules:

- Put the user's search text in `Query`. Keep it focused and within 1 to 100 characters.
- Use `SearchType=web` when the user needs webpages, current facts, news, official pages, or cited textual evidence.
- Use `SearchType=image` only when the user asks for image search results.
- Do not send `SearchType=web_summary`. For summarized web results, send `SearchType=web` and keep `NeedSummary=true`.
- Set `Count` to the number of results needed for the task. Defaults are `10` for `web` and `5` for `image`; hard limits are `50` for `web` and `5` for `image`.
- Use `TimeRange` only with `web`. Valid values are `OneDay`, `OneWeek`, `OneMonth`, `OneYear`, or `YYYY-MM-DD..YYYY-MM-DD`.
- Put all filters inside `Filter`; omit empty filters instead of sending null values.
- Set `Filter.NeedContent=true` when the answer needs page body text, not only snippets.
- Set `Filter.NeedUrl=true` when the answer must cite original URLs.
- Set `Filter.Sites` to a `|`-separated allowlist of complete domains when the user asks for specific sites or high-trust sources.
- Set `Filter.BlockHosts` to a `|`-separated blocklist of complete domains when noisy domains should be excluded.
- Set `Filter.AuthInfoLevel=1` when the answer should prefer very authoritative sources.
- Set `Filter.QueryRewrite=true` only when recall matters more than latency.

## Response Rules

Handle successful responses with these rules:

- Treat `Result.ResultCount` and `Result.TimeCost` as request metadata, not answer evidence.
- For `web`, answer only from `Result.WebResults`. Preserve each useful item's `Title`, `SiteName`, `Url`, `PublishTime`, and `Summary` or `Snippet`.
- If `Content` is present, use it for deeper evidence, but keep citations tied to the item's `Url`.
- If `Url` is empty, keep the result as uncited context unless the user explicitly accepts source-less results.
- For `image`, use `Result.ImageResults`; preserve the image URL plus width, height, shape, source page URL, title, and site name when present.
- `CardResults` contains structured 火山如意 cards for some web results. Use it only as extra structured context, not as a replacement for `WebResults`.
- Use `Result.SearchContext` to detect provider query rewrites or the final search type when that affects the answer.
- Use `ResponseMetadata.RequestId` or `Result.LogId` only for debugging, failure reports, or reproducibility notes.

## Error Rules

Handle failures with these rules:

- If `ResponseMetadata.Error` is present, stop and report its `Code` and `Message`.
- For `10400`, fix the request shape before retrying.
- For `10401`, report that `ARK_AGENT_PLAN_API_KEY` is invalid or expired.
- For `10402`, use only supported search types: `web` or `image`.
- For `10403`, report that the account lacks permission for the requested search product.
- For `10406`, report quota exhaustion; do not retry immediately.
- For `10500`, retry once if the task is still useful.
- For `700429`, back off before retrying; the default account limit is 5 QPS.
- If HTTP transport fails before a JSON response is returned, report the HTTP or network error without inventing search results.
