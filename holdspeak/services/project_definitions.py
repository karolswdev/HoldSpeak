"""The Project vocabulary and its pure word helpers (2026-11-08, after HS-S51).

The words every Project reader shares: the hub's local week and its stamp
forms, the watch source maps, the closed Project and item vocabularies
(lifecycles, severities, item types and their lifecycles, provenance kinds,
the per-type ``details_json`` schemas), the Room caps and receipt scope, the
needs-you words (change-kind phrases, plain reasons, severity and token
order), and the pure helpers that turn a row into words or refuse a bad
word (``validate_severity``, ``validate_lifecycle``, ``validate_optional_ref``,
``validate_details``: each raises :class:`~holdspeak.services.errors.ValidationError`).

One direction only: this module imports nothing from ``project_service``,
``project_room*``, the web or the runtime. ``project_service`` re-exports
every name here, so ``project_service.ITEM_LIFECYCLES is
project_definitions.ITEM_LIFECYCLES``; ``ProjectService`` keeps its old
class attributes as aliases of the same objects. The runtime (the write
lock, the command replay, the custody identity, the review query boundary,
the repositories) stays in the service.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from ..refs import parse as parse_ref
from .errors import ValidationError


# ── HS-175 counsel C8: the hub's local week, one helper ──────────────
#
# Calendar events are stored UTC (``YYYY-MM-DDTHH:MM:SSZ``); the owner's
# week is his local week.  Every "this week" read in this service and the
# calendar sources route goes through this helper so the Monday boundary
# is the hub's local Monday (``datetime.now().astimezone()``), consistent
# with the arrival's strip.


def local_now(now: datetime | None = None) -> datetime:
    """The hub's local, tz-aware now (or ``now`` made aware in local tz)."""
    if now is None:
        return datetime.now().astimezone()
    if now.tzinfo is None:
        return now.astimezone()
    return now


def localize(wall: datetime) -> datetime:
    """A naive LOCAL wall-clock -> aware, with THAT instant's offset.

    Counsel re-read condition 4 (DST): ``datetime.now().astimezone()`` yields
    a FIXED offset; arithmetic in it crosses a DST edge an hour off.  A
    naive value's ``.astimezone()`` consults the system zone's rules for the
    instant itself, so every bound carries its own true offset.
    """
    return wall.replace(tzinfo=None).astimezone()


def local_week_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    """(local Monday 00:00, next local Monday 00:00) as aware datetimes,
    each localized per instant (DST-safe)."""
    current = local_now(now)
    wall = current.replace(tzinfo=None)
    monday_wall = (wall - timedelta(days=wall.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )
    return localize(monday_wall), localize(monday_wall + timedelta(days=7))


def _wall(value: Any) -> datetime | None:
    """A stored stamp as a naive LOCAL wall clock (aware stamps converted)."""
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def utc_z(value: datetime) -> str:
    """Aware datetime -> the stored calendar_events form ``...Z``."""
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def aware_iso(value: Any) -> str | None:
    """Normalize a stored timestamp to an offset-carrying ISO string.

    SQLite's ``datetime('now')`` writes naive UTC (``YYYY-MM-DD HH:MM:SS``);
    the browser's ``new Date()`` would read that as LOCAL time and print
    the wrong clock (counsel H4-1: ``CHECKED 23:47`` beside ``READ 17:48``).
    A naive value is UTC here by construction; an aware value passes
    through.  ``None``/empty stays ``None``.
    """
    if value is None or value == "":
        return None
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat(timespec="seconds")


# ── M-1 finalize mapping tables (HS-161-07 counsel) ─────────────────
#
# _PROVIDER_TO_CONNECTOR: the watch table's connector_id is "gh", not
# "github".  Moved from the loop body to module level per counsel N-2.
#
# _SUBJECT_TO_QUERY_KIND: WatchSpec@1 subject.kind is singular
# ("pull_request"), but GitHubWatchSource.snapshot demands the plural
# wire form ("pull_requests").  The mapping lives here rather than in
# the spec so the spec vocabulary stays domain-level.
_PROVIDER_TO_CONNECTOR: dict[str, str] = {
    "github": "gh", "jira": "jira", "meeting": "meeting",
}

_SUBJECT_TO_QUERY_KIND: dict[str, str] = {
    "pull_request": "pull_requests",
    "issue": "issues",
    "branch_ci": "branch_ci",  # HS-169-04: CI on the base branch
    "meeting": "meetings",  # HS-175-04: meeting watch adapter
}


# ── Closed Project Room vocabularies (HS-158-02, SRS WEB §4) ─────────

# Project lifecycle: closed vocabulary per SRS WEB-LC §4.
# 'archived' is EXCLUDED — it is a storage state managed by archive_project/
# restore_project, not a user-settable lifecycle value via PATCH.
PROJECT_LIFECYCLES: frozenset[str] = frozenset({
    "proposed", "active", "paused", "complete", "cancelled",
})

# Maximum lengths for free-text room fields.
_POSTURE_MAX = 64
_POSTURE_REASON_MAX = 500
_SLUG_MAX = 64

# ── Closed item vocabularies (HS-158-03) ──────────────────────────────

# Severity: nullable; validated on write.
SEVERITY_LEVELS: frozenset[str] = frozenset({
    "critical", "high", "medium", "low",
})

# Explicit rank for focus ordering (CASE expression: highest first).
SEVERITY_RANK: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}

