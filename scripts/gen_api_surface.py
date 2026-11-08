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
- A path value is followed to the call that sends it: through a ``const``, a
  table row (``paths[kind]``, with a ``method:`` ternary on the row key), a
  function that returns it, and a local wrapper's parameter. A ``${verb}``
  parameter that every caller passes as a literal is filled with each one.
- A web call with no fixed segment after ``/api`` (``/api/${path}/${id}``)
  names no route by itself. ``api_surface_web_dynamic_calls.json`` (next to
  this script) names the routes each one reaches, by hand; those routes are
  tagged and the entries are listed under ``web_dynamic_calls``. A dynamic
  call with no entry (same file and method) tags nothing and is listed under
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
# Web calls with no fixed segment after /api, resolved by hand.
WEB_DYNAMIC_CALLS = Path(__file__).resolve().parent / "api_surface_web_dynamic_calls.json"

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


def _methods_in(region: str, key: str | None = None) -> set[str] | None:
    """The verbs a ``method:`` key names in a call's options.

    Returns None when the region has no ``method:`` key, and an empty set when
    the key holds no quoted verb (a value read at run time). A ternary on the
    table key (``kind === "project" ? "PATCH" : "PUT"``) picks one verb when
    the value came from a table row whose key is known.
    """
    match = _METHOD_KEY.search(region)
    if match is None:
        return None
    value = re.split(r"[,}\n]", region[match.end():], maxsplit=1)[0]
    ternary = re.fullmatch(
        r"\s*([^?]*)\?\s*[\"'`](\w+)[\"'`]\s*:\s*[\"'`](\w+)[\"'`]\s*", value
    )
    if key is not None and ternary is not None:
        compared = re.findall(r"===?\s*[\"'](\w+)[\"']", ternary.group(1))
        if compared:
            verb = ternary.group(2) if key in compared else ternary.group(3)
            return {verb.upper()} if verb.upper() in _VERBS else set()
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


# The calls that send a request; a value passed to one with no ``method:`` is
# a GET (or reaches a path through a wrapper, see ``_method_matches``).
_REQUEST_CALLS = frozenset({
    "apiFetch", "apiRequest", "apiBlob", "fetch", "fetchJson", "readJson",
    "useResource", "EventSource", "WebSocket", "sendBeacon",
})
_NOT_FUNCTIONS = frozenset({"if", "for", "while", "switch", "catch", "return", "function"})
_IDENT = r"[A-Za-z_$][\w$]*"
# A type argument list on one line (one level of nesting): ``<Record<string, X>>``.
_GENERIC = r"<(?:[^<>()\n;]|<[^<>()\n;]*>)*>"
_FOLLOW_DEPTH = 8


