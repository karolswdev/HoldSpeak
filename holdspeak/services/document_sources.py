"""Stored document sources for channel preview and send (PHILO-11-01).

Each source renders one durable record by its explicit id.  The registry is
deliberately a plain table: adding a source is one renderer and one row.  A
renderer never invokes inference and never accepts caller-supplied document
text.  The source interface is pure ``render(db, source_id)``; transport
authentication remains at the channel service seam.
"""
from __future__ import annotations

import re
from typing import Any

from .channel_contract import ChannelRefused, Document, DocumentSource, render_update
from .errors import NotFound


def _slug(value: Any, fallback: str = "document") -> str:
    words = re.findall(r"[a-z0-9]+", str(value or "").lower())
    return "-".join(words)[:60].strip("-") or fallback


def _make_document(
    *,
    ref: str,
    title: str,
    body_md: str,
    slug: str,
    label: str,
) -> Document:
    """Construct a source-owned document with its frozen file label."""
    return Document(ref=ref, title=title, body_md=body_md, slug=slug, label=label)


def _document_not_found(kind: str, source_id: str) -> ChannelRefused:
    return ChannelRefused(
        "document_not_found",
        f"No {kind} document exists for {source_id}",
        status=404,
    )


def _no_summary(meeting_id: str, kind: str = "meeting") -> ChannelRefused:
    return ChannelRefused(
        "no_summary",
        f"The {kind} for meeting {meeting_id} has no stored summary",
        status=400,
    )


def _date_text(value: Any) -> str:
    text = str(value or "")
    return text[:10]


def _format_period(start: Any, end: Any) -> str:
    left = _date_text(start)
    right = _date_text(end)
    if left and right and left != right:
        return f"{left} – {right}"
    return left or right


def _source_read_context() -> Any:
    """Internal read context for source composition, independent of transport."""
    from holdspeak.principals import Principal, PrincipalKind

    return Principal(PrincipalKind.OWNER, "channel-document-source")


def _brief_person_overlay(db: Any, brief: Any) -> dict[str, Any]:
    """Compose the same read-time People overlay as the brief face.

    The sidecar may be unavailable on a machine without People access.  That
    state is retained as an explicit empty result; it never causes a renderer
    to invent person content or run a model.
    """
    try:
        from .follow_through_service import FollowThroughService
        from .person_overlay import compose_person_overlay
        from .people_service import PeopleService, UnavailablePeopleStore

        try:
            from holdspeak.people import production_people_store

            people_service = PeopleService(production_people_store())
        except Exception:
            people_service = PeopleService(UnavailablePeopleStore())

        # The source protocol has no second document identity or People send
        # gate. The owner-controlled production sidecar is read-only here and
        # uses the same internal read context for owner and agent preparation.
        follow_through = FollowThroughService(db, people_projection=people_service)
        return compose_person_overlay(
            (str(brief.period_start), str(brief.period_end)),
            people_service,
            follow_through,
            db,
            _source_read_context(),
        )
    except Exception:
        # A closed or partially composed People sidecar is honest unavailable
        # state.  It is not a source-not-found condition for the brief itself.
        return {"state": "unavailable", "sections": []}


def _brief_markdown(brief: Any, overlay: dict[str, Any]) -> str:
    lines = [
        "# Monday Brief",
        f"Period: {_format_period(brief.period_start, brief.period_end)}",
        f"Generated: {brief.generated_at}",
        "",
        str(brief.headline or "").strip(),
    ]
    section_titles = {
        "this_week": "This week",
        "changed": "Changed",
        "broke": "Needs attention",
        "waiting": "Waiting",
        "decisions": "Decisions",
    }
    for section, items in brief.sections.items():
        if not items:
            continue
        lines.extend(["", f"## {section_titles.get(section, section.replace('_', ' ').title())}"])
        for item in items:
            text = str(item.text or "").strip()
            # Every stored item stays in the brief, including acknowledged and
            # deferred rows.  The shelf is intentionally never read here.
            lines.append(f"- {text}")
            detail = str(item.detail or "").strip()
            if detail:
                lines.append(f"  {detail}")

    if overlay.get("state") == "unavailable":
        lines.extend(["", "PEOPLE · UNAVAILABLE"])
    elif overlay.get("state") == "ready":
        sections = overlay.get("sections") or []
        if sections:
            lines.extend(["", "## People"])
            for section in sections:
                name = str(section.get("display_name") or "Person").strip() or "Person"
                lines.extend(["", f"### {name}"])
                fields = (
                    ("They owe", section.get("they_owe_count")),
                    ("You owe", section.get("you_owe_count")),
                    ("Agenda", section.get("agenda_backlog")),
                )
                for label, value in fields:
                    if value:
                        lines.append(f"- {label}: {value}")
                upcoming = section.get("next_one_on_one")
                if upcoming:
                    title = str(upcoming.get("title") or "One-on-one")
                    starts = str(upcoming.get("starts_at") or "")
                    lines.append(f"- Next: {title}" + (f" ({starts})" if starts else ""))
    return "\n".join(lines).strip() + "\n"


