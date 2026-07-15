---
name: feishu-media-send
description: 通过飞书开放平台直接发送本地图片、视频或文件到指定飞书用户/群聊。适用于 OpenClaw message+media 上传失败时的可靠兜底，支持图片 image、MP4 视频 media、普通文件 file。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/feishu-media-send
metadata: {"openclaw":{"skillKey":"feishu-media-send","emoji":"📎","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/feishu-media-send","requires":{"anyBins":["python3","python"]},"install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Feishu Media Send

Use this skill to send a local image, video, or file through Feishu OpenAPI when the normal OpenClaw `message` tool media upload path is unreliable.

## Command

Send an image to a Feishu user:

```bash
python3 {baseDir}/scripts/feishu_media_send.py --path /root/workspace/media/image.jpg --to ou_xxx
```

Send an MP4 video:

```bash
python3 {baseDir}/scripts/feishu_media_send.py --path /root/workspace/media/video.mp4 --to oc_xxx --receive-id-type chat_id
```

Send a text caption before the media:

```bash
python3 {baseDir}/scripts/feishu_media_send.py --path ./image.png --to ou_xxx --caption "生成好了"
```

## Contract

1. The script reads Feishu `appId` and `appSecret` from the existing OpenClaw config by default.
2. Override credentials only with `FEISHU_APP_ID` and `FEISHU_APP_SECRET` when explicitly needed.
3. Images are uploaded to `/open-apis/im/v1/images` and sent with `msg_type=image`.
4. MP4 videos are uploaded to `/open-apis/im/v1/files` with `file_type=mp4` and sent with `msg_type=media`.
5. Other files are uploaded to `/open-apis/im/v1/files` and sent with `msg_type=file`.
6. Expect stdout JSON containing `success`, `message_id`, `chat_id`, `media_kind`, `upload_key`, and `path`.
