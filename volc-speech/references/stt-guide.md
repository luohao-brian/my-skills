# STT 参数指南

## 命令格式

```bash
{baseDir}/bin/volc-speech stt <FILE> [OPTIONS]
```

## 参数说明

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `file` | 是 | - | 本地音频文件路径 |
| `--format` | 否 | 扩展名推断，失败时 `ogg` | 音频容器格式 |
| `--codec` | 否 | 按 format 推断 | 常见值：`opus`、`raw`、`mp3` |
| `--rate` | 否 | `16000` | 采样率 |
| `--bits` | 否 | `16` | 位深，对 PCM/WAV 很重要 |
| `--channels` | 否 | `1` | 声道数 |
| `--seg-duration` | 否 | `200` | 每个音频包发送间隔毫秒数 |
| `--json` | 否 | `false` | 是否把最终原始 payload 一起返回 |
| `--uid` | 否 | `demo_user` | 透传给接口的用户 ID |

## 常见格式组合

| 文件类型 | 推荐 format | 推荐 codec | 说明 |
| --- | --- | --- | --- |
| `.ogg` / `.opus` | `ogg` | `opus` | 最常见的流式语音上传组合 |
| `.wav` | `wav` | `raw` | 原始 PCM 波形最稳妥 |
| `.pcm` | `pcm` | `raw` | 原始裸流场景 |
| `.mp3` | `mp3` | `raw` | 参考新版文档，`format=mp3` 时 `codec` 不生效，传默认值 `raw` 即可 |

如果文件真实编码与 `format` / `codec` 不匹配，常见后果是：

- 返回空文本
- 结果截断
- 时间戳异常
- 服务端直接报错

## 使用建议

### OGG / Opus

```bash
VOLC_STT_RESOURCE_ID=volc.seedasr.sauc.duration {baseDir}/bin/volc-speech stt ./meeting.ogg
```

### WAV / RAW

```bash
VOLC_STT_RESOURCE_ID=volc.seedasr.sauc.duration {baseDir}/bin/volc-speech stt ./speech.wav --format wav --codec raw
```

### 带原始 payload 调试

```bash
VOLC_STT_RESOURCE_ID=volc.seedasr.sauc.duration {baseDir}/bin/volc-speech stt ./speech.wav --format wav --codec raw --json
```

## 返回 JSON

默认返回：

```json
{
  "type": "transcript",
  "text": "这是最终识别出的文本",
  "file_path": "/abs/path/audio.wav"
}
```

加 `--json` 后，会把最终 `payload` 一并返回，适合调试字段映射和服务端结构变化。

## 常见问题

- 识别结果为空：优先检查 `format` / `codec` / `rate`
- 连接失败：检查 `VOLC_AUDIO_RESOURCE_ID` 是否切到了 STT
- PCM/WAV 结果异常：优先检查 `bits=16`、`channels=1`
- 长音频节奏问题：可以尝试调整 `--seg-duration`
