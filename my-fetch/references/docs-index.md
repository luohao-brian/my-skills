# my-fetch references

## 能力概览

`my-fetch` 是一个轻量网页抓取 skill，能力面尽量贴近 OpenClaw `web_fetch`：

- 抓取单个 URL
- 提取可读正文
- 返回适合 agent 继续处理的 markdown 或 text
- 支持局部提取和代理环境

## 提取链路

当前实现顺序：

1. 直连抓取
2. `text/markdown` / `application/json` 快速分支
3. HTML：
   - selector
   - Readability
   - 主内容 selector fallback
   - 整页 HTML -> markdown
4. 直连失败、`403/429/5xx`、或提取后为空时，回退 Jina Reader

## 对外输出

输出头固定以 `[web_fetch]` 开始，并保留这组最小字段：

- `url`
- `final_url`（仅发生跳转时出现）
- `status`
- `content_type`
- `extract_mode`
- `extractor`
- `title`（有值时出现）
- `truncated`（发生截断时出现）
- `warning`（有必要提示时出现）

正文放在头部后面，空一行输出。

## 兼容点

- 代理参数和 `volc-websearch` 保持一致：
  - `--http-proxy`
  - `--https-proxy`
  - `--no-proxy`
- 默认环境变量兼容 `WEB_SEARCH_*`

## 当前未实现的点

- 没有接 Firecrawl
- 没有接 OpenClaw 的 SSRF / trusted endpoint guard
- 没有浏览器渲染路径
- 没有 runtime 级缓存

## 调试建议

- 如果 `warning` 里出现 `Used Jina Reader fallback`，说明直连路径不稳定或正文为空
- 如果需要稳定提取页面局部内容，优先显式传 `--selector`
- 如果正文很长但只需要一部分，优先配合 `--selector` 或 `--max-chars`
