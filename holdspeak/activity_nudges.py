"""Activity pre-briefing nudges (Phase 53, HS-53-01).

A pure reader over the existing activity ledger + the meeting window. Computes a
small set (1 to 3) of source-cited, dismissible nudges that surface relevant
recent activity before the user dictates or meets:

- A windowed summary nudge ("you touched N things since your last meeting"),
  scoped by the previous ``MeetingSummary.ended_at`` or a recent-window fallback.
- Per-record suggestion nudges ("you were looking at github_issue owner/repo#123")
  for the most relevant recent records.

Every nudge carries a citation a user can verify on ``/activity`` (the
originating ``ActivityRecord.id``, ``source_browser`` / ``source_profile``,
entity, and ``last_seen_at``). Relevance is a deterministic heuristic — recency,
entity type, project match — never an LLM. A weak-signal record does not become
a nudge; quiet beats noisy. Dismissals persist via
``ActivityRepository.dismiss_nudge``, keyed deterministically so the same nudge
stays dismissed across recomputation.

The engine returns an empty list when the activity privacy toggle is off.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

from .db import ActivityRecord, Database, get_database


# Heuristic constants — kept small and explicit so the ordering is auditable.
_FALLBACK_WINDOW_HOURS = 24
_MIN_RECORDS_FOR_WINDOW_NUDGE = 2
_MIN_RECORD_SCORE = 1.0
_ENTITY_TYPE_BONUS = {
    "github_issue": 2.5,
    "github_pull_request": 2.5,
    "jira_issue": 2.5,
    "calendar_event": 2.0,
}
_DEFAULT_LIMIT = 3
_PER_RECORD_FETCH_LIMIT = 50


@dataclass(frozen=True)
class NudgeCitation:
    """Source citation for a nudge — names where the record came from."""

    record_id: int
    source_browser: str
    source_profile: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    domain: str
    title: Optional[str]
    url: str
    last_seen_at: Optional[str]
    visit_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "source_browser": self.source_browser,
            "source_profile": self.source_profile,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "domain": self.domain,
            "title": self.title,
            "url": self.url,
            "last_seen_at": self.last_seen_at,
            "visit_count": self.visit_count,
        }


@dataclass(frozen=True)
class Nudge:
    """A single source-cited pre-briefing nudge."""

    key: str
    kind: str  # "window" | "record"
    title: str
    body: str
    score: float
    citations: list[NudgeCitation]
    window_since: Optional[str] = None
    window_record_count: int = 0
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "kind": self.kind,
            "title": self.title,
            "body": self.body,
            "score": round(float(self.score), 4),
            "citations": [c.to_dict() for c in self.citations],
            "window_since": self.window_since,
            "window_record_count": self.window_record_count,
            "extras": dict(self.extras),
        }


def compute_nudges(
    db: Optional[Database] = None,
    *,
    project_id: Optional[str] = None,
    now: Optional[datetime] = None,
    limit: int = _DEFAULT_LIMIT,
) -> list[Nudge]:
    """Compute the current pre-briefing nudges (read-only).

    Returns an empty list when activity tracking is off, when there are no
    recent records in the window, or when no record clears the relevance floor.
    Dismissed nudges (by deterministic key) are filtered out.
    """
    database = db or get_database()

    privacy = database.activity.get_activity_privacy_settings()
    if not bool(privacy.get("enabled", False)):
        return []

    cap = max(1, min(int(limit or _DEFAULT_LIMIT), 10))
    current_time = now or datetime.now()
    since_ts, since_source = _resolve_since(database, current_time)

    records = database.activity.list_activity_records(
        project_id=project_id,
        since=since_ts,
        limit=_PER_RECORD_FETCH_LIMIT,
    )
    if not records:
        return []

    dismissed = database.activity.list_dismissed_nudge_keys()
    since_iso = since_ts.isoformat(timespec="seconds")

    nudges: list[Nudge] = []

    window_nudge = _build_window_nudge(
        records=records,
        since_iso=since_iso,
        since_source=since_source,
    )
    if window_nudge is not None and window_nudge.key not in dismissed:
        nudges.append(window_nudge)

    scored = [
        (record, _score_record(record, project_id=project_id, now=current_time))
        for record in records
    ]
    scored = [pair for pair in scored if pair[1] >= _MIN_RECORD_SCORE]
    scored.sort(
        key=lambda pair: (
            -pair[1],
            -(_seen_dt(pair[0]) or datetime.min).timestamp(),
            -pair[0].id,
        )
    )

    seen_keys: set[str] = {n.key for n in nudges}
    for record, score in scored:
        if len(nudges) >= cap:
            break
        nudge = _build_record_nudge(record, score=score)
        if nudge.key in dismissed or nudge.key in seen_keys:
            continue
        nudges.append(nudge)
        seen_keys.add(nudge.key)

    return nudges[:cap]


def _resolve_since(db: Database, now: datetime) -> tuple[datetime, str]:
    """Lower bound for "what you touched recently".

    Prefer the previous meeting's ``ended_at``; fall back to a recent window when
    there is no prior ended meeting. Returns (timestamp, source) so the engine
    can name what it cited.
    """
    fallback = now - timedelta(hours=_FALLBACK_WINDOW_HOURS)
    try:
        recent_meetings = db.meetings.list_meetings(limit=5)
    except Exception:
        recent_meetings = []
    for meeting in recent_meetings:
        ended = meeting.ended_at
        if ended is not None and ended <= now:
            return ended, "previous_meeting"
    return fallback, "recent_window"


def _build_window_nudge(
    *,
    records: list[ActivityRecord],
    since_iso: str,
    since_source: str,
) -> Optional[Nudge]:
    if len(records) < _MIN_RECORDS_FOR_WINDOW_NUDGE:
        return None
    top = records[:3]
    citations = [_citation_for(r) for r in top]
    entity_counts = Counter(
        (r.entity_type or "page") for r in records if r is not None
    )
    headline_source = "your last meeting" if since_source == "previous_meeting" else "recently"
    title = f"You touched {len(records)} things since {headline_source}"
    body_parts = [
        f"{count} {label.replace('_', ' ')}" for label, count in entity_counts.most_common(3)
    ]
    body = ", ".join(body_parts) if body_parts else "Recent local activity."
    return Nudge(
        key=f"window:{since_iso}",
        kind="window",
        title=title,
        body=body,
        score=float(len(records)),
        citations=citations,
        window_since=since_iso,
        window_record_count=len(records),
        extras={"since_source": since_source},
    )


def _build_record_nudge(record: ActivityRecord, *, score: float) -> Nudge:
    entity_label = _entity_label(record)
    if entity_label:
        title = f"You were looking at {entity_label}"
    else:
        title = record.title or record.url
    body = _record_body(record)
    return Nudge(
        key=f"record:{record.id}",
        kind="record",
        title=title,
        body=body,
        score=float(score),
        citations=[_citation_for(record)],
    )


def _citation_for(record: ActivityRecord) -> NudgeCitation:
    return NudgeCitation(
        record_id=record.id,
        source_browser=record.source_browser,
        source_profile=record.source_profile,
        entity_type=record.entity_type,
        entity_id=record.entity_id,
        domain=record.domain,
        title=record.title,
        url=record.url,
        last_seen_at=record.last_seen_at.isoformat() if record.last_seen_at else None,
        visit_count=int(record.visit_count or 0),
    )


def _entity_label(record: ActivityRecord) -> Optional[str]:
    if record.entity_type and record.entity_id:
        return f"{record.entity_type} {record.entity_id}"
    return None


def _record_body(record: ActivityRecord) -> str:
    visit = max(1, int(record.visit_count or 1))
    visit_phrase = "1 visit" if visit == 1 else f"{visit} visits"
    last_seen = record.last_seen_at.date().isoformat() if record.last_seen_at else "recently"
    domain = record.domain or "local activity"
    return f"{visit_phrase} on {domain}, last on {last_seen}"


def _score_record(
    record: ActivityRecord,
    *,
    project_id: Optional[str],
    now: datetime,
) -> float:
    """Deterministic relevance score: recency + entity type + project match."""
    score = 0.0

    seen = _seen_dt(record)
    if seen is not None:
        hours = max(0.0, (now - seen).total_seconds() / 3600.0)
        if hours <= 1:
            score += 4.0
        elif hours <= 6:
            score += 3.0
        elif hours <= 24:
            score += 2.0
        elif hours <= 72:
            score += 1.0

    entity_type = (record.entity_type or "").strip().lower() or None
    if entity_type:
        score += _ENTITY_TYPE_BONUS.get(entity_type, 0.5)

    if project_id and record.project_id and record.project_id == project_id:
        score += 1.5
    elif record.project_id:
        score += 0.25

    visit_count = int(record.visit_count or 0)
    if visit_count >= 5:
        score += 0.5

    return score


def _seen_dt(record: ActivityRecord) -> Optional[datetime]:
    return record.last_seen_at
