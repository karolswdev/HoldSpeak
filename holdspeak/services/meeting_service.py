"""Transport-neutral meeting lifecycle and archive operations (HS-122-04).

The live capture engine remains owned by the runtime.  Its callbacks are bound
at composition time, so this module can serve HTTP, MCP, and tests without
importing a web-layer type.
"""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

from datetime import datetime
from pathlib import Path
import threading
import uuid
from typing import Any, Callable

from ..config import Config
from ..db.core import Database
from ..meeting_exports import render_meeting_export
from ..meeting_import import (
    DEFAULT_SPEAKER_LABEL,
    DEFAULT_TRANSCRIPT_SPEAKER_LABEL,
    MeetingImportError,
    import_meeting as run_meeting_import,
    import_transcript,
    is_transcript_filename,
    validate_format,
)
from ..meeting_session import MeetingState
from ..principals import Principal
from holdspeak.services.errors import ConflictError, NotFound, ServiceError, ValidationError


class ActionItemTriageUnavailable(ServiceError):
    """No live session and no saved row can serve this item's triage (HS-132-02).

    Raised only when this server has no live-session handler bound at all *and*
    the persisted store does not know the item — i.e. there is no path that
    could ever serve the verb here. When a live handler is bound and simply does
    not own the item, the persisted miss stays an honest ``NotFound``.
    """

    def __init__(self, item_id: str) -> None:
        super().__init__(
            "triage_unavailable",
            "Live action-item triage is not wired on this server, "
            "and no saved action item matches.",
            context={"id": item_id},
        )


def _accepts_principal(callback: Any) -> bool:
    """Whether a bound capture-start callback takes the authenticated principal.

    The runtime's ``_start_meeting`` does; partial test/adapter bindings need not,
    and must not be handed an argument they cannot name.
    """
    import inspect

    try:
        parameters = inspect.signature(callback).parameters
    except (TypeError, ValueError):
        return False
    if "principal" in parameters:
        return True
    return any(p.kind is inspect.Parameter.VAR_KEYWORD for p in parameters.values())


class _MeetingPersonRedactor:
    """Keep the read-time People projection out of durable observation.

    HS-149 close-counsel finding 1: ``_enrich_calendar_origin`` injects
    ``person_label`` (a display name resolved from the ENCRYPTED People
    store) into meeting read payloads. The observer serializes results
    into the plaintext ``pipeline_events`` table, which would persist
    that name outside the encrypted boundary — the same crossing
    ``_FollowThroughObserver`` exists to prevent for the board. Meeting
    reads that can carry the projection have their result replaced, not
    trimmed (timing/outcome retained).
    """

    _REDACTED_METHODS = frozenset({"list_meetings", "get_meeting"})

    def __init__(self, delegate: "PipelineObserver") -> None:
        self._delegate = delegate

    def on_event(self, event):  # PipelineEvent
        from dataclasses import replace as _replace
        if event.service == "MeetingService" and event.method in self._REDACTED_METHODS:
            if event.result_summary and "person_label" in str(event.result_summary):
                event = _replace(event, result_summary='{"meetings":"person_projection_redacted"}')
        self._delegate.on_event(event)


