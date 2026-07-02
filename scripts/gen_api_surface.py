#!/usr/bin/env python3
"""Generate the declared API surface: docs/api-surface.json + docs/API_SURFACE.md.

The HTTP surface used to be an emergent property of 13 routers, and which
routes each client consumes was discoverable only by grepping the Swift and
web sources. This generator makes the surface a committed artifact:

- **Routes** are enumerated from the REAL assembled FastAPI app (the same
  construction the route pre-flight uses), so nothing can hide.
- **Consumers** are extracted from the real call sites: every string literal
  carrying an ``api/…`` path in ``apple/`` (the iOS client) and ``web/src``
  (the web app). Interpolations (``\\(…)`` in Swift, ``${…}`` in JS, ``{…}``)
  become wildcard segments; query strings are stripped.
- Each route is tagged ``web`` / ``ios`` / both / neither (server-only).

Regenerate after any route change:

    uv run python scripts/gen_api_surface.py

The snapshot guard (``tests/unit/test_api_surface.py``) fails when the
committed manifest drifts from the live app, and when a client calls a path
the app does not serve.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]
MANIFEST_JSON = REPO / "docs" / "api-surface.json"
MANIFEST_MD = REPO / "docs" / "API_SURFACE.md"

# A wildcard segment: a route path param or a client-side interpolation.
WILD = "*"

_SWIFT_LITERAL = re.compile(r'"((?:/)?(?:api/|health\b|ws\b)[^"\n]*)"')
_WEB_LITERAL = re.compile(r'["\'`](/(?:api|ws)(?:/[^"\'`\n]*)?)["\'`]')
# Client-side interpolations that become wildcard segments.
_SWIFT_INTERP = re.compile(r"\\\([^)]*\)")
_JS_INTERP = re.compile(r"\$\{[^}]*\}")
_BRACE_PARAM = re.compile(r"\{[^}]*\}")


def build_app_routes() -> list[dict[str, Any]]:
    """Enumerate the real app's HTTP routes (path, methods, defining module)."""
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    routes: list[dict[str, Any]] = []
    for route in server.app.routes:
        path = getattr(route, "path", "")
        endpoint = getattr(route, "endpoint", None)
        module = getattr(endpoint, "__module__", "") or ""
        methods = sorted((getattr(route, "methods", set()) or set()) - {"HEAD", "OPTIONS"})
        kind = type(route).__name__
        if kind == "Mount":
            # Static mounts are environment-dependent (the /_built dir is a
            # gitignored build product, absent on a fresh clone), so they
            # cannot live in a manifest that must match every environment.
            continue
        if kind.endswith("WebSocketRoute"):
            routes.append({"path": path, "methods": ["WS"], "module": _short(module)})
            continue
        if not methods:
            continue
        routes.append({"path": path, "methods": methods, "module": _short(module)})
    routes.sort(key=lambda r: (r["path"], r["methods"]))
    return routes


def _short(module: str) -> str:
    return module.removeprefix("holdspeak.")


def _normalize(raw: str) -> str | None:
    """A call-site literal → a comparable path template (wildcarded), or None."""
    text = raw.split("?", 1)[0].strip()
    text = _SWIFT_INTERP.sub(WILD, text)
    text = _JS_INTERP.sub(WILD, text)
    text = _BRACE_PARAM.sub(WILD, text)
    # An interpolation the literal-regex could not close (nested quotes/parens,
    # e.g. `…${projectRootParam(…`) — usually a query-string builder. Keep the
    # path part and let the matcher fall back to prefix matching.
    if "${" in text:
        text = text.split("${", 1)[0]
    if not text or " " in text:
        return None  # a log/format string, not a path
    if not text.startswith("/"):
        text = "/" + text
    # Collapse wildcard runs produced by adjacent interpolations.
    text = re.sub(r"\*+", WILD, text)
    if text in ("/", "/api", "/api/"):
        return None
    return text


def _extract(paths: Iterable[Path], pattern: re.Pattern[str]) -> set[str]:
    found: set[str] = set()
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for match in pattern.finditer(text):
            normalized = _normalize(match.group(1))
            if normalized:
                found.add(normalized)
    return found


def extract_ios_calls() -> set[str]:
    files = list((REPO / "apple" / "Sources").rglob("*.swift"))
    files += list((REPO / "apple" / "App").rglob("*.swift"))
    return _extract(files, _SWIFT_LITERAL)


def extract_web_calls() -> set[str]:
    web_src = REPO / "web" / "src"
    files = [p for suffix in ("*.js", "*.ts", "*.astro") for p in web_src.rglob(suffix)]
    return _extract(files, _WEB_LITERAL)


