# 官方文档索引

以下是实现 `volc-speech` 时参考的官方文档，按需打开即可。

## TTS

- [豆包语音产品简介](https://www.volcengine.com/docs/6561/1354871)
- [HTTP Chunked/SSE 单向流式 V3](https://www.volcengine.com/docs/6561/1598757)
- [音色列表](https://www.volcengine.com/docs/6561/1257544?lang=zh)
- [在线语音合成 API 参数基本说明](https://www.volcengine.com/docs/6561/79823)

关键信息：

- `speaker` 对应官方的 `voice_type`
- 常见输出编码：`mp3`、`wav`、`pcm`、`ogg_opus`
- 常见采样率：`24000`、`16000`、`8000`
- 当前 V3 接口里的语速参数名是 `speech_rate`，范围 `-50..100`
- 当前 V3 接口里的音量参数名是 `loudness_rate`，范围 `-50..100`
- 当前 V3 接口支持 `emotion` 与 `emotion_scale(1..5)`；不同音色支持范围不同
- 大模型 TTS 常见资源 ID：`volc.service_type.10029`

## STT

- [大模型流式语音识别API](https://www.volcengine.com/docs/6561/1354869?lang=zh)
- [流式语音识别](https://www.volcengine.com/docs/6561/80818)
- [语音识别大模型产品简介](https://www.volcengine.com/docs/6561/1354871)
- [调用量查询接口说明](https://www.volcengine.com/docs/6561/1476625)

关键信息：

- WebSocket 二进制协议使用大端整数
- 常见输入配置：`rate=16000`、`bits=16`、`channel=1`
- 支持的容器格式：`pcm` / `wav` / `ogg` / `mp3`
- 常见格式 / 编码组合：`ogg + opus`、`wav + raw`
- 当 `format=ogg` 时，`codec` 必须传 `opus`
- 当 `format=mp3` 时，文档说明 `codec` 不生效，传默认值 `raw` 即可
- 大模型流式 STT 常见资源 ID：
  - 2.0 小时版：`volc.seedasr.sauc.duration`
  - 2.0 并发版：`volc.seedasr.sauc.concurrent`
  - 1.0 小时版：`volc.bigasr.sauc.duration`
  - 1.0 并发版：`volc.bigasr.sauc.concurrent`
