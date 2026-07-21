# OpenViking API contract

默认服务地址：`https://api.vikingdb.cn-beijing.volces.com/openviking`。

认证头：`Authorization: Bearer $ARK_AGENT_PLAN_OPENVIKING_API_KEY`。

本 Skill 使用以下只读接口：

| 操作 | HTTP API |
| --- | --- |
| 健康检查 | `GET /health` |
| 系统状态 | `GET /api/v1/system/status` |
| 浏览目录 | `GET /api/v1/fs/ls?uri=...` |
| 查看属性 | `GET /api/v1/fs/stat?uri=...` |
| 读取内容 | `GET /api/v1/content/read?uri=...` |
| 语义检索 | `POST /api/v1/search/find` |

`find` 的请求体至少包含 `query`，并可包含 `target_uri` 和 `limit`。URI 使用 `viking://` 协议；目录 URI 推荐以 `/` 结尾。

可通过 `ARK_AGENT_PLAN_OPENVIKING_BASE_URL` 覆盖服务地址，但不要把 API Key 写入配置文件、参数或输出。

Rspress 原文链接的站点根地址读取 `ARK_VIKING_RSPRESS_PUBLIC_BASE_URL`，默认值为 `http://8.140.22.158`。它不是凭证，可按部署域名覆盖。
