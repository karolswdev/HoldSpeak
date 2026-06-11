"""HS-32-06: a lightweight guard against the worst doc-rot returning.

The phase-29 plugin rollout made every built-in real — **zero**
``DeterministicPlugin`` stubs remain, locked at the code level by
``test_decision_announcement_drafter_plugin.py::test_no_deterministic_stub_remains``.
This guard stops the *docs* from drifting back to claiming stubs exist (the most
actively misleading historical doc-rot — see HS-32-06).

Scope is **non-PMO** live docs (`docs/*.md`, excluding `docs/evidence/` snapshots);
the PMO roadmap corpus is the historical record and is kept verbatim by design.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
# Matches a per-plugin stub claim like: `**stub** (`DeterministicPlugin`)`.
_STUB_CLAIM = re.compile(r"\*\*stub\*\*\s*\(\s*`?DeterministicPlugin", re.IGNORECASE)


def _live_docs() -> list[Path]:
    docs = _REPO / "docs"
    return [
        p
        for p in docs.rglob("*.md")
        if "/evidence/" not in p.as_posix()
    ]


def test_no_live_doc_claims_a_deterministicplugin_stub() -> None:
    offenders: list[str] = []
    for path in _live_docs():
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _STUB_CLAIM.search(line):
                offenders.append(f"{path.relative_to(_REPO)}:{lineno}: {line.strip()}")

    assert not offenders, (
        "A live doc claims a built-in is a `DeterministicPlugin` stub, but zero "
        "stubs remain (locked by test_no_deterministic_stub_remains). Reconcile "
        "these stale lines:\n  " + "\n  ".join(offenders)
    )


def test_drift_guard_actually_scans_docs() -> None:
    """Sanity: the guard sees real files (so a green result isn't vacuous)."""
    docs = _live_docs()
    assert len(docs) > 5
    assert any(p.name == "PLAN_ARCHITECT_PLUGIN_SYSTEM.md" for p in docs)


# HS-33-03: a lightweight link-check so the `docs/` reorg (and future moves)
# can't silently leave a dangling relative link. Scope is the same live-docs
# set; the PMO corpus + evidence snapshots are frozen history and excluded.
_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def test_no_live_doc_has_a_dangling_relative_link() -> None:
    offenders: list[str] = []
    for path in _live_docs():
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for target in _MD_LINK.findall(line):
                target = target.strip()
                # Skip external, anchor-only, and non-doc targets.
                if target.startswith(("http://", "https://", "mailto:", "#", "<")):
                    continue
                # Drop any #fragment / ?query suffix.
                rel = target.split("#", 1)[0].split("?", 1)[0]
                if not rel:
                    continue
                resolved = (path.parent / rel).resolve()
                if not resolved.exists():
                    offenders.append(
                        f"{path.relative_to(_REPO)}:{lineno}: -> {target}"
                    )

    assert not offenders, (
        "A live doc links a path that does not exist (dangling relative link). "
        "Fix the path or the move:\n  " + "\n  ".join(offenders)
    )


# HS-46-01: the README headlines a built-in-plugin count ("ships **14 built-in
# plugins**"). That number drifted before and is exactly the kind of "cool fact"
# the docs lead with — pin it to the registry so it can't silently rot. Cheap:
# one import + one regex.
_PLUGIN_COUNT_CLAIM = re.compile(r"(\d+)\s+built-in plugins", re.IGNORECASE)


def test_readme_plugin_count_matches_registry() -> None:
    from holdspeak.plugins.builtin import _BUILTIN_PLUGIN_DEFS

    registry_count = len(_BUILTIN_PLUGIN_DEFS)
    readme = (_REPO / "README.md").read_text(encoding="utf-8")
    claims = [int(m) for m in _PLUGIN_COUNT_CLAIM.findall(readme)]

    assert claims, (
        "README no longer states a built-in-plugin count ('N built-in plugins'). "
        "If the phrasing changed, update this guard; otherwise restore the count."
    )
    mismatched = [n for n in claims if n != registry_count]
    assert not mismatched, (
        f"README advertises {mismatched} built-in plugins but the registry has "
        f"{registry_count} (holdspeak/plugins/builtin/_BUILTIN_PLUGIN_DEFS). "
        "Reconcile the count and the plugin table."
    )


# HS-46-04: real UI screenshots + pixellab art are embedded via HTML `<img src>`
# (for width/centering), which the markdown-link guard above does NOT see. Guard
# every local image reference — markdown `![](...)` *and* `<img src="...">`, across
# the README *and* the live docs — so a renamed/missing asset can't ship a broken
# image. (The markdown-link guard already covers `![](...)` in docs; this adds the
# HTML tags and the root README.)
_IMG_TAG_SRC = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']", re.IGNORECASE)
_MD_IMG = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def _docs_with_images() -> list[Path]:
    return [_REPO / "README.md", *_live_docs()]


def test_all_embedded_image_refs_resolve() -> None:
    offenders: list[str] = []
    for path in _docs_with_images():
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            for src in _IMG_TAG_SRC.findall(line) + _MD_IMG.findall(line):
                src = src.strip()
                if src.startswith(("http://", "https://", "data:", "#", "<")):
                    continue
                rel = src.split("#", 1)[0].split("?", 1)[0]
                if not rel:
                    continue
                if not (path.parent / rel).resolve().exists():
                    offenders.append(f"{path.relative_to(_REPO)}:{lineno}: -> {src}")

    assert not offenders, (
        "A doc embeds an image whose path does not resolve (renamed/missing asset). "
        "Fix the path or restore the file:\n  " + "\n  ".join(offenders)
    )


# HS-51-03: keep internal roadmap/process vocabulary out of the user-facing docs.
# Phase 51 scrubbed `Phase NN` / `HS-NN-NN` / `PMO` / "the current roadmap" /
# "closeout" from the guides a user or operator actually reads, and rewrote the
# phase-relative claims into product-tense. This guard stops them coming back.
#
# Scope is DELIBERATELY NARROWER than _live_docs() above: the user-facing surface is
# the root README plus the top-level guides `docs/*.md`. The internal corpus
# (docs/internal/**, docs/evidence/**, docs/assets/**, and pm/roadmap/**) is the
# historical/internal record and keeps its phase/story vocabulary by design, so it
# is NOT scanned. Patterns are case-insensitive: lowercase "phase 15" leaks were
# real (see Phase 51 HS-51-02), and the patterns stay narrow enough that the kept
# architecture spec names MIR-01 / DIR-01 / WFS-01 never match.
_ROADMAP_VOCAB = re.compile(
    r"\bHS-\d{1,2}(?:-\d+)?\b"    # story ids: HS-25, HS-17-05, HS-9-03
    r"|\bphase[ -]\d+\b"          # phase tags: Phase 15, phase-37, phase 9
    r"|\bPMO\b"
    r"|the current roadmap"
    r"|\bcloseout\b",
    re.IGNORECASE,
)


def _user_facing_docs() -> list[Path]:
    """The docs a user/operator actually reads: root README + top-level docs/*.md.

    Non-recursive on purpose, so docs/internal/, docs/evidence/, and docs/assets/
    are excluded; they keep roadmap vocabulary by design.
    """
    return [_REPO / "README.md", *sorted((_REPO / "docs").glob("*.md"))]


def test_no_user_facing_doc_leaks_roadmap_vocabulary() -> None:
    offenders: list[str] = []
    for path in _user_facing_docs():
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _ROADMAP_VOCAB.search(line):
                offenders.append(f"{path.relative_to(_REPO)}:{lineno}: {line.strip()}")

    assert not offenders, (
        "A user-facing doc leaks internal roadmap vocabulary (Phase NN / HS-NN-NN / "
        "PMO / 'the current roadmap' / 'closeout'). User-facing docs speak in "
        "product-tense; the internal corpus (docs/internal, docs/evidence, "
        "docs/assets, pm/roadmap) is where that vocabulary belongs. Reword these in "
        "product-tense, see docs/internal/DOCS_STYLE.md:\n  " + "\n  ".join(offenders)
    )


def test_roadmap_vocab_guard_scans_real_user_facing_docs() -> None:
    """Sanity: the guard sees the real user-facing set, so a green run isn't vacuous,
    and the internal corpus is genuinely out of scope."""
    docs = _user_facing_docs()
    names = {p.name for p in docs}
    assert (_REPO / "README.md") in docs
    assert {"CONNECTOR_DEVELOPMENT.md", "DEVICE_PROTOCOL.md", "SECURITY.md"} <= names
    assert len(docs) > 5
    # The internal corpus keeps phase/story vocabulary and must NOT be scanned.
    assert (_REPO / "docs/internal/DOCS_STYLE.md") not in docs
    assert not any(p.parent.name in ("internal", "evidence", "assets") for p in docs)


def test_roadmap_vocab_pattern_is_narrow_enough_to_keep_spec_names() -> None:
    """The pattern flags phase/story tags but never the kept architecture spec names
    (MIR-01 / DIR-01 / WFS-01) or bare 'phase' with no number."""
    for leak in ("Phase 15", "phase-37", "phase 9", "HS-25-03", "HS-17-05",
                 "HS-9-03",  # single-digit phase — leaked past the old pattern (found live)
                 "the current roadmap", "PMO", "from HS-19 closeout"):
        assert _ROADMAP_VOCAB.search(leak), f"guard should flag {leak!r}"
    for keep in ("the DIR-01 dictation pipeline spec",
                 "the MIR-01 meeting-side routing spec",
                 "WFS-01", "a phased rollout",
                 "the actuator phase of the pipeline"):
        assert not _ROADMAP_VOCAB.search(keep), f"guard should NOT flag {keep!r}"


def test_qlippy_doc_states_the_guarantees_verbatim() -> None:
    """HS-56-06: the mascot doc must keep the never-acts guarantee and the three
    privacy answers verbatim-checkable (the same markers the cards render)."""
    guide = (_REPO / "docs" / "INTELLIGENT_TYPING_GUIDE.md").read_text()
    assert "Qlippy, the mascot" in guide
    assert "never acts on his own" in guide
    for marker in ('"Data used:"', '"If you approve, this goes to"', '"Your controls:"'):
        assert marker in guide, f"privacy answer missing from the guide: {marker}"
    # The cards themselves render the same three markers (locked in
    # qlippy-events.js); the doc and the UI cannot drift apart silently.
    events = (_REPO / "web" / "src" / "scripts" / "qlippy-events.js").read_text()
    for marker in ("Data used:", "If you approve, this goes to", "Your controls:"):
        assert marker in events


# ── HS-58-05: the voice guard ────────────────────────────────────────────────
# Phase 51 guards WHAT user-facing docs say (no roadmap vocabulary); this
# guards HOW they say it, per docs/internal/POSITIONING.md: no em/en dashes
# in prose, none of the high-frequency AI-vocabulary tells, and no banned
# synonyms for canonical feature names. Fenced code blocks are exempt
# (example code and shell output are not prose), as are the explicitly
# allowlisted verbatim UI quotes below.

# Lines that quote real UI strings verbatim (the UI may contain dashes; the
# doc must match the UI exactly). Keyed by a stable substring of the line.
_VERBATIM_UI_QUOTES = (
    'with "Preview only — nothing',  # journal replay note (web/src/scripts/dictation/journal.js)
)

_AI_VOCAB = re.compile(
    r"\bdelve[sd]?\b|\bdelving\b"
    r"|\bseamless(?:ly)?\b"
    r"|\bleverag(?:es|ing)\b"        # the verb; compounds like "highest-leverage" stay
    r"|\bsupercharge[sd]?\b"
    r"|\beffortless(?:ly)?\b"
    r"|\bgame[- ]chang\w+"
    r"|\bcutting[- ]edge\b"
    r"|\bis a testament\b"
    # The negative-parallelism TIC only ("it's not just X, it's Y"); a plain
    # logical "not just X" ("every meeting, not just the visible page") is
    # legitimate prose and stays legal.
    r"|\b(?:it|this|that)'?s not just\b|\bisn'?t just\b|\baren'?t just\b"
    r"|\bnot merely\b",
    re.IGNORECASE,
)

# Banned synonyms for canonical feature names (POSITIONING.md table).
_BANNED_NAMES = re.compile(
    r"\bvoice macros?\b"             # canonical: voice commands
    r"|\bintelligent dictation\b",   # canonical: the dictation pipeline
    re.IGNORECASE,
)


def _prose_lines(path: Path):
    """Yield (lineno, line) for non-code-block lines of a doc."""
    fenced = False
    for lineno, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            yield lineno, line


def test_no_user_facing_doc_uses_dashes_in_prose() -> None:
    offenders = []
    for doc in _user_facing_docs():
        for lineno, line in _prose_lines(doc):
            if "—" not in line and "–" not in line:
                continue
            if any(marker in line for marker in _VERBATIM_UI_QUOTES):
                continue
            offenders.append(f"{doc.relative_to(_REPO)}:{lineno}: {line.strip()[:80]}")
    assert not offenders, (
        "Em/en dashes in user-facing prose (use a period, comma, colon, or "
        "parentheses — see docs/internal/POSITIONING.md voice rules; verbatim "
        "UI quotes belong in _VERBATIM_UI_QUOTES):\n  " + "\n  ".join(offenders)
    )


def test_no_user_facing_doc_uses_ai_vocabulary() -> None:
    offenders = []
    for doc in _user_facing_docs():
        for lineno, line in _prose_lines(doc):
            match = _AI_VOCAB.search(line)
            if match:
                offenders.append(
                    f"{doc.relative_to(_REPO)}:{lineno}: {match.group(0)!r}"
                )
    assert not offenders, (
        "AI-vocabulary tells in user-facing docs (reword per "
        "docs/internal/POSITIONING.md voice rules):\n  " + "\n  ".join(offenders)
    )


def test_no_user_facing_doc_uses_banned_feature_names() -> None:
    offenders = []
    for doc in _user_facing_docs():
        for lineno, line in _prose_lines(doc):
            match = _BANNED_NAMES.search(line)
            if match:
                offenders.append(
                    f"{doc.relative_to(_REPO)}:{lineno}: {match.group(0)!r}"
                )
    assert not offenders, (
        "Non-canonical feature names (the canonical table lives in "
        "docs/internal/POSITIONING.md):\n  " + "\n  ".join(offenders)
    )


def test_voice_guard_patterns_catch_seeded_violations() -> None:
    """Proven both ways: each pattern flags what it must and spares what it must."""
    for hit in ("we delve into", "a seamless flow", "leverages the runtime",
                "it isn't just a tool", "it's not just a transcript",
                "not merely a wrapper"):
        assert _AI_VOCAB.search(hit), f"AI-vocab pattern should flag {hit!r}"
    for keep in ("the highest-leverage way", "elevated artifact cards",
                 "cut leverage ratios",
                 "every meeting, not just the visible page"):  # plain logic stays legal
        assert not _AI_VOCAB.search(keep), f"AI-vocab pattern should NOT flag {keep!r}"
    for hit in ("configure voice macros", "intelligent dictation mode"):
        assert _BANNED_NAMES.search(hit), f"name pattern should flag {hit!r}"
    assert not _BANNED_NAMES.search("voice commands fire on keywords")