class _Source:
    """One web source with its bracket pairs, for following a path value."""

    def __init__(self, text: str) -> None:
        self.text = text
        self._pairs: dict[int, int] | None = None

    @property
    def pairs(self) -> dict[int, int]:
        """Each bracket's partner (both ways), outside strings and templates."""
        if self._pairs is None:
            pairs: dict[int, int] = {}
            stack: list[int] = []
            text = self.text
            i = 0
            while i < len(text):
                ch = text[i]
                if ch in "'\"":
                    i = _skip_quoted(text, i)
                    continue
                if ch == "`":
                    _, i = _read_template(text, i)
                    continue
                if ch in "([{":
                    stack.append(i)
                elif ch in ")]}" and stack:
                    opener = stack.pop()
                    pairs[opener] = i
                    pairs[i] = opener
                i += 1
            self._pairs = pairs
        return self._pairs

    def block_of(self, i: int) -> tuple[int, int]:
        """The span of the innermost ``{…}`` around ``i`` (the file at the top)."""
        best = (0, len(self.text))
        for opener, close in self.pairs.items():
            if opener < i < close and self.text[opener] == "{" and opener > best[0]:
                best = (opener, close)
        return best

    def function_of_params(self, params_close: int) -> tuple[str, int] | None:
        """The function whose parameter list closes at ``params_close``."""
        params_open = self.pairs.get(params_close)
        if params_open is None or params_open > params_close:
            return None
        head = self.text[max(0, params_open - 160) : params_open]
        match = (
            re.search(rf"\bfunction\s*\*?\s*({_IDENT})\s*(?:{_GENERIC})?\s*$", head)
            or re.search(rf"\b({_IDENT})\s*(?::[^=;]*)?=\s*(?:useCallback\(\s*)?(?:async\s*)?$", head)
            or re.search(rf"(?:^|[\s,;{{}}])(?:async\s+)?({_IDENT})\s*$", head)
        )
        if match is None or match.group(1) in _NOT_FUNCTIONS:
            return None
        return match.group(1), params_open

    def _params_close_before(self, i: int) -> int | None:
        """The ``)`` of a parameter list just before ``i`` (over a return type)."""
        text = self.text
        j = i - 1
        while j >= 0 and text[j].isspace():
            j -= 1
        if text[max(0, j - 1) : j + 1] == "=>":
            j -= 2
            while j >= 0 and text[j].isspace():
                j -= 1
        if j >= 0 and text[j] == "}" and j in self.pairs:  # ): { url: string } {
            k = self.pairs[j] - 1
            while k >= 0 and text[k].isspace():
                k -= 1
            j = k - 1 if k >= 0 and text[k] == ":" else j
            while j >= 0 and text[j].isspace():
                j -= 1
        else:  # ): string | null {
            typed = re.search(r"\)\s*:\s*[\w$<>\[\]|.,\s]+$", text[max(0, j - 120) : j + 1])
            if typed is not None:
                j = max(0, j - 120) + typed.start()
        return j if j >= 0 and text[j] == ")" else None

    def function_around(self, i: int) -> tuple[str, int] | None:
        """The innermost named function whose body holds ``i``."""
        openers = sorted(
            (o for o, c in self.pairs.items() if o < i < c and self.text[o] == "{"),
            reverse=True,
        )
        for opener in openers:
            close = self._params_close_before(opener)
            found = self.function_of_params(close) if close is not None else None
            if found is not None:
                return found
        return None

    def params(self, params_open: int) -> list[str]:
        """The parameter names of the list that opens at ``params_open``."""
        inner = self.text[params_open + 1 : self.pairs[params_open]]
        names = []
        for part in _split_top(inner):
            match = re.match(rf"\s*(?:\.\.\.)?({_IDENT})", part)
            names.append(match.group(1) if match else "")
        return names

    def calls_of(self, name: str, *, start: int = 0, end: int | None = None):
        """Each call ``name(…)`` in the range: (name start, paren open, paren close)."""
        for use in re.finditer(rf"(?<![\w$.])({re.escape(name)})\s*(?:{_GENERIC})?\s*\(", self.text[: end or len(self.text)]):
            if use.start() < start:
                continue
            paren = use.end() - 1
            if paren not in self.pairs:
                continue  # inside a template interpolation
            if re.search(r"\bfunction\s*$", self.text[max(0, use.start() - 12) : use.start()]):
                continue
            yield use.start(), paren, self.pairs[paren]


def _split_top(text: str) -> list[str]:
    """Split on commas outside brackets and angle brackets."""
    parts, depth, current = [], 0, []
    for ch in text:
        if ch in "([{<":
            depth += 1
        elif ch in ")]}>":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if "".join(current).strip():
        parts.append("".join(current))
    return parts


def _arg_index(src: _Source, paren_open: int, at: int) -> int:
    """Which argument of the call opening at ``paren_open`` holds ``at``."""
    return src.text[paren_open + 1 : at].count(",") and len(
        _split_top(src.text[paren_open + 1 : at] + "x")
    ) - 1


def _assigned_names(before: str) -> list[str]:
    """The names a ``const x =`` or a destructuring ``const [a, b] =`` binds."""
    single = re.search(rf"\b(?:const|let|var)\s+({_IDENT})\s*(?::[^=;]*)?=\s*$", before)
    if single is not None:
        return [single.group(1)]
    many = re.search(r"\b(?:const|let|var)\s*[\[{]([^\]}=;]*)[\]}]\s*(?::[^=;]*)?=\s*$", before)
    if many is None:
        return []
    names = [n for n in re.findall(_IDENT, many.group(1))]
    # The path is the url/path field; the rest of the tuple is its body.
    preferred = [n for n in names if re.search("url|path|href|endpoint|route", n, re.I)]
    return preferred or names


