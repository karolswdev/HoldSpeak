"""HS-100-05 (B1) — the web vocabulary guard.

The glass speaks the canon (docs/internal/POSITIONING.md vocabulary
table; docs/internal/CONSTITUTION.md Article VI honesty): "intel" is
banned in user-facing copy (canonical: intelligence), "persona" is
banned as a user-facing noun (canonical: agents), and no refusal or
status string may leak an absolute filesystem path.

Mechanics mirror the token gate: today's offenders are frozen in
_ALLOWLIST and the scan must match it EXACTLY — a new offender fails
the guard, and fixing an offender forces its allowlist entry to be
deleted, so the list only shrinks. HS-100-09/10 (Agents, Settings)
burn it to zero; HS-100-12 asserts it stays empty.

Copy detection: string literals and JSX text that read as prose (a
space + at least three letters). URL/path segments (leading "/") are
code, not copy.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_WEB_SRC = _REPO / "web" / "src"

_STR_RE = re.compile(
    r'"([^"\\]*(?:\\.[^"\\]*)*)"'
    r"|'([^'\\]*(?:\\.[^'\\]*)*)'"
    r"|`([^`]*)`"
)
_JSX_TEXT_RE = re.compile(r">([^<>{}]+)<")

_BANNED = {
    "intel": re.compile(r"\bintel\b", re.IGNORECASE),
    "persona": re.compile(r"\bpersonas?\b", re.IGNORECASE),
    "abs-path": re.compile(r"/Users/|/home/\w"),
}

# HS-103-02 — the same em/en-dash-in-prose ban
# (docs/internal/POSITIONING.md voice rules) that
# test_doc_drift_guard.py::test_no_user_facing_doc_uses_dashes_in_prose
# enforces over user-facing DOCS, extended to the glass itself: neither
# existing guard covered rendered web/src copy for dashes (this one scans
# terms, that one scans docs). A template literal's `${...}` interpolation
# is stripped before the dash check so a nested code-level fallback value
# (e.g. `x || "—"`, an established "no value" glyph — see AttentionDrawer.tsx,
# CommandsCore.tsx) isn't mistaken for prose punctuation. A dash directly
# between digits (`3–4`, `F1–F12`) is a numeric range, not prose — exempt,
# per the story's own named exception.
_DASH_RE = re.compile(r"(?<!\d)[—–](?!\d)")
_INTERPOLATION_RE = re.compile(r"\$\{[^{}]*\}")

# HS-100-10 emptied the allowlist (Studio died; Settings speaks
# "intelligence"). It stays empty: any entry added here is a defect.
_ALLOWLIST: dict[str, frozenset[str]] = {}


def _sources() -> list[Path]:
    return sorted(
        p
        for p in _WEB_SRC.rglob("*.ts*")
        if ".test." not in p.name and p.suffix in {".ts", ".tsx"}
    )


# HS-103-02 — comments are source annotation, not glass the user reads;
# scanning them (the STR_RE quote-matcher previously wandered into `/** ... */`
# prose across an apostrophe, e.g. "the zone's" pairing with a later quote)
# produced false positives in both the term-ban and dash-ban rules. Only
# JSDoc-style `/** ... */` comments are blanked (newlines kept, so line
# numbers stay stable) — a bare `/*` isn't matched, since this codebase's
# comments are consistently `/**`-style and a bare `/*` can appear inside a
# real string (e.g. the `audio/*` MIME wildcard), which a naive block-comment
# match would wrongly swallow everything up to the next unrelated `*/`. Line
# comments are truncated at `//`, except a `://` (a URL) which is code, not
# a comment marker.
_BLOCK_COMMENT_RE = re.compile(r"/\*\*.*?\*/", re.DOTALL)
_LINE_COMMENT_RE = re.compile(r"(?<!:)//.*$")


def _strip_comments(text: str) -> str:
    def _blank(m: re.Match) -> str:
        return "\n".join(" " * len(chunk) for chunk in m.group(0).split("\n"))

    text = _BLOCK_COMMENT_RE.sub(_blank, text)
    return "\n".join(_LINE_COMMENT_RE.sub("", line) for line in text.split("\n"))


def _prose_segments(path: Path):
    """Yield (lineno, segment) for string-literal and JSX prose."""
    for lineno, line in enumerate(_strip_comments(path.read_text()).split("\n"), 1):
        segments = [
            next(g for g in m.groups() if g is not None)
            for m in _STR_RE.finditer(line)
        ]
        if path.suffix == ".tsx":
            segments += [m.group(1).strip() for m in _JSX_TEXT_RE.finditer(line)]
        for seg in segments:
            text = seg.strip()
            if text.startswith("/"):
                continue  # URL/path, not copy
            if " " in seg and sum(c.isalpha() for c in seg) >= 3:
                yield lineno, seg
            elif text[:1].isupper() and text.isalpha():
                # A lone Capitalized word is a display label ("Persona"
                # on a chip) — the round-8 miss. Lowercase single words
                # stay exempt: those are wire keys, not copy.
                yield lineno, text


def _scan() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for path in _sources():
        rel = str(path.relative_to(_WEB_SRC))
        for _lineno, seg in _prose_segments(path):
            for word, rx in _BANNED.items():
                if rx.search(seg):
                    found.setdefault(rel, set()).add(word)
    return found


def test_web_copy_speaks_the_canon() -> None:
    """Offenders must equal the allowlist exactly, both directions."""
    found = _scan()
    new = {
        f"{rel}: {sorted(words - _ALLOWLIST.get(rel, frozenset()))}"
        for rel, words in found.items()
        if words - _ALLOWLIST.get(rel, frozenset())
    }
    assert not new, (
        "Banned vocabulary in NEW web copy (canon: 'intelligence' not "
        "'intel', 'agents' not 'personas', never an absolute path):\n  "
        + "\n  ".join(sorted(new))
    )
    stale = {
        f"{rel}: {sorted(words - found.get(rel, set()))}"
        for rel, words in _ALLOWLIST.items()
        if words - found.get(rel, set())
    }
    assert not stale, (
        "Allowlist entries whose offender is fixed — DELETE them (the "
        "list only shrinks):\n  " + "\n  ".join(sorted(stale))
    )


def test_web_copy_has_no_dash_in_prose() -> None:
    """Em/en dashes never compose rendered UI prose (POSITIONING voice
    rules) — a hole neither this guard (terms only) nor the doc-drift
    guard (docs only) was positioned to catch until HS-103-02."""
    offenders = []
    for path in _sources():
        rel = str(path.relative_to(_WEB_SRC))
        for lineno, seg in _prose_segments(path):
            if _DASH_RE.search(_INTERPOLATION_RE.sub("", seg)):
                offenders.append(f"{rel}:{lineno}: {seg.strip()[:80]}")
    assert not offenders, (
        "Em/en dashes in rendered UI prose (compose with a period, comma, "
        "colon, or parentheses instead — POSITIONING.md voice rules):\n  "
        + "\n  ".join(sorted(offenders))
    )


def test_dash_guard_patterns_catch_seeded_violations() -> None:
    """Proven both ways, like the vocabulary guard above."""
    stripped = lambda s: _DASH_RE.search(_INTERPOLATION_RE.sub("", s))
    for hit in (
        "Pipeline is off — speaking still works",
        "Needs you — 3",
        "'task — owner — due'",
    ):
        assert stripped(hit), hit
    for keep in (
        "3–4 tight sentences",  # a numeric range, not prose
        "F1–F12",  # a numeric range, not prose
        'budget ${presentValue(x) || "—"} ms',  # a nested placeholder value
        "Pipeline off. Speaking still works.",
        "Needs you: 3",
    ):
        assert not stripped(keep), keep


def test_comment_stripping_does_not_blank_real_code() -> None:
    """A bare `/*` inside a string (a MIME wildcard) must not be mistaken
    for a JSDoc comment open and swallow real code up to the next `*/`."""
    src = (
        'const accept = "audio/*,.wav";\n'
        "/** a real comment */\n"
        'const label = "Drop it here";\n'
    )
    stripped = _strip_comments(src)
    assert "audio/*" in stripped
    assert "Drop it here" in stripped
    assert "a real comment" not in stripped
    assert stripped.count("\n") == src.count("\n")


def test_refusals_never_leak_paths() -> None:
    """No web copy carries an absolute filesystem path, allowlist or not."""
    found = _scan()
    leaks = sorted(rel for rel, words in found.items() if "abs-path" in words)
    assert not leaks, "Absolute paths in user-facing copy:\n  " + "\n  ".join(leaks)


def test_guard_patterns_catch_seeded_violations() -> None:
    """Proven both ways, like the voice guard."""
    for hit in ("Intel model not found", "the intel summary", "New Persona",
                "Personas and coders", "Persona", "Intel"):
        assert any(rx.search(hit) for rx in _BANNED.values()), hit
    for keep in ("Meeting intelligence", "intelligent routing",
                 "personal notes stay local"):
        assert not _BANNED["intel"].search(keep) and not _BANNED[
            "persona"
        ].search(keep), keep


def test_backend_refusal_names_its_fix() -> None:
    """The model-missing refusal points at Settings and carries no path
    (the trace-C conviction, UIUX_JUDGMENT §1/§5.5)."""
    providers = (_REPO / "holdspeak" / "intel" / "providers.py").read_text()
    engine = (_REPO / "holdspeak" / "intel" / "engine.py").read_text()
    for src in (providers, engine):
        assert "Intel model not found" not in src
        assert "No language model on this hub" in src
