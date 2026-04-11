# README_MY_FETCH

`my-fetch` 是轻量网页抓取 skill，对应实现位于 [`/Users/bytedance/Documents/my-skills/rust/my-fetch`](/Users/bytedance/Documents/my-skills/rust/my-fetch)。

## 能力范围

- 单 URL 抓取
- HTML -> markdown / text
- CSS selector 定向提取
- JSON 格式化
- Jina Reader fallback
- 和搜索技能一致的代理参数

## 运行入口

- skill：[`/Users/bytedance/Documents/my-skills/my-fetch/SKILL.md`](/Users/bytedance/Documents/my-skills/my-fetch/SKILL.md)
- Rust CLI：[`/Users/bytedance/Documents/my-skills/rust/my-fetch/src/main.rs`](/Users/bytedance/Documents/my-skills/rust/my-fetch/src/main.rs)
- 参考文档：[`/Users/bytedance/Documents/my-skills/my-fetch/references/docs-index.md`](/Users/bytedance/Documents/my-skills/my-fetch/references/docs-index.md)

## 常见环境变量

- `WEB_FETCH_JINA_API_KEY`
- `JINA_API_KEY`
- `WEB_SEARCH_HTTP_PROXY`
- `WEB_SEARCH_HTTPS_PROXY`
- `WEB_SEARCH_NO_PROXY`

## 最小验证

```bash
cd /Users/bytedance/Documents/my-skills
bash scripts/my-fetch/verify.sh
```

带真实联网抓取：

```bash
cd /Users/bytedance/Documents/my-skills
bash scripts/my-fetch/verify.sh --live
```
