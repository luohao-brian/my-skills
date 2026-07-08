#!/usr/bin/env python3
"""Ark Agent Plan WebSearch API client using API key authentication only."""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import textwrap
from typing import Any

ENDPOINT = "https://open.feedcoopapi.com/search_api/web_search"
TIME_RANGE_SHORTCUTS = {"OneDay", "OneWeek", "OneMonth", "OneYear"}
DATE_RANGE_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})$")


def _require_requests():
    try:
        import requests
    except ImportError:
        print("Error: requests not installed. Run: pip install requests", file=sys.stderr)
        sys.exit(1)
    return requests


def _get_api_key() -> str:
    api_key = os.getenv("ARK_AGENT_PLAN_API_KEY", "").strip()
    if not api_key:
        raise ValueError("missing ARK_AGENT_PLAN_API_KEY")
    return api_key


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
    count: int = 10,
    sites: str | None = None,
    block_hosts: str | None = None,
    time_range: str | None = None,
    auth_level: int = 0,
    need_content: bool = False,
    need_url: bool = False,
    query_rewrite: bool = False,
    need_summary: bool = True,
) -> dict[str, Any]:
    body: dict[str, Any] = {"Query": query, "SearchType": search_type, "Count": count}
    filters: dict[str, Any] = {}

    if query_rewrite:
        filters["QueryRewrite"] = True

    if search_type == "web":
        if need_summary:
            body["NeedSummary"] = True
        if need_content:
            filters["NeedContent"] = True
        if need_url:
            filters["NeedUrl"] = True
        if sites:
            filters["Sites"] = sites
        if block_hosts:
            filters["BlockHosts"] = block_hosts
        if auth_level > 0:
            filters["AuthInfoLevel"] = auth_level
        if time_range:
            body["TimeRange"] = time_range

    if filters:
        body["Filter"] = filters

    return body


def do_search(body: dict[str, Any], api_key: str, timeout: float) -> dict[str, Any]:
    requests = _require_requests()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.post(ENDPOINT, headers=headers, json=body, timeout=timeout)
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
    parser = argparse.ArgumentParser(
        description="Search with Ark Agent Plan. Use web for cited text evidence and image only for image results.",
        epilog=textwrap.dedent(
            """\
            Examples:
              web evidence:   web_search.py "OpenAI latest release" --time-range OneWeek --count 5 --need-url
              deeper context: web_search.py "北京旅游攻略" --need-content --need-url
              trusted sites:  web_search.py "豆包搜索 API" --sites "volcengine.com" --auth-level 1
              image search:   web_search.py "OpenAI logo" --type image --count 3
            """
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", help="Focused search text, ideally 1 to 100 characters.")
    parser.add_argument("--type", "-t", default="web", choices=["web", "image"], help="Use web for textual evidence; use image only for image results.")
    parser.add_argument("--count", "-c", type=int, help="Number of results. Defaults: web=10, image=5. Limits: web<=50, image<=5.")
    parser.add_argument("--time-range", help="Web-only publish-time filter: OneDay, OneWeek, OneMonth, OneYear, or YYYY-MM-DD..YYYY-MM-DD.")
    parser.add_argument("--sites", help="Web-only allowlist of complete domains separated by |, for example volcengine.com|openai.com.")
    parser.add_argument("--block-hosts", help="Web-only blocklist of complete domains separated by |.")
    parser.add_argument("--auth-level", type=int, default=0, choices=[0, 1], help="Web-only authority filter. Use 1 for very authoritative sources.")
    parser.add_argument("--need-content", action="store_true", help="Web-only. Require results with page Content for deeper evidence.")
    parser.add_argument("--need-url", action="store_true", help="Web-only. Require original URLs for citation-ready results.")
    parser.add_argument("--query-rewrite", action="store_true", help="Ask the provider to rewrite the query when recall matters more than latency.")
    parser.add_argument("--no-summary", action="store_true", help="Web-only. Skip requesting Summary; useful when snippets are enough.")
    parser.add_argument("--timeout", type=float, default=30, help="HTTP timeout in seconds.")
    args = parser.parse_args()

    count = args.count
    if count is None:
        count = 5 if args.type == "image" else 10

    if count < 1:
        print("Error: --count must be at least 1.", file=sys.stderr)
        return 1
    if args.type == "image" and count > 5:
        print("Error: image type supports at most 5 results. Adjust --count.", file=sys.stderr)
        return 1
    if args.type == "web" and count > 50:
        print("Error: web type supports at most 50 results. Adjust --count.", file=sys.stderr)
        return 1
    if args.type == "image" and (args.need_content or args.need_url or args.sites or args.block_hosts or args.auth_level):
        print("Error: --need-content/--need-url/--sites/--block-hosts/--auth-level are web-only parameters.", file=sys.stderr)
        return 1
    if args.type == "image" and args.time_range:
        print("Error: --time-range is a web-only parameter.", file=sys.stderr)
        return 1

    try:
        time_range = _validate_time_range(args.time_range)
        api_key = _get_api_key()
        body = build_body(
            query=args.query,
            search_type=args.type,
            count=count,
            sites=args.sites,
            block_hosts=args.block_hosts,
            time_range=time_range,
            auth_level=args.auth_level,
            need_content=args.need_content,
            need_url=args.need_url,
            query_rewrite=args.query_rewrite,
            need_summary=not args.no_summary,
        )
        data = do_search(body, api_key=api_key, timeout=args.timeout)
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
