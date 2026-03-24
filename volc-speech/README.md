# volc-speech

这个 `README.md` 只留在仓库里，方便人读，不会进入 skill 安装包。

`volc-speech` 是一个同时覆盖 TTS 和 STT 的火山语音 skill，对应的 Rust CLI 是 `volc-speech`。运行时环境变量已经拆分成两组：

- TTS：`VOLC_TTS_*`
- STT：`VOLC_STT_*`

## 仓库内参考文档

- [references/volc_tts.md](references/volc_tts.md)：TTS 参考文档，参数、音色、情感、语速、音量、返回 JSON
- [references/volc_stt.md](references/volc_stt.md)：STT 参考文档，格式、编码、资源 ID、返回 JSON
- [references/voices.md](references/voices.md)：常用音色整理
- [references/setup-guide.md](references/setup-guide.md)：OpenClaw 注入、环境变量和资源 ID 配置
- [references/docs-index.md](references/docs-index.md)：官方文档索引

## 代码入口

- Skill 入口：[SKILL.md](SKILL.md)
- Rust CLI：[rust/volc-speech/src/main.rs](/Users/bytedance/Documents/my-skills/rust/volc-speech/src/main.rs)
- 打包脚本：[build-skill-bundle.sh](/Users/bytedance/Documents/my-skills/build-skill-bundle.sh)

## 说明

- 安装包内只保留 `SKILL.md`、`references/` 和 `bin/volc-speech`
- 这个 `README.md` 仅用于仓库维护和人工查阅
