# 来源与配比

| source | URL | 采集方式 | 默认权重 |
| --- | --- | --- | ---: |
| Hubwiz | https://www.hubwiz.com/blog/ | 按博客分页与发布时间采集 | 0.75 |
| QingkeAI | https://qingkeai.online | 按公开 Halo 内容 API 的发布时间采集 | 0.25 |

配额使用最大剩余法近似权重分配。某来源不足时，另一来源可以补足剩余额度；全部候选仍必须在指定窗口内。

`--weights` 接受逗号分隔的 `source=value`。来源名固定为 `Hubwiz`、`QingkeAI`；非法或空配置回退为默认权重。
