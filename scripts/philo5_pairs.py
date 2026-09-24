"""Pair the named PHILO-5-03 observations.

The pair input is a small index of retained observation *paths*::

    {"pairs": [{"pair_id": "case...", "op": "/tmp/op/observation.json",
                "browser": "/tmp/browser/observation.json"}]}

``build_pairs`` is the public API used by the evidence job and the command
line wrapper.  This module reads only the rig's named observation slots.  A
JSON-RPC envelope, a DOM snapshot, or an unnamed dictionary is never a
durable read.  Each family has its own projection and identity checks because
the generated ids, clocks, model prose, and receipt timestamps have different
meanings in different families.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ENGINE_MODES = frozenset({"real", "replayed", "none"})
VERDICTS = frozenset({"pass", "fail", "blocked"})
LAN_HOST = "192.168.1.43"

# These are behavioural families, not a general-purpose comparison language.
# The atlas uses 18 pair rows, with a few rows sharing one projection.
PAIR_FAMILIES: dict[str, dict[str, Any]] = {
    "closure.s1_import_complete": {"kind": "import"},
    "closure.s2_summary_with_host": {"kind": "summary"},
    "closure.s3_same_summary_after_restart": {"kind": "restart"},
    "closure.s4_decision_recorded": {"kind": "decision"},
    "a1.decision_create": {"kind": "decision_refusal", "refusal": "invalid decision status"},
    "a3.brief_next_day": {"kind": "next_day"},
    "closure.s5_next_day_brief": {"kind": "next_day"},
    "closure.s5_next_day_brief_breakage": {"kind": "breakage"},
    "philo404.arrival_triage": {"kind": "triage"},
    "j11.thought_keep": {"kind": "thought"},
    "summary.no_transcript": {"kind": "summary_refusal", "refusal": "Meeting has no transcript"},
    "summary.no_assignment": {"kind": "summary_refusal", "refusal": "route_unavailable"},
    "brief.same_day": {"kind": "same_day"},
    "shelf.acknowledged": {"kind": "shelf", "state": "acknowledged"},
    "shelf.deferred": {"kind": "shelf", "state": "deferred"},
    "shelf.refused": {"kind": "shelf_refusal", "refusal": "unknown shelf state"},
}

_PAIR_PREFIXES: tuple[tuple[str, str], ...] = (
    ("case.closure.chain.s1_", "closure.s1_import_complete"),
    ("case.closure.chain.s2_", "closure.s2_summary_with_host"),
    ("case.closure.chain.s3_", "closure.s3_same_summary_after_restart"),
    ("case.closure.chain.s4_", "closure.s4_decision_recorded"),
    ("case.closure.chain.s5_", "closure.s5_next_day_brief"),
    ("case.a1.decision_face_create", "a1.decision_create"),
    ("case.a3.brief_next_day", "a3.brief_next_day"),
    ("case.philo404", "philo404.arrival_triage"),
    ("case.j11.thought_keep", "j11.thought_keep"),
)


def _family_for(pair_id: str, explicit: str | None = None) -> str | None:
    if explicit:
        return explicit if explicit in PAIR_FAMILIES else None
    value = pair_id.lower()
    for prefix, family in _PAIR_PREFIXES:
        if value.startswith(prefix):
            if family == "closure.s5_next_day_brief" and "with_breakage" in value:
                return "closure.s5_next_day_brief_breakage"
            return family
    if "no_transcript" in value:
        return "summary.no_transcript"
    if "no_assignment" in value:
        return "summary.no_assignment"
    if "route_intelligence_run.refusal" in value:
        return "summary.no_transcript"
    if "same_day" in value:
        return "brief.same_day"
    if "shelf" in value and ("acknowledged" in value or "ack" in value):
        return "shelf.acknowledged"
    if "shelf" in value and "defer" in value:
        return "shelf.deferred"
    if "shelf" in value and ("refus" in value or "invalid" in value):
        return "shelf.refused"
    return None


def _as_str(value: Any) -> str | None:
    return str(value) if value is not None else None


def _engine_mode(observation: Mapping[str, Any], entry: Mapping[str, Any]) -> str | None:
    if entry.get("engine_mode") is not None:
        return str(entry["engine_mode"])
    provenance = observation.get("provenance")
    if isinstance(provenance, Mapping) and provenance.get("engine_mode") is not None:
        return str(provenance["engine_mode"])
    return None


def _load_observation(entry: Any) -> tuple[dict[str, Any] | None, str | None]:
    """Load an observation from a retained path or an explicit inline value."""
    if isinstance(entry, Mapping):
        inline = entry.get("observation")
        if isinstance(inline, Mapping):
            return dict(inline), _as_str(entry.get("observation_path") or entry.get("path"))
        path = entry.get("observation_path") or entry.get("path")
        if path:
            try:
                return json.loads(Path(str(path)).read_text(encoding="utf-8")), str(path)
            except (OSError, json.JSONDecodeError):
                return None, str(path)
        # Inline observations are useful for callers, but only a complete
        # observation shape is accepted. An arbitrary domain dictionary is not.
        if any(key in entry for key in ("setup", "before", "after", "trigger", "provenance")):
            return dict(entry), None
        return None, None
    if isinstance(entry, (str, Path)):
        path = str(entry)
        try:
            return json.loads(Path(path).read_text(encoding="utf-8")), path
        except (OSError, json.JSONDecodeError):
            return None, path
    return None, None


def _path_get(value: Any, path: str) -> tuple[bool, Any]:
    """Small explicit path reader for dot and JSON-pointer paths."""
    if not isinstance(path, str):
        return False, None
    parts = [part for part in path.split("/") if part] if path.startswith("/") else [part for part in path.split(".") if part]
    current = value
    for part in parts:
        if isinstance(current, Mapping) and part in current:
            current = current[part]
        elif isinstance(current, Sequence) and not isinstance(current, (str, bytes)) and part.isdigit():
            index = int(part)
            if index >= len(current):
                return False, None
            current = current[index]
        else:
            return False, None
    return True, current


def _first(value: Any, *paths: str) -> Any:
    for path in paths:
        found, result = _path_get(value, path)
        if found:
            return result
    return None


def _record_payload(record: Mapping[str, Any], transport: str) -> Any:
    """Decode only fields emitted by graph_walk's actual record producers."""
    if transport == "op":
        if "domain_response" in record:
            return record.get("domain_response")
        if "response" in record:
            return record.get("response")
        return None
    if "payload" in record:
        return record.get("payload")
    if "response" in record:
        return record.get("response")
    if "body" in record:
        return record.get("body")
    return None


def _record_refusal(record: Mapping[str, Any], transport: str) -> Any:
    refusal = record.get("refusal") or record.get("named_refusal") or record.get("domain_refusal")
    if refusal is not None:
        return refusal
    payload = _record_payload(record, transport)
    status = record.get("status")
    if isinstance(status, int) and status >= 400:
        return payload
    return None


def _make_record(record: Any, transport: str, stage: str, source: str) -> dict[str, Any] | None:
    if not isinstance(record, Mapping):
        return None
    # Operation records must retain their canonical name. API records must
    # retain their route. This rejects unnamed arbitrary dictionaries.
    name = record.get("name") or record.get("operation") or record.get("op")
    path = record.get("path")
    if transport == "op" and not isinstance(name, str):
        return None
    if transport == "api" and not isinstance(path, str):
        return None
    payload = _record_payload(record, transport)
    refusal = _record_refusal(record, transport)
    if payload is None and refusal is None:
        return None
    return {
        "transport": transport, "stage": stage, "source": source,
        "name": str(name) if name is not None else None,
        "method": str(record.get("method")) if record.get("method") is not None else None,
        "path": path, "payload": payload, "refusal": refusal,
        "status": record.get("status"), "record": dict(record),
    }


def _collect_records(observation: Mapping[str, Any], transport: str) -> list[dict[str, Any]]:
    """Read the rig's fixed slots and retain stage/name/path metadata."""
    rows: list[dict[str, Any]] = []

    def add(value: Any, stage: str, source: str) -> None:
        row = _make_record(value, transport, stage, source)
        if row is not None:
            rows.append(row)

    for slot in ("setup", "preconditions"):
        values = observation.get(slot)
        if isinstance(values, list):
            for index, value in enumerate(values):
                if isinstance(value, Mapping) and value.get("kind") == transport:
                    add(value, f"{slot}[{index}]", f"{slot}[{index}]")
                if isinstance(value, Mapping) and transport == "api":
                    wait = value.get("completion_wait")
                    if isinstance(wait, Mapping) and "payload" in wait and isinstance(wait.get("path"), str):
                        add({"method": wait.get("method"), "path": wait.get("path"),
                             "status": wait.get("status"), "payload": wait.get("payload")},
                            f"{slot}[{index}].completion_wait", f"{slot}[{index}].completion_wait")
    trigger = observation.get("trigger")
    if isinstance(trigger, Mapping) and trigger.get("kind") == transport:
        add(trigger, "trigger", "trigger")
    if transport == "api" and isinstance(trigger, Mapping):
        # Fixture triggers retain the real HTTP producer in ``route`` and the
        # final durable read in ``completion_wait``. Both are named rig slots;
        # the fixture path itself is not an API route.
        route = trigger.get("route")
        if isinstance(route, Mapping) and isinstance(route.get("path"), str):
            add({"method": route.get("method"), "path": route.get("path"),
                 "status": trigger.get("status"), "payload": trigger.get("response")},
                "trigger", "trigger.route")
        wait = trigger.get("completion_wait")
        if isinstance(wait, Mapping) and isinstance(wait.get("path"), str) and "payload" in wait:
            add({"method": wait.get("method"), "path": wait.get("path"),
                 "status": wait.get("status"), "payload": wait.get("payload")},
                "after", "trigger.completion_wait")

    # ``initial_feedback`` and ``terminal_outcome`` contain progress or
    # protocol metadata. They are not final durable reads and must not win
    # over the named ``after`` slots when a family takes its last projection.
    for label in ("before", "after"):
        snapshot = observation.get(label)
        if not isinstance(snapshot, Mapping):
            continue
        if transport == "op":
            for key in ("op", "operation_trigger"):
                value = snapshot.get(key)
                if isinstance(value, Mapping):
                    add(value, label, f"{label}.{key}")
            values = snapshot.get("op_reads")
            if isinstance(values, list):
                for index, value in enumerate(values):
                    add(value, label, f"{label}.op_reads[{index}]")
            elif isinstance(values, Mapping):
                add(values, label, f"{label}.op_reads")
        else:
            values = snapshot.get("api_reads")
            if isinstance(values, list):
                for index, value in enumerate(values):
                    add(value, label, f"{label}.api_reads[{index}]")
            elif isinstance(values, Mapping):
                add(values, label, f"{label}.api_reads")
            protocol = snapshot.get("protocol")
            if isinstance(protocol, Mapping) and isinstance(protocol.get("path"), str):
                add({"method": protocol.get("method"), "path": protocol.get("path"),
                     "status": protocol.get("status"), "payload": protocol.get("payload")},
                    label, f"{label}.protocol")

    # A browser refusal has no durable record in trigger itself. The rig keeps
    # the trigger's own HTTP response in this explicit slot; route matching
    # prevents it becoming a durable read.
    if transport == "api":
        for key in ("trigger_response", "trigger_response_capture"):
            value = observation.get(key)
            if isinstance(value, Mapping) and isinstance(value.get("path"), str):
                add(value, "trigger", key)
            value = (observation.get("after") or {}).get(key) if isinstance(observation.get("after"), Mapping) else None
            if isinstance(value, Mapping) and isinstance(value.get("path"), str):
                add(value, "trigger", f"after.{key}")
    return rows


