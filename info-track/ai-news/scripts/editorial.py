#!/usr/bin/env python3
"""Conservative event grouping and reviewed AI-news composition."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from ai_news import canonical_url, load_json, validate_document


CATEGORIES = (
    ("model_research", "🧠 模型 / 研究"),
    ("agent_tools", "🛠️ Agent / 开发者工具"),
    ("products", "🚀 产品 / 应用"),
    ("business", "💼 商业 / 融资"),
    ("safety_governance", "🛡️ 安全 / 治理"),
)
CATEGORY_LABELS = dict(CATEGORIES)


def normalized_title(title: str) -> str:
    return "".join(re.findall(r"[\w\u4e00-\u9fff]+", title.casefold()))


def identity_url(item: dict) -> str:
    return canonical_url(str(item.get("original_url") or item["url"]))


def title_anchors(item: dict) -> set[str]:
    generic = {"agent", "agents", "ai", "model", "models", "news", "openai", "nvidia", "meta", "google", "anthropic", "microsoft"}
    return {token.casefold() for token in re.findall(r"[A-Za-z][A-Za-z0-9.-]{2,}", str(item.get("title") or ""))
            if token.casefold() not in generic}


def same_event(a: dict, b: dict) -> tuple[bool, str]:
    left_url, right_url = identity_url(a), identity_url(b)
    if left_url and left_url == right_url:
        # Aggregator digest pages can contain several unrelated headlines.
        if a.get("source_role") != "aggregator" or b.get("source_role") != "aggregator":
            return True, "same_original_url"
        if _has_chinese(str(a.get("title") or "")) != _has_chinese(str(b.get("title") or "")):
            if len(title_anchors(a) & title_anchors(b)) >= 2:
                return True, "same_original_url_bilingual"
    ta, tb = normalized_title(str(a["title"])), normalized_title(str(b["title"]))
    if len(ta) < 12 or len(tb) < 12:
        return False, ""
    if ta == tb:
        return True, "same_title"
    return False, ""


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def article_id(item: dict) -> str:
    return "a_" + _digest(canonical_url(str(item["url"])) + "\n" + normalized_title(str(item["title"])))


def _representative(item: dict) -> tuple[int, int, int]:
    role = {"official": 3, "media": 2, "aggregator": 1}.get(item.get("source_role"), 0)
    return role, len(str(item.get("summary") or "")), len(str(item.get("title") or ""))


def _has_chinese(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def _display_member(event: dict) -> dict:
    return max(event["members"], key=lambda m: (
        _has_chinese(str(m.get("title") or "")),
        _has_chinese(str(m.get("summary") or "")),
        *_representative(m),
    ))


def _published_timestamp(event: dict) -> float:
    values = []
    for member in event["members"]:
        try:
            values.append(datetime.fromisoformat(str(member.get("published_at") or "").replace("Z", "+00:00")).timestamp())
        except ValueError:
            continue
    return max(values, default=0)


def short_summary(value: str) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    text = re.sub(r"^\d+[.、．]\s*", "", text)
    text = re.sub(r"^arXiv:\S+\s+Announce Type:\s*\w+\s+Abstract:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+来源[:：]\s*[^。！？]*$", "", text).strip()
    if not text:
        return ""
    chinese = _has_chinese(text)
    limit = 100 if chinese else 180
    truncated = text.endswith(("...", "…"))
    complete_part = text[:-3] if text.endswith("...") else text[:-1] if text.endswith("…") else text
    sentence_end = re.search(r"[。！？]" if chinese else r"[.!?](?=\s+[A-Z]|$)", complete_part)
    if sentence_end and sentence_end.end() <= limit:
        return complete_part[:sentence_end.end()].strip()
    if len(text) <= limit and not truncated:
        return text
    return ""


def markdown_link(label: str, url: str) -> str:
    destination = f"<{url}>" if any(mark in url for mark in "() ") else url
    return f"[{label}]({destination})"


def prepare_document(document: dict) -> dict:
    errors = validate_document(document)
    if errors:
        raise ValueError("invalid candidate document: " + "; ".join(errors))
    items = document["candidates"]
    parent = list(range(len(items)))
    links: list[dict] = []

    def root(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for i, a in enumerate(items):
        for j in range(i):
            b = items[j]
            matched, reason = same_event(a, b)
            if matched:
                ai, bj = root(i), root(j)
                if ai != bj:
                    parent[ai] = bj
                links.append({"articles": [article_id(a), article_id(b)], "reason": reason})

    groups: dict[int, list[dict]] = {}
    for index, item in enumerate(items):
        groups.setdefault(root(index), []).append({"article_id": article_id(item), **item})

    events = []
    for members in groups.values():
        members.sort(key=_representative, reverse=True)
        identity = min(member["article_id"] for member in members)
        roles = {m.get("source_role") for m in members}
        direct_sources = {m.get("source_id") for m in members if m.get("source_role") != "aggregator"}
        priority = (3 if "official" in roles else 2 if "media" in roles else 1) + min(len(direct_sources) - 1, 2) if direct_sources else 1
        event = {
            "event_id": "e_" + _digest(identity),
            "review_priority": priority,
            "representative_article_id": members[0]["article_id"],
            "members": members,
            "review": {"decision": "pending", "category": "", "title_zh": "", "summary_zh": "", "verified_url": ""},
        }
        events.append(event)
    events.sort(key=lambda e: (-e["review_priority"], e["event_id"]))
    return {
        "window": document["window"],
        "sources": document["sources"],
        "diagnostics": {**document.get("diagnostics", {}), "event_count": len(events), "grouped_rows": len(items) - len(events)},
        "group_links": links,
        "events": events,
    }


def merge_reviewed_events(document: dict, pairs: list[list[str]]) -> dict:
    """Apply explicit same-event judgments before editorial decisions."""
    by_id = {event["event_id"]: event for event in document["events"]}
    for pair in pairs:
        if not isinstance(pair, list) or len(pair) != 2 or pair[0] == pair[1]:
            raise ValueError("each manual merge must name two different event IDs")
        left, right = (by_id.get(name) for name in pair)
        if left is None or right is None:
            raise ValueError(f"unknown event in manual merge: {pair}")
        if any(event["review"]["decision"] != "pending" for event in (left, right)):
            raise ValueError("manual merge must happen before editorial decisions")
        if left is right:
            continue
        existing = {member["article_id"] for member in left["members"]}
        left["members"].extend(member for member in right["members"] if member["article_id"] not in existing)
        left["members"].sort(key=_representative, reverse=True)
        left["representative_article_id"] = left["members"][0]["article_id"]
        left["review_priority"] = max(left["review_priority"], right["review_priority"])
        document["group_links"].append({"events": pair, "reason": "manual_same_event"})
        del by_id[right["event_id"]]
        for key, event in list(by_id.items()):
            if event is right:
                by_id[key] = left
    document["events"] = list({id(event): event for event in by_id.values()}.values())
    document["diagnostics"]["event_count"] = len(document["events"])
    document["diagnostics"]["grouped_rows"] = sum(len(e["members"]) - 1 for e in document["events"])
    return document


def _reviewed(event: dict) -> dict | None:
    review = event.get("review") or {}
    decision = review.get("decision")
    if decision != "select":
        return None
    missing = [key for key in ("category", "title_zh", "summary_zh", "verified_url") if not review.get(key)]
    if missing:
        raise ValueError(f"{event.get('event_id')}: selected event missing {', '.join(missing)}")
    category = str(review["category"])
    if category not in CATEGORY_LABELS:
        label = str(review.get("category_label") or "")
        if not re.fullmatch(r"[a-z][a-z0-9_]{1,39}", category) or not label or len(label) > 60 or "\n" in label:
            raise ValueError(f"{event.get('event_id')}: custom category needs a safe key and category_label")
    valid_urls = {str(m.get(k) or "") for m in event["members"] for k in ("url", "original_url")}
    if review["verified_url"] not in valid_urls:
        raise ValueError(f"{event.get('event_id')}: verified_url is not a member link")
    checked = urlsplit(review["verified_url"])
    if checked.scheme not in {"http", "https"} or not checked.netloc:
        raise ValueError(f"{event.get('event_id')}: verified_url is not HTTP(S)")
    return review


def render_report(document: dict, *, allow_partial: bool = False, category_level: int = 2) -> str:
    invalid = [e["event_id"] for e in document["events"] if (e.get("review") or {}).get("decision") not in {"pending", "select", "reject"}]
    if invalid:
        raise ValueError("invalid review decision in " + ", ".join(invalid))
    pending = sum((e.get("review") or {}).get("decision") == "pending" for e in document["events"])
    if pending and not allow_partial:
        raise ValueError("unreviewed events remain; set decision to select or reject")
    label = document["window"].get("date") or document["window"]["label"]
    sections: dict[str, list[str]] = {}
    headings: dict[str, str] = dict(CATEGORIES)
    for event in document["events"]:
        review = _reviewed(event)
        if not review:
            continue
        verified = review["verified_url"]
        matching = next(m for m in event["members"] if verified in (m.get("url"), m.get("original_url")))
        if matching.get("original_url") and verified == matching["original_url"]:
            source_line = "来源链接：" + markdown_link("原文", verified) + " · " + markdown_link("AIHOT 条目", matching["url"])
        elif matching.get("original_url") and verified == matching["url"]:
            source_line = "来源链接：" + markdown_link("AIHOT 条目", verified) + " · " + markdown_link("第三方原文", matching["original_url"])
        else:
            source_line = "来源链接：" + markdown_link("原文", verified)
        category = str(review["category"])
        headings[category] = CATEGORY_LABELS.get(category, str(review.get("category_label")))
        summary = short_summary(str(review["summary_zh"]))
        if not summary:
            raise ValueError(f"{event.get('event_id')}: selected summary needs one complete short sentence")
        sections.setdefault(category, []).append(
            f"{'#' * (category_level + 1)} {review['title_zh']}\n摘要：{summary}\n{source_line}"
        )
    lines = [f"# AI 新闻简报{'样例' if pending else ''}｜{label}"]
    if pending:
        lines.extend(["", f"尚有 {pending} 个事件未审核；本样例只展示已核验的入选事件，不代表完整简报。"])
    for key in [*CATEGORY_LABELS, *(key for key in sections if key not in CATEGORY_LABELS)]:
        if key not in sections:
            continue
        heading = headings[key]
        lines.extend(["", f"{'#' * category_level} {heading}", ""])
        lines.append("\n\n".join(sections[key]))
    return "\n".join(lines).rstrip() + "\n"


PENDING_EXTRA_CATEGORIES = (
    ("science", "🔬 AI 科研 / 医疗", r"生物|医疗|医院|疾病|疫苗|蛋白|基因|数学|庞加莱|科学发现|\b(?:crispr|biolog\w*|clinical|medical|hospital|protein|vaccine|math\w*|scientific|discovery)\b"),
    ("hardware", "🧩 芯片 / 算力", r"芯片|算力|半导体|显卡|张量|能效|晶圆|CoWoS|\b(?:GPU|DPU|NPU|semiconductor|chip|tensor|compute)\b"),
    ("robotics", "🤖 机器人 / 具身智能", r"机器人|具身|自动驾驶|\b(?:VLA|robot\w*|driving)\b"),
    ("evaluation", "📊 评测 / 基准", r"评测|基准|准确率|榜单|排名|量化对比|\b(?:Arena|benchmark\w*|accuracy|leaderboard|evaluation)\b"),
    ("opensource", "🧰 开源 / 项目", r"开源|星标|代码库|\b(?:GitHub|open.source|repository)\b"),
    ("safety_governance", "🛡️ 安全 / 治理", r"安全|漏洞|攻击|越狱|隐私|泄露|注入|蠕虫|失控|终止开关|风险|末日论|人类全灭|披露|未提|信任危机|\b(?:safety|security|privacy|cyber|hack\w*|rogue|threat|dangerous|extinction|surveillance)\b"),
    ("policy", "⚖️ 政策 / 法律", r"政府|国会|法院|参议院|听证|政策|法律|法案|监管|诉讼|审批|条款|抗议|\b(?:government|senate|court|lawsuit|sued|regulation|treaty|congress|border|protest\w*|democrat)\b"),
    ("business", "💼 商业 / 融资", r"融资|收购|估值|上市|招股|募资|协议|投资|美元|\b(?:IPO|acquir\w*|funding|raises?|valuation|investment|transactions?|startups?|support|expense)\b"),
    ("enterprise", "🏢 企业 / 办公", r"企业|办公|工作流|组织|Excel|病历|\b(?:enterprise|workplace|office|business|workbook|productivity|collaboration)\b"),
    ("creative", "🎨 创作 / 媒体", r"视频|音乐|游戏|动画|创作|影像|相册|\b(?:video|music|gaming|trailer|film|camera.roll|photo)\b"),
    ("analysis", "📚 技术解读 / 观点", r"教程|指南|解读|详解|综述|评论|观点|专访|复盘|实测|呼吁|争论|为何|\b(?:guide|tutorial|analysis|opinion|review|interview|framework|why|roundtables)\b"),
)
PENDING_LABELS = {**CATEGORY_LABELS, **{key: label for key, label, _ in PENDING_EXTRA_CATEGORIES}, "other": "📰 其他动态"}


def _pending_category(event: dict) -> tuple[str, str]:
    review = event.get("review") or {}
    key = str(review.get("category") or "")
    if key:
        label = PENDING_LABELS.get(key) or str(review.get("category_label") or "")
        if label:
            return key, label
    title = _pending_title(event, _display_member(event))
    for key, label, pattern in PENDING_EXTRA_CATEGORIES:
        if re.search(pattern, title, re.IGNORECASE):
            return key, label
    source_url = urlsplit(str(_display_member(event).get("original_url") or _display_member(event).get("url") or ""))
    if source_url.netloc.casefold() in {"github.com", "www.github.com"}:
        return "opensource", PENDING_LABELS["opensource"]
    for key, label, pattern in (
        ("agent_tools", CATEGORY_LABELS["agent_tools"], r"智能体|代理|开发|编程|代码|工具链|调度层|\b(?:agent\w*|Codex|MCP|SDK|API|router|copilot)\b"),
        ("model_research", CATEGORY_LABELS["model_research"], r"模型|研究|推理|训练|建模|\b(?:model\w*|LLM|research|planning|inference)\b"),
        ("products", CATEGORY_LABELS["products"], r"产品|应用|上线|推出|发布|更新|升级|购物|结账|照片|玩具|截图|\b(?:app|launch|release|updating|checkout|platform|grokipedia)\b"),
    ):
        if re.search(pattern, title, re.IGNORECASE):
            return key, label
    return "other", PENDING_LABELS["other"]


def _pending_title(event: dict, member: dict) -> str:
    review = event.get("review") or {}
    title = str(review.get("display_title") or member.get("title") or "").replace("\n", " ").strip()
    if review.get("display_title"):
        return title
    url = urlsplit(str(member.get("original_url") or member.get("url") or ""))
    if url.netloc.casefold() in {"github.com", "www.github.com"}:
        parts = url.path.strip("/").split("/")
        if len(parts) >= 2 and normalized_title(parts[1]) not in normalized_title(title):
            return f"{parts[1]}：{title}"
    return title


def summary_queue(document: dict) -> list[dict]:
    """List events that still need a source-backed editorial summary."""
    queue = []
    for event in document["events"]:
        review = event.get("review") or {}
        if review.get("decision") in {"reject", "select"}:
            continue
        member = _display_member(event)
        summary = str(review.get("display_summary") or "")
        source_url = str(review.get("display_summary_source_url") or "")
        valid_urls = {str(source.get(key) or "") for source in event["members"] for key in ("url", "original_url")}
        if summary and short_summary(summary) == summary.strip() and source_url in valid_urls:
            continue
        sources_by_url: dict[str, dict] = {}
        for source in event["members"]:
            url = str(source.get("original_url") or source.get("url") or "")
            collected = str(source.get("summary") or "")
            identity = canonical_url(url)
            prior = sources_by_url.get(identity)
            if prior is None or len(collected) > len(prior["collected_summary"]):
                sources_by_url[identity] = {
                    "url": url,
                    "collected_summary": collected,
                    "complete_excerpt": short_summary(collected),
                }
        queue.append({
            "event_id": event["event_id"],
            "title": str(review.get("title_zh") or _pending_title(event, member)),
            "sources": list(sources_by_url.values()),
        })
    return queue


def render_all_events(document: dict) -> str:
    """Render every non-rejected event in one consistent public layout."""
    events = [e for e in document["events"] if (e.get("review") or {}).get("decision") != "reject"]
    invalid = [e["event_id"] for e in events if (e.get("review") or {}).get("decision") not in {"pending", "select"}]
    if invalid:
        raise ValueError("invalid review decision in " + ", ".join(invalid))
    label = document["window"].get("date") or document["window"]["label"]
    lines = [f"# AI 新闻简报｜{label}", "", f"收录 {len(events)} 条资讯；同一事件的中英文报道合在一条，各栏目中文资讯靠前。"]
    groups: dict[str, list[tuple[dict, str, str, str]]] = {}
    headings: dict[str, str] = dict(PENDING_LABELS)
    missing: list[str] = []
    uncategorized: list[str] = []
    for event in events:
        review = _reviewed(event)
        member = _display_member(event)
        if review:
            title = str(review["title_zh"])
            summary = short_summary(str(review["summary_zh"]))
            key = str(review["category"])
            headings[key] = CATEGORY_LABELS.get(key, str(review.get("category_label")))
        else:
            title = _pending_title(event, member)
            display_summary = str((event.get("review") or {}).get("display_summary") or "")
            if display_summary:
                source_url = str((event.get("review") or {}).get("display_summary_source_url") or "")
                valid_urls = {str(source.get(key) or "") for source in event["members"] for key in ("url", "original_url")}
                if source_url not in valid_urls or not source_url:
                    raise ValueError(f"{event['event_id']}: display_summary_source_url must be a member link")
            summary = short_summary(display_summary)
            if summary != display_summary.strip():
                summary = ""
            key, category_label = _pending_category(event)
            headings[key] = category_label
            if key == "other":
                uncategorized.append(event["event_id"])
        if not summary:
            missing.append(event["event_id"])
        groups.setdefault(key, []).append((event, title, summary, str(review["verified_url"]) if review else ""))
    if missing:
        raise ValueError("source-backed editorial summaries required for: " + ", ".join(missing))
    if uncategorized:
        raise ValueError("category review required for: " + ", ".join(uncategorized))
    for key in [*PENDING_LABELS, *(key for key in groups if key not in PENDING_LABELS)]:
        rows = groups.get(key)
        if not rows:
            continue
        rows.sort(key=lambda row: (not _has_chinese(row[1]), (row[0].get("review") or {}).get("decision") != "select", -_published_timestamp(row[0]), row[0]["event_id"]))
        lines.extend(["", f"## {headings[key]}（{len(rows)}）"])
        for event, title, summary, verified_url in rows:
            links: list[str] = []
            seen: set[str] = set()
            if verified_url:
                seen.add(canonical_url(verified_url))
                links.append(markdown_link("原文", verified_url))
            for source in event["members"]:
                for url, name in ((source.get("original_url"), source.get("original_source") or "原文"),
                                  (source.get("url"), source.get("source") or source.get("source_id") or "来源")):
                    url = str(url or "")
                    if not url or canonical_url(url) in seen:
                        continue
                    seen.add(canonical_url(url))
                    if source.get("source_id") == "hex2077" and urlsplit(url).netloc.casefold() in {"github.com", "www.github.com"}:
                        name = "GitHub 项目（Hex 2077 收录）"
                    links.append(markdown_link(str(name), url))
            lines.extend(["", f"### {title}", f"摘要：{summary}", "来源链接：" + " · ".join(links)])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Group news candidates and compose a reviewed brief.")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--input", type=Path, required=True)
    prepare.add_argument("--out", type=Path, required=True)
    merge = sub.add_parser("merge")
    merge.add_argument("--input", type=Path, required=True)
    merge.add_argument("--pairs", type=Path, required=True, help="JSON array of [event_id, event_id] pairs")
    merge.add_argument("--out", type=Path, required=True)
    queue = sub.add_parser("summary-queue")
    queue.add_argument("--input", type=Path, required=True)
    queue.add_argument("--out", type=Path)
    queue.add_argument("--limit", type=int, default=25)
    queue.add_argument("--offset", type=int, default=0)
    render = sub.add_parser("render")
    render.add_argument("--input", type=Path, required=True)
    render.add_argument("--out", type=Path)
    render.add_argument("--allow-partial", action="store_true", help="Render a labeled validation sample with pending events")
    render.add_argument("--all-events", action="store_true", help="Keep all non-rejected events and list all member sources")
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare_document(load_json(args.input))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif args.command == "merge":
        pairs = json.loads(args.pairs.read_text(encoding="utf-8"))
        if not isinstance(pairs, list):
            raise ValueError("manual merge pairs must be a JSON array")
        result = merge_reviewed_events(load_json(args.input), pairs)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif args.command == "summary-queue":
        if args.limit < 1 or args.offset < 0:
            raise ValueError("summary-queue requires --limit >= 1 and --offset >= 0")
        items = summary_queue(load_json(args.input))
        result = json.dumps({"total": len(items), "offset": args.offset, "items": items[args.offset:args.offset + args.limit]}, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(result, encoding="utf-8")
        else:
            print(result, end="")
    else:
        document = load_json(args.input)
        report = render_all_events(document) if args.all_events else render_report(document, allow_partial=args.allow_partial)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(report, encoding="utf-8")
        else:
            print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
