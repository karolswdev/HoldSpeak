"""Session-to-story correlation (WLA-13-03).

`dw sessions --json` joins HoldSpeak's agent-session registry —
read-only, never written — to the rails: each live agent session is
resolved to the in-progress stories of the rails repo its hook
already identified (`repo_root`), with honest outcomes when the
join cannot be exact. Contract: docs/mission-control.md §2.

Correlation is its own document (`sessions_schema`), not a feed
key: the feed (§1) is per-repo and frozen; sessions span every
repo on the desk and carry desk-runtime state. Clients merge them.

The registry is desk-runtime state on a 0.x project. Verified live
2026-07-04: the file is `{"version": 1, "sessions": {"<agent>:<id>":
{record}}}`; the record fields this module reads are pinned in
`OBSERVED_REGISTRY_FIELDS` and every read is defensive. A registry
`version` other than 1 yields the polite failure shape, the pack
precedent.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .model import normalize_status
from .parse import discover_phases, discover_projects, parse_story_rows

SESSIONS_SCHEMA = 1
REGISTRY_VERSION = 1
STALE_TTL_SECONDS = 30 * 60  # contract §2

DEFAULT_REGISTRY_PATH = (
    Path.home() / ".config" / "holdspeak" / "agent_sessions.json"
)

# The registry record fields this module consumes, as observed live
# on holdspeak main (2026-07-04). Reads are defensive; this list is
# the compatibility pin, exercised by the test fixtures.
OBSERVED_REGISTRY_FIELDS = (
    "agent",
    "session_id",
    "model",
    "repo_root",
    "project_name",
    "awaiting_response",
    "last_assistant_text",
    "tmux_session",
    "tmux_window",
    "tmux_pane",
    "updated_at",
)

_IN_PROGRESS = {"in-progress"}


def _parse_ts(raw: object) -> datetime | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_rails_repo(root: Path) -> bool:
    return (root / "pm" / "roadmap").is_dir() and (
        root / ".githooks" / "dw"
    ).is_file()


def _in_progress_stories(root: Path) -> list[dict] | None:
    """In-progress stories of a rails repo, or None when the roadmap
    cannot be read (the `unreadable` outcome — unknown beats guessed)."""
    try:
        stories: list[dict] = []
        for project in discover_projects(root):
            for phase in discover_phases(project):
                for row in parse_story_rows(
                    phase.path / "current-phase-status.md"
                ):
                    if normalize_status(row.status) in _IN_PROGRESS:
                        stories.append(
                            {
                                "story_id": row.story_id,
                                "title": row.title,
                                "status": row.status,
                                "project": project.slug,
                            }
                        )
        return stories
    except Exception:
        return None


def _correlate_record(key: str, record: dict, now: datetime) -> dict:
    repo_root = str(record.get("repo_root") or "").strip()
    root = Path(repo_root) if repo_root else None

    if root is None or not root.is_dir() or not _is_rails_repo(root):
        outcome, stories = "off_rails", []
    else:
        found = _in_progress_stories(root)
        if found is None:
            outcome, stories = "unreadable", []
        elif len(found) == 1:
            outcome, stories = "on_story", found
        elif found:
            outcome, stories = "ambiguous", found
        else:
            outcome, stories = "idle_on_rails", []

    updated = _parse_ts(record.get("updated_at"))
    if updated is not None and updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    stale = (
        updated is None
        or (now - updated).total_seconds() > STALE_TTL_SECONDS
    )

    tmux_session = record.get("tmux_session")
    tmux = (
        {
            "session": tmux_session,
            "window": record.get("tmux_window"),
            "pane": record.get("tmux_pane"),
        }
        if tmux_session
        else None
    )
    return {
        "key": key,
        "agent": str(record.get("agent") or ""),
        "model": record.get("model"),
        "repo_root": repo_root or None,
        "project_name": record.get("project_name"),
        "correlation": outcome,
        "stories": stories,
        "awaiting_response": bool(record.get("awaiting_response")),
        "last_assistant_text": record.get("last_assistant_text"),
        "tmux": tmux,
        "stale": stale,
        "updated_at": record.get("updated_at"),
    }


def correlate_sessions(
    registry_path: Path | None = None, now: datetime | None = None
) -> dict:
    path = registry_path or DEFAULT_REGISTRY_PATH
    now = now or datetime.now(timezone.utc)
    base = {"sessions_schema": SESSIONS_SCHEMA, "sessions": []}
    if not path.exists():
        return {**base, "registry": "absent"}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {**base, "registry": "unreadable"}
    if not isinstance(raw, dict) or raw.get("version") != REGISTRY_VERSION:
        return {
            **base,
            "registry": (
                f"version {raw.get('version')!r} is not the registry "
                f"version this reader was proven against ({REGISTRY_VERSION})"
                if isinstance(raw, dict)
                else "unreadable"
            ),
        }
    records = raw.get("sessions")
    if not isinstance(records, dict):
        return {**base, "registry": "unreadable"}
    sessions = [
        _correlate_record(key, record, now)
        for key, record in sorted(records.items())
        if isinstance(record, dict)
    ]
    return {"sessions_schema": SESSIONS_SCHEMA, "registry": "ok", "sessions": sessions}


def render_sessions(registry_path: Path | None = None) -> str:
    return json.dumps(
        correlate_sessions(registry_path), indent=2, sort_keys=True
    )
