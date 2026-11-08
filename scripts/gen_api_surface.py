#!/usr/bin/env python3
"""Generate the declared API surface: docs/api-surface.json + docs/API_SURFACE.md.

The HTTP surface used to be an emergent property of 13 routers, and which
routes each client consumes was discoverable only by grepping the Swift and
web sources. This generator makes the surface a committed artifact:

- **Routes** are enumerated from the REAL assembled FastAPI app (the same
  construction the route pre-flight uses), so nothing can hide.
- **Consumers** are extracted from the real call sites: every string literal
  carrying an ``api/…`` path in ``apple/`` (the iOS client) and ``web/src``
  (the web app), including JS template literals with nested templates.
  Interpolations (``\\(…)`` in Swift, ``${…}`` in JS, ``{…}``) become
  wildcard segments; query strings are stripped.
- Each web call also carries its HTTP method: the ``method:`` in its options
  (every quoted verb of a ternary counts), the helper's name (``apiDelete``,
  ``postJson``), or GET when neither names one. A web call tags a route only
  when the path AND the method match. A call that names no method and whose
  path serves no GET goes through a wrapper (``perform(path)``, an exported
  path constant); it tags the routes of its path whatever their method.
- Comments in web sources are not calls; they are read as blank.
- A web call with no fixed segment after ``/api`` (``/api/${path}/${id}``)
  names no route. It tags nothing and is listed under
  ``unresolved_dynamic_calls`` so it is not lost.
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
import tempfile
import sys
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]
# A shared environment can point at another checkout. Inspect this checkout.
sys.path.insert(0, str(REPO))
MANIFEST_JSON = REPO / "docs" / "api-surface.json"
MANIFEST_MD = REPO / "docs" / "API_SURFACE.md"

# A wildcard segment: a route path param or a client-side interpolation.
WILD = "*"
# The method of a web call that names none (GET unless its path serves no GET).
UNNAMED = "GET?"

_SWIFT_LITERAL = re.compile(r'"((?:/)?(?:api/|health\b|ws\b)[^"\n]*)"')
_WEB_LITERAL = re.compile(r'["\'`](/(?:api|ws)(?:/[^"\'`\n]*)?)["\'`]')
# The regex above closes a template literal at the first quote or backtick, so
# a nested template such as
# `/api/projects/${a}/resources/${encodeURIComponent(`note:${id}`)}` reads as a
# fragment. ``_web_templates`` also reads each template literal whole.
_WEB_TEMPLATE_START = re.compile(r"`(?=/(?:api|ws)\b)")
# Client-side interpolations that become wildcard segments.
_SWIFT_INTERP = re.compile(r"\\\([^)]*\)")
_JS_INTERP = re.compile(r"\$\{[^}]*\}")
_BRACE_PARAM = re.compile(r"\{[^}]*\}")
# The HTTP method of a web call.
_VERBS = ("GET", "POST", "PUT", "PATCH", "DELETE")
_METHOD_KEY = re.compile(r"\bmethod\s*:")
_VERB_LITERAL = re.compile(r"[\"'`](GET|POST|PUT|PATCH|DELETE)[\"'`]", re.IGNORECASE)
_CALLEE = re.compile(r"([A-Za-z_$][\w$]*)\s*\(\s*$")
_ASSIGNED = re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*$")
# How far after a path literal the call's options are looked for.
_REGION_LIMIT = 2000


def build_reference_app():
    """Assemble the reference app against a disposable database, without serving."""
    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    # Route generation must never open or reconcile a contributor's live Desk.
    # MeetingWebServer reaches the process-wide database singleton while it
    # assembles a few service-backed routers, so point that singleton at an
    # isolated, disposable database for the duration of this read-only census.
    reset_database()
    with tempfile.TemporaryDirectory(prefix="holdspeak-api-surface-") as tmp:
        get_database(Path(tmp) / "api-surface.db")
        try:
            server = MeetingWebServer(
                WebRuntimeCallbacks(
                    on_bookmark=lambda *_a, **_k: None,
                    on_stop=lambda *_a, **_k: None,
                    get_state=lambda: None,
                ),
                host="127.0.0.1",
            )
        finally:
            reset_database()
    return server.app


def build_app_routes() -> list[dict[str, Any]]:
    """Enumerate the real app's HTTP routes (path, methods, defining module)."""
    routes: list[dict[str, Any]] = []
    for route in build_reference_app().routes:
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


