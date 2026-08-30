# OpenClaw Skill 包规范

本文件定义 `my-skills` 仓库接受和发布的 skill 包格式。仓库校验器、同步脚本和本地维护的 skill 都遵循这里的约定；阅读本文件不依赖其他仓库或本机相邻目录。

## 1. 包边界

一个 skill 是包含 `SKILL.md` 的独立目录。最小结构为：

```text
<skill-name>/
└── SKILL.md
```

按功能需要增加以下目录：

```text
<skill-name>/
├── SKILL.md              入口、触发条件和最小执行合同
├── references/           按需读取的规则和接口说明
├── scripts/              可重复执行的实现
├── templates/            输出模板和静态资源
└── requirements.txt      组件级 Python 依赖，可选
```

仓库使用两个一级集合：

```text
info-track/<skill-name>/SKILL.md
openclaw-skills/<skill-name>/SKILL.md
```

skill 名称在整个部署环境中必须唯一；分组目录不属于 skill 名称。

## 2. `SKILL.md` frontmatter

`SKILL.md` 必须以 YAML frontmatter 开头，并包含三个单行字段：

```yaml
---
name: skill-name
description: 说明能力、适用输入和触发场景
metadata: {"openclaw":{"skillKey":"skill-name","emoji":"🔧"}}
---
```

字段要求：

| 字段 | 要求 |
| --- | --- |
| `name` | 与 skill 目录名完全一致；使用小写字母、数字和连字符 |
| `description` | 同时说明“做什么”和“什么时候使用”；保持单行 |
| `metadata` | 单行 JSON 对象，必须包含 `metadata.openclaw.skillKey` |
| `metadata.openclaw.skillKey` | 与 `name` 和目录名完全一致，是部署、配置和 UI 的稳定标识 |
| `homepage` | 可选；也可以只使用 `metadata.openclaw.homepage` |

frontmatter 中不要保存密钥、endpoint 的私有值、用户名目录或机器专属路径。

## 3. `metadata.openclaw`

本仓库使用以下字段：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `skillKey` | string | skill 的稳定标识，必填 |
| `emoji` | string | skill 列表中的图标 |
| `homepage` | string | 源码或项目主页 |
| `os` | string[] | 可运行的操作系统 |
| `always` | boolean | 是否跳过能力门控并始终加载 |
| `primaryEnv` | string | 配置界面的主要凭证字段 |
| `requires.bins` | string[] | 必须全部位于 `PATH` 的命令 |
| `requires.anyBins` | string[] | 至少一个必须位于 `PATH` 的命令 |
| `requires.env` | string[] | 运行前必须存在的环境变量名称 |
| `requires.config` | string[] | 运行前必须存在的配置项路径 |
| `install` | object[] | 缺少依赖时可执行的安装声明 |

`requires.env` 只写变量名。凭证值由部署环境的 shell environment、配置存储或技能配置界面注入，不写入 Git。

`primaryEnv` 用于突出主要凭证；它不能替代 `requires.env`。如果 skill 在缺少该变量时不可运行，应同时把变量名加入 `requires.env`。

## 4. 依赖声明

Python skill 优先声明 `uv` installer，并允许运行环境在 `python3` 与 `python` 之间选择：

```yaml
metadata: {"openclaw":{"skillKey":"example","emoji":"🔧","primaryEnv":"ARK_AGENT_PLAN_API_KEY","requires":{"anyBins":["python3","python"],"env":["ARK_AGENT_PLAN_API_KEY"]},"install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
```

依赖所有权遵循以下顺序：

1. `metadata.openclaw.install` 描述运行时自动安装入口。
2. `requirements.txt` 描述组件完整 Python 依赖。
3. 仓库根目录的 `pyproject.toml` 只服务仓库级工具，不代替组件依赖。

新增必填环境变量时，必须同时更新 `requires.env`、相关 reference 和协议测试。

## 5. 路径与工作目录

skill 内命令使用 `{baseDir}` 引用当前 skill 根目录：

```bash
python3 {baseDir}/scripts/tool.py --help
```

输入、输出和项目工作区由调用方选择。需要稳定路径时传入绝对路径，不假设仓库位于固定用户名或固定目录下。

文档和示例允许使用：

- `{baseDir}`：当前 skill 目录
- `$HOME`：当前用户主目录
- `<workspace>`：调用方选择的工作区
- `<repo-root>`：本仓库根目录

不得写入开发机器上的真实用户名路径。

## 6. 渐进式加载

入口只承担路由，不承载整套手册：

- `SKILL.md`：触发条件、必读文件、最小命令、执行顺序和失败边界。
- `references/`：参数、数据结构、服务提供方差异、恢复步骤和详细规则。
- `scripts/`：解析、转换、校验和 API 调用等确定性行为。
- `templates/`：模板、schema、示例资源和固定词表。

每条规则只保留一个归属文件。其他文件通过链接引用，不复制命令、成功条件或失败语义。这样可以避免同一流程出现多个相互冲突的版本。

## 7. 上游与本地版本

本仓库区分两种交付方式：

### 直接使用上游

部署 CLI 从上游来源安装，本仓库不保存副本、不覆盖入口、不维护 patch。此类 skill 只出现在 README 的部署清单中。

### 本地维护版本

最终交付源码在本仓库中。它可以是完全本地实现，也可以基于固定上游版本生成。基于上游的本地版本必须保存：

- 上游仓库与固定 commit 或发布版本；
- 未修改快照或可重建的发布目录；
- 确定性打包转换；
- 本地覆盖层与最小补丁队列；
- 对应许可证和同步验证。

是否存在上游不改变所有权：只要最终包包含本地入口、适配或补丁，就按本地维护版本发布。

## 8. 文档写法

文档先写当前合同，再写原因和边界：

1. 说明能力或结论。
2. 给出输入、输出、执行顺序和规则归属。
3. 给出可直接运行的命令或结构示例。
4. 最后说明限制、失败状态和恢复动作。

避免写调查过程、临时判断、对话式提醒和依赖维护者本机环境的引用。术语首次出现时在当前文件解释；链接用于展开细节，不能替代核心合同。

## 9. 验证合同

仓库基础检查命令：

```bash
bash scripts/verify-repo.sh
```

它验证：

- 两个 skill 集合中的每个一级目录都包含 `SKILL.md`；
- frontmatter 的 `name`、`description` 和 `metadata` 存在且为单行；
- `name`、`skillKey` 与目录名一致；
- `metadata` 和仓库内 JSON 可解析；
- Python、JavaScript 和 Shell 文件语法正确；
- `pyproject.toml` 与 `uv.lock` 一致。

组件行为由对应专项入口验证：

```bash
bash scripts/verify-ark-skills.sh
bash scripts/verify-guizang-ppt-skill.sh
PYTHON_BIN="$HOME/Documents/hermes-workspace/.venv/bin/python" bash scripts/verify-ppt-master.sh
```

仓库新增 metadata 字段或包结构时，应先更新本文件和 `scripts/verify-repo.sh`，再修改各 skill。这样文档和可执行校验保持同一个合同。