# Item types and their closed lifecycle vocabularies.
ITEM_TYPES: frozenset[str] = frozenset({
    "milestone", "risk", "dependency", "signal", "workstream",
})

ITEM_LIFECYCLES: dict[str, tuple[str, ...]] = {
    "milestone": ("planned", "reached", "missed", "dropped"),
    "risk": ("open", "mitigated", "accepted", "closed"),
    "dependency": ("healthy", "at_risk", "broken", "resolved"),
    "signal": ("active", "retired"),
    "workstream": ("active", "paused", "done"),
}

# Default lifecycle per item type (the initial state on create).
ITEM_DEFAULT_LIFECYCLE: dict[str, str] = {
    "milestone": "planned",
    "risk": "open",
    "dependency": "healthy",
    "signal": "active",
    "workstream": "active",
}

# Provenance kinds (P1 = owner only).
PROVENANCE_KINDS: frozenset[str] = frozenset({"owner"})

# ── Closed details_json schemas per item_type (DB-004) ────────────────
#
# Each entry: field_name -> (required, validator_fn).
# Unknown fields are refused.  Common fields (title, summary, lifecycle,
# severity, owner_ref, due_at, sort_key) are COLUMNS, not in details_json.

def _is_str(v: Any) -> bool:
    return isinstance(v, str)

def _is_str_or_none(v: Any) -> bool:
    return v is None or isinstance(v, str)

def _is_number_or_none(v: Any) -> bool:
    return v is None or isinstance(v, (int, float))

_DETAILS_SCHEMAS: dict[str, dict[str, tuple[bool, Any]]] = {
    "milestone": {
        # completion_evidence_refs: optional list of ref strings
        "completion_evidence_refs": (False, lambda v: v is None or (isinstance(v, list) and all(isinstance(x, str) for x in v))),
    },
    "risk": {
        "likelihood": (True, _is_str),
        "impact": (True, _is_str),
        "mitigation": (False, _is_str_or_none),
    },
    "dependency": {
        "direction": (True, lambda v: v in ("upstream", "downstream")),
        "counterpart_ref": (True, _is_str),
        "required_by": (False, _is_str_or_none),
        "confidence": (False, _is_str_or_none),
    },
    "signal": {
        "metric": (True, _is_str),
        "unit": (False, _is_str_or_none),
        "latest_value": (False, _is_number_or_none),
        "source_ref": (False, _is_str_or_none),
        "observed_at": (False, _is_str_or_none),
    },
    "workstream": {
        # No type-specific extras.
    },
}

# ── Room projection constants (HS-158-04, DB-005/NFR-001) ───────────────
# WEB-NOW-006 spirit: the focus block shows the top-N most urgent items.
ROOM_FOCUS_CAP: int = 5
# Recent changes shown in the room projection.
ROOM_CHANGES_CAP: int = 10

