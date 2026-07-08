"""The rail event log (WLA-13-04).

Append-only JSONL at `.git/pmo-events.jsonl` — beside the contract
archive, surviving aborted commits, never itself committed. One
line per rail moment, carrying rails metadata only. Contract:
docs/mission-control.md §3.

The consent stance is enforced in code, not promised: `emit` only
writes whitelisted event types, only the detail keys each type
declares, only scalar values, truncated — a rogue caller cannot
smuggle diff or transcript content into the log. And telemetry
never breaks the rails: emission failures are swallowed, because a
full disk must not block a story flip.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

EVENTS_REL = Path(".git") / "pmo-events.jsonl"

_MAX_VALUE_CHARS = 200

# Taxonomy v1 — the moments the machinery already observes, and the
# only detail keys each may carry (docs/mission-control.md §3).
EVENT_TYPES: dict[str, frozenset[str]] = {
    "story_status": frozenset({"from", "to"}),
    "evidence_capture": frozenset({"exit_code", "timestamp"}),
    "gate_pass": frozenset({"stories"}),
    "gate_refusal": frozenset({"rule"}),
    "contract_generated": frozenset({"stories"}),
    "phase_created": frozenset({"phase"}),
    "phase_closed": frozenset({"phase"}),
}


def events_path(root: Path) -> Path:
    return root / EVENTS_REL


def _clean_scalar(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    text = str(value)
    return text[:_MAX_VALUE_CHARS]


def emit(
    root: Path,
    event: str,
    *,
    project: str | None = None,
    story: str | None = None,
    detail: dict | None = None,
    tree: str | None = None,
) -> None:
    """Append one event line; never raises, never blocks the rails."""
    try:
        allowed = EVENT_TYPES.get(event)
        if allowed is None:
            return
        git_dir = root / ".git"
        if not git_dir.is_dir():
            return
        clean_detail = {
            key: _clean_scalar(value)
            for key, value in (detail or {}).items()
            if key in allowed
        }
        if tree is None:
            from .gitio import write_tree

            tree = write_tree(root) or "unknown"
        line = json.dumps(
            {
                "ts": datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "event": event,
                "project": _clean_scalar(project),
                "story": _clean_scalar(story),
                "detail": clean_detail,
                "tree": tree,
            },
            sort_keys=True,
        )
        with events_path(root).open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except Exception:
        return


def read_events(root: Path, tail: int | None = None) -> list[dict]:
    path = events_path(root)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    if tail is not None:
        lines = lines[-tail:]
    out: list[dict] = []
    for line in lines:
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            out.append(parsed)
    return out