@observe_service
class MeetingService:
    """One service boundary for meeting capture and persisted meeting data."""

    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._on_start: Callable[..., Any] | None = None
        self._on_stop: Callable[[], Any] | None = None
        self._on_bookmark: Callable[[str], Any] | None = None
        self._on_update: Callable[..., Any] | None = None
        # HS-132-02: the live-session action-item triage seam. Bound at an
        # application edge exactly like the lifecycle callbacks above; unbound
        # means "this server has no live session to ask".
        self._on_live_update_action_item: Callable[[str, str], Any] | None = None
        self._on_live_review_action_item: Callable[[str, str], Any] | None = None
        self._on_live_edit_action_item: Callable[..., Any] | None = None
        # HS-149-04: optional person resolver for the calendar origin line.
        # When bound, _enrich_calendar_origin extends with person_label.
        self._resolve_person: Callable[[str, str], str | None] | None = None
        self._observer = _MeetingPersonRedactor(observer or NullObserver())

    def bind_lifecycle(
        self,
        *,
        on_start: Callable[..., Any] | None = None,
        on_stop: Callable[[], Any] | None = None,
        on_bookmark: Callable[[str], Any] | None = None,
        on_update: Callable[..., Any] | None = None,
    ) -> None:
        """Bind runtime-owned capture callbacks at an application edge."""
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_bookmark = on_bookmark
        self._on_update = on_update

    def bind_live_triage(
        self,
        *,
        on_update: Callable[[str, str], Any] | None = None,
        on_review: Callable[[str, str], Any] | None = None,
        on_edit: Callable[..., Any] | None = None,
    ) -> None:
        """Bind the runtime's live-session action-item mutations (HS-132-02).

        A meeting that is still running holds its action items in the session,
        not the archive, so the triage verbs ask the live session first and fall
        through to the persisted rows when no live session owns the item.
        """
        self._on_live_update_action_item = on_update
        self._on_live_review_action_item = on_review
        self._on_live_edit_action_item = on_edit

    def bind_person_resolver(
        self,
        resolver: Callable[[str, str], str | None] | None = None,
    ) -> None:
        """HS-149-04: bind a (uid, source_id) -> display_name resolver.

        The resolver returns the person's display_name when the sidecar
        is open and the series is linked, or ``None`` otherwise.
        """
        self._resolve_person = resolver

    def validate_import(self, principal: Principal, filename: str) -> None:
        try:
            validate_format(filename)
        except MeetingImportError as exc:
            raise ValidationError(str(exc)) from exc

    def import_meeting(
        self,
        principal: Principal,
        *,
        tmp_path: Path,
        filename: str,
        title: str | None,
        speaker: str | None,
        tags: list[str],
        started_at: datetime,
        config: Config,
        transcriber_factory: Callable[[Config], Any],
    ) -> dict[str, str]:
        """Create the visible importing row and start its background worker."""
        meeting_id = uuid.uuid4().hex[:8]
        resolved_title = (title or Path(filename).stem).strip() or Path(filename).stem
        placeholder = MeetingState(
            id=meeting_id,
            started_at=started_at,
            title=resolved_title,
            tags=tags,
            segments=[],
        )
        placeholder.intel_status = "importing"
        placeholder.intel_status_detail = (
            "Parsing transcript…"
            if is_transcript_filename(filename)
            else "Preparing transcription…"
        )
        self._db.meetings.save_meeting(placeholder)
        worker = threading.Thread(
            target=self._run_import_job,
            kwargs={
                # HS-131-09: the import transcribes with local Whisper under its own
                # admitted session, so the AUTHENTICATED route principal must reach
                # it. Dropping it here would let a remote import run under the
                # synthesized local-owner hold identity — authority elevation.
                "principal": principal,
                "config": config,
                "meeting_id": meeting_id,
                "tmp_path": tmp_path,
                "title": resolved_title,
                "speaker": speaker,
                "tags": tags,
                "started_at": started_at,
                "transcriber_factory": transcriber_factory,
            },
            daemon=True,
            name=f"meeting-import-{meeting_id}",
        )
        worker.start()
        return {"meeting_id": meeting_id, "status": "importing"}

    def _run_import_job(
        self,
        *,
        principal: Principal,
        config: Config,
        meeting_id: str,
        tmp_path: Path,
        title: str | None,
        speaker: str | None,
        tags: list[str],
        started_at: datetime,
        transcriber_factory: Callable[[Config], Any],
    ) -> None:
        try:
            if is_transcript_filename(tmp_path.name):
                import_transcript(
                    tmp_path,
                    db=self._db,
                    config=config,
                    meeting_id=meeting_id,
                    title=title,
                    speaker=speaker or DEFAULT_TRANSCRIPT_SPEAKER_LABEL,
                    tags=tags,
                    started_at=started_at,
                )
                return
            transcriber = transcriber_factory(config)

            def on_progress(done: int, total: int) -> None:
                self._set_import_status(
                    meeting_id, "importing", f"Transcribing — window {done} of {total}."
                )

            run_meeting_import(
                tmp_path,
                db=self._db,
                transcriber=transcriber,
                config=config,
                meeting_id=meeting_id,
                title=title,
                speaker=speaker or DEFAULT_SPEAKER_LABEL,
                tags=tags,
                started_at=started_at,
                progress=on_progress,
                principal=principal,
            )
        except MeetingImportError as exc:
            self._set_import_status(meeting_id, "import_failed", str(exc))
        except Exception as exc:  # noqa: BLE001 — preserve the durable failure state.
            self._set_import_status(
                meeting_id, "import_failed", f"{type(exc).__name__}: {exc}"
            )
        finally:
            tmp_path.unlink(missing_ok=True)

    def _set_import_status(self, meeting_id: str, status: str, detail: str) -> None:
        state = self._db.meetings.get_meeting(meeting_id)
        if state is None:
            return
        state.intel_status = status
        state.intel_status_detail = detail
        self._db.meetings.save_meeting(state)

    def list_meetings(
        self,
        principal: Principal,
        query: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 50,
        cursor: str | int | None = None,
        *,
        speaker: str | None = None,
        tag: str | None = None,
        has_open_actions: bool = False,
    ) -> dict[str, Any]:
        """Return archive summaries, preserving the web archive's filters."""
        bounded_limit = max(1, min(int(limit), 500))
        offset = self._offset(cursor)
        parsed_from = self._parse_date(from_date)
        parsed_to = self._parse_date(to_date, end_of_day=True)
        search_ids: list[str] | None = None
        if query and query.strip():
            search_ids = list(
                dict.fromkeys(
                    meeting_id
                    for meeting_id, _ in self._db.meetings.search_transcripts(
                        query.strip(), limit=500
                    )
                )
            )
        meetings = self._db.meetings.list_meetings(
            limit=bounded_limit,
            offset=offset,
            date_from=parsed_from,
            date_to=parsed_to,
            speaker=speaker,
            tag=tag,
            has_open_actions=has_open_actions,
            meeting_ids=search_ids,
        )
        filtered = bool(query or from_date or to_date or speaker or tag or has_open_actions)
        total = len(meetings) if filtered else self._db.meetings.get_meeting_count()
        payloads = [self._summary_payload(meeting) for meeting in meetings]
        self._enrich_calendar_origin(payloads)
        return {
            "meetings": payloads,
            "total": total,
            "next_cursor": str(offset + len(meetings)) if len(meetings) == bounded_limit else None,
        }

    def get_meeting(
        self,
        principal: Principal,
        meeting_id: str | None = None,
        include: str | None = None,
        *,
        id: str | None = None,
    ) -> dict[str, Any]:
        """Return a meeting; ``id`` is accepted for adapter-facing callers."""
        resolved_id = id if id is not None else meeting_id
        if not resolved_id:
            raise ValidationError("meeting id is required")
        meeting = self._db.meetings.get_meeting(resolved_id)
        if meeting is None:
            raise NotFound("meeting", resolved_id)
        payload = meeting.to_dict()
        self._enrich_calendar_origin([payload])
        return payload

    def start_capture(
        self, principal: Principal, config: dict[str, Any] | None = None
    ) -> dict[str, Any] | Any:
        if self._on_start is None:
            raise ValidationError("Meeting start control not supported")
        devices = list((config or {}).get("devices") or [])
        # HS-131-08: the AUTHENTICATED caller reaches capture start, because live
        # meeting intelligence is admitted under exactly this principal.
        kwargs: dict[str, Any] = {"principal": principal} if _accepts_principal(self._on_start) else {}
        if devices:
            kwargs["devices"] = devices
        result = self._on_start(**kwargs)
        return self._callback_payload(result)

    def stop_capture(
        self, principal: Principal, meeting_id: str | None = None
    ) -> dict[str, Any] | Any:
        if self._on_stop is None:
            raise ValidationError("Meeting stop control not supported")
        return self._callback_payload(self._on_stop()) or {"status": "stopped"}

    def bookmark(
        self,
        principal: Principal,
        meeting_id: str | None = None,
        *,
        label: str = "",
    ) -> dict[str, Any] | Any:
        if self._on_bookmark is None:
            raise ValidationError("Meeting bookmark control not supported")
        return self._callback_payload(self._on_bookmark(label))

    def update_meeting(
        self, principal: Principal, meeting_id: str, **patch: Any
    ) -> dict[str, Any]:
        title = patch.get("title")
        tags = patch.get("tags")
        if title is not None and not isinstance(title, str):
            raise ValidationError("meeting title must be a string")
        if tags is not None and not isinstance(tags, list):
            raise ValidationError("meeting tags must be a list")
        if self._on_update is not None:
            result = self._on_update(title=title, tags=tags)
            return self._callback_payload(result) or {}

        existing = self._db.meetings.get_meeting(meeting_id)
        if existing is None:
            raise NotFound("meeting", meeting_id)
        updated = self._db.meetings.update_meeting_metadata(
            meeting_id,
            title if title is not None else (existing.title or ""),
            tags if tags is not None else existing.tags,
        )
        if not updated:
            raise NotFound("meeting", meeting_id)
        return self.get_meeting(principal, meeting_id)

    def rename_meeting(
        self, principal: Principal, meeting_id: str, title: str
    ) -> dict[str, Any]:
        """Rename ONE archived meeting (HS-132-07).

        ``update_meeting`` speaks to the live capture session when one is
        bound, so it can never address a specific archived meeting. Rename
        is the archive's own verb: it writes the named row and nothing else.
        """
        if not isinstance(title, str):
            raise ValidationError("meeting title must be a string")
        name = title.strip()
        if not name:
            raise ValidationError("meeting title must not be empty")
        existing = self._db.meetings.get_meeting(meeting_id)
        if existing is None:
            raise NotFound("meeting", meeting_id)
        if not self._db.meetings.update_meeting_metadata(
            meeting_id, name, existing.tags
        ):
            raise NotFound("meeting", meeting_id)
        return self.get_meeting(principal, meeting_id)

    def delete_meeting(self, principal: Principal, meeting_id: str) -> bool:
        if not self._db.meetings.delete_meeting(meeting_id):
            raise NotFound("meeting", meeting_id)
        return True

    def export_meeting(
        self, principal: Principal, meeting_id: str, format: str
    ) -> dict[str, str]:
        export_format = str(format or "").strip().lower()
        if export_format == "md":
            export_format = "markdown"
        if export_format not in {"markdown", "json"}:
            raise ValidationError(f"Invalid export format: {format}")
        meeting = self._db.meetings.get_meeting(meeting_id)
        if meeting is None:
            raise NotFound("meeting", meeting_id)
        content = render_meeting_export(
            meeting,
            export_format,  # type: ignore[arg-type]
            artifacts=self._db.plugins.list_artifacts(meeting_id, limit=200),
        )
        extension = "md" if export_format == "markdown" else "json"
        return {
            "content": content,
            "media_type": (
                "text/markdown; charset=utf-8"
                if export_format == "markdown"
                else "application/json; charset=utf-8"
            ),
            "filename": f"holdspeak-meeting-{meeting_id}.{extension}",
        }

    def search_artifacts(
        self, principal: Principal, query: str, limit: int = 50
    ) -> dict[str, Any]:
        clean_query = str(query or "").strip()
        if not clean_query:
            raise ValidationError("query is required")
        return self._db.memory.search(
            clean_query, kinds=("artifact",), limit=limit
        ).to_dict()

    def get_intent_timeline(self, principal: Principal, meeting_id: str, limit: int = 200) -> dict[str, Any]:
        if self._db.meetings.get_meeting(meeting_id) is None:
            raise NotFound("meeting", meeting_id)
        from ..intent_timeline import detect_intent_transitions
        windows = self._db.plugins.list_intent_windows(meeting_id, limit=limit)
        return {"meeting_id": meeting_id, "windows": [{"meeting_id": window.meeting_id, "window_id": window.window_id, "start_seconds": window.start_seconds, "end_seconds": window.end_seconds, "transcript_hash": window.transcript_hash, "transcript_excerpt": window.transcript_excerpt, "profile": window.profile, "threshold": window.threshold, "active_intents": window.active_intents, "intent_scores": window.intent_scores, "override_intents": window.override_intents, "tags": window.tags, "metadata": window.metadata, "created_at": window.created_at.isoformat(), "updated_at": window.updated_at.isoformat()} for window in windows], "transitions": detect_intent_transitions([(window.window_id, list(window.active_intents)) for window in windows])}

    def list_plugin_runs(self, principal: Principal, meeting_id: str, *, limit: int = 500, window_id: str | None = None) -> dict[str, Any]:
        if self._db.meetings.get_meeting(meeting_id) is None:
            raise NotFound("meeting", meeting_id)
        runs = self._db.plugins.list_plugin_runs(meeting_id, window_id=window_id, limit=limit)
        return {"meeting_id": meeting_id, "window_id": window_id, "runs": [{"id": run.id, "meeting_id": run.meeting_id, "window_id": run.window_id, "plugin_id": run.plugin_id, "plugin_version": run.plugin_version, "status": run.status, "idempotency_key": run.idempotency_key, "duration_ms": run.duration_ms, "output": run.output, "error": run.error, "deduped": run.deduped, "created_at": run.created_at.isoformat(), "updated_at": run.updated_at.isoformat()} for run in runs]}

    def list_artifacts(self, principal: Principal, meeting_id: str, limit: int = 200) -> dict[str, Any]:
        if self._db.meetings.get_meeting(meeting_id) is None:
            raise NotFound("meeting", meeting_id)
        artifacts = self._db.plugins.list_artifacts(meeting_id, limit=limit)
        return {"meeting_id": meeting_id, "artifacts": [{"id": artifact.id, "meeting_id": artifact.meeting_id, "artifact_type": artifact.artifact_type, "title": artifact.title, "body_markdown": artifact.body_markdown, "structured_json": artifact.structured_json, "confidence": artifact.confidence, "status": artifact.status, "plugin_id": artifact.plugin_id, "plugin_version": artifact.plugin_version, "sources": artifact.sources, "created_at": artifact.created_at.isoformat(), "updated_at": artifact.updated_at.isoformat(), "origin": artifact.origin} for artifact in artifacts]}

    def facets(self, principal: Principal, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return archive facet values from the same durable meeting store."""
        return self._db.meetings.list_facet_values()

    def recover_capture(self, principal: Principal, meeting_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        meeting = self._db.meetings.recover_capture(meeting_id)
        if meeting is None:
            raise NotFound("meeting", meeting_id)
        return {"meeting": meeting.to_dict(), "recovered": True}

    def list_sync_conflicts(self, principal: Principal, meeting_id: str) -> dict[str, Any]:
        if self._db.meetings.get_meeting(meeting_id) is None:
            raise NotFound("meeting", meeting_id)
        return {"conflicts": self._db.meetings.list_sync_conflicts(meeting_id)}

    def resolve_sync_conflict(self, principal: Principal, meeting_id: str, conflict_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        resolution = str(payload.get("resolution") or "").strip()
        if resolution not in {"keep_current", "use_incoming"}:
            raise ValidationError("resolution must be keep_current or use_incoming")
        conflict = self._db.meetings.get_sync_conflict(meeting_id, conflict_id)
        if conflict is None:
            raise NotFound("meeting conflict", conflict_id)
        if conflict.get("resolved_at") is not None:
            raise ConflictError("Meeting conflict was already resolved; reload the Meeting.", code="already_resolved")
        incoming_state = None
        incoming = conflict.get("incoming")
        if resolution == "use_incoming" and not (isinstance(incoming, dict) and bool(incoming.get("deleted"))):
            if not isinstance(incoming, dict):
                raise ConflictError("Incoming Meeting version is unreadable; current work retained.", code="unreadable_incoming")
            try:
                from .sync_service import meeting_state_from_sync_value
                incoming_state = meeting_state_from_sync_value({**incoming, "id": meeting_id})
            except (TypeError, ValueError) as exc:
                raise ConflictError(f"Incoming Meeting version is unreadable; current work retained: {exc}", code="unreadable_incoming") from exc
        try:
            outcome = self._db.meetings.resolve_sync_conflict(meeting_id, conflict_id, resolution=resolution, incoming_state=incoming_state)
        except (TypeError, ValueError) as exc:
            raise ConflictError(f"Conflict was not changed; both versions remain: {exc}. Choose a version and retry.", code="resolution_failed") from exc
        if outcome == "missing":
            raise NotFound("meeting conflict", conflict_id)
        if outcome == "already_resolved":
            raise ConflictError("Meeting conflict was already resolved; reload the Meeting.", code="already_resolved")
        meeting = self._db.meetings.get_meeting(meeting_id)
        return {"resolution": resolution, "deleted": outcome == "deleted", "meeting": meeting.to_dict() if meeting is not None else None, "remaining_conflicts": self._db.meetings.list_sync_conflicts(meeting_id)}

    def list_speakers(self, principal: Principal, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        speakers = []
        for speaker in self._db.meetings.get_all_speakers():
            stats = self._db.meetings.get_speaker_stats(speaker.id)
            speakers.append({
                "id": speaker.id, "name": speaker.name, "avatar": speaker.avatar,
                "sample_count": speaker.sample_count,
                "total_segments": stats.get("total_segments", 0),
                "total_speaking_time": stats.get("total_speaking_time", 0.0),
                "meeting_count": stats.get("meeting_count", 0),
                "first_seen": stats["first_seen"].isoformat() if stats.get("first_seen") else None,
                "last_seen": stats["last_seen"].isoformat() if stats.get("last_seen") else None,
            })
        speakers.sort(key=lambda item: (item.get("last_seen") or "", item.get("sample_count") or 0), reverse=True)
        return {"speakers": speakers, "total": len(speakers)}

    def get_speaker(self, principal: Principal, speaker_id: str, limit: int = 500) -> dict[str, Any]:
        speaker = self._db.meetings.get_speaker(speaker_id)
        if speaker is None:
            raise NotFound("speaker", speaker_id)
        stats = self._db.meetings.get_speaker_stats(speaker_id)
        groups = self._db.meetings.get_speaker_segments(speaker_id, limit=limit)
        for group in groups:
            if isinstance(group.get("meeting_date"), datetime):
                group["meeting_date"] = group["meeting_date"].isoformat()
        return {"speaker": {"id": speaker.id, "name": speaker.name, "avatar": speaker.avatar, "sample_count": speaker.sample_count}, "stats": {"total_segments": stats.get("total_segments", 0), "total_speaking_time": stats.get("total_speaking_time", 0.0), "meeting_count": stats.get("meeting_count", 0), "first_seen": stats["first_seen"].isoformat() if stats.get("first_seen") else None, "last_seen": stats["last_seen"].isoformat() if stats.get("last_seen") else None}, "meetings": groups}

    def update_speaker(self, principal: Principal, speaker_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        updated = False
        if patch.get("name") is not None:
            name = str(patch["name"]).strip()
            if not name:
                raise ValidationError("Speaker name cannot be empty. The saved name is unchanged. Enter a name and retry.")
            updated = self._db.meetings.update_speaker_name(speaker_id, name) or updated
        if patch.get("avatar") is not None:
            avatar = str(patch["avatar"]).strip()
            if not avatar:
                raise ValidationError("Speaker avatar cannot be empty. The saved avatar is unchanged. Pick an avatar and retry.")
            updated = self._db.meetings.update_speaker_avatar(speaker_id, avatar) or updated
        speaker = self._db.meetings.get_speaker(speaker_id) if updated else None
        if speaker is None:
            raise NotFound("speaker", speaker_id)
        return {"success": True, "speaker": {"id": speaker.id, "name": speaker.name, "avatar": speaker.avatar, "sample_count": speaker.sample_count}}

    def list_all_action_items(self, principal: Principal, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        filters = filters or {}
        items = self._db.meetings.list_action_items(include_completed=bool(filters.get("include_completed", False)), owner=filters.get("owner"), meeting_id=filters.get("meeting_id"))
        return {"action_items": [self._action_item_payload(item) for item in items]}

    def update_action_item(self, principal: Principal, item_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        status = patch.get("status")
        if status not in ("done", "pending", "dismissed"):
            raise ValidationError(f"Invalid status: {status}")
        live = self._live_triage(self._on_live_update_action_item, item_id, status)
        if live is not None:
            return {"success": True, "action_item": live}
        if not self._db.meetings.update_action_item_status(item_id, status):
            raise self._unserved_action_item(item_id, self._on_live_update_action_item)
        return self._updated_action_item(item_id)

    def review_action_item(self, principal: Principal, item_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        state = str(patch.get("review_state") or "").strip().lower()
        if state not in ("pending", "accepted"):
            raise ValidationError(f"Invalid review_state: {state}")
        live = self._live_triage(self._on_live_review_action_item, item_id, state)
        if live is not None:
            return {"success": True, "action_item": live}
        if not self._db.meetings.update_action_item_review_state(item_id, state):
            raise self._unserved_action_item(item_id, self._on_live_review_action_item)
        return self._updated_action_item(item_id)

    def edit_action_item(self, principal: Principal, item_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        task = str(patch.get("task") or "").strip()
        if not task:
            raise ValidationError("Action item task cannot be empty. The saved task is unchanged. Enter a task and retry.")
        owner, due = patch.get("owner"), patch.get("due")
        live = self._live_triage(self._on_live_edit_action_item, item_id, task=task, owner=owner, due=due)
        if live is not None:
            return {"success": True, "action_item": live}
        if not self._db.meetings.edit_action_item(item_id, task=task, owner=owner, due=due):
            raise self._unserved_action_item(item_id, self._on_live_edit_action_item)
        return self._updated_action_item(item_id)

    def _live_triage(self, callback: Callable[..., Any] | None, item_id: str, *args: Any, **kwargs: Any) -> dict[str, Any] | None:
        """Ask the live session first; ``None`` means "no live session owns it".

        Callback failures are never swallowed — a live session that raises is a
        real failure, not a reason to quietly rewrite the archive instead.
        """
        if callback is None:
            return None
        return self._callback_payload(callback(item_id, *args, **kwargs))

    @staticmethod
    def _unserved_action_item(item_id: str, callback: Callable[..., Any] | None) -> ServiceError:
        if callback is None:
            return ActionItemTriageUnavailable(item_id)
        return NotFound("action item", item_id)

    def _updated_action_item(self, item_id: str) -> dict[str, Any]:
        item = self._db.meetings.get_action_item(item_id)
        return {"success": True, "action_item": self._action_item_payload(item) if item is not None else None}

    @staticmethod
    def _action_item_payload(item: Any) -> dict[str, Any]:
        return {"id": item.id, "task": item.task, "owner": item.owner, "due": item.due, "status": item.status, "review_state": item.review_state, "source_timestamp": item.source_timestamp, "meeting_id": item.meeting_id, "meeting_title": item.meeting_title, "meeting_date": item.meeting_date.isoformat(), "created_at": item.created_at.isoformat(), "completed_at": item.completed_at.isoformat() if item.completed_at else None, "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None}

    @staticmethod
    def _callback_payload(result: Any) -> dict[str, Any] | Any | None:
        if hasattr(result, "to_dict"):
            return result.to_dict()
        return result if isinstance(result, dict) else None

    @staticmethod
    def _parse_date(value: str | None, *, end_of_day: bool = False) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValidationError(f"Invalid date: {value}") from exc
        if end_of_day and len(text) == 10:
            return parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
        return parsed

    @staticmethod
    def _offset(cursor: str | int | None) -> int:
        if cursor in (None, ""):
            return 0
        try:
            return max(0, int(cursor))
        except (TypeError, ValueError) as exc:
            raise ValidationError("cursor must be a non-negative integer") from exc

    def _enrich_calendar_origin(self, payloads: list[dict[str, Any]]) -> None:
        """Attach calendar event title and source label to meeting payloads.

        Honest degradation: when the calendar_events row is gone (feed moved
        on), the fields stay absent rather than raising a dangling lookup error.
        """
        event_ids = [
            p["calendar_event_id"]
            for p in payloads
            if p.get("calendar_event_id")
        ]
        if not event_ids:
            return
        event_map: dict[str, Any] = {}
        for eid in event_ids:
            try:
                ev = self._db.calendar_events.get(eid)
                if ev is not None:
                    event_map[eid] = ev
            except Exception:
                pass
        for p in payloads:
            eid = p.get("calendar_event_id")
            if not eid:
                continue
            ev = event_map.get(eid)
            if ev is not None:
                p["calendar_event_title"] = ev.title
                p["calendar_source_label"] = ev.source_label
                # HS-149-04: resolve person display name when the sidecar is open.
                if self._resolve_person is not None:
                    try:
                        person = self._resolve_person(ev.uid, ev.source_id)
                        if person:
                            p["person_label"] = person
                    except Exception:
                        pass

    @staticmethod
    def _summary_payload(meeting: Any) -> dict[str, Any]:
        return {
            "id": meeting.id,
            "started_at": meeting.started_at.isoformat(),
            "ended_at": meeting.ended_at.isoformat() if meeting.ended_at else None,
            "title": meeting.title,
            "duration_seconds": meeting.duration_seconds,
            "segment_count": meeting.segment_count,
            "action_item_count": meeting.action_item_count,
            "tags": meeting.tags,
            "intel_status": meeting.intel_status,
            "intel_status_detail": meeting.intel_status_detail,
            "capture_status": meeting.capture_status,
            "capture_failure": meeting.capture_failure,
            "capture_checkpoint_seconds": meeting.capture_checkpoint_seconds,
            "provenance": meeting.provenance,
            "calendar_event_id": getattr(meeting, "calendar_event_id", None),
        }