def _skip_quoted(text: str, i: int) -> int:
    """Index after the '…' or "…" string that opens at ``text[i]``."""
    quote = text[i]
    i += 1
    while i < len(text) and text[i] not in (quote, "\n"):
        i += 2 if text[i] == "\\" else 1
    return i + 1


def _skip_expression(text: str, i: int) -> int:
    """Index after the ``}`` that closes the ``${`` expression starting at ``text[i]``."""
    depth = 1
    while i < len(text):
        ch = text[i]
        if ch in "'\"":
            i = _skip_quoted(text, i)
            continue
        if ch == "`":
            _, i = _read_template(text, i)
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return i


def _read_template(text: str, start: int) -> tuple[str | None, int]:
    """Read the template literal that opens at ``text[start]`` (a backtick).

    Returns the literal with every ``${…}`` replaced by a wildcard (nested
    templates inside an interpolation are skipped whole), and the index after
    the closing backtick. The literal is None when it spans lines.
    """
    out: list[str] = []
    single_line = True
    i = start + 1
    while i < len(text):
        ch = text[i]
        if ch == "\\":
            out.append(text[i : i + 2])
            i += 2
        elif ch == "`":
            return ("".join(out) if single_line else None), i + 1
        elif text.startswith("${", i):
            out.append(WILD)
            i = _skip_expression(text, i + 2)
        else:
            if ch == "\n":
                single_line = False
            out.append(ch)
            i += 1
    return None, i


def _blank_comments(text: str) -> str:
    """The text with each ``//`` and ``/* */`` comment replaced by spaces.

    Strings and template literals are kept, and every offset stays the same.
    """
    out = list(text)
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in "'\"":
            i = _skip_quoted(text, i)
        elif ch == "`":
            _, i = _read_template(text, i)
        elif text.startswith("//", i):
            end = text.find("\n", i)
            end = len(text) if end < 0 else end
            out[i:end] = " " * (end - i)
            i = end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            end = len(text) if end < 0 else end + 2
            out[i:end] = [c if c == "\n" else " " for c in text[i:end]]
            i = end
        else:
            i += 1
    return "".join(out)


def _web_literals(text: str) -> Iterable[tuple[str, int, int]]:
    """Every /api or /ws path literal in a web source: (raw, start, end).

    Quoted strings come from ``_WEB_LITERAL``; template literals are also read
    whole, so a nested template does not cut the path short.
    """
    whole: set[int] = set()
    for match in _WEB_TEMPLATE_START.finditer(text):
        literal, end = _read_template(text, match.start())
        if literal is not None:
            whole.add(match.start())
            yield literal, match.start(), end
    for match in _WEB_LITERAL.finditer(text):
        # A template read whole above; the regex reads only its first fragment.
        if match.start() not in whole:
            yield match.group(1), match.start(), match.end()


def _call_region(text: str, i: int) -> tuple[str, bool]:
    """The text from ``i`` to the end of the enclosing call or statement.

    The second value is True when a ``;`` or a new statement line ended the
    region at the top level (the literal was a whole statement value, such as
    ``const url = `/api/…`;``), and False when a closing bracket did.
    """
    depth = 0
    start = i
    while i < len(text) and i - start < _REGION_LIMIT:
        ch = text[i]
        if ch in "'\"":
            i = _skip_quoted(text, i)
            continue
        if ch == "`":
            _, i = _read_template(text, i)
            continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth < 0:
                return text[start:i], False
        elif ch == ";" and depth == 0:
            return text[start:i], True
        i += 1
    return text[start:i], False


def _methods_in(region: str) -> set[str] | None:
    """The verbs a ``method:`` key names in a call's options.

    Returns None when the region has no ``method:`` key, and an empty set when
    the key holds no quoted verb (a value read at run time).
    """
    match = _METHOD_KEY.search(region)
    if match is None:
        return None
    value = re.split(r"[,}\n]", region[match.end():], maxsplit=1)[0]
    return {verb.upper() for verb in _VERB_LITERAL.findall(value)}


def _helper_verb(text: str, start: int) -> str | None:
    """The verb a helper's name carries (``apiDelete(``, ``postJson(``)."""
    match = _CALLEE.search(text[max(0, start - 80) : start])
    if match is None:
        return None
    name = match.group(1).lower()
    name = name.removeprefix("api").removeprefix("http").removesuffix("json")
    if name == "del":
        name = "delete"
    return name.upper() if name.upper() in _VERBS else None


