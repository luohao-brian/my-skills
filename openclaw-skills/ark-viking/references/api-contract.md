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

`retrieve` 先在默认范围检索候选文章，再以每篇文章的资源根目录作为 `target_uri` 检索相关章节。整个流程只调用上表中的只读接口。

服务地址和 Rspress 原文链接根地址固定在脚本中。脚本只读取 `ARK_AGENT_PLAN_OPENVIKING_API_KEY`，不要把 Key 写入参数、文件或输出。
