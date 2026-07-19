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

# Today's offenders, frozen. Shrink-only: entries may ONLY be removed.
_ALLOWLIST: dict[str, frozenset[str]] = {
    "desk/components/DeskToolShelf.tsx": frozenset({"persona"}),
    "desk/components/PersonaChat.tsx": frozenset({"persona"}),
    "desk/components/SurfaceWindows.tsx": frozenset({"persona"}),
    "desk/store.ts": frozenset({"persona"}),
    "pages/cores/CompanionCore.tsx": frozenset({"persona"}),
    "pages/cores/SettingsCore.tsx": frozenset({"intel"}),
    "pages/cores/StudioCore.tsx": frozenset({"persona"}),
}


def _sources() -> list[Path]:
    return sorted(
        p
        for p in _WEB_SRC.rglob("*.ts*")
        if ".test." not in p.name and p.suffix in {".ts", ".tsx"}
    )


def _prose_segments(path: Path):
    """Yield (lineno, segment) for string-literal and JSX prose."""
    for lineno, line in enumerate(path.read_text().split("\n"), 1):
        segments = [
            next(g for g in m.groups() if g is not None)
            for m in _STR_RE.finditer(line)
        ]
        if path.suffix == ".tsx":
            segments += [m.group(1).strip() for m in _JSX_TEXT_RE.finditer(line)]
        for seg in segments:
            if seg.strip().startswith("/"):
                continue  # URL/path, not copy
            if " " in seg and sum(c.isalpha() for c in seg) >= 3:
                yield lineno, seg


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


def test_refusals_never_leak_paths() -> None:
    """No web copy carries an absolute filesystem path, allowlist or not."""
    found = _scan()
    leaks = sorted(rel for rel, words in found.items() if "abs-path" in words)
    assert not leaks, "Absolute paths in user-facing copy:\n  " + "\n  ".join(leaks)


def test_guard_patterns_catch_seeded_violations() -> None:
    """Proven both ways, like the voice guard."""
    for hit in ("Intel model not found", "the intel summary", "New Persona",
                "Personas and coders"):
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
