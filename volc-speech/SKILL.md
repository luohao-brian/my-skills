---
name: volc-speech
description: 使用火山引擎语音能力完成语音合成和语音识别，支持文本转语音(TTS)与本地音频转文本(STT)。当用户需要把文本生成语音、把录音转成文字、做字幕初稿、语音播报或验证语音接口时使用。
homepage: https://www.volcengine.com/docs/6561/1354871
metadata: {"openclaw":{"emoji":"🎙️"}}
---

# 火山引擎语音处理

调用火山引擎语音接口完成语音合成（TTS）和语音识别（STT）。

命令成功时默认输出 JSON，便于 agent 直接解析字段；TTS 返回落盘音频路径，STT 返回最终识别文本。

## 何时使用

- 需要把文本生成为语音播报、旁白、提示音
- 需要把本地录音、会议音频、采访素材转成文字
- 需要快速做字幕初稿、转写草稿或语音接口联调
- 需要基于音色、语速、情感参数生成不同风格的音频

## 快速开始

先准备环境变量：

- TTS：
- `VOLC_TTS_APP_ID`
- `VOLC_TTS_ACCESS_KEY`
- `VOLC_TTS_RESOURCE_ID`
- STT：
- `VOLC_STT_APP_ID`
- `VOLC_STT_ACCESS_KEY`
- `VOLC_STT_RESOURCE_ID`

典型资源 ID：

- TTS：`volc.service_type.10029`
- STT 2.0 流式小时版：`volc.seedasr.sauc.duration`
- STT 2.0 流式并发版：`volc.seedasr.sauc.concurrent`
- STT 1.0 流式小时版：`volc.bigasr.sauc.duration`
- STT 1.0 流式并发版：`volc.bigasr.sauc.concurrent`

最小示例：

```bash
VOLC_TTS_RESOURCE_ID=volc.service_type.10029 {baseDir}/bin/volc-speech tts "欢迎使用火山语音"
VOLC_STT_RESOURCE_ID=volc.seedasr.sauc.duration {baseDir}/bin/volc-speech stt ./meeting.ogg
```

当前推荐的环境变量前缀已经拆分：

- TTS：`VOLC_TTS_*`
- STT：`VOLC_STT_*`

## OpenClaw 注入

这个 skill 已符合 OpenClaw skill 标准：

- `metadata.openclaw` 保留了标准结构
- 因为 TTS 和 STT 使用两套不同环境变量，主 skill 不再用 `requires.env` 强绑定某一组，否则会错误挡住另一种能力
- 推荐通过 `skills.entries.volc-speech.env` 显式注入你实际需要的 TTS / STT 环境变量

示例：

```json
{
  "skills": {
    "entries": {
      "volc-speech": {
        "enabled": true,
        "env": {
          "VOLC_TTS_APP_ID": "your_tts_app_id",
          "VOLC_TTS_ACCESS_KEY": "your_tts_access_key",
          "VOLC_TTS_RESOURCE_ID": "volc.service_type.10029",
          "VOLC_STT_APP_ID": "your_stt_app_id",
          "VOLC_STT_ACCESS_KEY": "your_stt_access_key",
          "VOLC_STT_RESOURCE_ID": "volc.seedasr.sauc.duration"
        }
      }
    }
  }
}
```

## 常用命令

### TTS

```bash
VOLC_TTS_RESOURCE_ID=volc.service_type.10029 {baseDir}/bin/volc-speech tts "欢迎使用火山语音" --speaker zh_female_cancan_mars_bigtts
VOLC_TTS_RESOURCE_ID=volc.service_type.10029 {baseDir}/bin/volc-speech tts "今天心情特别好" --emotion happy --emotion-scale 4 --speech-rate 15 --loudness-rate 10
```

### STT

```bash
VOLC_STT_RESOURCE_ID=volc.seedasr.sauc.duration {baseDir}/bin/volc-speech stt ./meeting.ogg
VOLC_STT_RESOURCE_ID=volc.seedasr.sauc.duration {baseDir}/bin/volc-speech stt ./speech.wav --format wav --codec raw --json
```

## 参数导航

不要把所有细节都塞进主 skill。按需打开下面的参考文档：

- [references/setup-guide.md](references/setup-guide.md)：环境变量、资源 ID、OpenClaw 注入、兼容变量
- [references/tts-guide.md](references/tts-guide.md)：TTS 参数、情感、语速、音量、输出格式、返回 JSON
- [references/stt-guide.md](references/stt-guide.md)：STT 参数、格式/编码组合、常见音频配置、返回 JSON
- [references/voices.md](references/voices.md)：常用音色分组、示例 `voice_type`、情感支持说明
- [references/docs-index.md](references/docs-index.md)：官方文档入口和实现参考

## 故障排查

- 缺少 TTS 凭证：优先检查 `VOLC_TTS_APP_ID` 和 `VOLC_TTS_ACCESS_KEY`
- 缺少 STT 凭证：优先检查 `VOLC_STT_APP_ID` 和 `VOLC_STT_ACCESS_KEY`
- TTS 权限错误：检查 `VOLC_TTS_RESOURCE_ID` 是否指向正确的 TTS 资源
- STT 权限错误：检查 `VOLC_STT_RESOURCE_ID` 是否指向正确的 STT 资源
- STT 文本为空：检查上传文件是否为空，`format` / `codec` / `rate` 是否与真实音频一致
- TTS 情感不生效：先换一个支持多情感的音色，再检查 `emotion` 与 `emotion_scale`
