# AI 厂商来源

固定来源是输入边界。默认全部检查；来源失败时在 stderr 报告并继续，不以非官方来源补位。

| source | URL | 内容范围 |
| --- | --- | --- |
| OpenAI News | https://openai.com/news/rss.xml | 产品、模型、研究与公司更新 |
| Anthropic News | https://www.anthropic.com/news | 产品、模型、公司与安全更新 |
| Anthropic Engineering | https://www.anthropic.com/engineering | 工程与技术文章 |
| Claude Blog | https://claude.com/blog | Claude 产品、工作流与技术博客 |
| Google AI Blog | https://blog.google/innovation-and-ai/technology/ai/rss/ | Google AI 产品与技术更新 |
| Google DeepMind | https://deepmind.google/blog/rss.xml | 模型、研究与技术进展 |
| Cursor Blog | https://cursor.com/cn/blog | Cursor 产品、工程与研究文章 |
| Interconnects AI | https://www.interconnects.ai/feed | 模型与产业技术分析 |

分类规则：

- `AI厂商产品更新`：产品发布、功能更新、API/订阅变化、客户案例、商业合作和企业落地。
- `AI厂商博客更新`：技术博客、研究、工程实践、模型机制、Agent harness、科学与系统架构。
- `-misc`：与上述两类无直接关系的条目；成稿时丢弃。
