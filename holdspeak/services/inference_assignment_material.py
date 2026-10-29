"""The one builder of stored assignment material (InferenceAssignment@1).

Every writer of an ``inference_assignment_revisions`` row builds its
``payload_json`` and ``sha256`` here: the assignment service's write paths
and the startup reconcile (the copy backfills and the copy-identity repair).
The verifier is ``InferenceAssignmentService._assignment_material``: the
material must name the row's own id, revision, created_at and scope.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

ASSIGNMENT_SCHEMA = "InferenceAssignment@1"


def canonical(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def sha256_of(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value).encode()).hexdigest()


def build_assignment_material(
    *,
    assignment_id: str,
    public_scope: Mapping[str, Any],
    entries: Sequence[Mapping[str, Any]],
    retry_policy_id: str | None,
    revision: int,
    created_at: str,
) -> tuple[dict[str, Any], str, str]:
    """Return ``(material, payload_json, sha256)`` for one new revision."""
    material = {
        "schema": ASSIGNMENT_SCHEMA,
        "id": assignment_id,
        "scope": dict(public_scope),
        "entries": [dict(entry) for entry in entries],
        "retry_policy_id": retry_policy_id,
        "revision": revision,
        "created_at": created_at,
    }
    return material, canonical(material), sha256_of(material)


def entries_from_rows(rows: Sequence[Any]) -> list[dict[str, Any]]:
    """Normalize ``inference_assignments`` rows (profile_id, profile_revision,
    profile_schema_version, ordinal) into material entries, in ordinal order."""
    return [
        {
            "ordinal": int(row[3]),
            "profile_id": str(row[0]),
            "profile_revision": int(row[1]),
            "profile_schema_version": int(row[2]),
        }
        for row in sorted(rows, key=lambda item: int(item[3]))
    ]


def public_scope_from_columns(
    *,
    scope_kind: str,
    scope_id: str,
    subject_kind: str,
    selector_kind: str,
    capability_id: str,
    group_id: str,
) -> dict[str, str] | None:
    """The public scope a revision row's discriminant columns describe."""
    if scope_kind == "global":
        if selector_kind == "global":
            return {"kind": "global"}
        if selector_kind == "group" and group_id:
            return {"kind": "group", "group_id": group_id}
        if selector_kind == "capability" and capability_id:
            return {"kind": "capability", "capability_id": capability_id}
    if scope_kind == "subject" and selector_kind == "capability":
        return {
            "kind": "subject",
            "subject_kind": subject_kind,
            "subject_id": scope_id,
            "capability_id": capability_id,
        }
    if scope_kind == "invocation" and selector_kind == "capability":
        return {
            "kind": "invocation",
            "invocation_id": scope_id,
            "capability_id": capability_id,
        }
    return None


def assignment_key_for_scope(scope: Any) -> str | None:
    """The head key a public scope names (the service's ``_scope`` keys)."""
    if not isinstance(scope, Mapping):
        return None
    kind = scope.get("kind")
    if kind == "global" and set(scope) == {"kind"}:
        return "global"
    if kind == "group" and set(scope) == {"kind", "group_id"}:
        return f"group:{scope['group_id']}"
    if kind == "capability" and set(scope) == {"kind", "capability_id"}:
        return f"capability:{scope['capability_id']}"
    if kind == "subject" and set(scope) == {
        "kind", "subject_kind", "subject_id", "capability_id",
    }:
        return (
            f"subject:{scope['subject_kind']}:{scope['subject_id']}"
            f":capability:{scope['capability_id']}"
        )
    if kind == "invocation" and set(scope) == {"kind", "invocation_id", "capability_id"}:
        return f"invocation:{scope['invocation_id']}:capability:{scope['capability_id']}"
    return None
