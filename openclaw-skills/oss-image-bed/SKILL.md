---
name: oss-image-bed
description: 上传文件到阿里云 OSS 或火山 TOS，生成临时链接并自动清理文件。需要给应用、模型或其他 agent 分享图片、HTML、文档时使用。
metadata: {"openclaw":{"skillKey":"oss-image-bed","emoji":"☁️","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/oss-image-bed","primaryEnv":"IMAGE_BED_SECRET_KEY","requires":{"anyBins":["python3","python"],"env":["IMAGE_BED_PROVIDER","IMAGE_BED_ACCESS_KEY","IMAGE_BED_SECRET_KEY","IMAGE_BED_BUCKET","IMAGE_BED_REGION"]},"install":[{"id":"tos-sdk","kind":"uv","package":"tos>=2.9.2,<3"},{"id":"oss-sdk","kind":"uv","package":"oss2>=2.19.1,<3"},{"id":"http","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# OSS Image Bed

上传单个本地文件，使用返回的 GET URL 访问。支持任意文件类型，不限图片。

## 执行

1. 首次使用时读取 [配置说明](references/configuration.md)，设置环境变量并配置自动清理。凭证不写入 skill。
2. 上传时传入自己的 agent 名称。链接默认 1 小时有效，最多 24 小时。
3. 将成功结果中的 `url` 和 `expires_at` 交给调用方。失败时报告错误，不返回可用链接。

```bash
python3 {baseDir}/scripts/image_bed.py setup-lifecycle
python3 {baseDir}/scripts/image_bed.py upload ./image.png --agent-name researcher
python3 {baseDir}/scripts/image_bed.py upload ./report.html --agent-name writer --expires-in 3600
```

## 注意

- 并发 agent 只运行 `upload`。文件统一放在 `image_bed_temp/`，自动生成唯一名称，不提供覆盖或删除操作。
- 链接到期后失效；文件满 1 天后由云端异步清理，不是到期立即删除。清理规则缺失时上传会停止。
- 为 HTML 配图或验证网页时，再读 [HTML 访问说明](references/html.md)。
