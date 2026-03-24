# volc-speech

这是 `volc-speech` 的仓库内说明文档，只给人看，不会被安装到最终 skill 包里。

`volc-speech` 是一个同时覆盖 TTS 和 STT 的火山语音 skill，对应的 Rust CLI 是 `volc-speech`。当前这套 skill 已经完成：

- TTS 实现
- STT 实现
- OpenClaw / agent skill 结构整理
- `VOLC_TTS_*` / `VOLC_STT_*` 前缀拆分
- 真实 API 联调验证

## 能力范围

### TTS

- 文本转语音
- 音色选择
- 情感参数
- 语速控制
- 音量控制
- 输出格式控制

### STT

- 本地音频文件上传识别
- WebSocket 大模型流式语音识别
- 支持常见格式：`wav`、`pcm`、`ogg`、`mp3`
- 支持输出完整 JSON payload 便于调试

## 官方参考文档

### TTS

- [豆包语音产品简介](https://www.volcengine.com/docs/6561/1354871)
- [HTTP Chunked/SSE 单向流式 V3](https://www.volcengine.com/docs/6561/1598757)
- [音色列表](https://www.volcengine.com/docs/6561/1257544?lang=zh)
- [在线语音合成 API 参数基本说明](https://www.volcengine.com/docs/6561/79823)

### STT

- [大模型流式语音识别API](https://www.volcengine.com/docs/6561/1354869?lang=zh)
- [流式语音识别](https://www.volcengine.com/docs/6561/80818)
- [语音识别大模型产品简介](https://www.volcengine.com/docs/6561/1354871)
- [调用量查询接口说明](https://www.volcengine.com/docs/6561/1476625)

仓库内索引：

- [references/docs-index.md](references/docs-index.md)

## 环境变量

### 推荐前缀

TTS：

- `VOLC_TTS_APP_ID`
- `VOLC_TTS_ACCESS_KEY`
- `VOLC_TTS_RESOURCE_ID`

STT：

- `VOLC_STT_APP_ID`
- `VOLC_STT_ACCESS_KEY`
- `VOLC_STT_RESOURCE_ID`

### 兼容 fallback

为了兼容旧 demo 和旧 skill 配置，CLI 仍接受：

- TTS：`VOLC_AUDIO_*`、`TTS_*`
- STT：`VOLC_AUDIO_*`、`VOLC_*`

优先级建议：

1. `VOLC_TTS_*` / `VOLC_STT_*`
2. `VOLC_AUDIO_*`
3. 旧 demo 变量

## 常见资源 ID

### TTS

- `volc.service_type.10029`

### STT

- 2.0 小时版：`volc.seedasr.sauc.duration`
- 2.0 并发版：`volc.seedasr.sauc.concurrent`
- 1.0 小时版：`volc.bigasr.sauc.duration`
- 1.0 并发版：`volc.bigasr.sauc.concurrent`

## TTS 参数总表

| 参数 | 默认值 | 可选值 / 范围 | 说明 |
| --- | --- | --- | --- |
| `text` | - | 任意文本 | 输入文本 |
| `--speaker` | `zh_female_cancan_mars_bigtts` | 参考音色列表 | 对应官方 `voice_type` |
| `--format` | `mp3` | `mp3` `wav` `pcm` `ogg_opus` | 输出音频格式 |
| `--sample-rate` | `24000` | `24000` `16000` `8000` | 输出采样率 |
| `--emotion` | - | 如 `happy` `sad` `angry` `storytelling` `news` `ASMR` | 情感标签，仅部分音色支持 |
| `--emotion-scale` | - | `1..5` | 情感强度，要求同时传 `--emotion` |
| `--speech-rate` | `0` | `-50..100` | 官方 V3 语速参数 |
| `--loudness-rate` | `0` | `-50..100` | 官方 V3 音量参数 |
| `--speed-ratio` | `--speech-rate` 别名 | 同上 | 兼容旧叫法 |
| `--volume-ratio` | `--loudness-rate` 别名 | 同上 | 兼容旧叫法 |
| `--output` | 自动生成 | 文件路径 | 输出音频文件路径 |
| `--uid` | `demo_user` | 任意字符串 | 透传用户 ID |

### 常见音色示例

- `zh_female_cancan_mars_bigtts`
- `zh_female_vv_uranus_bigtts`
- `zh_female_xiaohe_uranus_bigtts`
- `zh_male_m191_uranus_bigtts`
- `zh_male_taocheng_uranus_bigtts`
- `zh_male_lengkugege_emo_v2_mars_bigtts`
- `zh_female_gaolengyujie_emo_v2_mars_bigtts`
- `zh_female_tianxinxiaomei_emo_v2_mars_bigtts`

详细分组见：

- [references/voices.md](references/voices.md)

### 常见情感示例

- `happy`
- `sad`
- `angry`
- `surprised`
- `fear`
- `excited`
- `neutral`
- `tender`
- `storytelling`
- `news`
- `advertising`
- `ASMR`

注意：不是每个 `speaker` 都支持每个 `emotion`。

## STT 参数总表

| 参数 | 默认值 | 可选值 / 范围 | 说明 |
| --- | --- | --- | --- |
| `file` | - | 本地音频文件路径 | 输入音频文件 |
| `--format` | 按扩展名推断 | `pcm` `wav` `ogg` `mp3` | 音频容器格式 |
| `--codec` | 按格式推断 | 常见为 `raw` `opus` | `ogg` 时必须 `opus` |
| `--rate` | `16000` | 常见 `16000` | 输入采样率 |
| `--bits` | `16` | 常见 `16` | 位深 |
| `--channels` | `1` | 常见 `1` | 声道数 |
| `--seg-duration` | `200` | 建议 `100..200` ms | 发包间隔 |
| `--json` | `false` | `true/false` | 返回完整 payload |
| `--uid` | `demo_user` | 任意字符串 | 透传用户 ID |

### STT 格式说明

| 文件类型 | 推荐 format | 推荐 codec | 备注 |
| --- | --- | --- | --- |
| `.ogg` / `.opus` | `ogg` | `opus` | 最常用 |
| `.wav` | `wav` | `raw` | 最稳妥 |
| `.pcm` | `pcm` | `raw` | 原始裸流 |
| `.mp3` | `mp3` | `raw` | 参考新版文档，`codec` 不生效 |

## 典型命令

### TTS

```bash
VOLC_TTS_RESOURCE_ID=volc.service_type.10029 \
volc-speech tts "欢迎使用火山语音" \
  --speaker zh_female_cancan_mars_bigtts
```

```bash
VOLC_TTS_RESOURCE_ID=volc.service_type.10029 \
volc-speech tts "今天心情特别好" \
  --speaker zh_female_gaolengyujie_emo_v2_mars_bigtts \
  --emotion happy \
  --emotion-scale 4 \
  --speech-rate 15 \
  --loudness-rate 10
```

### STT

```bash
VOLC_STT_RESOURCE_ID=volc.seedasr.sauc.duration \
volc-speech stt ./meeting.ogg
```

```bash
VOLC_STT_RESOURCE_ID=volc.seedasr.sauc.duration \
volc-speech stt ./speech.wav --format wav --codec raw --json
```

## 与 skill 安装包的关系

安装包中保留：

- `SKILL.md`
- `references/`
- `bin/volc-speech`

不会进入安装包：

- 这个 `README.md`

当前 [build-skill-bundle.sh](/Users/bytedance/Documents/my-skills/build-skill-bundle.sh) 已经显式排除了 `volc-speech/README.md`。我实际检查过 [dist/volc-speech-macos.tar.gz](/Users/bytedance/Documents/my-skills/dist/volc-speech-macos.tar.gz)，包内没有这个文件。

## 代码与文档入口

- skill 入口：[SKILL.md](SKILL.md)
- TTS 细节：[references/tts-guide.md](references/tts-guide.md)
- STT 细节：[references/stt-guide.md](references/stt-guide.md)
- 音色表：[references/voices.md](references/voices.md)
- 配置说明：[references/setup-guide.md](references/setup-guide.md)
- Rust CLI：[rust/volc-speech/src/main.rs](/Users/bytedance/Documents/my-skills/rust/volc-speech/src/main.rs)
