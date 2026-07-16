"""The rail event log (WLA-13-04; cursors and worktree truth HS-94-01).

Append-only JSONL at `<git common dir>/pmo-events.jsonl` — beside
the contract archive, surviving aborted commits, never itself
committed. One line per rail moment, carrying rails metadata only.
Contract: docs/mission-control.md §3.

The location is the COMMON git dir, resolved with git plumbing:
a linked `git worktree` has a `.git` FILE, and the old
`root / ".git"` directory assumption silently disabled the journal
there. Sharing the common dir is deliberate — every worktree of one
repository appends to ONE event stream, and a reader in any
worktree sees the whole timeline; the `tree` field on each event
keeps parallel work distinguishable.

The consent stance is enforced in code, not promised: `emit` only
writes whitelisted event types, only the detail keys each type
declares, only scalar values, truncated — a rogue caller cannot
smuggle diff or transcript content into the log. And telemetry
never breaks the rails: emission failures are swallowed, because a
full disk must not block a story flip.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

EVENTS_FILENAME = "pmo-events.jsonl"
# Historical constant (primary-checkout layout); resolution now goes
# through events_path(), which honors linked worktrees.
EVENTS_REL = Path(".git") / EVENTS_FILENAME

# The cursor-addressable envelope version (`dw events --json --after`),
# versioned independently of feed_schema per PLATFORM-CONTRACT §5.2.
EVENTS_SCHEMA = 2

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


def _git_common_dir(root: Path) -> Path | None:
    """The repository's common git dir via `git rev-parse` — never a
    manual parse of a `.git` file. None when root is not a work tree
    (emit no-ops, reads are empty; telemetry never invents a home)."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--git-common-dir"],
            stdin=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    if not out:
        return None
    common = Path(out)
    if not common.is_absolute():
        common = root / common
    return common if common.is_dir() else None


def events_path(root: Path) -> Path | None:
    common = _git_common_dir(root)
    if common is None:
        return None
    return common / EVENTS_FILENAME


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
        path = events_path(root)
        if path is None:
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
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except Exception:
        return


def _read_lines(root: Path) -> list[str]:
    path = events_path(root)
    if path is None or not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def read_events(root: Path, tail: int | None = None) -> list[dict]:
    lines = _read_lines(root)
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


def read_events_after(root: Path, cursor: int | None = None) -> dict:
    """Cursor-addressable read (events_schema 2, HS-94-01).

    The cursor is the count of journal lines already consumed. The
    journal is append-only, so the physical line number is a stable,
    monotonic event id: replaying `--after <cursor>` returns no
    duplicates and skips no events. Malformed lines keep their
    number (cursors never shift) but are never returned. The legacy
    bare-array read above is unchanged for feed_schema-era consumers.
    """
    after = max(0, int(cursor or 0))
    lines = _read_lines(root)
    events: list[dict] = []
    for seq, line in enumerate(lines, start=1):
        if seq <= after:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            events.append({**parsed, "event_id": str(seq)})
    return {
        "events_schema": EVENTS_SCHEMA,
        "source_cursor": str(len(lines)),
        "events": events,
    }
