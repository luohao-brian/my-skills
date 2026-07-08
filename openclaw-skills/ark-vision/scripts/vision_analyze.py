#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any


def _require_requests():
    try:
        import requests
    except ImportError:
        print("Error: requests not installed. Run: pip install requests", file=sys.stderr)
        sys.exit(1)
    return requests


def api_key_value() -> str:
    return os.getenv("ARK_AGENT_PLAN_API_KEY", "").strip()


def endpoint(base_url: str, suffix: str) -> str:
    base = base_url.strip().rstrip("/")
    suffix = suffix.strip("/")
    if base.endswith(f"/{suffix}"):
        return base
    if base.endswith("/chat/completions") and suffix != "chat/completions":
        base = base[: -len("/chat/completions")]
    if base.endswith("/responses") and suffix != "responses":
        base = base[: -len("/responses")]
    return f"{base}/{suffix}"


def file_to_data_url(path_text: str) -> str:
    path = Path(path_text).expanduser()
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def normalize_image(image: str) -> str:
    if image.startswith(("http://", "https://", "data:")):
        return image
    path = Path(image).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"image file not found: {image}")
    return file_to_data_url(str(path))


def extract_responses_text(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    chunks: list[str] = []
    for item in payload.get("output") or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            if not isinstance(content, dict):
                continue
            text = content.get("text") or content.get("output_text")
            if isinstance(text, str) and text.strip():
                chunks.append(text.strip())
    return "\n".join(chunks).strip()


def response_error(response: Any) -> str:
    try:
        payload = response.json()
        error = payload.get("error")
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])[:800]
        if isinstance(error, str) and error:
            return error[:800]
    except Exception:
        pass
    return response.text[:800]


def analyze_image(args: argparse.Namespace) -> dict[str, Any]:
    requests = _require_requests()
    api_key = api_key_value()
    if not api_key:
        raise ValueError("Missing ARK_AGENT_PLAN_API_KEY")

    image_url = normalize_image(args.image)
    payload = {
        "model": args.model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_image", "image_url": image_url},
                    {"type": "input_text", "text": args.question},
                ],
            }
        ],
        "temperature": args.temperature,
        "max_output_tokens": args.max_output_tokens,
    }
    response = requests.post(
        endpoint(args.base_url, "responses"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=args.timeout,
    )
    if response.status_code >= 400:
        raise RuntimeError(response_error(response))

    body = response.json()
    analysis = extract_responses_text(body)
    result: dict[str, Any] = {
        "success": True,
        "type": "vision",
        "analysis": analysis,
        "model": args.model,
        "image": args.image,
    }
    if args.raw:
        result["raw"] = body
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze images with Ark Agent Plan vision models")
    parser.add_argument("image", help="Local image path, remote URL, or data URL")
    parser.add_argument("question", help="Question or extraction instruction about the image")
    parser.add_argument("--model", default=os.getenv("VOLC_VISION_MODEL_ID", "doubao-seed-2.0-lite"))
    parser.add_argument("--base-url", default=os.getenv("VOLC_ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/plan/v3"))
    parser.add_argument("--max-output-tokens", type=int, default=int(os.getenv("VOLC_VISION_MAX_OUTPUT_TOKENS", "2000")))
    parser.add_argument("--temperature", type=float, default=float(os.getenv("VOLC_VISION_TEMPERATURE", "0.1")))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("VOLC_VISION_TIMEOUT", "120")))
    parser.add_argument("--json", action="store_true", help="Print structured JSON instead of plain analysis text")
    parser.add_argument("--raw", action="store_true", help="Include raw provider response in JSON output")
    args = parser.parse_args()

    try:
        result = analyze_image(args)
    except Exception as exc:
        error = {"success": False, "type": "vision", "error": str(exc), "model": args.model, "image": args.image}
        print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        return 1

    if args.json or args.raw:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["analysis"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
