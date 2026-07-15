#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
VIDEO_EXTS = {".mp4"}
FILE_TYPE_BY_EXT = {
    ".opus": "opus",
    ".mp4": "mp4",
    ".pdf": "pdf",
    ".doc": "doc",
    ".docx": "doc",
    ".xls": "xls",
    ".xlsx": "xls",
    ".ppt": "ppt",
    ".pptx": "ppt",
}
MAX_FEISHU_FILE_BYTES = 30 * 1024 * 1024


class FeishuError(RuntimeError):
    pass


def eprint_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)


def expand_path(value: str | None) -> Path | None:
    if not value:
        return None
    return Path(value).expanduser()


def json_pointer(data: Any, pointer: str) -> Any:
    current = data
    for raw_part in pointer.strip("/").split("/"):
        if raw_part == "":
            continue
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        raise KeyError(pointer)
    return current


def default_config_path() -> Path:
    if os.getenv("OPENCLAW_CONFIG"):
        return Path(os.environ["OPENCLAW_CONFIG"]).expanduser()
    home = Path(os.getenv("OPENCLAW_HOME") or Path.home()).expanduser()
    candidates = [
        home / ".openclaw" / "openclaw.json",
        Path.home() / ".openclaw" / "openclaw.json",
        Path("/root/.openclaw/openclaw.json"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def load_openclaw_config(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise FeishuError(f"OpenClaw config not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FeishuError(f"Invalid OpenClaw config JSON: {path}") from exc


def resolve_secret_ref(config: dict[str, Any], ref: Any) -> str:
    if isinstance(ref, str):
        return ref.strip()
    if not isinstance(ref, dict):
        return ""
    if ref.get("source") != "file":
        return ""
    provider_name = ref.get("provider")
    pointer = ref.get("id")
    providers = ((config.get("secrets") or {}).get("providers") or {})
    provider = providers.get(provider_name) if isinstance(providers, dict) else None
    if not isinstance(provider, dict) or not pointer:
        return ""
    secret_path_raw = provider.get("path")
    if not isinstance(secret_path_raw, str):
        return ""
    secret_path = Path(secret_path_raw).expanduser()
    secret_data = json.loads(secret_path.read_text())
    value = json_pointer(secret_data, str(pointer))
    return str(value).strip()


def load_credentials(config_path: Path) -> tuple[str, str]:
    env_app_id = os.getenv("FEISHU_APP_ID", "").strip()
    env_app_secret = os.getenv("FEISHU_APP_SECRET", "").strip()
    if env_app_id and env_app_secret:
        return env_app_id, env_app_secret

    config = load_openclaw_config(config_path)
    channels = config.get("channels") if isinstance(config.get("channels"), dict) else {}
    channel = channels.get("feishu") or channels.get("lark") or {}
    if not isinstance(channel, dict):
        channel = {}
    app_id = env_app_id or str(channel.get("appId") or channel.get("app_id") or "").strip()
    app_secret = env_app_secret or resolve_secret_ref(config, channel.get("appSecret") or channel.get("app_secret"))
    if not app_id:
        raise FeishuError("Missing Feishu appId. Set FEISHU_APP_ID or configure channels.feishu.appId.")
    if not app_secret:
        raise FeishuError("Missing Feishu appSecret. Set FEISHU_APP_SECRET or configure channels.feishu.appSecret.")
    return app_id, app_secret


def api_url(domain: str, path: str) -> str:
    host = "open.larksuite.com" if domain == "lark" else "open.feishu.cn"
    return f"https://{host}{path}"


def request_json(method: str, url: str, *, timeout: float, **kwargs: Any) -> dict[str, Any]:
    import requests

    response = requests.request(method, url, timeout=timeout, **kwargs)
    text = response.text
    if response.status_code >= 400:
        raise FeishuError(f"HTTP {response.status_code}: {text[:800]}")
    try:
        body = response.json()
    except ValueError as exc:
        raise FeishuError(f"Non-JSON response: {text[:800]}") from exc
    if body.get("code") not in (None, 0):
        raise FeishuError(f"Feishu API code={body.get('code')}, msg={body.get('msg')}")
    return body


def tenant_access_token(app_id: str, app_secret: str, domain: str, timeout: float) -> str:
    body = request_json(
        "POST",
        api_url(domain, "/open-apis/auth/v3/tenant_access_token/internal"),
        timeout=timeout,
        json={"app_id": app_id, "app_secret": app_secret},
    )
    token = body.get("tenant_access_token") or (body.get("data") or {}).get("tenant_access_token")
    if not token:
        raise FeishuError("tenant_access_token missing from response")
    return str(token)


def infer_receive_id_type(target: str) -> str:
    if target.startswith("oc_"):
        return "chat_id"
    if target.startswith("ou_"):
        return "open_id"
    if target.startswith("on_"):
        return "union_id"
    return "user_id"


def media_kind(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    return "file"


def upload_image(path: Path, token: str, domain: str, timeout: float) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    with path.open("rb") as handle:
        body = request_json(
            "POST",
            api_url(domain, "/open-apis/im/v1/images"),
            timeout=timeout,
            headers={"Authorization": f"Bearer {token}"},
            data={"image_type": "message"},
            files={"image": (path.name, handle, mime)},
        )
    image_key = (body.get("data") or {}).get("image_key") or body.get("image_key")
    if not image_key:
        raise FeishuError("image_key missing from upload response")
    return str(image_key)


def file_type_for(path: Path) -> str:
    return FILE_TYPE_BY_EXT.get(path.suffix.lower(), "stream")


def upload_file(path: Path, token: str, domain: str, timeout: float, duration_ms: int | None) -> tuple[str, str]:
    size = path.stat().st_size
    if size <= 0:
        raise FeishuError("Cannot upload an empty file")
    if size > MAX_FEISHU_FILE_BYTES:
        raise FeishuError(f"File exceeds Feishu IM upload limit: {size} bytes > {MAX_FEISHU_FILE_BYTES}")
    file_type = file_type_for(path)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    data: dict[str, str] = {"file_type": file_type, "file_name": path.name}
    if duration_ms is not None and file_type in {"mp4", "opus"}:
        data["duration"] = str(duration_ms)
    with path.open("rb") as handle:
        body = request_json(
            "POST",
            api_url(domain, "/open-apis/im/v1/files"),
            timeout=timeout,
            headers={"Authorization": f"Bearer {token}"},
            data=data,
            files={"file": (path.name, handle, mime)},
        )
    file_key = (body.get("data") or {}).get("file_key") or body.get("file_key")
    if not file_key:
        raise FeishuError("file_key missing from upload response")
    return str(file_key), file_type


def send_message(
    *,
    token: str,
    domain: str,
    target: str,
    receive_id_type: str,
    msg_type: str,
    content: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    return request_json(
        "POST",
        api_url(domain, f"/open-apis/im/v1/messages?receive_id_type={receive_id_type}"),
        timeout=timeout,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"receive_id": target, "msg_type": msg_type, "content": json.dumps(content, ensure_ascii=False)},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Send local media to Feishu via OpenAPI")
    parser.add_argument("--path", required=True, help="Local image, video, or file path")
    parser.add_argument("--to", required=True, help="Feishu target id: open_id, chat_id, union_id, or user_id")
    parser.add_argument("--receive-id-type", choices=["auto", "open_id", "chat_id", "union_id", "user_id"], default="auto")
    parser.add_argument("--caption", help="Optional text message sent before the media")
    parser.add_argument("--duration-ms", type=int, help="Optional duration for mp4/opus uploads")
    parser.add_argument("--domain", choices=["feishu", "lark"], default=os.getenv("FEISHU_DOMAIN", "feishu"))
    parser.add_argument("--config", default=str(default_config_path()))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("FEISHU_MEDIA_TIMEOUT", "60")))
    args = parser.parse_args()

    path = expand_path(args.path)
    if path is None or not path.is_file():
        eprint_json({"success": False, "error": f"File not found: {args.path}"})
        return 2

    try:
        app_id, app_secret = load_credentials(Path(args.config).expanduser())
        token = tenant_access_token(app_id, app_secret, args.domain, args.timeout)
        receive_id_type = infer_receive_id_type(args.to) if args.receive_id_type == "auto" else args.receive_id_type

        caption_result = None
        if args.caption:
            caption_result = send_message(
                token=token,
                domain=args.domain,
                target=args.to,
                receive_id_type=receive_id_type,
                msg_type="text",
                content={"text": args.caption},
                timeout=args.timeout,
            )

        kind = media_kind(path)
        if kind == "image":
            upload_key = upload_image(path, token, args.domain, args.timeout)
            msg_type = "image"
            content = {"image_key": upload_key}
            upload_file_type = None
        else:
            upload_key, upload_file_type = upload_file(path, token, args.domain, args.timeout, args.duration_ms)
            msg_type = "media" if kind == "video" else "file"
            content = {"file_key": upload_key}

        send_result = send_message(
            token=token,
            domain=args.domain,
            target=args.to,
            receive_id_type=receive_id_type,
            msg_type=msg_type,
            content=content,
            timeout=args.timeout,
        )
        data = send_result.get("data") or {}
        caption_data = (caption_result or {}).get("data") or {}
        print(json.dumps({
            "success": True,
            "path": str(path),
            "media_kind": kind,
            "msg_type": msg_type,
            "upload_key": upload_key,
            "file_type": upload_file_type,
            "receive_id_type": receive_id_type,
            "message_id": data.get("message_id"),
            "chat_id": data.get("chat_id"),
            "caption_message_id": caption_data.get("message_id"),
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        eprint_json({"success": False, "error": str(exc), "path": str(path)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
