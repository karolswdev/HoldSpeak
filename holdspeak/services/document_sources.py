"""Stored document sources for channel preview and send (PHILO-11-01).

Each source renders one durable record by its explicit id.  The registry is
deliberately a plain table: adding a source is one renderer and one row.  A
renderer never invokes inference and never accepts caller-supplied document
text.  The source interface is pure ``render(db, source_id)``; transport
authentication remains at the channel service seam.
"""
from __future__ import annotations

import re
from datetime import datetime
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


_SYNTHESIS_FOOTER = re.compile(
    r"(?:^|\n)(?P<footer>- Source windows: (?P<windows>[^\n]*)\n"
    r"- Source plugin runs: (?P<runs>[^\n]*))\s*\Z"
)


def _without_synthesis_footer(body: str, sources: list[dict[str, Any]]) -> str:
    """Remove only the footer emitted by meeting synthesis for this lineage.

    The body is authored/stored text.  A footer-shaped paragraph remains when
    it does not exactly match the artifact's own ``intent_window`` and
    ``plugin_run`` source rows, including when it appears inside a code block.
    """
    windows = {
        str(source.get("source_ref") or "").strip()
        for source in sources
        if str(source.get("source_type") or "").strip().lower() == "intent_window"
        and str(source.get("source_ref") or "").strip()
    }
    plugin_runs = {
        str(source.get("source_ref") or "").strip()
        for source in sources
        if str(source.get("source_type") or "").strip().lower() == "plugin_run"
        and str(source.get("source_ref") or "").strip()
    }
    if not windows and not plugin_runs:
        return body

    candidate = body.rstrip("\n")
    match = _SYNTHESIS_FOOTER.search(candidate)
    if match is None:
        return body
    expected_windows = ", ".join(sorted(windows)) if windows else "none"
    expected_plugin_runs = ", ".join(sorted(plugin_runs)) if plugin_runs else "none"
    if match.group("windows") != expected_windows:
        return body
    if match.group("runs") != expected_plugin_runs:
        return body

    prefix = candidate[: match.start()]
    # The match consumes the newline that separates the stored body from the
    # synthesis footer. Remove that separator only; keep authored spacing in
    # the body before it.
    if prefix.endswith("\n"):
        prefix = prefix[:-1]
    return prefix


_MISSING_ARTIFACT = object()


def _raw_artifact_body(db: Any, source_id: str) -> Any:
    """Read the stored body before ``get_artifact`` coerces it to ``str``."""
    with db._connection() as conn:
        row = conn.execute(
            "SELECT body_markdown FROM artifacts WHERE id = ?", (source_id,)
        ).fetchone()
    return _MISSING_ARTIFACT if row is None else row["body_markdown"]


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


_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _time_text(value: Any) -> str:
    """A stored time as a reader writes it: `30 Sep 2026, 07:59`.

    PHILO-11-05a: one format for the preview and the bytes that are sent (both
    come from this document). The stored clock is kept as it is (no zone
    change); a value that does not parse is shown as stored.
    """
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    return f"{moment.day} {_MONTHS[moment.month - 1]} {moment.year}, {moment:%H:%M}"


def _day_text(value: Any) -> str:
    """A stored date as a reader writes it: `29 Sep 2026` (empty when unknown)."""
    if isinstance(value, datetime):
        moment = value
    else:
        text = str(value or "").strip()
        if not text:
            return ""
        try:
            moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return ""
    return f"{moment.day} {_MONTHS[moment.month - 1]} {moment.year}"


_MEETING_IN_REF = re.compile(r"^meeting:([^#]+)")


def _meeting_line(db: Any, meeting_id: str) -> str:
    """A meeting as a person recognizes it: its title and date, never its id."""
    meeting = db.meetings.get_meeting(meeting_id) if meeting_id else None
    if meeting is None:
        return "A meeting (removed)"
    title = str(meeting.title or "").strip() or "A meeting"
    day = _day_text(meeting.started_at)
    return f"{title}, {day}" if day else title


def _source_lines(db: Any, sources: list[dict[str, Any]]) -> list[str]:
    """PHILO-11-05a (Muad'Dib's ruling): the text is SENT to other people, so a
    record's sources are named by what a person recognizes, never by an
    internal id or ref. A meeting (also one named only by a transcript
    segment) -> its title and date; a proposal -> "From a meeting proposal";
    the desk or a manual entry -> "Written on the desk". Artifact rows and the
    supersession links carry nothing a reader can use and are left out."""
    lines: list[str] = []
    for source in sources:
        kind = str(source.get("source_type") or "").strip()
        ref = str(source.get("source_ref") or "").strip()
        if kind == "meeting":
            line = _meeting_line(db, str(source.get("meeting_id") or ref))
        elif kind in ("segment", "transcript"):
            found = _MEETING_IN_REF.match(ref)
            meeting_id = str(source.get("meeting_id") or (found.group(1) if found else ""))
            line = _meeting_line(db, meeting_id) if meeting_id else ""
        elif kind == "proposal":
            line = "From a meeting proposal"
        elif kind in ("desk", "manual"):
            line = "Written on the desk"
        else:
            line = ""
        if line and f"- {line}" not in lines:
            lines.append(f"- {line}")
    return lines


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