def _family_records(records: Sequence[Mapping[str, Any]], family: str, *, final_only: bool = False) -> list[dict[str, Any]]:
    kind = PAIR_FAMILIES[family]["kind"]
    selected: list[dict[str, Any]] = []
    for row in records:
        stage = str(row.get("stage") or "")
        if final_only and not stage.startswith("after"):
            continue
        name = str(row.get("name") or "")
        method = str(row.get("method") or "").upper()
        path = str(row.get("path") or "")
        trigger_capture = stage == "trigger" and str(row.get("source") or "") in {
            "trigger_response", "after.trigger_response", "trigger_response_capture", "after.trigger_response_capture"
        } and not (kind == "thought" and row.get("refusal") is None)
        # A same-day browser walk records the generate response in the
        # trigger slot.  It is a producer stage, not an unscoped refusal
        # capture, and must remain available for the identity chain.
        trigger_same_day_producer = (
            kind == "same_day" and stage == "trigger"
            and (name == "brief.generate" or (method == "POST" and path == "/api/brief/generate"))
        )
        producer = (
            (kind in {"import", "summary", "restart", "summary_refusal"} and name in {"meeting.import", "meeting.summary.run"})
            or (kind in {"decision", "decision_refusal"} and name in {"decision.create", "decision.update"})
            or (kind in {"next_day", "breakage", "same_day", "triage", "shelf", "shelf_refusal"} and name == "brief.generate")
            or (kind == "thought" and name in {"thought.create", "thought.save"})
        )
        if not final_only and trigger_same_day_producer:
            selected.append(dict(row))
            continue
        if not final_only and producer and (not trigger_capture or trigger_same_day_producer):
            selected.append(dict(row))
            continue
        if not final_only and not trigger_capture and kind in {"import", "summary", "restart", "summary_refusal"} and method == "POST" and path == "/api/meetings/import":
            selected.append(dict(row))
            continue
        if not final_only and not trigger_capture and kind in {"decision", "decision_refusal"} and method in {"POST", "PUT", "PATCH"} and path.startswith("/api/decisions"):
            selected.append(dict(row))
            continue
        if not final_only and not trigger_capture and kind in {"next_day", "breakage", "same_day", "triage", "shelf", "shelf_refusal"} and method == "POST" and path == "/api/brief/generate":
            selected.append(dict(row))
            continue
        if not final_only and not trigger_capture and kind == "thought" and method in {"POST", "PATCH"} and path.startswith("/api/thoughts"):
            selected.append(dict(row))
            continue
        if kind in {"import", "summary", "restart", "summary_refusal"}:
            if name == "meeting.read" or (method == "GET" and re.fullmatch(r"/api/meetings/[^/]+", path)):
                selected.append(dict(row))
        elif kind in {"decision", "decision_refusal"}:
            if name == "decision.read" or (method == "GET" and re.fullmatch(r"/api/decisions/[^/]+", path)):
                selected.append(dict(row))
            if kind == "decision_refusal" and (name == "decision.list" or (method == "GET" and path == "/api/decisions")):
                selected.append(dict(row))
        elif kind in {"next_day", "breakage", "same_day", "triage", "shelf", "shelf_refusal"}:
            if name == "brief.latest" or (method == "GET" and path == "/api/brief/latest"):
                selected.append(dict(row))
        elif kind == "thought":
            if name in {"thought.read", "thought.workbench.read", "thought.list"} or (
                    method == "GET" and (path.startswith("/api/thoughts") or path.startswith("/api/notes"))):
                selected.append(dict(row))
    return selected


def _shelf_records(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in records if str(row.get("name") or "") in {"brief.shelf.read", "shelf.read"}
            or (str(row.get("method") or "").upper() == "GET" and row.get("path") == "/api/brief/shelf")]