def _value_methods(
    src: _Source, start: int, end: int, depth: int = 0, key: str | None = None
) -> set[str]:
    """The HTTP methods of the calls that send the value at ``text[start:end]``.

    The ``method:`` in the call's options wins, then the helper's name. Else
    the value is followed: through a ``const`` (each use in its block), a table
    (``paths[kind]``), a returned value (each call of the function), and a
    local wrapper (each use of the parameter it lands in). A request call
    with no method gives ``UNNAMED``; an empty set means nothing sends it.
    """
    if depth > _FOLLOW_DEPTH:
        return set()
    text = src.text
    region, statement = _call_region(text, end)
    found = _methods_in(region, key)
    if found is not None:
        return found or {WILD}
    verb = _helper_verb(text, start)
    if verb:
        return {verb}
    close = end + len(region)
    before = text[max(0, start - 300) : start]
    methods: set[str] = set()
    if not statement and close < len(text) and close in src.pairs:
        opener = src.pairs[close]
        if text[close] == ")":
            callee = re.search(rf"({_IDENT})\s*(?:{_GENERIC})?\s*$", text[max(0, opener - 80) : opener])
            name = callee.group(1) if callee else ""
            if name in _REQUEST_CALLS or re.search(r"\bnew\s+" + re.escape(name) + r"\s*$", text[max(0, opener - 90) : opener]):
                return {UNNAMED}
            return _wrapper_methods(src, name, _arg_index(src, opener, start), depth)
        # A value in a table or an object: follow the whole container, and
        # keep the row's key for a method chosen by key.
        if key is None:
            row = re.search(rf"[\"']?({_IDENT})[\"']?\s*:\s*$", before)
            key = row.group(1) if row else None
        return _value_methods(src, opener, close + 1, depth + 1, key)
    # A returned value: each call of the function that returns it.
    if re.search(r"(?:\breturn|=>)\s*\(?\s*$", before):
        if re.search(r"=>\s*\(?\s*$", before):
            arrow = src._params_close_before(start - len(before) + len(before.rstrip().rstrip("(").rstrip()))
            owner = src.function_of_params(arrow) if arrow is not None else None
        else:
            owner = src.function_around(start)
        if owner is not None:
            for name_at, _, paren_close in src.calls_of(owner[0]):
                if name_at != start:
                    methods |= _value_methods(src, name_at, paren_close + 1, depth + 1, key)
        return methods
    # A const: each use of its name in its block.
    names = _assigned_names(before)
    if names:
        block_start, block_end = src.block_of(start)
        for name in names:
            methods |= _uses_methods(src, name, end, block_end, depth, key)
    return methods


def _uses_methods(
    src: _Source, name: str, start: int, end: int, depth: int, key: str | None = None
) -> set[str]:
    """The methods of each use of ``name`` as a value in ``text[start:end]``."""
    text = src.text
    methods: set[str] = set()
    for use in re.finditer(rf"\(\s*{re.escape(name)}\s+as\b", text[:end]):  # (name as T)[key]
        at = use.start()
        if at < start or at not in src.pairs:
            continue
        after = src.pairs[at] + 1
        if text[after : after + 1] == "[" and after in src.pairs:
            methods |= _value_methods(src, at, src.pairs[after] + 1, depth + 1, key)
    for use in re.finditer(rf"(?<![\w$.]){re.escape(name)}\b", text[:end]):
        at, after = use.start(), use.end()
        if at < start:
            continue
        if text[after : after + 1] == "[" and after in src.pairs:  # name[key]
            methods |= _value_methods(src, at, src.pairs[after] + 1, depth + 1, key)
        elif re.match(r"\s*[,)]", text[after : after + 8]):
            methods |= _value_methods(src, at, after, depth + 1, key)
    return methods


def _wrapper_methods(src: _Source, name: str, index: int, depth: int) -> set[str]:
    """The methods a local function sends the value in its ``index`` argument with."""
    if not name or name in _NOT_FUNCTIONS:
        return set()
    text = src.text
    definition = re.search(
        rf"(?:\bfunction\s+{re.escape(name)}\s*(?:{_GENERIC})?\s*|(?<![\w$.]){re.escape(name)}\s*(?::[^=;]*)?=\s*(?:useCallback\(\s*)?(?:async\s*)?)\(",
        text,
    )
    if definition is None or definition.end() - 1 not in src.pairs:
        return set()
    params_open = definition.end() - 1
    params = src.params(params_open)
    if index >= len(params) or not params[index]:
        return set()
    params_close = src.pairs[params_open]
    body = re.compile(r"[^{;]*?\{").match(text, params_close + 1)
    body_open = body.end() - 1 if body else None
    body_end = src.pairs.get(body_open, len(text)) if body_open is not None else len(text)
    return _uses_methods(src, params[index], params_close, body_end, depth + 1)


