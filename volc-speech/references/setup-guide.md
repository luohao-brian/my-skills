# 配置指南

这个 skill 同时支持 TTS 和 STT，推荐分别使用 `VOLC_TTS_*` 和 `VOLC_STT_*` 前缀管理凭证。

## 推荐环境变量

### TTS

- `VOLC_TTS_APP_ID`
- `VOLC_TTS_ACCESS_KEY`
- `VOLC_TTS_RESOURCE_ID`

### STT

- `VOLC_STT_APP_ID`
- `VOLC_STT_ACCESS_KEY`
- `VOLC_STT_RESOURCE_ID`

资源 ID 需要按能力切换：

| 能力 | 典型资源 ID | 说明 |
| --- | --- | --- |
| TTS 大模型 | `volc.service_type.10029` | 文本转语音 |
| STT 2.0 流式小时版 | `volc.seedasr.sauc.duration` | 你给的新版文档口径 |
| STT 2.0 流式并发版 | `volc.seedasr.sauc.concurrent` | 你给的新版文档口径 |
| STT 1.0 流式小时版 | `volc.bigasr.sauc.duration` | 兼容旧资源 |
| STT 1.0 流式并发版 | `volc.bigasr.sauc.concurrent` | 兼容旧资源 |

## OpenClaw 注入

这个 skill 可以直接通过标准 `skills.entries.<skill>.env` 注入：

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

说明：

1. 主 skill 没有使用 `requires.env` 做硬性门控
2. 原因是 TTS 和 STT 使用两套不同凭证，OpenClaw 当前没有“任意一组 env 满足即可”的标准门控语义
3. 因此，正确做法是通过 `skills.entries.volc-speech.env` 显式注入你要用的那一组或两组环境变量

## 兼容旧变量

为了兼容参考脚本和旧调用方式，当前 CLI 仍接受以下 fallback 变量：

### TTS

- `VOLC_TTS_APP_ID`
- `VOLC_TTS_ACCESS_KEY`
- `VOLC_TTS_RESOURCE_ID`
- `VOLC_AUDIO_APP_ID`
- `VOLC_AUDIO_ACCESS_KEY`
- `VOLC_AUDIO_RESOURCE_ID`
- `TTS_APP_ID`
- `TTS_ACCESS_KEY`
- `TTS_RESOURCE_ID`

### STT

- `VOLC_STT_APP_ID`
- `VOLC_STT_ACCESS_KEY`
- `VOLC_STT_RESOURCE_ID`
- `VOLC_APP_ID`
- `VOLC_ACCESS_KEY`
- `VOLC_RESOURCE_ID`

优先级建议：

1. `VOLC_TTS_*` / `VOLC_STT_*`
2. `VOLC_AUDIO_*`
3. 旧变量 fallback

## 推荐测试配置

TTS 测试：

```bash
export VOLC_AUDIO_APP_ID=your_app_id
export VOLC_TTS_ACCESS_KEY=your_access_key
export VOLC_TTS_RESOURCE_ID=volc.service_type.10029
```

STT 测试：

```bash
export VOLC_STT_APP_ID=your_app_id
export VOLC_STT_ACCESS_KEY=your_access_key
export VOLC_STT_RESOURCE_ID=volc.seedasr.sauc.duration
```