def _parked_brief_person_overlay(db: Any, brief: Any) -> dict[str, Any]:
    """PARKED (2026-10-03, inventory gap 5): the sent Brief carries no People data.

    People records are in custody. A sent document leaves the desk and stays
    in ``channel_sends.payload`` as plain text, and Send has no People gate.
    The Brief face on the desk still shows the overlay
    (``web/routes/monday_brief.py``). No caller uses this function.

    Compose the same read-time People overlay as the brief face.

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


def _brief_markdown(brief: Any) -> str:
    """The Brief as a sent document: the stored items only, no People data."""
    from .monday_brief_service import brief_period_label, brief_title

    period = brief_period_label(brief.period_start, brief.period_end)
    lines = [
        f"# {brief_title(brief.period_end)}",
        # PHILO-15-09 (B04, ruling 3): the one range the window head says.
        *([f"Period: {period}"] if period else []),
        f"Generated: {_time_text(brief.generated_at)}",
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

    return "\n".join(lines).strip() + "\n"


def _parked_brief_people_lines(overlay: dict[str, Any]) -> list[str]:
    """PARKED with ``_parked_brief_person_overlay``: the People lines of a sent Brief."""
    lines: list[str] = []
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
    return lines


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

        brief = MondayBriefService(db).get_by_id(source_id)
        if brief is None:
            raise _document_not_found("brief", source_id)
        from .monday_brief_service import brief_title

        period = _date_text(brief.period_end) or _date_text(brief.generated_at)
        # PHILO-15-09 (B04, ruling 2): the brief's own weekday and date.
        title = brief_title(brief.period_end or brief.generated_at)
        return _make_document(
            ref=f"{self.kind}:{brief.id}",
            title=title,
            body_md=_brief_markdown(brief),
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
            label="DECISION",  # never the id: the label names the saved file (PHILO-11-05a)
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
            # The meeting by its title and date, never its id (it is sent to people).
            body.extend(["", f"Meeting: {_meeting_line(db, meeting_id)}"])
        title_for_slug = str(decision.get("text") or title)
        return _make_document(
            ref=f"{self.kind}:{source_id}",
            title=str(decision.get("text") or title),
            body_md="\n".join(body).strip() + "\n",
            slug=_slug(title_for_slug, "decision"),
            label="DECISION",  # never the id: the label names the saved file (PHILO-11-05a)
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
        named = _source_lines(db, record.get("sources") or [])
        if named:
            lines.extend(["", "## Sources", *named])
        successor = str(record.get("successor_id") or "").strip()
        if successor:
            # The later decision by its words, never its record id.
            later = DecisionRecordService(db).get(_source_read_context(), successor)
            words = str((later or {}).get("decision_text") or "").strip()
            lines.extend(["", "## Superseded by", words or "A later decision (removed)"])
        return _make_document(
            ref=f"{self.kind}:{source_id}",
            title=title,
            body_md="\n".join(lines).strip() + "\n",
            slug=_slug(title, "decision"),
            label="DECISION",  # never the id: the label names the saved file (PHILO-11-05a)
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
        lines = [f"# {title}", f"Date: {_date_text(meeting.started_at)}"]
        # PHILO-15-07 (Astra r1 on #982): a transcript with honest gaps says so
        # in the sent document, from the marks themselves, never from the model.
        from ..transcript_guard import count_unclear

        unclear = count_unclear(getattr(segment, "text", "") for segment in (meeting.segments or []))
        if unclear:
            lines.append(f"Transcript: {unclear} unclear span{'' if unclear == 1 else 's'}")
        lines.extend(["", "## Summary", summary])
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


class _ArtifactSource:
    kind = "artifact"

    def render(self, db: Any, source_id: str) -> Document:
        # Read the native SQLite value first.  ``get_artifact`` intentionally
        # returns a DTO and coerces its body to text for older callers.
        raw_body = _raw_artifact_body(db, source_id)
        if raw_body is _MISSING_ARTIFACT:
            raise _document_not_found("artifact", source_id)
        if raw_body is None:
            # The row exists, so a NULL body is a missing body rather than a
            # missing document.  A non-text value is rejected before the DTO
            # value can hide its native type.
            raise ChannelRefused(
                "artifact_body_missing",
                f"Artifact {source_id} has no stored body",
                status=400,
            )
        if not isinstance(raw_body, str):
            raise ChannelRefused(
                "artifact_not_text",
                f"Artifact {source_id} body is not text",
                status=400,
            )
        if not raw_body.strip():
            raise ChannelRefused(
                "artifact_body_missing",
                f"Artifact {source_id} has no stored body",
                status=400,
            )

        artifact = db.plugins.get_artifact(source_id)
        if artifact is None:
            raise _document_not_found("artifact", source_id)

        title = str(artifact.title or "Artifact").strip() or "Artifact"
        artifact_type = str(artifact.artifact_type or "plugin_output").strip()
        type_label = artifact_type.replace("_", " ").upper() or "PLUGIN OUTPUT"
        return _make_document(
            ref=f"{self.kind}:{source_id}",
            title=title,
            body_md=_without_synthesis_footer(raw_body, artifact.sources),
            slug=_slug(title, "artifact"),
            label=f"ARTIFACT · {type_label}",
        )


class _NoteSource:
    """PHILO-17 U08: a note (also a Thought's working note) as he wrote it."""

    kind = "note"

    def render(self, db: Any, source_id: str) -> Document:
        from .primitive_service import PrimitiveService

        note = PrimitiveService(db).get_note(_source_read_context(), source_id)
        title = str(note.get("title") or "").strip()
        body = str(note.get("body_markdown") or "").strip()
        if not title and not body:
            raise ChannelRefused("note_empty", f"Note {source_id} has no words", status=400)
        title = title or "Note"
        # A thought takes its first words as its title: say them once.
        first, _, rest = body.partition("\n")
        if first.strip().lstrip("#").strip() == title:
            body = rest.strip()
        return _make_document(
            ref=f"{self.kind}:{source_id}",
            title=title,
            body_md=f"# {title}\n\n{body}\n" if body else f"# {title}\n",
            slug=_slug(title, "note"),
            label="NOTE",  # never the id: the label names the saved file
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
    "artifact": _ArtifactSource(),
    "note": _NoteSource(),
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