# Absent-section marker for domains not yet built (Art VI, NFR-006).
_ABSENT_SECTION: dict[str, str] = {"state": "absent", "reason": "not_yet_built"}

#: PHILO-9-01 (F7): the observed service methods that WRITE a Room; the
#: Room's RECEIPTS list these pipeline events only (its reads are not
#: receipts). Only ``@observe_service`` classes emit pipeline events:
#: ProjectService and WatchService.
ROOM_WRITE_METHODS: frozenset[str] = frozenset({
    # ProjectService
    "create_project", "create_from_setup", "update_project", "archive_project",
    "restore_project", "add_resource", "remove_resource", "associate_meeting",
    "disassociate_meeting", "create_item", "create_item_in_transaction",
    "update_item", "transition_item", "save_ask", "record_ask_stop", "discard_ask",
    # WatchService (a Room's watches)
    "update_watch", "pause_watch", "resume_watch", "retire_watch",
    "test_watch", "baseline_watch", "evaluate_once", "set_rules",
})


#: PHILO-9-03 (F7): admitted Room operations whose write is a ProjectService
#: call -- already a pipeline receipt, so the kernel read skips them.
_SERVICE_OBSERVED_OPERATIONS: frozenset[str] = frozenset({
    "project.create", "project.archive", "project.restore", "project.update",
    "project.link", "project.unlink",
})
_SERVICE_OBSERVED_PREFIXES: tuple[str, ...] = ("project.item.", "project.resource.", "project.door.")


#: PHILO-9-03 (Codex Astra r2 finding 3): where each Room write's PRODUCER
#: writes the project's identity -- a structured field, never any value in the
#: payload (a title equal to another project's id is free text). The census
#: fence (tests/unit/test_philo9_03_receipt_scope.py) holds every method of
#: ROOM_WRITE_METHODS to exactly one entry here.
#:   ("args", "project_id")   the call's own ``project_id`` argument
#:   ("result", "id")         the created project's own id
#:   ("result", "project_id") the returned record's ``project_id`` field
_RECEIPT_SCOPE: dict[str, tuple[str, str]] = {
    "create_project": ("result", "id"),
    "create_from_setup": ("result", "id"),
    **{m: ("args", "project_id") for m in (
        "update_project", "archive_project", "restore_project", "add_resource", "remove_resource",
        "associate_meeting", "disassociate_meeting", "create_item", "create_item_in_transaction",
        "update_item", "transition_item", "save_ask")},
    **{m: ("result", "project_id") for m in (
        "record_ask_stop", "discard_ask",
        "update_watch", "pause_watch", "resume_watch", "retire_watch",
        "test_watch", "baseline_watch", "evaluate_once", "set_rules")},
}


def _top_level(summary: Any) -> dict[str, Any]:
    """The TOP-LEVEL keys of a JSON object summary, read value by value.

    The observer truncates a long summary (observer.py ``_truncate``), so the
    object may not parse whole: the keys read before the cut still count; a
    nested value never does.
    """
    if isinstance(summary, dict):
        return summary
    if not isinstance(summary, str) or not summary.lstrip().startswith("{"):
        return {}
    decoder = json.JSONDecoder()
    text, out, i = summary.strip(), {}, 1
    try:
        while True:
            while text[i] in " \n\t,":
                i += 1
            if text[i] == "}":
                break
            key, i = decoder.raw_decode(text, i)
            while text[i] in " \n\t:":
                i += 1
            value, i = decoder.raw_decode(text, i)
            out[str(key)] = value
    except (ValueError, IndexError):
        pass
    return out


def _receipt_project(method: str, args_summary: Any, result_summary: Any) -> str | None:
    """The project a pipeline receipt belongs to, from the producer's own
    identity field (``_RECEIPT_SCOPE``); ``None`` when the method is not a
    Room write or the field is absent."""
    where = _RECEIPT_SCOPE.get(method)
    if where is None:
        return None
    side, key = where
    value = _top_level(args_summary if side == "args" else result_summary).get(key)
    return value if isinstance(value, str) else None


