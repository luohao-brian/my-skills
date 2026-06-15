#!/usr/bin/env python3
"""Volcengine WebSearch API client using AK/SK authentication only."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import hmac
import json
import os
import re
import sys
from typing import Any
from urllib.parse import quote

SERVICE = "volc_torchlight_api"
VERSION = "2025-01-01"
REGION = "cn-beijing"
HOST = "mercury.volcengineapi.com"
ACTION = "WebSearch"
TIME_RANGE_SHORTCUTS = {"OneDay", "OneWeek", "OneMonth", "OneYear"}
DATE_RANGE_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})$")


def _require_requests():
    try:
        import requests
    except ImportError:
        print("Error: requests not installed. Run: pip install requests", file=sys.stderr)
        sys.exit(1)
    return requests


def _hmac_sha256(key: bytes, content: str) -> bytes:
    return hmac.new(key, content.encode("utf-8"), hashlib.sha256).digest()


def _hash_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _norm_query(params: dict[str, Any]) -> str:
    query = ""
    for key in sorted(params.keys()):
        if isinstance(params[key], list):
            for value in params[key]:
                query += quote(key, safe="-_.~") + "=" + quote(value, safe="-_.~") + "&"
        else:
            query += quote(key, safe="-_.~") + "=" + quote(str(params[key]), safe="-_.~") + "&"
    return query[:-1].replace("+", "%20") if query else ""


def _utc_now() -> datetime.datetime:
    try:
        from datetime import timezone

        return datetime.datetime.now(timezone.utc)
    except ImportError:
        return datetime.datetime.utcnow()


def _sign_request(method: str, ak: str, sk: str, body: str) -> dict[str, str]:
    now = _utc_now()
    x_date = now.strftime("%Y%m%dT%H%M%SZ")
    short_date = x_date[:8]
    content_sha256 = _hash_sha256(body)
    content_type = "application/json"
    query_params = {"Action": ACTION, "Version": VERSION}

    signed_header_keys = ["content-type", "host", "x-content-sha256", "x-date"]
    signed_headers_str = ";".join(signed_header_keys)
    canonical_headers = "\n".join(
        [
            f"content-type:{content_type}",
            f"host:{HOST}",
            f"x-content-sha256:{content_sha256}",
            f"x-date:{x_date}",
        ]
    )
    canonical_request = "\n".join(
        [
            method.upper(),
            "/",
            _norm_query(query_params),
            canonical_headers,
            "",
            signed_headers_str,
            content_sha256,
        ]
    )

    credential_scope = f"{short_date}/{REGION}/{SERVICE}/request"
    string_to_sign = "\n".join(
        [
            "HMAC-SHA256",
            x_date,
            credential_scope,
            _hash_sha256(canonical_request),
        ]
    )

    k_date = _hmac_sha256(sk.encode("utf-8"), short_date)
    k_region = _hmac_sha256(k_date, REGION)
    k_service = _hmac_sha256(k_region, SERVICE)
    k_signing = _hmac_sha256(k_service, "request")
    signature = _hmac_sha256(k_signing, string_to_sign).hex()
    authorization = (
        f"HMAC-SHA256 Credential={ak}/{credential_scope}, "
        f"SignedHeaders={signed_headers_str}, "
        f"Signature={signature}"
    )

    return {
        "Content-Type": content_type,
        "Host": HOST,
        "X-Date": x_date,
        "X-Content-Sha256": content_sha256,
        "Authorization": authorization,
    }


def _get_credentials() -> tuple[str, str]:
    ak = os.getenv("VOLCENGINE_ACCESS_KEY", "").strip()
    sk = os.getenv("VOLCENGINE_SECRET_KEY", "").strip()
    if not ak or not sk:
        raise ValueError("missing VOLCENGINE_ACCESS_KEY or VOLCENGINE_SECRET_KEY")
    return ak, sk


def _validate_time_range(time_range: str | None) -> str | None:
    if not time_range:
        return None
    if time_range in TIME_RANGE_SHORTCUTS:
        return time_range

    match = DATE_RANGE_PATTERN.match(time_range)
    if not match:
        raise ValueError("--time-range must be OneDay/OneWeek/OneMonth/OneYear or YYYY-MM-DD..YYYY-MM-DD")

    start_text, end_text = match.groups()
    try:
        start_date = datetime.date.fromisoformat(start_text)
        end_date = datetime.date.fromisoformat(end_text)
    except ValueError as exc:
        raise ValueError("--time-range dates must use valid YYYY-MM-DD values") from exc

    if start_date > end_date:
        raise ValueError("--time-range start date must not be later than end date")

    return time_range


def build_body(
    query: str,
    search_type: str = "web",
    count: int = 5,
    sites: str | None = None,
    block_hosts: str | None = None,
    time_range: str | None = None,
    auth_level: int = 0,
) -> dict[str, Any]:
    body: dict[str, Any] = {"Query": query, "SearchType": search_type, "Count": count}

    if search_type == "web":
        body["NeedSummary"] = True
        filters: dict[str, Any] = {}
        if sites:
            filters["Sites"] = sites
        if block_hosts:
            filters["BlockHosts"] = block_hosts
        if auth_level > 0:
            filters["AuthInfoLevel"] = auth_level
        if filters:
            body["Filter"] = filters
        if time_range:
            body["TimeRange"] = time_range

    return body


def do_search(body: dict[str, Any], ak: str, sk: str, timeout: float) -> dict[str, Any]:
    requests = _require_requests()
    body_str = json.dumps(body, ensure_ascii=False)
    headers = _sign_request("POST", ak, sk, body_str)
    url = f"https://{HOST}?Action={ACTION}&Version={VERSION}"
    response = requests.post(url, headers=headers, data=body_str.encode("utf-8"), timeout=timeout)
    response.raise_for_status()
    return response.json()


def format_output(data: dict[str, Any], search_type: str) -> str:
    result = data.get("Result", {})
    lines = [f"结果数: {result.get('ResultCount', 0)}  耗时: {result.get('TimeCost', 0)}ms", ""]

    if search_type == "web":
        for item in result.get("WebResults") or []:
            lines.append(f"[{item.get('SortId', '')}] {item.get('Title', '')}")
            meta_parts = [part for part in [item.get("SiteName", ""), item.get("AuthInfoDes", "")] if part]
            if meta_parts:
                lines.append(f"    {' | '.join(meta_parts)}")
            if item.get("Url"):
                lines.append(f"    {item['Url']}")
            if item.get("PublishTime"):
                lines.append(f"    {item['PublishTime']}")
            summary = item.get("Summary") or item.get("Snippet", "")
            if summary:
                lines.append(f"    {summary[:300]}")
            lines.append("")

    elif search_type == "image":
        for item in result.get("ImageResults") or []:
            image = item.get("Image", {})
            lines.append(f"[{item.get('SortId', '')}] {item.get('Title', '')}")
            if image.get("Url"):
                lines.append(f"    {image['Url']}")
            lines.append(f"    {image.get('Width', '?')}x{image.get('Height', '?')} ({image.get('Shape', '')})")
            lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Volcengine WebSearch API\nhttps://www.volcengine.com/docs/85508/1650263")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--type", "-t", default="web", choices=["web", "image"])
    parser.add_argument("--count", "-c", type=int, default=5)
    parser.add_argument("--time-range", help="OneDay/OneWeek/OneMonth/OneYear/YYYY-MM-DD..YYYY-MM-DD")
    parser.add_argument("--sites", help="Include sites, separated by |")
    parser.add_argument("--block-hosts", help="Blocked hosts, separated by |")
    parser.add_argument("--auth-level", type=int, default=0, choices=[0, 1])
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()

    if args.type == "image" and args.count > 5:
        print("Error: image type supports at most 5 results. Adjust --count.", file=sys.stderr)
        return 1
    if args.type == "web" and args.count > 50:
        print("Error: web type supports at most 50 results. Adjust --count.", file=sys.stderr)
        return 1

    try:
        time_range = _validate_time_range(args.time_range)
        ak, sk = _get_credentials()
        body = build_body(
            query=args.query,
            search_type=args.type,
            count=args.count,
            sites=args.sites,
            block_hosts=args.block_hosts,
            time_range=time_range,
            auth_level=args.auth_level,
        )
        data = do_search(body, ak=ak, sk=sk, timeout=args.timeout)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if data is None:
        print("No response.", file=sys.stderr)
        return 1

    error = (data.get("ResponseMetadata") or {}).get("Error")
    if error:
        print(f"API Error [{error.get('Code')}]: {error.get('Message')}", file=sys.stderr)
        return 1

    print(format_output(data, args.type))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