def _segments(path: str) -> list[str]:
    return [s for s in path.split("/") if s]


def _route_matches(call: str, route_path: str) -> bool:
    """A wildcarded call template matches a route template segment-wise.

    A call ending in a dangling separator (a concatenation fragment like
    ``/api/meetings/``) prefix-matches instead.
    """
    call_segs = _segments(call)
    route_segs = _segments(route_path)
    if len(call_segs) != len(route_segs):
        return False
    for c, r in zip(call_segs, route_segs):
        if c == WILD or r.startswith("{"):
            continue
        if c != r:
            return False
    return True


def _prefix_matches(call: str, route_path: str) -> bool:
    """A concatenation/truncation fragment prefix-matches a route."""
    call_segs = _segments(call)
    route_segs = _segments(route_path)
    if not call_segs or len(call_segs) > len(route_segs):
        return False
    for c, r in zip(call_segs, route_segs[: len(call_segs)]):
        if c == WILD or r.startswith("{"):
            continue
        if c != r:
            return False
    return True


def match_consumers(
    routes: list[dict[str, Any]], ios: set[str], web: set[str]
) -> tuple[list[dict[str, Any]], set[str], set[str]]:
    """Tag each route with its consumers; return unmatched call templates too."""
    unmatched_ios = set(ios)
    unmatched_web = set(web)
    for route in routes:
        consumers = []
        if any(_route_matches(c, route["path"]) for c in ios):
            consumers.append("ios")
            unmatched_ios -= {c for c in ios if _route_matches(c, route["path"])}
        if any(_route_matches(c, route["path"]) for c in web):
            consumers.append("web")
            unmatched_web -= {c for c in web if _route_matches(c, route["path"])}
        route["consumers"] = consumers
    # Second pass: fragments (concatenations/truncated interpolations) count as
    # consumed-by if they prefix-match; they just can't pin the exact route.
    for pool, unmatched in ((ios, unmatched_ios), (web, unmatched_web)):
        for call in list(unmatched):
            if any(_prefix_matches(call, r["path"]) for r in routes):
                unmatched.discard(call)
    return routes, unmatched_ios, unmatched_web


def build_manifest() -> dict[str, Any]:
    routes = build_app_routes()
    ios = extract_ios_calls()
    web = extract_web_calls()
    routes, unmatched_ios, unmatched_web = match_consumers(routes, ios, web)
    return {
        "note": "Generated by scripts/gen_api_surface.py. Do not edit by hand.",
        "routes": routes,
        "unmatched_calls": {
            "ios": sorted(unmatched_ios),
            "web": sorted(unmatched_web),
        },
    }


def render_markdown(manifest: dict[str, Any]) -> str:
    routes = manifest["routes"]
    by_module: dict[str, list[dict[str, Any]]] = {}
    for r in routes:
        by_module.setdefault(r["module"], []).append(r)

    def consumer_cell(r: dict[str, Any]) -> str:
        return ", ".join(r["consumers"]) if r["consumers"] else "server only"

    lines = [
        "# The API surface",
        "",
        "Generated by `scripts/gen_api_surface.py`. Do not edit by hand;",
        "regenerate with `uv run python scripts/gen_api_surface.py` after any",
        "route change (the snapshot test fails otherwise).",
        "",
        "Every HTTP route the runtime serves, with the module that defines it",
        "and the clients that call it (extracted from the real call sites in",
        "`web/src` and `apple/`). \"server only\" means no in-repo client calls",
        "it today.",
        "",
        f"Routes: {sum(1 for r in routes if r['methods'] not in (['MOUNT'],))} "
        f"(plus static mounts). iOS-consumed: "
        f"{sum(1 for r in routes if 'ios' in r['consumers'])}. Web-consumed: "
        f"{sum(1 for r in routes if 'web' in r['consumers'])}.",
        "",
    ]
    for module in sorted(by_module):
        lines.append(f"## {module}")
        lines.append("")
        lines.append("| Method | Path | Consumers |")
        lines.append("|---|---|---|")
        for r in by_module[module]:
            lines.append(
                f"| {' '.join(r['methods'])} | `{r['path']}` | {consumer_cell(r)} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    manifest = build_manifest()
    MANIFEST_JSON.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    MANIFEST_MD.write_text(render_markdown(manifest), encoding="utf-8")
    print(f"wrote {MANIFEST_JSON.relative_to(REPO)} ({len(manifest['routes'])} routes)")
    print(f"wrote {MANIFEST_MD.relative_to(REPO)}")
    unmatched = manifest["unmatched_calls"]
    for surface in ("ios", "web"):
        if unmatched[surface]:
            print(f"WARNING unmatched {surface} calls: {unmatched[surface]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