def _count_unit(count: int, unit: str) -> str:
    """``1 DAY`` / ``2 DAYS`` -- HS-200-16.

    The Room read ``WAITING ON YOUR REVIEW · 1 DAYS`` where the arrival
    read ``1 DAY`` for the same row.
    """
    return f"{count} {unit}" if count == 1 else f"{count} {unit}S"


def _format_age(iso_str: str, now: datetime) -> str:
    """Format an ISO timestamp as a human-readable age token."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00").rstrip("Z"))
        delta = now - dt.replace(tzinfo=None)
        days = delta.days
        if days > 0:
            return _count_unit(days, "DAY")
        hours = delta.seconds // 3600
        if hours > 0:
            return _count_unit(hours, "HOUR")
        minutes = delta.seconds // 60
        if minutes > 0:
            return f"{minutes} MIN AGO"
        return "JUST NOW"
    except (ValueError, TypeError):
        return ""


# ── watch source identity (PHILO-17 U10) ─────────────────────────────

def _source_watch_identity(spec: dict[str, Any]) -> tuple[str, str, str]:
    """A source spec's stored identity: (connector_id, query_kind, query_json).

    The shape ``_arm_source_watch_in_txn`` writes; PHILO-17 U10 compares it to
    refuse a source the project already watches.
    """
    # Map provider spec IDs to connector_pack IDs
    # (the watch table's connector_id is "gh", not "github")
    raw_provider = spec.get("provider", {}).get("id", "native")
    connector_id = _PROVIDER_TO_CONNECTOR.get(raw_provider, raw_provider)
    # M-1 counsel: map singular subject kind to the plural
    # wire form GitHubWatchSource.snapshot demands.
    raw_kind = spec.get("subject", {}).get("kind", "")
    query_kind = _SUBJECT_TO_QUERY_KIND.get(raw_kind, raw_kind)
    # M-1 counsel: build the stored query in the shape
    # GitHubWatchSource expects: repository (singular string)
    # + query filters (state/base/search).  Mirror the shape
    # project_setup_service._native_test_read already uses.
    subject = spec.get("subject", {})
    scope = subject.get("scope", {})
    query_filters = dict(subject.get("query", {}))
    repos = scope.get("repositories", [])
    if repos:
        query_filters["repository"] = repos[0]
    # HS-166-03: flatten jira scope into the stored query
    # the way repos[0] is flattened for gh.
    jira_connection_ref = scope.get("connection_ref") or spec.get("provider", {}).get("connection_ref")
    if jira_connection_ref:
        query_filters["connection_ref"] = jira_connection_ref
    jira_projects = scope.get("projects", [])
    if jira_projects:
        query_filters["projects"] = list(jira_projects)
    jira_issue_types = scope.get("issue_types", [])
    if jira_issue_types:
        query_filters["issue_types"] = list(jira_issue_types)
    return connector_id, query_kind, json.dumps(query_filters, sort_keys=True, separators=(",", ":"))


# ── Room words (class constants of ProjectService before the split) ─────

#: PHILO-9-01 (F6): the Room's update list is bounded like its other sections.
_ROOM_UPDATES_CAP = 10

#: HS-200-13: the commitment states that are still owed.  `closed` is
#: what `FollowThroughService.complete` writes on done/dismiss;
#: `completed` is the People vocabulary the Room read already excluded.
_COMMITMENT_SETTLED = frozenset({"closed", "completed", "done", "dismissed"})

#: Betterment P3: the days a meeting's risks stay "this week".
_WEEK_DAYS = 7

# A code, not a sentence: the shape a refusal token is allowed to have.
_ASK_STOP_CODE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


# ── needs-you words and the snapshot reader ──────────────────────────

def snapshot_entities(snapshot: Any) -> list[dict[str, Any]]:
    """Extract entity list from a watch snapshot.

    The persisted snapshot is ``{"schema":1, "entities": {"526": {...}}}``
    (a dict keyed by entity ID, written by normalize_snapshot).  Some
    paths may pass the raw list from GitHubWatchSource.snapshot().
    Returns a flat list either way.
    """
    if isinstance(snapshot, list):
        return snapshot
    if isinstance(snapshot, dict):
        entities = snapshot.get("entities")
        if isinstance(entities, dict):
            return list(entities.values())
        if isinstance(entities, list):
            return entities
    return []

# Severity ordering for needsYou rows
_SEVERITY_ORDER = {"danger": 0, "warning": 1, "info": 2}

# Change-kind phrases: raw snake_case kind -> human phrase.
# The guard test asserts no raw kind (underscored) leaks into a phrase.
_CHANGE_KIND_PHRASES: dict[str, str] = {
    "project.created": "created",
    "project.updated": "updated",
    "project.archived": "archived",
    "project.restored": "restored",
    "project.resource.linked": "resource linked",
    "project.resource.unlinked": "resource unlinked",
    "watch.created": "watch created",
    "watch.snapshot": "snapshot refreshed",
    "watch.evaluated": "watch evaluated",
    "watch.error": "watch error",
    "item.created": "item added",
    "item.updated": "item updated",
    "item.transitioned": "item transitioned",
    "meeting.linked": "meeting linked",
    "meeting.unlinked": "meeting unlinked",
    "review.opened": "review opened",
    "review.accepted": "review accepted",
    "update.drafted": "update drafted",
    "update.published": "update published",
    "steward.ran": "steward ran",
}

# Plain-reason mapping for Watch errors (HS-169-04 D4 SOURCES)
_PLAIN_REASON_PATTERNS: list[tuple[str, str]] = [
    ("JQL parse error", "Jira rejected the query"),
    ("The value '", "Jira rejected the query"),
    ("does not exist for the field", "Jira rejected the query"),
    ("no local query adapter", "No local adapter for meeting activity yet"),
    ("lock timeout", "acli is busy"),
    ("connector_snapshot_adapter_unavailable", "No local adapter for meeting activity yet"),
    # PHILO-17 (needsyou): a provider CLI that is not signed in.
    ("gh auth login", "Not signed in"),
    ("not logged in", "Not signed in"),
    ("bad credentials", "Not signed in"),
    ("authentication required", "Not signed in"),
    ("acli auth login", "Not signed in"),
    ("unauthorized", "Not signed in"),
    ("executable file not found", "Tool not installed"),
    ("command not found", "Tool not installed"),
]

#: The plain words ``_plain_reason`` can give. A reason that is not one of
#: these is a raw error line (Needs you keeps it behind the row's detail).
PLAIN_REASONS: frozenset[str] = frozenset(
    {plain for _pattern, plain in _PLAIN_REASON_PATTERNS}
    | {"No local adapter for this source yet"}
)

def plain_reason(error: str | None) -> str | None:
    """Map a raw Watch error to plain words (ONCE in the service)."""
    if not error:
        return None
    lower = error.lower()
    for pattern, plain in _PLAIN_REASON_PATTERNS:
        if pattern.lower() in lower:
            return plain
    # First line of the error, no stack
    return error.split("\n")[0][:200]


# ── source token order ───────────────────────────────────────────────

# State severity for merging: cant_check > paused > live
_STATE_SEVERITY = {"cant_check": 0, "paused": 1, "live": 2}

# Template order for merged source tokens (the artboard's row order)
_TOKEN_ORDER_PREFIXES = [
    "OPEN PRS", "WAITING ON YOU", "CHECKS FAILING",
    "CI RED", "CI GREEN",
    "OVERDUE", "DUE THIS WEEK", "BLOCKED",
    "CLEAR",
]

def token_sort_key(token: str) -> int:
    """Sort key for template order. Known prefixes first; unknown last."""
    for i, prefix in enumerate(_TOKEN_ORDER_PREFIXES):
        if token.endswith(prefix) or token == prefix:
            return i
    return len(_TOKEN_ORDER_PREFIXES)


# ── item validation (DB-004) ─────────────────────────────────────────

def validate_severity(value: Any) -> Optional[str]:
    """Validate severity (nullable, closed vocabulary)."""
    if value is None or value == "":
        return None
    sev = str(value).strip().lower()
    if sev not in SEVERITY_LEVELS:
        raise ValidationError(
            f"severity must be one of {sorted(SEVERITY_LEVELS)} or null, "
            f"got {sev!r}",
            code="validation",
        )
    return sev

def validate_lifecycle(item_type: str, lifecycle: str) -> None:
    """Validate lifecycle against the item type's closed vocabulary."""
    valid = ITEM_LIFECYCLES.get(item_type)
    if valid is None:
        raise ValidationError(
            f"Unknown item_type: {item_type!r}",
            code="validation",
        )
    if lifecycle not in valid:
        raise ValidationError(
            f"lifecycle {lifecycle!r} is not valid for {item_type}; "
            f"must be one of {list(valid)}",
            code="validation",
        )

