# Ark Files API Reference

## Scope

This skill manages inference files in standard Ark. Its resource shape follows the same upload/list/retrieve/delete pattern as the OpenAI Files API, while retaining Ark-specific asynchronous preprocessing and expiry behavior.

| Operation | Method and path | Command |
| --- | --- | --- |
| Upload | `POST /api/v3/files` | `upload` |
| List | `GET /api/v3/files` | `list` |
| Retrieve metadata | `GET /api/v3/files/{file_id}` | `retrieve` / `get` |
| Wait for preprocessing | repeated retrieve | `wait` |
| Delete | `DELETE /api/v3/files/{file_id}` | `delete` |

Ark does not expose a general file-content download endpoint for these inference uploads. A `file_id` is a provider-side reference, not a public URL.

## Supported `user_data` formats

- Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`, `.tiff`, `.ico`, `.icns`, `.sgi`, `.jp2`, `.heic`, `.heif`
- Videos: `.mp4`, `.avi`, `.mov`
- Documents: `.pdf`
- Audio: `.mp3`, `.wav`, `.aac`, `.m4a`

HTML, DOCX, TXT, source code, and arbitrary archives are not accepted by the inference `user_data` upload contract. Files for Managed Agents use a separate purpose and product contract; this skill intentionally does not mix that lifecycle into inference files.

## Lifecycle

Uploads normally move from `processing` to `active`. `failed`, `error`, and `expired` are terminal failures. The default expiry is 7 days; use `--ttl-days` to request 1–30 days. The script sends an absolute Unix timestamp as `expire_at`.

```bash
python3 {baseDir}/scripts/ark_file.py upload ./clip.mp4 --ttl-days 3
python3 {baseDir}/scripts/ark_file.py upload ./clip.mp4 --no-wait
python3 {baseDir}/scripts/ark_file.py wait file-20260101000000-example --timeout 600
```

`list` accepts Ark's cursor and filter fields:

```bash
python3 {baseDir}/scripts/ark_file.py list --limit 99 --order desc --purpose user_data
python3 {baseDir}/scripts/ark_file.py list --after file-20260101000000-example --scope-id SCOPE_ID
```

## Model consumption

The same-account Agent Plan key can consume a file uploaded with `ARK_API_KEY`, even though it cannot call the Files API itself.

Chat Completions content blocks:

```json
{"type":"image_url","image_url":{"file_id":"file-..."}}
{"type":"video_url","video_url":{"file_id":"file-..."}}
{"type":"file","file":{"file_id":"file-..."}}
```

Use the first for images, the second for videos, and the third for PDFs. `ark-vision` builds these shapes.

Files API compatibility is endpoint-specific. Image generation accepts reference-image URL or Base64. Video generation accepts image/video/audio URL strings, image/audio data URLs where documented, and `asset://` trusted assets. Neither generation endpoint documents a Files API `file_id` input, and Files API does not return a public URL. Do not place `file-...` inside a generation `url` field.

## Limits and billing

- Ark-managed storage: up to 512 MB per file and 20 GB per account.
- The default managed storage and Files API lifecycle operations are not separately charged. Model inference still consumes the selected model's tokens or plan quota.
- A user-owned TOS storage configuration has its own storage charges and limits; it is outside this skill's managed-storage path.

## Official documentation

- https://docs.volcengine.com/docs/82379/1885708?lang=zh
- https://docs.volcengine.com/docs/82379/1873424?lang=zh
- https://docs.volcengine.com/docs/82379/1870406?lang=zh
- https://docs.volcengine.com/docs/82379/1870408?lang=zh
