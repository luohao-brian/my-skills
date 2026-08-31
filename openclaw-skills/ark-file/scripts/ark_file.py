#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
from pathlib import Path
from typing import Any


BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
API_KEY_ENV = "ARK_API_KEY"
PURPOSE = "user_data"
REQUEST_TIMEOUT_SECONDS = 120
DEFAULT_WAIT_TIMEOUT_SECONDS = 600.0
DEFAULT_POLL_INTERVAL_SECONDS = 2.0
DEFAULT_TTL_DAYS = 7
MIN_TTL_DAYS = 1
MAX_TTL_DAYS = 30
MAX_FILE_BYTES = 512 * 1024 * 1024
READY_STATUS = "active"
FAILURE_STATUSES = {"failed", "error", "expired", "cancelled"}
SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff",
    ".ico", ".icns", ".sgi", ".jp2", ".heic", ".heif",
    ".mp4", ".avi", ".mov", ".pdf", ".mp3", ".wav", ".aac", ".m4a",
}


def require_requests():
    try:
        import requests
    except ImportError:
        print("Error: requests is unavailable in the caller-selected Python environment", file=sys.stderr)
        raise SystemExit(1)
    return requests


def api_key() -> str:
    value = os.getenv(API_KEY_ENV, "").strip()
    if not value:
        raise ValueError(f"Missing {API_KEY_ENV}")
    return value


def headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key()}"}


def response_error(response: Any) -> str:
    message = ""
    try:
        payload = response.json()
        error = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(error, dict):
            message = str(error.get("message") or error.get("code") or "")
        elif error:
            message = str(error)
        elif isinstance(payload, dict):
            message = str(payload.get("message") or "")
    except Exception:
        pass
    if not message:
        message = response.text[:800]
    request_id = response.headers.get("x-request-id") or response.headers.get("x-tt-logid")
    suffix = f"; request_id={request_id}" if request_id else ""
    return f"HTTP {response.status_code}: {message[:800]}{suffix}"


def decode_json(response: Any) -> Any:
    if response.status_code >= 400:
        raise RuntimeError(response_error(response))
    try:
        return response.json()
    except Exception as exc:
        raise RuntimeError(f"Ark returned invalid JSON: {response.text[:800]}") from exc


def validate_file_id(file_id: str) -> str:
    value = file_id.strip()
    if not value.startswith("file-") or len(value) <= len("file-"):
        raise ValueError("file_id must start with file-")
    return value


def validate_upload_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if not path.is_file():
        raise ValueError(f"Upload file does not exist: {path_text}")
    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        values = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Unsupported user_data file extension {extension or '<none>'}; supported: {values}")
    size = path.stat().st_size
    if size <= 0:
        raise ValueError("Upload file is empty")
    if size > MAX_FILE_BYTES:
        raise ValueError("Upload file exceeds the 512 MB Ark-managed storage limit")
    return path


def retrieve_file(file_id: str) -> dict[str, Any]:
    requests = require_requests()
    value = validate_file_id(file_id)
    response = requests.get(
        f"{BASE_URL}/files/{value}",
        headers=headers(),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    body = decode_json(response)
    if not isinstance(body, dict):
        raise RuntimeError("Ark retrieve response is not an object")
    return body


def wait_for_file(file_id: str, *, timeout: float, poll_interval: float) -> dict[str, Any]:
    if timeout <= 0 or poll_interval <= 0:
        raise ValueError("timeout and poll interval must be positive")
    deadline = time.monotonic() + timeout
    last: dict[str, Any] = {}
    while True:
        last = retrieve_file(file_id)
        status = str(last.get("status") or "unknown").lower()
        if status == READY_STATUS:
            return last
        if status in FAILURE_STATUSES:
            raise RuntimeError(f"File preprocessing ended with status {status}: {json.dumps(last, ensure_ascii=False)[:800]}")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"Timed out waiting for {file_id}; last status={status}")
        time.sleep(min(poll_interval, remaining))