def validate_optional_ref(value: Any, field_name: str) -> Optional[str]:
    """Validate an optional qualified ref through holdspeak.refs."""
    if value is None or value == "":
        return None
    ref_str = str(value).strip()
    try:
        parse_ref(ref_str)
    except Exception as exc:
        raise ValidationError(
            f"{field_name} is not a valid qualified ref: {ref_str!r}",
            code="validation",
        ) from exc
    return ref_str

def validate_details(item_type: str, details: dict[str, Any]) -> str:
    """Validate details_json against the closed per-type schema (DB-004).

    Returns the JSON string to persist.  Unknown fields or wrong types
    raise a typed validation error.
    """
    schema = _DETAILS_SCHEMAS.get(item_type)
    if schema is None:
        raise ValidationError(
            f"No details schema for item_type {item_type!r}",
            code="validation",
        )

    if not isinstance(details, dict):
        raise ValidationError(
            "details must be a JSON object",
            code="validation",
        )

    # Refuse unknown fields
    unknown = set(details.keys()) - set(schema.keys())
    if unknown:
        raise ValidationError(
            f"Unknown fields in details for {item_type}: {sorted(unknown)}",
            code="validation",
        )

    # Validate each field
    clean: dict[str, Any] = {}
    for field_name, (required, validator) in schema.items():
        value = details.get(field_name)
        if value is None and field_name not in details:
            if required:
                raise ValidationError(
                    f"details.{field_name} is required for {item_type}",
                    code="validation",
                )
            continue  # omitted optional field
        if not validator(value):
            raise ValidationError(
                f"details.{field_name} has invalid type/value for {item_type}",
                code="validation",
            )
        clean[field_name] = value

    return json.dumps(clean, ensure_ascii=False)


