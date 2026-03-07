# My Skills

这是一个通用的 Agent 技能（Skills）集合仓库。这里的技能遵循通用的规范，可以通过 `skills` 工具安装并管理，供各种 Code Agents（如 Gemini CLI 等）调用。

## 项目结构

- `volc-gen/`: 调用火山引擎 Ark API 进行内容生成的技能，支持文生图、图生图及图生视频。
- `cli/`: 各技能共享的命令行工具目录（如 `volc`）。
- `install-cli.sh`: 将 `cli/` 下命令安装到 `/usr/local/bin`。
- `uninstall-cli.sh`: 从 `/usr/local/bin` 卸载 `cli/` 下命令。

## 安装与使用

1. 安装 CLI 命令到系统路径：
   ```bash
   cd /Users/bytedance/Documents/my-skills
   ./install-cli.sh
   ```
   如果当前用户对 `/usr/local/bin` 没有写权限，请使用：
   ```bash
   sudo ./install-cli.sh
   ```

2. 安装后即可直接执行命令（以 `volc` 为例）：
   ```bash
   volc query
   volc t2i "一只赛博朋克风格的猫"
   ```

3. 卸载 CLI 命令：
   ```bash
   ./uninstall-cli.sh
   ```
   无权限时同样可使用 `sudo ./uninstall-cli.sh`。

## 依赖

当前已包含的 `volc` 命令依赖以下系统工具：

- `curl`
- `jq`

安装示例：

```bash
# macOS (Homebrew)
brew install curl jq

# Ubuntu / Debian
sudo apt-get update
sudo apt-get install -y curl jq
```

## 环境变量配置

`volc` 需要设置火山引擎 Ark API Key：

```bash
export ARK_API_KEY="your-volcengine-api-key"
```

建议写入 shell 配置文件（如 `~/.bashrc` 或 `~/.zshrc`）：

```bash
echo 'export ARK_API_KEY="your-volcengine-api-key"' >> ~/.bashrc
source ~/.bashrc
```

## 兼容性

本项目中的技能旨在兼容支持标准 Skill 协议的 AI 助手和 CLI 工具。