def _call_methods(text: str, start: int, end: int) -> set[str]:
    """The HTTP methods of the call that sends the literal at ``text[start:end]``.

    The ``method:`` in the call's options wins, then the helper's name. A path
    assigned to a variable (``const url = `/api/…`;``) takes the method of the
    first call that passes that variable. ``UNNAMED`` when nothing names a
    method (GET, unless the path serves no GET; see ``_method_matches``).
    """
    region, statement = _call_region(text, end)
    found = _methods_in(region)
    if found is None and statement:
        assigned = _ASSIGNED.search(text[max(0, start - 120) : start])
        if assigned is not None:
            use = re.compile(r"\b" + re.escape(assigned.group(1)) + r"\b\s*[,)]")
            later = use.search(text, end)
            if later is not None:
                name_end = later.end() - 1
                found = _methods_in(_call_region(text, name_end)[0])
                if found is None:
                    verb = _helper_verb(text, later.start())
                    found = {verb} if verb else None
    if found is None:
        verb = _helper_verb(text, start)
        found = {verb} if verb else None
    if found is None:
        return {UNNAMED}
    return found


def _is_dynamic(path: str) -> bool:
    """An /api call with no fixed segment after /api names no route."""
    segments = _segments(path)
    return bool(segments) and segments[0] == "api" and all(
        s == WILD for s in segments[1:]
    )


def web_call_sites(text: str) -> set[tuple[str, str]]:
    """Every web call in one source text as (method, path template).

    A call whose method is read at run time carries ``*`` as its method.
    """
    sites: set[tuple[str, str]] = set()
    text = _blank_comments(text)
    for raw, start, end in _web_literals(text):
        path = _normalize(raw)
        if not path:
            continue
        for method in _call_methods(text, start, end) or {WILD}:
            sites.add((method, path))
    return sites


def _extract(
    paths: Iterable[Path], pattern: re.Pattern[str], *, templates: bool = False
) -> set[str]:
    found: set[str] = set()
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        found |= extract_from_text(text, pattern, templates=templates)
    return found


def extract_from_text(
    text: str, pattern: re.Pattern[str] = _WEB_LITERAL, *, templates: bool = True
) -> set[str]:
    """The call path templates in one source text (web by default).

    A web call with no fixed segment after /api is left out (see
    ``web_call_sites`` for the calls with their methods).
    """
    if templates:
        return {path for _, path in web_call_sites(text) if not _is_dynamic(path)}
    raws = [match.group(1) for match in pattern.finditer(text)]
    return {n for n in map(_normalize, raws) if n}


def extract_ios_calls() -> set[str]:
    files = list((REPO / "apple" / "Sources").rglob("*.swift"))
    files += list((REPO / "apple" / "App").rglob("*.swift"))
    return _extract(files, _SWIFT_LITERAL)


def _web_files() -> list[Path]:
    web_src = REPO / "web" / "src"
    return sorted(
        p
        for suffix in ("*.js", "*.ts", "*.tsx", "*.astro")
        for p in web_src.rglob(suffix)
        if not p.name.endswith((".test.js", ".test.ts", ".test.tsx"))
        and "__tests__" not in p.parts
    )


def extract_web_call_sites() -> tuple[set[tuple[str, str]], list[dict[str, str]]]:
    """The web calls as (method, path), and the unresolved dynamic calls.

    An unresolved call has no fixed segment after /api; it is returned with
    its file instead of being matched.
    """
    calls: set[tuple[str, str]] = set()
    dynamic: set[tuple[str, str, str]] = set()
    for path in _web_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for method, call in web_call_sites(text):
            if _is_dynamic(call):
                dynamic.add((str(path.relative_to(REPO)), method, call))
            else:
                calls.add((method, call))
    unresolved = [
        {"file": file, "method": method, "path": call}
        for file, method, call in sorted(dynamic)
    ]
    return calls, unresolved


def extract_web_calls() -> set[str]:
    """The web call path templates (methods dropped, dynamic calls left out)."""
    return {call for _, call in extract_web_call_sites()[0]}


def _segments(path: str) -> list[str]:
    return [s for s in path.split("/") if s]


def _segment_matches(call_segment: str, route_segment: str) -> bool:
    if call_segment == WILD or route_segment.startswith("{"):
        return True
    if WILD in call_segment:
        pattern = re.escape(call_segment).replace(r"\*", ".*")
        return re.fullmatch(pattern, route_segment) is not None
    return call_segment == route_segment


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
        if not _segment_matches(c, r):
            return False
    return True


