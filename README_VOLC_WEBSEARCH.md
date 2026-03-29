# README_VOLC_WEBSEARCH

`volc-websearch` 是多搜索源网页搜索 skill，对应实现位于 [`/Users/hluo/Documents/my-skills/rust/volc-websearch`](/Users/hluo/Documents/my-skills/rust/volc-websearch)。

## 能力范围

- Tavily / Brave / Bocha / Volc 搜索
- 结构化参数层
- 日期、站点、语言、地域约束
- 多引擎交叉检索

## 运行入口

- skill：[`/Users/hluo/Documents/my-skills/volc-websearch/SKILL.md`](/Users/hluo/Documents/my-skills/volc-websearch/SKILL.md)
- Rust CLI：[`/Users/hluo/Documents/my-skills/rust/volc-websearch/src/main.rs`](/Users/hluo/Documents/my-skills/rust/volc-websearch/src/main.rs)
- 文档索引：[`/Users/hluo/Documents/my-skills/volc-websearch/references/docs-index.md`](/Users/hluo/Documents/my-skills/volc-websearch/references/docs-index.md)

## 常见环境变量

- `TAVILY_API_KEY`
- `BOCHA_API_KEY`
- `BRAVE_API_KEY`
- `VE_ACCESS_KEY`
- `VE_SECRET_KEY`

## 最小验证

```bash
cd /Users/hluo/Documents/my-skills
bash scripts/volc-websearch/verify.sh
```

带真实凭证：

```bash
cd /Users/hluo/Documents/my-skills
bash scripts/volc-websearch/verify.sh --live
```
