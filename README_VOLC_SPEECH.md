# README_VOLC_SPEECH

`volc-speech` 是火山引擎语音 skill，覆盖 TTS 和 STT，对应实现位于 [`/Users/bytedance/Documents/my-skills/rust/volc-speech`](/Users/bytedance/Documents/my-skills/rust/volc-speech)。

## 能力范围

- 文本转语音 `tts`
- 本地音频转文本 `stt`
- 常见音频格式识别
- 调试 JSON 输出

## 运行入口

- skill：[`/Users/bytedance/Documents/my-skills/volc-speech/SKILL.md`](/Users/bytedance/Documents/my-skills/volc-speech/SKILL.md)
- Rust CLI：[`/Users/bytedance/Documents/my-skills/rust/volc-speech/src/main.rs`](/Users/bytedance/Documents/my-skills/rust/volc-speech/src/main.rs)
- 参考文档索引：[`/Users/bytedance/Documents/my-skills/volc-speech/references/docs-index.md`](/Users/bytedance/Documents/my-skills/volc-speech/references/docs-index.md)

## 推荐环境变量

TTS：

- `VOLC_TTS_APP_ID`
- `VOLC_TTS_ACCESS_KEY`
- `VOLC_TTS_RESOURCE_ID`

STT：

- `VOLC_STT_APP_ID`
- `VOLC_STT_ACCESS_KEY`
- `VOLC_STT_RESOURCE_ID`

## 最小验证

```bash
cd /Users/bytedance/Documents/my-skills
bash scripts/volc-speech/verify.sh
```

带真实凭证：

```bash
cd /Users/bytedance/Documents/my-skills
bash scripts/volc-speech/verify.sh --live
```