def upload_file(
    path_text: str,
    *,
    ttl_days: int,
    wait: bool,
    timeout: float,
    poll_interval: float,
) -> dict[str, Any]:
    if not MIN_TTL_DAYS <= ttl_days <= MAX_TTL_DAYS:
        raise ValueError(f"ttl-days must be between {MIN_TTL_DAYS} and {MAX_TTL_DAYS}")
    path = validate_upload_path(path_text)
    requests = require_requests()
    expire_at = int(time.time()) + ttl_days * 24 * 60 * 60
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    with path.open("rb") as source:
        response = requests.post(
            f"{BASE_URL}/files",
            headers=headers(),
            files={"file": (path.name, source, mime)},
            data={"purpose": PURPOSE, "expire_at": str(expire_at)},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    body = decode_json(response)
    if not isinstance(body, dict) or not body.get("id"):
        raise RuntimeError(f"Ark upload response has no file id: {json.dumps(body, ensure_ascii=False)[:800]}")
    if not wait:
        return body
    return wait_for_file(str(body["id"]), timeout=timeout, poll_interval=poll_interval)


def normalize_list(body: Any) -> dict[str, Any]:
    if body is None:
        return {"object": "list", "data": [], "has_more": False}
    if isinstance(body, list):
        return {"object": "list", "data": body, "has_more": False}
    if not isinstance(body, dict):
        raise RuntimeError("Ark list response is neither an object nor null")
    result = dict(body)
    data = result.get("data")
    if data is None:
        result["data"] = []
    elif not isinstance(data, list):
        raise RuntimeError("Ark list response data is not an array")
    result.setdefault("object", "list")
    result.setdefault("has_more", False)
    return result


def list_files(
    *,
    after: str | None,
    limit: int,
    order: str,
    purpose: str | None,
    scope_id: str | None,
) -> dict[str, Any]:
    if not 1 <= limit <= 99:
        raise ValueError("limit must be between 1 and 99")
    requests = require_requests()
    params: dict[str, Any] = {"limit": limit, "order": order}
    if after:
        params["after"] = validate_file_id(after)
    if purpose:
        params["purpose"] = purpose
    if scope_id:
        params["scope_id"] = scope_id
    response = requests.get(
        f"{BASE_URL}/files",
        headers=headers(),
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    return normalize_list(decode_json(response))


def delete_file(file_id: str) -> dict[str, Any]:
    requests = require_requests()
    value = validate_file_id(file_id)
    response = requests.delete(
        f"{BASE_URL}/files/{value}",
        headers=headers(),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    body = decode_json(response)
    if not isinstance(body, dict):
        raise RuntimeError("Ark delete response is not an object")
    return body


def print_json(value: Any, *, stream: Any = sys.stdout) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2), file=stream)


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage standard Ark inference files with ARK_API_KEY")
    subparsers = parser.add_subparsers(dest="command", required=True)

    upload = subparsers.add_parser("upload", help="Upload one local user_data file")
    upload.add_argument("path", help="Local image, video, PDF, or audio path")
    upload.add_argument("--ttl-days", type=int, default=DEFAULT_TTL_DAYS, help="Expiry in 1-30 days; default 7")
    upload.add_argument("--no-wait", action="store_true", help="Return the initial processing object without polling")
    upload.add_argument("--timeout", type=float, default=DEFAULT_WAIT_TIMEOUT_SECONDS)
    upload.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL_SECONDS)

    listing = subparsers.add_parser("list", help="List inference files")
    listing.add_argument("--after", help="Cursor file ID")
    listing.add_argument("--limit", type=int, default=99)
    listing.add_argument("--order", choices=("asc", "desc"), default="desc")
    listing.add_argument("--purpose", default=PURPOSE)
    listing.add_argument("--scope-id")

    retrieve = subparsers.add_parser("retrieve", aliases=["get"], help="Retrieve file metadata")
    retrieve.add_argument("file_id")

    wait = subparsers.add_parser("wait", help="Wait until file preprocessing becomes active")
    wait.add_argument("file_id")
    wait.add_argument("--timeout", type=float, default=DEFAULT_WAIT_TIMEOUT_SECONDS)
    wait.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL_SECONDS)

    delete = subparsers.add_parser("delete", help="Permanently delete one file")
    delete.add_argument("file_id")

    args = parser.parse_args()
    try:
        if args.command == "upload":
            result = upload_file(
                args.path,
                ttl_days=args.ttl_days,
                wait=not args.no_wait,
                timeout=args.timeout,
                poll_interval=args.poll_interval,
            )
        elif args.command == "list":
            result = list_files(
                after=args.after,
                limit=args.limit,
                order=args.order,
                purpose=args.purpose,
                scope_id=args.scope_id,
            )
        elif args.command in {"retrieve", "get"}:
            result = retrieve_file(args.file_id)
        elif args.command == "wait":
            result = wait_for_file(args.file_id, timeout=args.timeout, poll_interval=args.poll_interval)
        elif args.command == "delete":
            result = delete_file(args.file_id)
        else:
            raise ValueError(f"Unsupported command: {args.command}")
    except Exception as exc:
        print_json({"success": False, "type": "ark_file", "command": args.command, "error": str(exc)}, stream=sys.stderr)
        return 1

    print_json({"success": True, "type": "ark_file", "command": args.command, "result": result})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