class _ProjectUpdateSource:
    kind = "project_update"

    def render(self, db: Any, source_id: str) -> Document:
        try:
            return render_update(db, source_id)
        except NotFound as exc:
            raise _document_not_found("project update", source_id) from exc


class _MondayBriefSource:
    kind = "monday_brief"

    def render(self, db: Any, source_id: str) -> Document:
        from .monday_brief_service import MondayBriefService

        with db._connection() as conn:
            row = conn.execute("SELECT * FROM monday_briefs WHERE id = ?", (source_id,)).fetchone()
            if row is None:
                raise _document_not_found("Monday brief", source_id)
            brief = MondayBriefService._load_brief(conn, row)
        overlay = _brief_person_overlay(db, brief)
        period = _date_text(brief.period_end) or _date_text(brief.generated_at)
        title = f"Monday Brief — {period}" if period else "Monday Brief"
        return _make_document(
            ref=f"{self.kind}:{brief.id}",
            title=title,
            body_md=_brief_markdown(brief, overlay),
            slug=f"brief-{_slug(period, 'brief')}",
            label=f"BRIEF {period}" if period else "BRIEF",
        )


class _DeskDecisionSource:
    kind = "desk_decision"

    def render(self, db: Any, source_id: str) -> Document:
        from .primitive_service import PrimitiveService

        decision = PrimitiveService(db).get_decision(None, source_id)
        if decision is None:
            raise _document_not_found("desk decision", source_id)
        title = str(decision.get("title") or "Desk decision")
        lines = [f"# {title}", f"Status: {decision.get('status') or 'proposed'}"]
        if decision.get("deciders"):
            lines.extend(["", "## Deciders", ", ".join(map(str, decision["deciders"]))])
        for heading, field in (
            ("Context", "context_markdown"),
            ("Decision", "decision_markdown"),
            ("Consequences", "consequences_markdown"),
        ):
            value = str(decision.get(field) or "").strip()
            if value:
                lines.extend(["", f"## {heading}", value])
        alternatives = decision.get("alternatives") or []
        if alternatives:
            lines.extend(["", "## Alternatives"])
            for alternative in alternatives:
                if isinstance(alternative, dict):
                    name = str(alternative.get("name") or "").strip()
                    reason = str(alternative.get("reason") or "").strip()
                    lines.append(f"- {name}" + (f": {reason}" if reason else ""))
                else:
                    lines.append(f"- {alternative}")
        return _make_document(
            ref=f"{self.kind}:{source_id}",
            title=title,
            body_md="\n".join(lines).strip() + "\n",
            slug=_slug(title, "decision"),
            label=f"DECISION {source_id}",
        )


class _MeetingDecisionSource:
    kind = "meeting_decision"

    def render(self, db: Any, source_id: str) -> Document:
        from .decision_lifecycle_service import DecisionLifecycleService

        try:
            result = DecisionLifecycleService(db).get_decision(
                _source_read_context(), source_id
            )
        except NotFound as exc:
            raise _document_not_found("meeting decision", source_id) from exc
        decision = result.get("decision") if isinstance(result, dict) else None
        if not isinstance(decision, dict) or not decision.get("source_meeting_id"):
            raise _document_not_found("meeting decision", source_id)
        meeting_id = str(decision.get("source_meeting_id") or "")
        meeting = db.meetings.get_meeting(meeting_id) if meeting_id else None
        title = str(meeting.title if meeting and meeting.title else "Meeting decision")
        meeting_date = _date_text(meeting.started_at if meeting else "")
        body = [
            f"# {title}",
            f"Decision date: {_date_text(decision.get('decided_at'))}",
            f"Lifecycle: {decision.get('lifecycle') or 'recorded'}",
            "",
            "## Decision",
            str(decision.get("text") or "").strip(),
        ]
        if meeting_date:
            body.insert(1, f"Meeting date: {meeting_date}")
        if decision.get("rationale"):
            body.extend(["", "## Rationale", str(decision["rationale"]).strip()])
        if meeting_id:
            body.extend(["", f"Meeting: {meeting_id}"])
        title_for_slug = str(decision.get("text") or title)
        return _make_document(
            ref=f"{self.kind}:{source_id}",
            title=str(decision.get("text") or title),
            body_md="\n".join(body).strip() + "\n",
            slug=_slug(title_for_slug, "decision"),
            label=f"DECISION {source_id}",
        )


