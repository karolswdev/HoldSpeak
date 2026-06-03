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
