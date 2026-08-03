---
name: feishu-media-send
description: 通过飞书开放平台直接发送本地图片、视频或文件到指定飞书用户或群聊。适用于任意 Agent 需要可靠发送图片、MP4 视频或普通文件，或已有媒体发送能力失败时的兜底。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/feishu-media-send
metadata: {"openclaw":{"skillKey":"feishu-media-send","emoji":"📎","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/feishu-media-send","requires":{"anyBins":["python3","python"]},"install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Feishu Media Send

Use this skill to send a local image, video, or file through Feishu OpenAPI from any Agent environment.

## Command

Send an image to a Feishu user:

```bash
python3 {baseDir}/scripts/feishu_media_send.py --path ./media/image.jpg --to ou_xxx
```

Send an MP4 video:

```bash
python3 {baseDir}/scripts/feishu_media_send.py --path ./media/video.mp4 --to oc_xxx --receive-id-type chat_id
```

Send a text caption before the media:

```bash
python3 {baseDir}/scripts/feishu_media_send.py --path ./image.png --to ou_xxx --caption "生成好了"
```

## Contract

1. Read credentials from `FEISHU_APP_ID` and `FEISHU_APP_SECRET` by default.
2. When the caller explicitly supplies `--config`, use that OpenClaw config only as an optional credential adapter. Do not discover Agent-specific config paths.
3. Images are uploaded to `/open-apis/im/v1/images` and sent with `msg_type=image`.
4. MP4 videos are uploaded to `/open-apis/im/v1/files` with `file_type=mp4` and sent with `msg_type=media`.
5. Other files are uploaded to `/open-apis/im/v1/files` and sent with `msg_type=file`.
6. Expect stdout JSON containing `success`, `message_id`, `chat_id`, `media_kind`, `upload_key`, and `path`.