class _DecisionRecordSource:
    kind = "decision_record"

    def render(self, db: Any, source_id: str) -> Document:
        from .decision_record_service import DecisionRecordService

        record = DecisionRecordService(db).get(_source_read_context(), source_id)
        if record is None:
            raise _document_not_found("decision record", source_id)
        title = str(record.get("decision_text") or "Decision record")
        lines = [f"# {title}", f"Lifecycle: {record.get('lifecycle') or 'active'}"]
        for heading, field in (("Rationale", "rationale"), ("Owner", "owner"), ("Review date", "review_date")):
            value = str(record.get(field) or "").strip()
            if value:
                lines.extend(["", f"## {heading}", value])
        sources = record.get("sources") or []
        if sources:
            lines.extend(["", "## Sources"])
            for source in sources:
                source_type = str(source.get("source_type") or "source").strip()
                source_ref = str(source.get("source_ref") or "").strip()
                lines.append(f"- {source_type}: {source_ref}" if source_ref else f"- {source_type}")
        successor = str(record.get("successor_id") or "").strip()
        if successor:
            lines.extend(["", "## Successor", successor])
        return _make_document(
            ref=f"{self.kind}:{source_id}",
            title=title,
            body_md="\n".join(lines).strip() + "\n",
            slug=_slug(title, "decision"),
            label=f"DECISION {source_id}",
        )


class _MeetingSummarySource:
    kind = "meeting_summary"

    def render(self, db: Any, source_id: str) -> Document:
        meeting = db.meetings.get_meeting(source_id)
        if meeting is None:
            raise _document_not_found("meeting", source_id)
        intel = meeting.intel
        summary = str(intel.summary if intel else "").strip()
        if not summary:
            raise _no_summary(source_id)
        title = str(meeting.title or "Meeting")
        lines = [f"# {title}", f"Date: {_date_text(meeting.started_at)}", "", "## Summary", summary]
        topics = [str(topic).strip() for topic in ((intel.topics if intel else []) or []) if str(topic).strip()]
        if topics:
            lines.extend(["", "## Topics", *[f"- {topic}" for topic in topics]])
        return _make_document(
            ref=f"{self.kind}:{source_id}",
            title=title,
            body_md="\n".join(lines).strip() + "\n",
            slug=_slug(title, "meeting"),
            label=f"SUMMARY {_date_text(meeting.started_at)}".strip(),
        )


class _MeetingAftercareSource:
    def __init__(self, kind: str) -> None:
        self.kind = kind

    def render(self, db: Any, source_id: str) -> Document:
        from ..meeting_aftercare import compute_meeting_aftercare
        from ..slack_export import document_markdown_for

        digest = compute_meeting_aftercare(db, source_id)
        if digest is None:
            raise _document_not_found("meeting", source_id)
        if digest.get("is_empty"):
            raise _no_summary(source_id, "aftercare")
        what = "digest" if self.kind == "meeting_digest" else "followup"
        title = str(digest.get("meeting_title") or "Meeting")
        date = _date_text(digest.get("meeting_date"))
        return _make_document(
            ref=f"{self.kind}:{source_id}",
            title=title,
            body_md=document_markdown_for(digest, what),
            slug=_slug(title, "meeting"),
            label=f"{what.upper()} {date}".strip(),
        )


DOCUMENT_SOURCES: dict[str, DocumentSource] = {
    "project_update": _ProjectUpdateSource(),
    "monday_brief": _MondayBriefSource(),
    "desk_decision": _DeskDecisionSource(),
    "meeting_decision": _MeetingDecisionSource(),
    "decision_record": _DecisionRecordSource(),
    "meeting_summary": _MeetingSummarySource(),
    "meeting_digest": _MeetingAftercareSource("meeting_digest"),
    "meeting_followup": _MeetingAftercareSource("meeting_followup"),
}


def render_document(db: Any, document_ref: str) -> Document:
    """Resolve and render ``<kind>:<source_id>`` through the registry."""
    kind, separator, source_id = str(document_ref or "").partition(":")
    if not separator or not kind or not source_id:
        raise ChannelRefused("document_kind_unknown", f"Unknown document kind in {document_ref!r}", status=400)
    source = DOCUMENT_SOURCES.get(kind)
    if source is None:
        raise ChannelRefused("document_kind_unknown", f"Unknown document kind: {kind}", status=400)
    try:
        return source.render(db, source_id)
    except NotFound as exc:
        raise _document_not_found(kind, source_id) from exc


__all__ = ["DOCUMENT_SOURCES", "DocumentSource", "render_document"]
