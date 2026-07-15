#!/usr/bin/env python3
"""Browser-accurate SVG layout audit for PPT Master projects.

Checks authored ``svg_output/*.svg`` through the same preview API used by the
editor. The audit is deterministic: it measures rendered SVG geometry in
Chromium at several viewport sizes and writes a JSON report.

Exit codes:
    0  no blocking errors (warnings may remain)
    1  one or more blocking layout/style errors
    2  invalid input or preview-server failure
    3  Playwright/browser unavailable
"""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


DEFAULT_VIEWPORTS = ((1280, 720), (1024, 768), (1440, 900), (720, 1280))
MAX_ISSUES_PER_CODE = 30


def _stderr(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _read_json(url: str, timeout: float = 3.0) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _wait_ready(url: str, process: subprocess.Popen[bytes], timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"preview server exited with code {process.returncode}")
        try:
            payload = _read_json(f"{url}/api/health")
            if payload.get("status") == "ok":
                return
        except (OSError, ValueError, urllib.error.URLError) as exc:
            last_error = exc
        time.sleep(0.15)
    raise RuntimeError(f"preview server did not become ready: {last_error}")


@contextmanager
def preview_server(project: Path, supplied_url: str | None) -> Iterator[str]:
    if supplied_url:
        url = supplied_url.rstrip("/")
        try:
            health = _read_json(f"{url}/api/health")
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"preview server unreachable at {url}: {exc}") from exc
        server_project = Path(str(health.get("project") or "")).resolve()
        if server_project != project.resolve():
            raise RuntimeError(
                f"preview server serves {server_project}, expected {project.resolve()}"
            )
        yield url
        return

    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    server_script = Path(__file__).resolve().parent / "svg_editor" / "server.py"
    command = [
        sys.executable,
        str(server_script),
        str(project),
        "--port",
        str(port),
        "--no-browser",
    ]
    process = subprocess.Popen(  # noqa: S603 - fixed local script + validated args
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_ready(url, process)
        yield url
    finally:
        try:
            request = urllib.request.Request(
                f"{url}/api/shutdown",
                data=b'{"reason":"layout-audit-complete"}',
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(request, timeout=1.5).read()
        except Exception:  # noqa: BLE001 - termination fallback below
            pass
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()


def _parse_viewports(raw: str) -> list[tuple[int, int]]:
    viewports: list[tuple[int, int]] = []
    for token in raw.split(","):
        parts = token.lower().strip().split("x")
        if len(parts) != 2:
            raise ValueError(f"invalid viewport {token!r}; expected WIDTHxHEIGHT")
        width, height = (int(value) for value in parts)
        if width < 320 or height < 320:
            raise ValueError(f"viewport too small: {width}x{height}")
        viewports.append((width, height))
    return viewports


def _launch_browser(playwright: Any) -> Any:
    attempts: list[str] = []
    for kwargs in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
        label = kwargs.get("channel", "playwright-chromium")
        try:
            return playwright.chromium.launch(**kwargs)
        except Exception as exc:  # noqa: BLE001
            attempts.append(f"{label}: {exc}")
    raise RuntimeError("; ".join(attempts))


INJECT_AND_AUDIT_JS = r"""
async ({pageName, minWidthUse, minHeightUse}) => {
  const response = await fetch('/api/slide/' + encodeURIComponent(pageName) + '?_=' + Date.now());
  if (!response.ok) throw new Error('slide fetch failed: HTTP ' + response.status);
  const payload = await response.json();
  document.documentElement.innerHTML = `
    <head><style>
      *{box-sizing:border-box}
      html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#17191d}
      #stage{width:100vw;height:100vh;display:grid;place-items:center;overflow:hidden}
      #stage>svg{display:block;width:100%;height:100%;max-width:100%;max-height:100%}
    </style></head><body><main id="stage">${payload.content}</main></body>`;
  await document.fonts.ready;
  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));

  const svg = document.querySelector('#stage > svg');
  if (!svg) throw new Error('preview did not contain a root SVG');
  const viewBox = svg.viewBox && svg.viewBox.baseVal;
  if (!viewBox || !(viewBox.width > 0) || !(viewBox.height > 0)) {
    throw new Error('root SVG has no positive viewBox');
  }
  const ns = 'http://www.w3.org/2000/svg';
  const tag = el => (el.localName || '').toLowerCase();
  const finiteRect = r => [r.x,r.y,r.width,r.height].every(Number.isFinite);
  const area = r => Math.max(0,r.width) * Math.max(0,r.height);
  const intersection = (a,b) => {
    const x1=Math.max(a.x,b.x), y1=Math.max(a.y,b.y);
    const x2=Math.min(a.x+a.width,b.x+b.width), y2=Math.min(a.y+a.height,b.y+b.height);
    return {x:x1,y:y1,width:Math.max(0,x2-x1),height:Math.max(0,y2-y1)};
  };
  const contains = (outer, inner, tolerance=1) =>
    inner.x >= outer.x-tolerance && inner.y >= outer.y-tolerance &&
    inner.x+inner.width <= outer.x+outer.width+tolerance &&
    inner.y+inner.height <= outer.y+outer.height+tolerance;
  const selector = el => {
    if (el.id) return '#' + el.id;
    const parent = el.parentElement;
    if (!parent) return tag(el);
    const siblings = [...parent.children].filter(node => tag(node) === tag(el));
    return `${parent.id ? '#'+parent.id : tag(parent)} > ${tag(el)}:nth-of-type(${siblings.indexOf(el)+1})`;
  };
  const textLabel = el => (el.textContent || '').replace(/\s+/g,' ').trim().slice(0,80);
  const visible = el => {
    if (!(el instanceof SVGGraphicsElement)) return false;
    if (el.closest('defs,clipPath,mask,pattern,marker,symbol')) return false;
    const style = getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    const opacity = Number.parseFloat(style.opacity || '1');
    return Number.isFinite(opacity) && opacity > 0.001;
  };
  const rootMatrix = svg.getScreenCTM();
  if (!rootMatrix) throw new Error('root SVG has no screen transform');
  const rootInverse = rootMatrix.inverse();
  const rootBox = el => {
    let box, matrix;
    try { box = el.getBBox(); matrix = el.getScreenCTM(); } catch { return null; }
    if (!box || !matrix || !finiteRect(box)) return null;
    const points = [
      new DOMPoint(box.x, box.y), new DOMPoint(box.x+box.width, box.y),
      new DOMPoint(box.x+box.width, box.y+box.height), new DOMPoint(box.x, box.y+box.height)
    ].map(p => p.matrixTransform(matrix).matrixTransform(rootInverse));
    const xs=points.map(p=>p.x), ys=points.map(p=>p.y);
    return {x:Math.min(...xs),y:Math.min(...ys),width:Math.max(...xs)-Math.min(...xs),height:Math.max(...ys)-Math.min(...ys)};
  };
  const screenBox = el => {
    const r = el.getBoundingClientRect();
    return {x:r.x,y:r.y,width:r.width,height:r.height};
  };
  const graphics = [...svg.querySelectorAll('*')].filter(visible);
  const records = graphics.map(el => ({el, tag:tag(el), selector:selector(el), root:rootBox(el), screen:screenBox(el)}))
    .filter(rec => rec.root && rec.screen && finiteRect(rec.root) && finiteRect(rec.screen));
  const issues = [];
  const push = (severity, code, rec, detail, extra={}) => issues.push({severity,code,element:rec ? rec.selector : null,detail,...extra});
  const canvas = {x:viewBox.x,y:viewBox.y,width:viewBox.width,height:viewBox.height};
  const viewport = {x:0,y:0,width:innerWidth,height:innerHeight};

  if (svg.querySelector('style')) push('error','forbidden_style_element',null,'SVG contains <style>; use inline attributes');
  for (const el of [svg, ...svg.querySelectorAll('[class]')].filter(el => el.hasAttribute('class'))) {
    push('error','forbidden_class', {selector:selector(el)}, 'SVG class attributes are outside the inline-style contract');
  }

  for (const rec of records) {
    const isContainer = rec.tag === 'g' || rec.tag === 'svg';
    if (!isContainer && !contains(canvas, rec.root, 1.25)) {
      push('error','canvas_overflow',rec,`bbox ${JSON.stringify(rec.root)} exceeds viewBox ${JSON.stringify(canvas)}`);
    }
    if (!isContainer && !contains(viewport, rec.screen, 1.25)) {
      push('error','viewport_overflow',rec,`rendered bbox ${JSON.stringify(rec.screen)} exceeds ${innerWidth}x${innerHeight}`);
    }
    if (['text','image','use'].includes(rec.tag) && (rec.root.width < 0.1 || rec.root.height < 0.1)) {
      push('error','zero_size_render',rec,`${rec.tag} rendered with near-zero bounds`);
    }
  }

  const texts = records.filter(rec => rec.tag === 'text' && (rec.el.textContent || '').trim());
  for (let i=0; i<texts.length; i++) {
    for (let j=i+1; j<texts.length; j++) {
      const a=texts[i], b=texts[j];
      if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
      const hit=intersection(a.root,b.root);
      if (hit.width > 1.5 && hit.height > 1.5 && area(hit) > 4) {
        const ratio=area(hit)/Math.max(1,Math.min(area(a.root),area(b.root)));
        if (ratio > 0.015) {
          const severity=ratio > 0.08 ? 'error' : 'warning';
          push(severity,'text_overlap',a,`"${textLabel(a.el)}" overlaps "${textLabel(b.el)}" (${b.selector}); intersection ratio ${ratio.toFixed(3)}`,{other:b.selector});
        }
      }
    }
  }

  const containerPattern = /(card|panel|tile|container|callout|takeaway|kpi|metric|step|column|box)/i;
  for (const group of [...svg.querySelectorAll('g[id]')].filter(el => containerPattern.test(el.id))) {
    const directRects=[...group.children].filter(el => tag(el)==='rect' && visible(el)).map(el=>({el,box:rootBox(el)})).filter(x=>x.box);
    if (!directRects.length) continue;
    directRects.sort((a,b)=>area(b.box)-area(a.box));
    const frame=directRects[0].box;
    const descendants=[...group.querySelectorAll('text,image,use')].filter(visible);
    for (const child of descendants) {
      const box=rootBox(child);
      if (box && !contains(frame,box,2.5)) {
        push('warning','container_overflow',{selector:selector(child)},`content exceeds ${selector(directRects[0].el)} in #${group.id}`);
      }
    }
  }

  const leaf = records.filter(rec => {
    if (['g','svg'].includes(rec.tag)) return false;
    if (rec.el.querySelector && rec.el.querySelector('*')) return false;
    const fullWidth=rec.root.width/viewBox.width > 0.92;
    const fullHeight=rec.root.height/viewBox.height > 0.92;
    if (fullWidth && fullHeight && ['rect','path'].includes(rec.tag)) return false;
    return rec.root.width > 0.1 && rec.root.height > 0.1;
  });
  let union=null;
  for (const rec of leaf) {
    const b=rec.root;
    union = union ? {
      x:Math.min(union.x,b.x), y:Math.min(union.y,b.y),
      width:Math.max(union.x+union.width,b.x+b.width)-Math.min(union.x,b.x),
      height:Math.max(union.y+union.height,b.y+b.height)-Math.min(union.y,b.y)
    } : {...b};
  }
  const utilization = union ? {
    width: union.width/viewBox.width,
    height: union.height/viewBox.height,
    left:(union.x-viewBox.x)/viewBox.width,
    right:(viewBox.x+viewBox.width-union.x-union.width)/viewBox.width,
    top:(union.y-viewBox.y)/viewBox.height,
    bottom:(viewBox.y+viewBox.height-union.y-union.height)/viewBox.height,
    meaningful_elements:leaf.length
  } : {width:0,height:0,left:1,right:1,top:1,bottom:1,meaningful_elements:0};
  if (utilization.width < minWidthUse || utilization.height < minHeightUse) {
    push('warning','underused_canvas',null,`content span ${(utilization.width*100).toFixed(1)}% × ${(utilization.height*100).toFixed(1)}%`,{utilization});
  }
  const tightSides=['left','right','top','bottom'].filter(key => utilization[key] < 0.008);
  if (tightSides.length >= 3) push('warning','edge_crowding',null,`content is tight to ${tightSides.join(', ')}`,{utilization});

  const corners=[
    new DOMPoint(viewBox.x,viewBox.y),new DOMPoint(viewBox.x+viewBox.width,viewBox.y),
    new DOMPoint(viewBox.x+viewBox.width,viewBox.y+viewBox.height),new DOMPoint(viewBox.x,viewBox.y+viewBox.height)
  ].map(p=>p.matrixTransform(rootMatrix));
  const xs=corners.map(p=>p.x), ys=corners.map(p=>p.y);
  const fitted={x:Math.min(...xs),y:Math.min(...ys),width:Math.max(...xs)-Math.min(...xs),height:Math.max(...ys)-Math.min(...ys)};
  if (!contains(viewport,fitted,1.25)) push('error','canvas_viewport_fit',null,`mapped viewBox exceeds viewport: ${JSON.stringify(fitted)}`);
  const expected=viewBox.width/viewBox.height, actual=fitted.width/fitted.height;
  if (Math.abs(actual/expected-1) > 0.01) push('error','responsive_aspect_distortion',null,`mapped aspect ${actual.toFixed(4)} differs from viewBox ${expected.toFixed(4)}`);

  return {
    page:pageName,
    viewport:{width:innerWidth,height:innerHeight},
    viewBox:{x:viewBox.x,y:viewBox.y,width:viewBox.width,height:viewBox.height},
    fittedCanvas:fitted,
    utilization,
    elementCount:records.length,
    issues,
    iconWarnings:payload.icon_warnings || payload.warnings || []
  };
}
"""


def _deduplicate_issues(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    counts: dict[str, int] = {}
    issues: list[dict[str, Any]] = []
    for result in results:
        viewport = result["viewport"]
        viewport_label = f"{viewport['width']}x{viewport['height']}"
        for issue in result.get("issues", []):
            key = (
                result["page"],
                issue.get("code"),
                issue.get("element"),
                issue.get("other"),
            )
            if key in seen:
                continue
            seen.add(key)
            code = str(issue.get("code"))
            if counts.get(code, 0) >= MAX_ISSUES_PER_CODE:
                continue
            counts[code] = counts.get(code, 0) + 1
            issues.append({"page": result["page"], "viewport": viewport_label, **issue})
    return issues


def audit(
    project: Path,
    server_url: str,
    pages: list[str],
    viewports: list[tuple[int, int]],
    min_width_use: float,
    min_height_use: float,
) -> list[dict[str, Any]]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ModuleNotFoundError(
            "playwright is not installed; install requirements.txt and a Chromium browser"
        ) from exc

    results: list[dict[str, Any]] = []
    with sync_playwright() as playwright:
        browser = _launch_browser(playwright)
        try:
            for width, height in viewports:
                context = browser.new_context(viewport={"width": width, "height": height})
                try:
                    page = context.new_page()
                    page.goto(server_url, wait_until="domcontentloaded")
                    for page_name in pages:
                        result = page.evaluate(
                            INJECT_AND_AUDIT_JS,
                            {
                                "pageName": page_name,
                                "minWidthUse": min_width_use,
                                "minHeightUse": min_height_use,
                            },
                        )
                        results.append(result)
                finally:
                    context.close()
        finally:
            browser.close()
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit rendered PPT Master SVG geometry at multiple viewport sizes."
    )
    parser.add_argument("project_path", help="Project directory containing svg_output/")
    parser.add_argument("--pages", nargs="+", help="Page filename prefixes or exact names")
    parser.add_argument(
        "--viewports",
        default=",".join(f"{w}x{h}" for w, h in DEFAULT_VIEWPORTS),
        help="Comma-separated WIDTHxHEIGHT list",
    )
    parser.add_argument("--server-url", help="Reuse an existing preview server for this project")
    parser.add_argument("--report", help="JSON report path (default: <project>/.review/layout-audit.json)")
    parser.add_argument("--min-width-use", type=float, default=0.48)
    parser.add_argument("--min-height-use", type=float, default=0.38)
    parser.add_argument("--fail-on-warnings", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project = Path(args.project_path).expanduser().resolve()
    svg_dir = project / "svg_output"
    if not svg_dir.is_dir():
        _stderr(f"svg_output directory not found: {svg_dir}")
        return 2
    all_pages = sorted(path.name for path in svg_dir.glob("*.svg"))
    if not all_pages:
        _stderr(f"no SVG pages found in: {svg_dir}")
        return 2
    pages = all_pages
    if args.pages:
        pages = []
        for token in args.pages:
            match = next((name for name in all_pages if name == token or name.startswith(token)), None)
            if match is None:
                _stderr(f"no SVG page matches {token!r}")
                return 2
            if match not in pages:
                pages.append(match)
    try:
        viewports = _parse_viewports(args.viewports)
    except (TypeError, ValueError) as exc:
        _stderr(str(exc))
        return 2
    if not (0 < args.min_width_use <= 1 and 0 < args.min_height_use <= 1):
        _stderr("utilization thresholds must be in (0, 1]")
        return 2

    try:
        with preview_server(project, args.server_url) as server_url:
            results = audit(
                project,
                server_url,
                pages,
                viewports,
                args.min_width_use,
                args.min_height_use,
            )
    except ModuleNotFoundError as exc:
        _stderr(str(exc))
        return 3
    except RuntimeError as exc:
        _stderr(f"layout audit unavailable: {exc}")
        return 3 if "browser" in str(exc).lower() or "chrom" in str(exc).lower() else 2
    except Exception as exc:  # noqa: BLE001
        _stderr(f"layout audit failed: {type(exc).__name__}: {exc}")
        return 2

    issues = _deduplicate_issues(results)
    errors = [issue for issue in issues if issue.get("severity") == "error"]
    warnings = [issue for issue in issues if issue.get("severity") == "warning"]
    report = {
        "project": str(project),
        "pages": pages,
        "viewports": [{"width": width, "height": height} for width, height in viewports],
        "summary": {"errors": len(errors), "warnings": len(warnings)},
        "issues": issues,
        "measurements": results,
    }
    report_path = (
        Path(args.report).expanduser().resolve()
        if args.report
        else project / ".review" / "layout-audit.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"Layout audit: {len(pages)} page(s), {len(viewports)} viewport(s), "
        f"{len(errors)} error(s), {len(warnings)} warning(s)"
    )
    for issue in issues[:40]:
        print(
            f"[{issue['severity'].upper()}] {issue['page']} {issue['code']} "
            f"{issue.get('element') or ''}: {issue.get('detail') or ''}"
        )
    if len(issues) > 40:
        print(f"... {len(issues) - 40} more issue(s); see report")
    print(f"Report: {report_path}")
    if errors or (args.fail_on_warnings and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
