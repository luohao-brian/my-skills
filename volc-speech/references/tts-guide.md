# TTS 参数指南

## 命令格式

```bash
{baseDir}/bin/volc-speech tts <TEXT> [OPTIONS]
```

## 参数说明

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `text` | 是 | - | 要合成的文本 |
| `--speaker` | 否 | `zh_female_cancan_mars_bigtts` | 音色 ID，对应官方 `voice_type` |
| `--format` | 否 | `mp3` | 输出音频格式，常见值：`mp3`、`wav`、`pcm`、`ogg_opus` |
| `--sample-rate` | 否 | `24000` | 输出采样率，常见值：`24000`、`16000`、`8000` |
| `--emotion` | 否 | - | 情感标签，仅部分音色支持 |
| `--emotion-scale` | 否 | - | 情感强度，范围 `1..5`，必须与 `--emotion` 搭配 |
| `--speech-rate` | 否 | `0` | 官方 V3 语速参数，范围 `-50..100` |
| `--loudness-rate` | 否 | `0` | 官方 V3 音量参数，范围 `-50..100` |
| `--output` | 否 | 自动生成 | 输出文件路径；不传时落到当前目录下的 `generated/` |
| `--uid` | 否 | `demo_user` | 透传给接口的用户 ID |

兼容别名：

- `--speed-ratio` 等价于 `--speech-rate`
- `--volume-ratio` 等价于 `--loudness-rate`

## 情感参数

当前官方文档中中文音色常见情感包括：

- `happy`
- `sad`
- `angry`
- `surprised`
- `fear`
- `hate`
- `excited`
- `coldness`
- `neutral`
- `depressed`
- `lovey-dovey`
- `shy`
- `comfort`
- `tension`
- `tender`
- `storytelling`
- `radio`
- `magnetic`
- `advertising`
- `vocal-fry`
- `ASMR`
- `news`
- `entertainment`
- `dialect`

注意：

- 不是所有音色都支持所有情感
- 多情感音色更适合联动 `emotion`
- `emotion-scale` 建议从 `3` 或 `4` 开始试

## 使用建议

### 最稳的通用配置

```bash
VOLC_TTS_RESOURCE_ID=volc.service_type.10029 {baseDir}/bin/volc-speech tts "欢迎使用火山语音"
```

### 情感示例

```bash
VOLC_TTS_RESOURCE_ID=volc.service_type.10029 {baseDir}/bin/volc-speech tts "今天真是太开心了" \
  --speaker zh_female_gaolengyujie_emo_v2_mars_bigtts \
  --emotion happy \
  --emotion-scale 4
```

### 语速和音量示例

```bash
VOLC_TTS_RESOURCE_ID=volc.service_type.10029 {baseDir}/bin/volc-speech tts "请仔细听下面的说明" \
  --speech-rate -10 \
  --loudness-rate 10
```

### 低码率链路友好示例

```bash
VOLC_TTS_RESOURCE_ID=volc.service_type.10029 {baseDir}/bin/volc-speech tts "电话通知测试" \
  --format mp3 \
  --sample-rate 16000
```

## 返回 JSON

成功时返回：

```json
{
  "type": "audio",
  "local_path": "/abs/path/file.mp3",
  "format": "mp3",
  "bytes": 30573,
  "log_id": "202603241459295412FD1DA15A39DC05E5",
  "speaker": "zh_female_cancan_mars_bigtts",
  "sample_rate": 24000,
  "emotion": "happy",
  "emotion_scale": 4,
  "speech_rate": 15,
  "loudness_rate": 10
}
```

## 常见问题

- `speaker permission denied`：通常是 `speaker` 未授权或资源 ID 配错
- `emotion` 无效：当前音色可能不支持该情感
- `--emotion-scale` 报错：需要和 `--emotion` 一起使用
- 参数越界：`speech-rate` / `loudness-rate` 必须在 `-50..100`，`emotion-scale` 必须在 `1..5`
