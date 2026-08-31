# Ark Video Generation Reference

## 后端与模型

| `--backend` | 凭证 | 端点 | 默认模型 |
| --- | --- | --- | --- |
| `ark-agent-plan` | `ARK_AGENT_PLAN_API_KEY` | `https://ark.cn-beijing.volces.com/api/plan/v3` | `doubao-seedance-2.0-fast` |
| `ark-api` | `ARK_API_KEY` | `https://ark.cn-beijing.volces.com/api/v3` | `doubao-seedance-2-5-260628` |

Agent Plan 还支持 `doubao-seedance-2.0`。Ark API 还支持 `doubao-seedance-2-0-fast-260128`、`doubao-seedance-2-0-mini-260615` 和 `doubao-seedance-2-0-260128`。后端之间不自动重试或切换。

## 模型能力

| 模型 | 时长 | 分辨率 | 参考图片 | 参考视频 | 参考音频 |
| --- | --- | --- | --- | --- | --- |
| Seedance 2.5 | 4–30 秒或 `-1` | 480p、720p、1080p | 最多 30 张 | 最多 10 段 | 最多 10 段 |
| Seedance 2.0 | 4–15 秒或 `-1` | 480p、720p、1080p、4K | 最多 9 张 | 最多 3 段 | 最多 3 段 |
| Seedance 2.0 Fast/Mini | 4–15 秒或 `-1` | 480p、720p | 最多 9 张 | 最多 3 段 | 最多 3 段 |

Seedance 2.5 单次最多输入 50 个参考素材；视频总时长不超过 30 秒，音频总时长不超过 30 秒。Seedance 2.0 系列的视频总时长不超过 15 秒，音频总时长不超过 15 秒，参考音频需要与图片或视频一起使用。

Seedance 2.x 不使用 `seed` 或 `camera_fixed`。

## 生成模式

| 模式 | 参数 | API role |
| --- | --- | --- |
| 文生视频 | 无素材参数 | 无 |
| 首帧生视频 | `--first-frame` | `first_frame` |
| 首尾帧生视频 | `--first-frame`、`--last-frame` | `first_frame`、`last_frame` |
| 参考生视频 | 重复 `--reference-image`、`--reference-video`、`--reference-audio` | `reference_image`、`reference_video`、`reference_audio` |
| Seedance 2.5 编辑 | `--task-type edit`、参考视频 | `reference_video` |
| Seedance 2.5 延长 | `--task-type extend`、参考视频 | `reference_video` |

首帧、首尾帧、编辑和延长必须使用 `--aspect-ratio adaptive`。编辑还必须使用 `--duration -1`。严格首帧模式和全模态参考模式互斥。

## 素材输入

- 图片：本地文件、HTTP(S) URL、图片 data URL 或 `asset://` 素材 ID。
- 视频：HTTP(S) URL 或 `asset://` 素材 ID。Ark 不接受视频 Base64；本地视频需要先上传。
- 音频：本地 WAV/MP3、HTTP(S) URL、音频 data URL 或 `asset://` 素材 ID。

这里的“上传”必须得到 Seedance 可读取的 HTTP(S) URL 或受信任 `asset://` ID。标准 Ark Files API 只返回推理用 `file_id`，不返回公开 URL；当前视频生成 schema 的 `image_url`、`video_url`、`audio_url` 内部都只接受 `url: string`。因此不要把 `file-...` 填进这些字段。Files API 适合先用 `ark-vision` 分析参考素材，但不是 Seedance 参考素材托管接口。

本地图片必须小于 30 MB，本地音频必须小于 15 MB。图片、视频和音频分别按同类素材的参数顺序编号，提示词编号必须使用相同顺序。

Seedance 2.5 和 2.0 系列不能直接上传普通的真人人脸参考图或视频。需要使用已授权素材、平台预置虚拟人，或同账号有效期内的受信任 Ark 原始产物。

## 常用命令

文生视频：

```bash
python3 {baseDir}/scripts/volc_video_gen.py "海边日落，镜头缓慢后退。" --duration 5 --aspect-ratio 16:9
```

首尾帧：

```bash
python3 {baseDir}/scripts/volc_video_gen.py "人物从首帧姿态自然转身，最终到达尾帧姿态。" --backend ark-api --first-frame ./start.png --last-frame ./end.png
```

多素材参考：

```bash
python3 {baseDir}/scripts/volc_video_gen.py "使用@图像1中的人物外形，参考@视频1中的动作和运镜，使用@音频1中的音色。" --backend ark-api --reference-image ./person.png --reference-video https://example.com/motion.mp4 --reference-audio ./voice.mp3 --audio --task-type reference
```

只校验请求，不使用凭证或额度：

```bash
python3 {baseDir}/scripts/volc_video_gen.py "一只可爱的小狗面向镜头，轻轻摇动尾巴。中景固定镜头，小狗保持清晰居中，动作自然连贯。" --dry-run
```

恢复任务：

```bash
python3 {baseDir}/scripts/volc_video_gen.py --backend ark-api --resume-task TASK_ID --timeout 600
```

## 请求与输出

Agent Plan 和 Ark API 都把 `duration`、`ratio`、`resolution`、`generate_audio` 和 `watermark` 作为结构化字段发送。脚本不向提示词追加接口参数。

Seedance 2.5 按需发送 `omni_reference_task_type`、`output_format` 和 `return_last_frame`。

脚本默认轮询 600 秒，每 5 秒查询一次，可使用 `--timeout` 和 `--poll-interval` 调整。超时结果保留 `task_id` 和最后状态；`--resume-task` 只查询已有任务，不重新提交。

成功结果包含远程 `video_url` 和本地 `local_path`。默认下载到 `$HOME/Documents/hermes-workspace/videos`。视频和尾帧 URL 有效期为 24 小时；Seedance 2.5 结果 URL 最多下载 100 次。

下载失败时远端生成仍然成功，结果保留 URL 并在 `warnings` 中说明下载错误。`duration`、`aspect_ratio`、`resolution` 和 `generate_audio` 使用任务详情返回的实际值，不用请求值补齐。

## 官方资料

- https://docs.volcengine.com/docs/82379/1520757?lang=zh
- https://docs.volcengine.com/docs/82379/1521309?lang=zh
- https://docs.volcengine.com/docs/82379/1521675?lang=zh
- https://docs.volcengine.com/docs/82379/2298881?lang=zh
- https://docs.volcengine.com/docs/82379/2607689?lang=zh
- https://docs.volcengine.com/docs/82379/2607688?lang=zh
