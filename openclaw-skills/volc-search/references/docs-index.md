# 火山引擎联网搜索文档索引

所有文档均位于火山引擎官网。官网页面可能动态渲染，必要时直接在浏览器中访问。

## 核心文档

| 文档 | 链接 |
| --- | --- |
| 融合信息搜索 API | https://www.volcengine.com/docs/85508/1650263 |
| 火山如意数据结构 | https://www.volcengine.com/docs/85508/1995628 |
| 产品简介 | https://www.volcengine.com/docs/85508/1510774 |
| 产品计费 | https://www.volcengine.com/docs/85508/1510784 |
| 快速入门 | https://www.volcengine.com/docs/85508/1544858 |

## 鉴权与 SDK

| 文档 | 链接 |
| --- | --- |
| Access Key 管理 | https://www.volcengine.com/docs/6291/65568 |
| 签名方法 | https://www.volcengine.com/docs/6369/67269 |
| 官方签名示例 Python | https://github.com/volcengine/volc-openapi-demos/blob/main/signature/python/sign.py |

## 控制台入口

| 入口 | 链接 |
| --- | --- |
| 联网搜索 API 开通 | https://console.volcengine.com/ask-echo/web-search |
| 联网问答 Agent 控制台 | https://console.volcengine.com/ask-echo |

## API 关键参数

请求：

```text
POST https://mercury.volcengineapi.com?Action=WebSearch&Version=2025-01-01
Content-Type: application/json
Authorization: HMAC-SHA256 Credential=..., SignedHeaders=..., Signature=...
```

固定签名参数：

- ServiceName: `volc_torchlight_api`
- Region: `cn-beijing`

请求体字段：

| 字段 | 类型 | 必须 | 说明 |
| --- | --- | --- | --- |
| `Query` | String | 是 | 搜索关键词，1 到 100 字符 |
| `SearchType` | String | 是 | `web` / `image` |
| `Count` | Number | 否 | 返回条数，`web` 最多 50，`image` 最多 5 |
| `NeedSummary` | Boolean | 否 | `web` 搜索建议设为 `true` |
| `TimeRange` | String | 否 | `OneDay` / `OneWeek` / `OneMonth` / `OneYear` / `YYYY-MM-DD..YYYY-MM-DD` |
| `Filter` | Object | 否 | 含 `Sites`、`BlockHosts`、`AuthInfoLevel` 等 |

响应字段：

- `Result.ResultCount`
- `Result.WebResults[]`
- `Result.ImageResults[]`
- `Result.TimeCost`
- `ResponseMetadata.Error`

`WebResults` 常用字段：

- `Title`
- `SiteName`
- `Url`
- `Snippet`
- `Summary`
- `Content`
- `PublishTime`
- `RankScore`
- `AuthInfoDes`
- `AuthInfoLevel`

错误码：

| 码 | 说明 |
| --- | --- |
| `10400` | 参数错误 |
| `10402` | 非法搜索类型 |
| `10403` | 权限错误 |
| `10500` | 内部错误，可重试 |
| `100013` | AccessDenied，子账号未授权 |