def _param_variants(src: _Source, start: int, end: int) -> list[str]:
    """A template's source with a ``${param}`` filled by each literal passed.

    ``url: `/api/coders/relay/${node}/${verb}``` inside ``verbEndpoint(node,
    key, verb)`` becomes one source per ``verbEndpoint(…, "arm")`` call. Only
    a parameter every call passes as a string literal is filled.
    """
    source = src.text[start:end]
    owner = src.function_around(start)
    if owner is None:
        return [source]
    params = src.params(owner[1])
    for ident in re.findall(rf"\$\{{\s*({_IDENT})\s*\}}", source):
        if ident not in params:
            continue
        index = params.index(ident)
        values = []
        for _, paren_open, paren_close in src.calls_of(owner[0]):
            args = _split_top(src.text[paren_open + 1 : paren_close])
            literal = re.fullmatch(r"\s*[\"']([\w-]+)[\"']\s*", args[index]) if index < len(args) else None
            if literal is None:
                values = []
                break
            values.append(literal.group(1))
        if values:
            return [source.replace("${" + ident + "}", v) for v in sorted(set(values))]
    return [source]


def _is_dynamic(path: str) -> bool:
    """An /api call with no fixed segment after /api names no route."""
    segments = _segments(path)
    return bool(segments) and segments[0] == "api" and all(
        s == WILD for s in segments[1:]
    )


def web_call_sites(text: str) -> set[tuple[str, str]]:
    """Every web call in one source text as (method, path template).

    A call whose method is read at run time carries ``*`` as its method; a
    call that names none carries ``UNNAMED``.
    """
    sites: set[tuple[str, str]] = set()
    src = _Source(_blank_comments(text))
    for raw, start, end in _web_literals(src.text):
        raws = [raw]
        if src.text[start] == "`" and _read_template(src.text, start)[1] == end:
            variants = (_read_template(v, 0)[0] for v in _param_variants(src, start, end))
            raws = [v for v in variants if v is not None] or [raw]
        methods = _value_methods(src, start, end) or {UNNAMED}
        for one in raws:
            path = _normalize(one)
            if not path:
                continue
            for method in methods:
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
        and "_parked" not in p.parts  # parked code is neither compiled nor served
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


def load_web_dynamic_calls() -> list[dict[str, Any]]:
    """The dynamic web calls resolved by hand."""
    return json.loads(WEB_DYNAMIC_CALLS.read_text(encoding="utf-8"))["web_dynamic_calls"]


def apply_web_dynamic_calls(
    routes: list[dict[str, Any]],
    hand: list[dict[str, Any]],
    unresolved: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Tag the routes the hand entries name; return the calls still unresolved.

    An entry that names a route the app does not serve with its method fails.
    """
    served = {(r["path"], m): r for r in routes for m in r["methods"]}
    for entry in hand:
        for path in entry["routes"]:
            route = served.get((path, entry["method"]))
            if route is None:
                raise ValueError(
                    f"{WEB_DYNAMIC_CALLS.name}: {entry['site']} names "
                    f"{entry['method']} {path}, which the app does not serve"
                )
            if "web" not in route["consumers"]:
                route["consumers"].append("web")
    covered = {(e["site"].split(":", 1)[0], e["method"]) for e in hand}
    return [c for c in unresolved if (c["file"], c["method"]) not in covered]


def build_manifest() -> dict[str, Any]:
    routes = build_app_routes()
    ios = extract_ios_calls()
    web, unresolved = extract_web_call_sites()
    routes, unmatched_ios, unmatched_web = match_consumers(routes, ios, web)
    hand = load_web_dynamic_calls()
    unresolved = apply_web_dynamic_calls(routes, hand, unresolved)
    return {
        "note": "Generated by scripts/gen_api_surface.py. Do not edit by hand.",
        "routes": routes,
        "unmatched_calls": {
            "ios": sorted(unmatched_ios),
            "web": sorted(unmatched_web),
        },
        "web_dynamic_calls": {"resolved_by_hand": hand},
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
    hand = manifest.get("web_dynamic_calls", {}).get("resolved_by_hand", [])
    if hand:
        lines += [
            "## Dynamic web calls resolved by hand",
            "",
            "These web calls have no fixed segment after `/api`.",
            "`scripts/api_surface_web_dynamic_calls.json` names the routes each one reaches,",
            "and those routes carry the web tag above.",
            "",
            "| Method | Site | Routes | Why |",
            "|---|---|---|---|",
        ]
        for call in hand:
            reached = "<br>".join(f"`{path}`" for path in call["routes"])
            lines.append(f"| {call['method']} | `{call['site']}` | {reached} | {call['why']} |")
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