def _refusal_code(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key in ("code", "reason_code", "refusal_code"):
            if isinstance(value.get(key), str) and value[key]:
                return value[key]
        error = value.get("error")
        if isinstance(error, Mapping):
            return _refusal_code(error)
        if isinstance(error, str) and error:
            return error
        message = value.get("message") or value.get("detail")
        return str(message) if message else None
    if isinstance(value, str) and value:
        return value
    return None


def _refusal_text(value: Any) -> str:
    if isinstance(value, Mapping):
        parts: list[str] = []
        for key in ("code", "reason_code", "refusal_code", "error", "message", "detail"):
            child = value.get(key)
            if isinstance(child, Mapping):
                parts.append(_refusal_text(child))
            elif child not in (None, ""):
                parts.append(str(child))
        return " ".join(parts)
    return str(value or "")


def _refusals(records: Sequence[Mapping[str, Any]]) -> list[str]:
    values = {_refusal_code(row.get("refusal")) for row in records}
    return sorted(value for value in values if value)


def _entity_id(payload: Any, entity: str) -> str | None:
    if not isinstance(payload, Mapping):
        return None
    direct = payload.get("id")
    if direct not in (None, ""):
        return str(direct)
    for key in (f"{entity}_id", "meeting_id" if entity == "meeting" else ""):
        if key and payload.get(key) not in (None, ""):
            return str(payload[key])
    child = payload.get(entity)
    if isinstance(child, Mapping) and child.get("id") not in (None, ""):
        return str(child["id"])
    if entity == "thought":
        child = payload.get("working_note")
        if isinstance(child, Mapping) and child.get("thought_id") not in (None, ""):
            return str(child["thought_id"])
    return None


def _meeting_projection(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {}
    intel = payload.get("intel") if isinstance(payload.get("intel"), Mapping) else {}
    status = payload.get("transcription_status")
    duration = payload.get("duration")
    segments = payload.get("segments")
    return {
        "title": payload.get("title"), "transcription_status": status,
        "duration": duration, "segments_count": len(segments) if isinstance(segments, list) else None,
        "summary_present": bool((intel.get("summary") if intel else None) or payload.get("summary")),
        "summary_state": _first(payload, "intel_status.state", "intel_job.status"),
        "receipt": _receipt_projection(payload.get("run_receipt")),
    }


def _meeting_refusal_projection(payload: Any) -> dict[str, Any]:
    """Durable no-transcript state without live computed duration fields."""
    if not isinstance(payload, Mapping):
        return {}
    intel = payload.get("intel") if isinstance(payload.get("intel"), Mapping) else {}
    job = payload.get("intel_job") if isinstance(payload.get("intel_job"), Mapping) else {}
    return {
        "id": _entity_id(payload, "meeting"),
        "transcription_status": payload.get("transcription_status"),
        "transcription_status_detail": payload.get("transcription_status_detail"),
        "segments": payload.get("segments"),
        "summary": intel.get("summary") if intel else payload.get("summary"),
        "summary_state": _first(payload, "intel_status.state", "intel_job.status", "intel_job.state"),
        "job": {key: job.get(key) for key in ("id", "job_id", "status", "state", "code", "error")
                if job.get(key) is not None},
        "receipt": _receipt_projection(payload.get("run_receipt")),
    }


def _meeting_identity_projection(payload: Any) -> dict[str, Any]:
    """Stable transcript identity used by a route refusal before/after."""
    if not isinstance(payload, Mapping):
        return {}
    segments = payload.get("segments")
    return {"id": _entity_id(payload, "meeting"),
            "transcription_status": payload.get("transcription_status"),
            "segments": segments}


def _meeting_assignment_outcome_projection(payload: Any) -> dict[str, Any]:
    """Route refusal outcome, excluding generated job/receipt identities."""
    if not isinstance(payload, Mapping):
        return {}
    job = payload.get("intel_job") if isinstance(payload.get("intel_job"), Mapping) else {}
    receipt = payload.get("run_receipt") if isinstance(payload.get("run_receipt"), Mapping) else {}
    meeting_id = _entity_id(payload, "meeting")
    return {
        "meeting_id_present": meeting_id is not None,
        "job_status": job.get("status"), "job_error": job.get("last_error") or job.get("error"),
        "receipt_present": bool(receipt), "receipt_outcome": receipt.get("outcome"),
        "receipt_meeting_matches": bool(receipt) and receipt.get("meeting_id") == meeting_id,
        "receipt_attempts": len(receipt.get("attempts")) if isinstance(receipt.get("attempts"), list) else None,
    }


def _assignment_refusal_checks(payload: Any, label: str) -> list[dict[str, Any]]:
    """Require the route refusal's failed job and empty receipt attempts."""
    if not isinstance(payload, Mapping):
        return [_check(f"{label}.assignment_refusal_state", "blocked", "final meeting read is absent")]
    status = _first(payload, "intel_status.state")
    job = payload.get("intel_job") if isinstance(payload.get("intel_job"), Mapping) else None
    receipt = payload.get("run_receipt") if isinstance(payload.get("run_receipt"), Mapping) else None
    checks: list[dict[str, Any]] = []
    checks.append(_check(f"{label}.assignment_status", "pass" if status == "error" else ("fail" if status else "blocked"),
                         "summary assignment ended in error" if status == "error" else "summary assignment error state is absent or wrong"))
    job_status = job.get("status") if isinstance(job, Mapping) else None
    checks.append(_check(f"{label}.assignment_job", "pass" if job_status == "failed" else ("fail" if job_status else "blocked"),
                         "summary refusal job is failed" if job_status == "failed" else "summary refusal job is absent or not failed"))
    if not isinstance(receipt, Mapping):
        checks.append(_check(f"{label}.assignment_receipt", "blocked", "summary refusal receipt is absent"))
        checks.append(_check(f"{label}.assignment_receipt_attempts", "blocked", "summary refusal receipt attempts are absent"))
        return checks
    outcome = receipt.get("outcome")
    checks.append(_check(f"{label}.assignment_receipt", "pass" if outcome == "refused" else ("fail" if outcome else "blocked"),
                         "summary refusal receipt is refused" if outcome == "refused" else "summary refusal receipt outcome is absent or wrong"))
    attempts = receipt.get("attempts")
    checks.append(_check(f"{label}.assignment_receipt_attempts", "pass" if attempts == [] else ("fail" if attempts is not None else "blocked"),
                         "summary refusal receipt has no provider attempts" if attempts == [] else "summary refusal receipt attempts are absent or nonempty"))
    meeting_id = _entity_id(payload, "meeting")
    relation_ok = receipt.get("meeting_id") == meeting_id and meeting_id not in (None, "")
    checks.append(_check(f"{label}.assignment_receipt_identity", "pass" if relation_ok else "fail",
                         "summary refusal receipt retains meeting identity" if relation_ok else "summary refusal receipt meeting identity is absent or changed"))
    return checks


def _meeting_cross_refusal_projection(payload: Any) -> dict[str, Any]:
    """Compare refusal state across hubs without generated meeting identity."""
    projection = _meeting_refusal_projection(payload)
    if not projection:
        return projection
    projection = dict(projection)
    projection["meeting_id_present"] = projection.pop("id") not in (None, "")
    return projection


def _receipt_projection(receipt: Any) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        return {}
    attempts = receipt.get("attempts")
    host = None
    if isinstance(attempts, list) and attempts and isinstance(attempts[0], Mapping):
        host = attempts[0].get("host")
    host = host or receipt.get("host")
    return {
        "present": True, "host": host, "outcome": receipt.get("outcome"),
        "meeting_id": receipt.get("meeting_id"),
        "job_id": receipt.get("job_id"),
        "meeting_id_present": receipt.get("meeting_id") not in (None, ""),
        "job_id_present": receipt.get("job_id") not in (None, ""),
    }


def _decision_projection(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {}
    if isinstance(payload.get("decision"), Mapping):
        payload = payload["decision"]
    return {key: payload.get(key) for key in ("title", "status", "decision_markdown", "context_markdown")}


def _decision_created_at(payload: Any) -> str | None:
    value = _first(payload, "created_at", "decision.created_at")
    return value if isinstance(value, str) and value else None


def _brief_payload(payload: Any) -> Mapping[str, Any] | None:
    if not isinstance(payload, Mapping):
        return None
    child = payload.get("brief")
    return child if isinstance(child, Mapping) else payload


def _brief_projection(payload: Any) -> dict[str, Any]:
    brief = _brief_payload(payload)
    if brief is None:
        return {}
    sections = brief.get("sections")
    decisions = sections.get("decisions") if isinstance(sections, Mapping) else None
    titles: list[str] = []
    source_refs: list[str] = []
    if isinstance(decisions, list):
        for item in decisions:
            if isinstance(item, Mapping):
                title = item.get("title") or item.get("text") or item.get("headline")
                if isinstance(title, str):
                    titles.append(title)
                source = item.get("source_ref")
                if isinstance(source, str):
                    source_refs.append(source)
    return {"headline": brief.get("headline"), "decision_titles": titles,
            "decision_source_refs": source_refs,
            "decision_count": len(decisions) if isinstance(decisions, list) else None}


def _thought_projection(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {}
    thought = payload.get("thought") if isinstance(payload.get("thought"), Mapping) else payload
    if isinstance(thought.get("items"), list) and thought["items"] and isinstance(thought["items"][0], Mapping):
        thought = thought["items"][0]
    working = thought.get("working_note") if isinstance(thought.get("working_note"), Mapping) else {}
    body = _first(working, "body_markdown", "body", "text")
    last_modified = _first(working, "last_modified", "last_modified_at")
    return {
        "id": _entity_id(thought, "thought") or _entity_id(payload, "thought"), "body": body,
        "note_id": _first(thought, "working_note.id"),
        "raw_id": thought.get("raw_id"), "raw_sha256": thought.get("raw_sha256"),
        "working_revision": thought.get("working_revision"),
        "aggregate_revision": thought.get("aggregate_revision"),
        "last_modified": last_modified,
        "cursor_thought_id": _first(payload, "cursor.thought_id", "workspace_cursor.thought_id",
                                     "workbench.workspace_cursor.thought_id", "thought_id"),
        "cursor_aggregate_revision": _first(payload, "cursor.aggregate_revision", "workspace_cursor.aggregate_revision",
                                             "workbench.workspace_cursor.aggregate_revision"),
    }


def _shelf_projection(payload: Any) -> dict[str, str]:
    if not isinstance(payload, Mapping):
        return {}
    shelf = payload.get("shelf")
    if isinstance(shelf, Mapping):
        payload = shelf
    # The durable service shape is {brief_id, shelf: {item_id: state}}. A
    # direct state map is accepted only when every value is a known state.
    return {str(key): str(value) for key, value in payload.items()
            if isinstance(value, str) and value in {"acknowledged", "deferred", "Ack", "Defer"}}


def _shelf_brief_id(payload: Any) -> str | None:
    if not isinstance(payload, Mapping) or payload.get("brief_id") in (None, ""):
        return None
    return str(payload["brief_id"])


def _shelf_state_kind(value: Any) -> str:
    state = str(value or "").lower()
    if state in {"ack", "acknowledged"}:
        return "acknowledged"
    if state in {"defer", "deferred"}:
        return "deferred"
    return state


def _brief_item_ids(payload: Any) -> set[str]:
    brief = _brief_payload(payload)
    if brief is None or not isinstance(brief.get("sections"), Mapping):
        return set()
    ids: set[str] = set()
    sections = brief["sections"]
    for section_name, section in sections.items():
        if str(section_name).lower() in {"this_week", "this week", "hidden", "raw"}:
            continue
        if not isinstance(section, list):
            continue
        for item in section:
            if isinstance(item, Mapping) and item.get("id") not in (None, ""):
                ids.add(str(item["id"]))
    return ids


def _brief_items(payload: Any) -> dict[str, Mapping[str, Any]]:
    """Return only visible final brief items eligible for shelf membership."""
    brief = _brief_payload(payload)
    if brief is None or not isinstance(brief.get("sections"), Mapping):
        return {}
    result: dict[str, Mapping[str, Any]] = {}
    for section_name, section in brief["sections"].items():
        if str(section_name).lower() in {"this_week", "this week", "hidden", "raw"}:
            continue
        if not isinstance(section, list):
            continue
        for item in section:
            if isinstance(item, Mapping) and item.get("id") not in (None, ""):
                result[str(item["id"])] = item
    return result


def _breakage_text_detail_projection(payload: Any) -> list[dict[str, Any]] | None:
    """Project every final ``broke`` row while retaining duplicate events.

    Breakage source ids are generated independently by each hub.  The event's
    text and detail are the durable observation, so compare that ordered list
    across transports.  Sorting only makes producer order deterministic; it
    never turns the rows into a set or removes duplicate failures.
    """
    brief = _brief_payload(payload)
    sections = brief.get("sections") if isinstance(brief, Mapping) else None
    rows = sections.get("broke") if isinstance(sections, Mapping) else None
    if not isinstance(rows, list):
        return None
    projection = [
        {"text": item.get("text"), "detail": item.get("detail")}
        for item in rows
        if isinstance(item, Mapping)
    ]
    if not projection or any(row["text"] in (None, "") or row["detail"] in (None, "")
                             for row in projection):
        return None
    return sorted(projection, key=lambda row: (str(row["text"]), str(row["detail"])))


def _shelf_semantic_projection(brief_payload: Any, shelf_payload: Any) -> dict[str, str] | None:
    """Map logical source/text to state so generated item ids can differ."""
    items = _brief_items(brief_payload)
    shelf = _shelf_projection(shelf_payload)
    if not shelf or not set(shelf).issubset(items):
        return None
    projection: dict[str, str] = {}
    for item_id, state in shelf.items():
        item = items[item_id]
        text = item.get("text") or item.get("title") or item.get("headline")
        source = item.get("source_ref")
        # Generated source ids differ across independent hubs. Prefer the
        # durable user-facing row text for the cross-transport key, while
        # retaining source_ref as the within-run scope evidence.
        logical = text if isinstance(text, str) and text else source
        if not isinstance(logical, str) or not logical:
            return None
        projection[logical] = _shelf_state_kind(state)
    return projection if len(projection) == len(shelf) else None


def _shelf_refusal_cross_projection(records: Sequence[Mapping[str, Any]], family: str) -> dict[str, str] | None:
    """Compare refusal shelf state by logical row text, never generated ids."""
    shelf_rows = [row for row in _shelf_records(records) if str(row.get("stage", "")).startswith("after")]
    if not shelf_rows:
        return None
    brief = _final_brief_payload(_family_records(records, family))
    if brief is None:
        return None
    shelf = _shelf_projection(shelf_rows[-1].get("payload"))
    if not shelf:
        return {}
    return _shelf_semantic_projection(brief, shelf_rows[-1].get("payload"))


def _records_payloads(records: Sequence[Mapping[str, Any]]) -> list[Any]:
    return [row.get("payload") for row in records if row.get("payload") is not None]


def _target_ids(records: Sequence[Mapping[str, Any]], entity: str) -> list[str]:
    return [value for value in (_entity_id(row.get("payload"), entity) for row in records) if value]


def _check(name: str, status: str, detail: str, **values: Any) -> dict[str, Any]:
    row = {"name": name, "status": status, "detail": detail}
    row.update({key: value for key, value in values.items() if value is not None})
    return row


def _require_records(name: str, records: Sequence[Mapping[str, Any]], *, minimum: int = 1) -> dict[str, Any]:
    if len(records) < minimum:
        return _check(name, "blocked", f"required named durable reads: {minimum}; retained {len(records)}")
    return _check(name, "pass", f"retained {len(records)} named durable read(s)")


def _same_within(records: Sequence[Mapping[str, Any]], values: Sequence[Any], label: str,
                 *, minimum: int = 2) -> dict[str, Any]:
    usable = [value for value in values if value not in (None, "")]
    stages = {str(row.get("stage")) for row, value in zip(records, values) if value not in (None, "")}
    if len(usable) < minimum or len(stages) < minimum:
        return _check(label, "blocked", f"{label} needs {minimum} producer/read stages")
    stable = len(set(map(str, usable))) == 1
    return _check(label, "pass" if stable else "fail",
                  f"{label} is {'stable' if stable else 'different'} within the run", values=list(usable))


def _identity_check(records: Sequence[Mapping[str, Any]], entity: str, *, created: bool = False,
                    label: str = "identity") -> list[dict[str, Any]]:
    ids = [_entity_id(row.get("payload"), entity) for row in records]
    checks = [_same_within(records, ids, label)]
    if created:
        created_paths = ("created_at", "decision.created_at") if entity == "decision" else ("created_at",)
        created_values = [_first(row.get("payload"), *created_paths) for row in records]
        present = [value for value in created_values if isinstance(value, str) and value]
        if len(present) < 2:
            checks.append(_check("created_at_present", "blocked", "created_at is required in producer and read stages"))
        else:
            checks.append(_check("created_at_stable_within_run", "pass" if len(set(present)) == 1 else "fail",
                                 "created_at is stable across producer/read stages", values=present))
    return checks


def _compare_exact(name: str, left: Any, right: Any, *, required: bool = True) -> dict[str, Any]:
    if left is None or right is None or (required and (left == {} or right == {})):
        return _check(name, "blocked", f"required projection {name} is absent")
    return _check(name, "pass" if left == right else "fail",
                  f"{name} {'matches' if left == right else 'differs'}", op=left, browser=right)


def _restart_detail(observation: Mapping[str, Any]) -> Mapping[str, Any] | None:
    record = observation.get("restart")
    if isinstance(record, Mapping):
        return record
    for slot in ("after", "trigger"):
        value = observation.get(slot)
        if isinstance(value, Mapping) and isinstance(value.get("restart"), Mapping):
            return value["restart"]
    trigger = observation.get("trigger")
    if isinstance(trigger, Mapping) and trigger.get("kind") == "cli":
        return trigger
    provenance = observation.get("provenance")
    if isinstance(provenance, Mapping) and isinstance(provenance.get("restarts"), list):
        for restart in reversed(provenance["restarts"]):
            if isinstance(restart, Mapping) and restart.get("action") == "restart_hub":
                return restart
    return None


def _restart_checks(observation: Mapping[str, Any], label: str) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    detail = _restart_detail(observation)
    if not isinstance(detail, Mapping):
        return [_check(f"restart.{label}", "blocked", "real restart detail is absent")]
    for key in ("summary_retained", "receipt_retained", "meeting_identity_retained"):
        value = detail.get(key)
        checks.append(_check(f"restart.{label}.{key}", "pass" if value is True else ("fail" if value is False else "blocked"),
                             f"restart {key} is retained" if value is True else f"restart {key} is absent or false"))
    before, after = detail.get("meeting_before"), detail.get("meeting_after")
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        checks.append(_check(f"restart.{label}.meeting_before_after", "blocked", "real meeting_before and meeting_after details are required"))
    else:
        checks.append(_compare_exact(f"restart.{label}.meeting_id", before.get("meeting_id"), after.get("meeting_id")))
    return checks


def _breakage_clock_check(observation: Mapping[str, Any], label: str) -> dict[str, Any]:
    """Require the producer's next-day lookback to overlap the 17:00 close."""
    provenance = observation.get("provenance")
    clock = provenance.get("clock") if isinstance(provenance, Mapping) else None
    if not isinstance(clock, Mapping) or "tz" not in clock:
        return _check(f"{label}.producer_clock_overlap", "blocked",
                      "producer clock timezone is absent; breakage overlap is unproven")
    tz = clock.get("tz")
    reads = clock.get("producer_clock_reads")
    if not isinstance(reads, list) or not reads or not isinstance(reads[0], str):
        return _check(f"{label}.producer_clock_overlap", "blocked",
                      "producer clock first reading is absent; breakage overlap is unproven", tz=tz)
    match = re.search(r"\bnow=(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", reads[0])
    if match is None:
        return _check(f"{label}.producer_clock_overlap", "blocked",
                      "producer clock first reading has no timestamp", tz=tz, first_read=reads[0])
    try:
        hour = datetime.fromisoformat(match.group(1)).hour
    except ValueError:
        return _check(f"{label}.producer_clock_overlap", "blocked",
                      "producer clock first timestamp is invalid", tz=tz, first_read=reads[0])
    valid = 17 <= hour < 23
    return _check(f"{label}.producer_clock_overlap", "pass" if valid else "blocked",
                  "producer clock first reading overlaps the 17:00–23:00 breakage window"
                  if valid else "producer clock first reading is outside the 17:00–23:00 breakage window",
                  tz=tz, first_read=reads[0], first_hour=hour)


def _trigger_records(observation: Mapping[str, Any], transport: str) -> list[dict[str, Any]]:
    return [row for row in _collect_records(observation, transport) if row.get("stage") == "trigger"]


def _expected_refusal(family: str, pair: Mapping[str, Any]) -> str:
    value = pair.get("expected_refusal") or pair.get("refusal")
    if isinstance(value, Mapping):
        value = value.get("error_contains") or value.get("code")
    if not value and family == "shelf.refused":
        return "invalid_shelf_state"
    return str(value or PAIR_FAMILIES[family].get("refusal") or "")


def _refusal_check(family: str, pair: Mapping[str, Any], op_obs: Mapping[str, Any], browser_obs: Mapping[str, Any]) -> dict[str, Any]:
    expected = _expected_refusal(family, pair).lower()
    values: list[str] = []
    for obs, transport in ((op_obs, "op"), (browser_obs, "api")):
        trigger = _trigger_records(obs, transport)
        texts = [_refusal_text(row.get("refusal")) for row in trigger if row.get("refusal") is not None]
        if not texts:
            return _check(f"{transport}.named_refusal", "blocked", "the original trigger refusal was not retained")
        text = " ".join(texts).lower()
        values.append(text)
        if family == "shelf.refused":
            # The MCP schema rejects ``shelved`` before registry dispatch;
            # HTTP reaches the service and answers 422. They share the named
            # semantic refusal while retaining their distinct origin below.
            if transport == "op":
                semantic = ("invalid arguments" in text and "shelved" in text
                            and ("enum" in text or "acknowledged" in text or "deferred" in text))
            else:
                semantic = (any(row.get("status") == 422 for row in trigger)
                            and "unknown shelf state: shelved" in text)
            if not semantic:
                return _check(f"{transport}.named_refusal", "fail", "shelf refusal is not the invalid state outcome", value=text)
        elif family == "summary.no_transcript":
            code = " ".join(_refusal_code(row.get("refusal")) or "" for row in trigger).lower()
            semantic = ("no transcript" in text or "no_transcript" in text
                        or "empty transcript" in text or re.search(r"(?:^|\s)empty(?:$|\s)", code) is not None)
            if not semantic:
                return _check(f"{transport}.named_refusal", "fail", "refusal does not name the missing transcript", value=text)
        elif family == "summary.no_assignment":
            semantic = "route_unavailable" in text or "no assignment" in text or "assignment" in text
            if not semantic:
                return _check(f"{transport}.named_refusal", "fail", "refusal does not name route unavailability", value=text)
        elif expected and expected not in text:
            return _check(f"{transport}.named_refusal", "fail", f"refusal does not contain {expected!r}", value=text)
    if len(values) == 2 and expected:
        return _check("named_refusal", "pass", "both original triggers name the expected refusal")
    return _check("named_refusal", "blocked", "both original trigger refusals are required")


def _durable_stability(records: Sequence[Mapping[str, Any]], family: str) -> list[dict[str, Any]]:
    """Show that a refusal left the relevant durable reads unchanged."""
    kind = PAIR_FAMILIES[family]["kind"]
    if kind in {"summary_refusal", "decision_refusal"}:
        entity = "meeting" if kind == "summary_refusal" else "decision"
        target = _family_records(records, family)
        target = [row for row in target if row.get("refusal") is None and row.get("payload") is not None]
        before = [row for row in target if not str(row.get("stage", "")).startswith("after")]
        after = [row for row in target if str(row.get("stage", "")).startswith("after")]
        if not before or not after:
            return [_check("durable_unchanged", "blocked", "refusal has no before and after durable reads")]
        def project(payload: Any) -> Any:
            if entity == "meeting":
                return (_meeting_identity_projection(payload)
                        if family == "summary.no_assignment" else _meeting_refusal_projection(payload))
            if isinstance(payload, Mapping) and isinstance(payload.get("decisions"), list):
                return [_decision_projection(item) for item in payload["decisions"] if isinstance(item, Mapping)]
            return _decision_projection(payload)
        return [_compare_exact("durable_unchanged", project(before[-1].get("payload")), project(after[-1].get("payload")))]
    if kind == "shelf_refusal":
        shelf = _shelf_records(records)
        before = [row for row in shelf if not str(row.get("stage", "")).startswith("after")]
        after = [row for row in shelf if str(row.get("stage", "")).startswith("after")]
        brief = _family_records(records, family)
        brief_before = [row for row in brief if not str(row.get("stage", "")).startswith("after")]
        brief_after = [row for row in brief if str(row.get("stage", "")).startswith("after")]
        if not before or not after or not brief_before or not brief_after:
            return [_check("durable_unchanged", "blocked", "shelf refusal has no before and after shelf reads")]
        before_projection = _shelf_projection(before[-1].get("payload"))
        after_projection = _shelf_projection(after[-1].get("payload"))
        def brief_state(row: Mapping[str, Any]) -> Any:
            payload = _brief_payload(row.get("payload"))
            if not isinstance(payload, Mapping):
                return None
            return {key: payload.get(key) for key in
                    ("id", "generated_at", "headline", "sections", "shelf")}
        brief_check = _compare_exact("refusal.brief_unchanged",
                                     brief_state(brief_before[-1]), brief_state(brief_after[-1]))
        if before_projection == {} and after_projection == {}:
            return [_check("durable_unchanged", "pass",
                           "named before/after shelf reads and brief reads prove an unchanged empty shelf",
                           before=before_projection, after=after_projection), brief_check]
        return [_compare_exact("durable_unchanged", before_projection, after_projection), brief_check]
    return [_check("durable_unchanged", "blocked", "family has no refusal durability projection")]


def _shelf_refusal_origin(op_obs: Mapping[str, Any], browser_obs: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Keep the HTTP service refusal and MCP schema refusal distinguishable."""
    checks: list[dict[str, Any]] = []
    op_rows = _trigger_records(op_obs, "op")
    browser_rows = _trigger_records(browser_obs, "api")
    op_row = next((row for row in op_rows if row.get("refusal") is not None), None)
    browser_row = next((row for row in browser_rows if row.get("refusal") is not None), None)
    if op_row is None:
        checks.append(_check("op.refusal_origin", "blocked", "MCP refusal origin is absent"))
        checks.append(_check("op.registry_reached", "blocked", "MCP registry reach evidence is absent"))
    else:
        envelope = op_row.get("record", {}).get("envelope")
        is_error = isinstance(envelope, Mapping) and isinstance(envelope.get("result"), Mapping) and envelope["result"].get("isError") is True
        text = _refusal_text(op_row.get("refusal")).lower()
        schema_text = ("invalid arguments" in text and "shelved" in text
                       and ("enum" in text or "acknowledged" in text or "deferred" in text))
        origin_ok = is_error and schema_text
        checks.append(_check("op.refusal_origin", "pass" if origin_ok else "blocked",
                             "transport_schema" if origin_ok else "MCP schema refusal text or isError is not retained",
                             refusal_origin="transport_schema" if origin_ok else None))
        checks.append(_check("op.registry_reached", "pass" if origin_ok else "blocked",
                             "schema validation stopped before registry dispatch" if origin_ok else "registry reach is unknown",
                             registry_reached=False if origin_ok else None))
    if browser_row is None:
        checks.append(_check("browser.refusal_origin", "blocked", "HTTP refusal origin is absent"))
        checks.append(_check("browser.registry_reached", "blocked", "HTTP registry reach evidence is absent"))
    else:
        status = browser_row.get("status")
        text = _refusal_text(browser_row.get("refusal")).lower()
        service = status == 422 and "unknown shelf state: shelved" in text
        checks.append(_check("browser.refusal_origin", "pass" if service else "blocked",
                             "service_registry" if service else "HTTP refusal origin is not retained",
                             refusal_origin="service_registry" if service else None))
        checks.append(_check("browser.registry_reached", "pass" if service else "blocked",
                             "HTTP refusal reached the service boundary" if service else "registry reach is unknown",
                             registry_reached=True if service else None))
    return checks


def _check_import(op_records: Sequence[Mapping[str, Any]], browser_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    checks = [_require_records("op.meeting_reads", op_records, minimum=2),
              _require_records("browser.meeting_reads", browser_records, minimum=2)]
    for label, records in (("op", op_records), ("browser", browser_records)):
        ids = [_entity_id(row.get("payload"), "meeting") for row in records]
        checks.extend(_identity_check(records, "meeting", label=f"{label}.meeting_identity"))
        payloads = [payload for payload in _records_payloads(records) if isinstance(payload, Mapping)]
        if not payloads:
            checks.append(_check(f"{label}.import_projection", "blocked", "meeting payload is absent"))
            continue
        projection = _meeting_projection(payloads[-1])
        segments = payloads[-1].get("segments") if isinstance(payloads[-1], Mapping) else None
        bounds_ok = (isinstance(segments, list) and bool(segments)
                     and all(isinstance(segment, Mapping)
                             and isinstance(segment.get("start_time"), (int, float))
                             and isinstance(segment.get("end_time"), (int, float))
                             and segment["end_time"] >= segment["start_time"]
                             for segment in segments))
        valid = (isinstance(projection.get("title"), str) and projection.get("transcription_status") == "complete"
                 and isinstance(projection.get("duration"), (int, float)) and projection["duration"] > 0
                 and isinstance(projection.get("segments_count"), int) and projection["segments_count"] > 0
                 and bounds_ok)
        checks.append(_check(f"{label}.import_projection", "pass" if valid else "blocked",
                             "durable import has completed status, positive duration, and bounded segments"
                             if valid else "durable import projection is incomplete or segment bounds are invalid",
                             projection=projection, ids=ids))
        checks.append(_check(f"{label}.segment_bounds", "pass" if bounds_ok else "blocked",
                             "every imported segment has ordered numeric bounds"
                             if bounds_ok else "imported segment bounds are absent or invalid"))
    left = _meeting_projection(op_records[-1].get("payload")) if op_records else {}
    right = _meeting_projection(browser_records[-1].get("payload")) if browser_records else {}
    for key in ("title", "transcription_status", "duration", "segments_count"):
        checks.append(_compare_exact(f"import.{key}", left.get(key), right.get(key)))
    return checks


def _summary_projection_check(op_records: Sequence[Mapping[str, Any]], browser_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    checks = [_require_records("op.meeting_read", op_records), _require_records("browser.meeting_read", browser_records)]
    projections: list[dict[str, Any]] = []
    for label, records in (("op", op_records), ("browser", browser_records)):
        checks.extend(_identity_check(records, "meeting", label=f"{label}.summary_meeting_identity"))
        payload = records[-1].get("payload") if records else None
        projection = _meeting_projection(payload)
        projections.append(projection)
        receipt = projection.get("receipt") or {}
        ready = projection.get("summary_present") and projection.get("summary_state") in {"ready", "completed", "succeeded"}
        checks.append(_check(f"{label}.summary_nonempty_completed", "pass" if ready else "blocked",
                             "summary is nonempty and completed" if ready else "summary is absent or not completed", projection=projection))
        receipt_ok = (receipt.get("present") is True and receipt.get("host") == LAN_HOST
                      and receipt.get("outcome") == "succeeded" and receipt.get("meeting_id_present")
                      and receipt.get("job_id_present")
                      and receipt.get("meeting_id") == _entity_id(payload, "meeting"))
        job = payload.get("intel_job") if isinstance(payload, Mapping) and isinstance(payload.get("intel_job"), Mapping) else {}
        receipt_job = receipt.get("job_id")
        job_identity_ok = not job.get("id") and not job.get("job_id") or receipt_job in {job.get("id"), job.get("job_id")}
        receipt_ok = receipt_ok and job_identity_ok
        checks.append(_check(f"{label}.receipt_lan_identity", "pass" if receipt_ok else "blocked",
                             "receipt names LAN host and durable meeting/job identity" if receipt_ok else "receipt is absent, incomplete, or has wrong host",
                             receipt=receipt))
        planned_hash = _first(payload, "planned_route.selection_hash")
        receipt_hash = _first(payload, "run_receipt.selection_hash")
        checks.append(_compare_exact(f"{label}.receipt_selection_identity", planned_hash, receipt_hash))
    for key in ("title", "transcription_status", "summary_state"):
        checks.append(_compare_exact(f"summary.{key}", projections[0].get(key), projections[1].get(key)))
    return checks


def _decision_check(op_records: Sequence[Mapping[str, Any]], browser_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for label, records in (("op", op_records), ("browser", browser_records)):
        checks.extend(_identity_check(records, "decision", created=True, label=f"{label}.decision_identity"))
    left = _decision_projection(op_records[-1].get("payload")) if op_records else {}
    right = _decision_projection(browser_records[-1].get("payload")) if browser_records else {}
    for key in ("title", "status", "decision_markdown", "context_markdown"):
        checks.append(_compare_exact(f"decision.{key}", left.get(key), right.get(key)))
    return checks


def _saved_decision_records(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Select the successful saved decision lifecycle for the A1 refusal.

    The refusal trigger and its HTTP/MCP capture are deliberately excluded.
    A decision list is a separate durable proof used by ``_durable_stability``;
    this projection needs the named create/read/reopen records themselves.
    """
    selected: list[dict[str, Any]] = []
    for row in records:
        if row.get("refusal") is not None:
            continue
        name = str(row.get("name") or "")
        method = str(row.get("method") or "").upper()
        path = str(row.get("path") or "")
        if name in {"decision.create", "decision.update", "decision.read"}:
            selected.append(dict(row))
        elif method == "GET" and re.fullmatch(r"/api/decisions/[^/]+", path):
            selected.append(dict(row))
        elif ((method == "POST" and path == "/api/decisions")
              or (method in {"POST", "PUT", "PATCH"} and re.fullmatch(r"/api/decisions/[^/]+", path))):
            selected.append(dict(row))
    return selected


def _brief_ids(observation: Mapping[str, Any], records: Sequence[Mapping[str, Any]], *, final: bool = False) -> list[str]:
    variables = observation.get("variables")
    found: list[str] = []
    if isinstance(variables, Mapping) and variables.get("first_brief_id"):
        found.append(str(variables["first_brief_id"]))
    for row in records:
        if final and not str(row.get("stage", "")).startswith("after"):
            continue
        payload = _brief_payload(row.get("payload"))
        value = _entity_id(payload, "brief") if payload else None
        if value:
            found.append(value)
    return found


def _decision_ids(observation: Mapping[str, Any], records: Sequence[Mapping[str, Any]]) -> set[str]:
    # A variables capture can describe a run, but it is not durable proof that
    # the decision was created. Only a named producer response may authorize
    # the final brief's ``decision:<id>`` source_ref.
    ids: set[str] = set()
    for row in records:
        name = str(row.get("name") or "")
        path = str(row.get("path") or "")
        method = str(row.get("method") or "").upper()
        payload = row.get("payload")
        if name in {"decision.create", "decision.read"} or (method == "POST" and path == "/api/decisions") \
                or (method == "GET" and re.fullmatch(r"/api/decisions/[^/]+", path)):
            value = _entity_id(payload, "decision")
            if value:
                ids.add(value)
        if name == "decision.list" or (method == "GET" and path == "/api/decisions"):
            values = payload.get("decisions") if isinstance(payload, Mapping) else payload
            if isinstance(values, list):
                ids.update(value for value in (_entity_id(item, "decision") for item in values) if value)
    return ids


def _final_brief_payload(records: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """Return the final named brief read, keeping the durable read slot."""
    after = [row for row in records if str(row.get("stage", "")).startswith("after")
             and isinstance(_brief_payload(row.get("payload")), Mapping)]
    preferred = [row for row in after if str(row.get("name") or "") == "brief.latest"
                 or (str(row.get("method") or "").upper() == "GET" and row.get("path") == "/api/brief/latest")]
    row = (preferred or after)
    return _brief_payload(row[-1].get("payload")) if row else None


def _next_day_decision_records(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Select named decision producer/read slots for the next-day proof."""
    return _saved_decision_records(records)


def _next_day_decision_projection(records: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    rows = _next_day_decision_records(records)
    after = [row for row in rows if str(row.get("stage", "")).startswith("after")]
    row = (after or rows)
    if not row:
        return None
    payload = row[-1].get("payload")
    projection = _decision_projection(payload)
    if not projection or any(value is None for value in projection.values()):
        return None
    return projection


def _next_day_decision_checks(label: str, records: Sequence[Mapping[str, Any]],
                              final: Mapping[str, Any] | None) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    checks: list[dict[str, Any]] = []
    decision_records = _next_day_decision_records(records)
    checks.extend(_identity_check(decision_records, "decision", created=True,
                                  label=f"{label}.decision_identity"))
    decision_ids = _decision_ids({}, records)
    if not decision_records or not decision_ids:
        checks.append(_check(f"{label}.decision_durable", "blocked",
                             "named decision create/read slots are required"))
        return checks, None
    projection = _next_day_decision_projection(records)
    if projection is None:
        checks.append(_check(f"{label}.decision_projection", "blocked",
                             "user-authored decision title/status/body is absent"))
    else:
        checks.append(_check(f"{label}.decision_projection", "pass",
                             "user-authored decision title/status/body is retained",
                             projection=projection))

    items: list[Mapping[str, Any]] = []
    sections = final.get("sections") if isinstance(final, Mapping) else None
    if isinstance(sections, Mapping) and isinstance(sections.get("decisions"), list):
        items = [item for item in sections["decisions"] if isinstance(item, Mapping)]
    if not items:
        checks.append(_check(f"{label}.brief_decision_rows", "blocked",
                             "final brief has no durable decision rows"))
        return checks, projection
    valid_rows = 0
    decision_created = {_entity_id(row.get("payload"), "decision"): _decision_created_at(row.get("payload"))
                        for row in decision_records}
    for item in items:
        source = item.get("source_ref")
        row_text = item.get("text") or item.get("title")
        source_id = source[len("decision:"):] if isinstance(source, str) and source.startswith("decision:") else None
        source_ok = source_id in decision_ids
        created_at = item.get("created_at")
        created_ok = (isinstance(created_at, str) and bool(created_at)
                      and source_id in decision_created
                      and decision_created.get(source_id) == created_at)
        text_ok = isinstance(row_text, str) and bool(row_text)
        if source_ok and created_ok and text_ok:
            valid_rows += 1
        else:
            checks.append(_check(f"{label}.brief_row_source", "fail" if source_ok else "blocked",
                                 "brief row source and created_at point to the created decision"
                                 if source_ok and created_ok and text_ok
                                 else "brief row needs text, source_ref decision:<created id>, and matching created_at",
                                 source_ref=source, created_at=created_at))
    if valid_rows == len(items):
        checks.append(_check(f"{label}.brief_row_source", "pass",
                             "brief row text/source relation and created_at are durable", rows=valid_rows))
    return checks, projection


def _next_day_check(family: str, op_obs: Mapping[str, Any], browser_obs: Mapping[str, Any],
                    op_records: Sequence[Mapping[str, Any]], browser_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    decision_projections: dict[str, dict[str, Any] | None] = {}
    breakage_projections: dict[str, list[dict[str, Any]] | None] = {}
    for label, obs, records in (("op", op_obs, op_records), ("browser", browser_obs, browser_records)):
        brief_records = _family_records(records, family)
        ids = _brief_ids(obs, brief_records)
        final_ids = _brief_ids(obs, brief_records, final=True)
        if len(ids) < 2 or not final_ids:
            checks.append(_check(f"{label}.brief_identity", "blocked", "first and final brief ids are not retained"))
        else:
            checks.append(_check(f"{label}.brief_identity", "pass" if ids[0] != final_ids[-1] else "fail",
                                 "first and final brief ids differ" if ids[0] != final_ids[-1] else "first and final brief ids are equal",
                                 first=ids[0], final=final_ids[-1]))
        final = _final_brief_payload(brief_records)
        decision_checks, projection = _next_day_decision_checks(label, records, final)
        checks.extend(decision_checks)
        decision_projections[label] = projection
        if family == "closure.s5_next_day_brief_breakage":
            checks.append(_breakage_clock_check(obs, label))
            before_db = obs.get("before", {}).get("brief_db") if isinstance(obs.get("before"), Mapping) else None
            after_db = obs.get("after", {}).get("brief_db") if isinstance(obs.get("after"), Mapping) else None
            required_db_keys = ("brief", "items", "shelf")
            if (not isinstance(before_db, Mapping) or not isinstance(after_db, Mapping)
                    or any(key not in before_db or key not in after_db for key in required_db_keys)):
                checks.append(_check(f"{label}.old_brief_shelf_unchanged", "blocked", "breakage case lacks before/after brief DB snapshots"))
            else:
                before_old = {key: before_db.get(key) for key in required_db_keys}
                after_old = {key: after_db.get(key) for key in required_db_keys}
                checks.append(_check(f"{label}.old_brief_shelf_unchanged", "pass" if before_old == after_old else "fail",
                                     "old brief and shelf are unchanged" if before_old == after_old else "old brief or shelf changed"))
            sections = final.get("sections") if isinstance(final, Mapping) else None
            broke = sections.get("broke") if isinstance(sections, Mapping) else None
            broke_items = [item for item in broke if isinstance(item, Mapping)] if isinstance(broke, list) else []
            broke_ids = [str(item.get("id")) for item in broke_items if item.get("id")]
            final_id = final.get("id") if isinstance(final, Mapping) else None
            final_shelf = final.get("shelf") if isinstance(final, Mapping) else None
            final_shelf_ok = isinstance(final_shelf, Mapping) and not final_shelf
            checks.append(_check(f"{label}.final_brief_shelf_empty", "pass" if final_shelf_ok else ("blocked" if final_shelf is None else "fail"),
                                 "final generated brief has an empty shelf" if final_shelf_ok else "final generated brief shelf is absent or nonempty"))
            old_items = before_db.get("items") if isinstance(before_db, Mapping) else None
            old_brief = before_db.get("brief") if isinstance(before_db, Mapping) else None
            old_brief_id = old_brief.get("id") if isinstance(old_brief, Mapping) else None
            old_rows = [item for item in old_items if isinstance(item, Mapping)] if isinstance(old_items, list) else []
            old_by_source = {
                str(item.get("source_ref")): str(item.get("id"))
                for item in old_rows
                if item.get("source_ref") not in (None, "") and item.get("id") not in (None, "")
            }
            old_shelf = before_db.get("shelf") if isinstance(before_db, Mapping) else None
            if isinstance(old_shelf, list):
                old_shelf_rows = [row for row in old_shelf if isinstance(row, Mapping)]
            elif isinstance(old_shelf, Mapping):
                old_shelf_rows = [{"item_id": item_id, "state": state, "brief_id": old_brief_id}
                                  for item_id, state in old_shelf.items()]
            else:
                old_shelf_rows = []
            old_shelf_ok = (bool(old_rows) and bool(old_shelf_rows) and bool(old_brief_id)
                            and all(row.get("item_id") in {item.get("id") for item in old_rows}
                                    and row.get("brief_id") == old_brief_id
                                    for row in old_shelf_rows)
                            and any(_shelf_state_kind(row.get("state")) == "acknowledged"
                                    for row in old_shelf_rows))
            checks.append(_check(f"{label}.old_shelf_ack_scope", "pass" if old_shelf_ok else "blocked",
                                 "old brief has a scoped acknowledged shelf item" if old_shelf_ok
                                 else "old brief shelf is absent, empty, unscoped, or has no acknowledged item"))
            source_pairs = [(str(item.get("source_ref")), str(item.get("id")))
                            for item in broke_items if item.get("source_ref") not in (None, "") and item.get("id") not in (None, "")]
            source_ok = (bool(broke_items) and len(source_pairs) == len(broke_items)
                         and bool(old_by_source)
                         and all(source in old_by_source and old_brief_id
                                 and any(row.get("source_ref") == source
                                         and row.get("brief_id") == old_brief_id
                                         for row in old_rows)
                                 for source, _ in source_pairs))
            ids_changed = source_ok and all(old_by_source[source] != item_id for source, item_id in source_pairs)
            scoped = (bool(final_id) and bool(broke_ids) and len(broke_ids) == len(set(broke_ids))
                      and len(broke_ids) == len(broke_items)
                      and all(item.get("brief_id") in (None, final_id)
                              and str(item.get("id", "")).startswith(f"brief-break-pipeline-{final_id}-")
                              for item in broke_items))
            scoped = scoped and source_ok and ids_changed
            checks.append(_check(f"{label}.breakage_scoped_ids", "pass" if scoped else "blocked",
                                 "breakage ids are distinct, brief scoped, and differ from the old source rows" if scoped
                                 else "breakage ids lack source mapping, collide, escape the final brief, or reuse the old id"))
            breakage_projections[label] = _breakage_text_detail_projection(final)
    left, right = decision_projections.get("op"), decision_projections.get("browser")
    if left is None or right is None:
        checks.append(_check("next_day.decision_projection", "blocked",
                             "both transports need the user-authored decision projection"))
    else:
        for key in ("title", "status", "decision_markdown", "context_markdown"):
            checks.append(_compare_exact(f"next_day.decision.{key}", left.get(key), right.get(key)))
    if family == "closure.s5_next_day_brief_breakage":
        left_rows, right_rows = breakage_projections.get("op"), breakage_projections.get("browser")
        if left_rows is None or right_rows is None:
            checks.append(_check("next_day.breakage_causes", "blocked",
                                 "both transports need complete final broke text/detail rows"))
        else:
            checks.append(_compare_exact("next_day.breakage_causes", left_rows, right_rows))
    return checks


def _same_day_check(op_obs: Mapping[str, Any], browser_obs: Mapping[str, Any],
                    op_records: Sequence[Mapping[str, Any]], browser_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for label, obs, records in (("op", op_obs, op_records), ("browser", browser_obs, browser_records)):
        # Same-day identity must come from two retained producer/read stages;
        # a convenience variable is metadata, not a durable observation slot.
        producers: list[dict[str, Any]] = []
        reads: list[dict[str, Any]] = []
        for row in records:
            name = str(row.get("name") or "")
            method = str(row.get("method") or "").upper()
            path = str(row.get("path") or "")
            brief_id = _entity_id(_brief_payload(row.get("payload")), "brief")
            if not brief_id:
                continue
            if name == "brief.generate" or (method == "POST" and path == "/api/brief/generate"):
                producers.append({"row": row, "id": brief_id})
            elif name == "brief.latest" or (method == "GET" and path == "/api/brief/latest"):
                reads.append({"row": row, "id": brief_id})
        # A duplicate ``after.op``/``after.op_reads`` pair is one stage. Keep
        # one producer and one read per observation phase to prove a real
        # generate/read sequence.
        def one_per_phase(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
            chosen: dict[str, Mapping[str, Any]] = {}
            for entry in rows:
                row = entry["row"]
                phase = str(row.get("stage") or "").split(".", 1)[0].split("[", 1)[0]
                chosen.setdefault(phase, entry)
            return list(chosen.values())
        producer_stages = one_per_phase(producers)
        read_stages = one_per_phase(reads)
        stages = producer_stages + read_stages
        ids = [str(entry["id"]) for entry in stages]
        pre_reads = [entry for entry in read_stages
                     if str(entry["row"].get("stage") or "").split(".", 1)[0].split("[", 1)[0] in {"setup", "before"}]
        post_reads = [entry for entry in read_stages
                      if str(entry["row"].get("stage") or "").split(".", 1)[0].split("[", 1)[0] == "after"]
        if not producer_stages or not pre_reads or not post_reads:
            checks.append(_check(f"{label}.same_day_identity", "blocked",
                                 "same-day case needs a producer, a pre-trigger durable read, and an after read"))
        else:
            identity_ok = len(set(ids)) == 1
            checks.append(_check(f"{label}.same_day_identity", "pass" if identity_ok else "fail",
                                 "same-day generate/read ids are stable" if identity_ok else "same-day generate/read ids differ", ids=ids))
            times = [entry["row"].get("payload").get("generated_at")
                     if isinstance(entry["row"].get("payload"), Mapping) else None
                     for entry in stages]
            time_ok = bool(times) and all(isinstance(value, str) and value for value in times) and len(set(times)) == 1
            checks.append(_check(f"{label}.same_day_generated_at", "pass" if time_ok else ("fail" if any(times) else "blocked"),
                                 "same-day generated_at is stable across retained stages"
                                 if time_ok else "same-day generated_at is absent or changed", generated_at=times))
            contents = [_brief_projection(entry["row"].get("payload")) for entry in stages]
            content_ok = bool(contents) and all(content == contents[0] and content for content in contents)
            checks.append(_check(f"{label}.same_day_content", "pass" if content_ok else "fail",
                                 "same-day brief content is stable across retained stages"
                                 if content_ok else "same-day brief content changed across retained stages", content=contents))
    return checks


def _triage_check(family: str, op_records: Sequence[Mapping[str, Any]], browser_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    semantic_projections: dict[str, dict[str, str] | None] = {}
    for label, records in (("op", op_records), ("browser", browser_records)):
        briefs = [row.get("payload") for row in _family_records(records, family) if row.get("payload") is not None]
        shelf_rows = _shelf_records(records)
        shelves = [_shelf_projection(row.get("payload")) for row in shelf_rows]
        if not briefs or not shelves:
            checks.append(_check(f"{label}.triage_evidence", "blocked", "final brief and shelf durable reads are required"))
            continue
        ids = _brief_item_ids(briefs[-1])
        shelf = shelves[-1]
        brief_id = _entity_id(_brief_payload(briefs[-1]), "brief")
        shelf_id = _shelf_brief_id(shelf_rows[-1].get("payload"))
        shelf_identity_ok = shelf_id is None or (brief_id is not None and shelf_id == brief_id)
        checks.append(_check(f"{label}.shelf_brief_identity", "pass" if shelf_identity_ok else "fail",
                             "shelf item membership is scoped to the final brief" if shelf_id is None and shelf_identity_ok
                             else ("shelf belongs to the final brief" if shelf_identity_ok else "shelf brief_id differs from final brief id")))
        valid = {key: state for key, state in shelf.items() if key in ids and state in {"acknowledged", "deferred", "Ack", "Defer"}}
        if family == "philo404.arrival_triage":
            final_items: dict[str, Mapping[str, Any]] = {}
            final_brief = _brief_payload(briefs[-1])
            sections = final_brief.get("sections") if isinstance(final_brief, Mapping) else None
            if isinstance(sections, Mapping):
                for section_name, section in sections.items():
                    if str(section_name).lower() in {"this_week", "this week", "hidden", "raw"} or not isinstance(section, list):
                        continue
                    for item in section:
                        if isinstance(item, Mapping) and item.get("id") not in (None, ""):
                            final_items[str(item["id"])] = item
            ack_ok = defer_ok = False
            for item_id, item in final_items.items():
                state = str(valid.get(item_id, "")).lower()
                label_text = str(item.get("title") or item.get("text") or item.get("headline") or "").lower()
                if "ack" in label_text and state in {"ack", "acknowledged"}:
                    ack_ok = True
                if "defer" in label_text and state in {"defer", "deferred"}:
                    defer_ok = True
            semantic = _shelf_semantic_projection(briefs[-1], shelf_rows[-1].get("payload"))
            semantic_projections[label] = semantic
            ok = (len(ids) == 2 and len(valid) == 2 and set(valid) == set(shelf)
                  and semantic is not None and ack_ok and defer_ok)
            checks.append(_check(f"{label}.all_handled", "pass" if ok else "fail",
                                 "exactly two valid brief items are handled as Ack and Defer" if ok else "ALL 2 HANDLED evidence is not durable, scoped, or state matched",
                                 item_ids=sorted(ids), shelf=shelf))
        else:
            wanted = PAIR_FAMILIES[family].get("state")
            semantic = _shelf_semantic_projection(briefs[-1], shelf_rows[-1].get("payload"))
            semantic_projections[label] = semantic
            # An individual shelf proof covers the complete actual shelf
            # read. Every entry must be in the final brief and carry the
            # intended state; one matching entry beside a rogue entry is not
            # evidence for the named operation.
            state_ok = bool(shelf) and all(_shelf_state_kind(state) == wanted for state in shelf.values())
            scoped_ok = bool(shelf) and set(shelf).issubset(ids) and set(valid) == set(shelf)
            ok = state_ok and scoped_ok and semantic is not None
            checks.append(_check(f"{label}.shelf_state", "pass" if ok else ("fail" if shelf else "blocked"),
                                 f"shelf contains only scoped {wanted} items with logical source/text" if ok
                                 else "expected shelf state is absent, mixed, out of brief scope, or lacks source/text",
                                 logical_shelf=semantic))
    left, right = semantic_projections.get("op"), semantic_projections.get("browser")
    if left is None or right is None:
        checks.append(_check("shelf.logical_source_state", "blocked",
                             "both transports need logical source/text to state shelf evidence"))
    else:
        checks.append(_compare_exact("shelf.logical_source_state", left, right))
    return checks


def _thought_check(op_records: Sequence[Mapping[str, Any]], browser_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    final_bodies: dict[str, Any] = {}
    for label, records in (("op", op_records), ("browser", browser_records)):
        detail_reads = [row for row in records
                        if str(row.get("name") or "") == "thought.read"
                        or (str(row.get("method") or "").upper() == "GET"
                            and re.fullmatch(r"/api/thoughts/[^/]+", str(row.get("path") or "")))]
        workbench_reads = [row for row in records
                           if str(row.get("name") or "") == "thought.workbench.read"
                           or "/workbench" in str(row.get("path") or "")]
        save_rows = [row for row in records
                     if str(row.get("name") or "") in {"thought.create", "thought.save"}
                     or (str(row.get("method") or "").upper() in {"POST", "PATCH", "PUT"}
                         and str(row.get("path") or "").startswith("/api/thoughts"))]
        before = next((row for row in detail_reads if str(row.get("stage", "")).startswith(("setup", "before"))), None)
        after = next((row for row in reversed(detail_reads) if str(row.get("stage", "")).startswith("after")), None)
        if before is None or after is None:
            checks.append(_check(f"{label}.thought_stages", "blocked", "create/read before/save/read after stages are required"))
            continue
        if not save_rows:
            checks.append(_check(f"{label}.thought_save", "blocked", "named thought.save or HTTP save stage is required"))
        else:
            saved = _thought_projection(save_rows[-1].get("payload"))
            saved_id, saved_body = saved.get("id"), saved.get("body")
            saved_time = saved.get("last_modified")
            after_projection = _thought_projection(after.get("payload"))
            checks.append(_check(f"{label}.saved_read_identity", "pass"
                                 if saved_id and saved_id == after_projection.get("id") else "fail",
                                 "saved thought id is retained on detail read"
                                 if saved_id and saved_id == after_projection.get("id") else "saved thought id is absent or changed"))
            checks.append(_check(f"{label}.saved_read_body", "pass"
                                 if isinstance(saved_body, str) and saved_body == after_projection.get("body") else "fail",
                                 "saved body is retained on detail read"
                                 if isinstance(saved_body, str) and saved_body == after_projection.get("body") else "saved body is absent or changed"))
            checks.append(_check(f"{label}.saved_read_last_modified", "pass"
                                 if isinstance(saved_time, str) and saved_time == after_projection.get("last_modified") else "fail",
                                 "saved last_modified is retained on detail read"
                                 if isinstance(saved_time, str) and saved_time == after_projection.get("last_modified") else "saved last_modified is absent or changed"))
            saved_revision_ok = (saved.get("working_revision") == after_projection.get("working_revision")
                                 and saved.get("aggregate_revision") == after_projection.get("aggregate_revision")
                                 and isinstance(saved.get("working_revision"), (int, float))
                                 and isinstance(saved.get("aggregate_revision"), (int, float)))
            checks.append(_check(f"{label}.saved_read_revisions", "pass" if saved_revision_ok else "fail",
                                 "saved revisions equal the detail read revisions"
                                 if saved_revision_ok else "saved revisions are absent or differ from the detail read"))
        left, right = _thought_projection(before.get("payload")), _thought_projection(after.get("payload"))
        checks.append(_check(f"{label}.thought_id", "pass" if left.get("id") and left.get("id") == right.get("id") else "fail",
                             "thought id is retained through save/read" if left.get("id") == right.get("id") else "thought id changed or is absent"))
        for key in ("note_id", "raw_id", "raw_sha256"):
            checks.append(_compare_exact(f"{label}.{key}_stable", left.get(key), right.get(key)))
        wr0, wr1 = left.get("working_revision"), right.get("working_revision")
        ar0, ar1 = left.get("aggregate_revision"), right.get("aggregate_revision")
        revision_ok = all(isinstance(value, (int, float)) for value in (wr0, wr1, ar0, ar1)) and wr1 > wr0 and ar1 > ar0
        checks.append(_check(f"{label}.revisions_increase", "pass" if revision_ok else "fail",
                             "working and aggregate revisions increase on save" if revision_ok else "revision did not increase on save"))
        body_ok = isinstance(right.get("body"), str) and bool(right.get("body"))
        body_changed = (isinstance(left.get("body"), str) and isinstance(right.get("body"), str)
                        and left.get("body") != right.get("body"))
        checks.append(_check(f"{label}.body_changed_on_save", "pass" if body_changed else "fail",
                             "saved body changes from the before read" if body_changed else "saved body was unchanged from the before read"))
        time_ok = isinstance(right.get("last_modified"), str) and bool(right.get("last_modified"))
        checks.append(_check(f"{label}.saved_body", "pass" if body_ok else "blocked", "saved body is retained" if body_ok else "saved body is absent"))
        checks.append(_check(f"{label}.last_modified", "pass" if time_ok else "blocked", "working note last_modified is retained" if time_ok else "working note last_modified is absent"))
        if workbench_reads:
            cursor_projection = _thought_projection(workbench_reads[-1].get("payload"))
            cursor = cursor_projection.get("cursor_thought_id")
            checks.append(_check(f"{label}.cursor_thought_id", "pass" if cursor == right.get("id") else "fail",
                                 "workbench cursor points to saved thought" if cursor == right.get("id") else "workbench cursor points elsewhere"))
            cursor_revision = cursor_projection.get("cursor_aggregate_revision")
            cursor_revision_ok = (isinstance(cursor_revision, (int, float))
                                  and cursor_revision == right.get("aggregate_revision"))
            checks.append(_check(f"{label}.cursor_revision", "pass" if cursor_revision_ok else "fail",
                                 "workbench cursor revision equals the saved aggregate revision"
                                 if cursor_revision_ok else "workbench cursor revision is absent or differs from the saved revision"))
        else:
            checks.append(_check(f"{label}.cursor_thought_id", "blocked", "thought workbench read is absent"))
        final_bodies[label] = right.get("body")
    if "op" not in final_bodies or "browser" not in final_bodies:
        checks.append(_check("thought.body", "blocked", "both transports need a final detail read"))
    else:
        # Identities and timestamps are generated per hub. Only the user's
        # saved body is a cross-transport durable projection.
        checks.append(_compare_exact("thought.body", final_bodies["op"], final_bodies["browser"]))
    return checks


def _metadata_checks(op_entry: Any, browser_entry: Any, op_obs: Mapping[str, Any], browser_obs: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    op_raw = op_entry if isinstance(op_entry, Mapping) else {}
    browser_raw = browser_entry if isinstance(browser_entry, Mapping) else {}
    op_mode, browser_mode = _engine_mode(op_obs, op_raw), _engine_mode(browser_obs, browser_raw)
    op_duration = next((value for value in (op_raw.get("duration_s"), op_obs.get("duration_s"))
                        if isinstance(value, (int, float)) and not isinstance(value, bool)), None)
    browser_viewport = browser_raw.get("viewport", browser_obs.get("viewport"))
    # The rig's protocol verdict is not a face verdict. A face verdict is
    # retained only when the caller recorded it explicitly.
    browser_face = browser_raw.get("face_verdict", browser_obs.get("face_verdict"))
    checks = [_check("op_engine_mode", "pass" if op_mode in ENGINE_MODES else "blocked", f"op engine mode {op_mode!r}"),
              _check("browser_engine_mode", "pass" if browser_mode in ENGINE_MODES else "blocked", f"browser engine mode {browser_mode!r}")]
    if op_mode in ENGINE_MODES and browser_mode in ENGINE_MODES:
        mixed = {op_mode, browser_mode} == {"real", "replayed"}
        checks.append(_check("engine_mode_compatible", "blocked" if mixed else ("pass" if op_mode == browser_mode else "blocked"),
                             "real and replayed runs cannot be paired" if mixed else ("engine modes match" if op_mode == browser_mode else "engine modes differ")))
    checks.append(_check("op_duration_numeric", "pass" if op_duration is not None else "blocked",
                         "actual op total elapsed is numeric" if op_duration is not None else "actual op total elapsed is absent or nonnumeric", duration_s=op_duration))
    checks.append(_check("browser_viewport", "pass" if browser_viewport in {1440, 393, "1440", "393"} else "blocked",
                         "browser viewport retained" if browser_viewport in {1440, 393, "1440", "393"} else "browser viewport is absent or unsupported"))
    op_meta = {"run_id": op_raw.get("run_id") or op_obs.get("run_id"), "engine_mode": op_mode, "duration_s": op_duration,
               "observation_path": op_raw.get("observation_path") or op_raw.get("path")}
    browser_meta = {"run_id": browser_raw.get("run_id") or browser_obs.get("run_id"), "engine_mode": browser_mode,
                    "viewport": browser_viewport, "face_verdict": browser_face,
                    "run_verdict": browser_obs.get("verdict"),
                    "observation_path": browser_raw.get("observation_path") or browser_raw.get("path")}
    return checks, op_meta, browser_meta


def canonical_domain(observation: Mapping[str, Any], *, op: bool, family: str | None = None) -> dict[str, Any]:
    """Expose named records for diagnostics and old callers."""
    if family not in PAIR_FAMILIES:
        return {"reads_present": False, "payloads": [], "raw_targets": [], "target_records": [], "refusals": [], "unknown_family": True}
    records = _collect_records(observation, "op" if op else "api")
    targets = _family_records(records, family)
    return {"reads_present": bool(records), "payloads": _records_payloads(targets),
            "raw_targets": _records_payloads(targets), "target_records": targets,
            "shelf_payloads": _records_payloads(_shelf_records(records)), "refusals": _refusals(records)}


def compare_pair(pair: Mapping[str, Any]) -> dict[str, Any]:
    pair_id = str(pair.get("pair_id") or pair.get("id") or "")
    family = _family_for(pair_id, _as_str(pair.get("family")))
    op_entry = (pair.get("op") or pair.get("operation") or pair.get("op_observation")
                or pair.get("op_path") or pair.get("operation_path"))
    browser_entry = (pair.get("browser") or pair.get("face") or pair.get("browser_observation")
                     or pair.get("browser_path") or pair.get("face_path"))
    op_obs, op_path = _load_observation(op_entry)
    browser_obs, browser_path = _load_observation(browser_entry)
    checks: list[dict[str, Any]] = []
    if family is None:
        checks.append(_check("named_family", "blocked", "pair id is not a named PHILO-5-03 family"))
    if op_obs is None:
        checks.append(_check("op_observation", "blocked", "op observation path is absent or unreadable"))
    if browser_obs is None:
        checks.append(_check("browser_observation", "blocked", "browser observation path is absent or unreadable"))
    if family is None or op_obs is None or browser_obs is None:
        return {"pair_id": pair_id, "family": family, "verdict": "blocked", "checks": checks,
                "equivalence": {"verdict": "blocked", "checks": checks}, "face_verdict": None,
                "op": {"observation_path": op_path}, "browser": {"observation_path": browser_path}}
    op_entry_map = op_entry if isinstance(op_entry, Mapping) else {"observation_path": op_path}
    browser_entry_map = browser_entry if isinstance(browser_entry, Mapping) else {"observation_path": browser_path}
    metadata, op_meta, browser_meta = _metadata_checks(op_entry_map, browser_entry_map, op_obs, browser_obs)
    checks.extend(metadata)
    transport_op, transport_browser = _collect_records(op_obs, "op"), _collect_records(browser_obs, "api")
    op_records, browser_records = _family_records(transport_op, family), _family_records(transport_browser, family)
    kind = PAIR_FAMILIES[family]["kind"]
    if kind == "import":
        checks.extend(_check_import(op_records, browser_records))
    elif kind == "summary":
        checks.extend(_summary_projection_check(op_records, browser_records))
    elif kind == "restart":
        checks.extend(_summary_projection_check(op_records, browser_records))
        for label, obs in (("op", op_obs), ("browser", browser_obs)):
            checks.extend(_restart_checks(obs, label))
    elif kind == "decision":
        checks.extend(_decision_check(op_records, browser_records))
        if family == "closure.s4_decision_recorded":
            for label, obs in (("op", op_obs), ("browser", browser_obs)):
                checks.extend(_restart_checks(obs, label))
    elif kind in {"decision_refusal", "summary_refusal", "shelf_refusal"}:
        checks.append(_refusal_check(family, pair, op_obs, browser_obs))
        if kind == "shelf_refusal":
            checks.extend(_shelf_refusal_origin(op_obs, browser_obs))
        if kind == "decision_refusal":
            checks.extend(_decision_check(_saved_decision_records(op_records),
                                          _saved_decision_records(browser_records)))
        checks.extend(_durable_stability(transport_op, family))
        checks.extend(_durable_stability(transport_browser, family))
        if kind == "shelf_refusal":
            left = _shelf_refusal_cross_projection(transport_op, family)
            right = _shelf_refusal_cross_projection(transport_browser, family)
            if left == {} and right == {}:
                checks.append(_check("refusal.durable_projection", "pass",
                                     "both transports retain an explicitly empty final shelf"))
            else:
                checks.append(_compare_exact("refusal.durable_projection", left, right))
        else:
            left = (_family_records(transport_op, family, final_only=True)
                    if kind == "summary_refusal" else _saved_decision_records(_family_records(transport_op, family, final_only=True)))
            right = (_family_records(transport_browser, family, final_only=True)
                     if kind == "summary_refusal" else _saved_decision_records(_family_records(transport_browser, family, final_only=True)))
            if left and right:
                if kind == "summary_refusal":
                    projection = (_meeting_assignment_outcome_projection
                                  if family == "summary.no_assignment" else _meeting_cross_refusal_projection)
                    lp, rp = projection(left[-1].get("payload")), projection(right[-1].get("payload"))
                    if family == "summary.no_assignment":
                        checks.extend(_assignment_refusal_checks(left[-1].get("payload"), "op"))
                        checks.extend(_assignment_refusal_checks(right[-1].get("payload"), "browser"))
                else:
                    lp, rp = (_decision_projection(left[-1].get("payload")),
                              _decision_projection(right[-1].get("payload")))
                checks.append(_compare_exact("refusal.durable_projection", lp, rp))
            else:
                checks.append(_check("refusal.durable_projection", "blocked", "final durable refusal projection is required"))
    elif kind in {"next_day", "breakage"}:
        checks.extend(_next_day_check(family, op_obs, browser_obs, transport_op, transport_browser))
        if family in {"closure.s5_next_day_brief", "closure.s5_next_day_brief_breakage"}:
            for label, obs in (("op", op_obs), ("browser", browser_obs)):
                checks.extend(_restart_checks(obs, label))
    elif kind == "same_day":
        checks.extend(_same_day_check(op_obs, browser_obs, op_records, browser_records))
    elif kind in {"triage", "shelf"}:
        # Shelf reads are a separate named slot from the final brief read.
        # Pass the complete transport record sets so the case projection can
        # retain both actual shapes.
        checks.extend(_triage_check(family, transport_op, transport_browser))
    elif kind == "thought":
        checks.extend(_thought_check(op_records, browser_records))

    blocking = [row for row in checks if row.get("status") == "blocked"]
    failing = [row for row in checks if row.get("status") == "fail"]
    verdict = "blocked" if blocking else ("fail" if failing else "pass")
    return {"pair_id": pair_id, "family": family, "verdict": verdict, "checks": checks,
            "equivalence": {"verdict": verdict, "checks": checks}, "face_verdict": browser_meta.get("face_verdict"),
            "op": {**op_meta, "observation_path": op_path or op_meta.get("observation_path")},
            "browser": {**browser_meta, "observation_path": browser_path or browser_meta.get("observation_path")}}


def _normalise_rows(source: Mapping[str, Any] | Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    if isinstance(source, Mapping):
        rows = source.get("pairs") or source.get("rows")
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, Mapping)]
        result = []
        for pair_id, value in source.items():
            if pair_id in {"schema_version", "counts"} or not isinstance(value, Mapping):
                continue
            result.append({"pair_id": pair_id, **value})
        return result
    return [row for row in source if isinstance(row, Mapping)]


def build_pairs(source: Mapping[str, Any] | Iterable[Mapping[str, Any]], *, output: str | Path | None = None) -> dict[str, Any]:
    """Build the pair index from actual op/browser observation paths.

    ``source`` is either ``{"pairs": [...]}`` or an iterable of rows. Each
    row names ``pair_id``, ``op`` and ``browser`` paths (inline complete
    observations remain useful for unit callers). If ``output`` is supplied,
    the resulting index is written there.
    """
    results = [compare_pair(row) for row in _normalise_rows(source)]
    index = {"schema_version": 2, "pairs": results,
             "counts": {"total": len(results), "pass": sum(result["verdict"] == "pass" for result in results),
                        "fail": sum(result["verdict"] == "fail" for result in results),
                        "blocked": sum(result["verdict"] == "blocked" for result in results)}}
    if output is not None:
        write_pairs_index(index, output)
    return index


def build_pairs_index(source: Mapping[str, Any] | Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Compatibility alias for callers of the retired generic comparator."""
    return build_pairs(source)


def write_pairs_index(index: Mapping[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pair retained PHILO-5-03 op/browser observations")
    parser.add_argument("--input", required=True, type=Path, help="JSON containing pair rows with actual observation paths")
    parser.add_argument("--output", required=True, type=Path, help="pairs.json destination")
    args = parser.parse_args(argv)
    index = build_pairs(json.loads(args.input.read_text(encoding="utf-8")), output=args.output)
    return 0 if index["counts"]["fail"] == 0 and index["counts"]["blocked"] == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