def _prefix_matches(call: str, route_path: str) -> bool:
    """A concatenation/truncation fragment prefix-matches a route."""
    call_segs = _segments(call)
    route_segs = _segments(route_path)
    if not call_segs or len(call_segs) > len(route_segs):
        return False
    for c, r in zip(call_segs, route_segs[: len(call_segs)]):
        if not _segment_matches(c, r):
            return False
    return True


def _method_matches(
    call_method: str, route_methods: list[str], *, path_serves_get: bool = True
) -> bool:
    """A web call's method against a route's methods.

    A WebSocket route takes any call (the upgrade is a GET); a method read at
    run time (``*``) takes any route method. A call that names no method is a
    GET when its path serves GET; otherwise a wrapper sends it, and it takes
    any route method of its path.
    """
    if call_method == WILD or "WS" in route_methods:
        return True
    if call_method == UNNAMED:
        return "GET" in route_methods or not path_serves_get
    return call_method in route_methods


def _serves_get(call: str, routes: list[dict[str, Any]], prefix: bool = False) -> bool:
    matches = _prefix_matches if prefix else _route_matches
    return any(matches(call, r["path"]) and "GET" in r["methods"] for r in routes)


def match_consumers(
    routes: list[dict[str, Any]], ios: set[str], web: set[tuple[str, str]]
) -> tuple[list[dict[str, Any]], set[str], set[str]]:
    """Tag each route with its consumers; return unmatched call templates too.

    iOS calls match by path. Web calls are (method, path) and match by both.
    """
    unmatched_ios = set(ios)
    unmatched_web = set(web)
    serves_get = {c: _serves_get(c, routes) for m, c in web if m == UNNAMED}
    for route in routes:
        consumers = []
        if any(_route_matches(c, route["path"]) for c in ios):
            consumers.append("ios")
            unmatched_ios -= {c for c in ios if _route_matches(c, route["path"])}
        web_hits = {
            (m, c)
            for m, c in web
            if _route_matches(c, route["path"])
            and _method_matches(m, route["methods"], path_serves_get=serves_get.get(c, True))
        }
        if web_hits:
            consumers.append("web")
            unmatched_web -= web_hits
        route["consumers"] = consumers
    # Second pass: fragments (concatenations/truncated interpolations) count as
    # consumed-by if they prefix-match; they just can't pin the exact route.
    for call in list(unmatched_ios):
        if any(_prefix_matches(call, r["path"]) for r in routes):
            unmatched_ios.discard(call)
    for method, call in list(unmatched_web):
        prefix_get = _serves_get(call, routes, prefix=True)
        if any(
            _prefix_matches(call, r["path"])
            and _method_matches(method, r["methods"], path_serves_get=prefix_get)
            for r in routes
        ):
            unmatched_web.discard((method, call))
    return routes, unmatched_ios, {
        f"{'GET' if m == UNNAMED else m} {c}" for m, c in unmatched_web
    }


def build_manifest() -> dict[str, Any]:
    routes = build_app_routes()
    ios = extract_ios_calls()
    web, unresolved = extract_web_call_sites()
    routes, unmatched_ios, unmatched_web = match_consumers(routes, ios, web)
    return {
        "note": "Generated by scripts/gen_api_surface.py. Do not edit by hand.",
        "routes": routes,
        "unmatched_calls": {
            "ios": sorted(unmatched_ios),
            "web": sorted(unmatched_web),
        },
        "unresolved_dynamic_calls": {"web": unresolved},
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
        "Routes registered by the reference FastAPI app, with their defining modules.",
        "Consumer tags are static matches in `web/src` and Swift sources.",
        "A web tag needs the path and the HTTP method of the call to match the route.",
        "They can include parked code and do not prove a current UI calls the route.",
        "The `server only` label means the extractor found no matching client literal.",
        "A registered compatibility route can return a named refusal instead of an effect.",
        "For example, the old meeting Slack-export route returns `slack_moved_to_channel`.",
        "Read the handler and owning guide before treating route presence as feature availability.",
        "Route semantics and authority live in [Intelligence Router architecture](internal/ARCHITECTURE_INTELLIGENCE_ROUTER.md).",
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
    unresolved = manifest.get("unresolved_dynamic_calls", {}).get("web", [])
    if unresolved:
        lines += [
            "## Unresolved dynamic calls",
            "",
            "These web calls have no fixed segment after `/api`, so they name no route",
            "and tag none. Read the call site to know which routes they reach.",
            "",
            "| Method | Path | File |",
            "|---|---|---|",
        ]
        for call in unresolved:
            lines.append(f"| {call['method']} | `{call['path']}` | `{call['file']}` |")
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
