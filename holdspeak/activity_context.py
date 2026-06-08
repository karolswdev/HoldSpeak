"""Shared activity context bundles for HoldSpeak plugins."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Any, Optional

from .activity_history import import_browser_history
from .db import ActivityRecord, Database, get_database
from .logging_config import get_logger

log = get_logger("activity_context")


@dataclass(frozen=True)
class ActivityContextBundle:
    """Serializable local activity context for plugin consumers."""

    records: list[dict[str, Any]]
    entity_counts: dict[str, int]
    domain_counts: dict[str, int]
    source_counts: dict[str, int]
    generated_at: str
    project_id: Optional[str] = None
    refreshed: bool = False
    refresh_errors: list[str] | None = None
    # Phase 53 (HS-53-03): when a nudge action selects a specific record, its id
    # is pinned at `records[0]` and recorded here so the rewrite stage can name
    # which entity the user is dictating "with". `None` for the default daily
    # path (byte-identical to pre-Phase-53 behaviour).
    selected_record_id: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "records": list(self.records),
            "entity_counts": dict(self.entity_counts),
            "domain_counts": dict(self.domain_counts),
            "source_counts": dict(self.source_counts),
            "generated_at": self.generated_at,
            "project_id": self.project_id,
            "refreshed": self.refreshed,
            "refresh_errors": list(self.refresh_errors or []),
        }
        if self.selected_record_id is not None:
            payload["selected_record_id"] = int(self.selected_record_id)
        return payload


class ActivityContextProvider:
    """Callable context provider that injects local activity into plugins."""

    def __init__(
        self,
        *,
        db: Database | None = None,
        limit: int = 20,
        refresh: bool = False,
        refresh_once: bool = True,
        importer: Callable[..., Any] = import_browser_history,
    ) -> None:
        self._db = db
        self._limit = max(1, min(int(limit), 200))
        self._refresh = bool(refresh)
        self._refresh_once = bool(refresh_once)
        self._importer = importer
        self._lock = Lock()
        self._refreshed = False

    def __call__(self, context: dict[str, Any]) -> dict[str, Any]:
        project_id = _project_id_from_context(context)
        selected_record_id = _selected_record_id_from_context(context)
        bundle = build_activity_context(
            db=self._db,
            project_id=project_id,
            limit=self._limit,
            refresh=self._should_refresh(),
            importer=self._importer,
            selected_record_id=selected_record_id,
        )
        return {"activity": bundle.to_dict()}

    def _should_refresh(self) -> bool:
        if not self._refresh:
            return False
        with self._lock:
            if self._refresh_once and self._refreshed:
                return False
            self._refreshed = True
            return True


def build_activity_context(
    *,
    db: Database | None = None,
    project_id: Optional[str] = None,
    limit: int = 20,
    refresh: bool = False,
    importer: Callable[..., Any] = import_browser_history,
    selected_record_id: Optional[int] = None,
) -> ActivityContextBundle:
    """Build a plugin-safe local activity context bundle."""
    database = db or get_database()
    refresh_errors: list[str] = []
    did_refresh = False
    if refresh:
        try:
            results = importer(db=database)
            did_refresh = True
            refresh_errors = [
                str(result.error)
                for result in results
                if getattr(result, "error", None)
            ]
        except Exception as exc:
            refresh_errors.append(f"{type(exc).__name__}: {exc}")
            log.warning("Activity context refresh failed: %s", exc)

    records = database.activity.list_activity_records(
        project_id=project_id,
        limit=max(1, min(int(limit), 200)),
    )
    serialized = [_serialize_activity_record(record) for record in records]

    resolved_selected_id: Optional[int] = None
    if selected_record_id is not None:
        # Pin the selected record at records[0] so the rewrite stage names it
        # first. Unknown ids are a quiet no-op — the default daily path stays
        # byte-identical.
        serialized, resolved_selected_id = _pin_selected_record(
            database, serialized, selected_record_id
        )

    return ActivityContextBundle(
        records=serialized,
        entity_counts=dict(Counter(item["entity_type"] for item in serialized if item["entity_type"])),
        domain_counts=dict(Counter(item["domain"] for item in serialized if item["domain"])),
        source_counts=dict(Counter(item["source_browser"] for item in serialized if item["source_browser"])),
        generated_at=datetime.now().isoformat(),
        project_id=project_id,
        refreshed=did_refresh,
        refresh_errors=refresh_errors,
        selected_record_id=resolved_selected_id,
    )


def _pin_selected_record(
    database: Database,
    serialized: list[dict[str, Any]],
    selected_record_id: int,
) -> tuple[list[dict[str, Any]], Optional[int]]:
    """Move the selected record to ``records[0]``; fetch it if absent.

    Returns the reordered list and the resolved selected id (``None`` when the
    id does not match a real record — the engine refuses to fabricate context).
    """
    try:
        wanted_id = int(selected_record_id)
    except (TypeError, ValueError):
        return serialized, None

    for index, item in enumerate(serialized):
        if item.get("id") == wanted_id:
            if index == 0:
                return serialized, wanted_id
            reordered = [item] + serialized[:index] + serialized[index + 1 :]
            return reordered, wanted_id

    record = database.activity.get_activity_record(wanted_id)
    if record is None:
        return serialized, None
    pinned = _serialize_activity_record(record)
    return [pinned] + serialized, wanted_id


def _serialize_activity_record(record: ActivityRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "source_browser": record.source_browser,
        "source_profile": record.source_profile,
        "url": record.url,
        "title": record.title,
        "domain": record.domain,
        "visit_count": record.visit_count,
        "first_seen_at": record.first_seen_at.isoformat() if record.first_seen_at else None,
        "last_seen_at": record.last_seen_at.isoformat() if record.last_seen_at else None,
        "entity_type": record.entity_type,
        "entity_id": record.entity_id,
        "project_id": record.project_id,
    }


def _selected_record_id_from_context(context: dict[str, Any]) -> Optional[int]:
    """Phase 53 (HS-53-03): a nudge action puts the selected record id here.

    Looks for ``context["selected_activity_record_id"]`` (preferred) or, as a
    convenience for callers that bundle the whole nudge,
    ``context["selected_activity"]["record_id"]``. Returns ``None`` when absent
    or unparsable so the default daily path is byte-identical.
    """
    raw = context.get("selected_activity_record_id")
    if raw in (None, ""):
        selected = context.get("selected_activity")
        if isinstance(selected, dict):
            raw = selected.get("record_id") or selected.get("id")
    if raw in (None, ""):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _project_id_from_context(context: dict[str, Any]) -> Optional[str]:
    raw_project_id = context.get("project_id")
    if raw_project_id not in (None, ""):
        return str(raw_project_id)
    project = context.get("project")
    if isinstance(project, dict):
        raw_project_id = project.get("id") or project.get("project_id")
        if raw_project_id not in (None, ""):
            return str(raw_project_id)
    return None
