"""Static guard against the Alpine "null member read under a false x-show" class.

Twice now a latent bug shipped where an Alpine binding evaluated a member read
on a field that is initialised to ``null`` in the page's ``x-data`` — and threw
on the very first paint, because Alpine still evaluates ``x-text`` / ``x-html``
/ ``x-show`` / ``:attr`` expressions even when an enclosing ``x-show`` is false
(``x-show`` toggles ``display``, it does not remove the node or stop its
bindings from running). The two real shipped instances were:

  * ``routePreview.active_intents`` on ``/``   (routePreview: null)
  * ``filing.id`` / ``filing.title`` on ``/desk`` (filing: null)

The route pre-flight e2e (``tests/e2e/test_route_preflight.py``) catches these
by loading every page in a real browser and asserting zero ``pageerror`` — but
CI has no Chromium, so that test *skips*. This pure-Python static scan makes CI
enforce the same class without a browser.

What it flags: an ``x-text`` / ``x-html`` / ``x-show`` / ``:attr`` binding that
reads ``IDENT.prop`` (dot access) where ``IDENT`` is a field this page/script
initialises to ``null``, and the read is *not* protected by optional chaining
(``IDENT?.prop``) or a same-expression truthiness guard (``IDENT && IDENT.x``).

Precision (to avoid false positives) — a read is considered SAFE when:

  * it uses optional chaining: ``IDENT?.prop`` (or ``IDENT?.[`` ),
  * the expression guards it: ``IDENT && …`` appears before the read, or
  * the binding lives inside a ``<template x-if="IDENT …">`` / ``x-for`` whose
    condition is on ``IDENT`` — Alpine's ``<template x-if>`` actually removes
    the subtree from the DOM, so member reads there never run while null.

Only idents this file can *see* initialised to ``null`` (in the page itself or
one of its imported ``../scripts/*.js`` factories) are ever considered, so an
unrelated always-an-object field is never flagged.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_PAGES = _REPO / "web" / "src" / "pages"
_SCRIPTS = _REPO / "web" / "src" / "scripts"

# The Alpine binding directives whose expressions Alpine evaluates eagerly on
# every render regardless of any enclosing x-show. (We deliberately do NOT scan
# @event / x-on handlers or x-model — those run on interaction, not on paint.)
_DIRECTIVE_RE = re.compile(
    r"""(?:^|\s)(
        x-text | x-html | x-show |   # plain directives
        :[A-Za-z][\w:-]*             # :attr shorthand bindings (:class, :disabled, …)
    )=(?P<q>["'])(?P<expr>.*?)(?P=q)""",
    re.VERBOSE | re.DOTALL,
)

# A field declared `IDENT: null,` at the top level of an x-data object literal.
_NULL_FIELD_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*:\s*null\s*,", re.MULTILINE)

# `<template x-if="…">` / `<template x-for="… in …">` opening tags — these guard
# their subtree (Alpine removes it from the DOM when the condition is falsy).
_TEMPLATE_OPEN_RE = re.compile(
    r"""<template\b[^>]*\b(?:x-if|x-for)=(["'])(?P<cond>.*?)\1""",
    re.DOTALL,
)
_TEMPLATE_CLOSE = "</template>"

# Reserved JS globals / Alpine magics that look like idents but are never
# x-data null fields — never treat these as the scanned ident.
_RESERVED = {"window", "document", "Array", "Object", "JSON", "Math", "$el", "$refs"}


def _null_fields(*sources: str) -> set[str]:
    """Names initialised to ``null`` across the given source bodies."""
    fields: set[str] = set()
    for src in sources:
        fields.update(_NULL_FIELD_RE.findall(src))
    return fields - _RESERVED


def _imported_scripts(page_text: str) -> list[Path]:
    """The ``../scripts/<name>.js`` files a page pulls into its x-data scope."""
    out: list[Path] = []
    for name in re.findall(r"scripts/([A-Za-z][\w-]*)\.js", page_text):
        p = _SCRIPTS / f"{name}.js"
        if p.exists():
            out.append(p)
    return out


def _strip_strings(expr: str) -> str:
    """Blank out JS string/template literals so we don't read into their text.

    Replaces the *contents* of '...', "...", and `...` with spaces (keeping
    length so offsets are stable) — a property name that only appears inside a
    string literal is not a real member read.
    """
    out = list(expr)
    i = 0
    n = len(expr)
    while i < n:
        ch = expr[i]
        if ch in "'\"`":
            quote = ch
            i += 1
            while i < n and expr[i] != quote:
                if expr[i] == "\\":
                    out[i] = " "
                    i += 1
                    if i < n:
                        out[i] = " "
                        i += 1
                    continue
                out[i] = " "
                i += 1
            # leave the closing quote (or EOF)
        i += 1
    return "".join(out)


def _unguarded_reads(expr: str, fields: set[str]) -> list[str]:
    """Member reads ``IDENT.prop`` in *expr* (IDENT in *fields*) lacking a guard.

    Guards accepted:
      * optional chaining at the access site: ``IDENT?.``
      * a truthiness guard anywhere in the expression: ``IDENT &&`` /
        ``IDENT ?`` (ternary) / ``IDENT ||`` short-circuit, or a ``!IDENT``
        style check.
    """
    clean = _strip_strings(expr)
    hits: list[str] = []
    for ident in fields:
        # Does the expression establish a truthiness guard for this ident?
        # e.g. `routePreview && routePreview.active_intents`,
        #      `filing ? filing.x : y`, `!filing || filing.x`.
        guarded_expr = re.search(
            rf"(?<![\w.]){re.escape(ident)}\s*(?:&&|\?(?!\.)|\|\|)", clean
        ) or re.search(rf"!\s*{re.escape(ident)}\b", clean)

        # Every plain `IDENT.prop` (dot, not `?.`) that is a *read* of the field
        # (not preceded by another `.`/`?` — so `a.IDENT.b` is a read of `a`).
        for m in re.finditer(rf"(?<![\w.?]){re.escape(ident)}(\?)?\.\s*\w", clean):
            optional = m.group(1) == "?"
            if optional:
                continue  # IDENT?.prop — safe
            if guarded_expr:
                continue  # a truthiness guard for IDENT is present in the expr
            hits.append(f"{ident}.{clean[m.end() - 1]}…")
    return hits


def _template_guarded_spans(text: str, fields: set[str]) -> list[tuple[int, int, str]]:
    """Char spans guarded by an enclosing ``<template x-if/x-for>`` on a field.

    Returns (start, end, ident) for each template block whose condition names a
    null field — bindings inside that span are DOM-removed when the field is
    falsy, so member reads on that ident are safe there.
    """
    spans: list[tuple[int, int, str]] = []
    for m in _TEMPLATE_OPEN_RE.finditer(text):
        cond = m.group("cond")
        idents = {f for f in fields if re.search(rf"(?<![\w.]){re.escape(f)}\b", cond)}
        if not idents:
            continue
        # Find the matching </template> accounting for nesting.
        depth = 1
        scan = m.end()
        while depth and scan < len(text):
            nxt_open = text.find("<template", scan)
            nxt_close = text.find(_TEMPLATE_CLOSE, scan)
            if nxt_close == -1:
                scan = len(text)
                break
            if nxt_open != -1 and nxt_open < nxt_close:
                depth += 1
                scan = nxt_open + len("<template")
            else:
                depth -= 1
                scan = nxt_close + len(_TEMPLATE_CLOSE)
        for ident in idents:
            spans.append((m.start(), scan, ident))
    return spans


def _scan_file(path: Path, fields: set[str]) -> list[str]:
    """Unguarded null-field member reads in *path*'s Alpine bindings."""
    text = path.read_text(encoding="utf-8")
    guard_spans = _template_guarded_spans(text, fields)
    problems: list[str] = []
    for m in _DIRECTIVE_RE.finditer(text):
        directive = m.group(1)
        expr = m.group("expr")
        pos = m.start("expr")
        # Drop fields that are template-guarded at this position.
        local_fields = {
            f
            for f in fields
            if not any(s <= pos < e and ident == f for (s, e, ident) in guard_spans)
        }
        for read in _unguarded_reads(expr, local_fields):
            problems.append(f'{path.name}: {directive}="{expr.strip()}" reads {read}')
    return problems


def _page_targets() -> list[tuple[Path, set[str], list[Path]]]:
    """Each page with the null fields in scope (page + imported scripts)."""
    targets: list[tuple[Path, set[str], list[Path]]] = []
    for page in sorted(_PAGES.glob("*.astro")):
        page_text = page.read_text(encoding="utf-8")
        scripts = _imported_scripts(page_text)
        fields = _null_fields(page_text, *(s.read_text(encoding="utf-8") for s in scripts))
        targets.append((page, fields, scripts))
    return targets


def test_pages_dir_present() -> None:
    """Sanity: the web source we scan actually exists (catches a path drift)."""
    assert _PAGES.is_dir(), f"expected web pages at {_PAGES}"
    assert list(_PAGES.glob("*.astro")), "no .astro pages found to scan"


def test_no_unguarded_null_member_reads_in_alpine_bindings() -> None:
    """No Alpine binding reads ``nullField.prop`` without ``?.`` or a guard."""
    problems: list[str] = []
    for page, fields, scripts in _page_targets():
        if not fields:
            continue
        problems.extend(_scan_file(page, fields))
        # Scripts can also embed Alpine bindings inside template-string HTML.
        for script in scripts:
            problems.extend(_scan_file(script, fields))

    assert not problems, (
        "Alpine binding reads a null-initialised x-data field member without "
        "optional chaining (`?.`) or a guard — it throws on first paint even "
        "under a false x-show (the bug class that broke / and /desk). Use "
        "`field?.prop` or `field && field.prop`:\n  " + "\n  ".join(sorted(problems))
    )


def test_guard_detects_a_reintroduced_bug() -> None:
    """The detector itself fires on the exact historical regressions.

    A behavioural lock so the guard can't silently rot into a no-op: feed it the
    two patterns that actually shipped and assert each is flagged, and assert
    the fixed forms are not.
    """
    fields = {"routePreview", "filing"}

    # The historical bugs — must be flagged.
    assert _unguarded_reads("routePreview.active_intents.join(', ')", fields)
    assert _unguarded_reads("filing.id", fields)
    assert _unguarded_reads(
        "filing && filing.id || other.id", {"routePreview", "filing", "other"}
    )[0].startswith("other")

    # The shipped fixes — must NOT be flagged.
    assert not _unguarded_reads("(routePreview?.active_intents || []).join(', ')", fields)
    assert not _unguarded_reads("routePreview && routePreview.active_intents", fields)
    assert not _unguarded_reads("filing && filing.title", fields)
    assert not _unguarded_reads("filing ? filing.id : null", fields)

    # A property name living only inside a string literal is not a read.
    assert not _unguarded_reads("`filing.id is null`", fields)
    # A member read on something else that merely contains the name is not it.
    assert not _unguarded_reads("state.routePreview.x", fields)


if __name__ == "__main__":  # pragma: no cover - manual debugging aid
    raise SystemExit(pytest.main([__file__, "-q"]))
