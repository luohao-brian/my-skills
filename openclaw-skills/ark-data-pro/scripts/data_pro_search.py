#!/usr/bin/env python3
"""Direct HTTP client for Ark Agent Plan professional datasets."""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from typing import Any

ENDPOINT = "https://datapro.hqd.cn-beijing.volces.com/mcp"
TOOL_NAME = "dataPro_search"
CATEGORY_PREFIXES = {
    "finance": "金融数据库 ",
    "enterprise-info": "企业工商数据库 ",
    "enterprise-risk": "企业风险数据库 ",
    "academic": "科研学术数据搜索 ",
}


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


def _post_json_rpc(payload: dict[str, Any], api_key: str, timeout: float) -> dict[str, Any]:
    requests = _require_requests()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "X-Agent-Plan-Key": api_key,
    }
    response = requests.post(ENDPOINT, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def build_query(query: str, category: str) -> str:
    prefix = CATEGORY_PREFIXES[category]
    if not prefix:
        return query
    if query.startswith(prefix.strip()):
        return query
    return f"{prefix}{query}"


def call_data_pro(query: str, api_key: str, timeout: float, category: str) -> dict[str, Any]:
    routed_query = build_query(query, category)
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": TOOL_NAME,
            "arguments": {"query": routed_query},
        },
    }
    return _post_json_rpc(payload, api_key=api_key, timeout=timeout)


def extract_tool_payload(response: dict[str, Any], requested_category: str) -> dict[str, Any]:
    if response.get("error"):
        error = response["error"]
        raise ValueError(f"JSON-RPC Error [{error.get('code')}]: {error.get('message')}")

    result = response.get("result") or {}
    if isinstance(result.get("structuredContent"), dict):
        payload = result["structuredContent"]
        payload.setdefault("requested_category", requested_category)
        return payload

    for item in result.get("content") or []:
        if item.get("type") != "text":
            continue
        text = item.get("text", "")
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {"code": 0, "msg": "success", "text": text}
        if isinstance(parsed, dict):
            parsed.setdefault("requested_category", requested_category)
            return parsed

    return {"code": 0, "msg": "success", "requested_category": requested_category, "result": result}


def format_payload(payload: dict[str, Any]) -> str:
    lines = [
        f"code: {payload.get('code')}",
        f"msg: {payload.get('msg')}",
        f"requested_category: {payload.get('requested_category', '')}",
        f"dataset_type: {payload.get('dataset_type', '')}",
        f"trace_id: {payload.get('trace_id', '')}",
    ]

    items = payload.get("items")
    if isinstance(items, list):
        lines.append(f"items: {len(items)}")
        for index, item in enumerate(items[:5], 1):
            lines.append("")
            lines.append(f"[{index}]")
            if isinstance(item, dict):
                for key, value in item.items():
                    if key in {"records", "table"} and isinstance(value, (list, dict)):
                        lines.append(f"  {key}: {len(value)} entries")
                    else:
                        rendered = json.dumps(value, ensure_ascii=False)
                        if len(rendered) > 500:
                            rendered = rendered[:500] + "..."
                        lines.append(f"  {key}: {rendered}")
            else:
                rendered = json.dumps(item, ensure_ascii=False)
                lines.append(f"  {rendered[:500]}")
    elif "text" in payload:
        lines.append("")
        lines.append(str(payload["text"]))

    hint = payload.get("hint")
    if hint:
        lines.extend(["", f"hint: {hint}"])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Query Ark Agent Plan professional datasets through direct HTTP JSON-RPC.",
        epilog=textwrap.dedent(
            """\
            Examples:
              finance:    data_pro_search.py "比亚迪 ROE 盈利水平" --category finance
              enterprise: data_pro_search.py "北京字节跳动科技有限公司 注册资本 经营范围" --category enterprise-info
              risk:       data_pro_search.py "某某有限公司 是否为失信被执行人 司法诉讼" --category enterprise-risk
              academic:   data_pro_search.py "大语言模型 检索增强生成 2025 综述 论文" --category academic
            """
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", help="Natural-language query with explicit company, stock code, paper topic, or dataset intent.")
    parser.add_argument(
        "--category",
        choices=sorted(CATEGORY_PREFIXES),
        required=True,
        help="Required dataset routing hint.",
    )
    parser.add_argument("--timeout", type=float, default=120, help="HTTP timeout in seconds.")
    parser.add_argument("--raw", action="store_true", help="Print the full parsed tool payload as JSON.")
    args = parser.parse_args()

    try:
        api_key = _get_api_key()
        response = call_data_pro(args.query, api_key=api_key, timeout=args.timeout, category=args.category)
        payload = extract_tool_payload(response, requested_category=args.category)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.raw:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_payload(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