__all__ = [
    "_ABSENT_SECTION",
    "_ASK_STOP_CODE",
    "aware_iso",
    "_CHANGE_KIND_PHRASES",
    "_COMMITMENT_SETTLED",
    "_count_unit",
    "_DETAILS_SCHEMAS",
    "_format_age",
    "_is_number_or_none",
    "_is_str",
    "_is_str_or_none",
    "ITEM_DEFAULT_LIFECYCLE",
    "ITEM_LIFECYCLES",
    "ITEM_TYPES",
    "local_now",
    "local_week_bounds",
    "localize",
    "plain_reason",
    "_PLAIN_REASON_PATTERNS",
    "PLAIN_REASONS",
    "_POSTURE_MAX",
    "_POSTURE_REASON_MAX",
    "PROJECT_LIFECYCLES",
    "PROVENANCE_KINDS",
    "_PROVIDER_TO_CONNECTOR",
    "_receipt_project",
    "_RECEIPT_SCOPE",
    "ROOM_CHANGES_CAP",
    "ROOM_FOCUS_CAP",
    "_ROOM_UPDATES_CAP",
    "ROOM_WRITE_METHODS",
    "_SERVICE_OBSERVED_OPERATIONS",
    "_SERVICE_OBSERVED_PREFIXES",
    "SEVERITY_LEVELS",
    "_SEVERITY_ORDER",
    "SEVERITY_RANK",
    "_SLUG_MAX",
    "snapshot_entities",
    "_source_watch_identity",
    "_STATE_SEVERITY",
    "_SUBJECT_TO_QUERY_KIND",
    "_TOKEN_ORDER_PREFIXES",
    "token_sort_key",
    "_top_level",
    "utc_z",
    "validate_details",
    "validate_lifecycle",
    "validate_optional_ref",
    "validate_severity",
    "_wall",
    "_WEEK_DAYS",
]
