---
name: my-fetch
description: 抓取 URL 并提取可读网页内容（HTML 转 markdown/text）。当用户需要轻量读取页面正文，且不需要浏览器渲染时使用。
homepage: https://github.com/luohao-brian/my-skills/tree/main/my-fetch
metadata: {"openclaw":{"emoji":"🌐","homepage":"https://github.com/luohao-brian/my-skills/tree/main/my-fetch","os":["darwin","linux"]}}
---

# Web Fetch

抓取单个 URL，并提取适合继续处理的网页正文。

默认返回 `markdown`，也支持 `text`。这个工具不执行 JavaScript。

## 何时使用

- 已经拿到 URL，需要继续读取正文
- 搜索结果摘要不够，需要抓详情页
- 需要抓官网文档、博客文章、公告页、说明页
- 只需要轻量 HTTP 抓取，不需要浏览器渲染

## 核心规则

- 默认直接传 URL 即可，不要额外拼无关说明
- 默认使用 `markdown`；只有下游明确需要纯文本时再加 `--format text`
- 只有需要页面局部内容时才传 `--selector`
- 只有当前网络环境必须显式走代理时，才传代理参数
- 如果页面依赖浏览器渲染、登录态或 challenge，不要反复重试；改用浏览器工具

## 常用调用

```bash
{baseDir}/bin/my-fetch "https://example.com/article"
{baseDir}/bin/my-fetch "https://example.com/article" --format text
{baseDir}/bin/my-fetch "https://example.com/article" --selector article
```

## 常用选项

- `--format <markdown|text>`：切换输出格式
- `--max-chars <n>`：限制返回正文长度
- `--selector <css>`：只提取页面某一部分

## 输出

输出会带一个 `[web_fetch]` 头，包含 URL、状态、提取模式、提取器和必要提示，后面接正文。

如果页面需要浏览器渲染、登录态或被站点拦截，可能拿不到正文或只拿到低质量内容。

## 参考

- [references/docs-index.md](references/docs-index.md)：补充说明
